/**
 * 획 찢기 연출 (48라운드 Q8 + 49라운드 1절 + 51라운드 1절) 의 순수 계산: 수치·속도→폭/세기·식는 곡선,
 * 부스러기(49), 3획 뒤 타오름·스며듦 타임라인(53)·경로 자르기(49). Phaser 의존 없음.
 * 51라운드: 획을 가늘게(이전 2~9px → 0.9~3.2px), **빠를수록 가늘고 밝게**(붓), 곡선은 `strokeFxSpline.ts`
 * (Catmull-Rom + 일정 간격 표본), 그리기는 `strokeFxPaint.ts`(캔버스 2D 안티앨리어싱, 1px 아래 단차).
 * 수치는 전부 시스템 임시값 (이번 작업 범위상 Constants.ts 대신 여기에 — 다음 정리 때 옮긴다).
 */
import { clamp01 } from '../mathUtil';

export const STROKE_FX = {
  /** 개성 선택은 새 런 시작 전 → 강조 램프는 1층(잔) */
  FLOOR: 1,
  /**
   * 속도(px/s) → 틈 폭(px)·빛 세기 (51라운드: 붓처럼 **느리면 굵게(SLOW_PX), 빠르면 가늘게(FAST_PX)**, 빠를수록 밝게).
   * 비율 = (속도 / SPEED_REF)^CURVE_POW. 이전(48·49라운드) 2~9px 의 약 1/3.
   */
  WIDTH: { SLOW_PX: 3.2, FAST_PX: 0.9, SPEED_REF: 1800, CURVE_POW: 0.8 },
  INTENSITY: { MIN: 0.55, MAX: 1 },
  /**
   * 곡선 (51라운드): 구심 Catmull-Rom(ALPHA 0.5)으로 입력점을 잇고 STEP_PX 간격으로 다시 찍는다. SUBDIV_PX = 곡선 걷기 세분 간격.
   * 폭 평활(표본마다 새 값 비중) · 낮은 주파수 흔들림(진폭 비율, 파장 2개 px) · 시작/끝 가늘어짐(길이 px, 최소 비율).
   * MIN_INPUT_PX 보다 가까운 입력점은 버린다.
   */
  SPLINE: {
    ALPHA: 0.5,
    /** 52라운드: 1920×1080 캔버스에 맞춰 0.5 논리 px(= 실제 1px) 간격 (이전 1 · 세분 0.5) */
    STEP_PX: 0.5,
    SUBDIV_PX: 0.25,
    MIN_INPUT_PX: 0.75,
    /** 표본마다 새 값 비중 (52라운드 표본 2배 → 1-(1-0.18)^0.5, 같은 거리에서 같은 평활) */
    WIDTH_SMOOTH: 0.095,
    NOISE_AMP: 0.12,
    NOISE_WAVE_PX: [11, 4.3] as [number, number],
    TAPER_IN_PX: 12,
    TAPER_OUT_PX: 18,
    TAPER_MIN: 0.25,
  },
  /** 빛 레이어를 이 표본 수씩 끊어 그린다 (조각마다 열기가 다르다) */
  CHUNK_SAMPLES: 12,
  /** 속도 계산의 최소 시간 간격 (같은 ms 에 몰린 포인터 이벤트가 속도를 튀게 하지 않도록) */
  MIN_DT_MS: 8,
  /** 속도 평활 (새 값 비중) */
  SPEED_SMOOTH: 0.45,
  /** 백열 → 식음: 경과/COOL_MS 의 (1-x)^POW. 획을 떼면 FLARE 동안 BOOST 만큼 더 밝게 한 번 */
  COOL_MS: 2600,
  COOL_POW: 1.5,
  FLARE_MS: 300,
  FLARE_BOOST: 0.7,
  /**
   * 빛 레이어 (ADD): 폭 배율·색·알파·식는 지수. 색 'x0'/'x1' = 팔레트 fx.core, 숫자 = 현재 층 램프 인덱스(9~11 = 강조 25~27).
   * 바깥 → 안쪽 순서. 안쪽일수록 빨리 식는다 (백열 → 층 강조색 → 꺼짐)
   */
  HOT_LAYERS: [
    { width: 5.5, color: 9, alpha: 0.2, pow: 0.6 },
    { width: 2.8, color: 10, alpha: 0.4, pow: 1 },
    { width: 1.25, color: 'x1', alpha: 0.88, pow: 1.6 },
    { width: 0.5, color: 'x0', alpha: 1, pow: 2.2 },
  ] as { width: number; color: number | 'x0' | 'x1'; alpha: number; pow: number }[],
  /**
   * 남는 자국 (캔버스, 필기처럼): 틈(폭 + GAP_EXTRA) · 들뜬 가장자리 선(틈 가장자리에서 LIP_OFFSET 밖, 선 굵기 LIP_WIDTH)
   * · 안쪽 달군 가장자리(LIP_HOT_WIDTH) · 식은 잔불(폭 × EMBER_WIDTH) · 가는 심(CORE_WIDTH px). 폭 단위는 px(1 미만 가능)
   */
  SCAR: {
    GAP_COLOR: 0x000000,
    GAP_ALPHA: 0.92,
    GAP_EXTRA_PX: 0.5,
    LIP_GRAY: 6,
    LIP_ALPHA: 0.5,
    LIP_WIDTH: 0.7,
    LIP_HOT_RAMP: 3,
    LIP_HOT_ALPHA: 0.42,
    LIP_HOT_WIDTH: 0.5,
    LIP_OFFSET_PX: 0.45,
    EMBER_RAMP: 4,
    EMBER_ALPHA: 0.6,
    EMBER_WIDTH: 0.45,
    CORE_RAMP: 7,
    CORE_ALPHA: 0.35,
    CORE_WIDTH: 0.45,
    /** 들뜬 조각(작은 사각형)이 가장자리에 붙을 확률 (표본마다 — 표본은 STEP_PX 간격) · 크기 px */
    CHIP_CHANCE: 0.0175,
    CHIP_PX: [0.7, 1.4] as [number, number],
  },
  /** 불티 (ADD 파티클): 이동 px 당 개수, 한 번에 최대, 진행 반대쪽 ±SPREAD°, 속도·수명·중력 */
  SPARKS: {
    /** 51라운드: 부드러운 점 텍스처(LINEAR) 를 작게 — 가는 획에 맞춰 1px 안팎 */
    KEY: 'setup_scratch_spark_soft',
    SIZE_PX: 6,
    SCALE: [0.5, 0.08] as [number, number],
    PER_PX: 0.07,
    MAX_PER_MOVE: 6,
    SPREAD_DEG: 60,
    SPEED: [50, 230] as [number, number],
    LIFE_MS: [180, 520] as [number, number],
    GRAVITY: 620,
    /** 색: 팔레트 fx.core 2 + 층 강조 27·26 */
    RAMP_TINTS: [11, 10],
  },
  /**
   * 부스러기 (49라운드 1절 "부스러기가 떨어지는 연출"): 긁힌 화면 조각(G05~G08)·검은 재·잔불 조각이 튀어 올랐다가 중력으로 떨어진다.
   * 보통 혼합(빛이 아니라 물질). 이동 px 당 개수 × (0.5 + 빛 세기), 한 번에 최대. 각도는 Phaser 도(270 = 위).
   */
  DEBRIS: {
    /** 51라운드: 텍스처 3px(LINEAR) × 배율 0.35~0.9 — 가는 획에 맞춘 잔 부스러기 */
    KEY: 'setup_scratch_debris_fine',
    SIZE_PX: 3,
    PER_PX: 0.06,
    MAX_PER_MOVE: 5,
    /** 누를 때 · 뗄 때 한 줌 */
    ON_BEGIN: 4,
    ON_END: 12,
    SPEED: [10, 70] as [number, number],
    ANGLE: [205, 335] as [number, number],
    LIFE_MS: [700, 1400] as [number, number],
    GRAVITY: 540,
    SCALE: [0.35, 0.9] as [number, number],
    /** 색: 팔레트 gray 인덱스(화면 조각) + 검은 재(0x000000, 개수만큼 비중) + 층 램프(잔불 조각) */
    GRAYS: [5, 6, 7, 8],
    ASH: 3,
    EMBER_RAMP: [4],
  },
  /**
   * 53라운드 Q3: 3획 뒤 마무리 = **상흔이 타오르며 스며듦** (49라운드 빛 터짐 교체). 시작 = 마지막 획을 떼고 HOLD_AFTER_LAST_MS 뒤.
   * 타오름(IGNITE: 획 전체가 호박빛으로 달아오름, 미세 흔들림) → 스며듦(SEEP: 빛이 가늘어지며 식고, 자국이 '굳은 균열 + 잔불 심'으로
   * 바뀜) → 불티(EMBERS: 획에서 불티가 피어오름) → 어두워짐(DARK: 검게 덮임, 가장 어두운 순간 = peak 에 회피 시험이 뒤에서 시작)
   * → 걷힘(DARK_OUT). 빛 층은 백열(흰색) 없이 호박 램프만 (SEAR_LAYERS). 전부 임시값.
   */
  SEAR: {
    IGNITE_MS: 650,
    /** 타오름 열기 (시작 → 끝) · 일렁임 세기·주기 ms */
    IGNITE_HEAT: [0.35, 1] as [number, number],
    FLICKER: 0.16,
    FLICKER_MS: 120,
    SHAKE_INTENSITY: 0.0016,
    /** 타오름 동안 프레임당 불꽃 */
    IGNITE_SPARKS: 2,
    SEEP_MS: 800,
    /** 빛 폭 배율 (타오름 끝 → 스며듦 끝) */
    WIDTH_MUL: [1.35, 0.42] as [number, number],
    /** 남는 잔불 심 열기 · 숨쉬기 주기 ms · 세기 */
    EMBER_HEAT: 0.3,
    EMBER_PULSE_MS: 900,
    EMBER_PULSE: 0.25,
    /** 불티: 시작 시각 · 길이 · 프레임당 개수 */
    EMBERS_AT: 1050,
    EMBERS_MS: 750,
    EMBERS_PER_FRAME: 3,
    /** 검게 덮임: 시작 시각 · 덮는 시간(끝 = peak) · 걷히는 시간 */
    DARK_AT: 1800,
    DARK_IN_MS: 420,
    DARK_OUT_MS: 480,
    /** 화면 덮개 깊이 (DEPTH.SCREEN_FX 와 같게) */
    DEPTH_DARK: 50,
  },
  /** 타오르는 획 빛 층 (호박 램프 22~25 만 — 흰빛으로 넘어가지 않게 열기 상한 1, HOT_LAYERS 와 같은 형식) */
  SEAR_LAYERS: [
    { width: 7, color: 5, alpha: 0.32, pow: 0.6 },
    { width: 3.4, color: 6, alpha: 0.55, pow: 0.9 },
    { width: 1.6, color: 7, alpha: 0.85, pow: 1.3 },
    { width: 0.6, color: 9, alpha: 0.9, pow: 1.9 },
  ] as { width: number; color: number | 'x0' | 'x1'; alpha: number; pow: number }[],
  /**
   * 스며든 뒤 남는 상흔 (자국 캔버스를 이것으로 교차): 그을린 살(넓고 옅은 어둠 2겹, 폭 + px) · 균열(폭 + px) · 잔불 심(폭 배율)
   * · 가는 심 선. 램프 인덱스는 1층 호박.
   */
  SETTLED: {
    CHAR: [
      { add: 7, alpha: 0.22 },
      { add: 3, alpha: 0.3 },
    ],
    CHAR_RAMP: 0,
    GAP_ADD: 0.7,
    GAP_ALPHA: 0.95,
    LIP_GRAY: 5,
    LIP_ALPHA: 0.35,
    EMBER_RAMP: 5,
    EMBER_ALPHA: 0.8,
    EMBER_SCALE: 0.42,
    CORE_RAMP: 8,
    CORE_ALPHA: 0.55,
    CORE_WIDTH: 0.35,
  },
  /** 불티 (위로 떠오르는 ADD 파티클): 속도·수명·떠오름(음수 중력)·크기 */
  EMBERS: {
    SPEED: [8, 40] as [number, number],
    ANGLE: [240, 300] as [number, number],
    LIFE_MS: [700, 1500] as [number, number],
    GRAVITY: -70,
    SCALE: [0.9, 0.1] as [number, number],
    RAMP_TINTS: [11, 10, 9],
  },
  /** 펜 끝 빛 번짐 (방사 그라데이션, ADD) */
  TIP: { KEY: 'setup_scratch_tip', RADIUS_PX: 22, ALPHA: 0.5, SCALE_MIN: 0.28, SCALE_MAX: 0.62 },
  /** 미세 흔들림: 이 속도 이상일 때, 간격을 두고 */
  SHAKE: { MIN_SPEED: 650, MS: 70, INTENSITY: [0.0008, 0.0026] as [number, number], THROTTLE_MS: 90 },
  /** 마지막 획을 뗀 뒤 그 획의 섬광을 보여 주는 시간 → 그 뒤 타오름·스며듦(SEAR) */
  HOLD_AFTER_LAST_MS: 450,
  /** 마무리 없이 떠날 때(폴백) 자국이 사라지는 시간 */
  FADE_OUT_MS: 650,
  /** 캔버스 텍스처 키 (연출이 만들고 파괴할 때 지운다) */
  CANVAS_KEYS: { SCAR: 'setup_stroke_scar', LIGHT: 'setup_stroke_light', SETTLED: 'setup_stroke_settled' },
  /** 깊이: 등 · 자국 · 부스러기 · 빛 · 불티 · 혼불 (라벨·예시 패널 텍스트는 DEPTH.DEBUG) */
  DEPTH_SURFACE: -2,
  DEPTH_SCAR: -1,
  DEPTH_DEBRIS: 4.25,
  DEPTH_HOT: 4.3,
  DEPTH_SPARK: 4.4,
  DEPTH_FIRE: 4.5,
};

export type StrokeFxConfig = typeof STROKE_FX;

/** 속도 비율 0~1 */
export function speedRatio(speedPxPerSec: number, C: StrokeFxConfig = STROKE_FX): number {
  return clamp01(speedPxPerSec / C.WIDTH.SPEED_REF);
}

/** 51라운드 붓: 느리면 굵고, 빠를수록 가늘다 (밝기는 `gapIntensity` — 빠를수록 밝다) */
export function gapWidth(speedPxPerSec: number, C: StrokeFxConfig = STROKE_FX): number {
  const r = Math.pow(speedRatio(speedPxPerSec, C), C.WIDTH.CURVE_POW);
  return C.WIDTH.SLOW_PX + (C.WIDTH.FAST_PX - C.WIDTH.SLOW_PX) * r;
}

/** 폭 → 0(가장 가늘게)~1(가장 굵게) */
export function widthRatio(widthPx: number, C: StrokeFxConfig = STROKE_FX): number {
  return clamp01((widthPx - C.WIDTH.FAST_PX) / (C.WIDTH.SLOW_PX - C.WIDTH.FAST_PX));
}

export function gapIntensity(speedPxPerSec: number, C: StrokeFxConfig = STROKE_FX): number {
  const r = speedRatio(speedPxPerSec, C);
  return C.INTENSITY.MIN + (C.INTENSITY.MAX - C.INTENSITY.MIN) * r;
}

/** 경과 ms 의 열기 0~1 (+ 획 끝 섬광). 0 이면 식어서 지운다 */
export function heatAt(ageMs: number, flareAgeMs: number | null, C: StrokeFxConfig = STROKE_FX): number {
  const x = ageMs / C.COOL_MS;
  const base = x >= 1 ? 0 : Math.pow(1 - Math.max(0, x), C.COOL_POW);
  const flare =
    flareAgeMs !== null && flareAgeMs >= 0 && flareAgeMs < C.FLARE_MS
      ? C.FLARE_BOOST * (1 - flareAgeMs / C.FLARE_MS)
      : 0;
  return Math.min(1.6, base + (base > 0 ? flare : 0));
}

// --- 53라운드: 타오름·스며듦 ---

export interface SearState {
  /** 타오름 0~1 · 스며듦 0~1 */
  ignite: number;
  seep: number;
  /** 획 빛 열기 (SEAR_LAYERS 기준) · 빛 폭 배율 */
  heat: number;
  widthMul: number;
  shaking: boolean;
  embers: boolean;
  /** 화면 검은 정도 0~1 */
  dark: number;
  /** 가장 어두운 순간을 지났다 (뒤에서 다음 장면 시작) */
  peaked: boolean;
  done: boolean;
}

/** 주요 시각 (시작 기준 ms) */
export function searTimes(C: StrokeFxConfig = STROKE_FX): {
  seepAt: number;
  settledAt: number;
  peakAt: number;
  doneAt: number;
} {
  const S = C.SEAR;
  const peakAt = S.DARK_AT + S.DARK_IN_MS;
  return { seepAt: S.IGNITE_MS, settledAt: S.IGNITE_MS + S.SEEP_MS, peakAt, doneAt: peakAt + S.DARK_OUT_MS };
}

export function searAt(t: number, C: StrokeFxConfig = STROKE_FX): SearState {
  const S = C.SEAR;
  const T = searTimes(C);
  const ignite = clamp01(t / S.IGNITE_MS);
  const seep = clamp01((t - T.seepAt) / S.SEEP_MS);
  const ease = (x: number) => x * x * (3 - 2 * x);
  let heat: number;
  let widthMul: number;
  if (t < T.seepAt) {
    heat = S.IGNITE_HEAT[0] + (S.IGNITE_HEAT[1] - S.IGNITE_HEAT[0]) * ease(ignite);
    heat *= 1 + S.FLICKER * Math.sin((t / S.FLICKER_MS) * Math.PI * 2);
    widthMul = 1 + (S.WIDTH_MUL[0] - 1) * ease(ignite);
  } else {
    const e = ease(seep);
    heat = S.IGNITE_HEAT[1] + (S.EMBER_HEAT - S.IGNITE_HEAT[1]) * e;
    if (seep >= 1) heat *= 1 + S.EMBER_PULSE * Math.sin(((t - T.settledAt) / S.EMBER_PULSE_MS) * Math.PI * 2);
    widthMul = S.WIDTH_MUL[0] + (S.WIDTH_MUL[1] - S.WIDTH_MUL[0]) * e;
  }
  let dark = 0;
  if (t >= S.DARK_AT && t < T.peakAt) dark = (t - S.DARK_AT) / S.DARK_IN_MS;
  else if (t >= T.peakAt) dark = 1 - (t - T.peakAt) / S.DARK_OUT_MS;
  return {
    ignite,
    seep,
    heat,
    widthMul,
    shaking: t < T.seepAt,
    embers: t >= S.EMBERS_AT && t < S.EMBERS_AT + S.EMBERS_MS,
    dark: clamp01(dark),
    peaked: t >= T.peakAt,
    done: t >= T.doneAt,
  };
}

/** 점 목록 [x0,y0,x1,y1,…] 의 길이 */
export function pathLength(pts: number[]): number {
  let L = 0;
  for (let i = 2; i < pts.length; i += 2) L += Math.hypot(pts[i] - pts[i - 2], pts[i + 1] - pts[i - 1]);
  return L;
}

/** 경로 앞쪽 frac(0~1) 만큼 (마지막 점은 보간) */
export function pathPrefix(pts: number[], frac: number): number[] {
  if (pts.length < 4 || frac >= 1) return pts.slice();
  if (frac <= 0) return pts.slice(0, 2);
  let remain = pathLength(pts) * frac;
  const out = [pts[0], pts[1]];
  for (let i = 2; i < pts.length; i += 2) {
    const d = Math.hypot(pts[i] - pts[i - 2], pts[i + 1] - pts[i - 1]);
    if (d >= remain) {
      const t = d > 0 ? remain / d : 0;
      out.push(pts[i - 2] + (pts[i] - pts[i - 2]) * t, pts[i - 1] + (pts[i + 1] - pts[i - 1]) * t);
      return out;
    }
    out.push(pts[i], pts[i + 1]);
    remain -= d;
  }
  return out;
}

/** 경로의 frac 지점 좌표 */
export function pathPointAt(pts: number[], frac: number): { x: number; y: number } {
  const p = pathPrefix(pts, frac);
  return { x: p[p.length - 2], y: p[p.length - 1] };
}
