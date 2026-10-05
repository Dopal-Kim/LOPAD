/**
 * 61 단계 4 P12 무기 성장 UI 틀 문구 (계약 §18). 임시값 — 도영 님·스토리 검수 대상. 데이터만 둔다(순수 계산 모듈이 import).
 * 텍스트 팩 조회는 `text.ts` 의 `growthText`(팩 `hud.<키>` 우선). 용어는 P12 용어표 하나의 뜻만:
 * 각성 게이지 · 개성 · 개성 발현 · 1차 각성 · 2차 각성 · 단련. 수치·내부 용어는 쓰지 않는다.
 */
export const GROWTH_TEXT = {
  // ---- HUD 각성 게이지
  gaugeLabel: '각성',
  /** 다음 눈금까지 남은 수 — {what} = 눈금 이름, {n} = 남은 수 */
  remain: '{what}까지 {n}',
  remainDone: '모든 눈금',
  markTrait: '개성 발현',
  markAwaken1: '1차 각성',
  markAwaken2: '2차 각성',
  markTemper: '단련',
  // ---- 선택 카드 머리표
  headTrait: '개성 발현',
  headAwaken1: '1차 각성',
  headAwaken2: '2차 각성',
  headTemper: '단련',
  /** 1차 각성 카드 아래 2차 길 미리보기 머리글 */
  pathsHead: '2차 각성 길',
  /** 바뀌는 칸 앞말 — {verb} = 그 칸의 지금 동작 이름 */
  changes: '{verb} 바뀜',
  /** 단련 눈금 */
  temperPips: '단련',
  // ---- 각성 배너 · 개성 알림
  bannerAwaken1: '1차 각성',
  bannerAwaken2: '2차 각성',
  traitGained: '개성 발현',
  // ---- 처음 안내 카드 (그림 + 두 줄)
  guideTraitTitle: '개성 발현',
  guideTrait1: '각성 게이지가 작은 눈금에 닿으면 개성 하나를 고른다.',
  guideTrait2: '개성은 키 하나의 싸우는 방식을 바꾼다 — 카드의 키를 보라.',
  guideAwaken1Title: '1차 각성',
  guideAwaken1_1: '큰 눈금에서 무기가 깨어난다. 갈래 셋 중 하나를 고른다.',
  guideAwaken1_2: '무기 모양과 키 하나가 바뀌고, 아래 두 길이 다음 각성에서 열린다.',
  guideAwaken2Title: '2차 각성',
  guideAwaken2_1: '둘째 큰 눈금. 내 갈래의 두 길 중 하나를 고른다.',
  guideAwaken2_2: '무기에 새 부분과 빛이 돋는다. 그 뒤 눈금은 단련 또는 개성.',
  guideNext: 'Enter · 클릭 — 고르러 간다',
  // ---- Tab 성장도
  treeTitle: '성장도',
  treeBase: '기본',
  treeGauge: '각성 게이지 {n}',
  traitsHead: '얻은 개성',
  traitsNone: '아직 없다',
  traitsMore: '외 {n}',
  // ---- 일기장
  diaryWeapon: '무기: {name}{route}   (각성 게이지 {n})',
} as const;
export type GrowthTextKey = keyof typeof GROWTH_TEXT;
