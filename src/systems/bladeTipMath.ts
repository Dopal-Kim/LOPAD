/**
 * 55라운드 Q7 칼끝 궤적 (계약 §16 리본 · 무기 v3 `bladeTipAnchors`). Phaser 의존 없음.
 * 몸 연격 시트의 실제 재생 프레임 시작(`starts`, 구간별 맞춤 반영) 위에서 시각 t 의 열·비율을 찾고, 열마다 그린 칼끝을
 * 판정 원점 둘레 극좌표로 보간한다(빠른 휘두름이 프레임 사이에서 직선으로 줄지 않게). 칼끝 메모가 없으면 판정 호 위를 훑는다.
 */

export interface Vec {
  x: number;
  y: number;
}

/** 열별 칼끝(발 피벗 기준 월드 오프셋, 없으면 null) + 실제 재생 프레임 시작 ms + 전체 길이 + 보간 중심(판정 원점 오프셋) */
export interface TipTrack {
  starts: readonly number[];
  total: number;
  tips: readonly (Vec | null)[];
  center: Vec;
}

/** 시각 t 의 열과 그 열 안 비율 (0..1). t 가 범위 밖이면 끝 열 */
export function columnAt(starts: readonly number[], total: number, t: number): { col: number; frac: number } {
  const n = starts.length;
  if (n === 0) return { col: 0, frac: 0 };
  let col = 0;
  while (col + 1 < n && t >= starts[col + 1]) col++;
  const end = col + 1 < n ? starts[col + 1] : total;
  const span = end - starts[col];
  const frac = span > 0 ? Math.max(0, Math.min(1, (t - starts[col]) / span)) : 0;
  return { col, frac };
}

/** a → b 각도 차를 (−π, π] 로 */
function wrap(d: number): number {
  let a = d;
  while (a > Math.PI) a -= Math.PI * 2;
  while (a <= -Math.PI) a += Math.PI * 2;
  return a;
}

/** 두 점을 중심 둘레 극좌표로 보간 (반지름·각도 선형) */
export function polarLerp(c: Vec, p0: Vec, p1: Vec, f: number): Vec {
  const a0 = Math.atan2(p0.y - c.y, p0.x - c.x);
  const a1 = Math.atan2(p1.y - c.y, p1.x - c.x);
  const r0 = Math.hypot(p0.x - c.x, p0.y - c.y);
  const r1 = Math.hypot(p1.x - c.x, p1.y - c.y);
  const a = a0 + wrap(a1 - a0) * f;
  const r = r0 + (r1 - r0) * f;
  return { x: c.x + Math.cos(a) * r, y: c.y + Math.sin(a) * r };
}

/** 시각 t 의 칼끝 오프셋 (다음 열 칼끝이 없으면 이 열 그대로). 이 열에 칼끝이 없으면 null */
export function tipAt(track: TipTrack, t: number): Vec | null {
  const { col, frac } = columnAt(track.starts, track.total, t);
  const p0 = track.tips[col] ?? null;
  if (!p0) return null;
  const p1 = track.tips[col + 1] ?? null;
  if (!p1 || col + 1 >= track.starts.length) return p0;
  return polarLerp(track.center, p0, p1, frac);
}

/**
 * 칼끝을 찍는 구간 [from, to] ms: 판정 첫 프레임 `lead` 프레임 전 시작 ~ 판정 마지막 프레임 `tail` 프레임 뒤 끝.
 * 판정 프레임 메모가 없으면 null
 */
export function swingWindow(
  starts: readonly number[],
  total: number,
  activeFrames: readonly number[] | undefined,
  lead: number,
  tail: number,
): { from: number; to: number } | null {
  if (!activeFrames || activeFrames.length === 0 || starts.length === 0) return null;
  const first = Math.max(0, Math.min(...activeFrames) - lead);
  const lastCol = Math.min(starts.length - 1, Math.max(...activeFrames) + tail);
  const to = lastCol + 1 < starts.length ? starts[lastCol + 1] : total;
  return { from: starts[first] ?? 0, to };
}

/** 칼끝 메모가 없을 때: 중심 둘레 반지름 r 의 호를 from → to 각도(rad)로 구간 비율 u(0..1)만큼 */
export function arcTipAt(c: Vec, r: number, fromRad: number, toRad: number, u: number): Vec {
  const k = Math.max(0, Math.min(1, u));
  const a = fromRad + (toRad - fromRad) * k;
  return { x: c.x + Math.cos(a) * r, y: c.y + Math.sin(a) * r };
}
