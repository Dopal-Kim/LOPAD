import { describe, expect, it } from 'vitest';
import {
  STROKE_FX,
  gapIntensity,
  gapWidth,
  heatAt,
  pathLength,
  pathPointAt,
  pathPrefix,
  searAt,
  searTimes,
} from './strokeFxMath';

describe('strokeFxMath (48라운드 Q8 획 찢기)', () => {
  it('51라운드 붓: 빠를수록 가늘고 밝다 (상한에서 멈춤), 이전(2~9px)의 절반 이하', () => {
    expect(gapWidth(0)).toBe(STROKE_FX.WIDTH.SLOW_PX);
    expect(gapWidth(STROKE_FX.WIDTH.SPEED_REF * 3)).toBeCloseTo(STROKE_FX.WIDTH.FAST_PX);
    expect(gapWidth(900)).toBeLessThan(gapWidth(300));
    expect(gapIntensity(1500)).toBeGreaterThan(gapIntensity(200));
    expect(STROKE_FX.WIDTH.SLOW_PX).toBeLessThanOrEqual(9 / 2);
    expect((STROKE_FX.WIDTH.SLOW_PX + STROKE_FX.WIDTH.FAST_PX) / 2).toBeLessThanOrEqual((2 + 9) / 4);
  });
  it('열기: 처음 1 → COOL_MS 에 0, 획 끝 섬광은 식기 전에만 더한다', () => {
    expect(heatAt(0, null)).toBe(1);
    expect(heatAt(STROKE_FX.COOL_MS / 2, null)).toBeLessThan(1);
    expect(heatAt(STROKE_FX.COOL_MS, null)).toBe(0);
    expect(heatAt(100, 0)).toBeGreaterThan(heatAt(100, null));
    expect(heatAt(STROKE_FX.COOL_MS + 1, 0)).toBe(0);
    expect(heatAt(100, STROKE_FX.FLARE_MS + 1)).toBe(heatAt(100, null));
  });
});

describe('strokeFxMath 53라운드: 타오름·스며듦 (빛 터짐 교체)', () => {
  it('타임라인: 타오름(열기 오름·흔들림) → 스며듦(열기·폭 줄어 잔불 심) → 불티 → 검게(peak) → 걷힘(done), 1.5~2.5초 안에 peak', () => {
    const S = STROKE_FX.SEAR;
    const T = searTimes();
    expect(T.peakAt).toBeGreaterThanOrEqual(1500);
    expect(T.peakAt).toBeLessThanOrEqual(2500);
    expect(T.settledAt).toBeLessThanOrEqual(S.DARK_AT);
    const a = searAt(0);
    const b = searAt(S.IGNITE_MS - 1);
    expect(a.shaking).toBe(true);
    expect(b.heat).toBeGreaterThan(a.heat);
    expect(b.seep).toBe(0);
    const c = searAt(T.settledAt);
    expect(c.shaking).toBe(false);
    expect(c.seep).toBe(1);
    expect(c.heat).toBeCloseTo(S.EMBER_HEAT, 2);
    expect(c.widthMul).toBeCloseTo(S.WIDTH_MUL[1]);
    expect(searAt(S.EMBERS_AT + 1).embers).toBe(true);
    expect(searAt(S.EMBERS_AT - 1).embers).toBe(false);
    expect(searAt(T.peakAt - 1).peaked).toBe(false);
    expect(searAt(T.peakAt)).toMatchObject({ dark: 1, peaked: true, done: false });
    expect(searAt(T.doneAt)).toMatchObject({ dark: 0, done: true });
  });
  it('타오르는 빛 층은 백열(흰색) 없이 호박 램프만', () => {
    for (const L of STROKE_FX.SEAR_LAYERS) expect(typeof L.color).toBe('number');
  });
  it('경로 자르기: 길이 비율만큼, 끝점은 보간', () => {
    const pts = [0, 0, 10, 0, 10, 10];
    expect(pathLength(pts)).toBe(20);
    expect(pathPrefix(pts, 0.25)).toEqual([0, 0, 5, 0]);
    expect(pathPrefix(pts, 0.75)).toEqual([0, 0, 10, 0, 10, 5]);
    expect(pathPrefix(pts, 1)).toEqual(pts);
    expect(pathPointAt(pts, 0.5)).toEqual({ x: 10, y: 0 });
  });
});
