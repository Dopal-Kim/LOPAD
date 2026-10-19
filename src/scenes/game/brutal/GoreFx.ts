/**
 * P21 피·상처·시체 (계약 dark-brutal §3·§5·§6 · art §37): 적이 맞을 때마다 분출·바닥 데칼·벽 튐, HP 단계에 따라 상처 스탬프·피 젖음·
 * 피 방울·절뚝임, 처치 때 사망 변형(시트 `death_<변형>`)·피 웅덩이·잘린 조각, 시체·데칼 지속(노드당 상한 — 넘치면 오래된 것부터 서서히).
 * 이벤트: ENEMY_GORE(적중마다) · ENEMY_WOUNDED(단계가 오를 때) · ENEMY_DEATH_VARIANT(ENEMY_DIED 바로 뒤).
 * 그림 = 아트 B `fx/v5/*` · `enemies/v4/<적>_death_<변형>`. 시트가 없으면 임시 그림(원 텍스처 방울·데칼, 짧은 막대 상처, 조각 없음).
 * 고어 1 = 피 1/3·더 어둡게·절단 없음 · 0 = 피 대신 먹·재(ink_ash_burst), 데칼·사망 변형 없음.
 * 노드가 바뀌면 씬이 다시 시작하므로 모든 그림은 씬과 함께 사라진다 (shutdown 에서 연결 해제).
 */
import Phaser from 'phaser';
import { BOSSES, ENEMIES } from '../../../data';
import { BRUTAL, DEPTH, TILE } from '../../../core/Constants';
import {
  EventBus,
  Events,
  type DeathVariant,
  type EnemyDeathVariantPayload,
  type EnemyGorePayload,
  type EnemyWoundedPayload,
  type GoreCut,
  type HazardExplodedPayload,
} from '../../../core/EventBus';
import type { UiGoreLevel } from '../../../contract/ui';
import type { Mob } from '../../../objects/Mob';
import { markDeathVariant, setGoreHooks, type GoreHooks, type MobDamageInfo } from '../../../systems/gore/goreHooks';
import {
  CappedList,
  cutOf,
  enemyWoundStage,
  executeVariant,
  goreAmount,
  goreCount,
  goreVariant,
  isGoreWeapon,
  pickDeathVariant,
  severs,
  stampTarget,
} from '../../../systems/gore/rules';
import { settings } from '../../../systems/settings';
import { spriteLibrary } from '../../../systems/sprites/sprites';
import { FX_ACTION, frameStarts } from '../../../systems/sprites/spriteDefs';
import { GORE_FX, deathAction } from './brutalArt';
import { fxSheet, pick, sheetImage } from './goreArt';
import type { Game } from '../../Game';

const TEX_DOT = 'gore_dot';
const TEX_STAMP = 'gore_stamp';
const TEX_POOL = 'gore_pool';
/** 임시 원 텍스처 반지름 (px) */
const DOT_R = 4;
const POOL_R = 16;
/** 상처 스탬프 회전 (베기만 칼길 ±30°) */
const SLASH_TILT = Math.PI / 6;
/** 바닥 데칼 기본 (byCut 이 없을 때) · 끌린 자국 · 절뚝 방울 · 조각 착지 */
const DECAL_ANY = [0, 1, 2, 3];

interface WoundState {
  stage: 0 | 1 | 2;
  /** ox 는 그 순간 보던 쪽 기준 — 좌우가 바뀌면 뒤집는다 */
  stamps: { img: Phaser.GameObjects.Image; ox: number; oy: number; left: boolean }[];
  dripAt: number;
}

interface Pending {
  mob: Mob;
  payload: EnemyDeathVariantPayload;
}

type Decal = Phaser.GameObjects.Image | Phaser.GameObjects.Sprite;
type Corpse = { obj: Decal; shadow: Phaser.GameObjects.Image | null };

function ensureTextures(scene: Phaser.Scene): void {
  if (scene.textures.exists(TEX_DOT)) return;
  const g = scene.make.graphics({}, false);
  g.fillStyle(0xffffff, 1).fillCircle(DOT_R, DOT_R, DOT_R);
  g.generateTexture(TEX_DOT, DOT_R * 2, DOT_R * 2);
  g.clear();
  g.fillStyle(0xffffff, 1).fillRect(0, 0, 8, 2);
  g.generateTexture(TEX_STAMP, 8, 2);
  g.clear();
  // 웅덩이: 가운데 진하고 가장자리 옅은 원 (겹친 원 3장)
  for (const [r, a] of [
    [POOL_R, 0.35],
    [POOL_R * 0.75, 0.6],
    [POOL_R * 0.5, 1],
  ] as const)
    g.fillStyle(0xffffff, a).fillCircle(POOL_R, POOL_R, r);
  g.generateTexture(TEX_POOL, POOL_R * 2, POOL_R * 2);
  g.destroy();
}

const isLeft = (mob: Mob) => mob.visual.facing === 'left' || mob.flipX;

export class GoreFx implements GoreHooks {
  private readonly decals = new CappedList<Decal>(BRUTAL.DECAL.MAX);
  private readonly corpses = new CappedList<Corpse>(BRUTAL.CORPSE.MAX);
  private readonly wounds = new Map<Mob, WoundState>();
  private pending: Pending[] = [];
  private readonly fellZone = new WeakMap<Mob, 'water' | 'drop' | 'fire'>();
  private blasts: { x: number; y: number; at: number }[] = [];
  private lastVariant: DeathVariant | null = null;
  /** 디버그·봇 */
  readonly counts = {
    gore: 0,
    wounded: 0,
    variants: {} as Record<string, number>,
    decals: 0,
    corpses: 0,
    parts: 0,
    sheets: 0,
  };

  constructor(private readonly g: Game) {
    ensureTextures(g);
    setGoreHooks(g, this);
    EventBus.on(Events.ENEMY_DIED, this.flushPending, this);
    EventBus.on(Events.HAZARD_EXPLODED, this.onBlast, this);
    EventBus.on(Events.HAZARD_IGNITED, this.onBlast, this);
    g.events.once(Phaser.Scenes.Events.SHUTDOWN, () => this.destroy());
  }

  private get gore(): UiGoreLevel {
    return settings.current().gore;
  }

  /** HitReactions: 낙하 구역에 밀려 떨어짐 (곧 오는 처치 = 물이면 drown, 불이면 burn) */
  markFell(mob: Mob, zone: 'water' | 'drop' | 'fire'): void {
    this.fellZone.set(mob, zone);
  }

  // --- GoreHooks ---

  onMobDamaged(m: unknown, info: MobDamageInfo): void {
    const mob = m as Mob;
    if (!mob.body) return;
    const len = Math.hypot(info.dirX ?? 0, info.dirY ?? 0);
    const nx = len > 0 ? (info.dirX ?? 0) / len : 0;
    const ny = len > 0 ? (info.dirY ?? 0) / len : 1;
    const weapon = info.cause ? null : isGoreWeapon(info.weapon) ? info.weapon : null;
    const execWeapon = info.cause === 'execute' && isGoreWeapon(info.weapon) ? info.weapon : null;
    const goreWeapon = weapon ?? execWeapon;
    const overkill = info.died ? Math.max(0, info.amount - info.hpBefore) / Math.max(1, mob.maxHp) : 0;
    const c = mob.body.center;
    const lift = mob.visual.hitLiftPx;
    const cut = cutOf(goreWeapon, info.heavy || info.crit);
    if (!info.tick || info.died) {
      const amount = goreAmount({ died: info.died, heavy: info.heavy, crit: info.crit, overkillRatio: overkill });
      const p: EnemyGorePayload = {
        id: mob.spriteId,
        x: c.x,
        y: c.y,
        dirX: +nx.toFixed(3),
        dirY: +ny.toFixed(3),
        weapon: goreWeapon,
        cut,
        amount: execWeapon ? 3 : amount,
      };
      EventBus.emit(Events.ENEMY_GORE, p);
      this.counts.gore += 1;
      this.spray(c.x, c.y - lift, mob.y, nx, ny, cut, p.amount);
      this.wallSplat(c.x, c.y, nx, ny, p.amount);
    }
    if (!info.died) {
      this.wound(mob, nx, ny, cut);
      return;
    }
    this.dropWounds(mob);
    const zone = this.fellZone.get(mob);
    const raw = pickDeathVariant({
      weapon: goreWeapon,
      overkillRatio: overkill,
      wallNear: goreWeapon === 'bow' && this.wallAlong(c.x, c.y, nx, ny, BRUTAL.DEATH.PIN_WALL_TILES) !== null,
      fire: zone === 'fire' || (info.cause === 'hazard' && (info.tick || this.nearBlast(c.x, c.y))),
      drown: zone === 'water',
      execute: execWeapon ? executeVariant(execWeapon) : null,
      boss: mob.isBoss,
    });
    const variant = goreVariant(raw, this.gore);
    const payload: EnemyDeathVariantPayload = {
      id: mob.spriteId,
      x: mob.x,
      y: mob.y,
      kind: mob.spriteId,
      variant,
      dirX: +nx.toFixed(3),
      dirY: +ny.toFixed(3),
      armored: Boolean(ENEMIES[mob.spriteId]?.shield) || mob.damageTakenMult < 1,
      elite: mob.elite !== null,
    };
    markDeathVariant(mob.spriteId);
    this.counts.variants[variant] = (this.counts.variants[variant] ?? 0) + 1;
    // 사망 변형 시체 (art §37 — collapse 도 상처·피 젖음을 그린 시트. 고어 0 은 원래 death. 술독병 폭발처럼 다른 동작이면 그대로)
    const sheetVariant = variant !== 'drown' && this.gore > 0;
    const hasSheet = sheetVariant && Boolean(spriteLibrary.sheet(mob.spriteId, deathAction(variant)));
    if (mob.corpseAction === 'death' && hasSheet) mob.corpseAction = deathAction(variant);
    // 군주는 ENEMY_DIED 가 없다 (BOSS_DIED) — 바로
    if (mob.isBoss) EventBus.emit(Events.ENEMY_DEATH_VARIANT, payload);
    else this.pending.push({ mob, payload });
    if (this.gore > 0 && variant !== 'drown') this.pool(mob.x, mob.y);
    if (this.gore === 2 && severs(variant)) this.parts(mob, variant, nx, ny, hasSheet);
  }

  keepCorpse(name: string, corpse: Phaser.GameObjects.Sprite, shadow: Phaser.GameObjects.Image | null): boolean {
    if (BOSSES[name]) return false;
    // 불탐 시트가 없으면 그을린 틴트
    if (this.lastVariant === 'burn' && !corpse.texture.key.includes('death_burn')) corpse.setTint(0x4a423c);
    this.keep({ obj: corpse, shadow });
    return true;
  }

  /** ENEMY_DIED (Enemy.onDeath 안 — 시체를 남기기 전) → 바로 뒤 DEATH_VARIANT */
  private flushPending(): void {
    const p = this.pending.shift();
    if (!p) return;
    this.lastVariant = p.payload.variant;
    EventBus.emit(Events.ENEMY_DEATH_VARIANT, p.payload);
  }

  private onBlast(p: HazardExplodedPayload | { x: number; y: number }): void {
    this.blasts.push({ x: p.x, y: p.y, at: this.g.time.now });
    if (this.blasts.length > 8) this.blasts.shift();
  }

  private nearBlast(x: number, y: number): boolean {
    const now = this.g.time.now;
    return this.blasts.some((b) => now - b.at < 600 && Math.hypot(b.x - x, b.y - y) < TILE * 4);
  }

  // --- 매 프레임 ---

  update(time: number): void {
    // ENEMY_DIED 를 내지 않는 개체(있다면)의 변형도 놓치지 않는다
    while (this.pending.length > 0) this.flushPending();
    this.lastVariant = null;
    const E = BRUTAL.ENEMY;
    for (const [mob, w] of this.wounds) {
      if (!mob.active || !mob.body) {
        this.dropWounds(mob);
        continue;
      }
      const lift = mob.visual.hitLiftPx;
      const left = isLeft(mob);
      for (const s of w.stamps)
        s.img
          .setPosition(mob.x + (s.left === left ? s.ox : -s.ox), mob.y - lift + s.oy)
          .setDepth(mob.depth + DEPTH.OVERLAY_STEP * 0.5)
          .setVisible(mob.visible);
      // 피 젖음: 다른 상태 색(경직·예고)이 없을 때만
      if (mob.visual.animated && !mob.isTinted && !mob.isBoss) mob.setTint(E.WET_TINT[w.stage]);
      if (w.stage < 2 || mob.isBoss) continue;
      const moving = mob.body.velocity.lengthSq() > 25;
      if (moving && time >= w.dripAt) {
        w.dripAt = time + E.DRIP_MS;
        if (this.gore > 0) this.drip(mob);
      }
    }
  }

  // --- 상처 ---

  private wound(mob: Mob, nx: number, ny: number, cut: GoreCut): void {
    const stage = enemyWoundStage(mob.hp, mob.maxHp);
    let w = this.wounds.get(mob);
    if (stage === 0 && !w) return;
    if (!w) {
      w = { stage: 0, stamps: [], dripAt: 0 };
      this.wounds.set(mob, w);
    }
    if (stage <= w.stage) return;
    w.stage = stage;
    const p: EnemyWoundedPayload = { id: mob.spriteId, x: mob.x, y: mob.y, stage: stage as 1 | 2, kind: mob.spriteId };
    EventBus.emit(Events.ENEMY_WOUNDED, p);
    this.counts.wounded += 1;
    // 군주는 단계 표시만 (절뚝임 없음)
    if (stage === 2 && !mob.isBoss) mob.speedMult *= BRUTAL.ENEMY.LIMP_MULT;
    if (this.gore === 0) return;
    const want = stampTarget(stage, Math.random());
    const hw = mob.body.halfWidth;
    const hh = Math.max(mob.body.halfHeight, mob.visual.hitLiftPx);
    const left = isLeft(mob);
    while (w.stamps.length < want) {
      // art §37 wound_cut: 적중 방향 쪽 몸 가장자리에서 안으로 (공격이 들어온 쪽 = −dir)
      const ox = -nx * hw * 0.45 + (Math.random() - 0.5) * hw * 0.8;
      const oy = -ny * hh * 0.3 + (Math.random() - 0.5) * hh;
      w.stamps.push({ img: this.stampImage(cut, Math.atan2(ny, nx)), ox, oy, left });
    }
  }

  private stampImage(cut: GoreCut, hitAngle: number): Phaser.GameObjects.Image {
    const s = fxSheet(this.g, GORE_FX.WOUND_CUT);
    if (s) {
      const frames = s.def.byCut?.[cut] ?? [0];
      const img = sheetImage(this.g, s, 0, 0, pick(frames));
      // 베기만 칼길 각도 쪽으로 ±30° (나머지는 흘러내림이 아래라 회전 금지)
      if (cut === 'slash')
        img.setRotation(Phaser.Math.Clamp(Phaser.Math.Angle.Wrap(hitAngle), -SLASH_TILT, SLASH_TILT));
      if (this.gore === 1) img.setTint(BRUTAL.GORE1.TINT);
      return img;
    }
    const E = BRUTAL.ENEMY;
    const len = E.STAMP_LEN_PX[0] + Math.random() * (E.STAMP_LEN_PX[1] - E.STAMP_LEN_PX[0]);
    return this.g.add
      .image(0, 0, TEX_STAMP)
      .setTint(this.gore === 1 ? BRUTAL.DECAL.DARK_COLOR : E.STAMP_COLOR)
      .setScale(len / 8, 0.5)
      .setRotation(hitAngle + Math.PI / 2 + (Math.random() - 0.5));
  }

  private dropWounds(mob: Mob): void {
    const w = this.wounds.get(mob);
    if (!w) return;
    for (const s of w.stamps) s.img.destroy();
    this.wounds.delete(mob);
  }

  /** stage 2 피 방울: blood_drip(상처에서 맺혀 떨어져 퍼짐 — 바닥 = 피벗 아래 floorDots) + 발밑 절뚝 데칼 */
  private drip(mob: Mob): void {
    const x = mob.x + (Math.random() - 0.5) * 4;
    const s = fxSheet(this.g, GORE_FX.DRIP);
    if (s && this.g.fx.has(GORE_FX.DRIP)) {
      const fall = (s.def.floorDots ?? 50) * s.scale;
      this.g.fx.play(GORE_FX.DRIP, x, mob.y - fall, { depth: DEPTH.FX_GROUND, hooks: false });
    }
    this.decal(x, mob.y, 0.7, 'limp');
  }

  // --- 피 ---

  /**
   * 분출: v5 `blood_spray_<cut>`(행 = amount, 오른쪽 기준 → 진행 방향으로 회전, 무작위 flipY) + 떨어진 자리 바닥 데칼(decalHint — 분출
   * spawnAtFrame 무렵). 시트가 없으면 날아가 떨어지는 원 방울
   */
  private spray(x: number, y: number, floorY: number, nx: number, ny: number, cut: GoreCut, amount: 1 | 2 | 3): void {
    const gore = this.gore;
    const g = this.g;
    if (gore === 0) {
      this.inkBurst(x, y, nx, ny, amount);
      return;
    }
    const id = GORE_FX.spray(cut);
    const angle = Math.atan2(ny, nx);
    const s = fxSheet(g, id);
    const D = BRUTAL.DECAL;
    if (s && g.fx.has(id)) {
      // 고어 1 = amount1 행만 + 어둡게 (art §37)
      const row = gore === 1 ? 1 : amount;
      const h = g.fx.play(id, x, y, {
        dir: `amount${row}`,
        angle,
        depth: DEPTH.HIT_FX,
        tint: gore === 1 ? BRUTAL.GORE1.TINT : undefined,
        hooks: false,
      });
      h?.sprite.setFlipY(Math.random() < 0.5);
      this.counts.sheets += 1;
      const hint = s.def.decalHint;
      const n = goreCount(hint?.count[amount - 1] ?? D.PER_HIT[amount], gore, Math.random());
      const [d0, d1] = hint?.distDots ?? [20, 70];
      const atMs = hint ? (frameStarts(s.def)[hint.spawnAtFrame] ?? 0) : 0;
      for (let i = 0; i < n; i++) {
        const a = angle + (Math.random() - 0.5) * 0.7;
        const d = (d0 + Math.random() * (d1 - d0)) * s.scale;
        // 데칼은 바닥(발 높이)에: 적중점 높이 − 바닥 사이를 진행 방향 거리로 메운다
        const tx = x + Math.cos(a) * d;
        const ty = floorY + Math.sin(a) * d * 0.6;
        g.time.delayedCall(atMs, () => {
          if (this.g.scene.isActive()) this.decal(tx, ty, 1, cut, a);
        });
      }
      return;
    }
    const n = goreCount(D.PER_HIT[amount], gore, Math.random());
    const color = gore === 1 ? D.DARK_COLOR : D.COLOR;
    for (let i = 0; i < n; i++) {
      const a = angle + (Math.random() - 0.5) * 1.1;
      const d = D.SPRAY_PX * (0.35 + Math.random() * 0.65) * (0.7 + amount * 0.25);
      const tx = x + Math.cos(a) * d;
      const ty = floorY + Math.sin(a) * d * 0.6;
      const r = D.RADIUS_PX[0] + Math.random() * (D.RADIUS_PX[1] - D.RADIUS_PX[0]);
      const drop = g.add
        .image(x, y, TEX_DOT)
        .setTint(color)
        .setScale((r * 0.6) / DOT_R)
        .setDepth(DEPTH.HIT_FX);
      g.tweens.add({
        targets: drop,
        x: tx,
        y: ty,
        duration: 160 + Math.random() * 140,
        ease: Phaser.Math.Easing.Quadratic.Out,
        onComplete: () => {
          drop.destroy();
          if (this.g.scene.isActive()) this.decal(tx, ty, r / DOT_R, cut, a);
        },
      });
    }
  }

  /** 고어 0: 피 대신 먹·재 (ink_ash_burst — 오른쪽 기준 회전, 데칼 없음). 시트가 없으면 회색·검정 점 */
  private inkBurst(x: number, y: number, nx: number, ny: number, amount: number): void {
    const g = this.g;
    if (g.fx.has(GORE_FX.INK_ASH)) {
      g.fx
        .play(GORE_FX.INK_ASH, x, y, { angle: Math.atan2(ny, nx), depth: DEPTH.HIT_FX, hooks: false })
        ?.sprite.setFlipY(Math.random() < 0.5);
      return;
    }
    for (let i = 0; i < 2 + amount * 2; i++) {
      const a = Math.atan2(ny, nx) + (Math.random() - 0.5) * 1.4;
      const d = 6 + Math.random() * 14;
      const dot = g.add
        .image(x, y, TEX_DOT)
        .setTint(i % 2 ? BRUTAL.GORE0.ASH : BRUTAL.GORE0.INK)
        .setScale(0.3 + Math.random() * 0.3)
        .setDepth(DEPTH.HIT_FX);
      g.tweens.add({
        targets: dot,
        x: x + Math.cos(a) * d,
        y: y + Math.sin(a) * d - 4,
        alpha: 0,
        duration: 360 + Math.random() * 200,
        onComplete: () => dot.destroy(),
      });
    }
  }

  /** 벽 근처(1칸)에서 맞으면 벽 튐 데칼 (blood_decal_wall 6 — 회전 금지, flipX 허용) */
  private wallSplat(x: number, y: number, nx: number, ny: number, amount: number): void {
    if (this.gore === 0 || amount < 2 || (nx === 0 && ny === 0)) return;
    const at = this.wallAlong(x, y, nx, ny, BRUTAL.DECAL.WALL_TILES);
    if (!at) return;
    const s = fxSheet(this.g, GORE_FX.DECAL_WALL);
    if (!s) {
      this.decal(at.x, at.y, 1.2, null, 0, true);
      return;
    }
    // shortcut: 흘러내린 줄을 벽 앞면 높이로 자르지 않는다 — 벽 앞면 높이 API 가 생기면 마스크
    const img = sheetImage(this.g, s, at.x, at.y, Math.floor(Math.random() * s.def.frames))
      .setFlipX(Math.random() < 0.5)
      .setDepth(DEPTH.ENTITY + at.y * DEPTH.ENTITY_Y_SCALE - DEPTH.OVERLAY_STEP);
    if (this.gore === 1) img.setTint(BRUTAL.GORE1.TINT);
    this.pushDecal(img);
  }

  /** (x, y) 에서 dir 쪽으로 maxTiles 안에 걸을 수 없는 칸이 있으면 그 바로 앞 자리 */
  private wallAlong(x: number, y: number, nx: number, ny: number, maxTiles: number): { x: number; y: number } | null {
    const w = this.g.world;
    const step = TILE / 4;
    for (let d = step; d <= maxTiles * TILE; d += step) {
      const px = x + nx * d;
      const py = y + ny * d;
      if (!w.isWalkableAt(px, py)) return { x: px - nx * step, y: py - ny * step };
    }
    return null;
  }

  /** 시체 밑 웅덩이: blood_pool(v0~v2 — 프레임이 퍼짐을 그린다, 스케일 트윈 없이 마지막 프레임 유지). 없으면 원이 1.5초에 퍼짐 */
  private pool(x: number, y: number): void {
    const D = BRUTAL.DECAL;
    const g = this.g;
    const s = fxSheet(g, GORE_FX.POOL);
    if (s) {
      const row = pick(['v0', 'v1', 'v2']);
      const anim = spriteLibrary.animKey(GORE_FX.POOL, FX_ACTION, row);
      const spr = g.add
        .sprite(x, y + 2, s.key, 0)
        .setOrigin(s.def.pivot.x / s.def.frameWidth, s.def.pivot.y / s.def.frameHeight)
        .setScale(s.scale)
        .setFlipX(Math.random() < 0.5)
        .setDepth(D.POOL_DEPTH);
      if (anim && g.anims.exists(anim)) spr.play(anim);
      if (this.gore === 1) spr.setTint(BRUTAL.GORE1.TINT);
      this.pushDecal(spr);
      return;
    }
    const img = this.decal(x, y + 2, 1, 'pool', 0, false, D.POOL_DEPTH);
    if (!img) return;
    const full = img.scaleX;
    img.setScale(full * D.POOL_SCALE0);
    g.tweens.add({ targets: img, scaleX: full, scaleY: full * 0.6, duration: D.POOL_MS, ease: 'Sine.easeOut' });
  }

  /**
   * 바닥 데칼 하나 (그림자 위·몸 아래). blood_decal_floor 가 있으면 kind(결·drag·limp·pool_small)의 byCut 프레임 —
   * directional 프레임은 angle(피가 날아간 방향)로 돌리고, 나머지는 무작위 회전·flip. 없으면 임시 원.
   */
  private decal(
    x: number,
    y: number,
    scale: number,
    kind: string | null,
    angle = 0,
    wall = false,
    depth: number = BRUTAL.DECAL.DEPTH,
  ): Decal | null {
    if (this.gore === 0) return null;
    const g = this.g;
    const D = BRUTAL.DECAL;
    const s = !wall && kind !== 'pool' ? fxSheet(g, GORE_FX.DECAL_FLOOR) : null;
    let img: Phaser.GameObjects.Image;
    if (s) {
      const frames = (kind && s.def.byCut?.[kind]) || DECAL_ANY;
      const f = pick(frames);
      img = sheetImage(g, s, x, y, f);
      if (s.def.directional?.includes(f)) img.setRotation(angle);
      else img.setRotation(Math.random() * Math.PI * 2).setFlipX(Math.random() < 0.5);
      if (this.gore === 1) img.setTint(BRUTAL.GORE1.TINT);
    } else {
      const pool = kind === 'pool';
      const r = pool ? D.POOL_RADIUS_PX : D.RADIUS_PX[0] + Math.random() * (D.RADIUS_PX[1] - D.RADIUS_PX[0]);
      const k = (pool ? r / POOL_R : r / DOT_R) * scale;
      img = g.add
        .image(x, y, pool ? TEX_POOL : TEX_DOT)
        .setTint(this.gore === 1 ? D.DARK_COLOR : D.COLOR)
        .setScale(pool ? k : k / 1.5, k * 0.6)
        .setAlpha(pool ? 0.85 : 0.9)
        .setRotation(wall ? 0 : Math.random() * Math.PI);
    }
    img.setDepth(wall ? DEPTH.ENTITY + y * DEPTH.ENTITY_Y_SCALE - DEPTH.OVERLAY_STEP : depth);
    this.pushDecal(img);
    return img;
  }

  private pushDecal(img: Decal): void {
    this.counts.decals += 1;
    for (const old of this.decals.push(img)) this.fadeOut(old, BRUTAL.DECAL.FADE_MS);
  }

  // --- 시체·조각 ---

  private keep(c: Corpse): void {
    this.counts.corpses += 1;
    for (const old of this.corpses.push(c)) {
      const targets = old.shadow ? [old.obj, old.shadow] : [old.obj];
      this.g.tweens.add({
        targets,
        alpha: 0,
        duration: BRUTAL.CORPSE.FADE_MS,
        // 어둡게 사라짐 (밝기 1 → 0.3)
        onUpdate: (tw) => {
          const v = Math.round(255 * (1 - tw.progress * 0.7));
          old.obj.setTint((v << 16) | (v << 8) | v);
        },
        onComplete: () => {
          old.obj.destroy();
          old.shadow?.destroy();
        },
      });
    }
  }

  /**
   * 잘린 조각 `gore_parts_<적>` (행 head·arm·upper, 열 45° 회전 8장 50ms 루프 → 멈추면 restFrame). 적 피벗 + spawnFromEnemyPivot 에서
   * physicsHint 대로 짧게 날아 튀고 바닥에 남아 시체 수에 든다. behead = 머리 · bisect = 팔(윗몸은 사망 변형 시트가 그린다 — 시트가 없으면 윗몸).
   * 떨어진 자리에 바닥 데칼 + 끌린 자국. 시트가 없으면 조각 없음
   */
  private parts(mob: Mob, variant: DeathVariant, nx: number, ny: number, deathSheet: boolean): void {
    const g = this.g;
    const s = fxSheet(g, GORE_FX.parts(mob.spriteId));
    if (!s) return;
    const rows = s.def.directions;
    const kinds = variant === 'behead' ? ['head'] : deathSheet ? ['arm'] : ['upper', 'arm'];
    const P = s.def.physicsHint;
    const C = BRUTAL.CORPSE;
    const left = isLeft(mob);
    for (const kind of kinds) {
      const row = rows.indexOf(kind);
      if (row < 0) continue;
      const sp = s.def.spawnFromEnemyPivot?.[kind] ?? { x: 0, y: -60 };
      const sx = mob.x + (left ? -sp.x : sp.x) * s.scale;
      const sy = mob.y + sp.y * s.scale;
      const ms = P ? P.flightMs[0] + Math.random() * (P.flightMs[1] - P.flightMs[0]) : C.PART_MS[0];
      const speed = P ? (P.speedDots[0] + Math.random() * (P.speedDots[1] - P.speedDots[0])) * s.scale : C.PART_PX[1];
      const up = P ? (P.upDots[0] + Math.random() * (P.upDots[1] - P.upDots[0])) * s.scale : C.PART_LIFT_PX;
      const a = Math.atan2(ny, nx) + (Math.random() - 0.5) * 0.9;
      const dist = (speed * ms) / 1000;
      const tx = mob.x + Math.cos(a) * dist;
      const ty = mob.y + Math.sin(a) * dist * 0.6;
      const cols = s.def.frames;
      const img = sheetImage(g, s, sx, sy, row * cols).setDepth(DEPTH.ENTITY + ty * DEPTH.ENTITY_Y_SCALE);
      const rest = row * cols + (s.def.restFrame?.[kind] ?? 0);
      const bounce = (P?.bounce ?? 0) > 0;
      g.tweens.addCounter({
        from: 0,
        to: 1,
        duration: ms,
        onUpdate: (tw) => {
          const t = tw.getValue() ?? 0;
          // 머리 높이 sy → 바닥 ty 로 떨어지며 포물선 + (튐 1번: 끝 25% 에 작은 호)
          const arc =
            Math.sin(Math.min(1, t / 0.75) * Math.PI) * up +
            (bounce && t > 0.75 ? Math.sin(((t - 0.75) / 0.25) * Math.PI) * up * 0.3 : 0);
          const fall = sy + (ty - sy) * Math.min(1, t / 0.75);
          img.setPosition(sx + (tx - sx) * t, fall - arc);
          img.setFrame(row * cols + (Math.floor((t * ms) / 50) % cols));
        },
        onComplete: () => {
          img.setFrame(rest).setPosition(tx, ty);
          if (!this.g.scene.isActive()) return;
          this.decal(tx, ty + 1, 1, null);
          this.decal(tx - Math.cos(a) * 6, ty - Math.sin(a) * 4, 1, 'drag', a);
        },
      });
      this.counts.parts += 1;
      this.keep({ obj: img, shadow: null });
    }
  }

  private fadeOut(obj: Decal, ms: number): void {
    this.g.tweens.add({ targets: obj, alpha: 0, duration: ms, onComplete: () => obj.destroy() });
  }

  /** 디버그 */
  summary(): Record<string, unknown> {
    return {
      ...this.counts,
      liveDecals: this.decals.size,
      liveCorpses: this.corpses.size,
      woundedNow: this.wounds.size,
    };
  }

  destroy(): void {
    setGoreHooks(this.g, null);
    EventBus.off(Events.ENEMY_DIED, this.flushPending, this);
    EventBus.off(Events.HAZARD_EXPLODED, this.onBlast, this);
    EventBus.off(Events.HAZARD_IGNITED, this.onBlast, this);
    this.decals.clear();
    this.corpses.clear();
    this.wounds.clear();
    this.pending = [];
  }
}
