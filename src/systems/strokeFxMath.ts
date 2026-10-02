/**
 * 획 찢기 연출 (48라운드 Q8) 의 순수 계산: 수치·속도→폭/세기·식는 곡선·찢긴 가장자리 점. Phaser 의존 없음.
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
  /** 속도(px/s) → 틈 폭(px)·빛 세기 */
  WIDTH: { MIN_PX: 2, MAX_PX: 9, SPEED_REF: 1800 },
  INTENSITY: { MIN: 0.55, MAX: 1 },
  /** 속도 계산의 최소 시간 간격 (같은 ms 에 몰린 포인터 이벤트가 속도를 튀게 하지 않도록) */
  MIN_DT_MS: 8,
  /** 속도 평활 (새 값 비중) */
  SPEED_SMOOTH: 0.45,
  /** 찢긴 선: 이 간격(px)마다 꺾고, 꺾임 폭 = 틈 폭 × AMP */
  JITTER: { STEP_PX: 7, AMP: 0.22 },
  /** 백열 → 식음: 경과/COOL_MS 의 (1-x)^POW. 획을 떼면 FLARE 동안 BOOST 만큼 더 밝게 한 번 */
  COOL_MS: 2600,
  COOL_POW: 1.5,
  FLARE_MS: 300,
  FLARE_BOOST: 0.7,
  /** 뜨거운 조각 최대 개수 (넘으면 오래된 것부터 버린다) */
  HOT_MAX: 480,
  /**
   * 빛 레이어 (ADD): 폭 배율·색·알파·식는 지수. 색 'x0'/'x1' = 팔레트 fx.core, 숫자 = 현재 층 램프 인덱스(9~11 = 강조 25~27).
   * 바깥 → 안쪽 순서. 안쪽일수록 빨리 식는다 (백열 → 층 강조색 → 꺼짐)
   */
  HOT_LAYERS: [
    { width: 3.6, color: 9, alpha: 0.2, pow: 0.6 },
    { width: 2.0, color: 10, alpha: 0.38, pow: 1 },
    { width: 1.0, color: 'x1', alpha: 0.85, pow: 1.6 },
    { width: 0.35, color: 'x0', alpha: 1, pow: 2.2 },
  ] as { width: number; color: number | 'x0' | 'x1'; alpha: number; pow: number }[],
  /** 남는 자국 (RenderTexture, 필기처럼): 틈 · 들뜬 가장자리 · 식은 잔불 */
  SCAR: {
    GAP_COLOR: 0x000000,
    GAP_ALPHA: 0.92,
    GAP_EXTRA_PX: 1.5,
    LIP_GRAY: 6,
    LIP_ALPHA: 0.5,
    LIP_HOT_RAMP: 3,
    LIP_HOT_ALPHA: 0.4,
    LIP_OFFSET_PX: 0.8,
    EMBER_RAMP: 4,
    EMBER_ALPHA: 0.6,
    EMBER_WIDTH: 0.45,
    CORE_RAMP: 7,
    CORE_ALPHA: 0.35,
    /** 들뜬 조각(작은 사각형)이 가장자리에 붙을 확률 (꺾임 점마다) */
    CHIP_CHANCE: 0.18,
    CHIP_PX: 2,
  },
  /** 불티 (ADD 파티클): 이동 px 당 개수, 한 번에 최대, 진행 반대쪽 ±SPREAD°, 속도·수명·중력 */
  SPARKS: {
    KEY: 'setup_scratch_spark',
    SIZE_PX: 2,
    PER_PX: 0.12,
    MAX_PER_MOVE: 9,
    SPREAD_DEG: 65,
    SPEED: [70, 300] as [number, number],
    LIFE_MS: [200, 560] as [number, number],
    GRAVITY: 620,
    /** 색: 팔레트 fx.core 2 + 층 강조 27·26 */
    RAMP_TINTS: [11, 10],
  },
  /** 펜 끝 빛 번짐 (방사 그라데이션, ADD) */
  TIP: { KEY: 'setup_scratch_tip', RADIUS_PX: 22, ALPHA: 0.55, SCALE_MIN: 0.6, SCALE_MAX: 1.3 },
  /** 미세 흔들림: 이 속도 이상일 때, 간격을 두고 */
  SHAKE: { MIN_SPEED: 650, MS: 70, INTENSITY: [0.0008, 0.0026] as [number, number], THROTTLE_MS: 90 },
  /** 마지막 획을 뗀 뒤 자국·섬광을 보여 주는 시간 → 그 뒤 FADE_OUT_MS 동안 사라짐 */
  HOLD_AFTER_LAST_MS: 900,
  /** 획 단계를 떠날 때 자국이 사라지는 시간 */
  FADE_OUT_MS: 650,
  /** 깊이: 표면 · 자국 · 빛 (라벨·예시 패널 텍스트는 DEPTH.DEBUG) */
  DEPTH_SURFACE: -2,
  DEPTH_SCAR: -1,
  DEPTH_HOT: 4.3,
  DEPTH_SPARK: 4.4,
};

export type StrokeFxConfig = typeof STROKE_FX;

/** 속도 비율 0~1 */
export function speedRatio(speedPxPerSec: number, C: StrokeFxConfig = STROKE_FX): number {
  return clamp01(speedPxPerSec / C.WIDTH.SPEED_REF);
}

/** 빠를수록 넓게 찢기고 밝다 */
export function gapWidth(speedPxPerSec: number, C: StrokeFxConfig = STROKE_FX): number {
  const r = speedRatio(speedPxPerSec, C);
  return C.WIDTH.MIN_PX + (C.WIDTH.MAX_PX - C.WIDTH.MIN_PX) * r;
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

/**
 * (x0,y0) → (x1,y1) 를 STEP 간격으로 나누고 안쪽 점을 수직으로 ±AMP×폭 흔든 찢긴 선. 시작점은 그대로(앞 조각과 이어짐),
 * 끝점도 그대로(다음 조각 시작). 반환: [x0,y0, ..., x1,y1]
 */
export function jaggedPoints(
  x0: number,
  y0: number,
  x1: number,
  y1: number,
  width: number,
  rnd: () => number,
  C: StrokeFxConfig = STROKE_FX,
): number[] {
  const dx = x1 - x0;
  const dy = y1 - y0;
  const len = Math.hypot(dx, dy);
  const n = Math.max(1, Math.ceil(len / C.JITTER.STEP_PX));
  const nx = len > 0 ? -dy / len : 0;
  const ny = len > 0 ? dx / len : 0;
  const out = [x0, y0];
  for (let i = 1; i < n; i++) {
    const t = i / n;
    const j = (rnd() * 2 - 1) * C.JITTER.AMP * width;
    out.push(x0 + dx * t + nx * j, y0 + dy * t + ny * j);
  }
  out.push(x1, y1);
  return out;
}

/** 점 목록을 수직으로 offset 만큼 민 선 (가장자리 들뜸). 각 점의 법선은 앞뒤 점 방향 */
export function offsetPoints(pts: number[], offset: number): number[] {
  const n = pts.length / 2;
  const out: number[] = [];
  for (let i = 0; i < n; i++) {
    const a = Math.max(0, i - 1);
    const b = Math.min(n - 1, i + 1);
    const dx = pts[b * 2] - pts[a * 2];
    const dy = pts[b * 2 + 1] - pts[a * 2 + 1];
    const len = Math.hypot(dx, dy) || 1;
    out.push(pts[i * 2] - (dy / len) * offset, pts[i * 2 + 1] + (dx / len) * offset);
  }
  return out;
}

function clamp01(v: number): number {
  return Math.max(0, Math.min(1, v));
}
