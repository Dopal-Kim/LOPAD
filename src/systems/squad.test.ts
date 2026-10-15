import { describe, expect, it } from 'vitest';
import { MobSquad } from './squad';

describe('P19 공격 토큰 (MobSquad)', () => {
  it('일반 적은 최대 3, 정예는 따로 1, 징집병은 2마리만', () => {
    const s = new MobSquad(3, 1, { dummy: 2 });
    const [a, b, c, d, e, f] = [{}, {}, {}, {}, {}, {}];
    expect(s.take(a, 'dummy', false)).toBe(true);
    expect(s.take(b, 'dummy', false)).toBe(true);
    expect(s.take(c, 'dummy', false)).toBe(false);
    expect(s.take(c, 'archer', false)).toBe(true);
    expect(s.take(d, 'charger', false)).toBe(false);
    expect(s.take(e, 'dummy', true)).toBe(true);
    expect(s.take(f, 'archer', true)).toBe(false);
    expect(s.count).toBe(3);
    s.release(a);
    expect(s.take(d, 'charger', false)).toBe(true);
    expect(s.take(d, 'charger', false)).toBe(true);
  });

  it('사라진 개체의 토큰은 거둔다', () => {
    const s = new MobSquad(1, 1, {});
    const dead = { active: true };
    expect(s.take(dead, 'x', false)).toBe(true);
    dead.active = false;
    expect(s.take({}, 'x', false)).toBe(true);
  });

  it('북 오라: 반경 안·시간 안만 배율', () => {
    const s = new MobSquad();
    s.drum(0, 0, 10, 1000, 1.25);
    expect(s.drumMult(5, 5, 500)).toBe(1.25);
    expect(s.drumMult(20, 0, 500)).toBe(1);
    expect(s.drumMult(5, 5, 1000)).toBe(1);
  });
});
