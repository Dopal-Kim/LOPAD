/**
 * 돌진 (35라운드, 동작·수치 그대로 옮김): 경로 예고선 → 직선 돌진 → 멈춤. 벽에 부딪히면 경직(패턴 파훼 창).
 * `repeat` 이면 짧은 예고(× repeatTelegraphRatio, 기본 0.5)로 이어서 다시. 끝나면 부채꼴 연계(fan.afterDash).
 */
import { COLORS, TILE } from '../../../core/Constants';
import type { BossDashParams, BossFanParams } from '../../../data/types';
import type { TelegraphHandle } from '../../../systems/telegraph';
import type { MobContext } from '../../Mob';
import type { BossHost, BossPatternModule, PatternEnd, PatternRun } from '../types';

/** 돌진이 끝난 뒤 부채꼴로 이어지는지 (이 페이즈가 fan 을 고르고, afterDash 이고, 쿨타임이 끝났을 때) */
export function afterDashNext(host: BossHost, ctx: MobContext): PatternEnd['next'] {
  if (!host.inPick('fan')) return undefined;
  const F = host.params<BossFanParams>('fan');
  if (!F.afterDash || ctx.time < host.readyAt('fan')) return undefined;
  return 'fan';
}

class DashRun implements PatternRun {
  state: 'telegraph' | 'dash' | 'stun' = 'telegraph';
  private until = 0;
  private left: number;
  private dirX = 1;
  private dirY = 0;
  private marker: TelegraphHandle | null = null;

  constructor(
    private readonly host: BossHost,
    ctx: MobContext,
  ) {
    const P = host.params<BossDashParams>('dash');
    this.left = (P.repeat ?? 1) - 1;
    this.beginTelegraph(ctx, P.telegraphMs, true);
  }

  private beginTelegraph(ctx: MobContext, telegraphMs: number, first: boolean): void {
    const h = this.host;
    const P = h.params<BossDashParams>('dash');
    this.state = 'telegraph';
    this.until = ctx.time + telegraphMs;
    h.setVelocity(0, 0);
    h.paint(COLORS.TELEGRAPH);
    h.pose.dashTelegraph(ctx.time, ctx.player, telegraphMs + P.durationMs, first);
    const c = h.center;
    const lengthPx = (P.speedTiles * TILE * P.durationMs) / 1000;
    this.clearMarker();
    this.marker = ctx.telegraph.line(c.x, c.y, h.angleTo(ctx.player.x, ctx.player.y), lengthPx, telegraphMs, {
      aura: true,
    });
    if (first) h.emitTelegraph('dash');
  }

  update(ctx: MobContext): PatternEnd | null {
    const h = this.host;
    const P = h.params<BossDashParams>('dash');
    switch (this.state) {
      case 'telegraph':
        this.marker?.aim(h.center.x, h.center.y, h.angleTo(ctx.player.x, ctx.player.y));
        if (ctx.time >= this.until) {
          this.clearMarker();
          const dx = ctx.player.x - h.pos.x;
          const dy = ctx.player.y - h.pos.y;
          const len = Math.hypot(dx, dy);
          this.dirX = len > 0 ? dx / len : 0;
          this.dirY = len > 0 ? dy / len : 0;
          this.state = 'dash';
          this.until = ctx.time + P.durationMs;
          h.restoreColor();
          h.pose.dashLoop(this.dirX, this.dirY);
          h.emitAttack('dash');
        }
        return null;
      case 'dash': {
        const s = P.speedTiles * TILE;
        h.setVelocity(this.dirX * s, this.dirY * s);
        if (h.blocked) {
          // 벽에 부딪힘 → 경직 (패턴 파훼 창). 다음 패턴 예약은 지금
          this.state = 'stun';
          this.until = ctx.time + P.wallStunMs;
          h.setVelocity(0, 0);
          h.paint(COLORS.STUN);
          h.pose.recover(ctx.time, P.wallStunMs);
          h.scheduleNext(ctx.time);
          h.emitWallHit();
        } else if (ctx.time >= this.until) {
          h.setVelocity(0, 0);
          if (this.left > 0) {
            this.left -= 1;
            this.beginTelegraph(ctx, P.telegraphMs * (P.repeatTelegraphRatio ?? 0.5), false);
          } else {
            h.pose.recover(ctx.time);
            return { finish: true, next: afterDashNext(h, ctx) };
          }
        }
        return null;
      }
      case 'stun':
        h.setVelocity(0, 0);
        if (ctx.time >= this.until) {
          h.pose.release();
          h.restoreColor();
          return { finish: false, next: afterDashNext(h, ctx) };
        }
        return null;
    }
  }

  contactAttack(): number | null {
    return this.state === 'dash' ? this.host.params<BossDashParams>('dash').attack : null;
  }

  cancel(): void {
    this.clearMarker();
  }

  private clearMarker(): void {
    this.marker?.end();
    this.marker = null;
  }
}

export const dashPattern: BossPatternModule = {
  name: 'dash',
  start: (host, ctx) => new DashRun(host, ctx),
};
