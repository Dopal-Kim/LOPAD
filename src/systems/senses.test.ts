import { describe, expect, it } from 'vitest';
import { SenseTracker } from './senses';

describe('SenseTracker', () => {
  it('같은 스테이지에서 새 방식마다 1씩', () => {
    const t = new SenseTracker();
    expect(t.recordKill('attack')).toBe(true);
    expect(t.recordKill('attack')).toBe(false);
    expect(t.recordKill('dashAttack')).toBe(true);
    expect(t.recordKill('parry')).toBe(true);
    expect(t.sense).toBe(3);
  });
  it('스테이지가 바뀌면 방식은 다시 셀 수 있고 수치는 유지', () => {
    const t = new SenseTracker();
    t.recordKill('attack');
    t.nextStage();
    expect(t.sense).toBe(1);
    expect(t.recordKill('attack')).toBe(true);
    expect(t.sense).toBe(2);
  });
});
