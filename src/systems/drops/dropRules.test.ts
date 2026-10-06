import { describe, expect, it } from 'vitest';
import { ECONOMY } from '../../data';
import { dropFrames, magnetStep, stretchScale, voucherSize } from './dropRules';

describe('61 P13 §4 바닥 줍기 규칙', () => {
  it('전표 무더기 크기: 경계(economy.pickup.voucherSize) 이상이면 mid · large', () => {
    const T = ECONOMY.pickup.voucherSize;
    expect(voucherSize(1, T)).toBe('small');
    expect(voucherSize(T.mid, T)).toBe('mid');
    expect(voucherSize(T.large - 1, T)).toBe('mid');
    expect(voucherSize(T.large, T)).toBe('large');
    // 1층 잡몹 전표(3~8)는 small·mid, 보스 전표(50+)는 large
    expect(voucherSize(3, T)).toBe('small');
    expect(voucherSize(100, T)).toBe('large');
  });

  it('시트 프레임: 행 = kinds 자리 × 행당 프레임 + 상태 열 · 상태가 없으면 idle 은 그 행 0 열', () => {
    const def = { frames: 8, kinds: ['small', 'mid', 'large'], states: { idle: [0, 1, 2, 3], pickup: [6, 7] } };
    expect(dropFrames(def, 'idle', 'mid')).toEqual([8, 9, 10, 11]);
    expect(dropFrames(def, 'pickup', 'large')).toEqual([22, 23]);
    expect(dropFrames(def, 'spawn', 'small')).toEqual([]);
    expect(dropFrames({ frames: 4 }, 'idle', null)).toEqual([0]);
    expect(dropFrames(def, 'idle', 'nope')).toEqual([0, 1, 2, 3]);
  });

  it('자석 흡수: 가속하며 다가가고, 한 걸음 안이면 도착 (넘어가지 않음)', () => {
    let p = { x: 0, y: 0 };
    let speed = 30;
    let arrived = false;
    let steps = 0;
    while (!arrived && steps < 200) {
      const r = magnetStep(p, { x: 40, y: 0 }, speed, 16, { accel: 640, max: 350 });
      expect(r.x).toBeLessThanOrEqual(40);
      expect(r.speed).toBeGreaterThanOrEqual(speed);
      p = r;
      speed = r.speed;
      arrived = r.arrived;
      steps++;
    }
    expect(arrived).toBe(true);
    expect(p).toMatchObject({ x: 40, y: 0 });
    expect(steps).toBeLessThan(40);
  });

  it('늘어남: 움직이는 축으로 길어지고 다른 축은 줄며, 속도에 비례 (최대 stretch)', () => {
    expect(stretchScale(0, 0, 100, 0.4)).toEqual([1, 1]);
    const [sx, sy] = stretchScale(100, 10, 100, 0.4);
    expect(sx).toBeCloseTo(1.4);
    expect(sy).toBeCloseTo(0.8);
    const [vx, vy] = stretchScale(0, -50, 100, 0.4);
    expect(vy).toBeCloseTo(1.2);
    expect(vx).toBeCloseTo(0.9);
  });
});
