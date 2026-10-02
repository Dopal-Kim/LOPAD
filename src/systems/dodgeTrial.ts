/**
 * 개성 선택 — 움직임 파트 "15초 회피 시험" (48라운드 Q7). Phaser 의존 없음: 수치·난이도 곡선·측정 집계·평가.
 *
 * 도영 님 원문: "둥근 원 안에서 맞으면 피격되서 밀려나고 15초에 다가갈수록 피하기 굉장히 어렵게 투사체를 계속 쏘아대.
 * 거기서 맞으며 잘 버텨내거나 떨어지면 순수 근거리, 잘 피하고 살아남으면 희귀한 직업이거나 멀리서 때리거나 민첩한 직업."
 * "멀찍이서 피하면 원거리 무기에 비중을 오기 직전에 피하면 근거리 무기에 비중"
 *
 * 모든 수치는 **시스템 임시값**(48라운드 이후 검수 대상). 이번 작업 범위상 Constants.ts·data/*.json 을 고치지 않아
 * 이 파일에 모았다 — 다음 정리 때 `data/personality.json`(trial 블록)·`Constants.ts` 로 옮긴다.
 */
import type { Affinity } from '../data/types';

export type PatternKind = 'aimed' | 'fan' | 'cross' | 'ring';
export type FallMode = 'end' | 'return';

export const DODGE_TRIAL = {
  /** 시험 길이 · 시작 전 안내 · 끝난 뒤 결과 한 줄 표시 */
  DURATION_MS: 15000,
  INTRO_MS: 2200,
  RESULT_MS: 1900,
  /** 운명 문구가 나올 때 경기장을 흐리게 */
  DIM_ALPHA: 0.15,
  DIM_MS: 400,
  /** 마지막 이 구간은 "매우 어렵게" (간격·속도·예고 최종값 + 동시 2패턴) */
  FINAL_MS: 3000,
  /** 게임 카메라와 같은 2배 확대 (48라운드 Q1) */
  ZOOM: 2,
  ARENA: {
    /** 원 반지름 (타일, 월드 px = × 16) */
    RADIUS_TILES: 6.5,
    /** 투사체가 나오는 바깥 고리 = 원 반지름 + 이만큼 */
    SPAWN_PAD_TILES: 1.6,
    /** 화면 위 안내문 자리를 위해 원을 아래로 (월드 px, 화면에서는 × ZOOM) */
    OFFSET_Y_PX: 14,
    /** 걸어서는 원 가장자리에서 이만큼 안쪽까지만 (밀려날 때만 떨어진다) */
    WALK_MARGIN_PX: 1,
  },
  PLAYER: {
    /** 판정 원 반지름 (월드 px) · 발 피벗과 판정 중심 사이 */
    HIT_RADIUS_PX: 5,
    FOOT_OFFSET_PX: 7,
    /** 피격 뒤 무적·깜빡임 */
    INVULN_MS: 650,
    BLINK_MS: 70,
    /** 밀려남: 투사체 진행 방향으로 거리·시간 (감속) */
    KNOCK_TILES: 2.2,
    KNOCK_MS: 180,
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
    /** 떨어짐: 작아지며 사라지는 시간 */
    FALL_MS: 420,
  },
  /** 원 밖으로 밀려나면: 'end' = 즉시 판정 종료(임시 기본) / 'return' = 원 중앙으로 복귀 + 이탈 횟수 패널티 */
  FALL_MODE: 'end' as FallMode,
  FALL_RETURN_INVULN_MS: 900,
  BULLET: {
    /** 판정 반지름 (월드 px): 적 탄(사수 탄 크기 4) · 보스 부채꼴 탄 */
    RADIUS_PX: 2.5,
    FAN_RADIUS_PX: 3,
    LIFE_MS: 4500,
    POOL: 220,
    /** 시트가 없을 때 원 지름(px)·색 (G13) */
    PLACEHOLDER_PX: 5,
    PLACEHOLDER_COLOR: 0xd8d9db,
    /** 시험이 끝날 때 남은 탄이 사라지는 시간 */
    END_FADE_MS: 260,
  },
  /**
   * 난이도 곡선: 시작 → (끝 - FINAL_MS) 까지 k = (t / T)^CURVE_POW 로 보간, 마지막 FINAL_MS 는 FINAL_* 고정.
   * [시작, 끝] 쌍.
   */
  CURVE: {
    CURVE_POW: 1.4,
    INTERVAL_MS: [1150, 470] as [number, number],
    SPEED_TILES: [6.5, 10.5] as [number, number],
    TELEGRAPH_MS: [520, 300] as [number, number],
    FINAL_INTERVAL_MS: 420,
    FINAL_SPEED_MULT: 1.25,
    FINAL_TELEGRAPH_MS: 230,
    /** 마지막 구간에 한 번에 쏘는 패턴 수 */
    FINAL_VOLLEYS: 2,
    /** 패턴이 풀리는 시각 (경과 ms) */
    UNLOCK_MS: { aimed: 0, fan: 2500, cross: 5500, ring: 8500 } as Record<PatternKind, number>,
    /** 패턴 뽑기 가중치 */
    WEIGHTS: { aimed: 3, fan: 2, cross: 2, ring: 1.5 } as Record<PatternKind, number>,
    FAN_COUNT: [3, 7] as [number, number],
    FAN_SPREAD_DEG: [36, 80] as [number, number],
    CROSS_STREAM: [3, 6] as [number, number],
    CROSS_GAP_MS: 95,
    /** 원형 확산: 한 바퀴 기준 발 수 (원 안쪽 반원만 실제로 쏜다) */
    RING_COUNT: [12, 22] as [number, number],
    /** 원형 확산의 빈틈 수 (시작 → 끝) */
    RING_GAPS: [2, 1] as [number, number],
    /** 빈틈 하나의 폭 (발 수) */
    RING_GAP_WIDTH: 2,
    /** 원형 확산 속도 배율 (원 밖 한 점에서 사방으로 퍼지는 탄막 — 안쪽 반원만 쏜다) */
    RING_SPEED_MULT: 0.75,
  },
  /** 측정 (거리는 타일 — 판정 원 가장자리 사이의 최근접 틈) */
  MEASURE: {
    /** 이 안으로 지나간 투사체만 '회피'로 센다 */
    RELEVANT_TILES: 3,
    /** 이하 = 직전 회피(아슬아슬) */
    CLOSE_TILES: 0.6,
    /** 이상 = 멀찍이 피함 */
    FAR_TILES: 1.8,
    /** 최근접 순간 직전 이 시간 안에 대쉬를 시작했고 틈이 DASH_NEAR 이하면 '대쉬 직전 회피' */
    DASH_WINDOW_MS: 280,
    DASH_NEAR_TILES: 1.2,
    /** 버팀(endure) = (피격 − GRACE) / (SAT − GRACE): 처음 GRACE 번은 누구나 맞는 것으로 본다 */
    HIT_GRACE: 2,
    HIT_SAT: 9,
    /** 대쉬 직전 회피 포화 */
    DASH_DODGE_SAT: 4,
  },
  /**
   * 평가 (임시). 축 이름은 `DodgeAxes` 키. 무기별 가산 = Σ 계수 × 축 값 → chooseWeapon 의 거리에서 뺀다.
   * 희귀 직업은 현재 4무기에 없으므로 rare 점수·플래그만 기록하고 무기 결정에는 쓰지 않는다 (후속 인터뷰).
   */
  EVAL: {
    /** keyAttack(근접 성향) = BASE + SPREAD × (close - far) + ENDURE × endure, 0~1 로 자름 */
    KEY_ATTACK: { BASE: 0.5, SPREAD: 0.4, ENDURE: 0.3 },
    WEAPON_BIAS: {
      bow: { far: 0.5, clean: 0.25 },
      dagger: { close: 0.2, dashDodge: 0.3, clean: 0.25 },
      katana: { close: 0.35, dashDodge: 0.15 },
      greatsword: { endure: 0.5 },
    } as Record<string, Partial<Record<keyof DodgeAxes, number>>>,
    /** 무피격 판정: 피격 0·이탈 없음·끝까지 생존 = 1, 피격 1 = 0.5 */
    CLEAN_ONE_HIT: 0.5,
    /** endure = max(피격 비율, 이탈 시 FELL) */
    FELL_ENDURE: 1,
    /** rare 점수 = clean × survival × (0.5 + 0.5 × max(far, dashDodge)); 이 이상이면 flag */
    RARE_MIN: 0.75,
  },
  /** 자리표시 문구 (스토리 파트 교체 대상) */
  TEXT: {
    INTRO: '원 안에서 15초를 버텨라\nWASD 이동 · 스페이스 대쉬 — 밀려나 원 밖으로 떨어지면 끝',
    RUN: '버텨라  남은 시간 {sec}초   피격 {hits}',
    RESULT: {
      fell: '원 밖으로 밀려났다.',
      endure: '맞으면서도 버텼다.',
      clean: '한 번도 닿지 않았다.',
      far: '멀찍이서 비껴섰다.',
      close: '닿기 직전에 몸을 틀었다.',
      mixed: '끝까지 움직였다.',
    } as Record<DodgeResultKind, string>,
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
  /** 원 밖으로 밀려난 횟수 (FALL_MODE 'end' 면 0 또는 1) */
  falls: number;
  /** 지나간(맞지 않은) 투사체 중 RELEVANT 안: 직전·중간·멀찍이 */
  passes: { close: number; mid: number; far: number };
  /** 대쉬 직전 회피 */
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

/** 평가 축 (전부 0~1) */
export interface DodgeAxes {
  /** 멀찍이 피한 비율 */
  far: number;
  /** 직전에 피한 비율 */
  close: number;
  /** 대쉬 직전 회피 (포화) */
  dashDodge: number;
  /** 맞고 버팀·떨어짐 */
  endure: number;
  /** 무피격 생존 */
  clean: number;
  /** 버틴 시간 비율 */
  survival: number;
}

export type DodgeResultKind = 'fell' | 'endure' | 'clean' | 'far' | 'close' | 'mixed';

export interface DodgeEvaluation {
  axes: DodgeAxes;
  /** 기존 6축 중 리듬 3축 자리를 채운다: 이동 비율 · 근접 성향 · 대쉬 */
  keys: Pick<Affinity, 'keyMove' | 'keyAttack' | 'keyDash'>;
  /** 무기 id → 가산 (chooseWeapon 의 거리에서 뺀다) */
  bias: Record<string, number>;
  /** 희귀 직업 (무기 결정에는 미반영, 기록만) */
  rare: { score: number; flag: boolean };
  kind: DodgeResultKind;
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

export function dodgeAxes(s: DodgeSample, C: TrialConfig = DODGE_TRIAL): DodgeAxes {
  const E = C.EVAL;
  const n = s.passes.close + s.passes.mid + s.passes.far;
  const survival = s.durationMs > 0 ? clamp01(s.survivedMs / s.durationMs) : 0;
  const fell = s.falls > 0;
  const M = C.MEASURE;
  const hitRate = clamp01((s.hits - M.HIT_GRACE) / Math.max(1, M.HIT_SAT - M.HIT_GRACE));
  const clean = !fell && survival >= 1 ? (s.hits === 0 ? 1 : s.hits === 1 ? E.CLEAN_ONE_HIT : 0) : 0;
  return {
    far: n > 0 ? s.passes.far / n : 0,
    close: n > 0 ? s.passes.close / n : 0,
    dashDodge: clamp01(s.dashDodges / C.MEASURE.DASH_DODGE_SAT),
    endure: Math.max(hitRate, fell ? E.FELL_ENDURE : 0),
    clean,
    survival,
  };
}

/** 결과 한 줄 분류: 떨어짐 > 무피격 > 많이 맞음 > 멀리/직전 우세 > 섞임 */
export function resultKind(a: DodgeAxes, s: DodgeSample): DodgeResultKind {
  if (s.falls > 0) return 'fell';
  if (a.clean >= 1) return 'clean';
  if (a.endure >= 0.5) return 'endure';
  if (a.far > a.close && a.far >= 0.4) return 'far';
  if (a.close >= a.far && (a.close >= 0.4 || a.dashDodge >= 0.5)) return 'close';
  return 'mixed';
}

/**
 * 회피 시험 평가. dashSaturation 은 기존 리듬 포화(`personality.json rhythm.dashSaturation`)를 그대로 쓴다.
 */
export function evaluateDodge(s: DodgeSample, dashSaturation: number, C: TrialConfig = DODGE_TRIAL): DodgeEvaluation {
  const a = dodgeAxes(s, C);
  const K = C.EVAL.KEY_ATTACK;
  const keys = {
    keyMove: s.frames > 0 ? clamp01(s.movingFrames / s.frames) : 0,
    keyAttack: clamp01(K.BASE + K.SPREAD * (a.close - a.far) + K.ENDURE * a.endure),
    keyDash: clamp01(s.dashes / Math.max(1, dashSaturation)),
  };
  const bias: Record<string, number> = {};
  for (const [id, coef] of Object.entries(C.EVAL.WEAPON_BIAS)) {
    let b = 0;
    for (const [axis, w] of Object.entries(coef) as [keyof DodgeAxes, number][]) b += w * a[axis];
    bias[id] = b;
  }
  const rareScore = a.clean * a.survival * (0.5 + 0.5 * Math.max(a.far, a.dashDodge));
  return {
    axes: a,
    keys,
    bias,
    rare: { score: rareScore, flag: rareScore >= C.EVAL.RARE_MIN },
    kind: resultKind(a, s),
  };
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
