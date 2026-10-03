/**
 * 내리찍기 (35라운드, 동작·수치 그대로 옮김): 플레이어 자리에 원 예고 → 반경 피해. 오라는 보스 히트박스 중심(46라운드 Q3).
 * 54라운드: v3 `slam` 시트가 있으면 impactFrame 이 예고 끝에 오도록 재생(없으면 기존 frame 3 유지)
 */
import { TILE } from '../../../core/Constants';
import type { BossSlamParams } from '../../../data/types';
import type { TelegraphHandle } from '../../../systems/telegraph';
import type { MobContext } from '../../Mob';
import type { BossHost, BossPatternModule, PatternEnd, PatternRun, Vec } from '../types';

class SlamRun implements PatternRun {
  readonly state = 'slamTelegraph';
  private readonly until: number;
  private readonly target: Vec;
  private marker: TelegraphHandle | null;

  constructor(
    private readonly host: BossHost,
    ctx: MobContext,
  ) {
    const S = host.params<BossSlamParams>('slam');
    this.until = ctx.time + S.telegraphMs;
    host.setVelocity(0, 0);
    this.target = { x: ctx.player.x, y: ctx.player.y };
    if (!host.pose.play('slam', ctx.time, { fitMs: S.telegraphMs + 200, keyAtMs: S.telegraphMs, target: this.target }))
      host.pose.holdFacing(ctx.time, ctx.player, S.telegraphMs);
    const c = host.center;
    this.marker = ctx.telegraph.circle(this.target.x, this.target.y, S.radiusTiles * TILE, S.telegraphMs, {
      aura: true,
      auraAt: { x: c.x, y: c.y },
    });
    host.emitTelegraph('slam');
  }

  update(ctx: MobContext): PatternEnd | null {
    const h = this.host;
    h.setVelocity(0, 0);
    if (ctx.time < this.until) return null;
    this.cancel();
    const S = h.params<BossSlamParams>('slam');
    ctx.areaHit(this.target.x, this.target.y, S.radiusTiles * TILE, S.attack);
    h.emitAttack('slam');
    h.pose.recover(ctx.time);
    return { finish: true };
  }

  cancel(): void {
    this.marker?.end();
    this.marker = null;
  }
}

export const slamPattern: BossPatternModule = {
  name: 'slam',
  start: (host, ctx) => new SlamRun(host, ctx),
};
