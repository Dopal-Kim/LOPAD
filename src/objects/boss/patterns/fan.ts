/** 부채꼴 탄 (35라운드, 동작·수치 그대로 옮김): 부채꼴 예고(telegraphMs, 없으면 즉시) → count 발 */
import { TILE } from '../../../core/Constants';
import type { BossFanParams } from '../../../data/types';
import type { TelegraphHandle } from '../../../systems/telegraph';
import type { MobContext } from '../../Mob';
import type { BossHost, BossPatternModule, PatternEnd, PatternRun } from '../types';

const DEG = Math.PI / 180;

export function fireFan(host: BossHost, ctx: MobContext): void {
  const F = host.params<BossFanParams>('fan');
  host.pose.holdFacing(ctx.time, ctx.player);
  host.emitAttack('fan');
  const c = host.center;
  const base = Math.atan2(ctx.player.y - c.y, ctx.player.x - c.x);
  const spread = F.spreadDeg * DEG;
  for (let i = 0; i < F.count; i++) {
    const a = F.count === 1 ? base : base - spread / 2 + (spread * i) / (F.count - 1);
    ctx.fire(c.x, c.y, Math.cos(a), Math.sin(a), {
      speedPx: F.projectileSpeedTiles * TILE,
      attack: F.attack,
      size: F.projectileSize,
      lifeMs: F.projectileLifeMs,
      sprite: F.sprite,
    });
  }
  host.setReadyAt('fan', ctx.time + F.cooldownMs);
}

class FanRun implements PatternRun {
  readonly state = 'fanTelegraph';
  private readonly until: number;
  private marker: TelegraphHandle | null;

  constructor(
    private readonly host: BossHost,
    ctx: MobContext,
    tele: number,
  ) {
    const F = host.params<BossFanParams>('fan');
    this.until = ctx.time + tele;
    host.setVelocity(0, 0);
    host.pose.holdFacing(ctx.time, ctx.player, tele);
    const c = host.center;
    this.marker = ctx.telegraph.cone(
      c.x,
      c.y,
      host.angleTo(ctx.player.x, ctx.player.y),
      (F.spreadDeg / 2) * DEG,
      (F.telegraphTiles ?? 5) * TILE,
      tele,
      { aura: true },
    );
    host.emitTelegraph('fan');
  }

  update(ctx: MobContext): PatternEnd | null {
    const h = this.host;
    h.setVelocity(0, 0);
    this.marker?.aim(h.center.x, h.center.y, h.angleTo(ctx.player.x, ctx.player.y));
    if (ctx.time < this.until) return null;
    this.cancel();
    fireFan(h, ctx);
    return { finish: true };
  }

  cancel(): void {
    this.marker?.end();
    this.marker = null;
  }
}

export const fanPattern: BossPatternModule = {
  name: 'fan',
  start(host, ctx) {
    const tele = host.params<BossFanParams>('fan').telegraphMs ?? 0;
    if (tele <= 0) {
      fireFan(host, ctx);
      return { finish: true };
    }
    return new FanRun(host, ctx, tele);
  },
};
