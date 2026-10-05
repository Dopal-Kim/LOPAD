/**
 * 61라운드 P9·P3: 지금 데이터로 1층(노드 지도 층) 하나를 어림한다 — `nodeSim` 을 층 구성(route.json floors)에 적용.
 * 61라운드 단계 2: 잔 구간은 단마다 종류·웨이브가 정해져 있으므로(`columns`) 길 = 단마다 고른 종류.
 * - 전투 많은 길(maxBattle): 단1 전투 · 단2 전투 · 단3 엘리트 위험 전투 · 단4 쉼터
 * - 보통(normal): 단1 전투 · 단2 이벤트 · 단3 전투 · 단4 상점
 * 위험 노드 엘리트는 HP 배율만(`bundle2.elite.hpMult` — 웨이브마다 한 마리), 패시브·빌드 배율은 넣지 않는다(기본기 기준선).
 * 메뉴 = 전투 보상(노드당 1) + 각성 눈금 + 비전투 노드 메뉴(상점·쉼터·이벤트 1). 결과는 `nodeSim.test` 가 표로 찍는다.
 * 61 G (P12): 각성 게이지 추적 — 단마다 누적(처치만 / 기대치 = 처치 + 완 + 획 자국 + 이벤트, `SIM.GROWTH` 가정)과
 * 1차 각성(90)·2차 각성(220) 눈금에 닿는 단.
 */
import { SIM } from '../../core/Constants';
import { BOSSES, ECONOMY, ENEMIES, PLAYER_DATA, STAGES, WEAPONS } from '../../data';
import { GROWTH, baseMarksOn } from '../../data/growth';
import { BUNDLE2 } from '../../data/bundle2';
import type { WaveEntry } from '../../data/types';
import { ROUTE, nodeWaves, type RouteKind } from '../route';
import {
  estimateBattleNode,
  estimateBossMs,
  simPlayerOf,
  weaponDps,
  type NodeEstimate,
  type SimWeapon,
} from './nodeSim';

export interface FloorNodeEstimate {
  kind: string;
  ms: number;
  kills: number;
  damageTaken: number;
  elite?: boolean;
}

export interface FloorEstimate {
  weapon: string;
  dps: number;
  path: string;
  nodes: FloorNodeEstimate[];
  totalMs: number;
  /** 보스를 뺀 시간 · 보스를 `SIM.BOSS_TARGET_MS`(보스 재구성 목표)로 바꾼 합 */
  withoutBossMs: number;
  withBossTargetMs: number;
  kills: number;
  damageTaken: number;
  personality: number;
  /** 보스 전 기대 게이지로 넘는 눈금 수 (성장 메뉴 수) */
  personalityMenus: number;
  /** 61 G: 단(여정·단1~4)별 누적 각성 게이지 — 처치만 · 기대치 */
  growth: { steps: string[]; killsOnly: number[]; expected: number[] };
  /** 61 G: 1차·2차 각성 눈금에 닿는 단 (기대치 기준, 못 닿으면 null) · 보스 전 기대 게이지 */
  awaken1At: string | null;
  awaken2At: string | null;
  gaugeBeforeBoss: number;
  /** 메뉴 수 (보상 + 개성 + 비전투) */
  menus: number;
}

/** 잔 구간 단마다 고르는 종류 (`elite` = 그 단 전투가 엘리트 위험 노드) */
export const FLOOR_PATHS: Record<string, (LaneStep | RouteKind)[]> = {
  maxBattle: ['battle', 'battle', { kind: 'battle', elite: true }, 'rest'],
  normal: ['battle', 'event', 'battle', 'shop'],
};

export interface LaneStep {
  kind: RouteKind;
  elite?: boolean;
}

const stepOf = (s: LaneStep | RouteKind): LaneStep => (typeof s === 'string' ? { kind: s } : s);

export function estimateFloor(weaponId: string, stageId = 'stage1', pathKey = 'normal'): FloorEstimate {
  const w: SimWeapon = WEAPONS[weaponId];
  const stage = STAGES[stageId];
  const floor = ROUTE.floors[stageId];
  const player = simPlayerOf(PLAYER_DATA.stats, ECONOMY.critDamageMult);
  const killMult = GROWTH.gain.normalKillMult;
  const battle = (waves: readonly (readonly WaveEntry[])[], elite: boolean): NodeEstimate =>
    estimateBattleNode({
      player,
      weapon: w,
      enemies: ENEMIES,
      waves,
      enemyScale: stage.enemyScale,
      spawnDistTiles: stage.trial.spawnMinDistTiles,
      personalityKillMult: killMult,
      ...(elite ? { eliteHpMult: BUNDLE2.elite.hpMult } : {}),
    });
  const nodes: FloorNodeEstimate[] = [];
  let personality = 0;
  let menus = 0;
  // 61 G 각성 게이지 추적
  const G = SIM.GROWTH;
  const gradeGain = BUNDLE2.grade.perfect.personality;
  const markGain = BUNDLE2.rewards.personality.amount;
  const eventGain = 30;
  let expected = 0;
  let markLeft = G.MARK_REWARD_EXPECT;
  const growth = { steps: [] as string[], killsOnly: [] as number[], expected: [] as number[] };
  const J = floor?.journey.length ?? 0;
  const steps: { kind: RouteKind; col: number; elite: boolean }[] = [
    ...(floor?.journey ?? []).map((kind, col) => ({ kind, col, elite: false })),
    ...(FLOOR_PATHS[pathKey] ?? FLOOR_PATHS.normal)
      .slice(0, floor?.laneLength ?? 4)
      .map((s, i) => ({ ...stepOf(s), col: J + i, elite: Boolean(stepOf(s).elite) })),
  ];
  for (const st of steps) {
    const def = ROUTE.kinds[st.kind];
    const waves = nodeWaves(stageId, st) ?? (def?.type === 'battle' ? stage.trial.waves : null);
    if (waves) {
      const e = battle(waves, st.elite);
      nodes.push({ kind: st.kind, ms: e.totalMs, kills: e.kills, damageTaken: e.damageTaken, elite: st.elite });
      personality += e.personality;
      menus += 1;
      // 완(위험 노드 ×2) · 획 자국 (층당 1회 기대 — 첫 전투 보상들에 나눠)
      const risk = st.elite ? BUNDLE2.grade.riskMult : 1;
      const mark = Math.min(markLeft, G.MARK_REWARD_EXPECT / 2);
      markLeft -= mark;
      expected += e.personality + gradeGain * risk * G.GRADE_PERFECT_SHARE + markGain * mark;
    } else {
      const ms = SIM.NONCOMBAT_MS[st.kind as keyof typeof SIM.NONCOMBAT_MS] ?? SIM.NONCOMBAT_MS.event;
      nodes.push({ kind: st.kind, ms: ms + SIM.EXIT_WALK_MS + SIM.CHOOSE_MS, kills: 0, damageTaken: 0 });
      if (st.kind === 'shop' || st.kind === 'rest' || st.kind === 'event') menus += 1;
      if (st.kind === 'event') expected += eventGain * G.EVENT_GAUGE_SHARE;
    }
    growth.steps.push(st.col < J ? `여정${st.col + 1}` : `단${st.col - J + 1}`);
    growth.killsOnly.push(Math.round(personality));
    growth.expected.push(Math.round(expected));
  }
  const boss = BOSSES[stage.boss];
  const bossMs = boss ? estimateBossMs(player, w, boss) : 0;
  if (boss) nodes.push({ kind: 'boss', ms: bossMs, kills: 1, damageTaken: 0 });
  const marks = baseMarksOn(1);
  const personalityMenus = marks.filter((m) => expected >= m.at).length;
  const reach = (kind: string) => {
    const at = marks.find((m) => m.kind === kind)?.at ?? Infinity;
    const i = growth.expected.findIndex((v) => v >= at);
    return i >= 0 ? growth.steps[i] : null;
  };
  menus += personalityMenus + (boss ? 1 : 0);
  // 메뉴 고르는 시간 (3지선다·보상)
  const menuMs = menus * SIM.MENU_MS;
  const totalMs = nodes.reduce((a, n) => a + n.ms, 0) + menuMs;
  return {
    weapon: weaponId,
    dps: Math.round(weaponDps(player, w).dps * 10) / 10,
    path: pathKey,
    nodes,
    totalMs,
    withoutBossMs: totalMs - bossMs,
    withBossTargetMs: totalMs - bossMs + SIM.BOSS_TARGET_MS,
    kills: nodes.reduce((a, n) => a + n.kills, 0),
    damageTaken: nodes.reduce((a, n) => a + n.damageTaken, 0),
    personality: Math.round(personality),
    personalityMenus,
    menus,
    growth,
    awaken1At: reach('awaken1'),
    awaken2At: reach('awaken2'),
    gaugeBeforeBoss: Math.round(expected),
  };
}
