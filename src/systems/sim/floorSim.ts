/**
 * 61라운드 P9: 지금 데이터로 1층(노드 지도 층) 하나를 어림한다 — `nodeSim` 을 층 구성(route.json floors)에 적용.
 * 길 3종: 전투 많은 길(잔 구간 노드가 전부 전투) · 보통(전투 2 + 이벤트) · 전투 적은 길(전투 1 + 상점 + 휴식).
 * 위험 노드·도전 성소·엘리트·패시브·빌드 배율은 넣지 않는다(기본기 기준선). 결과는 `nodeSim.test`/`floorSim.test` 가 표로 찍는다.
 */
import { SIM } from '../../core/Constants';
import { BOSSES, ECONOMY, ENEMIES, PLAYER_DATA, STAGES, WEAPONS } from '../../data';
import { BUILD } from '../../data/build';
import type { WaveEntry } from '../../data/types';
import { ROUTE } from '../route';
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
}

export interface FloorEstimate {
  weapon: string;
  dps: number;
  path: string;
  nodes: FloorNodeEstimate[];
  totalMs: number;
  kills: number;
  damageTaken: number;
  personality: number;
  /** 처치 개성으로 넘는 개성 임계 수 (3지선다 메뉴 수의 하한) */
  personalityMenus: number;
}

export const FLOOR_PATHS: Record<string, string[]> = {
  /** 잔 구간 3단 전부 전투 */
  maxBattle: ['battle', 'battle', 'battle'],
  normal: ['battle', 'event', 'battle'],
  minBattle: ['battle', 'shop', 'rest'],
};

export function estimateFloor(weaponId: string, stageId = 'stage1', pathKey = 'normal'): FloorEstimate {
  const w: SimWeapon = WEAPONS[weaponId];
  const stage = STAGES[stageId];
  const floor = ROUTE.floors[stageId];
  const player = simPlayerOf(PLAYER_DATA.stats, ECONOMY.critDamageMult);
  const killMult = BUILD.personality.normalKillMult;
  const battle = (waves: readonly (readonly WaveEntry[])[]): NodeEstimate =>
    estimateBattleNode({
      player,
      weapon: w,
      enemies: ENEMIES,
      waves,
      enemyScale: stage.enemyScale,
      spawnDistTiles: stage.trial.spawnMinDistTiles,
      personalityKillMult: killMult,
    });
  const nodes: FloorNodeEstimate[] = [];
  let personality = 0;
  const kinds = [
    ...(floor?.journey ?? []),
    ...(FLOOR_PATHS[pathKey] ?? FLOOR_PATHS.normal).slice(0, floor?.laneLength ?? 3),
  ];
  for (const kind of kinds) {
    const def = ROUTE.kinds[kind as keyof typeof ROUTE.kinds];
    const waves = def?.waves ?? (def?.type === 'battle' ? stage.trial.waves : null);
    if (waves) {
      const e = battle(waves);
      nodes.push({ kind, ms: e.totalMs, kills: e.kills, damageTaken: e.damageTaken });
      personality += e.personality;
    } else {
      const ms = SIM.NONCOMBAT_MS[kind as keyof typeof SIM.NONCOMBAT_MS] ?? SIM.NONCOMBAT_MS.event;
      nodes.push({ kind, ms: ms + SIM.EXIT_WALK_MS + SIM.CHOOSE_MS, kills: 0, damageTaken: 0 });
    }
  }
  const boss = BOSSES[stage.boss];
  if (boss) nodes.push({ kind: 'boss', ms: estimateBossMs(player, w, boss), kills: 1, damageTaken: 0 });
  const thresholds = w.personality.thresholds;
  const personalityMenus = thresholds.filter((t) => personality >= t).length;
  // 3지선다 고르는 시간
  const menuMs = personalityMenus * SIM.MENU_MS;
  return {
    weapon: weaponId,
    dps: Math.round(weaponDps(player, w).dps * 10) / 10,
    path: pathKey,
    nodes,
    totalMs: nodes.reduce((a, n) => a + n.ms, 0) + menuMs,
    kills: nodes.reduce((a, n) => a + n.kills, 0),
    damageTaken: nodes.reduce((a, n) => a + n.damageTaken, 0),
    personality: Math.round(personality),
    personalityMenus,
  };
}
