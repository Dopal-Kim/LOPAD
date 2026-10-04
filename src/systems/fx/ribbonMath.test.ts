import { describe, expect, it } from 'vitest';
import { FEEL } from '../core/Constants';
import { pruneRibbon, pushRibbonSample, ribbonAgeFrame, sampleTimes, type RibbonSample } from './ribbonMath';

describe('ribbonMath: 칼끝 잔상 리본 (55라운드 Q7)', () => {
  it('나이 프레임: 100ms 안에 4단계로 식는다', () => {
    const L = FEEL.RIBBON.LIFE_MS;
    expect(ribbonAgeFrame(0, L, 4)).toBe(0);
    expect(ribbonAgeFrame(30, L, 4)).toBe(1);
    expect(ribbonAgeFrame(60, L, 4)).toBe(2);
    expect(ribbonAgeFrame(80, L, 4)).toBe(3);
    expect(ribbonAgeFrame(500, L, 4)).toBe(3);
    expect(ribbonAgeFrame(10, L, 1)).toBe(0);
  });

  it('찍을 시각: 프레임 사이도 step 간격으로 (끝은 늘 to)', () => {
    expect(sampleTimes(null, 100, 4)).toEqual([100]);
    expect(sampleTimes(100, 110, 4)).toEqual([104, 108, 110]);
    expect(sampleTimes(100, 100, 4)).toEqual([]);
  });

  it('점 넣기: 도트 격자, 같은 자리는 시각만', () => {
    const s: RibbonSample[] = [];
    expect(pushRibbonSample(s, 1.1, 2.0, 0, 0.25)).toBe(true);
    expect(s[0]).toEqual({ x: 1, y: 2, t: 0 });
    expect(pushRibbonSample(s, 1.05, 2.01, 5, 0.25)).toBe(false);
    expect(s).toHaveLength(1);
    expect(s[0].t).toBe(5);
  });

  it('버리기: 수명 지난 점 · 최대 개수 초과', () => {
    const s: RibbonSample[] = [0, 20, 40, 60, 80, 100, 120].map((t, i) => ({ x: i, y: 0, t }));
    pruneRibbon(s, 130, 100, 40);
    expect(s.map((p) => p.t)).toEqual([40, 60, 80, 100, 120]);
    pruneRibbon(s, 130, 100, 2);
    expect(s.map((p) => p.t)).toEqual([100, 120]);
    pruneRibbon(s, 500, 100, 40);
    expect(s).toHaveLength(0);
  });
});
