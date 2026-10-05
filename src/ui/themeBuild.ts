/**
 * 57·60라운드 계약 §14 UI 수치 (전부 임시값, 도영 님 검토 대상). 색은 팔레트 안에서만 — 층 강조 램프 슬롯(16~27)·
 * 무채 G·세피아 S. 위치는 논리 960×540 px, 정수.
 */

/** §14.5 노드 지도 표지 (아이콘 가운데 기준 오프셋) */
export const MARKS = {
  /** 작은 표 한 변 (글자 11 + 링) */
  badge: 14,
  /** 보상 미리보기: 아이콘 오른쪽 아래 */
  rewardDx: 6,
  rewardDy: 4,
  /** 위험 표: 아이콘 왼쪽 위 */
  riskDx: -20,
  riskDy: -20,
  /** 위험 테두리: 노드 고리 바깥 간격·층 강조 슬롯 */
  riskRingGap: 5,
  riskSlot: 21,
  /** 성과 도장: 아이콘 오른쪽 위 */
  gradeDx: 6,
  gradeDy: -22,
  /** 숨은 노드 위치 표시 고리 반지름 */
  locatedR: 14,
  /**
   * 숨은 노드 얼룩 데칼 (키트 `stains`): 손때 번짐 `stain_smudge` 는 어두운 지도 그림 위에서 거의 안 보여(60라운드 캡처)
   * 발광 잉크 얼룩 `stain_blot` 을 쓴다
   */
  smudgeStain: 'stain_blot' as 'stain_ring' | 'stain_burn' | 'stain_blot' | 'stain_smudge',
} as const;

/** §14.1·§14.3 HUD 빌드 칩 (좌상단, 구조물 상태 칩 아래) */
export const BUILD_HUD = {
  /** 태그 칩 최대 개수 (점수 높은 순) */
  maxTags: 4,
  /** 칩 높이·간격 (STRUCT.chipH 24 와 같은 문체) */
  chipH: 24,
  chipGap: 2,
  /** 칩 위 여백 (상태 칩 아래) */
  topGap: 4,
  /** 태그 글리프 상자 한 변 */
  glyph: 14,
  /** 세트 단계 마름모 반지름·간격 */
  pipR: 3,
  pipGap: 2,
  /** 저주 띠 색 (층 강조 슬롯 — 손실 톤과 같음) */
  curseSlot: 19,
  /** 완벽 성공 깜빡임 (간파 칩) ms */
  flashMs: 420,
} as const;

/** §14.11 완벽 성공 HUD 문구 */
export const PERFECT = {
  /**
   * HUD 문구를 띄우는 종류. 패링·퍼펙트 가드는 시스템이 월드 문구('PARRY'·'PERFECT GUARD', §13)를 그리므로 기본은 빼고
   * 완벽 놓기·완벽 회피만 (계약 §14.11 '월드 문구는 시스템 제안' — 확정 전 임시)
   */
  hudKinds: ['perfectRelease', 'perfectEvade'] as readonly string[],
  /** 하단 묶음 위 거리·떠오름 px·머묾·사라짐 ms */
  aboveBundle: 30,
  rise: 8,
  holdMs: 520,
  fadeMs: 260,
} as const;

/** §14.10 성과 진행 칩·도장 카드 */
export const TRIAL = {
  /** 상단 가운데 y (도전 판이 떠 있으면 그 아래) */
  top: 34,
  belowChallenge: 52,
  barH: 2,
  /** 남은 시간 비율이 이 아래면 강조색 */
  lowRatio: 0.25,
} as const;

export const GRADE_CARD = {
  /** 카드 위 y·폭 하한 */
  top: 92,
  minW: 220,
  /** 도장 글자 배율 (정수만) */
  stampScale: 2 as const,
  /** 나타남·머묾·사라짐 ms, 찍힐 때 위에서 내려오는 px */
  inMs: 160,
  holdMs: 2400,
  fadeMs: 300,
  drop: 6,
  depth: 60,
} as const;

/** §14.8 소모품 칸 (하단 묶음 1행, 독주 Q 오른쪽) */
export const CONSUMABLE = {
  /** 독주 키 글자와의 간격 */
  gap: 12,
  /** 병 그림 칸 (8×12, 칸 1px) */
  iconW: 8,
  iconH: 12,
  /** 칸이 비었을 때 알파 */
  emptyAlpha: 0.55,
} as const;

/**
 * §14.9 엘리트 이름표 (아트 `elite_nameplate` 60 Q36 판: 192×40 도트, pivot (96,38), 가로 nineSlice 26/26, 글자 칸
 * `textArea` 26,7 140×24 · textCenterY 19, 권장 글자 #eecc78 = 1층 램프 슬롯 25). 글자 위치·이름표 폭·아래 끝은 JSON
 * (`textArea`·`textCenterY`·`pivot`)을 읽는다 — 바탕이 또 바뀌어도 사본 교체만으로 맞는다. `scale` 0.5 = 아트 도트 밀도 그대로(화면 96×20, 글자 칸 12px = Galmuri11 1배) — 문장 위 2단 배치(60 Q12).
 */
export const ELITE_PLATE = {
  scale: 0.5,
  /**
   * 머리 위 화면 좌표(`screen` = 머리 꼭대기, 계약 §14.9 · 60 Q39 확정)에서 이름표 아래 끝까지 (논리 px)
   * = 문장 pivot(머리 +10도트) 위 64도트 ≈ 37
   */
  aboveHead: 37,
  /** 글자 좌우 여백 (도트) — 가운데 칸이 이만큼 넓어진다 */
  textPadDots: 6,
  /** 체력 선 (이름표 아래 1px 띄워 2px) */
  hpH: 2,
  hpGap: 1,
  hpSlot: 23,
  /** 화면 가장자리 여백 */
  margin: 4,
  depth: 30,
  /** 글자 층 강조 슬롯 (권장 #eecc78) */
  textSlot: 25,
} as const;

/**
 * 60 Q38 개성·보상·패시브 3지선다 카드 3장 (MenuChoiceCards). 일기장 한 페이지 위 잉크 탁자 깔개 + 종이 카드 3장.
 * 카드 = 키트 panel_paper 9-slice + paper_tile, 머리표 = panel_ink 작은 탭 + 종류 띠. 색은 층 강조 램프 슬롯·세피아만.
 */
export const CHOICE_CARD = {
  /** 이 메뉴 id 들이 그만두기 줄을 빼고 `count` 칸이면 카드로 (그 밖은 목록) */
  menus: ['evolve', 'reward', 'passive'] as readonly string[],
  count: 3,
  /** 카드 폭·최소 높이·간격·안쪽 여백 */
  w: 212,
  minH: 208,
  gap: 22,
  pad: 14,
  /** 탁자 깔개(panel_ink) 안쪽 여백 */
  matPad: 16,
  /** 머리표 탭 높이(ink 9-slice 최소 24)·위 여백·종류 띠 폭 */
  tabH: 24,
  tabTop: 10,
  stripe: 3,
  /** 이름 글자 배율 (정수만) */
  nameScale: 2 as const,
  /** 희귀도 마름모 반지름·간격 */
  pipR: 3,
  pipGap: 3,
  /** 고른 카드 들림·그림자 어긋남(평소·들림)·그림자 알파 */
  lift: 6,
  shadow: 3,
  shadowLift: 7,
  shadowAlpha: 0.55,
  /** 고른 카드 테 (층 강조 슬롯, 2px) */
  focusSlot: 20,
  /** 못 고르는 카드 흔들림 px·ms */
  shakePx: 2,
  shakeMs: 50,
  /** 종류별 머리표 띠 색 (층 강조 슬롯). 없으면 `kindSlotDefault` */
  kindSlot: {
    branchA: 21,
    branchB: 21,
    reinforce: 22,
    bloodPact: 19,
    awaken: 25,
    dual: 23,
    passive: 22,
    curse: 19,
  } as Readonly<Record<string, number>>,
  kindSlotDefault: 20,
  /** 희귀도 마름모 칸 수·찬 칸 색 (전설만 밝게). 칸 수 매기기는 menuView `RARITY_RANK` (목록과 같이 쓴다) */
  rarityMax: 4,
  raritySlot: 22,
  rarityTopSlot: 25,
} as const;
