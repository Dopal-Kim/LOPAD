/**
 * 62라운드 P0-6 위 가운데 알림 줄 · P1-15 HUD 다이어트 · P1-4 엘리트 체력 선 (임시값 — 62 전권 위임, 프로듀서 검토 대상).
 */
export const ALERT_UI = {
  /** 첫 알림 위 끝 y (층 제목 줄 아래). 튜토리얼 단계 카드·도전 판이 떠 있으면 그 아래 */
  top: 40,
  /** 알림 사이 */
  gap: 6,
  /** 동시에 보이는 장수 — P19 ④G: 가운데 글 띠는 늘 1장 (더 중요한 것이 오면 접고, 나머지는 줄) */
  max: 1,
  /** 다른 것 아래로 비킬 때 사이 */
  belowGap: 6,
  /** 자리 옮김 (아래 알림이 올라옴) */
  slideMs: 140,
  /** 더 중요한 알림에 밀려 접힐 때 */
  foldMs: 160,
  /** 합쳐서 다시 그리면 머무는 시간을 이만큼은 남긴다 */
  mergeHoldMs: 1400,
  depth: 52,
  /** 하데스식 배너: 잉크 띠 + 위·아래 1px 선 (G00 α) */
  bandAlpha: 0.55,
  bandPad: 6,
  /** 띠 폭 (화면 가운데, 글 폭에 맞추되 이 범위) */
  bandMinW: 260,
  bandMaxW: 640,
  /** 띠 양 끝이 흐려지는 폭 (단계 3칸) */
  bandFade: 36,
  /** 방 이름 배너 (옛 화면 가운데 2배 글) — P19 ④G: 입장 0.8초만 */
  room: { inMs: 200, holdMs: 800, outMs: 300, drop: 4 },
  /** 새 지역 띠 (노드 이름 + 지역 · 한 줄 설명 — 읽을 글이 길어 옛 머묾 그대로) */
  region: { inMs: 200, holdMs: 1300, outMs: 300, drop: 4 },
  /** 주의 · 문 닫힘 카드 */
  warn: { inMs: 160, holdMs: 1800, outMs: 300, drop: 4, blinks: 3, blinkMs: 160 },
  /** 짧은 안내 (세트 단계 등 옛 가운데 배너) */
  info: { inMs: 180, holdMs: 1400, outMs: 300, drop: 3 },
} as const;

/**
 * '주의' 카드와 한 장으로 합칠 시스템 공지 (계약 `story-text.json` notices.trialStart). 시스템이 STORY notice 로 보낸다.
 * 문구가 바뀌면 여기와 계약을 함께 고친다.
 */
export const ROOM_LOCK_NOTICES: readonly string[] = ['문이 닫혔다.'];

/** P1-15 HUD 다이어트 (전투 묶음) */
export const DIET = {
  /** 각성 띠: 체력 막대 바로 밑 얇은 띠 (숫자·문구 없음) */
  growthBandH: 3,
  growthBandGap: 2,
  /** 눈금 표시 (작은 = 개성 발현·단련, 큰 = 각성) 띠 위아래로 튀어나오는 px */
  tickOut: 1,
  bigTickOut: 2,
  /** 반짝 */
  flashMs: 320,
  flashAlpha: 0.8,
  /** 기력(보조 자원) 작은 원 — 무기 줄 오른쪽 */
  ringR: 6,
  ringGap: 8,
  ringBlinkMs: 220,
} as const;

/** P1-4 엘리트 체력 선: 맞았을 때만 잠깐 */
export const ELITE_HP = {
  /** 마지막 피해 뒤 보이는 시간 */
  showMs: 2600,
  fadeMs: 400,
  /** 잃은 부분 흰 꼬리가 줄어드는 시간 */
  trailMs: 420,
} as const;
