/** 여러 시스템이 함께 쓰는 작은 수학 도우미 (57라운드 B4: 중복 통합). Phaser 의존 없음. */

/** 0..1 로 자른다 */
export function clamp01(v: number): number {
  return Math.max(0, Math.min(1, v));
}
