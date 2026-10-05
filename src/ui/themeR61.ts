/**
 * 61라운드 P10 UI 수치 (설정 화면 · 전투 HUD 다이어트 · 키캡 안내 · Tab 빌드 보기). 전부 임시값(도영 님 검토 대상).
 * 색은 팔레트 안에서만 — 층 강조 램프 슬롯(16~27)·무채 G·세피아 S. 위치는 논리 960×540 px, 정수.
 */

/** 설정 화면 (일기장 한 쪽) */
export const SETTINGS_UI = {
  pageW: 400,
  pad: 24,
  /** 제목 위 여백 */
  top: 14,
  /** 막대·켜고 끄기 줄 높이, 되돌리기·덮기 줄 높이 */
  rowH: 22,
  actionRowH: 18,
  /** 묶음 머리글(화면·소리) 높이 */
  headH: 16,
  /** 조작 칸 시작 x (쪽 안쪽 왼쪽에서) */
  ctrlX: 132,
  /** 막대 칸: 폭·높이·간격 (10칸) */
  cellW: 10,
  cellH: 8,
  cellGap: 2,
  /** 막대 양옆 화살표 (5×7 삼각형) 와 칸 사이 */
  arrowW: 4,
  arrowH: 7,
  arrowGap: 5,
  /** 마지막 화살표 → '70%' */
  pctGap: 6,
  /** '켬' → '끔' 간격 */
  toggleGap: 18,
  /** 고른 쪽 밑줄 두께·글 아래 거리 */
  underlineH: 2,
  /** 켜진 칸·화살표·밑줄: 고른 줄은 층 강조 22, 아닌 줄은 세피아 S5·S4 */
  litSlot: 22,
  /** 일시정지·타이틀 위 깊이 (일기장 위, '싸우는 법' 패널과 같은 층) */
  depth: 60,
} as const;

/**
 * 전투 HUD 다이어트 — 왼쪽 아래 전투 묶음 (데드셀·세피리아처럼 한쪽 구석에 체력·자원·소모품을 모은다).
 * 1행 체력(굵은 막대 + 수치) · 2행 무기 아이콘 + 고유 자원 하나(눈금 2배) · (자원이 둘이면 3행 작게) · 아래 행 독주·소모품·전표.
 * 맨 아래 2px 개성 진행선(글 없음 — 수치는 Tab·일기장).
 */
export const COMBAT_HUD = {
  /** 왼쪽·아래 여백 */
  left: 16,
  bottom: 12,
  padX: 8,
  padY: 7,
  /** 최소 폭 (체력 줄이 들어가는 폭) */
  minW: 292,
  rowGap: 6,
  /** 행 높이 (글 상자 16 · 아이콘 16) */
  rowH: 16,
  /** 2배 눈금 행 높이 */
  bigRowH: 18,
  /** 체력 막대 (보스 틀 14px — 기존 10px 보다 굵게) */
  hpW: 200,
  /** 체력 비율 이하면 수치를 강조색 + 깜빡임 */
  hpLowRatio: 0.3,
  hpBlinkMs: 300,
  /** 아이콘 → 글·막대 */
  iconGap: 4,
  /** 고유 자원 눈금 배율 (도트 그대로 정수 확대) */
  gaugeScale: 2,
  /** 아래 행: 묶음 사이 간격 */
  slotGap: 14,
  /** 개성 진행선: 두께·묶음 아래 끝에서 */
  personalityH: 2,
  personalityInset: 5,
  personalityOn: { gray: 9 },
  personalityFull: { slot: 22 },
  personalityOff: { gray: 3 },
  /** 보스 막대 (아래 가운데) 폭·묶음과 띄울 최소 간격 */
  bossW: 320,
  bossGap: 12,
} as const;

/** 빌드 띠 (좌상단 — 저주·태그 칩을 한 줄로 접는다) */
export const BUILD_STRIP = {
  h: 22,
  padX: 6,
  /** 칸 사이 */
  gap: 8,
  /** 태그 글리프 한 변 */
  glyph: 14,
  /** 글리프 → 점수 */
  scoreGap: 3,
} as const;

/** 키캡 안내 */
export const KEY_GUIDE = {
  /** 한 동작의 키 그림 사이 */
  keyGap: 2,
  /** 키 그림 → 동작 이름 */
  labelGap: 5,
  /** 가로 배치에서 동작 사이 */
  itemGap: 12,
  /** 세로 배치 줄 높이 */
  rowH: 20,
  /** 마우스 눌린 단추·홀드 막대 색 (층 강조) */
  litSlot: 22,
} as const;

/** Tab 빌드 보기 (누르고 있는 동안 — 게임은 멈추지 않는다). 종이 두 장: 왼쪽 무기·조작, 오른쪽 빌드 */
export const PEEK = {
  x: 16,
  y: 34,
  leftW: 236,
  rightW: 300,
  /** 두 장 사이 */
  gap: 6,
  pad: 16,
  top: 12,
  /** 전투 묶음 위로 띄울 여백 */
  bottomGap: 10,
  depth: 70,
} as const;
