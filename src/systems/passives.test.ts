import { describe, expect, it } from 'vitest';
import { ECONOMY } from '../data';
import { PASSIVES, PassiveSet } from './passives';
import { Rng } from './rng';

describe('passives', () => {
  it('8종 데이터, 희귀도는 경제 표에 존재', () => {
    expect(PASSIVES.items).toHaveLength(8);
    for (const p of PASSIVES.items) expect(ECONOMY.rarity[p.rarity]).toBeDefined();
  });
  it('레벨 누적과 효과 합계', () => {
    const s = new PassiveSet();
    expect(s.add('ironskin')).toBe(true);
    expect(s.add('ironskin')).toBe(true);
    expect(s.total('defense')).toBe(4);
    s.add('ironskin');
    expect(s.add('ironskin')).toBe(false); // maxLevel 3
    expect(s.total('defense')).toBe(6);
    expect(s.total('attackMult')).toBe(0);
    expect(s.add('nope')).toBe(false);
  });
  it('후보 3개는 서로 다르고 최대 레벨은 제외', () => {
    const s = new PassiveSet();
    s.owned = { ironskin: 3 };
    const rng = new Rng(3);
    for (let i = 0; i < 50; i++) {
      const c = s.rollChoices(rng, ECONOMY.rarity);
      expect(c).toHaveLength(3);
      expect(new Set(c.map((p) => p.id)).size).toBe(3);
      expect(c.some((p) => p.id === 'ironskin')).toBe(false);
    }
  });
  it('희귀도 가중: 일반이 전설보다 훨씬 자주 나온다', () => {
    const rng = new Rng(11);
    let common = 0;
    let legendary = 0;
    for (let i = 0; i < 400; i++) {
      const first = new PassiveSet().rollChoices(rng, ECONOMY.rarity, 1)[0];
      if (first.rarity === 'common') common += 1;
      if (first.rarity === 'legendary') legendary += 1;
    }
    expect(common).toBeGreaterThan(legendary * 3);
  });
  it('복원은 모르는 id 를 버리고 최대 레벨로 자른다', () => {
    const s = new PassiveSet();
    s.restore({ sprint: 9, ghost: 1 });
    expect(s.owned).toEqual({ sprint: 3 });
  });
});
