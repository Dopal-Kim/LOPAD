import { describe, expect, it } from 'vitest';
import { WEAPONS, WEAPON_RULES } from '../data';
import { WeaponState } from './weapons';

describe('WeaponState (27라운드 분기 트리)', () => {
  it('임계 도달 시 선택 대기가 되고 게이지는 멈춘다', () => {
    const w = new WeaponState('katana', WEAPONS.katana);
    expect(w.threshold).toBe(100);
    expect(w.gainPersonality(60)).toBe(false);
    expect(w.personality).toBe(60);
    expect(w.gainPersonality(50)).toBe(true);
    expect(w.choicePending).toBe(true);
    expect(w.personality).toBe(100);
    expect(w.stage).toBe(0);
    expect(w.gainPersonality(30)).toBe(false); // 선택 전엔 더 쌓이지 않음
    expect(w.personality).toBe(100);
    expect(w.options.map((o) => o.id)).toEqual(['iai', 'batto']);
  });

  it('변환 A 선택 → 1차, 다음 임계 200 에서 2차 선택지는 A 의 자식', () => {
    const w = new WeaponState('katana', WEAPONS.katana);
    const base = w.hitbox;
    w.gainPersonality(100);
    expect(w.choose('zangetsu')).toBeNull(); // 2차 노드는 아직 못 고름
    const node = w.choose('iai');
    expect(node?.name).toContain('거합');
    expect(w.stage).toBe(1);
    expect(w.personality).toBe(0);
    expect(w.choicePending).toBe(false);
    expect(w.hitbox.width).toBeCloseTo(base.width * 1.4);
    expect(w.damageMult).toBeCloseTo(1.2);
    expect(w.mods.slashTrail).toBe(true);
    expect(w.threshold).toBe(200);
    expect(w.gainPersonality(199)).toBe(false);
    expect(w.gainPersonality(1)).toBe(true);
    expect(w.options.map((o) => o.id)).toEqual(['wide', 'zangetsu']);
    expect(w.choose('batto')).toBeNull();
    w.choose('zangetsu');
    expect(w.stage).toBe(2);
    expect(w.path).toEqual(['iai', 'zangetsu']);
    expect(w.mods.slashTrail).toBe(true); // 경로 병합
    expect(w.mods.trailDot).toBeDefined();
    expect(w.options).toEqual([]); // 트리 끝
    expect(w.displayName).toBe('사무라이 칼 · 잔월 (殘月)');
  });

  it('강화는 피해·범위 +15% 를 누적하고 단계는 유지한다', () => {
    const w = new WeaponState('greatsword', WEAPONS.greatsword);
    w.gainPersonality(100);
    w.choose('weight');
    const dmg1 = w.damageMult;
    w.gainPersonality(200);
    expect(w.reinforceNow()).toBe(true);
    expect(w.stage).toBe(1);
    expect(w.reinforce).toBe(1);
    expect(w.personality).toBe(0);
    expect(w.damageMult).toBeCloseTo(dmg1 * 1.15);
    expect(w.hitbox.width).toBeCloseTo(WEAPONS.greatsword.hitbox.width * 1.15);
    expect(w.threshold).toBe(200); // 다음 임계 그대로
    expect(w.options.map((o) => o.id)).toEqual(['ironwall', 'giant']); // 다시 3지선다
    expect(w.displayName).toBe('대검 · 중압 (重壓) +1');
  });

  it('강화 최대 3회, 2차까지 끝나면 게이지가 멈춘다', () => {
    const w = new WeaponState('bow', WEAPONS.bow);
    w.gainPersonality(100);
    w.choose('scatter');
    w.gainPersonality(200);
    w.choose('seek');
    for (let i = 0; i < WEAPON_RULES.reinforceMax; i++) {
      expect(w.canEvolve).toBe(true);
      expect(w.gainPersonality(200)).toBe(true);
      expect(w.reinforceNow()).toBe(true);
    }
    expect(w.reinforce).toBe(3);
    expect(w.canReinforce).toBe(false);
    expect(w.canEvolve).toBe(false);
    expect(w.gainPersonality(500)).toBe(false);
    expect(w.personality).toBe(0);
    expect(w.reinforceNow()).toBe(false);
    expect(w.damageMult).toBeCloseTo(0.9 * 0.6 * 1.45);
    expect(w.mods.spread?.count).toBe(3);
    expect(w.mods.homingTurnDeg).toBe(240);
  });

  it('세이브 복원: 경로·강화·선택 대기, 모르는 id 는 잘라낸다', () => {
    const w = new WeaponState('dagger', WEAPONS.dagger);
    w.restore({ personality: 50, path: ['gale', 'assassin'], reinforce: 2, choicePending: false });
    expect(w.path).toEqual(['gale', 'assassin']);
    expect(w.reinforce).toBe(2);
    expect(w.mods.moveSpeedMult).toBe(1.25);
    expect(w.mods.shadowStepMult).toBe(3);
    const p = w.toProgress();
    const w2 = new WeaponState('dagger', WEAPONS.dagger);
    w2.restore(p);
    expect(w2.toProgress()).toEqual(p);
    const w3 = new WeaponState('dagger', WEAPONS.dagger);
    w3.restore({ personality: 0, path: ['twin', 'nope'], reinforce: 9, choicePending: true });
    expect(w3.path).toEqual(['twin']);
    expect(w3.reinforce).toBe(WEAPON_RULES.reinforceMax);
    expect(w3.choicePending).toBe(true);
  });
});
