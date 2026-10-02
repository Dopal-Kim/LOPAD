import { describe, expect, it } from 'vitest';
import {
  ARENA_SHAPES,
  DODGE_TRIAL,
  buildArena,
  cellIndexAt,
  classifyGap,
  emptySample,
  erodeTimeForRank,
  erodedFraction,
  gradeTrial,
  isDashDodge,
  isFloorAt,
  pickShape,
  pickPattern,
  ringIndices,
  trialStep,
  type DodgeSample,
} from './dodgeTrial';

const sample = (over: Partial<DodgeSample>): DodgeSample => ({
  ...emptySample(),
  survivedMs: DODGE_TRIAL.DURATION_MS,
  frames: 900,
  movingFrames: 600,
  ...over,
});

describe('dodgeTrial 측정', () => {
  it('틈 분류: 직전 · 중간 · 멀찍이 · 무관', () => {
    expect(classifyGap(-3)).toBe('close');
    expect(classifyGap(DODGE_TRIAL.MEASURE.CLOSE_TILES * 16)).toBe('close');
    expect(classifyGap(16)).toBe('mid');
    expect(classifyGap(DODGE_TRIAL.MEASURE.FAR_TILES * 16)).toBe('far');
    expect(classifyGap(DODGE_TRIAL.MEASURE.RELEVANT_TILES * 16 + 1)).toBeNull();
  });
  it('대쉬 직전 회피: 최근접 직전 창 안 + 가까운 틈만', () => {
    expect(isDashDodge(4, 1000, 800)).toBe(true);
    expect(isDashDodge(4, 1000, 1000 - DODGE_TRIAL.MEASURE.DASH_WINDOW_MS - 1)).toBe(false);
    expect(isDashDodge(4, 1000, 1100)).toBe(false);
    expect(isDashDodge(DODGE_TRIAL.MEASURE.DASH_NEAR_TILES * 16 + 1, 1000, 900)).toBe(false);
  });
});

/** 결정적 의사 난수 (mulberry32) */
const seeded = (seed: number) => () => {
  seed |= 0;
  seed = (seed + 0x6d2b79f5) | 0;
  let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
  t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};

describe('dodgeTrial 등급 (49라운드 2절)', () => {
  it('무피격 끝까지 = S(+3), 피격이 늘수록 내려간다', () => {
    expect(gradeTrial(sample({ hits: 0 }))).toMatchObject({ grade: 'S', bonus: 3, score: 100, fell: false });
    expect(gradeTrial(sample({ hits: 1 })).grade).toBe('S');
    expect(gradeTrial(sample({ hits: 3 }))).toMatchObject({ grade: 'A', bonus: 2 });
    expect(gradeTrial(sample({ hits: 7 }))).toMatchObject({ grade: 'B', bonus: 1 });
    expect(gradeTrial(sample({ hits: 12 }))).toMatchObject({ grade: 'C', bonus: 0 });
  });
  it('떨어지면 그때까지의 시간 + 감점', () => {
    const early = gradeTrial(sample({ falls: 1, survivedMs: 5000, hits: 1 }));
    expect(early.fell).toBe(true);
    expect(early.survival).toBeCloseTo(1 / 3);
    expect(early.grade).toBe('C');
    const late = gradeTrial(sample({ falls: 1, survivedMs: 14000 }));
    expect(late.score).toBe(Math.round((14000 / 15000) * 100 - DODGE_TRIAL.GRADE.FALL_PENALTY));
    expect(late.grade).toBe('A');
  });
  it('보상은 0~3, 등급 표는 점수 내림차순', () => {
    const T = DODGE_TRIAL.GRADE.TIERS;
    for (let i = 1; i < T.length; i++) expect(T[i].minScore).toBeLessThan(T[i - 1].minScore);
    for (let h = 0; h < 30; h++) {
      const b = gradeTrial(sample({ hits: h })).bonus;
      expect(b).toBeGreaterThanOrEqual(0);
      expect(b).toBeLessThanOrEqual(3);
    }
  });
});

describe('dodgeTrial 경기장 모양 · 갉아먹힘', () => {
  it('모양 뽑기: 4종 모두 나온다', () => {
    const seen = new Set(Array.from({ length: 40 }, (_, i) => pickShape(i / 40)));
    expect([...seen].sort()).toEqual([...ARENA_SHAPES].sort());
  });
  it('모든 모양: 시작 자리(중심·발)는 바닥이고 끝까지 남는다, 격자 안에 들어간다', () => {
    for (const shape of ARENA_SHAPES) {
      for (let seed = 1; seed <= 12; seed++) {
        const m = buildArena(shape, seeded(seed * 31 + shape.length));
        expect(m.cells).toBeGreaterThan(200);
        const foot = DODGE_TRIAL.PLAYER.FOOT_OFFSET_PX;
        expect(isFloorAt(m, 0, foot, 0)).toBe(true);
        expect(isFloorAt(m, 0, foot, DODGE_TRIAL.DURATION_MS)).toBe(true);
        expect(m.bounds.maxY).toBeLessThanOrEqual(DODGE_TRIAL.ARENA.HALF_H_PX + m.cell);
        expect(m.bounds.maxX).toBeLessThanOrEqual(DODGE_TRIAL.ARENA.HALF_W_PX + m.cell);
      }
    }
  });
  it('같은 시드 = 같은 경기장, 다른 시드 = 다른 경기장', () => {
    const a = buildArena('polygon', seeded(7));
    const b = buildArena('polygon', seeded(7));
    const c = buildArena('polygon', seeded(8));
    expect(Array.from(a.floor)).toEqual(Array.from(b.floor));
    expect(Array.from(a.floor)).not.toEqual(Array.from(c.floor));
  });
  it('가장자리부터: 먼저 무너지는 칸은 얕고, 나중 칸은 깊다', () => {
    const m = buildArena('circle', seeded(3));
    const n = m.order.length;
    const avg = (from: number, to: number) => {
      let s = 0;
      for (let k = from; k < to; k++) s += m.depth[m.order[k]];
      return s / (to - from);
    };
    expect(avg(0, Math.floor(n * 0.1))).toBeLessThan(avg(Math.floor(n * 0.6), Math.floor(n * 0.7)));
    for (let k = 1; k < n; k++) expect(m.erodeAt[m.order[k]]).toBeGreaterThanOrEqual(m.erodeAt[m.order[k - 1]]);
  });
  it('시간에 따라 좁아진다: 시작 전 0, 끝에 1 − END_FLOOR_FRAC 만큼', () => {
    const E = DODGE_TRIAL.EROSION;
    expect(erodedFraction(0)).toBe(0);
    expect(erodedFraction(E.START_MS)).toBe(0);
    expect(erodedFraction(8000)).toBeGreaterThan(0);
    expect(erodedFraction(DODGE_TRIAL.DURATION_MS)).toBeCloseTo(1 - E.END_FLOOR_FRAC);
    const m = buildArena('ellipse', seeded(5));
    const alive = (t: number) => Array.from(m.order).filter((i) => m.erodeAt[i] > t).length / m.cells;
    expect(alive(1000)).toBe(1);
    expect(alive(8000)).toBeLessThan(alive(4000));
    expect(alive(DODGE_TRIAL.DURATION_MS)).toBeCloseTo(E.END_FLOOR_FRAC, 1);
    expect(erodeTimeForRank(0.99)).toBe(Infinity);
  });
  it('여러 섬: 다리가 먼저 무너져 섬이 갈라진다 (다리 칸은 깊이 1~2)', () => {
    const m = buildArena('islands', seeded(11));
    const maxDepth = Math.max(...Array.from(m.depth));
    expect(maxDepth).toBeGreaterThan(6);
    // 중심에서 오른쪽/왼쪽 어딘가에 깊이 1~2 의 좁은 다리 칸이 있다
    const shallow = Array.from(m.order).filter((i) => m.depth[i] <= 2).length;
    expect(shallow).toBeGreaterThan(0);
  });
  it('칸 좌표: 격자 밖은 -1', () => {
    const m = buildArena('circle', seeded(1));
    expect(cellIndexAt(m, 0, 0)).toBeGreaterThanOrEqual(0);
    expect(cellIndexAt(m, 9999, 0)).toBe(-1);
    expect(isFloorAt(m, 9999, 0, 0)).toBe(false);
  });
});

describe('dodgeTrial 난이도', () => {
  it('49라운드: 48라운드보다 어렵다 (간격 짧고 속도 빠름)', () => {
    const V = DODGE_TRIAL.CURVE;
    expect(V.INTERVAL_MS[0]).toBeLessThan(1150);
    expect(V.INTERVAL_MS[1]).toBeLessThan(470);
    expect(V.SPEED_TILES[1]).toBeGreaterThan(10.5);
    expect(V.FINAL_INTERVAL_MS).toBeLessThan(420);
  });
  it('시간이 갈수록 간격·예고는 짧아지고 속도는 빨라진다', () => {
    const a = trialStep(0);
    const b = trialStep(8000);
    const c = trialStep(DODGE_TRIAL.DURATION_MS - DODGE_TRIAL.FINAL_MS - 1);
    expect(b.intervalMs).toBeLessThan(a.intervalMs);
    expect(c.intervalMs).toBeLessThan(b.intervalMs);
    expect(c.speedTiles).toBeGreaterThan(a.speedTiles);
    expect(c.telegraphMs).toBeLessThan(a.telegraphMs);
    expect(a.patterns).toEqual(['aimed']);
    expect(c.patterns).toEqual(['aimed', 'fan', 'cross', 'ring']);
  });
  it('마지막 구간은 최종값 + 동시 2패턴', () => {
    const f = trialStep(DODGE_TRIAL.DURATION_MS - 1000);
    expect(f.final).toBe(true);
    expect(f.intervalMs).toBe(DODGE_TRIAL.CURVE.FINAL_INTERVAL_MS);
    expect(f.volleys).toBe(2);
    expect(f.speedTiles).toBeGreaterThan(trialStep(DODGE_TRIAL.DURATION_MS - DODGE_TRIAL.FINAL_MS - 1).speedTiles);
  });
  it('패턴 뽑기: 가중치 경계', () => {
    expect(pickPattern(['aimed'], 0.99)).toBe('aimed');
    expect(pickPattern(['aimed', 'fan'], 0)).toBe('aimed');
    expect(pickPattern(['aimed', 'fan'], 0.99)).toBe('fan');
  });
  it('원형 빈틈: count - gaps × 폭 발', () => {
    const idx = ringIndices(12, 2, 2, 0);
    expect(idx).toHaveLength(8);
    expect(idx).not.toContain(0);
    expect(idx).not.toContain(1);
    expect(idx).not.toContain(6);
    expect(idx).not.toContain(7);
  });
});
