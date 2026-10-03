/**
 * 54라운드 Q8 등불 끄기 (인사불성 화면 패턴, 한 잔 더를 다 마셔야 발동): 보스가 바닥을 내리쳐(원 예고 → 반경 피해)
 * 촛대를 차례로 쓰러뜨리고 주변광을 낮춘다. 쓰러진 촛대를 치거나 E 로 다시 켜면 그 주변이 밝아지고, 불붙은 웅덩이도 광원.
 * durationMs 뒤 저절로 복구(방이 맡는다). 끝나면 어둠 속 3연 취권(next).
 */
import { TILE } from '../../../core/Constants';
import type { BossPatternName } from '../../../data/bossPatterns';
import type { TelegraphHandle } from '../../../systems/telegraph';
import type { MobContext } from '../../Mob';
import type { BossArenaApi, BossHost, BossPatternModule, PatternEnd, PatternRun } from '../types';

export interface LightsOutParams {
  telegraphMs: number;
  radiusTiles: number;
  attack: number;
  fadeMs: number;
  durationMs: number;
  cooldownMs: number;
  toppleGapMs: number;
  darkAmbient: string;
  next?: BossPatternName;
}

class LightsOutRun implements PatternRun {
  readonly state = 'darkTelegraph';
  private readonly until: number;
  private marker: TelegraphHandle | null;

  constructor(
    private readonly host: BossHost,
    private readonly arena: BossArenaApi,
    ctx: MobContext,
  ) {
    const P = this.P;
    this.until = ctx.time + P.telegraphMs;
    host.setVelocity(0, 0);
    if (!host.pose.play('slam', ctx.time, { fitMs: P.telegraphMs + 200, keyAtMs: P.telegraphMs, target: ctx.player }))
      host.pose.holdFacing(ctx.time, ctx.player, P.telegraphMs);
    const c = host.center;
    this.marker = ctx.telegraph.circle(c.x, c.y, P.radiusTiles * TILE, P.telegraphMs, { aura: true });
    host.emitTelegraph('lightsOut');
  }

  private get P(): LightsOutParams {
    return this.host.params<LightsOutParams>('lightsOut');
  }

  update(ctx: MobContext): PatternEnd | null {
    const h = this.host;
    h.setVelocity(0, 0);
    if (ctx.time < this.until) return null;
    this.cancel();
    const P = this.P;
    ctx.areaHit(h.center.x, h.center.y, P.radiusTiles * TILE, P.attack);
    this.arena.lightsOut(P);
    h.emitAttack('lightsOut');
    h.pose.recover(ctx.time);
    return { finish: true, next: P.next };
  }

  cancel(): void {
    this.marker?.end();
    this.marker = null;
  }
}

export const lightsOutPattern: BossPatternModule = {
  name: 'lightsOut',
  isReady: (_host, ctx) => Boolean(ctx.arena) && !ctx.arena!.dark,
  start: (host, ctx) => (ctx.arena ? new LightsOutRun(host, ctx.arena, ctx) : { finish: true }),
};
