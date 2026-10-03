/**
 * 54라운드 Q3 술독 굴리기: 술통을 걷어차(kick, impactFrame = 예고 끝) 벽·기둥에 bounces 번 튕기며 굴린다.
 * 예고 = 튕김 경로 꺾은선. 지나간 자리는 술 웅덩이(미끄러움·감속), 플레이어가 치면 방향이 바뀌고 보스에 맞으면 보스 피해·경직
 * (굴러가는 술통은 방(BossArena)이 맡는다 — 이 패턴은 걷어차기까지).
 */
import { TILE } from '../../../core/Constants';
import type { TelegraphPathHandle } from '../../../systems/telegraph';
import type { MobContext } from '../../Mob';
import type { BossArenaApi, BossHost, BossPatternModule, PatternEnd, PatternRun, Vec } from '../types';

export interface CaskRollParams {
  telegraphMs: number;
  speedTiles: number;
  bounces: number;
  maxTiles: number;
  attack: number;
  radiusPx: number;
  puddleEveryTiles: number;
  puddleMs: number;
  bossHitDamage: number;
  bossHitStunMs: number;
  cooldownMs: number;
  count: number;
  spreadDeg: number;
}

/** 걷어찬 뒤 멈춰 있는 시간 */
const KICK_RECOVER_MS = 300;

/** count 개 술통의 각도: 가운데 = 조준, spreadDeg 간격 */
export function caskAngles(aim: number, count: number, spreadDeg: number): number[] {
  const out: number[] = [];
  const step = (spreadDeg * Math.PI) / 180;
  for (let i = 0; i < count; i++) out.push(aim + (i - (count - 1) / 2) * step);
  return out;
}

class CaskRollRun implements PatternRun {
  state: 'caskTelegraph' | 'kickRecover' = 'caskTelegraph';
  private until: number;
  private markers: TelegraphPathHandle[] = [];
  private angles: number[] = [];

  constructor(
    private readonly host: BossHost,
    private readonly arena: BossArenaApi,
    ctx: MobContext,
  ) {
    const P = this.P;
    this.until = ctx.time + P.telegraphMs;
    host.setVelocity(0, 0);
    if (
      !host.pose.play('kick', ctx.time, {
        fitMs: P.telegraphMs + KICK_RECOVER_MS,
        keyAtMs: P.telegraphMs,
        target: ctx.player,
      })
    )
      host.pose.holdFacing(ctx.time, ctx.player, P.telegraphMs);
    this.aim(ctx);
    for (const a of this.angles) {
      const pts = this.trace(a);
      this.markers.push(ctx.telegraph.path(pts, P.telegraphMs, { aura: false }));
    }
    host.emitTelegraph('caskRoll');
  }

  private get P(): CaskRollParams {
    return this.host.params<CaskRollParams>('caskRoll');
  }

  private from(): Vec {
    const h = this.host;
    const foot = h.pose.anchor('kick', 'footAnchors');
    if (foot) return foot;
    const a = this.angles[Math.floor(this.angles.length / 2)] ?? 0;
    const off = h.halfWidth + this.P.radiusPx + 2;
    return { x: h.center.x + Math.cos(a) * off, y: h.center.y + Math.sin(a) * off };
  }

  private aim(ctx: MobContext): void {
    const P = this.P;
    this.angles = caskAngles(
      this.host.angleTo(ctx.player.x, ctx.player.y),
      Math.max(1, Math.round(P.count)),
      P.spreadDeg,
    );
  }

  private trace(angle: number): Vec[] {
    const P = this.P;
    return this.arena.traceCask(
      this.from(),
      Math.cos(angle),
      Math.sin(angle),
      P.bounces,
      P.maxTiles * TILE,
      P.radiusPx,
    );
  }

  update(ctx: MobContext): PatternEnd | null {
    const h = this.host;
    h.setVelocity(0, 0);
    if (this.state === 'caskTelegraph') {
      this.aim(ctx);
      this.angles.forEach((a, i) => this.markers[i]?.setPoints(this.trace(a)));
      if (ctx.time < this.until) return null;
      this.clear();
      const P = this.P;
      const from = this.from();
      for (const a of this.angles) this.arena.kickCask(from, Math.cos(a), Math.sin(a), P);
      h.emitAction('kick');
      h.emitAttack('caskRoll');
      this.state = 'kickRecover';
      this.until = ctx.time + KICK_RECOVER_MS;
      return null;
    }
    if (ctx.time < this.until) return null;
    h.pose.release();
    return { finish: true };
  }

  private clear(): void {
    for (const m of this.markers) m.end();
    this.markers = [];
  }

  cancel(): void {
    this.clear();
  }
}

export const caskRollPattern: BossPatternModule = {
  name: 'caskRoll',
  isReady: (_host, ctx) => Boolean(ctx.arena),
  start: (host, ctx) => (ctx.arena ? new CaskRollRun(host, ctx.arena, ctx) : { finish: true }),
};
