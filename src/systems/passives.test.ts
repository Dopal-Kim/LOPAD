import { describe, expect, it } from 'vitest';
import { ECONOMY } from '../data';
import { PASSIVES, PassiveSet, levelParam } from './passives';
import { Rng } from './rng';

describe('passives', () => {
  it('57라운드 29종 (기존 8 + 신규 17 + 취기 4), 희귀도는 경제 표에 존재, 태그 1~2개', () => {
    expect(PASSIVES.items).toHaveLength(29);
    for (const p of PASSIVES.items) {
      expect(ECONOMY.rarity[p.rarity]).toBeDefined();
      expect(p.tags.length).toBeGreaterThanOrEqual(1);
      expect(p.tags.length).toBeLessThanOrEqual(2);
    }
    // 취기 QC-6: 깨진 잔 조각·마지막 잔 취기 겸 + 신규 4종
    const drunk = PASSIVES.items.filter((p) => p.tags.includes('drunk')).map((p) => p.id);
    expect(drunk).toEqual(['brokenShard', 'lastCup', 'spilledDrink', 'hipFlask', 'harshBreath', 'drunkFist']);
    // 희귀도 분포 (설계안 1.6 + 취기 3장): 일반 11 · 희귀 9 · 영웅 6 · 전설 3
    const count = (r: string) => PASSIVES.items.filter((p) => p.rarity === r).length;
    expect([count('common'), count('rare'), count('epic'), count('legendary')]).toEqual([11, 9, 6, 3]);
  });
  it('byLevel 은 레벨별 합계, 규칙 인자는 레벨별 배열', () => {
    const s = new PassiveSet();
    s.add('hipFlask');
    expect(s.total('potionMaxAdd')).toBe(1);
    s.add('hipFlask');
    expect(s.total('potionMaxAdd')).toBe(1);
    s.add('hipFlask');
    expect(s.total('potionMaxAdd')).toBe(2);
    expect(s.total('potionDropAdd')).toBeCloseTo(0.09);
    s.add('lastCup');
    expect(s.rules().map((r) => r.rule.kind)).toEqual(['lastCup']);
    expect(levelParam([0, 0.1, 0.25], 2)).toBe(0.1);
    expect(levelParam(3, 2)).toBe(3);
  });
  it('뽑기 조건: 희귀도 제한 · 테마 태그 가중', () => {
    const rng = new Rng(5);
    const epic = new PassiveSet().rollChoices(rng, ECONOMY.rarity, 3, { rarities: ['epic'] });
    expect(epic.every((p) => p.rarity === 'epic')).toBe(true);
    let themed = 0;
    let plain = 0;
    for (let i = 0; i < 300; i++) {
      const a = new PassiveSet().rollChoices(rng, ECONOMY.rarity, 1, { themeTag: 'drunk', themeMult: 2 })[0];
      const b = new PassiveSet().rollChoices(rng, ECONOMY.rarity, 1)[0];
      if (a.tags.includes('drunk')) themed += 1;
      if (b.tags.includes('drunk')) plain += 1;
    }
    expect(themed).toBeGreaterThan(plain);
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

describe('60라운드 Q30 저주 길 보상: 영웅 이상 1개 확정 + 나머지 일반 확률', () => {
  it('처음 하나는 늘 영웅 이상, 나머지는 모든 희귀도에서 (중복 없음)', () => {
    const rng = new Rng(17);
    const others = new Set<string>();
    for (let i = 0; i < 200; i++) {
      const picks = new PassiveSet().rollChoices(rng, ECONOMY.rarity, 3, {
        guaranteed: { rarities: ['epic', 'legendary'], count: 1 },
      });
      expect(picks).toHaveLength(3);
      expect(['epic', 'legendary']).toContain(picks[0].rarity);
      expect(new Set(picks.map((p) => p.id)).size).toBe(3);
      for (const p of picks.slice(1)) others.add(p.rarity);
    }
    // 나머지 둘은 희귀도 제한 없이 — 일반 등급도 나온다
    expect(others.has('common')).toBe(true);
  });
});
