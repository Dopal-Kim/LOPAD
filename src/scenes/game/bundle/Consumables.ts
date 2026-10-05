/**
 * 60라운드 (i) 층 테마 소모품 1층 3종 (data/bundle2.json consumables — 57 Q38 확정안): 별도 소모품 칸 1개(같은 종류 최대 2,
 * 다른 종류면 '바꾼다 / 그대로 둔다' 필수 메뉴 consumableSwap — 계약 §14.7), 새 키(KEYS.CONSUMABLE).
 * - 화염 술병: 누르면 커서 방향 즉시 투척 — `fire_bottle_thrown` 포물선(손 높이 70 도트, 최대 6칸) → 착지 `fire_bottle_burst`
 *   (반지름 96 도트 = 1.5칸) → 불 웅덩이 4초 (0.5초마다 공격 ×0.3 + 고정 3) — 그림은 fire_pool 로 넘김 (계약 art §22.1)
 * - 깡술 한 모금: 8초 공격 +20% · 받는 피해 +10% · 피격 경직 없음 (취기 '마시기 사건')
 * - 냉수 한 바가지: 그로기 해제·기력 50% / 과열 0 / 탄창·숨 가득 · 3초 '세상이 돈다' 기울기 무시
 * 월드 드롭 = `items/v3/consumable_f1` (행 = 종류) — 밟으면 줍는다.
 */
import Phaser from 'phaser';
import { BUILD_ART, BUNDLE_FX, DEPTH, KEYS } from '../../../core/Constants';
import { EventBus, Events, type ConsumablePayload } from '../../../core/EventBus';
import { gameState } from '../../../core/GameState';
import { BUNDLE2, consumableDef } from '../../../data/bundle2';
import type { ConsumableDef, ConsumableId } from '../../../data/bundle2Types';
import { UI_EVENTS, __system, type UiConsumableSlot, type UiConsumableUsed } from '../../../contract/ui';
import { spriteLibrary } from '../../../systems/sprites/sprites';
import { FX_ACTION, artScale } from '../../../systems/sprites/spriteDefs';
import { ITEM_ACTION, ITEM_SHEET } from '../../../systems/bundle2/bundleSheets';
import type { Game } from '../../Game';
import { T } from '../shared';

export type { ConsumablePayload } from '../../../core/EventBus';

interface Drop {
  id: ConsumableId;
  sprite: Phaser.GameObjects.GameObject & { x: number; y: number; destroy(): void };
  until: number;
}

export class Consumables {
  /** 깡술 끝 · 냉수 기울기 무시 끝 */
  private strongUntil = -Infinity;
  private drops: Drop[] = [];

  constructor(private readonly g: Game) {}

  private get slot() {
    return gameState.bundle.consumable;
  }

  /** 얻기 — 칸이 다른 종류면 바꿀지 묻는다 (필수 메뉴). 가득이면 false */
  gain(id: ConsumableId, onDone: () => void = () => {}): boolean {
    const r = this.slot.tryGain(id);
    if (r === 'added') {
      onDone();
      return true;
    }
    if (r === 'full') {
      onDone();
      return false;
    }
    const g = this.g;
    const cur = this.slot.id ? consumableDef(this.slot.id) : undefined;
    const next = consumableDef(id);
    g.setFrozen(true);
    g.menu.open(
      'consumableSwap',
      `소모품 — ${next?.name ?? id}`,
      [
        { key: '1', label: `바꾼다 (${cur?.name ?? ''} 버림)`, enabled: true, detail: next?.description ?? '' },
        { key: '2', label: '그대로 둔다', enabled: true, detail: cur?.description ?? '' },
      ],
      (key) => {
        if (key === '1') this.slot.replace(id);
        g.menu.close();
        g.setFrozen(false);
        onDone();
      },
    );
    return true;
  }

  // --- 사용 ---

  update(pressed: boolean, now: number): void {
    if (pressed && !this.g.menu.isOpen && !this.g.frozen) this.use(now);
    this.pickDrops(now);
  }

  private use(now: number): void {
    const id = this.slot.use();
    if (!id) return;
    const def = consumableDef(id)!;
    EventBus.emit(Events.CONSUMABLE_USED, { id } satisfies ConsumablePayload);
    __system.emit(UI_EVENTS.CONSUMABLE_USED, {
      id,
      name: def.name,
      left: this.slot.count,
    } satisfies UiConsumableUsed);
    if (def.kind === 'throw') this.throwBottle(def, now);
    else if (id === 'strongDrink') this.strongDrink(def, now);
    else this.coldWater(def, now);
    if (def.kind === 'drink') this.g.build?.drink('consumable');
  }

  /** 화염 술병 — 커서 방향(최대 rangeTiles) 포물선 → 착지 폭발 → 불 웅덩이 */
  private throwBottle(def: ConsumableDef, _now: number): void {
    const g = this.g;
    const P = def.params;
    const pl = g.player;
    const tx0 = pl.aimPoint.x;
    const ty0 = pl.aimPoint.y;
    const d = Math.hypot(tx0 - pl.x, ty0 - pl.y) || 1;
    const max = T(P.rangeTiles ?? 6);
    const k = Math.min(1, max / d);
    const tx = pl.x + (tx0 - pl.x) * k;
    const ty = pl.y + (ty0 - pl.y) * k;
    const thrownDef = spriteLibrary.sheet(BUILD_ART.BOTTLE_THROWN, FX_ACTION);
    const hand = 70 * (thrownDef ? artScale(thrownDef) : 0.25);
    const sx = pl.x;
    const sy = pl.y - hand;
    const h = g.fx.has(BUILD_ART.BOTTLE_THROWN)
      ? g.fx.play(BUILD_ART.BOTTLE_THROWN, sx, sy, { depth: DEPTH.PROJECTILE, flipX: tx < pl.x, hooks: false })
      : null;
    const dot = h ? null : g.add.circle(sx, sy, 2, 0xe07a2a).setDepth(DEPTH.PROJECTILE);
    const shadow = g.add.ellipse(pl.x, pl.y, 6, 3, 0x000000, 0.35).setDepth(DEPTH.SHADOW);
    const ms = P.flightMs ?? 420;
    const arc = P.arcPx ?? 18;
    g.tweens.addCounter({
      from: 0,
      to: 1,
      duration: ms,
      onUpdate: (tw) => {
        const t = tw.getValue() ?? 0;
        const x = sx + (tx - sx) * t;
        const yBase = pl.y + (ty - pl.y) * t;
        const y = sy + (ty - sy) * t - Math.sin(t * Math.PI) * arc;
        h?.sprite.setPosition(x, y);
        dot?.setPosition(x, y);
        shadow.setPosition(x, yBase);
      },
      onComplete: () => {
        if (h) g.fx.stop(h, 0, false);
        dot?.destroy();
        shadow.destroy();
        if (g.scene.isActive()) this.burst(def, tx, ty);
      },
    });
  }

  private burst(def: ConsumableDef, x: number, y: number): void {
    const g = this.g;
    const P = def.params;
    const r = T(P.radiusTiles ?? 1.5);
    const bd = spriteLibrary.sheet(BUILD_ART.BOTTLE_BURST, FX_ACTION);
    const dots = (bd as unknown as { radiusPx?: number } | undefined)?.radiusPx;
    if (bd && g.fx.has(BUILD_ART.BOTTLE_BURST))
      g.fx.play(BUILD_ART.BOTTLE_BURST, x, y, {
        depth: DEPTH.HIT_FX,
        scaleMult: dots ? r / (dots * artScale(bd)) : 1,
      });
    EventBus.emit(Events.CONSUMABLE_IMPACT, { id: def.id } satisfies ConsumablePayload);
    const flat = P.tickFlat ?? 0;
    const side = r * 2;
    const pool = g.pools.add(new Phaser.Geom.Rectangle(x - r, y - r, side, side), {
      owner: 'structure',
      lifeMs: P.fireMs ?? 4000,
      playerSlow: 0,
      enemySlow: 0,
      slip: 0,
      fireMs: P.fireMs ?? 4000,
      fireTickMs: P.tickMs ?? 500,
      firePlayerAttack: 0,
      fireMobDamage: () => Math.max(1, Math.round(g.combat.rollDamage(P.tickMult ?? 0.3).dmg + flat)),
      fireFx: 'fire_pool',
      spreadMsPerCell: null,
      linkGapPx: 0,
      color: 0xe08a3a,
      alpha: 0.2,
    });
    g.pools.ignite(pool);
    // 술 웅덩이에 닿으면 술불 (취기 점화원 — 57 설계)
    g.pools.igniteIn(new Phaser.Geom.Rectangle(x - r, y - r, side, side));
  }

  private strongDrink(def: ConsumableDef, now: number): void {
    this.strongUntil = now + (def.params.ms ?? 8000);
  }

  private coldWater(def: ConsumableDef, now: number): void {
    const g = this.g;
    const P = def.params;
    g.player.resource?.refresh(P.staminaRatio ?? 0.5);
    const br = g.player.gauges.breath;
    if (br) br.value = br.max;
    g.bossArena?.suppressTilt(now + (P.tiltImmuneMs ?? 3000));
  }

  /** 깡술 중 공격 배율 (GameCombat.rollDamage) */
  attackMult(now: number): number {
    if (now >= this.strongUntil) return 1;
    return 1 + (consumableDef('strongDrink')?.params.attackMult ?? 0);
  }

  /** 깡술 중 받는 피해 배율 (BuildDefense.adjustDamage) */
  damageTakenMult(now: number): number {
    if (now >= this.strongUntil) return 1;
    return 1 + (consumableDef('strongDrink')?.params.damageTaken ?? 0);
  }

  /** 깡술 중 피격 경직 없음 */
  noFlinch(now: number): boolean {
    return now < this.strongUntil;
  }

  // --- 월드 드롭 ---

  /** 바닥에 떨어진 소모품 (밟으면 줍는다) */
  spawnDrop(x: number, y: number, id: ConsumableId): void {
    const g = this.g;
    const def = spriteLibrary.sheet(ITEM_SHEET, ITEM_ACTION);
    const tex = spriteLibrary.textureKey(ITEM_SHEET, ITEM_ACTION);
    const cdef = consumableDef(id);
    let sprite: Drop['sprite'];
    if (def && tex && g.textures.exists(tex) && cdef) {
      const meta = def as unknown as { kinds?: string[] };
      const row = Math.max(0, meta.kinds?.indexOf(cdef.kindRow) ?? 0);
      const img = g.add
        .sprite(x, y, tex, String(row * def.frames))
        .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
        .setScale(artScale(def))
        .setDepth(DEPTH.PICKUP);
      g.tweens.add({ targets: img, y: y - 2, yoyo: true, repeat: -1, duration: 600 });
      sprite = img;
    } else sprite = g.add.rectangle(x, y, 6, 8, 0xe07a2a).setDepth(DEPTH.PICKUP);
    this.drops.push({ id, sprite, until: g.time.now + BUNDLE2.consumables.dropLifeMs });
  }

  private pickDrops(now: number): void {
    if (this.drops.length === 0) return;
    const pl = this.g.player;
    this.drops = this.drops.filter((d) => {
      if (now >= d.until) {
        d.sprite.destroy();
        return false;
      }
      if (Math.hypot(pl.x - d.sprite.x, pl.y - d.sprite.y) > T(BUNDLE_FX.ITEM_PICK_TILES)) return true;
      if (this.g.menu.isOpen) return true;
      const r = this.slot.tryGain(d.id);
      if (r === 'full') return true;
      if (r === 'swap') {
        this.gainSwapFromDrop(d);
        return false;
      }
      d.sprite.destroy();
      EventBus.emit(Events.ITEM_PICKED, { kind: 'consumable', value: 1 });
      return false;
    });
  }

  private gainSwapFromDrop(d: Drop): void {
    d.sprite.destroy();
    this.gain(d.id);
  }

  /** 계약 §14.8 소모품 칸 */
  toUi(): UiConsumableSlot {
    const s = this.slot;
    const def = s.id ? consumableDef(s.id) : undefined;
    return {
      key: KEYS.CONSUMABLE,
      item: def
        ? { id: def.id, name: def.name, description: def.description, kind: def.kind, count: s.count, max: s.max }
        : null,
    };
  }

  debug(now: number): Record<string, unknown> {
    return { slot: this.slot.toSave(), strong: now < this.strongUntil, drops: this.drops.length };
  }

  destroy(): void {
    for (const d of this.drops) d.sprite.destroy();
    this.drops = [];
  }
}
