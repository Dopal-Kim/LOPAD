/**
 * 61 단계 6 (P14 §3, 계약 §19) 그림 속 입구 전환 · 수련장 UI 수치 (UI 판단 임시값 — 도영 님 데모 검토 대상).
 * 색은 팔레트 안(무채 G·세피아 S) + 입구 안 빛(아트 메타 `light`, 없으면 세피아 S5).
 */

/** 전환 단계 길이 (ms). 덮개를 씌우기까지 + 걷어내기 = 1.2~1.8초 (READY 기다림 제외) */
export const TRANSITION = {
  /** 'enterNode'·'training': 노드(방 자리)에서 입구 그림이 피어나는 시간 · 입구로 파고드는 시간 · 붓질로 걷히는 시간 */
  bloomMs: 160,
  diveMs: 720,
  revealMs: 620,
  /** 'floor': 큰 키아트가 액자로 떠오르는 시간 · 입구로 파고드는 시간 · 걷힘 */
  floorShowMs: 420,
  floorDiveMs: 760,
  floorRevealMs: 560,
  /** 'exitRoom': 방 화면이 붓 그림으로 굳는 시간 · 액자가 둘러지는 시간 · 줌 아웃 · 지도가 드러나는 시간 */
  freezeMs: 380,
  frameMs: 200,
  zoomOutMs: 560,
  exitRevealMs: 420,
  /** 건너뛰기: 남은 걷힘을 이만큼으로 줄인다 */
  skipRevealMs: 140,
  /** 덮인 뒤 READY 가 이만큼 안 오면 '…' 붓 점을 보인다 (계약 §19: 2초 — 덮개는 유지) */
  waitHintMs: 2000,
  /** 시스템이 끝내 READY 를 주지 않을 때 화면이 영영 검게 남지 않도록 스스로 걷는 시간 (계약 밖 안전망) */
  failsafeMs: 10000,
  /** 시작 직후 입력을 건너뛰기로 치지 않는 시간 (노드를 고른 Enter·클릭의 뗌·반복) */
  skipGuardMs: 160,
  /** 노드 지도에서 입구 그림이 처음 피어나는 크기 (논리 px 폭, 16:9) */
  bloomW: 84,
  /** 파고들기 끝: 입구 사각형 높이가 화면 높이의 몇 배가 될 때까지 */
  diveCover: 1.25,
  /** 파고들기 마지막 이 비율 동안 입구 안 어둠(덮개)이 짙어진다 */
  darkenFrom: 0.62,
  /** 'floor' 키아트 액자 크기 (화면 폭 비율) */
  floorArtW: 0.82,
  /** 'exitRoom' 줌 아웃 끝 배율 · 액자 테 두께(논리 px) */
  zoomOutTo: 0.3,
  frameW: 10,
  /** 붓 그림 처리 해상도 (논리 960×540 의 절반 — 표시할 때 부드럽게 늘린다) */
  paintW: 480,
  paintH: 270,
  /** 붓 그림: 색 단계 수 · 채도 남김 · 따뜻한 쪽으로 미는 정도 · 먹 윤곽 세기 · 종이 결 세기 · 가장자리 번짐 폭(비율) */
  posterLevels: 7,
  keepSat: 0.62,
  warm: 0.06,
  inkEdge: 0.7,
  grain: 0.08,
  bleed: 0.07,
  /** 굳음이 출구에서 번져 나가는 띠 폭 (0~1) */
  freezeSoft: 0.22,
  /** 붓질 걷힘 앞쪽 부드러움 (0~1) · 붓 줄 수 */
  brushSoft: 0.14,
  /** 아트 붓 마스크 앞쪽 부드러움 (아트 권장 띠 0.04 — 절반 해상도라 조금 넓게) */
  maskSoft: 0.05,
  brushStrokes: 6,
  /** 덮개 색: 입구 안 어둠(G01) · 종이(세피아 S1) */
  darkGray: 1,
  paperSepia: 1,
  /** 입구 안 빛이 가운데에서 번지는 세기 (0~1) */
  innerGlow: 0.2,
  /** 섬광(설정 '섬광' 켜짐일 때만): 입구에 닿는 순간 빛 알파 · 길이 */
  flashAlpha: 0.5,
  flashMs: 180,
  /** 흔들림(설정 배율): 진폭 px · 길이 */
  shakePx: 3,
  shakeMs: 160,
  /** 깊이: 모든 UI 씬 위 (씬을 맨 위로 올린다) */
  depth: 1000,
} as const;

/** 수련장 UI (오른쪽 과제 목록 · 도장 · 수련장 지도) */
export const TRAINING_UI = {
  /** 과제 목록: 오른쪽 끝 여백 · 위 y(수련장에서는 미니맵을 숨기므로 맨 위) · 폭 · 안쪽 여백 · 줄 높이 · 체크 칸 크기 */
  right: 16,
  top: 12,
  w: 232,
  padX: 10,
  padY: 8,
  rowH: 20,
  box: 10,
  /** 과제 완료 알림 머묾 · 사라짐 · 줄 반짝 */
  toastMs: 2200,
  toastFadeMs: 300,
  flashMs: 520,
  /** 방 도장: 찍히는 시간 · 머묾 · 크기(논리 px) · 기울기(도) */
  stampInMs: 220,
  stampHoldMs: 1300,
  stampSize: 96,
  stampTilt: -8,
  /** 지도: 두루마리 크기 · 방 자리 마름모 반지름 · 이름표 간격 */
  mapW: 864,
  mapH: 486,
  spotR: 16,
  labelGap: 6,
  /** HUD 깊이 (자막 50 아래, 지도 100) */
  depth: 44,
  mapDepth: 100,
} as const;

/**
 * 62 루프 2 (P2-6) 로딩 카드 (UI 판단 임시값). 키아트 960×540 을 0.5배(실제 화면 1:1)로 — 480×270.
 * 덮인 뒤 READY 가 `showAfterMs` 넘게 늦으면 띄운다(빠른 전환에는 안 보임).
 */
export const LOADING = {
  showAfterMs: 550,
  artW: 480,
  artH: 270,
  artTop: 104,
  tipGap: 14,
  tipWrap: 560,
  barGap: 12,
  barW: 320,
  barH: 4,
  /** 막대 색: 1층 강조 램프 슬롯 */
  barSlot: 22,
  inMs: 220,
  /** 다 찬 막대를 잠깐 보인 뒤 사라짐 */
  fullHoldMs: 120,
  outMs: 220,
  /** 깊이 (전환 덮개 위 · 섬광 아래) */
  depth: 20,
  /** 시간 어림: 남은 것의 63% 가 차는 시간 · 어림 상한 */
  estimateTauMs: 1600,
  estimateCap: 0.9,
  /**
   * 62 루프 3 UI H (P1-N4): 그림이 오기 전 액자 속 지역 색 종이 (바탕 · 아래 절반 번짐, 세피아·무채 램프에서) · 그림이 오면
   * 겹쳐 나타나는 시간 · 타이틀에서 키아트 5장을 미리 읽기 시작하는 지연 (타이틀 그림과 다투지 않게)
   */
  paper: {
    waste: ['#403227', '#30261e'],
    gate: ['#3e3f42', '#2f3033'],
    outer: ['#503f32', '#403227'],
    brewery: ['#6a5645', '#503f32'],
    hall: ['#30261e', '#1f1813'],
  } as Record<string, readonly [string, string]>,
  artInMs: 200,
  prefetchDelayMs: 2500,
} as const;

/**
 * 62 루프 3 UI G (도영 님 추가 지시) 지도 미리보기 카드 (UI 판단 임시값). 그림 16:9 — 수련장 지도 288×162 논리, 노드 지도 256×144
 * (노드 지도 칸 565×317 에서 어느 곳을 가리켜도 옆에 그 곳을 가리지 않는 자리가 남는 크기). 렌더 2배 텍스처를 1/2 로 그려 1:1,
 * 액자 테 4 + 그늘. 가리킨 곳이 바뀌면 0.15초 교차 페이드, 그림은 아주 느린 켄번스(1 → 1.03 → 1, 한쪽 9초).
 */
export const PREVIEW = {
  picW: 288,
  picH: 162,
  mapPicW: 256,
  mapPicH: 144,
  /** 렌더 배율 (그림 텍스처를 이만큼 크게 만들어 1/배율로 그린다 — 1920 렌더에서 1:1) */
  res: 2,
  /** 액자 테 두께 · 그늘 어긋남 */
  frame: 4,
  shadow: 3,
  /** 가리킨 곳 아이콘 가운데에서 카드까지 (아이콘 반 16 + 여백) */
  gap: 26,
  /** 그림 아래 먹 띠: 글 안쪽 여백 · 줄 사이 · 위로 번지는 계단 수·한 칸 높이 · 띠 알파 */
  bandPad: 6,
  lineGap: 1,
  bandSteps: 4,
  bandStepH: 5,
  bandAlpha: 0.78,
  /** 종류 아이콘 크기(논리) · 이름과 간격 */
  iconSize: 16,
  iconGap: 4,
  /** 교차 페이드 · 켄번스 */
  fadeMs: 150,
  kenZoom: 1.03,
  kenPeriodMs: 9000,
  /** 피할 것 무게 (겹친 넓이에 곱함): 가리킨 곳 · 지금 곳·갈 수 있는 다른 곳(+ 그 이름표) · 그 밖 노드 · 그 밖 이름표 */
  weightAnchor: 1000,
  weightKey: 40,
  weightNode: 3,
  weightLabel: 1,
  /** 수련장 지도 그림 조각: 그림 폭 대비 자르는 폭 */
  spotFrac: 0.3,
  /** 깊이 (노드 지도 100 위 · 커서 101 위) */
  depth: 102,
} as const;

/**
 * 62 루프 3 UI G 짧은 먹 번짐 암전 `mode: 'fade'` (시스템 H — 노드 이동). 가장자리에서 먹이 번져 coverMs 에 덮고(covered),
 * READY 뒤 가운데부터 revealMs 에 걷힌다. 시스템이 `durationMs` 를 주면 덮는 시간으로 쓴다(min~max 로 자름).
 */
export const FADE = {
  coverMs: 380,
  minCoverMs: 250,
  maxCoverMs: 600,
  revealMs: 300,
  /** 번지는 앞쪽 부드러움 (0~1) · 먹 얼룩 잡음 섞는 비율 · 얼룩 칸 크기(처리 해상도 px) */
  soft: 0.2,
  noise: 0.28,
  blotCell: 36,
} as const;
