/**
 * P21 색 보정 (계약 dark-brutal §7 · 아트 A `grade.json` 의미 — parts/art/work/dark21 grade_proposal `_semantics`) — 순수 계산 (단위 테스트).
 * 한 장의 ColorMatrix(4×5, 오프셋 0~1 단위 — `ColorMatrix.set`): 채도 → 대비 → 명도 → shadowTint(오프셋).
 * - saturation: Phaser `saturate(value)` 인자 그대로 (0 그대로 · −1 무채, 색 거리 배율 1 + value — 세 채널 평균 기준)
 * - contrast: out = (in − 0.5)·(1 + contrast) + 0.5 (Phaser `contrast()` 는 오프셋 기준점이 달라 쓰지 않는다)
 * - brightness: 곱 · shadowTint: 더하는 색 (대비로 눌린 검정을 차가운 먹색으로)
 * 비네트: ×(1 − strength·smoothstep(radius, 1, d)), d = 화면 가운데 → 모서리 1 (원형).
 */

export interface GradeParams {
  saturation: number;
  contrast: number;
  brightness: number;
  /** 0xrrggbb */
  shadowTint: number;
}

/** 4×5 행렬 (행 우선, ColorMatrix.set 형식) */
export function gradeMatrix(p: GradeParams): number[] {
  const x = (p.saturation * 2) / 3 + 1;
  const y = (x - 1) * -0.5;
  const v = 1 + p.contrast;
  const b = p.brightness;
  const tint = [(p.shadowTint >> 16) & 0xff, (p.shadowTint >> 8) & 0xff, p.shadowTint & 0xff].map((c) => c / 255);
  const k = v * b;
  const off = 0.5 * (1 - v) * b;
  const out: number[] = [];
  for (let row = 0; row < 3; row++) {
    const r = [y, y, y];
    r[row] = x;
    out.push(r[0] * k, r[1] * k, r[2] * k, 0, off + tint[row]);
  }
  out.push(0, 0, 0, 1, 0);
  return out;
}

/** 행렬을 색(0~1) 에 적용 (테스트·측정용) */
export function applyMatrix(m: readonly number[], rgb: readonly [number, number, number]): [number, number, number] {
  const [r, g, b] = rgb;
  const ch = (i: number) => Math.min(1, Math.max(0, m[i] * r + m[i + 1] * g + m[i + 2] * b + m[i + 4]));
  return [ch(0), ch(5), ch(10)];
}

/** smoothstep(e0, e1, x) */
export function smoothstep(e0: number, e1: number, x: number): number {
  const t = Math.min(1, Math.max(0, (x - e0) / Math.max(1e-6, e1 - e0)));
  return t * t * (3 - 2 * t);
}

/** 비네트 어둠 알파 (0~1 — 검정을 이 알파로 덮으면 ×(1 − 알파)) · d = 가운데 → 모서리 1 */
export function vignetteAlpha(strength: number, radius: number, d: number): number {
  return strength * smoothstep(radius, 1, d);
}

/** 저HP 맥박 0.6 ↔ 1.0 (pulseHz, 시각 ms) */
export function pulseAt(timeMs: number, hz: number): number {
  return 0.8 + 0.2 * Math.sin((timeMs / 1000) * hz * Math.PI * 2);
}
