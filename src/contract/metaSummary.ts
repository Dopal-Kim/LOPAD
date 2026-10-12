/**
 * 시스템 파트: 62 계약 `UiSnapshot.meta` 메타 요약 (타이틀 UI 요청 — 타이틀·일기장 귀퉁이). UI 파트는 import 금지.
 * 메타 세이브(localStorage)를 매 프레임 읽지 않도록 짧게 기억한다 (게임 스냅샷은 매 프레임 만든다).
 */
import type { UiMetaSummary } from './ui';
import { metaStore } from '../systems/meta';

const CACHE_MS = 1000;
let cached: { at: number; value: UiMetaSummary } | null = null;

/** lives = 끝난 생 수(메타 runs — 첫 생이면 0) · souls · bestFloor */
export function metaSummary(now: number = Date.now()): UiMetaSummary {
  if (cached && now - cached.at < CACHE_MS) return { ...cached.value };
  const m = metaStore.read();
  const value = { lives: m.runs, souls: m.souls, bestFloor: m.bestFloor };
  cached = { at: now, value };
  return { ...value };
}

/** 메타가 바뀐 직후 (강화 구매·런 끝) — 다음 읽기에서 새로 */
export function invalidateMetaSummary(): void {
  cached = null;
}
