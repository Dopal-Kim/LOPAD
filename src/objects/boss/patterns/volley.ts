/** 정렬 사격 (35라운드 황제, 동작·수치 그대로 옮김): 일직선 예고 → shotGapMs 간격으로 count 발 */
import { TILE } from '../../../core/Constants';
import type { BossVolleyParams } from '../../../data/types';
import type { TelegraphHandle } from '../../../systems/telegraph';
import type { MobContext } from '../../Mob';
import type { BossHost, BossPatternModule, PatternEnd, PatternRun } from '../types';

class VolleyRun implements PatternRun {
  state: 'volleyTelegraph' | 'volley' = 'volleyTelegraph';
  private until: number;
  private marker: TelegraphHandle | null;
  private dirX = 1;
  private dirY = 0;
  private left = 0;
  private nextAt = 0;

  constructor(
    private readonly host: BossHost,
    ctx: MobContext,
  ) {
    const V = host.params<BossVolleyParams>('volley');
    this.until = ctx.time + V.telegraphMs;
    host.setVelocity(0, 0);
    host.pose.holdFacing(ctx.time, ctx.player, V.telegraphMs);
    const c = host.center;
    this.marker = ctx.telegraph.line(
      c.x,
      c.y,
      host.angleTo(ctx.player.x, ctx.player.y),
      V.telegraphTiles * TILE,
      V.telegraphMs,
      { aura: true },
    );
    host.emitTelegraph('volley');
  }

  update(ctx: MobContext): PatternEnd | null {
    const h = this.host;
    const V = h.params<BossVolleyParams>('volley');
    h.setVelocity(0, 0);
    if (this.state === 'volleyTelegraph') {
      this.marker?.aim(h.center.x, h.center.y, h.angleTo(ctx.player.x, ctx.player.y));
      if (ctx.time >= this.until) {
        this.cancel();
        const dx = ctx.player.x - h.center.x;
        const dy = ctx.player.y - h.center.y;
        const len = Math.hypot(dx, dy);
        this.dirX = len > 0 ? dx / len : 0;
        this.dirY = len > 0 ? dy / len : 0;
        this.left = V.count;
        this.nextAt = ctx.time;
        this.state = 'volley';
        h.emitAttack('volley');
      }
      return null;
    }
    if (ctx.time >= this.nextAt && this.left > 0) {
      this.left -= 1;
      this.nextAt = ctx.time + V.shotGapMs;
      const c = h.center;
      ctx.fire(c.x, c.y, this.dirX, this.dirY, {
        speedPx: V.projectileSpeedTiles * TILE,
        attack: V.attack,
        size: V.projectileSize,
        lifeMs: V.projectileLifeMs,
        sprite: V.sprite,
      });
    }
    return this.left <= 0 ? { finish: true } : null;
  }

  cancel(): void {
    this.marker?.end();
    this.marker = null;
  }
}

export const volleyPattern: BossPatternModule = {
  name: 'volley',
  start: (host, ctx) => new VolleyRun(host, ctx),
};
