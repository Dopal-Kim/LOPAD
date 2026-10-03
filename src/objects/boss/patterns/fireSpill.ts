/**
 * 54라운드 Q3 불붙은 술: 술을 뿌려(예고 = 물결 경로) 웅덩이 칸 → 횃불 던짐(예고 = 떨어질 자리 원) → 떨어진 칸에서
 * 연결된 웅덩이를 따라 불이 도화선처럼 번진다(번지는 방향·속도가 보이게 — 다음 칸에 불씨가 먼저 켜진다, BossArena·LiquorPools).
 * 횃불은 뿌린 줄의 보스 쪽 끝에 던진다 → 불이 플레이어 쪽으로 달려간다. 술독 굴리기 웅덩이와 이어져 있으면 거기로도 번진다.
 */
import { TILE } from '../../../core/Constants';
import type { TelegraphHandle, TelegraphPathHandle } from '../../../systems/telegraph';
import type { MobContext } from '../../Mob';
import { wobblyLine } from '../curve';
import type { BossArenaApi, BossHost, BossPatternModule, PatternEnd, PatternRun, Vec } from '../types';

export interface FireSpillParams {
  telegraphMs: number;
  lengthTiles: number;
  wobbleTiles: number;
  puddleMs: number;
  torchTelegraphMs: number;
  torchFlightMs: number;
  spreadMsPerCell: number;
  fireMs: number;
  fireTickMs: number;
  firePlayerAttack: number;
  cooldownMs: number;
  arms?: number;
  armSpreadDeg?: number;
}

/** 뿌린 줄 위 점 간격 (타일) */
const SPILL_STEP_TILES = 0.5;
/** 횃불 떨어질 자리 원 반경 (타일) */
const TORCH_MARK_TILES = 1;
/** 뿌린 줄의 몇 번째 점에 횃불 (점 간격 0.5칸 — 4 = 보스에서 2칸 앞, 보스 몸에 가리지 않게) */
const TORCH_INDEX = 4;

export function spillArms(
  from: Vec,
  aim: number,
  P: Pick<FireSpillParams, 'lengthTiles' | 'wobbleTiles' | 'arms' | 'armSpreadDeg'>,
): Vec[][] {
  const arms = Math.max(1, Math.round(P.arms ?? 1));
  const step = ((P.armSpreadDeg ?? 0) * Math.PI) / 180;
  const samples = Math.max(2, Math.round(P.lengthTiles / SPILL_STEP_TILES));
  const out: Vec[][] = [];
  for (let i = 0; i < arms; i++) {
    const a = aim + (i - (arms - 1) / 2) * step;
    out.push(wobblyLine(from, Math.cos(a), Math.sin(a), P.lengthTiles * TILE, P.wobbleTiles * TILE, samples));
  }
  return out;
}

class FireSpillRun implements PatternRun {
  state: 'spillTelegraph' | 'torchTelegraph' = 'spillTelegraph';
  private until: number;
  private markers: TelegraphPathHandle[] = [];
  private torchMarker: TelegraphHandle | null = null;
  private lines: Vec[][] = [];
  private torchAt: Vec = { x: 0, y: 0 };

  constructor(
    private readonly host: BossHost,
    private readonly arena: BossArenaApi,
    ctx: MobContext,
  ) {
    const P = this.P;
    this.until = ctx.time + P.telegraphMs;
    host.setVelocity(0, 0);
    if (!host.pose.play('throw', ctx.time, { fitMs: P.telegraphMs + 200, keyAtMs: P.telegraphMs, target: ctx.player }))
      host.pose.holdFacing(ctx.time, ctx.player, P.telegraphMs);
    this.plan(ctx);
    for (const l of this.lines) this.markers.push(ctx.telegraph.path(l, P.telegraphMs, { aura: true }));
    host.emitTelegraph('fireSpill');
  }

  private get P(): FireSpillParams {
    return this.host.params<FireSpillParams>('fireSpill');
  }

  /** 횃불 출발점: throw_torch releaseFrame 의 횃불 끝(놓는 프레임은 null → 바로 앞 점) → throw 손 → 바디 중심 */
  private origin(): Vec {
    const h = this.host;
    return (
      h.pose.anchor('throw_torch', 'handAnchors', 'releaseFrame') ??
      h.pose.anchor('throw', 'handAnchors', 'releaseFrame') ??
      h.center
    );
  }

  private plan(ctx: MobContext): void {
    const h = this.host;
    this.lines = spillArms(h.center, h.angleTo(ctx.player.x, ctx.player.y), this.P);
  }

  update(ctx: MobContext): PatternEnd | null {
    const h = this.host;
    const P = this.P;
    h.setVelocity(0, 0);
    if (this.state === 'spillTelegraph') {
      this.plan(ctx);
      this.lines.forEach((l, i) => this.markers[i]?.setPoints(l));
      if (ctx.time < this.until) return null;
      this.clear();
      // 술 방울은 잔 마구리(throw releaseFrame 의 handAnchors)에서 날아간다 (웅덩이 줄은 그대로)
      const cup = h.pose.anchor('throw', 'handAnchors', 'releaseFrame');
      for (const l of this.lines) this.arena.spill(l, P, cup ?? undefined);
      h.emitAction('spill');
      const first = this.lines[0];
      this.torchAt = first[Math.min(TORCH_INDEX, first.length - 1)];
      this.state = 'torchTelegraph';
      this.until = ctx.time + P.torchTelegraphMs;
      // 아트 v3 throw_torch (releaseFrame 이 예고 끝) → 없으면 throw → 없으면 멈춤 자세
      const pose = { fitMs: P.torchTelegraphMs + 200, keyAtMs: P.torchTelegraphMs, target: this.torchAt };
      if (!h.pose.play('throw_torch', ctx.time, pose) && !h.pose.play('throw', ctx.time, pose))
        h.pose.holdFacing(ctx.time, this.torchAt, P.torchTelegraphMs);
      this.torchMarker = ctx.telegraph.circle(
        this.torchAt.x,
        this.torchAt.y,
        TORCH_MARK_TILES * TILE,
        P.torchTelegraphMs,
        {
          aura: false,
        },
      );
      return null;
    }
    if (ctx.time < this.until) return null;
    this.clear();
    this.arena.throwTorch(this.origin(), this.torchAt, P.torchFlightMs);
    h.emitAction('torchThrow');
    h.emitAttack('fireSpill');
    h.pose.release();
    return { finish: true };
  }

  private clear(): void {
    for (const m of this.markers) m.end();
    this.markers = [];
    this.torchMarker?.end();
    this.torchMarker = null;
  }

  cancel(): void {
    this.clear();
  }
}

export const fireSpillPattern: BossPatternModule = {
  name: 'fireSpill',
  isReady: (_host, ctx) => Boolean(ctx.arena),
  start: (host, ctx) => (ctx.arena ? new FireSpillRun(host, ctx.arena, ctx) : { finish: true }),
};
