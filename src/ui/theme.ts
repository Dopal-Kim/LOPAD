import type { MapPathSpec } from './routeView';

/**
 * UI 테마 (41라운드, 계약 `contracts/ui-art-kit.md` v0.4).
 * 색은 팔레트 사본 `assets/ui/kit/palette.json` 의 값만 쓴다 — 무채 G00~G15, 세피아 S0~S5, 층 강조 램프 16~27.
 * 글자는 1.2절 발광 규칙(`TEXT_STYLES`)만 쓴다. 새 색을 만들지 않는다 (알파 0.5 / 0.55 만 허용).
 */

/** 무채 16칸 (G00~G15) — 팔레트 고정값 */
export const GRAY = [
  '#000000',
  '#141516',
  '#212224',
  '#2f3033',
  '#3e3f42',
  '#4d4f52',
  '#5c5e62',
  '#6c6f73',
  '#7d8084',
  '#8e9195',
  '#a0a2a6',
  '#b2b4b8',
  '#c5c6c9',
  '#d8d9db',
  '#ebeced',
  '#ffffff',
] as const;

/** UI 전용 세피아 램프 S0~S5 (`ui.ramp`, v0.4) */
export const SEPIA = ['#1f1813', '#30261e', '#403227', '#503f32', '#6a5645', '#c6a58b'] as const;

/** 1층 '잔' 강조 램프 (슬롯 16~27 → 인덱스 0~11). 팔레트 JSON 을 못 읽었을 때의 폴백 */
export const FLOOR1_RAMP = [
  '#1a110f',
  '#3f271d',
  '#653b24',
  '#8b4d22',
  '#b0611a',
  '#d67a11',
  '#dc8e23',
  '#e2a33c',
  '#e8b858',
  '#eecc78',
  '#f4de9b',
  '#faeec0',
] as const;

/** 강조 램프 슬롯 번호 → 램프 배열 인덱스 */
export const ACCENT_FIRST_SLOT = 16;

/** 글꼴 (34·39라운드: Galmuri 단일, Bold 금지). 11 은 한자 포함 가능, 14 는 한자 없는 고정 제목만 */
export const FONT = {
  body: { family: 'Galmuri11', px: 11, lineHeight: 12 },
  title: { family: 'Galmuri14', px: 14, lineHeight: 15 },
} as const;
export type FontKind = keyof typeof FONT;

/** 글꼴 파일 (UI 소유). Galmuri11 은 `public/style.css` 의 @font-face 가 먼저 선언한다 */
export const FONT_FILES: Record<string, string> = {
  Galmuri11: 'assets-game/ui/fonts/Galmuri11.woff2',
  Galmuri14: 'assets-game/ui/fonts/Galmuri14.woff2',
};

/**
 * 발광 글자 스타일 (계약 1.2절 표). `halo`/`shade` 가 없으면 그 ring 을 그리지 않는다.
 * `accentSlot` 이 있으면 현재 층 강조 램프의 그 슬롯 색을 쓴다 (문자열 색은 무시).
 */
export interface GlowStyle {
  body: string | { accentSlot: number };
  bodyAlpha: number;
  halo?: { color: string | { accentSlot: number }; alpha: number };
  shade?: { color: string; alpha: number };
}

export const TEXT_STYLES = {
  /** 종이 본문 */
  page_body: {
    body: SEPIA[5],
    bodyAlpha: 1,
    halo: { color: SEPIA[4], alpha: 1 },
    shade: { color: SEPIA[2], alpha: 1 },
  },
  /** 종이 제목 */
  page_title: {
    body: GRAY[15],
    bodyAlpha: 1,
    halo: { color: SEPIA[4], alpha: 1 },
    shade: { color: SEPIA[2], alpha: 1 },
  },
  /** 선택 항목 (커서 옆): 할로 = 층 강조 20 (α0.5) */
  page_selected: {
    body: GRAY[15],
    bodyAlpha: 1,
    halo: { color: { accentSlot: 20 }, alpha: 0.5 },
    shade: { color: SEPIA[2], alpha: 1 },
  },
  /** 비선택 항목 */
  page_unsel: {
    body: GRAY[13],
    bodyAlpha: 1,
    halo: { color: SEPIA[4], alpha: 1 },
    shade: { color: SEPIA[2], alpha: 1 },
  },
  /** 흐린 글·안내 (할로·그늘 없음) */
  page_faint: { body: SEPIA[5], bodyAlpha: 0.55 },
  /** 잉크 HUD 본문·자막·층 제목 */
  ink_body: {
    body: GRAY[14],
    bodyAlpha: 1,
    halo: { color: { accentSlot: 20 }, alpha: 0.5 },
    shade: { color: GRAY[0], alpha: 1 },
  },
  /** HUD 흐림 (개성 수치·조작 안내·M) */
  ink_faint: { body: GRAY[11], bodyAlpha: 1, shade: { color: GRAY[0], alpha: 1 } },
  /** 공지·보스 이름 */
  ink_accent: {
    body: { accentSlot: 22 },
    bodyAlpha: 1,
    halo: { color: { accentSlot: 20 }, alpha: 0.5 },
    shade: { color: GRAY[0], alpha: 1 },
  },
  /**
   * 60라운드 §14.9 엘리트 이름표 글자 (아트 JSON 권장 #eecc78 = 1층 램프 슬롯 25, 자체 발광) — 할로 없이 그늘 G00.
   * 월드 위 이름표 전용 (종이·HUD 글자 아님)
   */
  plate_name: {
    body: { accentSlot: 25 },
    bodyAlpha: 1,
    shade: { color: GRAY[0], alpha: 1 },
  },
  /**
   * 61라운드 단계 2 원한의 한마디 (STORY 'voice', 월드 위 잉크 글자) — 무기마다 글씨 색이 다르다. 팔레트 색·허용 알파만.
   * 칼 = 서늘한 회백 G13 + 무채 할로 G07(0.5) · 대검 = 잉걸 강조 21 + 강조 18 할로(0.5) · 단검 = 흐린 G10 할로 없음(속삭임) ·
   * 활 = 세피아 S5 + S4 할로(0.5)
   */
  voice_katana: {
    body: GRAY[13],
    bodyAlpha: 1,
    halo: { color: GRAY[7], alpha: 0.5 },
    shade: { color: GRAY[0], alpha: 1 },
  },
  voice_greatsword: {
    body: { accentSlot: 21 },
    bodyAlpha: 1,
    halo: { color: { accentSlot: 18 }, alpha: 0.5 },
    shade: { color: GRAY[0], alpha: 1 },
  },
  voice_dagger: { body: GRAY[10], bodyAlpha: 1, shade: { color: GRAY[0], alpha: 1 } },
  voice_bow: {
    body: SEPIA[5],
    bodyAlpha: 1,
    halo: { color: SEPIA[4], alpha: 0.5 },
    shade: { color: GRAY[0], alpha: 1 },
  },
} as const satisfies Record<string, GlowStyle>;
export type TextStyleName = keyof typeof TEXT_STYLES;

/** 선택 목록·레이아웃 공통 수치 (정수) */
export const LAYOUT = {
  /** 화면 가장자리 안쪽 여백 (32라운드 권장 16 이상) */
  edge: 16,
  /** 선택 목록 줄 간격: 글꼴 높이 12 + 할로·그늘 4 + 여백 2 */
  row: 18,
  /** detail 줄 간격 */
  detail: 16,
  /** 항목 사이 추가 간격 (detail 있는 항목 뒤) */
  gap: 4,
  /** 비활성 항목 알파 (61라운드 플레이 점검 #13: 0.45 → 허용 알파 0.55, 양피지 위에서 읽히게) */
  disabledAlpha: 0.55,
  /** 도장 알파 (계약 2.5절 권장) */
  stampAlpha: 0.85,
  /** 미니맵 한 칸 */
  miniCell: 12,
} as const;

/** 워프 지도 (45라운드 Q3·Q9·Q10, 임시값) */
export const WARP = {
  /** 지도 한 칸 최대·최소 (정수 px) */
  cellMax: 40,
  cellMin: 16,
  /** 지도 영역 최대 크기 */
  mapMaxW: 520,
  mapMaxH: 340,
  /** 방 칸 안쪽 여백 */
  cellInset: 3,
  /** 오른쪽 안내 칸 폭 */
  sideW: 196,
  /** 페이지 안쪽 여백 */
  pad: 24,
  /** 배경 어둡게 (허용 알파 0.55) */
  dimAlpha: 0.55,
  /** 갈 수 없는 방 글리프 알파 */
  dimGlyphAlpha: 0.45,
  /** 오버레이 depth (HUD 자막 50 보다 위) */
  depth: 100,
} as const;

/**
 * 48라운드 노드 지도·HUD 노드 띠·탄생 연출 (임시값, 도영 님 검토 대상).
 * 960×540 화면에 일기장 한 페이지(책 틀 포함 896×488)로 1층 10노드 안팎이 들어가게 잡았다.
 */
export const ROUTE = {
  /** 페이지 크기 (책 틀 inner 16 이 사방에 붙는다) */
  pageW: 864,
  pageH: 456,
  pad: 28,
  /** 지도 영역 높이 (이름표 포함) */
  mapH: 288,
  /** 단계 가로 간격 상한·줄 세로 간격 상한 */
  colMax: 128,
  rowMax: 96,
  /** 이름표 자리 때문에 노드 줄을 위로 올리는 양 */
  labelLift: 14,
  /** 마름모 반대각선 (Graphics 폴백). 노드 아이콘 시트(32×32)가 있으면 iconR */
  nodeR: 18,
  iconR: 18,
  /** available 맥동 고리 반대각선·주기 */
  pulseR: 24,
  pulseMs: 640,
  /** 이름표: 노드 아래 간격, 줄바꿈 폭 = 단계 간격 - wrapPad */
  labelGap: 6,
  wrapPad: 12,
  /** 점선: 점 크기, 간격(지나온 길·고를 길 / 흐린 길), 노드 가장자리에서 비우는 양 */
  dot: 2,
  dotStep: 6,
  dotStepFaint: 9,
  dotTrim: 6,
  /** 주인공 표시 위아래 흔들림 주기 (정수 1px 이동) */
  bobMs: 420,
  /** 배경 어둡게 (허용 알파 0.55)·흐린 노드 알파 */
  dimAlpha: 0.55,
  faintAlpha: 0.45,
  /** 오버레이 depth (HUD 자막 50 보다 위, 워프 지도와 같은 자리) */
  depth: 100,
  /** HUD 우상단 노드 띠: 단계 간격·줄 간격·작은 마름모 반대각선·틀 안쪽 여백·글 줄 높이 */
  strip: { col: 12, row: 10, r: 3, pad: 8, textH: 16, minW: 100 },
  /** 노드 진입 제목은 기존 배너(1.6초)와 같다. 탄생 중 안내 위치·안전 해제 시간 */
  birthHintBottom: 24,
  birthFailsafeMs: 15000,
} as const;

/**
 * 49라운드 M 지도 (입체 지도 + 위치 정보 + 넘어가기 확인). 임시값, 도영 님 검토 대상.
 * 페이지(ROUTE.pageW×pageH) 안을 왼쪽 지도 칸 + 오른쪽 위치 정보 칸으로 나눈다.
 */
export const MAP3D = {
  /** 오른쪽 위치 정보 칸 폭·지도 칸과의 간격 */
  sideW: 232,
  sideGap: 16,
  /** 지도 칸: 제목 줄 아래부터 안내 줄 위까지. 아래 안내 줄 높이 */
  hintH: 22,
  /** 원근: 가장 먼 단계 크기 비, 멀수록 촘촘한 정도, 원근을 풀 최소 단계 간격, 가까운 줄 간격 상한 */
  farScale: 0.62,
  ease: 0.55,
  minGap: 40,
  rowMax: 150,
  /** 노드 자리: 위 여백(아이콘 높이 + 들림), 아래 여백(그림자·이름표) */
  padTop: 44,
  padBottom: 26,
  /** 양피지: 위 폭 비(=farScale 근처), 좌우·위아래 바깥 여백, 말린 가장자리 두께, 그림자 어긋남 */
  sheetTopRatio: 0.6,
  sheetInsetX: 4,
  sheetInsetY: 6,
  sheetRoll: 4,
  sheetShadow: 4,
  /** 지평선 격자: 가로선 개수(깊이 고르게), 세로 수렴선 개수 */
  gridRows: 6,
  gridCols: 7,
  /** 노드 들림(가까움·멂)과 그림자 반지름 (가까울 때) */
  liftNear: 8,
  liftFar: 4,
  shadowRx: 15,
  shadowRy: 4,
  /** 길 점: 가까운 쪽 점 크기 3 (깊이 < nearDotDepth), 그 외 2 */
  nearDotDepth: 0.34,
  /** 이름표: 아이콘 오른쪽 간격, 줄바꿈 폭 */
  labelGap: 6,
  labelWrap: 96,
  /** 넘어가기 확인 창: 크기, 버튼 높이·최소 폭·간격, 뒤 어둡게(허용 알파 0.5) */
  confirmW: 300,
  confirmH: 112,
  buttonH: 18,
  buttonMinW: 64,
  buttonGap: 16,
  confirmDim: 0.5,
} as const;

/**
 * 지도 배경 일러스트 (49라운드 자리, 50라운드 적용 — 계약 §12). `assets/ui/map_bg_<floor>.png` 가 있는 층 번호(UiRoute.floor).
 * 없는 파일을 읽어 404 를 내지 않게 목록으로 둔다. 그림은 지도 칸에 비율 유지로 맞추고(양피지 사다리꼴·원근 대신
 * 일러스트 좌표계 우선), 노드는 `MAP_PATHS[floor]` 의 길을 따라 놓는다. 큰 그림이라 그 층 노드 지도가 처음 필요할 때 읽는다.
 */
export const MAP_BG_FLOORS: readonly number[] = [1];

/**
 * 50라운드: 층별 지도 그림 속 길 (그림 원본 960×540 px 기준, 임시값 — 도영 님 검토 대상).
 * 1층 `map_bg_1`: 왼쪽 위 황무지 점선 길 → 성문 → 가운데 아래로 처진 밝은 길(외곽 거리 사이) → 양조 구역 → 오른쪽 위 연회장 계단(보스).
 * 단계(col)는 길이 비율로 고르게, 같은 단계 갈래(row)는 길에 수직으로 rowSpread 간격.
 */
export const MAP_PATHS: Readonly<Record<number, MapPathSpec>> = {
  1: {
    srcW: 960,
    srcH: 540,
    points: [
      [100, 112],
      [160, 146],
      [252, 212],
      [330, 262],
      [420, 312],
      [520, 345],
      [610, 348],
      [690, 305],
      [760, 250],
      [855, 220],
    ],
    rowSpread: 104,
    margin: 34,
    farScale: 0.82,
    tangentSpan: 40,
  },
};

/** 50라운드 일러스트 지도: 그림 그림자 어긋남·테두리, 길 점(밝은 점 + 어두운 테두리 1px) */
export const MAP_ILLUST = {
  shadow: 4,
  /** 길 점 테두리 두께 (어두운 그림 위에서 보이게) */
  dotRim: 1,
} as const;

/**
 * 50라운드 지역 키아트 (`assets/ui/keyart/keyart_<key>.png`, 960×540, 아트 §8 사본). 시스템의 `UiRouteNode.region` 은 표시 이름이라
 * 이름 안의 낱말로 키를 찾는다 (임시 — 계약에 지역 키가 생기면 그것을 쓴다). 위에서부터 처음 맞는 것.
 */
export const REGION_ART: readonly { key: string; match: readonly string[] }[] = [
  { key: 'gate', match: ['성문', 'gate'] },
  { key: 'outer', match: ['외곽', 'outer'] },
  { key: 'brewery', match: ['양조', 'brewery'] },
  { key: 'hall', match: ['연회', '본영', 'hall'] },
  { key: 'waste', match: ['황무지', '전장', '여정', 'waste'] },
];

/** 50라운드 지역 카드 (노드 진입 시 지역이 바뀌면 키아트 전면 카드, 임시값) */
export const REGION_CARD = {
  /** 나타남 · 머묾 · 사라짐 (합 1.9초) */
  fadeInMs: 300,
  holdMs: 1300,
  fadeOutMs: 300,
  /** 아무 키로 넘길 때 사라지는 시간, 카드가 뜬 직후 입력을 무시하는 시간 */
  skipFadeMs: 160,
  skipGuardMs: 200,
  /** 글자가 배경보다 늦게 나타나는 비율 (나타남 시간 기준) */
  textLag: 0.5,
  /** 키아트를 아직 못 읽었을 때 기다리는 최대 시간 (넘으면 그림 없이) */
  loadWaitMs: 1200,
  /** 글자 띠: 가운데 y·높이 (G00 α0.55) */
  bandY: 400,
  bandH: 84,
  /** 이름과 설명 사이 */
  lineGap: 6,
  /** HUD 자막(50) 위, 노드 지도(100) 아래 */
  depth: 90,
} as const;

/** 50라운드 M 지도 오른쪽 위치 정보 칸의 지역 키아트 배경: 칸 바깥 여백, 어둡게 덮는 횟수(G00 α0.55 씩) */
export const SIDE_ART = {
  padX: 8,
  padY: 6,
  darken: 2,
} as const;

/**
 * 49라운드 무기 자원 게이지 (HUD 하단 묶음 3행, 임시값). 색은 팔레트 안 — 유채색은 현재 층 강조 램프 슬롯.
 */
export const RES = {
  /** 자원이 있을 때 하단 묶음 높이 (없으면 64) */
  bundleH: 80,
  /** 3행 y (묶음 위에서) */
  rowY: 59,
  /** 라벨 시작 x·게이지 시작 x (묶음 왼쪽에서) */
  labelX: 8,
  gaugeX: 44,
  /** 기력 막대 폭 */
  barW: 150,
  /** 화살 칸: 한 칸 폭·간격·높이, 칸으로 그릴 최대 개수(넘으면 막대) */
  arrowW: 5,
  arrowGap: 3,
  arrowH: 11,
  arrowCap: 16,
  /** 진행 링 반지름 */
  ringR: 5,
  /** 열기: 막대 폭, 단계 눈금 수, 눈금 칸 크기·간격 */
  heatW: 120,
  heatStages: 3,
  pip: 6,
  pipGap: 3,
  /** 과열 맥동 (1 ↔ 0.55 계단) 주기 */
  blinkMs: 200,
  /** 상태별 색 슬롯: 기력 보통·부족, 화살 찬 칸, 열기 단계 1~3(달아오를수록 밝게), 링 */
  staminaOk: 23,
  staminaLow: 20,
  arrowFull: 22,
  heatSlots: [20, 22, 25],
  ring: 22,
} as const;

/**
 * 56라운드 무기 고유 자원 눈금 (계약 §13, 임시값). HUD 2행 무기 이름 바로 오른쪽: 라벨(ink_faint) + 칸.
 * 칸 모양은 문자열 행('.' 빈칸, 그 외 칠함). 꺼진 칸 = 테두리 G06 · 안쪽 G03 (열기 단계 눈금과 같은 문체).
 * 색은 팔레트 안에서만 — 유채색은 층 강조 슬롯(16~27), 무채 G.
 */
export const WGAUGE = {
  /** 무기 이름 끝 → 라벨, 라벨 → 첫 칸, 마지막 칸 → 개성 아이콘 사이 */
  gapName: 10,
  gapLabel: 4,
  gapAfter: 14,
  /** 마지막 칸 → 상태 글('집중') */
  gapState: 6,
  /** 개성 수치 글과 '우클릭 …' 사이 최소 간격 — 모자라면 고유 자원 라벨을 빼고, 그래도 모자라면 '우클릭 …' 을 숨긴다 */
  minGapSecondary: 8,
  /** 칸 위쪽 y (2행 글 상자 위에서. 개성 게이지 틀과 세로 가운데를 맞춤) */
  cellTop: 3,
  /** 검기: 칼날 마름모 7×8, 간격 2. 칸 색 = 재 G11 → 호박 22 → 백열 27 */
  kenki: {
    mask: ['...x...', '..xxx..', '.xxxxx.', 'xxxxxxx', 'xxxxxxx', '.xxxxx.', '..xxx..', '...x...'],
    gap: 2,
    colors: [{ gray: 11 }, { slot: 22 }, { slot: 27 }],
  },
  /** 울분: 이어진 3칸 막대 14×6, 간격 1. 채움 색 = 지금 구간(1·2·3단) 강조 20 → 22 → 25 */
  grudge: {
    w: 14,
    h: 6,
    top: 4,
    gap: 1,
    stageSlots: [20, 22, 25],
  },
  /** 낙인: 셈 획 2×8, 간격 2. 켜짐 강조 22, 가득(최대 스택) 이면 전부 강조 25 */
  brand: {
    mask: ['xx', 'xx', 'xx', 'xx', 'xx', 'xx', 'xx', 'xx'],
    gap: 2,
    on: 22,
    full: 25,
  },
  /** 숨: 방울 7×7, 간격 2. 켜짐 G12, 정밀 조준(focusing) 중 강조 25 + '집중' 깜빡임 */
  breath: {
    mask: ['..xxx..', '.xxxxx.', 'xxxxxxx', 'xxxxxxx', 'xxxxxxx', '.xxxxx.', '..xxx..'],
    gap: 2,
    on: { gray: 12 },
    focus: 25,
  },
  /** 가득일 때 라벨을 ink_accent 로 */
  fullAccent: true,
  /** 깜빡임 (1 ↔ 0.55 계단) 주기 */
  blinkMs: 200,
} as const;

/**
 * 56라운드 그로기 (계약 §13, 결정 Q7·Q19: 1.5초 · 시간으로만 회복, 임시 표시값).
 * 3행 기력 막대 아래 2px 남은 시간선(G03 바탕 · 강조 22 남은 만큼, 오른쪽부터 줄어듦) + '그로기 1.2초'(ink_accent 깜빡임) +
 * 2행 무기 아이콘·이름·고유 자원이 1px 떨림.
 */
export const GROGGY = {
  /** 전체 시간 기본값 (계약에 없어 그로기 시작 때 본 leftMs 를 우선) */
  defaultMs: 1500,
  /** 남은 시간선: 막대 아래 y 오프셋·두께·색 슬롯 */
  lineDy: 11,
  lineH: 2,
  lineSlot: 22,
  /** 무기 줄 떨림 한 칸 시간·폭 (px) */
  shakeMs: 60,
  shakeAmp: 1,
} as const;

/**
 * 47라운드 상호작용 구조물 UI (임시값). 색은 팔레트 안에서만 — 유채색은 현재 층 강조 램프 슬롯(16~27),
 * 그 외 무채 G·세피아 S. `slot` 은 강조 램프 슬롯 번호, `gray`/`sepia` 는 고정색 인덱스.
 */
export type SwatchRef = { slot: number } | { gray: number } | { sepia: number };
export const STRUCT = {
  /** 말풍선: 안쪽 여백·구조물 윗변과의 간격·화면 여백·depth(자막 50 아래) */
  bubblePad: 6,
  bubbleGap: 6,
  bubbleMargin: 8,
  bubbleDepth: 40,
  /** 길게 누르기 게이지 높이 */
  holdBarH: 3,
  /** 비용 부족·사용 불가 흐림 알파 (허용 알파 0.55) */
  dimAlpha: 0.55,
  /** HUD 상태 칩: 층 제목 아래 시작 y, 칩 높이(ink 9-slice 최소 24)·간격, 왼쪽 띠 폭, 타이머 바 높이 */
  chipTop: 34,
  chipH: 24,
  chipGap: 2,
  chipStripe: 3,
  chipBarH: 2,
  /** 결과 토스트: 표시 시간·사라짐·최대 개수·폭 상한 (하단 HUD 묶음 오른쪽 끝 720+8 ~ 화면 여백 944 안에 들도록 216) */
  toastHoldMs: 2600,
  toastFadeMs: 300,
  toastMax: 3,
  toastMaxW: 216,
  /** 도전 판: 상단 가운데 y, 결과 표시 시간 */
  challengeTop: 34,
  challengeResultMs: 2800,
  /** HUD 칩·토스트 depth */
  hudDepth: 45,
  /** 미니맵 점 크기(px)·워프 지도 점 크기 */
  miniDot: 2,
  warpDot: 4,
  /** 패 탁자 카드 크기·간격 */
  cardW: 104,
  cardH: 140,
  cardGap: 20,
  /** 상태 종류별 띠·바 색 */
  statusColor: {
    buff: { slot: 23 },
    debuff: { slot: 19 },
    resource: { sepia: 5 },
    timer: { slot: 25 },
    rule: { gray: 11 },
    progress: { sepia: 4 },
  } satisfies Record<string, SwatchRef>,
  /** 결과 토스트 tone 별 띠 색 */
  toneColor: {
    gain: { slot: 23 },
    loss: { slot: 19 },
    mixed: { sepia: 5 },
    warn: { slot: 25 },
    info: { gray: 11 },
  } satisfies Record<string, SwatchRef>,
} as const;

export function hexToNum(hex: string): number {
  return parseInt(hex.replace('#', ''), 16);
}
