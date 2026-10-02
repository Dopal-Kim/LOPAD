import { describe, expect, it } from 'vitest';
import {
  DODGE_TRIAL,
  classifyGap,
  dodgeAxes,
  emptySample,
  evaluateDodge,
  isDashDodge,
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

describe('dodgeTrial 평가', () => {
  it('무피격 끝까지 생존 = clean 1, 떨어지면 endure 1·clean 0', () => {
    expect(dodgeAxes(sample({ passes: { close: 0, mid: 2, far: 8 } })).clean).toBe(1);
    const fell = dodgeAxes(sample({ falls: 1, survivedMs: 6000 }));
    expect(fell.endure).toBe(1);
    expect(fell.clean).toBe(0);
    expect(fell.survival).toBeCloseTo(0.4);
  });
  it('멀찍이 피함 → 활 가산 최대, 근접 성향 낮음', () => {
    const e = evaluateDodge(sample({ passes: { close: 1, mid: 2, far: 9 }, hits: 1 }), 8);
    const top = Object.entries(e.bias).sort((a, b) => b[1] - a[1])[0][0];
    expect(top).toBe('bow');
    expect(e.keys.keyAttack).toBeLessThan(0.35);
    expect(e.kind).toBe('far');
  });
  it('직전 회피 + 대쉬 → 단검·칼 가산이 활보다 크고 근접 성향 높음', () => {
    const e = evaluateDodge(sample({ passes: { close: 9, mid: 3, far: 0 }, dashDodges: 4, dashes: 8, hits: 2 }), 8);
    expect(e.bias.dagger).toBeGreaterThan(e.bias.bow);
    expect(e.bias.katana).toBeGreaterThan(e.bias.bow);
    expect(e.keys.keyAttack).toBeGreaterThanOrEqual(0.75);
    expect(e.keys.keyDash).toBe(1);
    expect(e.kind).toBe('close');
  });
  it('많이 맞음·떨어짐 → 대검 가산 최대', () => {
    for (const s of [
      sample({ hits: 7, passes: { close: 3, mid: 3, far: 1 } }),
      sample({ falls: 1, survivedMs: 4000 }),
    ]) {
      const e = evaluateDodge(s, 8);
      const top = Object.entries(e.bias).sort((a, b) => b[1] - a[1])[0][0];
      expect(top).toBe('greatsword');
    }
  });
  it('희귀 직업: 무피격 + 멀찍이/대쉬 회피면 flag (무기 결정과 별개)', () => {
    expect(evaluateDodge(sample({ passes: { close: 0, mid: 1, far: 10 } }), 8).rare.flag).toBe(true);
    expect(evaluateDodge(sample({ hits: 2, passes: { close: 0, mid: 1, far: 10 } }), 8).rare.flag).toBe(false);
  });
  it('결과 한 줄 분류', () => {
    expect(evaluateDodge(sample({ falls: 1 }), 8).kind).toBe('fell');
    expect(evaluateDodge(sample({ passes: { close: 5, mid: 5, far: 5 } }), 8).kind).toBe('clean');
    expect(evaluateDodge(sample({ hits: 7 }), 8).kind).toBe('endure');
    expect(evaluateDodge(sample({ hits: 2, passes: { close: 3, mid: 6, far: 3 } }), 8).kind).toBe('mixed');
  });
});

describe('dodgeTrial 난이도', () => {
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
  it('마지막 3초는 최종값 + 동시 2패턴', () => {
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
