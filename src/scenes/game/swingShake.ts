/**
 * 56라운드 Q5 땅 균열 흔들림 (시트 `shakeHint` — 크기 행 s·m·l 별 {px, ms}, 아트 임시값). Phaser 의존 없음
 */
export type ShakeHint = Record<string, { px?: number; ms?: number } | undefined> | { px?: number; ms?: number };

/** 행의 흔들림 (없으면 null). 행별 표가 아니면 공통 값 */
export function crackShake(hint: ShakeHint | undefined, row: string): { px: number; ms: number } | null {
  if (!hint || typeof hint !== 'object') return null;
  const byRow = (hint as Record<string, { px?: number; ms?: number } | undefined>)[row];
  const h = byRow && typeof byRow === 'object' ? byRow : (hint as { px?: number; ms?: number });
  return typeof h.px === 'number' && typeof h.ms === 'number' && h.px > 0 && h.ms > 0 ? { px: h.px, ms: h.ms } : null;
}
