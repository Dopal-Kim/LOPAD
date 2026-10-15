import { describe, expect, it, vi } from 'vitest';
import { EventEmitter } from 'node:events';

// EventBus 가 Phaser 를 import 하므로(window 필요) 이벤트 이미터만 node 것으로 대체한다
vi.mock('phaser', () => ({ default: { Events: { EventEmitter } } }));

import { isReversal, steerVelocity } from './HeroMotion';

describe('P19 주인공 움직임 감각', () => {
  const max = 104;
  it('빠른 가속: 정지 → 최고 속도까지 accelMs (60fps 80ms = 5프레임)', () => {
    let v = { x: 0, y: 0 };
    let frames = 0;
    while (v.x < max - 1e-6 && frames < 20) {
      v = steerVelocity(v, { x: max, y: 0 }, max, 16, 80);
      frames++;
    }
    expect(frames).toBe(5);
    expect(v).toEqual({ x: max, y: 0 });
  });

  it('내딛기·대쉬 뒤 남은 큰 속도는 최고 속도로 자르고 멈춤도 같은 빠르기', () => {
    const v = steerVelocity({ x: 600, y: 0 }, { x: 0, y: 0 }, max, 16, 80);
    expect(v.x).toBeCloseTo(max - (max * 16) / 80);
  });

  it('반대 방향 입력 = 미끄럼 (빠르게 가는 중에만)', () => {
    const M = { skidDot: -0.3, skidMinSpeedRatio: 0.6 };
    expect(isReversal({ x: max, y: 0 }, { x: -1, y: 0 }, max, M)).toBe(true);
    expect(isReversal({ x: max, y: 0 }, { x: 0, y: 1 }, max, M)).toBe(false);
    expect(isReversal({ x: 20, y: 0 }, { x: -1, y: 0 }, max, M)).toBe(false);
    expect(isReversal({ x: max, y: 0 }, { x: 0, y: 0 }, max, M)).toBe(false);
  });
});
