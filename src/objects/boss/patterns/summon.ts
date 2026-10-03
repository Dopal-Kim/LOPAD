/** 소환 (35라운드, 동작·수치 그대로 옮김): 양옆에 count 마리 (같은 적 max 마리 이상이면 고르지 않음) → 잠깐 멈춤 */
import { ENEMY_FX, SPRITES } from '../../../core/Constants';
import type { BossSummonParams } from '../../../data/types';
import type { MobContext } from '../../Mob';
import type { BossHost, BossPatternModule, PatternEnd, PatternRun } from '../types';

class RecoverRun implements PatternRun {
  readonly state = 'recover';
  constructor(
    private readonly host: BossHost,
    private readonly until: number,
  ) {}

  update(ctx: MobContext): PatternEnd | null {
    this.host.setVelocity(0, 0);
    return ctx.time >= this.until ? { finish: true } : null;
  }

  cancel(): void {}
}

export const summonPattern: BossPatternModule = {
  name: 'summon',
  isReady(host, ctx) {
    const S = host.params<BossSummonParams>('summon');
    return ctx.countMobs(S.enemy) < S.max;
  },
  start(host: BossHost, ctx: MobContext) {
    const S = host.params<BossSummonParams>('summon');
    const room = Math.max(0, S.max - ctx.countMobs(S.enemy));
    const n = Math.min(S.count, room);
    const gap = host.halfWidth + ENEMY_FX.SUMMON_GAP_PX;
    let placed = 0;
    for (let i = 0; i < n; i++) {
      const side = i % 2 === 0 ? -1 : 1;
      const ring = 1 + Math.floor(i / 2);
      if (ctx.summon(S.enemy, host.pos.x + side * gap * ring, host.pos.y)) placed++;
    }
    host.emitAttack('summon');
    const holdMs = host.pose.recoverHoldMs();
    host.pose.holdFacing(ctx.time, ctx.player);
    host.addSummoned(placed);
    return new RecoverRun(host, ctx.time + Math.max(holdMs, SPRITES.BOSS_DASH_FRAME_MS));
  },
};
