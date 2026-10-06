/**
 * 61 단계 5 (P13 §1-4) 공명 — 같은 무기·같은 태그 개성 2장이 모이면 켜지는 엮임 효과 (Phaser 의존 없음).
 * 정의는 `data/traits.json resonance` (무기마다 2~3). 켜진 공명은 합산(`computeBuildMods`)에 규칙으로 들어가고(source 'trait'),
 * 스냅샷 `UiGrowth.resonance`(계약 UI §18.1)·켜짐 알림(`ui:resonance`)·개성 제시(짝 카드 한 장 보장)가 이것을 읽는다.
 */
import { RESONANCES } from '../../data/growth';
import type { ResonanceDef, TraitDef } from '../../data/growthTypes';

/** 공명을 켜는 같은 태그 개성 수 */
export const RESONANCE_NEED = 2;

/** 이 무기의 공명 정의 */
export function resonancesOf(weapon: string): readonly ResonanceDef[] {
  return RESONANCES.filter((r) => r.weapon === weapon);
}

/** 얻은 개성 중 이 태그 장 수 */
function tagCount(traits: readonly TraitDef[], weapon: string, tag: string): number {
  return traits.filter((t) => t.weapon === weapon && t.tag === tag).length;
}

/** 켜진 공명 (같은 태그 개성 RESONANCE_NEED 장 이상) */
export function activeResonances(weapon: string, traits: readonly TraitDef[]): ResonanceDef[] {
  return resonancesOf(weapon).filter((r) => tagCount(traits, weapon, r.tag) >= RESONANCE_NEED);
}

/** 한 장 모자란 공명 태그 (개성 제시가 짝 카드 한 장을 넣는다 — 조합의 맛) */
export function partnerTags(weapon: string, traits: readonly TraitDef[]): string[] {
  return resonancesOf(weapon)
    .filter((r) => tagCount(traits, weapon, r.tag) === RESONANCE_NEED - 1)
    .map((r) => r.tag);
}

/** 이번에 새로 켜진 공명 (전 → 후 개성 목록) */
export function newlyActive(weapon: string, before: readonly TraitDef[], after: readonly TraitDef[]): ResonanceDef[] {
  const was = new Set(activeResonances(weapon, before).map((r) => r.id));
  return activeResonances(weapon, after).filter((r) => !was.has(r.id));
}
