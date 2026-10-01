import { describe, expect, it } from 'vitest';
import { WEAPONS } from '../data';
import { WeaponState } from './weapons';

describe('WeaponState', () => {
  it('threshold 도달 시 진화하고 수치는 0으로', () => {
    const w = new WeaponState('katana', WEAPONS.katana);
    expect(w.gainPersonality(60)).toBeNull();
    expect(w.personality).toBe(60);
    expect(w.gainPersonality(50)).toBe(1);
    expect(w.personality).toBe(0);
    expect(w.stage).toBe(1);
    expect(w.evolution?.name).toContain('거합');
  });
  it('진화하면 히트박스·데미지 배율이 적용된다', () => {
    const w = new WeaponState('katana', WEAPONS.katana);
    const base = w.hitbox;
    w.gainPersonality(100);
    expect(w.hitbox.width).toBeCloseTo(base.width * 1.4);
    expect(w.damageMult).toBeCloseTo(1.2);
  });
  it('마지막 진화 후에는 더 쌓이지 않는다', () => {
    const w = new WeaponState('katana', WEAPONS.katana);
    w.gainPersonality(100);
    expect(w.canEvolve).toBe(false);
    expect(w.gainPersonality(100)).toBeNull();
    expect(w.personality).toBe(0);
  });
});
