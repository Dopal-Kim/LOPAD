import { describe, expect, it } from 'vitest';
import { WEAPONS } from '../../data';
import { GROWTH, TRAITS, growthBranches } from '../../data/growth';
import { WeaponState } from './weapons';

describe('WeaponState (61 G P12 — 각성 게이지 · 갈래 3 · 길 2 · 개성 · 단련)', () => {
  it('게이지는 누적이고 줄지 않는다 (음수·NaN 무시)', () => {
    const w = new WeaponState('katana', WEAPONS.katana);
    expect(w.gain(60)).toBe(60);
    expect(w.gain(-30)).toBe(0);
    expect(w.gain(Number.NaN)).toBe(0);
    expect(w.gauge).toBe(60);
    expect(w.options.map((o) => o.id)).toEqual(['iai', 'batto', 'mangetsu']);
  });

  it('1차 갈래 → 2차 길은 그 갈래의 자식만, 갈래·길 id 는 art §26 이름으로', () => {
    const w = new WeaponState('katana', WEAPONS.katana);
    expect(w.choose('zangetsu')).toBeNull();
    const node = w.choose('iai');
    expect(node?.move).toBe('spin');
    expect(w.stage).toBe(1);
    expect(w.branchId).toBe('senpu');
    expect(w.options.map((o) => o.id)).toEqual(['vortex', 'zangetsu']);
    expect(w.choose('batto')).toBeNull();
    w.choose('vortex');
    expect(w.stage).toBe(2);
    expect(w.pathId).toBe('whirl');
    expect(w.options).toEqual([]);
    expect(w.displayName).toBe('사무라이 칼 · 선풍 · 회오리');
  });

  it('단련: 피해·범위 +10% 누적, 최대 3', () => {
    const w = new WeaponState('greatsword', WEAPONS.greatsword);
    const d0 = w.damageMult;
    const r0 = w.rangeMult;
    for (let i = 0; i < 3; i++) expect(w.temperNow()).toBe(true);
    expect(w.temperNow()).toBe(false);
    expect(w.temper).toBe(GROWTH.temper.max);
    expect(w.damageMult).toBeCloseTo(d0 * 1.3);
    expect(w.rangeMult).toBeCloseTo(r0 * 1.3);
    expect(w.displayName).toContain('+3');
  });

  it('개성: 이 무기 것만 · 한 번씩', () => {
    const w = new WeaponState('dagger', WEAPONS.dagger);
    expect(w.addTrait('d_dashBrand')).toBe(true);
    expect(w.addTrait('d_dashBrand')).toBe(false);
    expect(w.addTrait('k_iaiWave')).toBe(false);
    expect(w.traitDefs.map((t) => t.id)).toEqual(['d_dashBrand']);
  });

  it('세이브 복원: 경로(트리 밖 id 자름)·개성(다른 무기·모르는 것 버림)·단련 상한·게이지·눈금', () => {
    const w = new WeaponState('bow', WEAPONS.bow);
    w.restore({
      gauge: 150,
      path: ['meteor', 'nope'],
      traits: ['b_ricochet', 'k_iaiWave', 'ghost'],
      temper: 9,
      marksDone: 3,
    });
    expect(w.path).toEqual(['meteor']);
    expect(w.traits).toEqual(['b_ricochet']);
    expect(w.temper).toBe(GROWTH.temper.max);
    expect(w.gauge).toBe(150);
    expect(w.marksDone).toBe(3);
    const back = new WeaponState('bow', WEAPONS.bow);
    back.restore(w.toProgress());
    expect(back.toProgress()).toEqual(w.toProgress());
  });

  it('갈래 트리: 무기당 1차 3 + 갈래마다 2차 2, growth.json 갈래·길이 모두 노드에 이어진다', () => {
    for (const [id, def] of Object.entries(WEAPONS)) {
      expect(def.personality.branches).toHaveLength(3);
      const gb = growthBranches(id);
      expect(gb).toHaveLength(3);
      for (const b of gb) {
        const node = def.personality.branches.find((n) => n.id === b.node);
        expect(node, `${id}.${b.id}`).toBeTruthy();
        expect(node!.tags!.length).toBeGreaterThan(0);
        expect(b.paths.map((p) => p.node).sort()).toEqual(node!.next!.map((n) => n.id).sort());
      }
      // 셋째 갈래 = 옛 최종 각성 (옛 모양 재사용)
      expect(gb[2].legacyLook).toBe(true);
    }
  });

  it('개성 풀: 무기당 14장 (기본 8 = 4동사 × 2 · 갈래마다 2)', () => {
    for (const id of Object.keys(WEAPONS)) {
      const mine = TRAITS.filter((t) => t.weapon === id);
      expect(mine).toHaveLength(14);
      expect(mine.filter((t) => !t.branch)).toHaveLength(8);
    }
  });
});
