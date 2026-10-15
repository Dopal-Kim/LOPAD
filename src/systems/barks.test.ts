import { describe, expect, it } from 'vitest';
import { BARK, BarkGate } from './barks';

describe('P19 지나가는 대사 간격', () => {
  it('같은 적 4초 · 전체 1.5초 · 후보 없으면 없음', () => {
    const g = new BarkGate();
    const a = {};
    const b = {};
    expect(g.pick(a, ['x', 'y'], 0, 0.9)).toBe('y');
    expect(g.pick(b, ['z'], 1000, 0)).toBeNull();
    expect(g.pick(b, ['z'], BARK.GLOBAL_MS, 0)).toBe('z');
    expect(g.pick(a, ['x'], 3000, 0)).toBeNull();
    expect(g.pick(a, ['x'], BARK.PER_MOB_MS, 0)).toBe('x');
    expect(g.pick(a, [], 99999, 0)).toBeNull();
  });
});
