/**
 * 56라운드 2단계 단검 고속 난타 순수 규칙 (Phaser 의존 없음): 찌르기 열 세기 · 과열 단계 fx.
 */

/**
 * 루프 열 순서(loop)에서 지난 열(prev) 다음부터 지금 열(cur)까지 앞으로 돌며 지나간 찌르기 열(stabs) 수. prev 가 루프 밖이면
 * 루프 첫 열부터 센다. cur 가 루프 밖이면 0
 */
export function stabsCrossed(loop: readonly number[], stabs: readonly number[], prev: number, cur: number): number {
  const ci = loop.indexOf(cur);
  if (ci < 0) return 0;
  const pi = loop.indexOf(prev);
  let n = 0;
  let i = pi < 0 ? -1 : pi;
  do {
    i = (i + 1) % loop.length;
    if (stabs.includes(loop[i])) n++;
  } while (i !== ci);
  return n;
}

/** 과열 비율 → fx 단계 (경계 수만큼, 0 = 기본 시트) */
export function heatLevelOf(ratio: number, bounds: readonly number[]): number {
  let lv = 0;
  for (const b of bounds) if (ratio >= b) lv++;
  return lv;
}
