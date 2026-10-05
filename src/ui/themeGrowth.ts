import type { UiTagId } from '../contract/ui';

/**
 * 61 단계 4 P12 무기 성장 UI 수치 (계약 §18). 전부 임시값(도영 님 검토 대상). 위치는 논리 960×540 px, 정수.
 * 색은 팔레트 안에서만 — 기본 강조 램프 슬롯(16~27)·무채 G·세피아 S (61 단계 4 §17.1: 층마다 바꾸지 않는다).
 */

/** HUD 각성 게이지 줄 (전투 묶음 무기·자원 줄 아래) */
export const GROWTH_HUD = {
  /** 줄 높이 (글 상자 16 과 맞춤) */
  rowH: 16,
  /** 막대 두께·세로 자리(줄 위에서) */
  barH: 3,
  barY: 7,
  /** 숫자 → 막대, 막대 → 남은 수 */
  gap: 6,
  /** 막대 폭 (숫자·남은 수와 한 줄에 — 묶음 최소 폭 안) */
  barW: 120,
  /** 눈금 마름모 반지름: 작은 눈금(◇ 개성 발현·단련) · 큰 눈금(◆ 각성) */
  tickR: 3,
  bigTickR: 4,
  /** 막대 바탕 · 찬 부분 · 지난 작은 눈금 · 지난 큰 눈금 · 앞 눈금 테 (작은 G09, 큰 = 강조 20) */
  trackGray: 3,
  fillSlot: 22,
  doneSlot: 22,
  bigDoneSlot: 25,
  todoGray: 9,
  bigTodoSlot: 20,
  /** 다음 눈금 (깜빡이지 않고 한 칸 밝게) */
  nextSlot: 24,
  /** ui:growth-gain 반짝: 막대 위 흰 덮개 알파 → 0, 숫자 강조 시간 */
  flashAlpha: 0.85,
  flashMs: 320,
  numAccentMs: 420,
} as const;

/** 선택 카드 (개성 발현 3 · 1차 각성 3 · 2차 각성 2 · 단련 눈금 [단련/개성/개성]) */
export const GROWTH_CARD = {
  /** 카드 폭: 3장 · 2장 */
  w3: 212,
  w2: 252,
  minH: 208,
  gap: 22,
  pad: 14,
  matPad: 16,
  tabH: 24,
  tabTop: 10,
  stripe: 3,
  /** 무기 모양 그림 칸 높이 (그림은 칸 안에 정수 배율로) */
  lookH: 64,
  /** 개성 카드의 큰 키 그림 배율 */
  keyScale: 2 as const,
  /** 고른 카드 들림·그림자 */
  lift: 6,
  shadow: 3,
  shadowLift: 7,
  shadowAlpha: 0.55,
  focusSlot: 20,
  shakePx: 2,
  shakeMs: 50,
  /** 머리표 띠 색 (강조 슬롯) */
  headSlot: { trait: 22, awaken1: 25, awaken2: 26, temper: 21 } as Readonly<Record<string, number>>,
  /** 바뀌는 키 강조 밑줄 */
  keyLineSlot: 22,
  /** 2차 길 미리보기 줄 앞 마름모 */
  pathDotSlot: 20,
  /** 단련 눈금 마름모 */
  pipR: 3,
  pipGap: 3,
  pipSlot: 22,
} as const;

/** 처음 안내 카드 (그림 + 두 줄) */
export const GROWTH_GUIDE = {
  w: 400,
  pad: 18,
  /** 그림 칸 높이 */
  artH: 72,
  /** 그림 칸의 큰 마름모 반지름 */
  artR: 18,
  lineGap: 4,
  depth: 10,
} as const;

/** 각성 배너 (ui:awaken) · 개성 알림 (ui:trait-gained) */
export const GROWTH_BANNER = {
  awaken: { top: 118, inMs: 200, holdMs: 1900, outMs: 400, drop: 6 },
  /** 배너 그림 최대 높이 */
  lookMaxH: 72,
  bandH: 150,
  trait: { top: 150, inMs: 180, holdMs: 2200, outMs: 360, drop: 4 },
  traitPadX: 10,
  traitPadY: 6,
  depth: 58,
} as const;

/** Tab 성장도 나무 (빌드 보기 왼쪽 장 안) */
export const GROWTH_TREE = {
  /** 열 x (기본 · 갈래 · 길 — 왼쪽 끝에서), 줄 높이(길 한 줄) */
  colX: [0, 44, 156] as readonly number[],
  /** 이음선이 꺾이는 자리 (자식 점 왼쪽으로) */
  elbow: 10,
  rowH: 15,
  dotR: 3,
  /** 지나온 길 선·점 (강조), 지금 고를 수 있는 것 (세피아 S5), 닫힌 것 (세피아 S3) */
  litSlot: 22,
  openSepia: 5,
  shutSepia: 4,
  /** 얻은 개성 목록 줄 높이 · 최대 줄 수 (넘치면 '외 n') */
  traitRowH: 18,
  traitMax: 6,
} as const;

/**
 * 층마다 켜진 태그 (P12 '1층 태그 6': 간파·돌파·급소·연쇄·중량·취기). 카드에서 꺼진 태그는 보이지 않는다.
 * 키 = 스냅샷 `stageIndex`(0 = 1층). 없는 층은 모두 보인다.
 */
export const LIVE_TAGS_BY_STAGE: Readonly<Record<number, readonly UiTagId[]>> = {
  0: ['insight', 'breach', 'vital', 'chain', 'weight', 'drunk'],
};

/** 4동사 칸 → 키 이름 (스냅샷 `weaponVerbs` 에 그 칸이 없을 때) */
export const VERB_KEY_FALLBACK: Readonly<Record<string, string>> = {
  attack: '좌클릭',
  signature: '우클릭',
  dash: 'Space',
  hold: '좌클릭 길게',
};
