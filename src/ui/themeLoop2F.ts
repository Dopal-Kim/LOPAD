/**
 * 62 루프 2 UI F 수치 (시스템 D 계약 2차 패스). 전부 논리 px(960×540) · ms. 임시값 — 62 전권 위임, 프로듀서 검토 대상.
 */

/** 아이콘 시트 (`assets/ui/kit/event_icons.png` — parts/ui/tools/event_icons.py, 키트 icons.png 결 16×16) */
export const EVENT_ICON_SHEET = {
  key: 'ui-kit-event_icons',
  url: 'assets-game/ui/kit/event_icons.png',
  size: 16,
  order: ['maxHp', 'growth', 'passive', 'curse', 'discount', 'enemies', 'diary', 'unknown'] as readonly string[],
} as const;

/** 사연·상인 메뉴 (일기장 한 쪽) */
export const EVENT_PAGE = {
  minW: 520,
  maxW: 640,
  pad: 24,
  /** 말하는 이 초상 칸 (NPC 시트 0프레임을 1배 — 키트 도트 밀도, 상반신만 보이고 발은 잘린다) · 칸 안 여백 · 글과 사이 */
  portraitW: 72,
  portraitH: 84,
  portraitScale: 1,
  portraitPad: 5,
  portraitGap: 12,
  /** 설명 문단 사이 */
  paraGap: 4,
  /** 선택지 표: 이름 칸 최소 폭 · 아이콘 칸 폭 · 칸 사이 · 줄 위아래 여백 · 아이콘 한 줄 높이 */
  labelColMin: 150,
  iconCol: 180,
  colGap: 12,
  rowPadY: 4,
  iconLineH: 18,
  /** 고름 자리 띠 알파 (S4) */
  selAlpha: 0.35,
  /** 머리말 줄 (하나를 고른다 · 내준다 · 얻는다) 아래 틈 */
  headGap: 4,
} as const;

/** 결과 컷 패널 (ui:event-result) — 화면 가운데 위쪽 */
export const EVENT_CUT = {
  /** 컷 그림 (아트 §31-7 320×180 — UI 1배) */
  w: 320,
  h: 180,
  pad: 10,
  /** 패널 가운데 y (화면 높이 비율) */
  centerY: 0.42,
  inMs: 260,
  /** 머무는 시간 (그 뒤 사라짐) · 사라짐 · 다음 메뉴가 기다리는 최대 (uiSequence) */
  holdMs: 3200,
  outMs: 320,
  menuWaitMaxMs: 1400,
  /** 아래로 내려오며 나타나는 px */
  drop: 6,
  depth: 58,
} as const;

/** 장터 노점 카드 (월드 위치 — 물건 윗변 가운데 위) */
export const SHOP_CARD = {
  w: 168,
  pad: 8,
  /** 물건 그림 칸 높이 (items/v3 80×96 시트 → 0.5 = 40×48). 유품 그림은 128 → 0.5 = 64 (도트 1:1) */
  artH: 48,
  artW: 44,
  /** 물건 위로 띄우는 틈 · 꼬리 높이 */
  gap: 6,
  tail: 5,
  margin: 6,
  depth: 44,
  inMs: 120,
} as const;

/** 산 물건이 주인공 쪽으로 빨려 드는 반짝임 */
export const SHOP_BUY_FX = {
  sparks: 7,
  /** 물건 윗변(offer.screen) 에서 물건 몸 가운데까지 — 월드 px (화면 px = × 카메라 논리 배율, P19 줌 1.75·1.6) */
  itemDyWorld: 7,
  flyMs: 420,
  stagger: 30,
  /** 주인공 몸 가운데 (스냅샷에 주인공 화면 좌표가 없어 카메라가 따라가는 화면 가운데 — 시스템 요청) */
  heroDy: -6,
  /** 전표 '−30' 이 떠오르는 거리 · 시간 */
  goldRise: 14,
  goldMs: 900,
  depth: 60,
} as const;

/** 수련장·시험장 허수아비 나무 팻말 */
export const WORLD_SIGN = {
  pad: 5,
  /** 말뚝 (팻말 아래 → 머리 위 끝) */
  post: 6,
  postW: 2,
  minW: 56,
  depth: 30,
} as const;

/** 무리 들어오는 쪽 화살표 (화면 가장자리) */
export const WAVE_ARROW = {
  /** 가장자리에서 안쪽으로 */
  inset: 14,
  /** 위쪽 화살표 y (알림 줄 위 끝 40 보다 위 — 겹치지 않게) */
  topY: 24,
  /** 아래쪽 화살표는 전투 묶음·자막 위를 피해 화면 아래 끝 근처 */
  bottomInset: 10,
  size: 7,
  holdMs: 1700,
  blinkMs: 180,
  outMs: 260,
  depth: 50,
} as const;
