/**
 * 61라운드 단계 2 (P3·SY-5): 1층 신규 적의 위험물 — 보스 '불붙은 술'·'술통 되치기' 예습 (계약 art §23).
 * - 화염 술병(독주 행상): 손 높이에서 포물선(fire_bottle_thrown) → 착지 폭발(fire_bottle_burst, 반경 안 주인공 피해)
 *   → 불 웅덩이(fire_pool, 주인공 틱 피해). 폭발이 술 웅덩이에 닿으면 술불(불 연계)
 * - 술통(술통 짐꾼): 직선으로 굴러간다(porter_rolling_barrel, 행 = 방향 · 열 = 굴러간 거리/둘레). 주인공에 닿으면 피해 후 깨짐,
 *   주인공이 치면(근접 판정·화살·패링) 되친 술통(porter_rolling_barrel_returned)이 되어 적에게 굴러가 피해·경직 후 깨짐.
 *   벽·단단한 구조물(걸을 수 없는 칸)·최대 거리에서 깨짐(porter_barrel_break) → 술 웅덩이(pool_liquor, 불이 닿으면 pool_liquor_fire)
 * - 술 웅덩이: 쓰러진 행상·짐꾼 자리에도 (미끄러움·감속, 불붙으면 주인공·적 모두 틱 피해)
 * 시계는 씬 update 의 delta 로만 진행한다 — 히트스톱·메뉴 정지 동안 멈춘다. 시트가 없으면 플레이스홀더 도형.
 */
import Phaser from 'phaser';
import { BUILD_ART, DEPTH, ENEMY_HAZARD, TILE, entityDepth } from '../../core/Constants';
import { EventBus, Events, type EnemyAttackPayload, type EnemyAttackPhase } from '../../core/EventBus';
import type { LiquorPoolParams, RollParams } from '../../data/enemyTypes';
import type { Mob } from '../../objects/Mob';
import type { Projectile } from '../../objects/Projectile';
import type { HitResult } from '../../objects/Player';
import type { FxPool } from '../fx/fx';
import { spriteLibrary } from '../sprites/sprites';
import { FX_ACTION, STRUCTURE_ACTION, artScale, facingOf, frameDurations } from '../sprites/spriteDefs';
import type { TelegraphFx } from '../telegraph';
import { caskCircumferenceWorld } from '../boss/caskMath';
import type { LiquorPools, PoolSpec } from './LiquorPools';
import type { BottleParams, EnemyHazardApi, HazardPt } from './enemyHazardTypes';
import { advanceBarrel, bottleArcAt, circleHitsRect, deflectDir, rollFrame, unit } from './hazardMath';

export interface EnemyHazardHost {
  scene: Phaser.Scene;
  world: { isWalkableAt(x: number, y: number): boolean };
  player: {
    body: Phaser.Physics.Arcade.Body;
    takeHit(attack: number, time: number, source?: { dirX: number; dirY: number }): HitResult;
  };
  mobs: Phaser.Physics.Arcade.Group;
  fx: FxPool;
  pools: LiquorPools;
  telegraph: TelegraphFx;
  hitMob(m: Mob, dmg: number, o: { crit: boolean; dirX: number; dirY: number; tick?: boolean }): boolean;
  onKill(m: Mob, kind: 'environment'): void;
  shake(px: number, ms: number): void;
}

interface Bottle {
  from: HazardPt;
  to: HazardPt;
  handPx: number;
  apexPx: number;
  elapsed: number;
  p: BottleParams;
  attackScale: number;
  view: ReturnType<FxPool['play']>;
  dot: Phaser.GameObjects.Arc | null;
  shadow: Phaser.GameObjects.Ellipse;
  /** 61 단계 5 (P13 개성 '쳐내기'): 주인공이 되쳐 보낸 술병 — 터지면 적만 다친다 */
  owner?: 'enemy' | 'player';
}

interface Barrel {
  x: number;
  y: number;
  dir: HazardPt;
  speedPx: number;
  radiusPx: number;
  traveled: number;
  rolled: number;
  owner: 'enemy' | 'player';
  p: RollParams;
  liquor: LiquorPoolParams;
  attackScale: number;
  view: Phaser.GameObjects.Sprite | Phaser.GameObjects.Graphics;
  /** 다시 칠 수 있는 시각 · 주인공을 다시 때릴 수 있는 시각 */
  redirectAt: number;
  playerHitAt: number;
  dead: boolean;
}

interface Breaking {
  sprite: Phaser.GameObjects.Sprite;
  durations: number[];
  elapsed: number;
  frame: number;
  /** 마지막 프레임(stateHold)에 들어설 때 술 웅덩이 (아트 handoff) — 한 번 */
  spill: (() => void) | null;
}

export class EnemyHazards implements EnemyHazardApi {
  private readonly bottles: Bottle[] = [];
  private readonly barrels: Barrel[] = [];
  private readonly breaking: Breaking[] = [];
  /** 디버그 */
  readonly stats = {
    thrown: 0,
    bursts: 0,
    rolled: 0,
    deflected: 0,
    broken: 0,
    returnedHits: 0,
    pools: 0,
    returnedBottles: 0,
  };
  private clock = 0;

  constructor(private readonly host: EnemyHazardHost) {}

  /** 히트스톱·정지에 함께 멈추는 이 시스템 시계 (ms) */
  private get now(): number {
    return this.clock;
  }

  // --- 화염 술병 ---

  throwBottle(from: HazardPt, handPx: number, to: HazardPt, p: BottleParams, attackScale: number): void {
    const H = this.host;
    const start = bottleArcAt(0, from, to, p.arcTiles * TILE, handPx);
    const view = H.fx.has(BOTTLE_THROWN)
      ? H.fx.play(BOTTLE_THROWN, start.x, start.y, { depth: DEPTH.PROJECTILE, flipX: to.x < from.x, hooks: false })
      : null;
    const D = ENEMY_HAZARD.BOTTLE_DOT;
    const dot = view ? null : H.scene.add.circle(start.x, start.y, D.R, D.COLOR).setDepth(DEPTH.PROJECTILE);
    const S = ENEMY_HAZARD.BOTTLE_SHADOW;
    const shadow = H.scene.add.ellipse(from.x, from.y, S.W, S.H, 0x000000, S.ALPHA).setDepth(DEPTH.SHADOW);
    this.bottles.push({ from, to, handPx, apexPx: p.arcTiles * TILE, elapsed: 0, p, attackScale, view, dot, shadow });
    this.stats.thrown++;
  }

  /**
   * 61 단계 5 (P13 개성 '쳐내기'·공명): 날아가는 적 술병 중 (x,y) 반경 안 것을 되쳐 보낸다 — 지금 자리에서 던진 쪽(행상 자리)으로
   * 다시 포물선, 터지면 적만 다친다. 되친 수
   */
  returnBottlesNear(x: number, y: number, radiusPx: number, attackMult = 1): number {
    let n = 0;
    for (const b of this.bottles) {
      if (b.owner === 'player') continue;
      const t = b.elapsed / Math.max(1, b.p.flightMs);
      const at = bottleArcAt(t, b.from, b.to, b.apexPx, b.handPx);
      if (Math.hypot(at.x - x, at.groundY - y) > radiusPx) continue;
      const back = { x: b.from.x, y: b.from.y };
      b.from = { x: at.x, y: at.groundY };
      b.to = back;
      b.handPx = Math.max(0, at.groundY - at.y);
      b.elapsed = 0;
      b.owner = 'player';
      b.attackScale *= attackMult;
      if (b.view) b.view.sprite.setFlipX(back.x < b.from.x);
      n += 1;
    }
    return n;
  }

  private stepBottles(delta: number): void {
    for (const b of this.bottles) {
      b.elapsed += delta;
      const t = b.elapsed / Math.max(1, b.p.flightMs);
      const at = bottleArcAt(t, b.from, b.to, b.apexPx, b.handPx);
      b.view?.sprite.setPosition(at.x, at.y);
      b.dot?.setPosition(at.x, at.y);
      b.shadow.setPosition(at.x, at.groundY);
    }
    for (let i = this.bottles.length - 1; i >= 0; i--) {
      const b = this.bottles[i];
      if (b.elapsed < b.p.flightMs) continue;
      this.bottles.splice(i, 1);
      this.clearBottle(b);
      this.burst(b);
    }
  }

  private clearBottle(b: Bottle): void {
    if (b.view && this.host.fx.isActive(b.view)) this.host.fx.stop(b.view, 0, false);
    b.dot?.destroy();
    b.shadow.destroy();
  }

  /** 착지: 폭발 그림 · 반경 안 주인공 피해 · 불 웅덩이 · 술 웅덩이 점화 */
  private burst(b: Bottle): void {
    const H = this.host;
    const { x, y } = b.to;
    const r = b.p.burstRadiusTiles * TILE;
    const bd = spriteLibrary.sheet(BOTTLE_BURST, FX_ACTION);
    const dots = (bd as unknown as { radiusPx?: number } | undefined)?.radiusPx;
    if (bd && H.fx.has(BOTTLE_BURST))
      H.fx.play(BOTTLE_BURST, x, y, { depth: DEPTH.HIT_FX, scaleMult: dots ? r / (dots * artScale(bd)) : 1 });
    this.stats.bursts++;
    sound('peddler', 'throw', 'burst');
    if (b.owner === 'player') {
      this.returnedBurst(b, r);
      return;
    }
    const c = H.player.body.center;
    if (Math.hypot(c.x - x, c.y - y) <= r + H.player.body.halfWidth) {
      const d = unit(c.x - x, c.y - y);
      H.player.takeHit(Math.round(b.p.burstAttack * b.attackScale), this.host.scene.time.now, { dirX: d.x, dirY: d.y });
    }
    const side = r * 2;
    const rect = new Phaser.Geom.Rectangle(x - r, y - r, side, side);
    const pool = H.pools.add(rect, {
      owner: 'structure',
      lifeMs: b.p.poolMs,
      playerSlow: 0,
      enemySlow: 0,
      slip: 0,
      fireMs: b.p.poolMs,
      fireTickMs: b.p.poolTickMs,
      firePlayerAttack: Math.max(1, Math.round(b.p.poolAttack * b.attackScale)),
      // 적의 불은 주인공만 노린다 (술불 연계는 술 웅덩이 쪽)
      fireMobDamage: null,
      fireFx: FIRE_POOL,
      spreadMsPerCell: null,
      linkGapPx: 0,
      color: ENEMY_HAZARD.FIRE_COLOR,
      alpha: ENEMY_HAZARD.FIRE_ALPHA,
    });
    H.pools.ignite(pool);
    H.pools.igniteIn(rect);
  }

  /** 되친 술병이 터짐: 반경 안 적 피해 · 적만 태우는 불 웅덩이 · 술 웅덩이 점화 */
  private returnedBurst(b: Bottle, r: number): void {
    const H = this.host;
    const { x, y } = b.to;
    const dmg = Math.max(1, Math.round(b.p.burstAttack * b.attackScale));
    for (const child of H.mobs.getChildren()) {
      const m = child as Mob;
      if (!m.active) continue;
      const c = m.body.center;
      if (Math.hypot(c.x - x, c.y - y) > r + m.body.halfWidth) continue;
      const d = unit(c.x - x, c.y - y);
      if (H.hitMob(m, dmg, { crit: false, dirX: d.x, dirY: d.y })) H.onKill(m, 'environment');
    }
    const side = r * 2;
    const rect = new Phaser.Geom.Rectangle(x - r, y - r, side, side);
    const tick = Math.max(1, Math.round(b.p.poolAttack * b.attackScale));
    const pool = H.pools.add(rect, {
      owner: 'structure',
      lifeMs: b.p.poolMs,
      playerSlow: 0,
      enemySlow: 0,
      slip: 0,
      fireMs: b.p.poolMs,
      fireTickMs: b.p.poolTickMs,
      firePlayerAttack: 0,
      fireMobDamage: () => tick,
      fireFx: FIRE_POOL,
      spreadMsPerCell: null,
      linkGapPx: 0,
      color: ENEMY_HAZARD.FIRE_COLOR,
      alpha: ENEMY_HAZARD.FIRE_ALPHA,
    });
    H.pools.ignite(pool);
    H.pools.igniteIn(rect);
    this.stats.returnedBottles++;
  }

  // --- 술통 ---

  rollBarrel(
    from: HazardPt,
    dirX: number,
    dirY: number,
    p: RollParams,
    liquor: LiquorPoolParams,
    attackScale: number,
  ): void {
    const dir = unit(dirX, dirY);
    const b: Barrel = {
      x: from.x,
      y: from.y,
      dir,
      speedPx: p.speedTiles * TILE,
      radiusPx: p.radiusTiles * TILE,
      traveled: 0,
      rolled: 0,
      owner: 'enemy',
      p,
      liquor,
      attackScale,
      view: this.barrelView(from.x, from.y, ENEMY_HAZARD.BARREL, p.radiusTiles * TILE),
      redirectAt: 0,
      playerHitAt: 0,
      dead: false,
    };
    this.barrels.push(b);
    this.stats.rolled++;
    this.spin(b, 0);
    sound('porter', 'roll', 'push');
  }

  private barrelView(x: number, y: number, sheet: string, r: number): Barrel['view'] {
    const sc = this.host.scene;
    const def = spriteLibrary.sheet(sheet, STRUCTURE_ACTION);
    const tex = spriteLibrary.textureKey(sheet, STRUCTURE_ACTION);
    if (def && tex && sc.textures.exists(tex))
      return sc.add
        .sprite(x, y, tex, 0)
        .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
        .setScale(artScale(def))
        .setDepth(entityDepth(y));
    const H = ENEMY_HAZARD;
    const g = sc.add.graphics().setPosition(x, y).setDepth(entityDepth(y));
    g.fillStyle(sheet === H.BARREL_RETURNED ? H.BARREL_RETURNED_COLOR : H.BARREL_COLOR, 1).fillCircle(0, -r, r);
    g.lineStyle(1, H.BARREL_BAND, 1).lineBetween(-r, -r, r, -r);
    return g;
  }

  /** 되치기: 주인 = 주인공, 되친 술통 그림(같은 열 번호), 속도 배율 */
  private deflect(b: Barrel, attackDir: HazardPt): boolean {
    if (b.dead || b.owner !== 'enemy' || this.now < b.redirectAt) return false;
    b.dir = deflectDir(b.dir, attackDir);
    b.owner = 'player';
    b.speedPx *= b.p.returnSpeedMult;
    b.traveled = 0;
    b.redirectAt = this.now + ENEMY_HAZARD.REDIRECT_COOLDOWN_MS;
    const old = b.view;
    b.view = this.barrelView(b.x, b.y, ENEMY_HAZARD.BARREL_RETURNED, b.radiusPx);
    old.destroy();
    this.spin(b, 0);
    this.stats.deflected++;
    sound('porter', 'roll', 'return');
    return true;
  }

  private stepBarrels(delta: number): void {
    const H = this.host;
    for (const b of this.barrels) {
      if (b.dead) continue;
      const step = advanceBarrel(
        b,
        b.dir,
        (b.speedPx * delta) / 1000,
        b.radiusPx,
        (x, y) => !H.world.isWalkableAt(x, y),
      );
      b.x = step.x;
      b.y = step.y;
      b.traveled += step.moved;
      this.spin(b, step.moved);
      if (step.hit || b.traveled >= b.p.maxTiles * TILE) {
        this.shatter(b);
        continue;
      }
      if (b.owner === 'enemy') this.touchPlayer(b);
      else this.touchMobs(b);
    }
    for (let i = this.barrels.length - 1; i >= 0; i--) if (this.barrels[i].dead) this.barrels.splice(i, 1);
    // 굴러가는 술통이 하나도 없으면 굴림 루프 끝
    if (this.barrels.length === 0) sound('porter', 'roll', 'rollEnd');
  }

  private bodyRect(body: Phaser.Physics.Arcade.Body) {
    return { x: body.x, y: body.y, w: body.width, h: body.height };
  }

  /** 술통 판정 원 중심 (그림 피벗 = 바닥 접점 → 반경만큼 위) */
  private center(b: Barrel): HazardPt {
    return { x: b.x, y: b.y - b.radiusPx };
  }

  private touchPlayer(b: Barrel): void {
    const H = this.host;
    if (this.now < b.playerHitAt || !circleHitsRect(this.center(b), b.radiusPx, this.bodyRect(H.player.body))) return;
    b.playerHitAt = this.now + ENEMY_HAZARD.PLAYER_REHIT_MS;
    const res = H.player.takeHit(Math.round(b.p.attack * b.attackScale), H.scene.time.now, {
      dirX: b.dir.x,
      dirY: b.dir.y,
    });
    // 패링 = 되치기 (굴러오던 반대로) · 무적으로 흘렸으면 지나간다 · 맞으면 깨짐
    if (res === 'parried') this.deflect(b, { x: -b.dir.x, y: -b.dir.y });
    else if (res !== 'ignored') this.shatter(b);
  }

  private touchMobs(b: Barrel): void {
    const H = this.host;
    for (const ch of H.mobs.getChildren()) {
      const m = ch as Mob;
      if (!m.active || !circleHitsRect(this.center(b), b.radiusPx, this.bodyRect(m.body))) continue;
      this.stats.returnedHits++;
      if (H.hitMob(m, b.p.returnDamage, { crit: false, dirX: b.dir.x, dirY: b.dir.y })) H.onKill(m, 'environment');
      else m.stun(H.scene.time.now, b.p.returnStunMs, 'hit');
      this.shatter(b);
      return;
    }
  }

  private spin(b: Barrel, dist: number): void {
    b.rolled += dist;
    b.view.setPosition(b.x, b.y).setDepth(entityDepth(b.y));
    if (!(b.view instanceof Phaser.GameObjects.Sprite)) return;
    const sheet = b.owner === 'player' ? ENEMY_HAZARD.BARREL_RETURNED : ENEMY_HAZARD.BARREL;
    const def = spriteLibrary.sheet(sheet, STRUCTURE_ACTION);
    if (!def) return;
    const row = Math.max(0, def.directions.indexOf(facingOf(b.dir.x, b.dir.y, 'down')));
    const circ = caskCircumferenceWorld(def) ?? def.frameWidth * artScale(def);
    b.view.setFrame(row * def.frames + rollFrame(b.rolled, circ, def.frames));
  }

  /** 깨짐: 깨짐 그림(마지막 프레임 유지) → 같은 피벗에 술 웅덩이 */
  private shatter(b: Barrel): void {
    if (b.dead) return;
    b.dead = true;
    b.view.destroy();
    this.stats.broken++;
    const H = this.host;
    const S = ENEMY_HAZARD.BREAK_SHAKE;
    H.shake(S.PX, S.MS);
    sound('porter', 'roll', 'break');
    const spill = () => {
      this.liquorPool(b.x, b.y - b.radiusPx, b.p.breakPoolTiles * TILE, b.p.breakPoolMs, b.liquor, b.attackScale);
      sound('porter', 'roll', 'spill');
    };
    const def = spriteLibrary.sheet(ENEMY_HAZARD.BARREL_BREAK, STRUCTURE_ACTION);
    const tex = spriteLibrary.textureKey(ENEMY_HAZARD.BARREL_BREAK, STRUCTURE_ACTION);
    if (def && tex && H.scene.textures.exists(tex)) {
      const sprite = H.scene.add
        .sprite(b.x, b.y, tex, 0)
        .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
        .setScale(artScale(def))
        .setDepth(entityDepth(b.y));
      this.breaking.push({ sprite, durations: frameDurations(def), elapsed: 0, frame: 0, spill });
    } else spill();
  }

  private stepBreaking(delta: number): void {
    for (let i = this.breaking.length - 1; i >= 0; i--) {
      const k = this.breaking[i];
      k.elapsed += delta;
      let acc = 0;
      let f = 0;
      while (f < k.durations.length - 1 && k.elapsed >= acc + k.durations[f]) acc += k.durations[f++];
      if (f !== k.frame) {
        k.frame = f;
        k.sprite.setFrame(f);
      }
      if (k.spill && f >= k.durations.length - 1) {
        k.spill();
        k.spill = null;
      }
      const total = k.durations.reduce((a, d) => a + d, 0);
      if (k.elapsed >= total) {
        k.spill?.();
        k.sprite.destroy();
        this.breaking.splice(i, 1);
      }
    }
  }

  // --- 술 웅덩이 ---

  liquorPool(x: number, y: number, radiusPx: number, ms: number, L: LiquorPoolParams, attackScale: number): void {
    const H = this.host;
    const side = radiusPx * 2;
    const spec: PoolSpec = {
      owner: 'structure',
      lifeMs: ms,
      playerSlow: L.playerSlow,
      enemySlow: L.enemySlow,
      slip: L.slip,
      fireMs: L.fireMs,
      fireTickMs: L.fireTickMs,
      firePlayerAttack: Math.max(1, Math.round(L.firePlayerAttack * attackScale)),
      fireMobDamage: () => L.fireMobAttack,
      fireFx: FIRE_POOL,
      spreadMsPerCell: null,
      linkGapPx: 0,
      color: ENEMY_HAZARD.LIQUOR_COLOR,
      alpha: ENEMY_HAZARD.LIQUOR_ALPHA,
      ...(this.liquorSheets() ? { sheets: this.liquorSheets()! } : {}),
    };
    H.pools.add(new Phaser.Geom.Rectangle(x - radiusPx, y - radiusPx, side, side), spec);
    this.stats.pools++;
  }

  /** 계약 art §21 술 웅덩이 그림 (pool_liquor · pool_liquor_fire, 반경 = 시트 radiusPx 도트) */
  private liquorSheets(): PoolSpec['sheets'] | undefined {
    const fx = this.host.fx;
    const def = fx.sheet(POOL_LIQUOR);
    if (!def) return undefined;
    const dots = (def as unknown as { radiusPx?: number }).radiusPx;
    return {
      pool: POOL_LIQUOR,
      fire: POOL_LIQUOR_FIRE,
      radiusPx: dots ? dots * artScale(def) : TILE,
      loop: loopRange(def),
      fireLoop: loopRange(fx.sheet(POOL_LIQUOR_FIRE)),
    };
  }

  // --- 주인공 공격 훅 ---

  /** 근접 판정 사각형(중심 x, y · 폭 w · 높이 h)에 닿은 적 술통을 공격 방향으로 되친다 */
  onMeleeSwing(x: number, y: number, w: number, h: number, dirX: number, dirY: number): void {
    const rect = { x: x - w / 2, y: y - h / 2, w, h };
    for (const b of this.barrels)
      if (!b.dead && b.owner === 'enemy' && circleHitsRect(this.center(b), b.radiusPx, rect))
        this.deflect(b, { x: dirX, y: dirY });
  }

  /** 주인공 화살: 술통에 닿으면 화살 방향으로 되친다 (화살은 그대로 날아간다) */
  tickShots(shots: readonly Projectile[]): void {
    if (this.barrels.length === 0) return;
    for (const s of shots) {
      if (!s.active || s.owner !== 'player') continue;
      for (const b of this.barrels) {
        if (b.dead || b.owner !== 'enemy') continue;
        const c = this.center(b);
        if (Math.hypot(s.x - c.x, s.y - c.y) > b.radiusPx + 2 || !s.registerHit(b)) continue;
        const v = s.body.velocity;
        this.deflect(b, { x: v.x, y: v.y });
      }
    }
  }

  update(delta: number): void {
    this.clock += delta;
    if (this.bottles.length) this.stepBottles(delta);
    if (this.barrels.length) this.stepBarrels(delta);
    if (this.breaking.length) this.stepBreaking(delta);
  }

  /** 디버그 */
  summary(): Record<string, unknown> {
    return {
      ...this.stats,
      clock: Math.round(this.clock),
      sceneNow: Math.round(this.host.scene.time.now),
      bottles: this.bottles.length,
      barrels: this.barrels.map((b) => ({ x: Math.round(b.x), y: Math.round(b.y), owner: b.owner })),
    };
  }

  destroy(): void {
    for (const b of this.bottles) this.clearBottle(b);
    this.bottles.length = 0;
    for (const b of this.barrels) b.view.destroy();
    this.barrels.length = 0;
    for (const k of this.breaking) k.sprite.destroy();
    this.breaking.length = 0;
  }
}

const BOTTLE_THROWN = BUILD_ART.BOTTLE_THROWN;
const BOTTLE_BURST = BUILD_ART.BOTTLE_BURST;
const FIRE_POOL = ENEMY_HAZARD.FIRE_POOL;
const POOL_LIQUOR = BUILD_ART.POOL_LIQUOR;
const POOL_LIQUOR_FIRE = BUILD_ART.POOL_LIQUOR_FIRE;

/** 음향 단계 이벤트 (계약 sound 61-2 `enemy:<id>`·`phase:<단계>`) */
function sound(id: string, kind: EnemyAttackPayload['kind'], phase: EnemyAttackPhase): void {
  EventBus.emit(Events.ENEMY_ATTACK, { id, kind, phase } satisfies EnemyAttackPayload);
}

function loopRange(def: unknown): [number, number] | undefined {
  const r = (def as { loopRange?: unknown } | null)?.loopRange;
  return Array.isArray(r) && r.length === 2 && r.every((v) => typeof v === 'number') ? [r[0], r[1]] : undefined;
}
