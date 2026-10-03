/** 54라운드 Q7 세상이 돈다 기울기 곡선 (Phaser 의존 없음) */
export interface TiltParams {
  durationMs: number;
  tiltDeg: number;
  periodMs: number;
  rampMs: number;
  blur?: number;
}

/** 시각 t(시작부터 ms)의 기울기 (도). 시작·끝 rampMs 동안 0 에서 부드럽게 */
export function tiltAt(t: number, p: TiltParams): number {
  if (t < 0 || t >= p.durationMs) return 0;
  const ramp = Math.max(1, p.rampMs);
  const env = Math.min(1, t / ramp, (p.durationMs - t) / ramp);
  const smooth = env * env * (3 - 2 * env);
  return p.tiltDeg * Math.sin((2 * Math.PI * t) / Math.max(1, p.periodMs)) * smooth;
}
