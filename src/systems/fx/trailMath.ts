/**
 * 화면 섬광 감쇠 수식 (Phaser 없음, 테스트 가능). 42라운드 잔상 리본 구간 스타일(segmentStyle)·베기 호(arcPoint)는
 * 55라운드 칼끝 리본(`ribbonMath`·`bladeTipMath`)으로 대체되어 뺐다.
 */

/** 남은 섬광 알파: alpha0 × (1 - 경과/ms), 0 미만이면 0 (화면 섬광은 합산하지 않고 큰 쪽 — fx-design §6.2) */
export function flashAlphaAt(alpha0: number, ms: number, elapsed: number): number {
  if (ms <= 0) return 0;
  return Math.max(0, alpha0 * (1 - elapsed / ms));
}
