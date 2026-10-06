/**
 * 61 단계 5 (P13 §3) 포물선 술병 던지기: 주인공이 보스 기준으로 기둥 뒤에 hiddenMs 넘게 가려지면(방 `hiddenMs` — 보이면 줄어드는 누적)
 * 패턴 간격을 기다리지 않고(`urgent`) 바로 던진다. 착탄 자리 원 예고(windupMs + flightMs, 0.6초 이상) → 높은 포물선(벽·기둥 위로)
 * → 떨어진 자리 폭발 + 불 웅덩이 — 독주 행상 화염 술병과 같은 위험물(`MobContext.hazards.throwBottle`, 그림 fire_bottle_thrown·
 * fire_bottle_burst·fire_pool). 둘째 병부터는 보스 → 주인공 방향으로 spreadTiles 씩 더 뒤(물러날 자리)에 떨어진다.
 */
import { TILE } from '../../../core/Constants';
import type { TelegraphHandle } from '../../../systems/telegraph';
import type { MobContext } from '../../Mob';
import type { BossHost, BossPatternModule, PatternEnd, PatternRun, Vec } from '../types';

export interface LobBottleParams {
  /** 이 누적 가려짐(ms) 이상이면 던진다 */
  hiddenMs: number;
  /** 들어 올림 → 놓기 (예고 시작부터) · 병 비행 */
  windupMs: number;
  flightMs: number;
  /** 포물선 꼭대기 높이 (칸 — 기둥 그림보다 높게) */
  arcTiles: number;
  burstRadiusTiles: number;
  burstAttack: number;
  poolMs: number;
  poolTickMs: number;
  poolAttack: number;
  count: number;
  spreadTiles: number;
  cooldownMs: number;
}

/** 착탄 자리: 첫 병 = 주인공 발, 다음 병 = 보스 → 주인공 방향으로 spread 씩 더 뒤 */
export function lobTargets(boss: Vec, player: Vec, count: number, spreadPx: number): Vec[] {
  const dx = player.x - boss.x;
  const dy = player.y - boss.y;
  const d = Math.hypot(dx, dy) || 1;
  const out: Vec[] = [];
  for (let i = 0; i < Math.max(1, Math.round(count)); i++)
    out.push({ x: player.x + (dx / d) * spreadPx * i, y: player.y + (dy / d) * spreadPx * i });
  return out;
}

class LobBottleRun implements PatternRun {
  readonly state = 'windup' as const;
  private readonly releaseAt: number;
  private readonly targets: Vec[];
  private readonly marks: TelegraphHandle[] = [];

  constructor(
    private readonly host: BossHost,
    ctx: MobContext,
  ) {
    const P = this.P;
    const h = host;
    this.releaseAt = ctx.time + P.windupMs;
    h.setVelocity(0, 0);
    this.targets = lobTargets(h.center, ctx.player, P.count, P.spreadTiles * TILE);
    const r = P.burstRadiusTiles * TILE;
    for (const t of this.targets) this.marks.push(ctx.telegraph.circle(t.x, t.y, r, P.windupMs + P.flightMs, {}));
    if (!h.pose.play('throw', ctx.time, { fitMs: P.windupMs + 200, keyAtMs: P.windupMs, target: ctx.player }))
      h.pose.holdFacing(ctx.time, ctx.player, P.windupMs);
    h.emitTelegraph('lobBottle');
  }

  private get P(): LobBottleParams {
    return this.host.params<LobBottleParams>('lobBottle');
  }

  update(ctx: MobContext): PatternEnd | null {
    const h = this.host;
    h.setVelocity(0, 0);
    if (ctx.time < this.releaseAt) return null;
    const P = this.P;
    // 손(throw releaseFrame 앵커) 아래 땅에서 손 높이로 출발 — 없으면 바디 중심
    const hand = h.pose.anchor('throw', 'handAnchors', 'releaseFrame') ?? h.center;
    const from = { x: hand.x, y: h.pos.y };
    const handPx = Math.max(0, h.pos.y - hand.y);
    this.targets.forEach((to, i) => {
      ctx.hazards?.throwBottle(from, handPx, to, P, 1);
      h.emitAction('lobThrow', i);
    });
    h.emitAttack('lobBottle');
    ctx.arena?.coverReset();
    h.pose.release();
    // 예고 원은 착탄까지 그대로 (windup + flight 길이로 만들었다)
    this.marks.length = 0;
    return { finish: true };
  }

  cancel(): void {
    for (const m of this.marks) m.end();
    this.marks.length = 0;
  }
}

export const lobBottlePattern: BossPatternModule = {
  name: 'lobBottle',
  urgent: true,
  isReady: (host, ctx) =>
    Boolean(ctx.arena && ctx.hazards) &&
    (ctx.arena?.hiddenMs ?? 0) >= host.params<LobBottleParams>('lobBottle').hiddenMs,
  start: (host, ctx) => (ctx.arena && ctx.hazards ? new LobBottleRun(host, ctx) : { finish: true }),
};
