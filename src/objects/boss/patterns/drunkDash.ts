/**
 * 54라운드 Q9 3연 취권 돌진: 돌진(dash)의 연속 돌진(repeat)을 확장 — 매 타 휘는 곡선 궤적(예고선도 곡선), 예고 시간은 타마다
 * telegraphSeqMs (얼큰·만취 600→350→350, 인사불성 500→300→300). 휘는 쪽은 타마다 번갈아. 세 번째 뒤 넘어져 fallMs 경직(반격 창).
 * 벽·기둥에 부딪히면 돌진과 같은 벽 경직(wallStunMs)으로 끝. 넘어져 있는 동안은 접촉 피해 없음.
 */
import { COLORS, TILE } from '../../../core/Constants';
import type { TelegraphPathHandle } from '../../../systems/telegraph';
import type { MobContext } from '../../Mob';
import { cumulative, curvedDashPath, pointAlong, type P2 } from '../curve';
import type { BossHost, BossPatternModule, PatternEnd, PatternRun } from '../types';

export interface DrunkDashParams {
  telegraphSeqMs?: number[];
  telegraphMs?: number;
  speedTiles: number;
  durationMs: number;
  attack: number;
  wallStunMs: number;
  repeat: number;
  bendRatio: number;
  fallMs: number;
  cooldownMs: number;
  leanDeg?: number;
}

/** i 번째 타의 예고 ms (목록이 짧으면 마지막 값, 없으면 telegraphMs, 그것도 없으면 500) */
export function reelTelegraphMs(P: Pick<DrunkDashParams, 'telegraphSeqMs' | 'telegraphMs'>, i: number): number {
  const seq = P.telegraphSeqMs;
  if (seq && seq.length > 0) return seq[Math.min(i, seq.length - 1)];
  return P.telegraphMs ?? 500;
}

const PATH_SAMPLES = 20;
/** 경로 추종: 목표점까지 속도 상한 = 경로 속도 × 이 값 */
const CATCHUP = 1.6;

class DrunkDashRun implements PatternRun {
  state: 'reelTelegraph' | 'reel' | 'wallStun' | 'fall' = 'reelTelegraph';
  private index = 0;
  private until = 0;
  private startedAt = 0;
  private sign: number;
  private path: P2[] = [];
  private acc: number[] = [0];
  private marker: TelegraphPathHandle | null = null;
  private rose = false;

  constructor(
    private readonly host: BossHost,
    ctx: MobContext,
  ) {
    this.sign = host.rng.next() < 0.5 ? 1 : -1;
    this.beginTelegraph(ctx);
  }

  private get P(): DrunkDashParams {
    return this.host.params<DrunkDashParams>('drunkDash');
  }

  private lengthPx(): number {
    return (this.P.speedTiles * TILE * this.P.durationMs) / 1000;
  }

  private plan(ctx: MobContext): void {
    this.path = curvedDashPath(
      this.host.center,
      ctx.player,
      this.lengthPx(),
      this.P.bendRatio,
      this.sign,
      PATH_SAMPLES,
    );
    this.acc = cumulative(this.path);
  }

  private beginTelegraph(ctx: MobContext): void {
    const h = this.host;
    const tele = reelTelegraphMs(this.P, this.index);
    this.state = 'reelTelegraph';
    this.until = ctx.time + tele;
    h.setVelocity(0, 0);
    h.paint(COLORS.TELEGRAPH);
    this.plan(ctx);
    // v3 stagger_dash 시트가 없으면 돌진 예고 자세 + 임시 몸 기울기
    if (!h.pose.phase('stagger_dash', 'telegraph', ctx.time, { target: ctx.player, fitMs: tele })) {
      h.pose.dashTelegraph(ctx.time, ctx.player, tele + this.P.durationMs, this.index === 0);
      h.pose.lean(((this.P.leanDeg ?? 0) * this.sign * Math.PI) / 180);
    }
    this.marker?.end();
    this.marker = ctx.telegraph.path(this.path, tele, { aura: true });
    if (this.index === 0) h.emitTelegraph('drunkDash');
    h.emitAction('reelTelegraph', this.index);
  }

  update(ctx: MobContext): PatternEnd | null {
    const h = this.host;
    const P = this.P;
    switch (this.state) {
      case 'reelTelegraph':
        // 예고 동안 목표를 따라 경로를 다시 그린다 (돌진 예고선과 같은 규칙)
        this.plan(ctx);
        this.marker?.setPoints(this.path);
        if (ctx.time >= this.until) {
          this.marker?.end();
          this.marker = null;
          this.state = 'reel';
          this.startedAt = ctx.time;
          this.until = ctx.time + P.durationMs;
          h.restoreColor();
          const end = this.path[this.path.length - 1];
          if (!h.pose.phase('stagger_dash', 'dash', ctx.time, { loop: true, target: end }))
            h.pose.dashLoop(end.x - h.center.x, end.y - h.center.y);
          if (this.index === 0) h.emitAttack('drunkDash');
          h.emitAction('reelDash', this.index);
        }
        return null;
      case 'reel': {
        if (h.blocked) {
          this.state = 'wallStun';
          this.until = ctx.time + P.wallStunMs;
          h.setVelocity(0, 0);
          h.paint(COLORS.STUN);
          h.pose.lean(0);
          h.pose.recover(ctx.time, P.wallStunMs);
          h.markBroken(P.wallStunMs);
          h.emitWallHit();
          return null;
        }
        const total = this.acc[this.acc.length - 1];
        const t = Math.min(1, (ctx.time - this.startedAt) / P.durationMs);
        const goal = pointAlong(this.path, this.acc, total * Math.min(1, t + ctx.delta / P.durationMs));
        const dt = Math.max(1, ctx.delta) / 1000;
        const max = (total / (P.durationMs / 1000)) * CATCHUP;
        let vx = (goal.x - h.center.x) / dt;
        let vy = (goal.y - h.center.y) / dt;
        const sp = Math.hypot(vx, vy);
        if (sp > max) {
          vx = (vx / sp) * max;
          vy = (vy / sp) * max;
        }
        h.setVelocity(vx, vy);
        if (ctx.time >= this.until) {
          h.setVelocity(0, 0);
          this.index += 1;
          this.sign = -this.sign;
          if (this.index < P.repeat) this.beginTelegraph(ctx);
          else this.beginFall(ctx);
        }
        return null;
      }
      case 'wallStun':
        h.setVelocity(0, 0);
        if (ctx.time < this.until) return null;
        h.pose.release();
        h.restoreColor();
        return { finish: true };
      case 'fall':
        h.setVelocity(0, 0);
        if (!this.rose && ctx.time >= this.until - this.riseMs()) {
          this.rose = true;
          h.pose.phase('fall', 'rise', ctx.time, { fitMs: this.riseMs() });
          h.emitAction('rise');
        }
        if (ctx.time < this.until) return null;
        h.pose.lie(false);
        h.pose.release();
        h.restoreColor();
        return { finish: true };
    }
  }

  private riseMs(): number {
    return Math.min(400, this.P.fallMs / 4);
  }

  private beginFall(ctx: MobContext): void {
    const h = this.host;
    this.state = 'fall';
    this.until = ctx.time + this.P.fallMs;
    h.pose.lean(0);
    // 넘어짐 → 누워 있음 루프 (시트가 없으면 임시: 눕힘)
    if (!h.pose.phase('fall', 'fall', ctx.time, { thenLoop: 'down' })) h.pose.lie(true);
    h.markBroken(this.P.fallMs);
    h.emitAction('fall');
  }

  contactAttack(): number | null {
    if (this.state === 'reel') return this.P.attack;
    if (this.state === 'fall') return 0;
    return null;
  }

  cancel(): void {
    this.marker?.end();
    this.marker = null;
    this.host.pose.lean(0);
    if (this.state === 'fall') this.host.pose.lie(false);
  }
}

export const drunkDashPattern: BossPatternModule = {
  name: 'drunkDash',
  start: (host, ctx) => new DrunkDashRun(host, ctx),
};
