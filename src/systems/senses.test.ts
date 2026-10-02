import { describe, expect, it } from 'vitest';
import { KILL_KINDS, SenseTracker } from './senses';

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
  it('47라운드: 환경 처치가 네 번째 방식 → 층당 최대 4', () => {
    const t = new SenseTracker();
    for (const k of KILL_KINDS) expect(t.recordKill(k)).toBe(true);
    expect(t.recordKill('environment')).toBe(false);
    expect(t.gainedThisStage).toBe(4);
    expect(KILL_KINDS).toHaveLength(4);
  });
});
