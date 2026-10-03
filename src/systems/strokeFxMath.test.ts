import { describe, expect, it } from 'vitest';
import {
  STROKE_FX,
  burstAt,
  burstRays,
  burstTimes,
  gapIntensity,
  gapWidth,
  heatAt,
  pathLength,
  pathPointAt,
  pathPrefix,
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

describe('strokeFxMath 49라운드: 빛 터짐', () => {
  it('타임라인 순서: 흔들림·모음 → 섬광 트레이스 → 광선 → 하얗게(peak) → 걷힘(done)', () => {
    const B = STROKE_FX.BURST;
    const T = burstTimes();
    expect(T.raysAt).toBeGreaterThan(B.CHARGE_MS);
    expect(T.peakAt).toBeGreaterThan(T.raysAt);
    expect(T.doneAt).toBeGreaterThan(T.peakAt);
    const a = burstAt(B.CHARGE_MS / 2);
    expect(a.shaking).toBe(true);
    expect(a.trace).toBe(0);
    expect(a.white).toBe(0);
    const b = burstAt(B.CHARGE_MS + B.TRACE_MS / 2);
    expect(b.shaking).toBe(false);
    expect(b.trace).toBeCloseTo(0.5);
    expect(b.rays).toBe(0);
    const p = burstAt(T.peakAt);
    expect(p.white).toBe(1);
    expect(p.peaked).toBe(true);
    expect(p.done).toBe(false);
    expect(burstAt(T.peakAt - 1).peaked).toBe(false);
    expect(burstAt(T.peakAt + B.HOLD_MS + B.WHITE_OUT_MS / 2).white).toBeCloseTo(0.5);
    expect(burstAt(T.doneAt)).toMatchObject({ white: 0, done: true });
  });
  it('경로 자르기: 길이 비율만큼, 끝점은 보간', () => {
    const pts = [0, 0, 10, 0, 10, 10];
    expect(pathLength(pts)).toBe(20);
    expect(pathPrefix(pts, 0.25)).toEqual([0, 0, 5, 0]);
    expect(pathPrefix(pts, 0.75)).toEqual([0, 0, 10, 0, 10, 5]);
    expect(pathPrefix(pts, 1)).toEqual(pts);
    expect(pathPointAt(pts, 0.5)).toEqual({ x: 10, y: 0 });
  });
  it('광선: 개수만큼, 획 위에서 무게중심 바깥쪽으로', () => {
    const paths = [
      [100, 100, 300, 100],
      [100, 300, 300, 300],
    ];
    const rays = burstRays(paths, () => 0.5);
    expect(rays).toHaveLength(STROKE_FX.BURST.RAY_COUNT);
    for (const r of rays) {
      expect([100, 300]).toContain(r.y);
      // 위 획은 위로(sin < 0), 아래 획은 아래로(sin > 0)
      expect(Math.sign(Math.sin(r.angle))).toBe(r.y === 100 ? -1 : 1);
      expect(r.len).toBeGreaterThanOrEqual(STROKE_FX.BURST.RAY_LEN[0]);
    }
    expect(burstRays([], () => 0.5)).toEqual([]);
  });
});
