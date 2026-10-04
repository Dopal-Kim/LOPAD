/**
 * 57라운드 개성 3지선다 칸 (27 Q4 확장 · 57 Q37 · 설계안 2.6) + 최종 각성 조건(Q33) + 이중 개성 자격(Q27). Phaser 의존 없음.
 * - 1단 임계 100 = [1단 A / 1단 B / 강화] · 2단 임계 200 = [2단 α / 2단 β / 강화]
 * - 그 뒤 200마다 = [강화 / 피의 계약 / 각성(조건 미충족이면 잠김 + 조건 안내)] — 27라운드 '게이지 정지' 규칙 대체
 * - 각성 후 강화 상한 3 → 5
 */
import type { DualTraitDef, TagId } from '../../data/buildTypes';
import type { WeaponEvolution } from '../../data/types';
import type { TagScores } from './tagScore';

export type EvolveSlotKind = 'branchA' | 'branchB' | 'reinforce' | 'bloodPact' | 'awaken';

export interface EvolveSlot {
  kind: EvolveSlotKind;
  enabled: boolean;
  /** 갈래 칸이면 그 노드 */
  node?: WeaponEvolution;
  /** 잠긴 각성 칸 — 조건 안내 */
  locked?: { condition: string } | null;
  /** 못 고르는 이유 (자리표시) */
  reason?: string;
}

export interface EvolveSlotInput {
  /** 다음 단계 갈래 선택지 (트리가 끝났으면 []) */
  options: readonly WeaponEvolution[];
  canReinforce: boolean;
  /** 저주가 걸려 있음 (동시 1개 — 계약 칸 막힘) */
  curseActive: boolean;
  /** 계약 풀에 뽑을 저주가 있음 */
  pactAvailable: boolean;
  awaken: { ready: boolean; done: boolean; condition: string };
}

export function evolveSlots(i: EvolveSlotInput): EvolveSlot[] {
  if (i.options.length > 0) {
    const out: EvolveSlot[] = (['branchA', 'branchB'] as const).map((kind, idx) => {
      const node = i.options[idx];
      return node ? { kind, enabled: true, node } : { kind, enabled: false, reason: '갈래 없음' };
    });
    out.push({ kind: 'reinforce', enabled: i.canReinforce, ...(i.canReinforce ? {} : { reason: '강화 최대' }) });
    return out;
  }
  return [
    { kind: 'reinforce', enabled: i.canReinforce, ...(i.canReinforce ? {} : { reason: '강화 최대' }) },
    {
      kind: 'bloodPact',
      enabled: !i.curseActive && i.pactAvailable,
      ...(i.curseActive ? { reason: '저주는 동시에 하나' } : {}),
    },
    i.awaken.done
      ? { kind: 'awaken', enabled: false, reason: '각성 완료' }
      : i.awaken.ready
        ? { kind: 'awaken', enabled: true }
        : { kind: 'awaken', enabled: false, locked: { condition: i.awaken.condition } },
  ];
}

/** 열린 칸이 하나라도 있는가 (없으면 게이지를 멈춘다) */
export function anySlotOpen(slots: readonly EvolveSlot[]): boolean {
  return slots.some((s) => s.enabled);
}

export interface AwakenInput {
  /** 선택한 갈래 노드 (경로 순서) */
  nodes: readonly WeaponEvolution[];
  scores: TagScores;
  /** 처치한 보스의 가장 높은 층 (1부터, 없으면 0) */
  bossFloorCleared: number;
  /** 시험장: 층 조건 무시 */
  lab: boolean;
  tagScore: number;
  afterBossFloor: number;
}

/** 각성 조건 (57 Q33 A): 2단 + 그 2단 태그 중 하나 tagScore 점 + afterBossFloor 층 보스 처치 이후 */
export function awakenReady(a: AwakenInput): { ready: boolean; tier2: boolean; tagOk: boolean; floorOk: boolean } {
  const tier2Node = a.nodes.length >= 2 ? a.nodes[1] : null;
  const tagOk = Boolean(tier2Node?.tags?.some((t) => a.scores[t] >= a.tagScore));
  const floorOk = a.lab || a.bossFloorCleared >= a.afterBossFloor;
  return { ready: Boolean(tier2Node) && tagOk && floorOk, tier2: Boolean(tier2Node), tagOk, floorOk };
}

/**
 * 이중 개성 자격 (57 Q27): 갈래 노드가 경로에 있고 짝 태그 점수가 (1단 tier1 · 2단 tier2) 이상, 아직 얻지 않음.
 * 데이터 순서대로 (같은 갈래에 둘이면 일반 짝 → 취기 짝 순)
 */
export function eligibleDualTraits(
  defs: readonly DualTraitDef[],
  weapon: string,
  path: readonly string[],
  scores: TagScores,
  owned: ReadonlySet<string>,
  need: { tier1Score: number; tier2Score: number },
): DualTraitDef[] {
  return defs.filter((d) => {
    if (d.weapon !== weapon || owned.has(d.id) || d.live === false) return false;
    const depth = path.indexOf(d.branch);
    if (depth < 0) return false;
    const want = depth === 0 ? need.tier1Score : need.tier2Score;
    return scores[d.tag as TagId] >= want;
  });
}

/** 1단 짝인가 (경로 첫 노드) */
export function dualTier(d: DualTraitDef, path: readonly string[]): 1 | 2 {
  return path.indexOf(d.branch) <= 0 ? 1 : 2;
}
