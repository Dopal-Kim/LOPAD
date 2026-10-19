/**
 * P19 1-U 자유 전투 UI (카메라·가독성) 수치. 전부 논리 px(960×540) · ms. 임시값 — 프로듀서 검토 대상.
 * 근거: decisions/2026-10-14-P19-free-combat.md ④G · contracts/free-combat.md §2·§4.
 */

/** 예고 색 언어 (계약 free-combat §2 — 시스템·아트와 같은 색. UI 는 이 넷만 새 색으로 쓴다) */
export const TELL = {
  /** 경고: 막기·회피 가능한 근접·돌진 준비 */
  warn: '#ffb347',
  /** 위험: 막을 수 없음 (잡기·광역·폭발) */
  danger: '#ff4a3a',
  /** 원거리: 조준·투척 */
  ranged: '#9fd8ff',
  /** 기회: 버팀이 깨짐·띄워짐 (추가타) */
  chance: '#ffe08a',
} as const;

/** 화면 밖 적 표식 (가장자리 화살촉) */
export const OFFSCREEN = {
  /** 화면 가장자리에서 안쪽으로 (화살촉 끝 자리) */
  inset: 10,
  /** 위 끝은 층 제목 줄 아래 · 아래 끝은 키 막대 위 */
  top: 30,
  bottom: 14,
  /** 화살촉 길이: 가까우면 크게 (distTiles ≤ nearTiles → max, ≥ farTiles → min) */
  sizeMin: 5,
  sizeMax: 9,
  nearTiles: 3,
  farTiles: 14,
  /** 멀면 흐리게 (알파 1 → farAlpha) */
  farAlpha: 0.55,
  /** 위협 없음(이동 중) 색 = 무채 G11 */
  idleGray: 11,
  depth: 8,
} as const;

/** 반응 팝 (벽꽝·볼링·낙하·연쇄 폭발) — 월드 위 짧은 그림 문자 + 큰 숫자 */
export const POP = {
  /** 동시에 떠 있는 팝 상한 (넘으면 가장 오래된 것부터 지운다 — 과하지 않게) */
  max: 4,
  /** 나타남 · 머묾 · 사라짐 (P21: 덜 튀게 — 들어옴 60 → 120, 뜸 10 → 4, 문자 12 → 10) */
  inMs: 120,
  holdMs: 420,
  outMs: 260,
  /** 머무는 동안 위로 뜨는 px */
  rise: 4,
  /** 맞은 자리 위로 */
  lift: 16,
  /** 그림 문자 한 변 · 숫자와 사이 */
  glyph: 10,
  gap: 3,
  depth: 5,
} as const;

/** 연속 처치 (COMBO_STREAK) — 오른쪽 가장자리에 작게, 보상 없음 */
export const COMBO = {
  /** 이 수부터 보인다 */
  min: 2,
  /** 오른쪽 끝에서 · 화면 높이 비율 (미니맵·과제 목록 아래, 공지 위) */
  right: 16,
  yRatio: 0.42,
  /** 마지막 처치 뒤 머묾 (windowMs 가 오면 그 값) · 사라짐 */
  holdMs: 1500,
  outMs: 260,
  /** 새 처치마다 숫자 튀어오름 px (P21: 3 → 1) */
  bump: 1,
  depth: 8,
} as const;

/** 처음 보는 적 소개 — 왼쪽 위 작은 카드 (옛 위 가운데 띠) */
export const INTRO_CORNER = {
  gap: 6,
  padX: 6,
  padY: 4,
  inMs: 160,
  holdMs: 3200,
  outMs: 300,
  /** 이어서 오면 한 장에 쌓는 상한 */
  queueMax: 3,
  depth: 50,
} as const;

/** 전투 묶음(왼쪽 아래) 전투 중 반투명 */
export const COMBAT_DIM = {
  /** 전투 중 알파 (체력 낮음이면 1) */
  alpha: 0.62,
  fadeMs: 300,
} as const;

/** 카메라 줌 기본값 (snapshot.camera 가 아직 없을 때 — 옛 논리 배율 2) */
export const CAMERA_FALLBACK_ZOOM = 2;
