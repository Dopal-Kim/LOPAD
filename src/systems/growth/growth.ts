/**
 * 61라운드 단계 4 P12 무기 성장 규칙 (Phaser 의존 없음): 눈금 목록 · 대기 눈금 · 눈금 종류 보정 · 개성 풀·제시.
 * 눈금 = 층 기본 눈금(growth.json marks — 1층 30 ◇ / 90 ◆ / 150 ◇ / 220 ◆ / 290 ◇) + 그 뒤 repeatEvery 마다 단련 눈금.
 * 게이지는 런 누적(줄지 않음), 처리한 눈금 수(`WeaponState.marksDone`)로 다음 눈금을 찾는다.
 */
import { GROWTH, TRAITS, baseMarksOn, growthBranch, pathTint } from '../../data/growth';
import type { FloorScope } from '../../data/floorScope';
import type { GrowthMarkKind, TraitDef } from '../../data/growthTypes';

export interface GrowthMark {
  /** 눈금 순번 (0부터) */
  index: number;
  at: number;
  kind: GrowthMarkKind;
}

/** 눈금 목록: 기본 눈금 + 단련 눈금을 count 개가 될 때까지 (최소 기본 눈금 수) */
export function growthMarks(floor: FloorScope, count = 0): GrowthMark[] {
  const base = baseMarksOn(floor);
  const out: GrowthMark[] = base.map((m, index) => ({ index, at: m.at, kind: m.kind }));
  let at = base[base.length - 1].at;
  while (out.length < count) {
    at += GROWTH.repeatEvery;
    out.push({ index: out.length, at, kind: 'temper' });
  }
  return out;
}

/** i 번째 눈금 */
export function markAt(floor: FloorScope, index: number): GrowthMark {
  return growthMarks(floor, index + 1)[index];
}

/** 아직 처리하지 않은 첫 눈금 (게이지가 넘었든 아니든) */
export function nextMarkOf(floor: FloorScope, marksDone: number): GrowthMark {
  return markAt(floor, marksDone);
}

/** 게이지가 넘었는데 처리하지 않은 눈금 (없으면 null) */
export function pendingMarkOf(floor: FloorScope, gauge: number, marksDone: number): GrowthMark | null {
  const m = markAt(floor, marksDone);
  return gauge >= m.at ? m : null;
}

/** 이번 게이지까지 넘긴 눈금 수 */
export function marksReached(floor: FloorScope, gauge: number): number {
  let n = 0;
  while (markAt(floor, n).at <= gauge) n += 1;
  return n;
}

/**
 * 눈금 종류 보정 (각성 단계와 어긋나면): 1차 눈금인데 이미 1차면 개성 · 2차 눈금인데 아직 0단이면 1차 · 이미 2차면 개성.
 * 단련 눈금은 2차 각성 전이면 개성
 */
export function effectiveKind(kind: GrowthMarkKind, stage: number): GrowthMarkKind {
  if (kind === 'awaken1') return stage >= 1 ? 'trait' : 'awaken1';
  if (kind === 'awaken2') return stage >= 2 ? 'trait' : stage === 0 ? 'awaken1' : 'awaken2';
  if (kind === 'temper') return stage >= 2 ? 'temper' : 'trait';
  return 'trait';
}

/** 지금 고를 수 있는 개성 (이 무기 기본 + 고른 갈래 것, 이미 가진 것 제외) */
export function traitPool(weapon: string, branch: string | null, owned: readonly string[]): TraitDef[] {
  return TRAITS.filter((t) => t.weapon === weapon && (!t.branch || t.branch === branch) && !owned.includes(t.id));
}

/**
 * 개성 제시 n장 (P12: 갈래 개성 우선 1장 — 갈래 개성이 남아 있으면 첫 장은 그중 하나). rnd() ∈ [0,1).
 * 나머지는 같은 칸(verb)이 겹치지 않게 고르고, 모자라면 아무거나
 */
export function pickTraits(pool: readonly TraitDef[], n: number, rnd: () => number): TraitDef[] {
  const out: TraitDef[] = [];
  const take = (list: readonly TraitDef[]) => {
    const rest = list.filter((t) => !out.includes(t));
    if (rest.length === 0) return false;
    out.push(rest[Math.floor(rnd() * rest.length) % rest.length]);
    return true;
  };
  take(pool.filter((t) => t.branch));
  while (out.length < n) {
    const used = new Set(out.map((t) => t.verb));
    if (!take(pool.filter((t) => !used.has(t.verb)))) if (!take(pool)) break;
  }
  return out.slice(0, n);
}

/** 각성 외형 (계약 art §26 — 무기 오버레이): 고른 갈래·단계·길 강조색. 0단이면 null */
export function growthLookOf(w: {
  id: string;
  stage: number;
  branchId: string | null;
  pathId: string | null;
}): { branch: string; stage: 1 | 2; path: string | null; tint: number | null; legacy: boolean } | null {
  if (w.stage < 1 || !w.branchId) return null;
  const stage: 1 | 2 = w.stage >= 2 ? 2 : 1;
  return {
    branch: w.branchId,
    stage,
    path: stage === 2 ? w.pathId : null,
    tint: stage === 2 && w.pathId ? pathTint(w.id, w.branchId, w.pathId) : null,
    legacy: Boolean(growthBranch(w.id, w.branchId)?.legacyLook),
  };
}
