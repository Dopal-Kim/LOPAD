import { describe, expect, it } from 'vitest';
import { STROKE_FX } from './strokeFxMath';
import { StrokePath, catmullRom, flatten, prefixCount, smoothstep } from './strokeFxSpline';

/** 반지름 r 원호를 n 개 입력점으로 (dtMs 간격) 그은 획 */
function arcStroke(n: number, r: number, dtMs: number, finish = true): StrokePath {
  const p = new StrokePath(() => 0.5);
  for (let k = 0; k < n; k++) {
    const a = (Math.PI * k) / (n - 1);
    p.push(200 + r * Math.cos(a), 200 + r * Math.sin(a), k * dtMs, k * dtMs);
  }
  if (finish) p.finish(n * dtMs);
  return p;
}

describe('strokeFxSpline (51라운드 1절 매끄러운 획)', () => {
  it('Catmull-Rom: 양 끝 점을 지나고, 같은 점 4개면 그 점', () => {
    const P = [
      { x: 0, y: 0 },
      { x: 10, y: 0 },
      { x: 20, y: 10 },
      { x: 30, y: 10 },
    ];
    expect(catmullRom(P[0], P[1], P[2], P[3], 0)).toEqual({ x: 10, y: 0 });
    const end = catmullRom(P[0], P[1], P[2], P[3], 1);
    expect(end.x).toBeCloseTo(20);
    expect(end.y).toBeCloseTo(10);
    const same = catmullRom(P[1], P[1], P[1], P[1], 0.5);
    expect(same.x).toBeCloseTo(10);
  });
  it('일정 간격 표본: 이웃 표본 사이가 STEP_PX (성긴 입력점 12개 → 수백 개 표본)', () => {
    const p = arcStroke(12, 120, 40);
    const s = p.samples;
    expect(s.length).toBeGreaterThan(300);
    for (let k = 1; k < s.length - 1; k++) {
      const d = Math.hypot(s[k].x - s[k - 1].x, s[k].y - s[k - 1].y);
      expect(d).toBeLessThanOrEqual(STROKE_FX.SPLINE.STEP_PX + 1e-6);
      expect(d).toBeGreaterThan(STROKE_FX.SPLINE.STEP_PX * 0.9);
    }
  });
  it('곡선이 원호를 따라간다 (반지름 오차 < 1.5px, 입력점 사이 직선 꺾임 없음)', () => {
    const r = 120;
    const p = arcStroke(12, r, 40);
    for (const q of p.samples) expect(Math.abs(Math.hypot(q.x - 200, q.y - 200) - r)).toBeLessThan(1.5);
    // 꺾임: 이웃 방향 차이가 작다 (직선 이음이면 입력점에서 16° 씩 꺾인다)
    const s = p.samples;
    let maxTurn = 0;
    for (let k = 2; k < s.length - 1; k++) {
      const a1 = Math.atan2(s[k - 1].y - s[k - 2].y, s[k - 1].x - s[k - 2].x);
      const a2 = Math.atan2(s[k].y - s[k - 1].y, s[k].x - s[k - 1].x);
      let d = Math.abs(a2 - a1);
      if (d > Math.PI) d = Math.PI * 2 - d;
      maxTurn = Math.max(maxTurn, d);
    }
    expect(maxTurn).toBeLessThan((3 * Math.PI) / 180);
  });
  it('붓: 빠른 획이 느린 획보다 가늘다, 시작·끝은 가늘어진다', () => {
    const slow = arcStroke(30, 120, 60);
    const fast = arcStroke(30, 120, 4);
    const mid = (p: StrokePath) => p.samples[Math.floor(p.samples.length / 2)].w;
    expect(mid(fast)).toBeLessThan(mid(slow));
    const s = slow.samples;
    expect(s[0].w).toBeLessThan(mid(slow) * 0.5);
    expect(s[s.length - 1].w).toBeLessThan(mid(slow) * 0.5);
    for (const q of s)
      expect(q.w).toBeLessThanOrEqual(STROKE_FX.WIDTH.SLOW_PX * (1 + STROKE_FX.SPLINE.NOISE_AMP) + 1e-6);
  });
  it('긋는 중: tail() 이 펜 끝까지 잇고 저장하지 않는다', () => {
    const p = arcStroke(8, 80, 30, false);
    const before = p.samples.length;
    const tail = p.tail(500);
    expect(tail.length).toBeGreaterThan(0);
    expect(p.samples.length).toBe(before);
    const last = tail[tail.length - 1];
    expect(Math.hypot(last.x - (200 - 80), last.y - 200)).toBeLessThan(0.01);
    p.finish(600);
    expect(p.tail(700)).toEqual([]);
  });
  it('경로 자르기·평탄화', () => {
    const p = arcStroke(10, 60, 30);
    expect(flatten(p.samples)).toHaveLength(p.samples.length * 2);
    expect(prefixCount(p.samples, 1)).toBe(p.samples.length);
    expect(prefixCount(p.samples, 0)).toBe(1);
    const half = prefixCount(p.samples, 0.5);
    expect(half / p.samples.length).toBeGreaterThan(0.45);
    expect(half / p.samples.length).toBeLessThan(0.55);
    expect(smoothstep(-1)).toBe(0);
    expect(smoothstep(2)).toBe(1);
  });
});
