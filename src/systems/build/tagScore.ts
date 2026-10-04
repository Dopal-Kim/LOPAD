/**
 * 57라운드 Q25 태그 점수 (설계안 1.2 A): 패시브 종류당 태그마다 1점 + Lv3(최대 레벨) 달성 시 +1 · 갈래 노드 태그마다 1점 ·
 * 강화 시 갈래 태그 +1(최대 reinforceTagMax) · 저주 이득·영구 보너스. 이중 개성은 점수 없음. Phaser 의존 없음.
 */
import { TAG_IDS, type BuildScoring, type SetThreshold, type TagId } from '../../data/buildTypes';

export type TagScores = Record<TagId, number>;

export interface TagScoreInput {
  /** 보유 패시브 (태그 · 레벨 · 최대 레벨) */
  passives: readonly { tags: readonly TagId[]; level: number; maxLevel: number }[];
  /** 선택한 갈래 노드 (경로 순서 — 마지막이 현재 노드) */
  branchNodes: readonly { tags?: readonly TagId[] }[];
  /** 강화 횟수 */
  reinforce: number;
  /** 저주 이득·영구 보너스 등 더하는 점수 */
  extra?: readonly Partial<Record<TagId, number>>[];
}

export function emptyScores(): TagScores {
  const out = {} as TagScores;
  for (const t of TAG_IDS) out[t] = 0;
  return out;
}

export function tagScores(input: TagScoreInput, S: BuildScoring): TagScores {
  const out = emptyScores();
  for (const p of input.passives) {
    if (p.level <= 0) continue;
    const bonus = p.level >= p.maxLevel ? S.passiveMaxLevelBonus : 0;
    for (const t of p.tags) out[t] += S.perPassive + bonus;
  }
  for (const n of input.branchNodes) for (const t of n.tags ?? []) out[t] += S.perBranchNode;
  const cur = input.branchNodes[input.branchNodes.length - 1];
  const r = Math.min(Math.max(0, input.reinforce), S.reinforceTagMax);
  if (cur?.tags?.length && r > 0) {
    const targets = S.reinforceTagTarget === 'all' ? cur.tags : cur.tags.slice(0, 1);
    for (const t of targets) out[t] += r;
  }
  for (const e of input.extra ?? []) for (const [t, v] of Object.entries(e)) out[t as TagId] += v ?? 0;
  return out;
}

/** 점수 → 켜진 세트 단계 (임계 2/4/6 중 넘은 가장 높은 것, 없으면 0) */
export function setStage(score: number, thresholds: readonly SetThreshold[]): 0 | SetThreshold {
  let s: 0 | SetThreshold = 0;
  for (const th of thresholds) if (score >= th) s = th;
  return s;
}

/** 다음 임계 (다 넘었으면 null) */
export function nextThreshold(score: number, thresholds: readonly SetThreshold[]): number | null {
  for (const th of thresholds) if (score < th) return th;
  return null;
}
