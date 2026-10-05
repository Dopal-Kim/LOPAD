/**
 * 61라운드 단계 2 (P3·SY-5) 1층 신규 적 행동 — 보스 '만취' 예습 (계약 art §23 앵커·타이밍).
 * - 독주 행상(`throw`): 3.5~5칸 거리 유지 · 2칸 안이면 도망 · 쿨다운마다 화염 술병 — 심지 불붙임(attack 0~4, 착탄 자리 원 예고)
 *   → 놓음 프레임(releaseFrame 5, 550ms)에 손 앵커(throwHandAnchors)에서 포물선(비행 0.7초) → 폭발 → 불 웅덩이 4초
 * - 술통 짐꾼(`roll`): 다가가다 사거리면 버팀·당겨 감기(attack 0~4, 진행 직선 예고 — 놓기 전까지 주인공을 따라 돈다)
 *   → 놓음 프레임(5, 530ms)에 술통 바닥 접점 앵커(barrelSpawnAnchors)에서 술통 굴림. 쿨다운 3.2초
 * 경직되면 준비를 끊는다. 실제 투사체·웅덩이는 씬의 EnemyHazards(MobContext.hazards).
 */
import Phaser from 'phaser';
import { TILE } from '../../core/Constants';
import { EventBus, Events, type EnemyAttackPayload, type EnemyTelegraphPayload } from '../../core/EventBus';
import type { EnemyDef } from '../../data/types';
import { clampThrowTarget, peddlerIntent, unit } from '../../systems/hazards/hazardMath';
import type { HazardPt } from '../../systems/hazards/enemyHazardTypes';
import { anchorOffset } from '../../systems/sprites/spriteMeta';
import type { TelegraphHandle } from '../../systems/telegraph';
import type { EntityVisual } from '../EntityVisual';
import type { MobContext } from '../Mob';

/** 행동이 몸에 요구하는 것 (Enemy 가 구현) */
export interface BrainBody {
  readonly x: number;
  readonly y: number;
  readonly body: Phaser.Physics.Arcade.Body;
  readonly visual: EntityVisual;
  readonly def: EnemyDef;
  readonly attackRateMult: number;
  readonly active: boolean;
  /** 층 적 공격 배율 */
  attackScale(): number;
  moveTo(x: number, y: number, speedPx: number): void;
  /** 공격 동작(시트) — 대상 쪽을 보고 재생 */
  attackAnim(time: number): void;
}

/** 놓음 프레임 시각 ms (시트 fireFrame, 없으면 fallback) */
function releaseMs(b: BrainBody, fallback: number): number {
  const ms = b.visual.impactDelayMs('attack');
  return ms > 0 ? ms : fallback;
}

/** 시트 앵커(프레임별 도트 좌표 표)의 월드 자리 — 지금 바라보는 방향·놓음 프레임. 없으면 null */
function releaseAnchor(b: BrainBody, field: string): HazardPt | null {
  const def = b.visual.sheet('attack');
  if (!def) return null;
  const meta = def as unknown as Record<string, unknown> & { releaseFrame?: number; fireFrame?: number };
  const f = typeof meta.releaseFrame === 'number' ? meta.releaseFrame : meta.fireFrame;
  const table = meta[field] as Record<string, ([number, number] | null)[]> | undefined;
  const p = typeof f === 'number' ? table?.[b.visual.facing]?.[f] : null;
  if (!p) return null;
  const o = anchorOffset(def, p);
  return { x: b.x + o.x, y: b.y + o.y };
}

/** 이 행동 기본 놓음 시각 (아트 §23: 행상 550 · 짐꾼 530 — 시트가 없을 때) */
const RELEASE_FALLBACK = { throw: 550, roll: 530 } as const;
/** 놓은 뒤 멈춰 서는 시간 (따라 휘두름·재장전 그림이 끝날 때까지 — 시트 길이에서 놓음 시각을 뺀 값, 없으면 이것) */
const RECOVER_FALLBACK_MS = 400;
/** 손 앵커가 없을 때 병을 드는 높이 (월드 px) */
const HAND_FALLBACK_PX = 14;

function recoverMs(b: BrainBody, release: number): number {
  const def = b.visual.sheet('attack');
  const total = def?.frameDurationsMs?.reduce((a, d) => a + d, 0) ?? 0;
  return total > release ? total - release : RECOVER_FALLBACK_MS;
}

type Phase = 'move' | 'windup' | 'recover';

/** 독주 행상 */
export class PeddlerBrain {
  phase: Phase = 'move';
  private until = 0;
  private nextAt = 0;
  private target: HazardPt = { x: 0, y: 0 };
  private marker: TelegraphHandle | null = null;

  constructor(private readonly b: BrainBody) {}

  get state(): string {
    return this.phase;
  }

  think(ctx: MobContext): void {
    const b = this.b;
    const T = b.def.throw!;
    const speed = b.def.speedTiles * TILE;
    if (this.phase === 'windup') {
      b.body.setVelocity(0, 0);
      if (ctx.time >= this.until) this.release(ctx);
      return;
    }
    if (this.phase === 'recover') {
      b.body.setVelocity(0, 0);
      if (ctx.time >= this.until) this.phase = 'move';
      return;
    }
    const dx = b.x - ctx.player.x;
    const dy = b.y - ctx.player.y;
    const dist = Math.hypot(dx, dy) / TILE;
    const intent = peddlerIntent(dist, T);
    const away = unit(dx, dy);
    if (intent === 'flee') b.body.setVelocity(away.x * speed * T.fleeSpeedMult, away.y * speed * T.fleeSpeedMult);
    else if (intent === 'back') b.body.setVelocity(away.x * speed, away.y * speed);
    else if (intent === 'close') b.moveTo(ctx.player.x, ctx.player.y, speed);
    else b.body.setVelocity(0, 0);
    const [lo, hi] = T.rangeTiles;
    if (intent !== 'flee' && ctx.hazards && ctx.time >= this.nextAt && dist >= lo && dist <= hi) this.windup(ctx);
  }

  /** 심지 불붙임: 떨어질 자리를 정하고(지금 주인공 자리, 사거리로 자름) 원 예고 — 놓음 + 비행 시간 동안 */
  private windup(ctx: MobContext): void {
    const b = this.b;
    const T = b.def.throw!;
    const rel = releaseMs(b, RELEASE_FALLBACK.throw);
    this.phase = 'windup';
    this.until = ctx.time + rel;
    b.body.setVelocity(0, 0);
    this.target = clampThrowTarget({ x: b.x, y: b.y }, ctx.player, T.rangeTiles[0] * TILE, T.rangeTiles[1] * TILE);
    this.marker = ctx.telegraph.circle(this.target.x, this.target.y, T.burstRadiusTiles * TILE, rel + T.flightMs);
    b.attackAnim(ctx.time);
    EventBus.emit(Events.ENEMY_TELEGRAPH, { id: 'peddler', kind: 'throw' } satisfies EnemyTelegraphPayload);
  }

  private release(ctx: MobContext): void {
    const b = this.b;
    const T = b.def.throw!;
    const hand = releaseAnchor(b, 'throwHandAnchors');
    const from = { x: hand?.x ?? b.x, y: b.y };
    const handPx = hand ? Math.max(0, b.y - hand.y) : HAND_FALLBACK_PX;
    // 예고 원은 착지까지 남는다 (marker 수명 = 놓음 + 비행)
    this.marker = null;
    ctx.hazards?.throwBottle(from, handPx, this.target, T, b.attackScale());
    EventBus.emit(Events.ENEMY_ATTACK, { id: 'peddler', kind: 'throw', phase: 'throw' } satisfies EnemyAttackPayload);
    this.phase = 'recover';
    this.until = ctx.time + recoverMs(b, releaseMs(b, RELEASE_FALLBACK.throw));
    this.nextAt = ctx.time + T.cooldownMs / Math.max(0.1, b.attackRateMult);
  }

  /** 경직·사망: 준비를 끊는다 (곧 다시 던지지 않게 쿨다운 절반) */
  interrupt(time: number): void {
    if (this.phase === 'windup') {
      this.marker?.end();
      this.marker = null;
      this.nextAt = time + this.b.def.throw!.cooldownMs / 2;
    }
    this.phase = 'move';
  }
}

/** 술통 짐꾼 */
export class PorterBrain {
  phase: Phase = 'move';
  private until = 0;
  private nextAt = 0;
  private marker: TelegraphHandle | null = null;
  private aim: HazardPt = { x: 1, y: 0 };

  constructor(private readonly b: BrainBody) {}

  get state(): string {
    return this.phase;
  }

  private center(): HazardPt {
    return { x: this.b.body.center.x, y: this.b.body.center.y };
  }

  think(ctx: MobContext): void {
    const b = this.b;
    const R = b.def.roll!;
    if (this.phase === 'windup') {
      b.body.setVelocity(0, 0);
      // 놓기 전까지 진행 방향이 주인공을 따라간다 (결사병 돌진 예고와 같은 규칙)
      const c = this.center();
      this.aim = unit(ctx.player.x - b.x, ctx.player.y - b.y, this.aim);
      this.marker?.aim(c.x, c.y, Math.atan2(this.aim.y, this.aim.x));
      if (ctx.time >= this.until) this.release(ctx);
      return;
    }
    if (this.phase === 'recover') {
      b.body.setVelocity(0, 0);
      if (ctx.time >= this.until) this.phase = 'move';
      return;
    }
    const dist = Phaser.Math.Distance.Between(b.x, b.y, ctx.player.x, ctx.player.y) / TILE;
    // 멀면 다가가고, 사거리 안에서는 굴릴 때를 기다리며 천천히 (아주 가까우면 몸으로 민다 = 접촉 공격)
    b.moveTo(ctx.player.x, ctx.player.y, b.def.speedTiles * TILE);
    if (ctx.hazards && ctx.time >= this.nextAt && dist <= R.triggerTiles && dist >= R.minTiles) this.windup(ctx);
  }

  private windup(ctx: MobContext): void {
    const b = this.b;
    const R = b.def.roll!;
    const rel = releaseMs(b, RELEASE_FALLBACK.roll);
    this.phase = 'windup';
    this.until = ctx.time + rel;
    b.body.setVelocity(0, 0);
    this.aim = unit(ctx.player.x - b.x, ctx.player.y - b.y);
    const c = this.center();
    this.marker = ctx.telegraph.line(c.x, c.y, Math.atan2(this.aim.y, this.aim.x), R.maxTiles * TILE, rel);
    b.attackAnim(ctx.time);
    EventBus.emit(Events.ENEMY_TELEGRAPH, { id: 'porter', kind: 'roll' } satisfies EnemyTelegraphPayload);
  }

  private release(ctx: MobContext): void {
    const b = this.b;
    const R = b.def.roll!;
    this.marker?.end();
    this.marker = null;
    const at = releaseAnchor(b, 'barrelSpawnAnchors') ?? {
      x: b.x + this.aim.x * TILE * 0.6,
      y: b.y + this.aim.y * TILE * 0.6,
    };
    if (b.def.liquor) ctx.hazards?.rollBarrel(at, this.aim.x, this.aim.y, R, b.def.liquor, b.attackScale());
    this.phase = 'recover';
    this.until = ctx.time + recoverMs(b, releaseMs(b, RELEASE_FALLBACK.roll));
    this.nextAt = ctx.time + R.cooldownMs / Math.max(0.1, b.attackRateMult);
  }

  interrupt(time: number): void {
    if (this.phase === 'windup') {
      this.marker?.end();
      this.marker = null;
      this.nextAt = time + this.b.def.roll!.cooldownMs / 2;
    }
    this.phase = 'move';
  }
}
