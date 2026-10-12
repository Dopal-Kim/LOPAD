/**
 * 62 루프 2 시스템 C (P16 §3 · P1-7) 사망 먹 번짐 화면 효과 그리기 값 (시간·배율은 data/runEnd.json death).
 * 논리 화면 960×540 위 먹 방울: 주인공 자리 큰 방울 1 + 가장자리 방울 EDGE_SEEDS → 시간에 따라 반지름이 자라고 잎(LOBES)이 번진다.
 */
export const INK_SMEAR = {
  /** 먹 · 번진 테두리 (G00 · G01 결 — 세피아 기운 검정) */
  COLOR: 0x0b0907,
  EDGE_COLOR: 0x1c1510,
  /** 깊이: 화면 효과(DEPTH.SCREEN_FX) 바로 위 */
  DEPTH_ABOVE_SCREEN_FX: 1,
  /** 주인공 방울 최종 반지름 (논리 px) · 가장자리 방울 반지름 범위 */
  CENTER_R: 260,
  EDGE_R_MIN: 120,
  EDGE_R_MAX: 230,
  EDGE_SEEDS: 9,
  /** 방울마다 잎(작은 원) 수 · 잎 거리(반지름 비) · 잎 크기(반지름 비) */
  LOBES: 7,
  LOBE_DIST: 0.72,
  LOBE_R: 0.42,
  /** 번진 테두리 두께(반지름 비) — 테두리·속 모두 불투명(겹쳐도 고리 무늬 없음) */
  EDGE_SPREAD: 1.18,
  /** 가장자리 방울은 이만큼 늦게 시작 (0..1 진행 비) */
  EDGE_DELAY: 0.18,
} as const;
