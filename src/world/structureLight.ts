/**
 * 61라운드 계약 art §24 구조물 상태별 광원 `lightByState` (Phaser 없음): 상태 → 광원.
 * 값이 광원 객체면 그것 · 문자열(예 '켜짐')이면 시트 기본 `light` · null 이거나 표에 없는 상태면 꺼짐.
 * `lightByState` 가 없는 시트는 undefined (기존 규칙 — 한 광원, 부서짐·다 씀이면 끔).
 */
import type { LightSpec } from '../systems/sprites/sheetJson';

export function stateLight(
  def: { light?: LightSpec; lightByState?: Record<string, LightSpec | string | null> } | null | undefined,
  state: string,
): LightSpec | null | undefined {
  const table = def?.lightByState;
  if (!table || typeof table !== 'object') return undefined;
  const v = table[state];
  if (v && typeof v === 'object') return v.radius > 0 ? v : null;
  if (typeof v === 'string') return def?.light && def.light.radius > 0 ? def.light : null;
  return null;
}
