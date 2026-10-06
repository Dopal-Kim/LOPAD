/**
 * 61 단계 5 (P13 §3) 보스 기둥 숨기 전략 시뮬 (순수 · 결정적 — `pillarSim.test` 가 표를 찍는다).
 * 1층 연회장(route.json arena.boss · setPieces.boss_hall 기둥 4) 안에서 보스·주인공 두 개체를 20ms 단위로 움직인다.
 * - 보스: 접근(옛 = 곧장 / 새 = 기둥 우회 `pillarGeom.steerWaypoint`) · 패턴 간격마다 돌진(예고 → 직진 → 기둥에 막히면 벽 경직
 *   = 파훼 창 ×breakDamageMult, 기둥 균열 +1) 또는 내리찍기(예고 → 반경) · 새 규칙: 가려짐 누적 ≥ hiddenMs 면 포물선 술병
 *   (착탄 원 예고 → 폭발 + 불 웅덩이) · 균열 3단 다음 충돌에서 기둥 무너짐(통과 가능). 술통·불붙은 술·한 잔 더 등 나머지 패턴은
 *   두 규칙에 같게 빠지므로 넣지 않는다(비교용 단순화 — 실제 싸움보다 덜 위험하다).
 * - 주인공 전략: hider = 보스 반대편 기둥 뒤에 붙어 있다가 보스가 벽 경직이면 나가서 때리고 돌아옴(경직이 아니어도 옆에 붙으면
 *   때림), 예고 원 안이면 밖으로 피하고 불 웅덩이엔 들어가지 않음 / brawler = 기둥을 쓰지 않고 붙어서 때림(비교 기준).
 *   돌진·내리찍기는 dodge 확률로 피한다(구르기). 접촉 피해는 붙어 있는 동안 간격마다.
 */
import { TILE } from '../../core/Constants';
import { BOSSES, PLAYER_DATA } from '../../data';
import { phaseIndexFor, resolvePatternParams } from '../../data/bossPatterns';
import { nextCrack } from '../boss/bossArtRules';
import { inflate, lineBlocked, newSteerMemo, steerWaypoint, stepHidden, type Box, type Pt } from '../boss/pillarGeom';
import { Rng } from '../rng';
import { ROUTE } from '../route';

export type PillarRules = 'old' | 'new';
export type PillarStrategy = 'hider' | 'brawler';

export interface PillarSimOpts {
  rules: PillarRules;
  strategy: PillarStrategy;
  /** 주인공 근접 DPS (공격 5 기본 공격 — weapon/dps) · 근접 사거리 px */
  dps: number;
  reachPx?: number;
  seed: number;
  /** 피하기 성공 확률 (돌진·내리찍기·술병 착탄) */
  dodge?: number;
  /** 제한 시간 ms (넘으면 시간 초과 = 패배로 셈) */
  limitMs?: number;
  /** 디버그 출력 */
  trace?: (line: string) => void;
}

export interface PillarSimResult {
  win: boolean;
  timeMs: number;
  /** 남은 보스 HP */
  bossHp: number;
  damageTaken: number;
  /** 가려진 시간 비율 · 무너진 기둥 수 · 술병 수 · 벽 경직 수 */
  hiddenShare: number;
  collapsed: number;
  lobs: number;
  wallStuns: number;
}

const DT = 20;
const BOSS_HALF = { x: 25, y: 18 };
const PLAYER_HALF = 6;

interface Pillar {
  box: Box;
  stage: number;
  solid: boolean;
}

interface Pending {
  kind: 'dash' | 'slam' | 'lob';
  at: number;
  /** dash: 예고 끝 · slam/lob: 판정 순간 */
  target: Pt;
  radius: number;
  dashUntil?: number;
  dir?: Pt;
}

function arenaPillars(): { w: number; h: number; pillars: Pillar[] } {
  const [tw, th] = (ROUTE.arena as unknown as { boss: [number, number] }).boss;
  const sp = (
    ROUTE.setPieces as unknown as Record<string, { pillars?: { at: [number, number]; size?: [number, number] }[] }>
  ).boss_hall;
  const cx = Math.floor(tw / 2);
  const cy = Math.floor(th / 2);
  const pillars = (sp?.pillars ?? []).map((p) => {
    const [w, h] = p.size ?? [1, 1];
    return {
      box: { x: (cx + p.at[0]) * TILE, y: (cy + p.at[1]) * TILE, w: w * TILE, h: h * TILE },
      stage: 0,
      solid: true,
    };
  });
  return { w: tw * TILE, h: th * TILE, pillars };
}

function overlaps(a: Box, b: Box): boolean {
  return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
}

const boxAt = (p: Pt, hx: number, hy: number): Box => ({ x: p.x - hx, y: p.y - hy, w: hx * 2, h: hy * 2 });

/** 축 나눠 이동 (Arcade 처럼 막힌 축만 멈춘다). 반환 = 막혔는지 */
function move(p: Pt, vx: number, vy: number, hx: number, hy: number, solids: Box[], W: number, H: number): boolean {
  let blocked = false;
  const nx = Math.max(hx, Math.min(W - hx, p.x + vx));
  if (nx !== p.x + vx || solids.some((s) => overlaps(boxAt({ x: nx, y: p.y }, hx, hy), s))) blocked = true;
  if (!solids.some((s) => overlaps(boxAt({ x: nx, y: p.y }, hx, hy), s))) p.x = nx;
  const ny = Math.max(hy, Math.min(H - hy, p.y + vy));
  if (ny !== p.y + vy || solids.some((s) => overlaps(boxAt({ x: p.x, y: ny }, hx, hy), s))) blocked = true;
  if (!solids.some((s) => overlaps(boxAt({ x: p.x, y: ny }, hx, hy), s))) p.y = ny;
  return blocked;
}

export function simulatePillarFight(o: PillarSimOpts): PillarSimResult {
  const def = BOSSES.stage1;
  const rng = new Rng(o.seed);
  const { w: W, h: H, pillars } = arenaPillars();
  const reach = o.reachPx ?? 20;
  const dodge = o.dodge ?? 0.6;
  const limit = o.limitMs ?? 300000;
  const P = (name: 'dash' | 'slam' | 'lobBottle', phase: number) =>
    resolvePatternParams(def, phase, name) as unknown as Record<string, number>;
  const boss = { x: W / 2 + 4 * TILE * -1, y: H / 2 };
  const pl = { x: W / 2 + 8 * TILE, y: H / 2 };
  let hp = def.hp;
  let php = PLAYER_DATA.stats.hp;
  let t = 0;
  let nextPattern = def.phases[0].intervalMs;
  let slamReady = 0;
  let lobReady = 0;
  let stunUntil = 0;
  let pending: Pending | null = null;
  let contactAt = 0;
  let hidden = 0;
  let hiddenTime = 0;
  let lobs = 0;
  let wallStuns = 0;
  const pools: { at: Pt; r: number; until: number; tickAt: number }[] = [];
  const memo = newSteerMemo();
  const plMemo = newSteerMemo();
  let damageTaken = 0;
  const hurt = (n: number) => {
    php -= n;
    damageTaken += n;
  };
  const solids = () => pillars.filter((p) => p.solid).map((p) => p.box);
  while (t < limit && hp > 0 && php > 0) {
    t += DT;
    const phase = phaseIndexFor(hp / def.hp, def.phases);
    const S = solids();
    const bc = boss;
    const isHidden = lineBlocked(bc, pl, S);
    if (isHidden) hiddenTime += DT;
    hidden = o.rules === 'new' ? stepHidden(hidden, isHidden, DT, 2) : 0;
    const stunned = t < stunUntil;
    // --- 보스 ---
    if (!stunned) {
      if (pending?.kind === 'dash' && pending.dashUntil !== undefined && t >= pending.at) {
        // 돌진 중
        const v = (P('dash', phase).speedTiles * TILE * DT) / 1000;
        const hit = move(boss, pending.dir!.x * v, pending.dir!.y * v, BOSS_HALF.x, BOSS_HALF.y, S, W, H);
        if (overlaps(boxAt(boss, BOSS_HALF.x, BOSS_HALF.y), boxAt(pl, PLAYER_HALF, PLAYER_HALF)) && !pending.radius) {
          pending.radius = 1; // 한 번만 판정
          if (rng.next() > dodge) hurt(P('dash', phase).attack);
        }
        if (hit) {
          const near = pillars.find(
            (p) => p.solid && overlaps(inflate(boxAt(boss, BOSS_HALF.x, BOSS_HALF.y), 3), p.box),
          );
          // 벽·기둥 어디든 막히면 벽 경직 (기둥이면 균열)
          wallStuns++;
          stunUntil = t + P('dash', phase).wallStunMs;
          if (near) {
            const n = nextCrack(near.stage, 3);
            if (n) near.stage = n.stage;
            if (o.rules === 'new' && n?.collapse) near.solid = false;
            else if (o.rules === 'old') near.stage = Math.min(near.stage, 3);
          }
          pending = null;
          nextPattern = t + def.phases[phase].intervalMs;
        } else if (t >= pending.dashUntil) {
          pending = null;
          nextPattern = t + def.phases[phase].intervalMs;
        }
      } else if (pending && pending.kind !== 'dash' && t >= pending.at) {
        const d = Math.hypot(pl.x - pending.target.x, pl.y - pending.target.y);
        if (pending.kind === 'slam' && d <= pending.radius + PLAYER_HALF && rng.next() > dodge)
          hurt(P('slam', phase).attack);
        if (pending.kind === 'lob') {
          const L = P('lobBottle', phase);
          if (d <= pending.radius + PLAYER_HALF && rng.next() > dodge) hurt(L.burstAttack);
          pools.push({ at: pending.target, r: pending.radius, until: t + L.poolMs, tickAt: t });
        }
        pending = null;
        nextPattern = t + def.phases[phase].intervalMs;
      } else if (pending?.kind === 'dash' && t >= pending.at - 1) {
        // 예고 끝 → 직진 시작
        pending.dir = (() => {
          const dx = pl.x - boss.x;
          const dy = pl.y - boss.y;
          const l = Math.hypot(dx, dy) || 1;
          return { x: dx / l, y: dy / l };
        })();
        pending.dashUntil = t + P('dash', phase).durationMs;
        pending.radius = 0;
      } else if (!pending) {
        const L = P('lobBottle', phase);
        if (o.rules === 'new' && hidden >= L.hiddenMs && t >= lobReady) {
          // 포물선 술병 (간격 무시)
          const n = Math.max(1, Math.round(L.count));
          const dx = pl.x - boss.x;
          const dy = pl.y - boss.y;
          const l = Math.hypot(dx, dy) || 1;
          for (let i = n - 1; i >= 0; i--) {
            const target = {
              x: pl.x + (dx / l) * L.spreadTiles * TILE * i,
              y: pl.y + (dy / l) * L.spreadTiles * TILE * i,
            };
            if (i > 0)
              pools.push({
                at: target,
                r: L.burstRadiusTiles * TILE,
                until: t + L.windupMs + L.flightMs + L.poolMs,
                tickAt: t + L.windupMs + L.flightMs,
              });
            else pending = { kind: 'lob', at: t + L.windupMs + L.flightMs, target, radius: L.burstRadiusTiles * TILE };
          }
          lobs++;
          hidden = 0;
          lobReady = t + L.cooldownMs;
        } else if (t >= nextPattern) {
          const useSlam = t >= slamReady && rng.next() < 0.4;
          if (useSlam) {
            const sP = P('slam', phase);
            pending = { kind: 'slam', at: t + sP.telegraphMs, target: { ...boss }, radius: sP.radiusTiles * TILE };
            slamReady = t + sP.cooldownMs;
          } else pending = { kind: 'dash', at: t + P('dash', phase).telegraphMs, target: { ...pl }, radius: 0 };
        } else {
          // 접근
          const sp = (def.approachSpeedTiles * TILE * DT) / 1000;
          let goal: Pt = pl;
          if (o.rules === 'new')
            goal = steerWaypoint(
              boss,
              pl,
              S.map((b) => inflate(b, BOSS_HALF.x + 2, BOSS_HALF.y + 2)),
              memo,
              {
                marginPx: 3,
                stickPx: 12,
                reachPx: 6,
              },
            );
          const dx = goal.x - boss.x;
          const dy = goal.y - boss.y;
          const l = Math.hypot(dx, dy);
          if (l > 1) move(boss, (dx / l) * sp, (dy / l) * sp, BOSS_HALF.x, BOSS_HALF.y, S, W, H);
        }
      }
    }
    // 접촉
    const touching = overlaps(inflate(boxAt(boss, BOSS_HALF.x, BOSS_HALF.y), 2), boxAt(pl, PLAYER_HALF, PLAYER_HALF));
    if (touching && !stunned && t >= contactAt) {
      if (rng.next() > dodge) hurt(def.contactAttack);
      contactAt = t + def.contactIntervalMs;
    }
    // 불 웅덩이
    for (const q of pools)
      if (t < q.until && t >= q.tickAt && Math.hypot(pl.x - q.at.x, pl.y - q.at.y) <= q.r) {
        hurt(P('lobBottle', phase).poolAttack);
        q.tickAt = t + P('lobBottle', phase).poolTickMs;
      }
    // --- 주인공 ---
    const gap = Math.max(
      0,
      Math.max(Math.abs(pl.x - boss.x) - BOSS_HALF.x, Math.abs(pl.y - boss.y) - BOSS_HALF.y) - PLAYER_HALF,
    );
    const danger =
      pending &&
      pending.kind !== 'dash' &&
      Math.hypot(pl.x - pending.target.x, pl.y - pending.target.y) <= pending.radius + PLAYER_HALF + 2
        ? pending.target
        : (pools.find((q) => t < q.until && Math.hypot(pl.x - q.at.x, pl.y - q.at.y) <= q.r + PLAYER_HALF)?.at ?? null);
    // 때릴 자리: 보스 몸 가장자리에서 사거리 안쪽 (몸에 붙지 않음 — 접촉 피해는 겹칠 때만)
    const attackSpot = (): Pt => {
      // 보스 네 옆 중 기둥에 겹치지 않고 주인공에게 가까운 곳 (기둥 너머 자리를 고르지 않게)
      const dx = BOSS_HALF.x + PLAYER_HALF + reach * 0.5;
      const dy = BOSS_HALF.y + PLAYER_HALF + reach * 0.5;
      const spots = [
        { x: boss.x - dx, y: boss.y },
        { x: boss.x + dx, y: boss.y },
        { x: boss.x, y: boss.y - dy },
        { x: boss.x, y: boss.y + dy },
      ].filter(
        (c) =>
          c.x > PLAYER_HALF &&
          c.x < W - PLAYER_HALF &&
          c.y > PLAYER_HALF &&
          c.y < H - PLAYER_HALF &&
          !S.some((b) => overlaps(boxAt(c, PLAYER_HALF, PLAYER_HALF), b)),
      );
      spots.sort(
        (a, b) =>
          Math.hypot(a.x - pl.x, a.y - pl.y) +
          (lineBlocked(pl, a, S) ? 64 : 0) -
          (Math.hypot(b.x - pl.x, b.y - pl.y) + (lineBlocked(pl, b, S) ? 64 : 0)),
      );
      return spots[0] ?? { x: boss.x, y: boss.y };
    };
    // 보스 몸에서 주인공에게 가장 가까운 점 — 근접은 몸 가장자리를 친다 (기둥 모서리 너머 중심을 볼 필요 없음)
    const nearPt = {
      x: Math.max(boss.x - BOSS_HALF.x, Math.min(boss.x + BOSS_HALF.x, pl.x)),
      y: Math.max(boss.y - BOSS_HALF.y, Math.min(boss.y + BOSS_HALF.y, pl.y)),
    };
    const canHit = gap <= reach && !lineBlocked(pl, nearPt, S);
    let goal: Pt | null = null;
    if (danger) {
      // 예고 원·불 웅덩이 밖으로 (중심에서 멀어지는 쪽)
      const dx = pl.x - danger.x || 1;
      const dy = pl.y - danger.y;
      const l = Math.hypot(dx, dy);
      goal = { x: pl.x + (dx / l) * 40, y: pl.y + (dy / l) * 40 };
    } else if (!stunned && gap < reach * 0.4) {
      // 치고 빠지기: 보스가 몸으로 밀고 들어오면 한 발 물러난다 (접촉 피해를 그냥 받지 않음)
      const dx = pl.x - boss.x || 1;
      const dy = pl.y - boss.y;
      const l = Math.hypot(dx, dy);
      goal = { x: pl.x + (dx / l) * 24, y: pl.y + (dy / l) * 24 };
    } else if (o.strategy === 'brawler' || stunned) {
      if (!canHit || gap > reach - 4 || touching) goal = attackSpot();
    } else {
      // hider: 가장 가까운 서 있는 기둥의 보스 반대편
      const cover = pillars
        .filter((p) => p.solid)
        .map((p) => {
          const c = { x: p.box.x + p.box.w / 2, y: p.box.y + p.box.h / 2 };
          const dx = c.x - boss.x;
          const dy = c.y - boss.y;
          const l = Math.hypot(dx, dy) || 1;
          const off = p.box.w / 2 + PLAYER_HALF + 3;
          return { x: c.x + (dx / l) * off, y: c.y + (dy / l) * off };
        })
        .filter((c) => !pools.some((q) => t < q.until && Math.hypot(c.x - q.at.x, c.y - q.at.y) <= q.r + PLAYER_HALF))
        .sort((a, b) => Math.hypot(a.x - pl.x, a.y - pl.y) - Math.hypot(b.x - pl.x, b.y - pl.y))[0];
      goal = cover ?? (!canHit || gap > reach - 4 || touching ? attackSpot() : null);
    }
    if (goal) {
      // 기둥을 돌아서 (주인공도 같은 우회 규칙)
      goal = steerWaypoint(
        pl,
        goal,
        S.map((b) => inflate(b, PLAYER_HALF + 1)),
        plMemo,
        {
          marginPx: 2,
          stickPx: 8,
          reachPx: 4,
        },
      );
      const dx = goal.x - pl.x;
      const dy = goal.y - pl.y;
      const l = Math.hypot(dx, dy);
      const sp = (PLAYER_DATA.stats.speedTiles * TILE * DT) / 1000;
      if (l > 1) move(pl, (dx / l) * Math.min(sp, l), (dy / l) * Math.min(sp, l), PLAYER_HALF, PLAYER_HALF, S, W, H);
    }
    if (o.trace && t % 200 === 0 && t < 30000)
      o.trace(
        `${t} st=${stunned} boss=${Math.round(boss.x)},${Math.round(boss.y)} pl=${Math.round(pl.x)},${Math.round(pl.y)} gap=${Math.round(gap)} blk=${lineBlocked(pl, boss, S)} goal=${goal ? Math.round(goal.x) + ',' + Math.round(goal.y) : '-'}`,
      );
    // 때리기: 사거리 안 · 가로막히지 않음
    if (canHit) {
      const mult = stunned ? (def.breakDamageMult ?? 1) : 1;
      hp -= (o.dps * mult * DT) / 1000;
    }
  }
  return {
    win: hp <= 0,
    timeMs: t,
    bossHp: Math.max(0, Math.round(hp)),
    damageTaken: Math.round(damageTaken),
    hiddenShare: hiddenTime / Math.max(1, t),
    collapsed: pillars.filter((p) => !p.solid).length,
    lobs,
    wallStuns,
  };
}

export interface PillarSimRow {
  rules: PillarRules;
  strategy: PillarStrategy;
  winRate: number;
  /** 이긴 판의 평균 시간 (초) · 평균 받은 피해 · 가려짐 비율 · 무너짐 · 술병 · 벽 경직 */
  winSec: number;
  damage: number;
  hidden: number;
  collapsed: number;
  lobs: number;
  wallStuns: number;
}

/** 시드 n 판 평균 */
export function pillarSimTable(dps: number, n = 24, dodge = 0.6): PillarSimRow[] {
  const rows: PillarSimRow[] = [];
  for (const strategy of ['hider', 'brawler'] as const)
    for (const rules of ['old', 'new'] as const) {
      const rs = Array.from({ length: n }, (_, i) =>
        simulatePillarFight({ rules, strategy, dps, seed: 1000 + i, dodge }),
      );
      const wins = rs.filter((r) => r.win);
      const avg = (f: (r: PillarSimResult) => number, list = rs) =>
        list.length ? list.reduce((a, r) => a + f(r), 0) / list.length : 0;
      rows.push({
        rules,
        strategy,
        winRate: wins.length / n,
        winSec: Math.round(avg((r) => r.timeMs, wins) / 100) / 10,
        damage: Math.round(avg((r) => r.damageTaken)),
        hidden: Math.round(avg((r) => r.hiddenShare) * 100) / 100,
        collapsed: Math.round(avg((r) => r.collapsed) * 10) / 10,
        lobs: Math.round(avg((r) => r.lobs) * 10) / 10,
        wallStuns: Math.round(avg((r) => r.wallStuns) * 10) / 10,
      });
    }
  return rows;
}
