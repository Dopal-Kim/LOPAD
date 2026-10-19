import { TELL } from './themeP19';

/**
 * P21 어두운 성인 톤 (decisions/2026-10-19-P21-dark-brutal §2 · contracts/dark-brutal). UI 판단 값 1차 — 2차 측정 뒤 조정.
 * 색은 뼈빛·검붉은색·먹 셋만 새로 둔다(따뜻한 색은 불·불씨·피에만 — 기둥 1). 예고 색(free-combat §2)은 그대로 `TELL`.
 * 이 파일은 theme.ts 가 부르므로 theme.ts 를 부르지 않는다.
 */
export const DARK = {
  /** 뼈빛 — HUD 본문·팝 숫자 */
  bone: '#d8cfc0',
  /** 밝은 뼈빛 — 강조 글 (할로가 검붉어 따로 읽힌다) */
  boneHi: '#ece3d2',
  /** 흐린 뼈빛 — 흐린 글 */
  boneDim: '#9d9587',
  /** 꺼진 뼈빛 — 못 고르는 줄 */
  boneDead: '#564e45',
  /** 검붉은 피 — 강조 할로 (title.json colors.accent.bloodLight 와 같은 값) */
  blood: '#741d12',
  /** 저HP 숫자 (먹 위에서 읽히는 피) */
  bloodLit: '#b8382b',
  /** 마른 피 — 비네트·띠 (title.json colors.accent.blood) */
  bloodDeep: '#3a0f0c',
  /** 먹 그림자 */
  ink: '#0a0807',
} as const;

/** 저HP 피 비네트 (`ui:low-hp` — HUD 씬 맨 아래 층. 시스템 월드 비네트와 별개로 가장자리만) */
export const LOW_HP_VIG = {
  /** 맥박 사이 알파 · 맥박 꼭대기 알파 · 섬광 끔(고정) 알파 */
  alphaMin: 0.22,
  alphaMax: 0.5,
  alphaFixed: 0.34,
  /** 심장 박동 (분당 ~66) — 쿵·쿵 두 번 */
  hz: 1.1,
  /** 둘째 박동이 오는 위상 · 박동 폭 (위상 단위) */
  beat2: 0.22,
  beatW: 0.07,
  beat2Gain: 0.6,
  /** 켜짐·꺼짐 */
  fadeInMs: 500,
  fadeOutMs: 900,
  depth: -1,
} as const;

/** 처형 순간 가장자리 (`ui:player-execute` — 짧게 조였다 풀린다) */
export const EXEC_EDGE = {
  alpha: 0.62,
  /** 섬광 끔이면 이만큼만 */
  alphaNoFlash: 0.3,
  inMs: 50,
  holdMs: 90,
  outMs: 320,
  /** 시작 배율 — 화면보다 크게 시작해 1 로 좁혀 들어온 뒤 반쯤 다시 풀린다 */
  squeeze: 1.18,
  depth: -0.5,
} as const;

/** 처형 가능 표식 (`ui:enemy-executable` — 적 발밑 짧은 낫 모양, 예고 색 '기회') */
export const EXEC_MARK = {
  color: TELL.chance,
  /** 낫 날 반지름 (논리 px) · 납작함(세로 배율) · 날 두께 */
  r: 8,
  flat: 0.45,
  thick: 2,
  /** 발밑에서 아래로 (계약: screen = 적 발밑) */
  dy: 1,
  /** 숨 쉬듯 알파 (느리게) */
  pulseMs: 900,
  alpha: [0.7, 1] as [number, number],
  depth: 6,
} as const;

/** 주인공 상흔 → 체력 막대 균열 (`ui:player-wounded` · snapshot.player.wound) */
export const WOUND_HUD = {
  /** 단계별 균열 수 (0·1·2·3) */
  cracks: [0, 1, 3, 5],
  /** 단계 2 부터 균열 끝에 새는 불씨 (주인공은 숯빛 망령 — 피 대신 불씨) */
  emberFrom: 2,
  crack: DARK.ink,
  ember: '#c4471c',
  /** 박힌 화살 표시 (하트 위 작은 획) 최대 */
  arrowsMax: 5,
  arrow: DARK.boneDim,
} as const;
