/** 잔상 궤적 구간 스타일·화면 섬광 감쇠 수식 (Phaser 없음, 테스트 가능). 색 = 코어 → 강조 → 보조 → 투명, 두께 from → to (정수) */

export interface TrailPalette {
  /** 백열 코어 (G15) */
  core: number;
  /** 층 강조색 (하이라이트) */
  accent: number;
  /** 무기 보조색 (몸통). 없으면 강조색과 같다 */
  body: number;
}

export interface SegmentStyle {
  width: number;
  color: number;
  alpha: number;
  /** 최신 구간에 겹치는 1px 코어 선 (0 이면 없음) */
  coreWidth: number;
  coreAlpha: number;
}

function lerpColor(a: number, b: number, t: number): number {
  const ar = (a >> 16) & 0xff;
  const ag = (a >> 8) & 0xff;
  const ab = a & 0xff;
  const br = (b >> 16) & 0xff;
  const bg = (b >> 8) & 0xff;
  const bb = b & 0xff;
  const r = Math.round(ar + (br - ar) * t);
  const g = Math.round(ag + (bg - ag) * t);
  const bl = Math.round(ab + (bb - ab) * t);
  return (r << 16) | (g << 8) | bl;
}

/**
 * `recency` 1 = 가장 새 구간, 0 = 가장 오래된 구간. `age` 0..1 = 샘플 나이 ÷ 수명.
 * 두께는 recency 로 from → to 보간 후 정수 반올림(최소 1). 색은 recency ≥ 0.66 코어→강조, 0.33~0.66 강조→보조, < 0.33 보조.
 * 알파 = (1 - age) × recency 쪽 가중(오래된 끝은 투명으로 빠진다). 최신 1/3 구간에는 1px 코어 선을 덧그린다.
 */
export function segmentStyle(
  recency: number,
  age: number,
  p: TrailPalette,
  widthFrom: number,
  widthTo: number,
): SegmentStyle {
  const r = Math.max(0, Math.min(1, recency));
  const a = Math.max(0, Math.min(1, age));
  const width = Math.max(1, Math.round(widthTo + (widthFrom - widthTo) * r));
  let color: number;
  if (r >= 2 / 3) color = lerpColor(p.accent, p.core, (r - 2 / 3) * 3);
  else if (r >= 1 / 3) color = lerpColor(p.body, p.accent, (r - 1 / 3) * 3);
  else color = p.body;
  const alpha = +((1 - a) * (0.35 + 0.65 * r)).toFixed(3);
  const coreOn = r >= 2 / 3 && width >= 2;
  return {
    width,
    color,
    alpha,
    coreWidth: coreOn ? 1 : 0,
    coreAlpha: coreOn ? alpha : 0,
  };
}

/** 베기 호 위의 점: 중심(cx, cy)·반지름·중심각 angle 에서 반각 half 를 t(0..1)로 훑는다 */
export function arcPoint(
  cx: number,
  cy: number,
  radius: number,
  angle: number,
  half: number,
  t: number,
): { x: number; y: number } {
  const a = angle - half + 2 * half * Math.max(0, Math.min(1, t));
  return { x: cx + Math.cos(a) * radius, y: cy + Math.sin(a) * radius };
}

/** 남은 섬광 알파: alpha0 × (1 - 경과/ms), 0 미만이면 0 (화면 섬광은 합산하지 않고 큰 쪽 — fx-design §6.2) */
export function flashAlphaAt(alpha0: number, ms: number, elapsed: number): number {
  if (ms <= 0) return 0;
  return Math.max(0, alpha0 * (1 - elapsed / ms));
}
