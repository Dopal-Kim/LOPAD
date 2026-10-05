/**
 * 60라운드 (g) 엘리트 접두어 1층 6종 (data/bundle2.json elite — 57 Q38 확정안): 엘리트 = 일반 적 + 접두어 1, HP ×2.5·그림 ×1.15.
 * 그림 (계약 art §22): 호박 외곽선 `enemies/v3/<적>_<동작>_elite` 를 적 **바로 아래** 같은 프레임·피벗·flip·배율로 (알파 맥동) ·
 * 머리 위 문장 `fx/v3/elite_emblem`(행 = 접두어, 0열 평소 · 1열 발동·변형). 이름표는 UI(UiSnapshot.elites — 계약 §14.9).
 * 접두어 규칙: 고주망태(휘는 걸음·피격 경직 절반·죽으면 술 웅덩이) · 불붙은(접촉 불 피해·지나간 자리 불씨) ·
 * 통 갑옷(받는 피해 −30%·경직 면역, 첫 강공에 깨짐) · 성난(HP 50% 이하 이동·공격 +40%) ·
 * 패거리 두목(주변 일반 적 이동 +20%·공격 간격 −20%, 죽으면 주변 1초 경직) · 들이켜는(주변 적이 죽으면 HP +15%·크기 +5%, 3회).
 */
import Phaser from 'phaser';
import { BUILD_ART, BUNDLE_FX, DEPTH, TILE } from '../../../core/Constants';
import { EventBus, Events, type ElitePrefixPayload, type EliteSpawnedPayload } from '../../../core/EventBus';
import { BUNDLE2, prefixDef } from '../../../data/bundle2';
import type { ElitePrefixDef, ElitePrefixId } from '../../../data/bundle2Types';
import type { UiElite } from '../../../contract/ui';
import type { Mob } from '../../../objects/Mob';
import { worldToLogicalScreen } from '../../../systems/display';
import type { FxHandle } from '../../../systems/fx/fx';
import { spriteLibrary } from '../../../systems/sprites/sprites';
import { FX_ACTION, artScale, frameStarts, fxDrawScale, parseAnimKey } from '../../../systems/sprites/spriteDefs';
import { ENEMIES } from '../../../data';
import type { Game } from '../../Game';
import { eliteAction } from '../../../systems/bundle2/bundleSheets';

export type ElitePrefixPhase = 'break' | 'trigger' | 'drink' | 'death';
export type { ElitePrefixPayload, EliteSpawnedPayload } from '../../../core/EventBus';

interface EliteRec {
  mob: Mob;
  def: ElitePrefixDef;
  outline: Phaser.GameObjects.Sprite | null;
  emblem: Phaser.GameObjects.Sprite | null;
  /** 문장 열 (0 평소 · 1 발동) */
  emblemCol: number;
  armorBroken: boolean;
  enraged: boolean;
  drinks: number;
  baseScale: number;
  nextContactAt: number;
  nextTrailAt: number;
  phase: number;
  /** §22.1: 통 갑옷 뒤·앞 판 · 술 김 루프 */
  barrelBack: Phaser.GameObjects.Sprite | null;
  barrelFront: Phaser.GameObjects.Sprite | null;
  barrelHitUntil: number;
  vapor: FxHandle | null;
}

/** §22.1 두목 연결선·발밑 고리 (강화 대상마다) */
interface LinkRec {
  line: Phaser.GameObjects.Sprite | null;
  aura: FxHandle | null;
}

type BodyBox = { cx: number; cy: number; scale: number };

const T = (n: number) => n * TILE;

export class EliteSystem {
  private readonly list: EliteRec[] = [];
  /** 두목이 강화한 일반 적 (매 프레임 다시 고른다) · 그 연결선·고리 */
  private boosted = new Set<Mob>();
  private readonly links = new Map<Mob, LinkRec>();

  constructor(private readonly g: Game) {}

  /** 이 적에 붙을 수 있는 접두어 (원하는 것이 안 맞으면 붙을 수 있는 것 중 무작위) */
  pickFor(mob: Mob, want: ElitePrefixId | null): ElitePrefixDef | null {
    const ok = BUNDLE2.elite.prefixes.filter((p) => p.enemies.includes(mob.spriteId));
    if (ok.length === 0) return null;
    const w = want ? ok.find((p) => p.id === want) : undefined;
    return w ?? ok[Math.floor(this.g.rng.next() * ok.length)];
  }

  /** 일반 적을 엘리트로 (이미 엘리트·보스면 false) */
  makeElite(mob: Mob, want: ElitePrefixId | null): boolean {
    if (mob.elite || mob.isBoss || !mob.active) return false;
    const def = this.pickFor(mob, want);
    if (!def) return false;
    const E = BUNDLE2.elite;
    const enemyName = ENEMIES[mob.spriteId]?.name ?? mob.spriteId;
    mob.elite = { prefix: def.id, name: `${def.name} ${enemyName}` };
    mob.scaleMaxHp(E.hpMult);
    mob.visual.setDrawScale(mob.visual.drawScale * E.sizeMult);
    if (def.id === 'drunkard') mob.hitStunMult = def.params.hitStunMult ?? 0.5;
    if (def.id === 'barrelArmor') {
      mob.damageTakenMult = 1 + (def.params.damageTaken ?? -0.3);
      mob.stunImmune = true;
    }
    const rec: EliteRec = {
      mob,
      def,
      outline: this.makeOutline(mob),
      emblem: this.makeEmblem(),
      emblemCol: 0,
      armorBroken: false,
      enraged: false,
      drinks: 0,
      baseScale: mob.visual.drawScale,
      nextContactAt: 0,
      nextTrailAt: 0,
      phase: this.g.rng.next() * Math.PI * 2,
      barrelBack: def.id === 'barrelArmor' ? this.fxSprite(BUILD_ART.ELITE_BARREL) : null,
      barrelFront: def.id === 'barrelArmor' ? this.fxSprite(BUILD_ART.ELITE_BARREL) : null,
      barrelHitUntil: 0,
      vapor: def.id === 'drunkard' ? this.playVapor(mob) : null,
    };
    this.list.push(rec);
    mob.once(Phaser.GameObjects.Events.DESTROY, () => this.drop(rec));
    EventBus.emit(Events.ELITE_SPAWNED, { id: mob.spriteId, prefix: def.id } satisfies EliteSpawnedPayload);
    return true;
  }

  private makeOutline(mob: Mob): Phaser.GameObjects.Sprite | null {
    return this.g.add.sprite(mob.x, mob.y, '__DEFAULT').setVisible(false);
  }

  /** fx 시트의 정지 프레임용 스프라이트 (없으면 null) */
  private fxSprite(id: string): Phaser.GameObjects.Sprite | null {
    const tex = spriteLibrary.textureKey(id, FX_ACTION);
    if (!tex || !this.g.textures.exists(tex)) return null;
    return this.g.add.sprite(0, 0, tex, 0).setVisible(false);
  }

  private headTop(id: string, mob: Mob): number {
    const def = spriteLibrary.sheet(id, FX_ACTION);
    const h = (def as unknown as { headTopByEnemy?: Record<string, number> } | undefined)?.headTopByEnemy?.[
      mob.spriteId
    ];
    return h ?? BUNDLE_FX.ELITE_HEAD_TOP_DOTS;
  }

  /** 술 김 (적 머리 꼭대기 − 8 도트, 문장 아래 — 따라감) */
  private playVapor(mob: Mob): FxHandle | null {
    const id = BUILD_ART.ELITE_VAPOR;
    const def = spriteLibrary.sheet(id, FX_ACTION);
    if (!def || !this.g.fx.has(id)) return null;
    const k = artScale(def) * mob.visual.drawScale;
    return this.g.fx.play(id, mob.x, mob.y, {
      follow: mob,
      followOffset: { x: 0, y: -(this.headTop(id, mob) - 8) * k },
      depthOffset: DEPTH.OVERLAY_STEP * 3,
      scaleMult: mob.visual.drawScale,
      hooks: false,
    });
  }

  private makeEmblem(): Phaser.GameObjects.Sprite | null {
    const tex = spriteLibrary.textureKey(BUILD_ART.ELITE_EMBLEM, FX_ACTION);
    if (!tex || !this.g.textures.exists(tex)) return null;
    return this.g.add.sprite(0, 0, tex, 0).setVisible(false);
  }

  private drop(rec: EliteRec): void {
    rec.outline?.destroy();
    rec.emblem?.destroy();
    rec.barrelBack?.destroy();
    rec.barrelFront?.destroy();
    this.g.fx.stop(rec.vapor, 0, false);
    if (rec.def.id === 'ringleader') this.clearLinks();
    const i = this.list.indexOf(rec);
    if (i >= 0) this.list.splice(i, 1);
  }

  private prefixEvent(def: ElitePrefixDef, phase: ElitePrefixPhase, count?: number): void {
    EventBus.emit(Events.ELITE_PREFIX, {
      prefix: def.id,
      phase,
      ...(count !== undefined ? { count } : {}),
    } satisfies ElitePrefixPayload);
  }

  /** 강공 적중 (GameCombat.hitMob — 통 갑옷 깨짐) */
  onHeavyHit(mob: Mob): void {
    const rec = this.list.find((r) => r.mob === mob);
    if (!rec || rec.def.id !== 'barrelArmor' || rec.armorBroken) return;
    rec.armorBroken = true;
    rec.emblemCol = 1;
    mob.damageTakenMult = 1;
    mob.stunImmune = false;
    rec.barrelBack?.destroy();
    rec.barrelFront?.destroy();
    rec.barrelBack = null;
    rec.barrelFront = null;
    // elite_barrel_armor_break: 적 발밑 가로 가운데(bodyBox cx) · scale = bodyBox.scale
    const box = this.bodyBox(BUILD_ART.ELITE_BARREL_BREAK, mob);
    const def = spriteLibrary.sheet(BUILD_ART.ELITE_BARREL_BREAK, FX_ACTION);
    if (def && box)
      this.g.fx.play(BUILD_ART.ELITE_BARREL_BREAK, mob.x + box.cx * artScale(def) * mob.visual.drawScale, mob.y, {
        depth: mob.depth + DEPTH.OVERLAY_STEP * 4,
        scaleMult: box.scale,
        flipX: mob.flipX,
      });
    this.prefixEvent(rec.def, 'break');
  }

  /** 통 갑옷이 막아낸 맞음 (1·2열 잠깐) */
  onArmorBlock(mob: Mob): void {
    const rec = this.list.find((r) => r.mob === mob);
    if (rec && rec.def.id === 'barrelArmor' && !rec.armorBroken) rec.barrelHitUntil = this.g.time.now + 160;
  }

  private bodyBox(id: string, mob: Mob): BodyBox | null {
    const def = spriteLibrary.sheet(id, FX_ACTION);
    return (
      (def as unknown as { bodyBoxByEnemy?: Record<string, BodyBox> } | undefined)?.bodyBoxByEnemy?.[mob.spriteId] ??
      null
    );
  }

  /** 처치 (Progression.onKill 뒤): 고주망태 웅덩이 · 두목 쓰러짐 · 들이켜는 주변 처치 */
  onKill(mob: Mob): void {
    const now = this.g.time.now;
    const rec = this.list.find((r) => r.mob === mob);
    if (rec?.def.id === 'drunkard' && this.g.build) {
      const P = rec.def.params;
      this.g.build.fx.liquorPool(mob.x, mob.y, T(P.deathPoolTiles ?? 1), P.deathPoolMs ?? 6000);
    }
    if (rec?.def.id === 'ringleader') {
      const P = rec.def.params;
      for (const m of this.mobsNear(mob.x, mob.y, T(P.radiusTiles ?? 4))) {
        if (m === mob) continue;
        m.stun(now, P.deathStunMs ?? 1000, 'hit');
        this.g.build?.art.stagger(m, P.deathStunMs ?? 1000);
      }
      this.clearLinks();
      this.prefixEvent(rec.def, 'death');
    }
    for (const r of this.list) {
      if (r.mob === mob || r.def.id !== 'guzzler' || !r.mob.active) continue;
      const P = r.def.params;
      if (r.drinks >= (P.maxDrinks ?? 3) || Math.hypot(r.mob.x - mob.x, r.mob.y - mob.y) > T(P.radiusTiles ?? 5))
        continue;
      r.drinks += 1;
      this.guzzle(r, mob.x, mob.y, P);
    }
  }

  /**
   * 들이켜는: 죽은 적 머리 위(60 도트)에서 줄기(elite_guzzle_trail)가 엘리트 머리로 0.35초 → 마시기(elite_guzzle_drink) healFrame
   * 에 HP·크기 증가 · 문장 1열 · 음향 ELITE_PREFIX drink. 시트가 없으면 바로 적용
   */
  private guzzle(r: EliteRec, fromX: number, fromY: number, P: Record<string, number>): void {
    const g = this.g;
    const apply = () => {
      if (!r.mob.active) return;
      r.mob.healRatio(P.healRatio ?? 0.15);
      r.mob.visual.setDrawScale(r.baseScale * (1 + (P.growPerDrink ?? 0.05) * r.drinks));
      r.emblemCol = 1;
      g.time.delayedCall(400, () => (r.emblemCol = 0));
      this.prefixEvent(r.def, 'drink', r.drinks);
    };
    const trailDef = spriteLibrary.sheet(BUILD_ART.ELITE_GUZZLE_TRAIL, FX_ACTION);
    const drinkDef = spriteLibrary.sheet(BUILD_ART.ELITE_GUZZLE_DRINK, FX_ACTION);
    const arrive = () => {
      if (!r.mob.active) return;
      if (!drinkDef || !g.fx.has(BUILD_ART.ELITE_GUZZLE_DRINK)) return apply();
      const k = artScale(drinkDef) * r.mob.visual.drawScale;
      g.fx.play(BUILD_ART.ELITE_GUZZLE_DRINK, r.mob.x, r.mob.y, {
        follow: r.mob,
        followOffset: { x: 0, y: -(this.headTop(BUILD_ART.ELITE_GUZZLE_DRINK, r.mob) - 70) * k },
        depthOffset: DEPTH.OVERLAY_STEP * 4,
        scaleMult: r.mob.visual.drawScale,
      });
      const hf = (drinkDef as unknown as { healFrame?: number }).healFrame ?? 4;
      g.time.delayedCall(frameStarts(drinkDef)[hf] ?? 0, apply);
    };
    if (!trailDef || !g.fx.has(BUILD_ART.ELITE_GUZZLE_TRAIL)) return arrive();
    const k = artScale(trailDef);
    const sx = fromX;
    const sy = fromY - 60 * k;
    const head = () => ({ x: r.mob.x, y: r.mob.y - this.headTop(BUILD_ART.ELITE_GUZZLE_DRINK, r.mob) * k });
    const h = g.fx.play(BUILD_ART.ELITE_GUZZLE_TRAIL, sx, sy, { depth: DEPTH.HIT_FX, hooks: false, durationMs: 400 });
    const ms = 350;
    const arc = 30 * k;
    if (h)
      g.tweens.addCounter({
        from: 0,
        to: 1,
        duration: ms,
        onUpdate: (tw) => {
          const t = tw.getValue() ?? 0;
          const e = head();
          const x = sx + (e.x - sx) * t;
          const y = sy + (e.y - sy) * t - Math.sin(t * Math.PI) * arc;
          h.sprite.setRotation(Math.atan2(y - h.sprite.y, x - h.sprite.x)).setPosition(x, y);
        },
      });
    g.time.delayedCall(ms, () => {
      if (h) g.fx.stop(h, 0, false);
      arrive();
    });
  }

  private mobsNear(x: number, y: number, r: number): Mob[] {
    return (this.g.mobs.getChildren() as Mob[]).filter((m) => m.active && Math.hypot(m.x - x, m.y - y) <= r);
  }

  /** 매 프레임 (적 갱신 뒤): 규칙 · 외곽선·문장 그림 */
  lateUpdate(now: number): void {
    const boosted = new Set<Mob>();
    for (const r of [...this.list]) {
      const m = r.mob;
      if (!m.active) continue;
      this.rule(r, now, boosted);
      this.draw(r, now);
    }
    // 두목 강화가 끝난 적은 원래대로 (연결선·고리도 끔)
    for (const m of this.boosted) {
      if (boosted.has(m)) continue;
      this.unlink(m);
      if (!m.active || m.elite) continue;
      m.eliteSpeedMult = 1;
      m.attackRateMult = 1;
    }
    this.boosted = boosted;
  }

  /**
   * 두목 연결선 (elite_ringleader_link — 두목 pivot 위 60 → 대상 pivot 위 60, 회전) · 대상 발밑 고리 (elite_ringleader_aura).
   * 반복 타일 시트를 한 장으로 길이에 맞춰 늘린다 (임시 — 타일 반복은 다음 정리)
   */
  private drawLink(leader: Mob, ally: Mob): void {
    const g = this.g;
    let rec = this.links.get(ally);
    if (!rec) {
      const aura = g.fx.has(BUILD_ART.ELITE_AURA)
        ? g.fx.play(BUILD_ART.ELITE_AURA, ally.x, ally.y, {
            follow: ally,
            depthOffset: -DEPTH.OVERLAY_STEP * 2,
            scaleMult: ally.spriteId === 'charger' ? 1.25 : 1,
            hooks: false,
          })
        : null;
      rec = { line: this.fxSprite(BUILD_ART.ELITE_LINK), aura };
      if (rec.line) {
        const key = spriteLibrary.animKey(BUILD_ART.ELITE_LINK, FX_ACTION, 'any');
        if (key && g.anims.exists(key)) rec.line.play(key);
      }
      this.links.set(ally, rec);
    }
    const line = rec.line;
    const def = spriteLibrary.sheet(BUILD_ART.ELITE_LINK, FX_ACTION);
    if (!line || !def) return;
    const k = artScale(def);
    const ax = leader.x;
    const ay = leader.y - 60 * k;
    const bx = ally.x;
    const by = ally.y - 60 * k;
    const len = Math.hypot(bx - ax, by - ay);
    const w = def.frameWidth * fxDrawScale(def);
    line
      .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
      .setPosition(ax, ay)
      .setRotation(Math.atan2(by - ay, bx - ax))
      .setScale(w > 0 ? (len / w) * fxDrawScale(def) : fxDrawScale(def), fxDrawScale(def))
      .setDepth(DEPTH.HIT_FX - 0.2)
      .setVisible(true);
  }

  private unlink(m: Mob): void {
    const rec = this.links.get(m);
    if (!rec) return;
    rec.line?.destroy();
    this.g.fx.stop(rec.aura, 0, false);
    this.links.delete(m);
  }

  private clearLinks(): void {
    for (const m of [...this.links.keys()]) this.unlink(m);
  }

  private rule(r: EliteRec, now: number, boosted: Set<Mob>): void {
    const m = r.mob;
    const P = r.def.params;
    const pl = this.g.player;
    switch (r.def.id) {
      case 'drunkard': {
        // 휘는 걸음: 진행 방향에 수직으로 흔들림을 더한다 (보스 취권 곡선 예고와 같은 언어)
        const v = m.body.velocity;
        const sp = Math.hypot(v.x, v.y);
        if (sp > 1) {
          const k = Math.sin(now * 0.001 * Math.PI * 2 * (P.wobbleHz ?? 1.2) + r.phase) * T(P.wobbleTiles ?? 0.6) * 2;
          const px = -v.y / sp;
          const py = v.x / sp;
          v.x += px * k;
          v.y += py * k;
        }
        r.emblemCol = Math.floor(now / 400) % 2;
        break;
      }
      case 'burning': {
        r.emblemCol = Math.floor(now / 250) % 2;
        const reach = (m.body.halfWidth + pl.body.halfWidth) * 1.1;
        if (now >= r.nextContactAt && Math.hypot(pl.x - m.x, pl.y - m.y) <= reach) {
          r.nextContactAt = now + (P.contactTickMs ?? 500);
          pl.takeHit(P.contactDamage ?? 5, now);
        }
        if (now >= r.nextTrailAt && Math.hypot(m.body.velocity.x, m.body.velocity.y) > 1) {
          r.nextTrailAt = now + (P.trailEveryMs ?? 400);
          this.ember(m.x, m.y, P);
        }
        break;
      }
      case 'enraged':
        if (!r.enraged && m.hp / m.maxHp <= (P.hpRatio ?? 0.5)) {
          r.enraged = true;
          r.emblemCol = 1;
          m.eliteSpeedMult = P.speedMult ?? 1.4;
          m.attackRateMult = P.attackRateMult ?? 1.4;
          this.prefixEvent(r.def, 'trigger');
        }
        break;
      case 'ringleader':
        r.emblemCol = Math.floor(now / 600) % 2;
        for (const o of this.mobsNear(m.x, m.y, T(P.radiusTiles ?? 4))) {
          if (o === m || o.elite || o.isBoss) continue;
          o.eliteSpeedMult = P.allySpeedMult ?? 1.2;
          o.attackRateMult = P.allyAttackRateMult ?? 1.25;
          boosted.add(o);
          this.drawLink(m, o);
        }
        break;
      default:
        break;
    }
  }

  /** 불붙은: 지나간 자리 불씨 (주인공만 다침 — 적 피해 없음) */
  private ember(x: number, y: number, P: Record<string, number>): void {
    const r = T(P.trailTiles ?? 0.5);
    const ms = P.trailMs ?? 1000;
    const pool = this.g.pools.add(new Phaser.Geom.Rectangle(x - r, y - r, r * 2, r * 2), {
      owner: 'structure',
      lifeMs: ms,
      playerSlow: 0,
      enemySlow: 0,
      slip: 0,
      fireMs: ms,
      fireTickMs: P.trailTickMs ?? 500,
      firePlayerAttack: Math.max(1, Math.round((P.contactDamage ?? 5) * (P.trailTickMult ?? 0.1) * 10)),
      fireMobDamage: null,
      fireFx: 'fire_pool',
      spreadMsPerCell: null,
      linkGapPx: 0,
      color: 0xe07a2a,
      alpha: 0.2,
    });
    this.g.pools.ignite(pool);
  }

  /** 외곽선(적 바로 아래 같은 프레임) · 문장(머리 위) */
  private draw(r: EliteRec, now: number): void {
    const m = r.mob;
    const o = r.outline;
    if (o) {
      const parsed = m.visual.current ? parseAnimKey(m.visual.current, m.visual.sheetName) : null;
      const tex = parsed ? spriteLibrary.textureKey(m.visual.sheetName, eliteAction(parsed.action)) : null;
      if (tex && this.g.textures.exists(tex)) {
        if (o.texture.key !== tex) o.setTexture(tex);
        const P = BUNDLE2.elite.outlinePulse;
        const t = (Math.sin((now / P.periodMs) * Math.PI * 2) + 1) / 2;
        o.setFrame(m.frame.name)
          .setOrigin(m.originX, m.originY)
          .setScale(m.scaleX, m.scaleY)
          .setFlipX(m.flipX)
          .setPosition(m.x, m.y)
          .setDepth(m.depth - BUNDLE_FX.ELITE_OUTLINE_DEPTH)
          .setAlpha(m.alpha * (P.alphaMin + (P.alphaMax - P.alphaMin) * t))
          .setVisible(m.visible);
      } else o.setVisible(false);
    }
    this.drawBarrel(r, now);
    const e = r.emblem;
    if (!e) return;
    const def = spriteLibrary.sheet(BUILD_ART.ELITE_EMBLEM, FX_ACTION);
    if (!def) return;
    const meta = def as unknown as { kinds?: string[]; headTopByEnemy?: Record<string, number> };
    const row = Math.max(0, meta.kinds?.indexOf(r.def.emblemRow) ?? 0);
    const k = artScale(def);
    const head = (meta.headTopByEnemy?.[m.spriteId] ?? BUNDLE_FX.ELITE_HEAD_TOP_DOTS) * (m.visual.drawScale || 1);
    e.setFrame(String(row * def.frames + Math.min(def.frames - 1, r.emblemCol)))
      .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
      .setScale(k)
      .setPosition(m.x, m.y - (head + BUNDLE_FX.ELITE_EMBLEM_GAP_DOTS) * k)
      .setDepth(DEPTH.HIT_FX - 0.1)
      .setVisible(m.visible);
  }

  /** 통 갑옷 판 (back = 적 아래·외곽선 위 / front = 적 위, bodyBox 자리·배율 × 엘리트 배율, flipX 같이) */
  private drawBarrel(r: EliteRec, now: number): void {
    const m = r.mob;
    const def = spriteLibrary.sheet(BUILD_ART.ELITE_BARREL, FX_ACTION);
    const box = this.bodyBox(BUILD_ART.ELITE_BARREL, m);
    if (!def || !box) return;
    const ek = BUNDLE2.elite.sizeMult;
    const k = artScale(def) * ek;
    const col = now < r.barrelHitUntil ? 1 + (Math.floor(now / 80) % 2) : 0;
    const x = m.x + box.cx * k * (m.flipX ? -1 : 1);
    const y = m.y + (box.cy + 22) * k;
    const place = (s: Phaser.GameObjects.Sprite | null, row: number, depth: number) =>
      s
        ?.setFrame(String(row * def.frames + col))
        .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
        .setScale(artScale(def) * box.scale * ek)
        .setFlipX(m.flipX)
        .setPosition(x, y)
        .setDepth(depth)
        .setVisible(m.visible);
    place(r.barrelBack, 0, m.depth - BUNDLE_FX.ELITE_OUTLINE_DEPTH * 0.5);
    place(r.barrelFront, 1, m.depth + DEPTH.OVERLAY_STEP * 0.5);
  }

  /** 계약 §14.9 이름표 (화면 안의 살아 있는 엘리트) */
  toUi(): UiElite[] {
    const cam = this.g.cameras.main;
    const out: UiElite[] = [];
    for (const r of this.list) {
      const m = r.mob;
      if (!m.active || !m.elite) continue;
      const top = r.emblem?.visible ? r.emblem.getTopCenter().y : m.getTopCenter().y;
      const s = worldToLogicalScreen(cam, m.x, top ?? m.y);
      if (!cam.worldView.contains(m.x, m.y)) continue;
      out.push({
        id: `${m.spriteId}#${this.list.indexOf(r)}`,
        name: m.elite.name,
        prefixes: [r.def.name],
        hp: Math.max(0, Math.round(m.hp)),
        maxHp: m.maxHp,
        screen: { x: Math.round(s.x), y: Math.round(s.y) },
      });
    }
    return out;
  }

  debug(): Record<string, unknown>[] {
    return this.list.map((r) => ({
      id: r.mob.spriteId,
      prefix: r.def.id,
      hp: r.mob.hp,
      maxHp: r.mob.maxHp,
      broken: r.armorBroken,
      enraged: r.enraged,
      drinks: r.drinks,
      outline: r.outline?.visible ?? false,
      emblem: r.emblem?.visible ?? false,
    }));
  }

  destroy(): void {
    for (const r of [...this.list]) this.drop(r);
    this.clearLinks();
    this.boosted.clear();
  }
}

export { prefixDef };
