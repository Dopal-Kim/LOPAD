import { describe, expect, it } from 'vitest';
import { arcPoint, flashAlphaAt, segmentStyle } from './trailMath';

const P = { core: 0xffffff, accent: 0xe2a33c, body: 0x6f7e97 };

describe('trail math (42라운드 잔상 궤적)', () => {
  it('두께는 최신 3 → 오래된 1 로 정수 감쇠, 최신 구간엔 코어 선', () => {
    const newest = segmentStyle(1, 0, P, 3, 1);
    const oldest = segmentStyle(0, 0, P, 3, 1);
    expect(newest.width).toBe(3);
    expect(oldest.width).toBe(1);
    expect(segmentStyle(0.5, 0, P, 3, 1).width).toBe(2);
    expect(newest.coreWidth).toBe(1);
    expect(oldest.coreWidth).toBe(0);
  });

  it('색은 코어 → 강조 → 보조, 나이가 차면 투명', () => {
    expect(segmentStyle(1, 0, P, 3, 1).color).toBe(P.core);
    expect(segmentStyle(2 / 3, 0, P, 3, 1).color).toBe(P.accent);
    expect(segmentStyle(1 / 3, 0, P, 3, 1).color).toBe(P.body);
    expect(segmentStyle(0.5, 0, P, 3, 1).color).not.toBe(P.body);
    expect(segmentStyle(0, 0, P, 3, 1).color).toBe(P.body);
    expect(segmentStyle(1, 1, P, 3, 1).alpha).toBe(0);
    expect(segmentStyle(1, 0.5, P, 3, 1).alpha).toBeCloseTo(0.5, 3);
    expect(segmentStyle(0, 0, P, 3, 1).alpha).toBeCloseTo(0.35, 3);
  });

  it('베기 호: t=0 은 angle-half, t=1 은 angle+half', () => {
    const a = arcPoint(0, 0, 10, 0, Math.PI / 2, 0);
    const b = arcPoint(0, 0, 10, 0, Math.PI / 2, 1);
    expect(a.x).toBeCloseTo(0, 6);
    expect(a.y).toBeCloseTo(-10, 6);
    expect(b.y).toBeCloseTo(10, 6);
    expect(arcPoint(0, 0, 10, 0, 1, 0.5)).toEqual({ x: 10, y: 0 });
  });

  it('화면 섬광 감쇠: 선형으로 0, 길이 0 이면 즉시 0', () => {
    expect(flashAlphaAt(0.2, 40, 0)).toBeCloseTo(0.2, 6);
    expect(flashAlphaAt(0.2, 40, 20)).toBeCloseTo(0.1, 6);
    expect(flashAlphaAt(0.2, 40, 40)).toBe(0);
    expect(flashAlphaAt(0.2, 40, 99)).toBe(0);
    expect(flashAlphaAt(0.2, 0, 0)).toBe(0);
  });
});
