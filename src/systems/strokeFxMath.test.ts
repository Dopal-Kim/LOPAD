import { describe, expect, it } from 'vitest';
import { STROKE_FX, gapIntensity, gapWidth, heatAt, jaggedPoints, offsetPoints } from './strokeFxMath';

describe('strokeFxMath (48라운드 Q8 획 찢기)', () => {
  it('빠를수록 틈이 넓고 밝다 (상한에서 멈춤)', () => {
    expect(gapWidth(0)).toBe(STROKE_FX.WIDTH.MIN_PX);
    expect(gapWidth(STROKE_FX.WIDTH.SPEED_REF * 3)).toBe(STROKE_FX.WIDTH.MAX_PX);
    expect(gapWidth(900)).toBeGreaterThan(gapWidth(300));
    expect(gapIntensity(1500)).toBeGreaterThan(gapIntensity(200));
  });
  it('열기: 처음 1 → COOL_MS 에 0, 획 끝 섬광은 식기 전에만 더한다', () => {
    expect(heatAt(0, null)).toBe(1);
    expect(heatAt(STROKE_FX.COOL_MS / 2, null)).toBeLessThan(1);
    expect(heatAt(STROKE_FX.COOL_MS, null)).toBe(0);
    expect(heatAt(100, 0)).toBeGreaterThan(heatAt(100, null));
    expect(heatAt(STROKE_FX.COOL_MS + 1, 0)).toBe(0);
    expect(heatAt(100, STROKE_FX.FLARE_MS + 1)).toBe(heatAt(100, null));
  });
  it('찢긴 선: 양 끝은 그대로, 안쪽 점은 수직으로만 흔들린다', () => {
    const pts = jaggedPoints(0, 0, 60, 0, 8, () => 1);
    expect(pts.slice(0, 2)).toEqual([0, 0]);
    expect(pts.slice(-2)).toEqual([60, 0]);
    expect(pts.length / 2).toBe(Math.ceil(60 / STROKE_FX.JITTER.STEP_PX) + 1);
    for (let i = 2; i < pts.length - 2; i += 2) expect(Math.abs(pts[i + 1])).toBeCloseTo(STROKE_FX.JITTER.AMP * 8);
  });
  it('가장자리 선: 수평선을 위아래로 민다', () => {
    const off = offsetPoints([0, 0, 10, 0, 20, 0], 3);
    expect(off.filter((_, i) => i % 2 === 1).every((y) => y === 3)).toBe(true);
  });
});
