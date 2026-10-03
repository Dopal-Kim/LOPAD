/**
 * 획 찢기 연출 (48라운드 Q8 + 49라운드 1절 + 51라운드 1절) 의 순수 계산: 수치·속도→폭/세기·식는 곡선,
 * 부스러기(49), 3획 뒤 빛 터짐 타임라인·광선 배치·경로 자르기(49). Phaser 의존 없음.
 * 51라운드: 획을 가늘게(이전 2~9px → 0.9~3.2px), **빠를수록 가늘고 밝게**(붓), 곡선은 `strokeFxSpline.ts`
 * (Catmull-Rom + 일정 간격 표본), 그리기는 `strokeFxPaint.ts`(캔버스 2D 안티앨리어싱, 1px 아래 단차).
 * 수치는 전부 시스템 임시값 (이번 작업 범위상 Constants.ts 대신 여기에 — 다음 정리 때 옮긴다).
 */

export const STROKE_FX = {
  /** 개성 선택은 새 런 시작 전 → 강조 램프는 1층(잔) */
  FLOOR: 1,
  /** 긁히는 표면 (절차 생성 캔버스 텍스처, 씬 재시작에도 재사용) */
  SURFACE: {
    KEY: 'setup_scratch_surface',
    /** 팔레트 gray 인덱스: 바탕 G01, 잡점 G02·G03, 결 G03 */
    BASE_GRAY: 1,
    GRAIN_GRAYS: [2, 3],
    GRAIN_DENSITY: 0.14,
    FIBERS: 70,
    FIBER_GRAY: 3,
    FIBER_ALPHA: 0.35,
    /** 가장자리 어둡게 (0 = 없음, 1 = 검정) */
    VIGNETTE: 0.55,
  },
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
    STEP_PX: 1,
    SUBDIV_PX: 0.5,
    MIN_INPUT_PX: 0.75,
    WIDTH_SMOOTH: 0.18,
    NOISE_AMP: 0.12,
    NOISE_WAVE_PX: [11, 4.3] as [number, number],
    TAPER_IN_PX: 12,
    TAPER_OUT_PX: 18,
    TAPER_MIN: 0.25,
  },
  /** 빛 레이어를 이 표본 수씩 끊어 그린다 (조각마다 열기가 다르다) */
  CHUNK_SAMPLES: 6,
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
    CHIP_CHANCE: 0.035,
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
   * 3획 뒤 빛 터짐 (49라운드 1절 "획을 다 그은 이후 … 화면이 살짝 흔들린 이후 해당 획에서 빛이 터져나오는 연출"):
   * 모음(CHARGE: 흔들림 + 획 전체가 맥동하며 달아오름 + 부스러기) → 백열 섬광이 획 경로를 따라 달림(TRACE)
   * → 획에서 광선이 사방으로 뻗음(RAYS, 트레이스 RAYS_AT 지점부터) → 화면이 하얗게(WHITE_IN) → 유지(HOLD) → 걷힘(WHITE_OUT).
   * 하얗게 가장 밝은 순간(peak)에 회피 시험이 뒤에서 시작되고, 걷히면서 드러난다.
   */
  BURST: {
    CHARGE_MS: 620,
    SHAKE_INTENSITY: 0.0045,
    /** 모음 동안 획 열기 (시작 → 끝) · 맥동 주기 ms */
    CHARGE_HEAT: [0.35, 1.05] as [number, number],
    PULSE_MS: 90,
    /** 모음 동안 프레임당 부스러기 */
    CHARGE_DEBRIS: 3,
    TRACE_MS: 420,
    /** 섬광 머리의 열기 (HOT_LAYERS 기준, 1 이상 = 더 하얗게) */
    TRACE_HEAT: 1.6,
    RAYS_AT: 0.7,
    RAYS_MS: 600,
    RAY_COUNT: 28,
    /** 광선 길이·끝 폭(px)·각도 흔들림(rad)·늦게 나오는 정도(0~1) */
    RAY_LEN: [180, 560] as [number, number],
    RAY_WIDTH: [6, 24] as [number, number],
    /** 광선 뿌리 반폭 px · 섬광 머리 반지름 px · 섬광 획 폭 배율(느린 폭 기준) */
    RAY_ROOT_PX: 0.8,
    TRACE_HEAD_PX: 4,
    TRACE_WIDTH: 1.4,
    RAY_JITTER: 0.4,
    RAY_STAGGER: 0.35,
    /** 중심 빛 번짐: 전용 방사 그라데이션 텍스처(반지름 px) · 최대 배율 */
    GLOW_KEY: 'setup_burst_glow',
    GLOW_RADIUS_PX: 128,
    GLOW_SCALE: 2.8,
    WHITE_IN_MS: 190,
    HOLD_MS: 110,
    WHITE_OUT_MS: 760,
    /** 화면 섬광 깊이 (DEPTH.SCREEN_FX 와 같게) */
    DEPTH_WHITE: 50,
  },
  /** 펜 끝 빛 번짐 (방사 그라데이션, ADD) */
  TIP: { KEY: 'setup_scratch_tip', RADIUS_PX: 22, ALPHA: 0.5, SCALE_MIN: 0.28, SCALE_MAX: 0.62 },
  /** 미세 흔들림: 이 속도 이상일 때, 간격을 두고 */
  SHAKE: { MIN_SPEED: 650, MS: 70, INTENSITY: [0.0008, 0.0026] as [number, number], THROTTLE_MS: 90 },
  /** 마지막 획을 뗀 뒤 그 획의 섬광을 보여 주는 시간 → 그 뒤 빛 터짐(BURST) */
  HOLD_AFTER_LAST_MS: 450,
  /** 빛 터짐 없이 떠날 때(폴백) 자국이 사라지는 시간 */
  FADE_OUT_MS: 650,
  /** 캔버스 텍스처 키 (연출이 만들고 파괴할 때 지운다) */
  CANVAS_KEYS: { SCAR: 'setup_stroke_scar', LIGHT: 'setup_stroke_light' },
  /** 깊이: 표면 · 자국 · 부스러기 · 빛 · 불티/광선 (라벨·예시 패널 텍스트는 DEPTH.DEBUG) */
  DEPTH_SURFACE: -2,
  DEPTH_SCAR: -1,
  DEPTH_DEBRIS: 4.25,
  DEPTH_HOT: 4.3,
  DEPTH_SPARK: 4.4,
  DEPTH_RAYS: 4.5,
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

// --- 49라운드: 빛 터짐 ---

export interface BurstState {
  /** 흔들림·모음 진행 0~1 */
  charge: number;
  shaking: boolean;
  /** 섬광이 획을 따라 달린 비율 0~1 */
  trace: number;
  /** 광선 진행 0~1 */
  rays: number;
  /** 화면 하얀 정도 0~1 */
  white: number;
  /** 가장 하얀 순간을 지났다 (뒤에서 다음 장면 시작) */
  peaked: boolean;
  done: boolean;
}

/** 빛 터짐 주요 시각 (시작 기준 ms) */
export function burstTimes(C: StrokeFxConfig = STROKE_FX): {
  raysAt: number;
  whiteAt: number;
  peakAt: number;
  doneAt: number;
} {
  const B = C.BURST;
  const raysAt = B.CHARGE_MS + B.TRACE_MS * B.RAYS_AT;
  const whiteAt = raysAt + B.RAYS_MS - B.WHITE_IN_MS;
  const peakAt = whiteAt + B.WHITE_IN_MS;
  return { raysAt, whiteAt, peakAt, doneAt: peakAt + B.HOLD_MS + B.WHITE_OUT_MS };
}

export function burstAt(t: number, C: StrokeFxConfig = STROKE_FX): BurstState {
  const B = C.BURST;
  const T = burstTimes(C);
  let white = 0;
  if (t >= T.whiteAt && t < T.peakAt) white = (t - T.whiteAt) / B.WHITE_IN_MS;
  else if (t >= T.peakAt && t < T.peakAt + B.HOLD_MS) white = 1;
  else if (t >= T.peakAt + B.HOLD_MS) white = 1 - (t - T.peakAt - B.HOLD_MS) / B.WHITE_OUT_MS;
  return {
    charge: clamp01(t / B.CHARGE_MS),
    shaking: t < B.CHARGE_MS,
    trace: clamp01((t - B.CHARGE_MS) / B.TRACE_MS),
    rays: clamp01((t - T.raysAt) / B.RAYS_MS),
    white: clamp01(white),
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

export interface BurstRay {
  x: number;
  y: number;
  angle: number;
  len: number;
  width: number;
  /** 0~RAY_STAGGER: 이 비율만큼 늦게 뻗기 시작 */
  delay: number;
}

/**
 * 광선 배치: 모든 획의 전체 길이를 따라 고르게 count 점을 고르고, 각 점에서 획들의 무게중심 반대쪽(바깥)으로 ± 흔들림.
 * 무게중심과 거의 같은 점이면 그 자리의 법선 방향.
 */
export function burstRays(paths: number[][], rnd: () => number, C: StrokeFxConfig = STROKE_FX): BurstRay[] {
  const B = C.BURST;
  const valid = paths.filter((p) => p.length >= 4);
  if (valid.length === 0) return [];
  let sx = 0;
  let sy = 0;
  let n = 0;
  for (const p of valid)
    for (let i = 0; i < p.length; i += 2) {
      sx += p[i];
      sy += p[i + 1];
      n += 1;
    }
  const cx = sx / n;
  const cy = sy / n;
  const lens = valid.map(pathLength);
  const total = lens.reduce((a, b) => a + b, 0) || 1;
  const range = ([a, b]: [number, number]) => a + (b - a) * rnd();
  const rays: BurstRay[] = [];
  for (let k = 0; k < B.RAY_COUNT; k++) {
    let at = ((k + 0.5) / B.RAY_COUNT) * total;
    let pi = 0;
    while (pi < valid.length - 1 && at > lens[pi]) at -= lens[pi++];
    const f = lens[pi] > 0 ? at / lens[pi] : 0;
    const { x, y } = pathPointAt(valid[pi], f);
    const ahead = pathPointAt(valid[pi], Math.min(1, f + 0.02));
    let base = Math.atan2(y - cy, x - cx);
    if (Math.hypot(x - cx, y - cy) < 4) base = Math.atan2(ahead.y - y, ahead.x - x) + Math.PI / 2;
    rays.push({
      x,
      y,
      angle: base + (rnd() * 2 - 1) * B.RAY_JITTER,
      len: range(B.RAY_LEN),
      width: range(B.RAY_WIDTH),
      delay: rnd() * B.RAY_STAGGER,
    });
  }
  return rays;
}

function clamp01(v: number): number {
  return Math.max(0, Math.min(1, v));
}
