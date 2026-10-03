import { describe, expect, it } from 'vitest';
import { arcTipAt, columnAt, polarLerp, swingWindow, tipAt } from './bladeTipMath';

describe('bladeTipMath: 칼끝 궤적 (55라운드 Q7)', () => {
  const starts = [0, 40, 80, 100, 140];
  const total = 200;

  it('시각 → 열·비율 (구간별 맞춤 재생 시작 기준)', () => {
    expect(columnAt(starts, total, 0)).toEqual({ col: 0, frac: 0 });
    expect(columnAt(starts, total, 60)).toEqual({ col: 1, frac: 0.5 });
    expect(columnAt(starts, total, 170)).toEqual({ col: 4, frac: 0.5 });
    expect(columnAt(starts, total, 999)).toEqual({ col: 4, frac: 1 });
  });

  it('극좌표 보간: 원점 둘레를 돈다 (직선 지름길이 아니라)', () => {
    const c = { x: 0, y: 0 };
    const mid = polarLerp(c, { x: 10, y: 0 }, { x: 0, y: 10 }, 0.5);
    expect(Math.hypot(mid.x, mid.y)).toBeCloseTo(10);
    expect(mid.x).toBeCloseTo(mid.y);
    // ±π 경계는 짧은 쪽으로
    const wrap = polarLerp(c, { x: -10, y: 1 }, { x: -10, y: -1 }, 0.5);
    expect(wrap.x).toBeLessThan(-9.9);
  });

  it('칼끝: 열 사이 보간, 칼집 안(null) 열은 null, 마지막 열은 그대로', () => {
    const track = {
      starts,
      total,
      tips: [null, { x: 10, y: 0 }, { x: 0, y: 10 }, { x: -10, y: 0 }, { x: -10, y: 0 }],
      center: { x: 0, y: 0 },
    };
    expect(tipAt(track, 10)).toBeNull();
    expect(tipAt(track, 40)).toEqual({ x: 10, y: 0 });
    const q = tipAt(track, 60)!;
    expect(Math.hypot(q.x, q.y)).toBeCloseTo(10);
    expect(tipAt(track, 150)).toEqual({ x: -10, y: 0 });
  });

  it('찍는 구간: 판정 앞 1프레임 ~ 판정 뒤 1프레임', () => {
    expect(swingWindow(starts, total, [2], 1, 1)).toEqual({ from: 40, to: 140 });
    expect(swingWindow(starts, total, [3, 4], 1, 1)).toEqual({ from: 80, to: 200 });
    expect(swingWindow(starts, total, undefined, 1, 1)).toBeNull();
  });

  it('호 폴백: from → to 각도를 비율만큼', () => {
    const p = arcTipAt({ x: 0, y: 0 }, 10, 0, Math.PI / 2, 1);
    expect(p.x).toBeCloseTo(0);
    expect(p.y).toBeCloseTo(10);
  });
});
