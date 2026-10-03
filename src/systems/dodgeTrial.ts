/**
 * 개성 선택 — 움직임 파트 "회피 시험" 수치·과제·등급 (Phaser 의존 없음).
 *
 * 51라운드 2절 원문: "13초부터 너무 괴랄해서 … 좀 더 회피 능력을 테스트하는 방향으로 15초라는 시간에 제한 받지 않고 재디자인"
 * → 결정: **짧은 과제 5개를 차례로** — ① 예고선 피하기 ② 조여오는 고리 틈 빠지기 ③ 유도탄 따돌리기(기둥으로 끊기)
 *   ④ 대쉬 무적으로 탄막 벽 통과 ⑤ 종합. 각 4~6초, 사이에 제목 카드 + 1초 정비. **읽으면 피할 수 있게**: 모든 위협은
 *   예고가 먼저, 정해진 박자(아래 cue 표)로만 나온다 — 화면을 덮는 난사 없음. 과제별 피격·떨어짐으로 점수 → 등급 → 시작 감각 +0~3.
 *   경기장은 과제마다 무작위 모양(과제에 맞는 모양만), 갉아먹힘은 ②·⑤ 에서만. 맞으면 밀려나고, 떨어지면 그 과제만 실패.
 * 49라운드 2절(유지): 무기는 3획만으로 결정 — 이 시험은 무기 결정과 무관, 보상은 시작 감각뿐.
 *
 * 모든 수치는 **시스템 임시값**(검수 대상). 작업 범위상 Constants.ts·data/*.json 을 고치지 않아 이 파일에 모았다 —
 * 다음 정리 때 `data/personality.json`(trial 블록)·`Constants.ts` 로 옮긴다.
 * 경기장 모양·갉아먹힘 = `dodgeTrialArena.ts`, 과제 박자·기하 = `dodgeTrialTasks.ts`, 화면 = `dodgeTrialRunner.ts`.
 */

export type ArenaShape = 'circle' | 'ellipse' | 'polygon' | 'islands';
export const ARENA_SHAPES: ArenaShape[] = ['circle', 'ellipse', 'polygon', 'islands'];
export type TrialGrade = 'S' | 'A' | 'B' | 'C';
export type TaskId = 'lines' | 'ring' | 'homing' | 'wall' | 'mix';
export const TASK_IDS: TaskId[] = ['lines', 'ring', 'homing', 'wall', 'mix'];

/** 갉아먹힘 (과제 시작 기준 ms): startMs 부터 endMs 까지, 끝에 남는 바닥 비율 endFloorFrac */
export interface ErosionSpec {
  startMs: number;
  endMs: number;
  endFloorFrac: number;
}

/** 예고선 신호: count 1 = 하나 · 2 = 서로 수직인 두 곳에서 · 3 = 한 곳에서 부채꼴 셋 */
export interface LineCue {
  at: number;
  kind: 'line';
  count: 1 | 2 | 3;
}
/** 고리: gapDeg 틈, closeMs 동안 조인다 (예고 RING.WARN_MS 뒤) */
export interface RingCue {
  at: number;
  kind: 'ring';
  gapDeg: number;
  closeMs: number;
}
export interface HomingCue {
  at: number;
  kind: 'homing';
}
export interface WallCue {
  at: number;
  kind: 'wall';
}
export type Cue = LineCue | RingCue | HomingCue | WallCue;

export interface TaskDef {
  /** 화면 이름 (자리표시 — 스토리·UI 파트 교체 대상) */
  name: string;
  /** 제목 카드 아래 한 줄 설명 */
  hint: string;
  /** 이 과제에서 뽑을 경기장 모양 */
  shapes: ArenaShape[];
  /** 갉아먹힘 (null = 없음) */
  erosion: ErosionSpec | null;
  /** 기둥 수 (유도탄을 끊는 장애물) */
  pillars: [number, number];
  /** 위협 박자 (과제 시작 기준 at ms = 예고 시작) */
  cues: Cue[];
}

export const DODGE_TRIAL = {
  /** 게임 카메라와 같은 2배 확대 (48라운드 Q1) */
  ZOOM: 2,
  /** 제목 카드(첫 과제는 조작 안내 포함으로 더 길게) · 정비(움직일 수 있고 위협 없음) */
  CARD_MS: 1500,
  FIRST_CARD_MS: 2600,
  PREP_MS: 1000,
  /** 과제 끝: 마지막 예고 뒤 남은 위협이 다 사라질 때까지 기다리는 최대 시간 · 과제 결과 한 줄을 보여 주는 시간 */
  SETTLE_MAX_MS: 1600,
  CLEAR_MS: 900,
  /** 전체 결과(과제별 한 줄 + 등급) 표시 → 운명 */
  RESULT_MS: 3600,
  /** 운명 문구가 나올 때 경기장을 흐리게 */
  DIM_ALPHA: 0.15,
  DIM_MS: 400,
  ARENA: {
    /** 기준 반지름 (타일, 월드 px = × 16). 모양마다 이 크기를 기준으로 넓이를 비슷하게 */
    RADIUS_TILES: 6.5,
    /** 바닥 격자 한 칸 (월드 px) — 갉아먹힘 단위 */
    CELL_PX: 4,
    /** 격자 범위 (경기장 중심에서 월드 px). 2배 화면(480×270 월드 px) 안에 들어가게 */
    HALF_W_PX: 176,
    HALF_H_PX: 108,
    /** 탄이 나오는 바깥 고리 = 바닥 외곽(타원) + 이만큼 */
    SPAWN_PAD_TILES: 1.6,
    /** 탄 고리 세로 반지름 상한 (화면 밖으로 너무 나가지 않게) */
    SPAWN_MAX_RY_PX: 132,
    /** 화면 위 안내문 자리를 위해 경기장을 아래로 (월드 px, 화면에서는 × ZOOM) */
    OFFSET_Y_PX: 14,
    /** 걸어서는 발 둘레 이만큼(px)까지 바닥이어야 한다 (가장자리에 바짝 붙지 않게, 밀려날 때만 떨어진다) */
    WALK_MARGIN_PX: 2,
    /** 원·타원 가장자리 일렁임 (반지름 비율 진폭, 고조파 3·5·7) */
    WOBBLE: 0.045,
    /** 타원: 가로/세로 비 · 기울기(rad, ±) — 넓이는 원과 같게 */
    ELLIPSE: { RATIO: [1.3, 1.7] as [number, number], TILT: 0.45 },
    /** 불규칙 다각형: 꼭짓점 수 · 꼭짓점 반지름 비 · 각도 흔들림(간격 비) · 가로 늘림 */
    POLYGON: {
      VERTS: [6, 10] as [number, number],
      RADIUS: [0.78, 1.22] as [number, number],
      ANGLE_JITTER: 0.35,
      STRETCH_X: 1.15,
    },
    /**
     * 여러 섬: 가운데 섬(반지름 비) + 둘레 섬 COUNT 개(거리·반지름 비, 가로 늘림) + 가운데와 잇는 다리(폭 px).
     * 다리는 가장 얕아서 먼저 무너진다 → 섬이 갈라진다.
     */
    ISLANDS: {
      CENTER_R: 0.62,
      COUNT: [2, 4] as [number, number],
      DIST: [0.95, 1.2] as [number, number],
      R: [0.32, 0.42] as [number, number],
      STRETCH_X: 1.3,
      STRETCH_Y: 0.78,
      BRIDGE_PX: 10,
    },
    /** 기둥 (③ 유도탄을 끊는 장애물): 반지름 px · 중심에서 거리 비(기준 반지름 대비) · 서로 최소 간격 px · 시작 자리와 최소 거리 px · 높이 px */
    PILLAR: {
      R_PX: [7, 10] as [number, number],
      DIST: [0.38, 0.78] as [number, number],
      MIN_GAP_PX: 26,
      CLEAR_CENTER_PX: 26,
      HEIGHT_PX: 16,
      TRIES: 60,
    },
  },
  /** 갉아먹힘 공통: 깊이 잡음 폭(칸) · 진행 지수 · 무너지기 전 균열 ms · 프레임당 부스러기 칸 수 · 칸당 조각 */
  EROSION: {
    POW: 1.1,
    NOISE_CELLS: 2.6,
    WARN_MS: 700,
    CRUMBLE_CELLS_PER_FRAME: 10,
    CRUMBLE_CHIPS: 2,
  },
  PLAYER: {
    /** 판정 원 반지름 (월드 px) · 발 피벗과 판정 중심 사이 · 기둥과 부딪히는 발 반지름 */
    HIT_RADIUS_PX: 5,
    FOOT_OFFSET_PX: 7,
    FOOT_RADIUS_PX: 4,
    /** 피격 뒤 무적·깜빡임 */
    INVULN_MS: 650,
    BLINK_MS: 70,
    /** 밀려남: 맞은 방향으로 거리·시간 (감속) */
    KNOCK_TILES: 2.4,
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
  BULLET: {
    /** 판정 반지름 (월드 px): 적 탄(사수 탄) · 보스 부채꼴 탄(고리·유도탄) */
    RADIUS_PX: 2.5,
    FAN_RADIUS_PX: 3,
    LIFE_MS: 4500,
    POOL: 220,
    /** 시트가 없을 때 원 지름(px)·색 (G13) */
    PLACEHOLDER_PX: 5,
    PLACEHOLDER_COLOR: 0xd8d9db,
    /** 과제가 끝날 때 남은 탄이 사라지는 시간 */
    END_FADE_MS: 260,
  },
  /** ① 예고선: 예고 시간(과제 처음 → 끝) · 탄 속도 · 한 선에 연달아 쏘는 수·간격 · 부채꼴 셋의 벌어짐 */
  LINES: {
    TELEGRAPH_MS: [680, 540] as [number, number],
    SPEED_TILES: 12,
    BURST: 2,
    BURST_GAP_MS: 70,
    FAN_DEG: 20,
  },
  /**
   * ② 고리: 예고(고리 윤곽 + 틈 강조) WARN_MS → closeMs 동안 반지름 R0 → 0. 중심 = 예고 시작 때 주인공 자리를 경기장
   * 중심 쪽으로 PULL 만큼 당긴 곳. 틈 방향은 바닥이 이어진 쪽에서 무작위. 구슬 간격 px · 구슬 반지름.
   */
  RING: {
    WARN_MS: 720,
    R0_PX: 92,
    PULL: 0.3,
    BEAD_SPACING_PX: 7,
    BEAD_R_PX: 2.5,
    /** 틈 방향 후보 간격(도) · 바닥 확인 거리(R0 비율) */
    DIR_STEP_DEG: 15,
    PROBE: [0.3, 0.6] as [number, number],
  },
  /** ③ 유도탄: 예고(원) · 속도 · 회전 한계(°/s) · 수명(끝나면 사그라짐) · 판정 */
  HOMING: {
    TELEGRAPH_MS: 600,
    SPEED_TILES: 4.4,
    TURN_DEG_PER_S: 115,
    LIFE_MS: 2200,
    /** 처음 이만큼은 곧게 (발사 방향 = 주인공 쪽) */
    STRAIGHT_MS: 220,
  },
  /**
   * ④ 탄막 벽: 예고(벽 자리 선 + 진행 방향 화살) WARN_MS → 속도로 경기장을 가로지른다. 탄 간격 px(판정 지름보다 좁아 걸어서
   * 빠질 틈이 없다 — 대쉬 무적으로만 통과). 벽이 주인공에게 DASH_HINT_PX 안으로 오면 벽 등뼈가 밝아진다(대쉬 박자).
   */
  WALL: {
    WARN_MS: 820,
    SPEED_TILES: 8.5,
    SPACING_PX: 8,
    PAD_PX: 12,
    DASH_HINT_PX: 56,
  },
  /** 과제 5개 (순서 = TASK_IDS). cue.at = 예고 시작 (과제 시작 기준 ms) */
  TASKS: {
    lines: {
      name: '예고선 읽기',
      hint: '선이 그어진 뒤 그 선을 따라 탄이 지나간다 — 선 밖으로',
      shapes: ['circle', 'ellipse', 'polygon', 'islands'],
      erosion: null,
      pillars: [0, 0],
      cues: [
        { at: 0, kind: 'line', count: 1 },
        { at: 750, kind: 'line', count: 1 },
        { at: 1450, kind: 'line', count: 1 },
        { at: 2200, kind: 'line', count: 2 },
        { at: 2950, kind: 'line', count: 3 },
        { at: 3650, kind: 'line', count: 2 },
      ],
    },
    ring: {
      name: '조여오는 고리',
      hint: '고리가 조여 온다 — 밝은 틈으로 빠져나가라. 발판은 가장자리부터 무너진다',
      shapes: ['circle', 'ellipse', 'polygon'],
      erosion: { startMs: 900, endMs: 5600, endFloorFrac: 0.72 },
      pillars: [0, 0],
      cues: [
        { at: 0, kind: 'ring', gapDeg: 80, closeMs: 1450 },
        { at: 1750, kind: 'ring', gapDeg: 62, closeMs: 1350 },
        { at: 3500, kind: 'ring', gapDeg: 50, closeMs: 1250 },
      ],
    },
    homing: {
      name: '유도탄 따돌리기',
      hint: '쫓아오는 탄은 기둥에 부딪히면 깨진다 — 기둥 뒤로 끌어들여라',
      shapes: ['circle', 'ellipse', 'polygon'],
      erosion: null,
      pillars: [3, 4],
      cues: [
        { at: 0, kind: 'homing' },
        { at: 1000, kind: 'homing' },
        { at: 2000, kind: 'homing' },
        { at: 2900, kind: 'homing' },
      ],
    },
    wall: {
      name: '탄막 벽 통과',
      hint: '빈틈 없는 벽 — 닿기 직전에 스페이스(대쉬)로 뚫고 지나가라. 대쉬 중엔 맞지 않는다',
      shapes: ['circle', 'ellipse', 'polygon'],
      erosion: null,
      pillars: [0, 0],
      cues: [
        { at: 0, kind: 'wall' },
        { at: 1400, kind: 'wall' },
        { at: 2800, kind: 'wall' },
      ],
    },
    mix: {
      name: '종합',
      hint: '지금까지의 전부 — 예고를 보고 박자에 맞춰',
      shapes: ['circle', 'ellipse', 'polygon'],
      erosion: { startMs: 1000, endMs: 5600, endFloorFrac: 0.76 },
      pillars: [0, 0],
      cues: [
        { at: 0, kind: 'line', count: 1 },
        { at: 700, kind: 'homing' },
        { at: 1400, kind: 'ring', gapDeg: 70, closeMs: 1300 },
        { at: 2700, kind: 'wall' },
        { at: 3500, kind: 'line', count: 2 },
      ],
    },
  } as Record<TaskId, TaskDef>,
  /**
   * 등급 (51라운드, 임시 기준): 과제 점수 = 100 − 피격 × HIT_PENALTY (떨어짐 = FELL_SCORE). 전체 = 과제 평균.
   * 위에서부터 minScore 이상인 첫 등급. bonus = 시작 감각 가산 (0~3).
   */
  GRADE: {
    HIT_PENALTY: 30,
    FELL_SCORE: 0,
    TIERS: [
      { grade: 'S', minScore: 90, bonus: 3 },
      { grade: 'A', minScore: 70, bonus: 2 },
      { grade: 'B', minScore: 45, bonus: 1 },
      { grade: 'C', minScore: 0, bonus: 0 },
    ] as { grade: TrialGrade; minScore: number; bonus: number }[],
  },
  /** 자리표시 문구 (스토리·UI 파트 교체 대상) */
  TEXT: {
    /** 첫 카드에만 붙는 조작 안내 */
    CONTROLS: 'WASD 이동 · 스페이스 대쉬(대쉬 중엔 맞지 않는다)\n맞으면 밀려난다 — 발판 밖으로 떨어지면 그 과제는 실패',
    CARD: '과제 {n} / {total}\n{name}',
    PREP: '과제 {n} / {total} · {name} — 준비',
    RUN: '과제 {n} / {total} · {name}   피격 {hits}',
    /** 과제 결과 한 줄: {mark} = 아래 MARK */
    TASK_LINE: '{n}. {name} — {mark}',
    MARK: { clean: '무피격', hits: '피격 {hits}', fell: '떨어짐 (실패)', skipped: '건너뜀' },
    RESULT: '{lines}\n\n{line}\n등급 {grade}   ·   시작 감각 +{bonus}',
    LINES: {
      S: '한 번도 흔들리지 않았다.',
      A: '거의 다 읽어 냈다.',
      B: '몇 번은 놓쳤다.',
      C: '상처투성이로 끝까지 섰다.',
    } as Record<TrialGrade, string>,
  },
};

export type TrialConfig = typeof DODGE_TRIAL;

/** 과제 하나의 결과 */
export interface TaskResult {
  id: TaskId;
  hits: number;
  fell: boolean;
  dashes: number;
  /** 디버그로 건너뜀 (점수는 무피격으로 친다) */
  skipped?: boolean;
}

export function emptyTaskResult(id: TaskId): TaskResult {
  return { id, hits: 0, fell: false, dashes: 0 };
}

export interface TrialResult {
  grade: TrialGrade;
  /** 시작 감각 가산 0~3 */
  bonus: number;
  /** 과제 평균 0~100 */
  score: number;
  tasks: (TaskResult & { score: number })[];
  /** 한 과제라도 떨어졌다 */
  fell: boolean;
}

export function taskScore(r: TaskResult, C: TrialConfig = DODGE_TRIAL): number {
  if (r.fell) return C.GRADE.FELL_SCORE;
  return Math.max(0, 100 - r.hits * C.GRADE.HIT_PENALTY);
}

/** 과제 결과 → 등급·시작 감각. 결과가 모자라면(중간 종료) 빠진 과제는 0점 */
export function gradeTrial(results: TaskResult[], C: TrialConfig = DODGE_TRIAL): TrialResult {
  const tasks = TASK_IDS.map((id) => {
    const r = results.find((x) => x.id === id);
    return r ? { ...r, score: taskScore(r, C) } : { ...emptyTaskResult(id), fell: true, score: 0 };
  });
  const score = Math.round(tasks.reduce((s, t) => s + t.score, 0) / tasks.length);
  const G = C.GRADE;
  const tier = G.TIERS.find((t) => score >= t.minScore) ?? G.TIERS[G.TIERS.length - 1];
  return { grade: tier.grade, bonus: tier.bonus, score, tasks, fell: tasks.some((t) => t.fell) };
}

/** 디버그 강제 등급용 과제 결과 묶음 (gradeTrial 로 그 등급이 나온다) */
export const GRADE_PRESETS: Record<TrialGrade | 'fell', Partial<TaskResult>[]> = {
  S: [{}, {}, {}, {}, {}],
  A: [{ hits: 1 }, { hits: 1 }, { hits: 1 }, {}, {}],
  B: [{ fell: true }, { hits: 1 }, { hits: 1 }, {}, { hits: 1 }],
  C: [{ fell: true }, { fell: true }, { hits: 2 }, { hits: 1 }, { hits: 2 }],
  fell: [{}, {}, { fell: true }, {}, {}],
};

export function presetResults(p: TrialGrade | 'fell'): TaskResult[] {
  return TASK_IDS.map((id, i) => ({ ...emptyTaskResult(id), ...GRADE_PRESETS[p][i] }));
}
