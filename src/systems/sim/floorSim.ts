/**
 * 61라운드 P9·P3: 지금 데이터로 1층(노드 지도 층) 하나를 어림한다 — `nodeSim` 을 층 구성(route.json floors)에 적용.
 * 61라운드 단계 2: 잔 구간은 단마다 종류·웨이브가 정해져 있으므로(`columns`) 길 = 단마다 고른 종류.
 * - 전투 많은 길(maxBattle): 단1 전투 · 단2 전투 · 단3 엘리트 위험 전투 · 단4 쉼터
 * - 보통(normal): 단1 전투 · 단2 이벤트 · 단3 전투 · 단4 상점
 * 위험 노드 엘리트는 HP 배율만(`bundle2.elite.hpMult` — 웨이브마다 한 마리), 패시브·빌드 배율은 넣지 않는다(기본기 기준선).
 * 메뉴 = 전투 보상(노드당 1) + 개성 임계 + 비전투 노드 메뉴(상점·쉼터·이벤트 1). 결과는 `nodeSim.test` 가 표로 찍는다.
 */
import { SIM } from '../../core/Constants';
import { BOSSES, ECONOMY, ENEMIES, PLAYER_DATA, STAGES, WEAPONS } from '../../data';
import { BUILD } from '../../data/build';
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
  /** 처치 개성으로 넘는 개성 임계 수 (3지선다 메뉴 수의 하한) */
  personalityMenus: number;
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
  const killMult = BUILD.personality.normalKillMult;
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
    } else {
      const ms = SIM.NONCOMBAT_MS[st.kind as keyof typeof SIM.NONCOMBAT_MS] ?? SIM.NONCOMBAT_MS.event;
      nodes.push({ kind: st.kind, ms: ms + SIM.EXIT_WALK_MS + SIM.CHOOSE_MS, kills: 0, damageTaken: 0 });
      if (st.kind === 'shop' || st.kind === 'rest' || st.kind === 'event') menus += 1;
    }
  }
  const boss = BOSSES[stage.boss];
  const bossMs = boss ? estimateBossMs(player, w, boss) : 0;
  if (boss) nodes.push({ kind: 'boss', ms: bossMs, kills: 1, damageTaken: 0 });
  const thresholds = w.personality.thresholds;
  const personalityMenus = thresholds.filter((t) => personality >= t).length;
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
  };
}
