/**
 * 개성 선택 — 움직임 파트 "15초 회피 시험". Phaser 의존 없음: 수치·난이도 곡선·경기장 모양·갉아먹힘·측정 집계·등급.
 *
 * 48라운드 Q7 원문: "둥근 원 안에서 맞으면 피격되서 밀려나고 15초에 다가갈수록 피하기 굉장히 어렵게 투사체를 계속 쏘아대."
 * 49라운드 2절 원문: "멀리서 피하거나 … 개성을 정하는 것은 좋지 않은 것 같음. 차라리 초반에 감각 수치를 어느 정도 부여하는 등의
 * 기본 체급과 관련된 보상 … 지금보다 더 난이도가 있으면 … 서있는 공간도 매번 새롭고 공간 자체가 점점 갉아먹혀서 좁아지는 것"
 * → 결정: 버틴 시간·피격 수로 **등급 → 시작 감각 +0~3**. 무기는 3획만으로 결정(이 시험은 무기 결정에서 완전히 제외).
 *   경기장 모양 매번 무작위(원·타원·불규칙 다각형·여러 섬) + 시간에 따라 가장자리부터 갉아먹혀 좁아짐(갉아먹힌 곳 = 낙사).
 *
 * 모든 수치는 **시스템 임시값**(검수 대상). 작업 범위상 Constants.ts·data/*.json 을 고치지 않아 이 파일에 모았다 —
 * 다음 정리 때 `data/personality.json`(trial 블록)·`Constants.ts` 로 옮긴다.
 */

export type PatternKind = 'aimed' | 'fan' | 'cross' | 'ring';
export type FallMode = 'end' | 'return';
export type ArenaShape = 'circle' | 'ellipse' | 'polygon' | 'islands';
export const ARENA_SHAPES: ArenaShape[] = ['circle', 'ellipse', 'polygon', 'islands'];
export type TrialGrade = 'S' | 'A' | 'B' | 'C';

export const DODGE_TRIAL = {
  /** 시험 길이 · 시작 전 안내 · 끝난 뒤 결과(등급) 표시 */
  DURATION_MS: 15000,
  INTRO_MS: 2200,
  RESULT_MS: 2400,
  /** 운명 문구가 나올 때 경기장을 흐리게 */
  DIM_ALPHA: 0.15,
  DIM_MS: 400,
  /** 마지막 이 구간은 "매우 어렵게" (간격·속도·예고 최종값 + 동시 2패턴) */
  FINAL_MS: 3000,
  /** 게임 카메라와 같은 2배 확대 (48라운드 Q1) */
  ZOOM: 2,
  ARENA: {
    /** 기준 반지름 (타일, 월드 px = × 16). 모양마다 이 크기를 기준으로 넓이를 비슷하게 */
    RADIUS_TILES: 6.5,
    /** 바닥 격자 한 칸 (월드 px) — 갉아먹힘 단위 */
    CELL_PX: 4,
    /** 격자 범위 (경기장 중심에서 월드 px). 2배 화면(480×270 월드 px) 안에 들어가게 */
    HALF_W_PX: 176,
    HALF_H_PX: 108,
    /** 투사체가 나오는 바깥 고리 = 바닥 외곽(타원) + 이만큼 */
    SPAWN_PAD_TILES: 1.6,
    /** 투사체 고리 세로 반지름 상한 (화면 밖으로 너무 나가지 않게) */
    SPAWN_MAX_RY_PX: 132,
    /** 화면 위 안내문 자리를 위해 경기장을 아래로 (월드 px, 화면에서는 × ZOOM) */
    OFFSET_Y_PX: 14,
    /** 걸어서는 발 둘레 이만큼(px)까지 바닥이어야 한다 (가장자리에 바짝 붙지 않게, 밀려날 때만 떨어진다) */
    WALK_MARGIN_PX: 2,
    /** 모양 뽑기 가중치 */
    SHAPE_WEIGHTS: { circle: 1, ellipse: 1, polygon: 1.3, islands: 1.1 } as Record<ArenaShape, number>,
    /** 원·타원 가장자리 일렁임 (반지름 비율 진폭, 고조파 3·5·7) */
    WOBBLE: 0.045,
    /** 타원: 가로/세로 비 · 기울기(rad, ±) — 넓이는 원과 같게 */
    ELLIPSE: { RATIO: [1.3, 1.7] as [number, number], TILT: 0.45 },
    /** 불규칙 다각형: 꼭짓점 수 · 꼭짓점 반지름 비 · 각도 흔들림(간격 비) · 가로 늘림 */
    POLYGON: {
      VERTS: [6, 10] as [number, number],
      RADIUS: [0.7, 1.22] as [number, number],
      ANGLE_JITTER: 0.35,
      STRETCH_X: 1.15,
    },
    /**
     * 여러 섬: 가운데 섬(반지름 비) + 둘레 섬 COUNT 개(거리·반지름 비, 가로 늘림) + 가운데와 잇는 다리(폭 px).
     * 다리는 가장 얕아서 먼저 무너진다 → 섬이 갈라진다.
     */
    ISLANDS: {
      CENTER_R: 0.56,
      COUNT: [2, 4] as [number, number],
      DIST: [0.95, 1.2] as [number, number],
      R: [0.3, 0.42] as [number, number],
      STRETCH_X: 1.3,
      STRETCH_Y: 0.78,
      BRIDGE_PX: 8,
    },
  },
  /**
   * 갉아먹힘: 바닥 칸을 '가장자리에서의 깊이 + 잡음' 순으로 줄 세우고, 시작 START_MS 뒤부터 끝날 때까지
   * 무너진 비율 = (1 − END_FLOOR_FRAC) × 진행^POW. 무너지기 WARN_MS 전부터 균열(경고).
   */
  EROSION: {
    START_MS: 1500,
    END_FLOOR_FRAC: 0.3,
    POW: 1.1,
    /** 깊이(칸)에 더하는 잡음 폭 — 클수록 가장자리가 들쭉날쭉 갉아먹힌다 */
    NOISE_CELLS: 2.6,
    WARN_MS: 700,
    /** 한 프레임에 부스러기를 내는 칸 수 상한 · 칸당 조각 수 */
    CRUMBLE_CELLS_PER_FRAME: 10,
    CRUMBLE_CHIPS: 2,
  },
  PLAYER: {
    /** 판정 원 반지름 (월드 px) · 발 피벗과 판정 중심 사이 */
    HIT_RADIUS_PX: 5,
    FOOT_OFFSET_PX: 7,
    /** 피격 뒤 무적·깜빡임 */
    INVULN_MS: 600,
    BLINK_MS: 70,
    /** 밀려남: 투사체 진행 방향으로 거리·시간 (감속) */
    KNOCK_TILES: 2.6,
    KNOCK_MS: 190,
    /** 피격 순간 흰 칠 */
    FLASH_MS: 80,
    /** 대쉬 잔상 수·지속·알파 */
    GHOSTS: 3,
    GHOST_MS: 220,
    GHOST_ALPHA: 0.45,
    /** 발밑 그림자 (월드 px) */
    SHADOW: { W: 12, H: 5, ALPHA: 0.35 },
    /** 피격 흔들림 (메인 카메라) */
    SHAKE_MS: 110,
    SHAKE_INTENSITY: 0.006,
    /** 떨어짐: 작아지며 사라지는 시간 · 가라앉는 거리(px) */
    FALL_MS: 520,
    FALL_DROP_PX: 18,
  },
  /** 바닥 밖으로 나가면: 'end' = 즉시 판정 종료(기본) / 'return' = 중앙으로 복귀 + 이탈 횟수 패널티 */
  FALL_MODE: 'end' as FallMode,
  FALL_RETURN_INVULN_MS: 900,
  BULLET: {
    /** 판정 반지름 (월드 px): 적 탄(사수 탄 크기 4) · 보스 부채꼴 탄 */
    RADIUS_PX: 2.5,
    FAN_RADIUS_PX: 3,
    LIFE_MS: 4500,
    POOL: 260,
    /** 시트가 없을 때 원 지름(px)·색 (G13) */
    PLACEHOLDER_PX: 5,
    PLACEHOLDER_COLOR: 0xd8d9db,
    /** 시험이 끝날 때 남은 탄이 사라지는 시간 */
    END_FADE_MS: 260,
  },
  /**
   * 난이도 곡선 (49라운드: 48라운드보다 상향): 시작 → (끝 - FINAL_MS) 까지 k = (t / T)^CURVE_POW 로 보간,
   * 마지막 FINAL_MS 는 FINAL_* 고정. [시작, 끝] 쌍.
   */
  CURVE: {
    CURVE_POW: 1.3,
    INTERVAL_MS: [950, 380] as [number, number],
    SPEED_TILES: [7.5, 12] as [number, number],
    TELEGRAPH_MS: [460, 250] as [number, number],
    FINAL_INTERVAL_MS: 340,
    FINAL_SPEED_MULT: 1.25,
    FINAL_TELEGRAPH_MS: 200,
    /** 마지막 구간에 한 번에 쏘는 패턴 수 */
    FINAL_VOLLEYS: 2,
    /** 패턴이 풀리는 시각 (경과 ms) */
    UNLOCK_MS: { aimed: 0, fan: 2000, cross: 4500, ring: 7000 } as Record<PatternKind, number>,
    /** 패턴 뽑기 가중치 */
    WEIGHTS: { aimed: 3, fan: 2, cross: 2, ring: 1.5 } as Record<PatternKind, number>,
    FAN_COUNT: [4, 8] as [number, number],
    FAN_SPREAD_DEG: [40, 84] as [number, number],
    CROSS_STREAM: [3, 7] as [number, number],
    CROSS_GAP_MS: 90,
    /** 원형 확산: 한 바퀴 기준 발 수 (경기장 쪽 반원만 실제로 쏜다) */
    RING_COUNT: [14, 24] as [number, number],
    /** 원형 확산의 빈틈 수 (시작 → 끝) */
    RING_GAPS: [2, 1] as [number, number],
    /** 빈틈 하나의 폭 (발 수) */
    RING_GAP_WIDTH: 2,
    RING_SPEED_MULT: 0.75,
  },
  /** 측정 (거리는 타일 — 판정 원 가장자리 사이의 최근접 틈). 49라운드부터 등급·무기에 쓰지 않고 기록만 */
  MEASURE: {
    RELEVANT_TILES: 3,
    CLOSE_TILES: 0.6,
    FAR_TILES: 1.8,
    DASH_WINDOW_MS: 280,
    DASH_NEAR_TILES: 1.2,
  },
  /**
   * 등급 (49라운드 2절, 임시 기준): 점수 = 버틴 비율 × 100 − 피격 × HIT_PENALTY − (떨어짐 ? FALL_PENALTY : 0).
   * 위에서부터 minScore 이상인 첫 등급. bonus = 시작 감각 가산 (0~3).
   */
  GRADE: {
    HIT_PENALTY: 6,
    FALL_PENALTY: 15,
    TIERS: [
      { grade: 'S', minScore: 90, bonus: 3 },
      { grade: 'A', minScore: 70, bonus: 2 },
      { grade: 'B', minScore: 45, bonus: 1 },
      { grade: 'C', minScore: 0, bonus: 0 },
    ] as { grade: TrialGrade; minScore: number; bonus: number }[],
  },
  /** 자리표시 문구 (스토리·UI 파트 교체 대상) */
  TEXT: {
    INTRO: '발판 위에서 15초를 버텨라\nWASD 이동 · 스페이스 대쉬 — 발판은 가장자리부터 무너진다. 떨어지면 끝',
    RUN: '버텨라  남은 시간 {sec}초   피격 {hits}',
    /** 결과: 한 줄 + 등급·보상 */
    RESULT: '{line}\n\n등급 {grade}   ·   시작 감각 +{bonus}\n(버틴 시간 {sec}초 · 피격 {hits})',
    LINES: {
      fell: '발밑이 무너졌다.',
      S: '한 번도 흔들리지 않았다.',
      A: '끝까지 버텼다.',
      B: '간신히 버텼다.',
      C: '버텼지만, 상처투성이다.',
    } as Record<TrialGrade | 'fell', string>,
  },
};

export type TrialConfig = typeof DODGE_TRIAL;

/** 시험 동안 모은 원자료 */
export interface DodgeSample {
  durationMs: number;
  /** 실제 버틴 시간 (떨어지면 그때까지) */
  survivedMs: number;
  frames: number;
  movingFrames: number;
  dashes: number;
  /** 이동량 (월드 px, 밀려남 제외) */
  travelPx: number;
  hits: number;
  /** 바닥 밖으로 떨어진 횟수 (FALL_MODE 'end' 면 0 또는 1) */
  falls: number;
  /** 지나간(맞지 않은) 투사체 중 RELEVANT 안: 직전·중간·멀찍이 (기록만) */
  passes: { close: number; mid: number; far: number };
  /** 대쉬 직전 회피 (기록만) */
  dashDodges: number;
  /** 회피로 센 투사체 최근접 틈 합 (px) — 평균 표시용 */
  gapSumPx: number;
}

export function emptySample(durationMs: number = DODGE_TRIAL.DURATION_MS): DodgeSample {
  return {
    durationMs,
    survivedMs: 0,
    frames: 0,
    movingFrames: 0,
    dashes: 0,
    travelPx: 0,
    hits: 0,
    falls: 0,
    passes: { close: 0, mid: 0, far: 0 },
    dashDodges: 0,
    gapSumPx: 0,
  };
}

/** 지나간 투사체의 최근접 틈(px)을 분류. RELEVANT 밖이면 null */
export function classifyGap(gapPx: number, C: TrialConfig = DODGE_TRIAL, tile = 16): 'close' | 'mid' | 'far' | null {
  const M = C.MEASURE;
  const g = Math.max(0, gapPx);
  if (g > M.RELEVANT_TILES * tile) return null;
  if (g <= M.CLOSE_TILES * tile) return 'close';
  if (g >= M.FAR_TILES * tile) return 'far';
  return 'mid';
}

/** 대쉬 직전 회피인지: 최근접 시각 at, 마지막 대쉬 시작 dashAt */
export function isDashDodge(
  gapPx: number,
  at: number,
  dashAt: number,
  C: TrialConfig = DODGE_TRIAL,
  tile = 16,
): boolean {
  const M = C.MEASURE;
  return Math.max(0, gapPx) <= M.DASH_NEAR_TILES * tile && dashAt <= at && at - dashAt <= M.DASH_WINDOW_MS;
}

// --- 등급 ---

export interface TrialResult {
  grade: TrialGrade;
  /** 시작 감각 가산 0~3 */
  bonus: number;
  score: number;
  /** 버틴 비율 0~1 */
  survival: number;
  fell: boolean;
}

/** 버틴 시간·피격·떨어짐 → 등급과 시작 감각 가산 */
export function gradeTrial(s: DodgeSample, C: TrialConfig = DODGE_TRIAL): TrialResult {
  const G = C.GRADE;
  const survival = s.durationMs > 0 ? clamp01(s.survivedMs / s.durationMs) : 0;
  const fell = s.falls > 0;
  const score = Math.max(0, Math.round(survival * 100 - s.hits * G.HIT_PENALTY - (fell ? G.FALL_PENALTY : 0)));
  const tier = G.TIERS.find((t) => score >= t.minScore) ?? G.TIERS[G.TIERS.length - 1];
  return { grade: tier.grade, bonus: tier.bonus, score, survival, fell };
}

// --- 경기장 모양 · 갉아먹힘 ---

/** 경기장 바닥 격자. 좌표는 경기장 중심 기준 월드 px */
export interface ArenaMask {
  shape: ArenaShape;
  cell: number;
  cols: number;
  rows: number;
  /** 격자 왼쪽 위 모서리 (중심 기준 px) */
  x0: number;
  y0: number;
  /** 1 = 처음 바닥 */
  floor: Uint8Array;
  /** 가장자리(빈 곳)까지의 칸 거리 (바닥만, 가장자리 칸 = 1) */
  depth: Uint16Array;
  /** 무너지는 시각 (본 시험 시작 기준 ms). Infinity = 끝까지 남음 */
  erodeAt: Float64Array;
  /** 바닥 칸 index 를 erodeAt 오름차순으로 */
  order: Int32Array;
  /** 처음 바닥 칸 수 */
  cells: number;
  /** 바닥 외곽 (중심 기준 px) */
  bounds: { minX: number; maxX: number; minY: number; maxY: number };
}

/** 가중치로 모양 하나 (r ∈ [0,1)) */
export function pickShape(r: number, C: TrialConfig = DODGE_TRIAL): ArenaShape {
  const W = C.ARENA.SHAPE_WEIGHTS;
  const total = ARENA_SHAPES.reduce((s, k) => s + W[k], 0);
  let acc = r * total;
  for (const k of ARENA_SHAPES) {
    acc -= W[k];
    if (acc < 0) return k;
  }
  return ARENA_SHAPES[ARENA_SHAPES.length - 1];
}

/** 모양별 '바닥인가' 판정 함수 (중심 기준 px). rnd 로 모양 변수를 뽑는다 */
export function shapeTest(
  shape: ArenaShape,
  rnd: () => number,
  C: TrialConfig = DODGE_TRIAL,
): (x: number, y: number) => boolean {
  const A = C.ARENA;
  const R = A.RADIUS_TILES * 16;
  const range = ([a, b]: [number, number]) => a + (b - a) * rnd();
  const wobble = () => {
    const ph = [rnd(), rnd(), rnd()].map((v) => v * Math.PI * 2);
    const amp = [rnd(), rnd(), rnd()].map((v) => A.WOBBLE * (0.4 + 0.6 * v));
    return (th: number) =>
      1 + amp[0] * Math.sin(3 * th + ph[0]) + amp[1] * Math.sin(5 * th + ph[1]) + amp[2] * Math.sin(7 * th + ph[2]);
  };
  switch (shape) {
    case 'circle': {
      const w = wobble();
      return (x, y) => Math.hypot(x, y) <= R * w(Math.atan2(y, x));
    }
    case 'ellipse': {
      const ratio = range(A.ELLIPSE.RATIO);
      const rx = R * Math.sqrt(ratio);
      const ry = R / Math.sqrt(ratio);
      const tilt = (rnd() * 2 - 1) * A.ELLIPSE.TILT;
      const c = Math.cos(tilt);
      const s = Math.sin(tilt);
      const w = wobble();
      return (x, y) => {
        const u = x * c + y * s;
        const v = -x * s + y * c;
        return Math.hypot(u / rx, v / ry) <= w(Math.atan2(v, u));
      };
    }
    case 'polygon': {
      const P = A.POLYGON;
      const n = Math.round(range(P.VERTS));
      const step = (Math.PI * 2) / n;
      const start = rnd() * step;
      const verts = Array.from({ length: n }, (_, i) => {
        const a = start + i * step + (rnd() * 2 - 1) * P.ANGLE_JITTER * step;
        const r = R * range(P.RADIUS);
        return [Math.cos(a) * r * P.STRETCH_X, Math.sin(a) * r] as [number, number];
      });
      return (x, y) => pointInPolygon(x, y, verts);
    }
    case 'islands': {
      const I = A.ISLANDS;
      const isles: { x: number; y: number; r: number }[] = [{ x: 0, y: 0, r: R * I.CENTER_R }];
      const k = Math.round(range(I.COUNT));
      const step = (Math.PI * 2) / k;
      const start = rnd() * step;
      for (let i = 0; i < k; i++) {
        const a = start + i * step + (rnd() * 2 - 1) * 0.3 * step;
        const d = R * range(I.DIST);
        isles.push({ x: Math.cos(a) * d * I.STRETCH_X, y: Math.sin(a) * d * I.STRETCH_Y, r: R * range(I.R) });
      }
      const half = I.BRIDGE_PX / 2;
      return (x, y) => {
        for (const s of isles) if (Math.hypot(x - s.x, y - s.y) <= s.r) return true;
        for (let i = 1; i < isles.length; i++) if (segDist(x, y, 0, 0, isles[i].x, isles[i].y) <= half) return true;
        return false;
      };
    }
  }
}

/** 4방향 BFS: 빈 칸(격자 밖 포함)까지의 칸 거리. 가장자리 바닥 칸 = 1 */
export function floorDepth(floor: Uint8Array, cols: number, rows: number): Uint16Array {
  const depth = new Uint16Array(cols * rows);
  const queue: number[] = [];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const i = r * cols + c;
      if (!floor[i]) continue;
      const edge =
        c === 0 ||
        r === 0 ||
        c === cols - 1 ||
        r === rows - 1 ||
        !floor[i - 1] ||
        !floor[i + 1] ||
        !floor[i - cols] ||
        !floor[i + cols];
      if (edge) {
        depth[i] = 1;
        queue.push(i);
      }
    }
  }
  for (let q = 0; q < queue.length; q++) {
    const i = queue[q];
    const c = i % cols;
    const nb = [c > 0 ? i - 1 : -1, c < cols - 1 ? i + 1 : -1, i - cols, i + cols];
    for (const j of nb) {
      if (j < 0 || j >= floor.length || !floor[j] || depth[j]) continue;
      depth[j] = depth[i] + 1;
      queue.push(j);
    }
  }
  return depth;
}

/** 순위 비율 q (0~1) 의 칸이 무너지는 시각. 끝까지 남는 칸이면 Infinity */
export function erodeTimeForRank(q: number, C: TrialConfig = DODGE_TRIAL): number {
  const E = C.EROSION;
  const eat = 1 - E.END_FLOOR_FRAC;
  if (q > eat) return Infinity;
  return E.START_MS + (C.DURATION_MS - E.START_MS) * Math.pow(Math.max(0, q) / eat, 1 / E.POW);
}

/** 경과 ms 까지 무너진 바닥 비율 (0 ~ 1 − END_FLOOR_FRAC) */
export function erodedFraction(elapsedMs: number, C: TrialConfig = DODGE_TRIAL): number {
  const E = C.EROSION;
  const p = clamp01((elapsedMs - E.START_MS) / Math.max(1, C.DURATION_MS - E.START_MS));
  return (1 - E.END_FLOOR_FRAC) * Math.pow(p, E.POW);
}

/** 모양을 격자로 굽고 갉아먹힘 순서를 정한다. 중심 칸(시작 자리)은 항상 바닥 */
export function buildArena(shape: ArenaShape, rnd: () => number, C: TrialConfig = DODGE_TRIAL): ArenaMask {
  const A = C.ARENA;
  const cell = A.CELL_PX;
  const cols = 2 * Math.ceil(A.HALF_W_PX / cell);
  const rows = 2 * Math.ceil(A.HALF_H_PX / cell);
  const x0 = (-cols / 2) * cell;
  const y0 = (-rows / 2) * cell;
  const test = shapeTest(shape, rnd, C);
  const floor = new Uint8Array(cols * rows);
  const bounds = { minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity };
  let cells = 0;
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const x = x0 + (c + 0.5) * cell;
      const y = y0 + (r + 0.5) * cell;
      if (!test(x, y)) continue;
      floor[r * cols + c] = 1;
      cells += 1;
      bounds.minX = Math.min(bounds.minX, x0 + c * cell);
      bounds.maxX = Math.max(bounds.maxX, x0 + (c + 1) * cell);
      bounds.minY = Math.min(bounds.minY, y0 + r * cell);
      bounds.maxY = Math.max(bounds.maxY, y0 + (r + 1) * cell);
    }
  }
  const depth = floorDepth(floor, cols, rows);
  const idx: number[] = [];
  const key = new Float64Array(cols * rows);
  for (let i = 0; i < floor.length; i++) {
    if (!floor[i]) continue;
    key[i] = depth[i] + rnd() * C.EROSION.NOISE_CELLS;
    idx.push(i);
  }
  idx.sort((a, b) => key[a] - key[b]);
  const erodeAt = new Float64Array(cols * rows).fill(Infinity);
  idx.forEach((i, rank) => {
    erodeAt[i] = erodeTimeForRank((rank + 1) / idx.length, C);
  });
  return { shape, cell, cols, rows, x0, y0, floor, depth, erodeAt, order: Int32Array.from(idx), cells, bounds };
}

/** 중심 기준 px → 칸 index (격자 밖이면 -1) */
export function cellIndexAt(m: ArenaMask, x: number, y: number): number {
  const c = Math.floor((x - m.x0) / m.cell);
  const r = Math.floor((y - m.y0) / m.cell);
  if (c < 0 || r < 0 || c >= m.cols || r >= m.rows) return -1;
  return r * m.cols + c;
}

/** 경과 elapsedMs 에 그 자리가 아직 바닥인가 */
export function isFloorAt(m: ArenaMask, x: number, y: number, elapsedMs: number): boolean {
  const i = cellIndexAt(m, x, y);
  return i >= 0 && m.floor[i] === 1 && m.erodeAt[i] > elapsedMs;
}

function pointInPolygon(x: number, y: number, v: [number, number][]): boolean {
  let inside = false;
  for (let i = 0, j = v.length - 1; i < v.length; j = i++) {
    const [xi, yi] = v[i];
    const [xj, yj] = v[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

function segDist(px: number, py: number, ax: number, ay: number, bx: number, by: number): number {
  const dx = bx - ax;
  const dy = by - ay;
  const l2 = dx * dx + dy * dy;
  const t = l2 > 0 ? clamp01(((px - ax) * dx + (py - ay) * dy) / l2) : 0;
  return Math.hypot(px - (ax + dx * t), py - (ay + dy * t));
}

/** 경과 시각의 난이도 (발사 간격·속도·예고·패턴 목록·동시 패턴 수와 패턴별 규모) */
export interface TrialStep {
  final: boolean;
  intervalMs: number;
  speedTiles: number;
  telegraphMs: number;
  volleys: number;
  patterns: PatternKind[];
  fanCount: number;
  fanSpreadDeg: number;
  crossStream: number;
  ringCount: number;
  ringGaps: number;
}

export function trialStep(elapsedMs: number, C: TrialConfig = DODGE_TRIAL): TrialStep {
  const V = C.CURVE;
  const rampEnd = C.DURATION_MS - C.FINAL_MS;
  const final = elapsedMs >= rampEnd;
  const k = final ? 1 : Math.pow(clamp01(elapsedMs / rampEnd), V.CURVE_POW);
  const lerp = ([a, b]: [number, number]) => a + (b - a) * k;
  const patterns = (Object.keys(V.UNLOCK_MS) as PatternKind[]).filter((p) => elapsedMs >= V.UNLOCK_MS[p]);
  return {
    final,
    intervalMs: final ? V.FINAL_INTERVAL_MS : lerp(V.INTERVAL_MS),
    speedTiles: lerp(V.SPEED_TILES) * (final ? V.FINAL_SPEED_MULT : 1),
    telegraphMs: final ? V.FINAL_TELEGRAPH_MS : lerp(V.TELEGRAPH_MS),
    volleys: final ? V.FINAL_VOLLEYS : 1,
    patterns,
    fanCount: Math.round(lerp(V.FAN_COUNT)),
    fanSpreadDeg: lerp(V.FAN_SPREAD_DEG),
    crossStream: Math.round(lerp(V.CROSS_STREAM)),
    ringCount: Math.round(lerp(V.RING_COUNT)),
    ringGaps: Math.max(1, Math.round(lerp(V.RING_GAPS))),
  };
}

/** 가중치로 패턴 하나 (r ∈ [0,1)) */
export function pickPattern(patterns: PatternKind[], r: number, C: TrialConfig = DODGE_TRIAL): PatternKind {
  const W = C.CURVE.WEIGHTS;
  const total = patterns.reduce((sum, p) => sum + W[p], 0);
  let acc = r * total;
  for (const p of patterns) {
    acc -= W[p];
    if (acc < 0) return p;
  }
  return patterns[patterns.length - 1] ?? 'aimed';
}

/**
 * 원형 패턴의 빈틈: count 발 중 gaps 개 구간(각 gapWidth 발)을 비운다. start 는 첫 빈틈 위치 (0~count-1).
 * 반환: 발사할 인덱스 목록
 */
export function ringIndices(count: number, gaps: number, gapWidth: number, start: number): number[] {
  const skip = new Set<number>();
  for (let g = 0; g < gaps; g++) {
    const at = Math.floor(start + (g * count) / gaps);
    for (let w = 0; w < gapWidth; w++) skip.add((at + w) % count);
  }
  return Array.from({ length: count }, (_, i) => i).filter((i) => !skip.has(i));
}

function clamp01(v: number): number {
  return Math.max(0, Math.min(1, v));
}
