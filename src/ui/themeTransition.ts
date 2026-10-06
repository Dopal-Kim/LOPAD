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
  /** 과제 목록: 오른쪽 끝 여백 · 위 y(미니맵·'M 지도' 아래) · 폭 · 안쪽 여백 · 줄 높이 · 체크 칸 크기 */
  right: 16,
  top: 64,
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
