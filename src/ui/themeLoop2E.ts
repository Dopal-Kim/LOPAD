/**
 * 62 루프 2 UI E 수치 (시스템 C 계약 2차 패스 — 결산 일기장 · 기억 장 · 출구 화살표 · 사망 연출). 전부 논리 px(960×540) · ms.
 */

/** 결산 일기장 (ResultScene) — 두 쪽 펼침 */
export const RESULT_UI = {
  pageW: 372,
  pageH: 468,
  pad: 20,
  /** 처치자 초상 (아트 96×96 — UI 1배, 키트 도트와 같은 밀도) · 테 */
  portrait: 96,
  portraitFrame: 2,
  /** 빌드 아이콘 줄: 칸 · 그림(128 → 32 · 64 → 32) · 사이 · 최대 줄 수 */
  buildCell: 36,
  buildIcon: 32,
  buildGap: 4,
  buildRows: 2,
  /** 지나온 곳 미니맵 높이 · 점 반지름 · 지난 길 두께 · 망령 표식 (아트 §31-9 40×56, 160ms × 6) */
  mapH: 150,
  nodeR: 4,
  pathLine: 2,
  ghost: {
    key: 'ui:map_marker_ghost',
    url: 'assets-game/sprites/ui/map_marker_ghost.png',
    w: 40,
    h: 56,
    frames: 6,
    ms: 160,
    pivotX: 20,
    pivotY: 53,
  },
  /** 층 끝: 맺음 문장 적기 (문장당 ms · 문장 사이 · 시작 지연) · 빈 장 괘선 간격 · 버튼이 나타나는 지연 */
  closingLineMs: 700,
  closingGapMs: 450,
  closingDelayMs: 900,
  blankRuleGap: 22,
  buttonsDelayMs: 400,
  /** 이름 번짐 (61 P7) */
  smudgeDelayMs: 900,
  smudgeInMs: 700,
  smudgeAlpha: 0.55,
} as const;

/** 일기장 '기억' 장 (MemoryBook) — 두 쪽 펼침 */
export const MEMORY_UI = {
  pageW: 368,
  pageH: 468,
  pad: 20,
  /** 오른쪽 장 칸 · 그림 (64 소품 → 32, 128 개성 → 32) · 칸 사이 · 줄 머리 높이 · 줄 사이 */
  cell: 44,
  icon: 32,
  cellGap: 8,
  headH: 16,
  rowGap: 12,
  /** 왼쪽 장 고름 자리 그림 (64) */
  focusIcon: 64,
  /** 뒤 어둠 알파 (타이틀·결과 위에 펼칠 때) */
  backdrop: 0.72,
  /** 떠올리기 연출: 먹 고리 반지름 · 시간 · 칸 튀어 오름 · 알림 머무름 · 다시 그린 뒤 이어 보일 시간 */
  ringR: 34,
  ringMs: 520,
  popScale: 1.18,
  popMs: 180,
  noticeMs: 2600,
  recallWindowMs: 1500,
  /** 강조 슬롯 (고름 자리 · 떠올림 · 지님 · 떠올릴 수 있음) */
  focusSlot: 20,
  recalledSlot: 22,
  equippedSlot: 25,
  readySlot: 23,
} as const;

/** 출구 방향 화살표 (계약 C `UiSnapshot.exitHint`) */
export const EXIT_ARROW = {
  /** 화면 가장자리 여백 (위는 알림 줄, 아래는 전투 묶음 위로) */
  margin: 30,
  marginBottom: 64,
  /** 화살 크기 (길이 · 폭) · 출렁임 (px · ms) */
  len: 18,
  width: 16,
  bob: 3,
  bobMs: 520,
  /** 글과 화살 사이 */
  labelGap: 6,
  /** 보였다 숨는 시간 */
  fadeMs: 180,
  slot: 22,
  depth: 6,
} as const;

/** 사망 연출 (계약 C `UiDeathFx`) — HUD 를 걷는 시간 상한 */
export const DEATH_VEIL = {
  fadeMs: 260,
} as const;
