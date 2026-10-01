import { describe, expect, it } from 'vitest';
import {
  META_CONFIG,
  MetaStore,
  buyUpgrade,
  emptyMeta,
  markUnderstood,
  metaBonus,
  recordRun,
  soulsForRun,
  upgradeCost,
  type RunSummary,
} from './meta';
import type { StorageLike } from './save';

function memStorage(): StorageLike {
  const m = new Map<string, string>();
  return { getItem: (k) => m.get(k) ?? null, setItem: (k, v) => void m.set(k, v), removeItem: (k) => void m.delete(k) };
}

const run: RunSummary = {
  weaponId: 'katana',
  weaponStage: 1,
  evolutionNames: ['거합'],
  floorReached: 3,
  kills: 25,
  cleared: false,
};

describe('meta', () => {
  it('영혼 = 층×10 + 처치×1 + 진화×20 (+클리어 100)', () => {
    expect(soulsForRun(run)).toBe(30 + 25 + 20);
    expect(soulsForRun({ ...run, cleared: true, floorReached: 7 })).toBe(70 + 25 + 20 + 100);
  });
  it('도감은 최고 기록을 누적한다', () => {
    let m = emptyMeta();
    m = recordRun(m, run).meta;
    m = recordRun(m, { ...run, weaponStage: 0, floorReached: 5, kills: 10, evolutionNames: [] }).meta;
    expect(m.codex.katana).toEqual({ runs: 2, kills: 35, maxStage: 1, bestFloor: 5, evolutions: ['거합'] });
    expect(m.runs).toBe(2);
    expect(m.bestFloor).toBe(5);
    expect(m.souls).toBe(75 + 60);
  });
  it('강화 구매: 비용 상승, 최대 레벨, 영혼 부족', () => {
    const def = META_CONFIG.upgrades.find((u) => u.id === 'maxHp')!;
    expect(upgradeCost(def, 0)).toBe(30);
    expect(upgradeCost(def, 2)).toBe(60);
    let m = { ...emptyMeta(), souls: 100 };
    m = buyUpgrade(m, 'maxHp')!;
    expect(m.souls).toBe(70);
    expect(m.upgrades.maxHp).toBe(1);
    m = buyUpgrade(m, 'maxHp')!; // 45
    expect(m.souls).toBe(25);
    expect(buyUpgrade(m, 'maxHp')).toBeNull(); // 60 필요
    const maxed = { ...emptyMeta(), souls: 9999, upgrades: { potionCarry: 2 } };
    expect(buyUpgrade(maxed, 'potionCarry')).toBeNull();
  });
  it('보너스 환산', () => {
    const b = metaBonus({ ...emptyMeta(), upgrades: { maxHp: 3, attack: 1, dashCooldown: 2, potionCarry: 1 } });
    expect(b).toEqual({ maxHp: 15, attack: 1, defense: 0, dashCooldownMult: 0.9, potionCarry: 1 });
  });
  it('저장소 읽기/쓰기와 깨진 데이터', () => {
    const st = memStorage();
    const s = new MetaStore(st);
    expect(s.read()).toEqual(emptyMeta());
    s.write({ ...emptyMeta(), souls: 5 });
    expect(s.read().souls).toBe(5);
    st.setItem('lopad.meta', '{bad');
    expect(s.read()).toEqual(emptyMeta());
  });

  it('엔딩 이해한다 기록은 영혼·도감을 건드리지 않고 understood 만 켠다', () => {
    const m = { ...emptyMeta(), souls: 7 };
    const u = markUnderstood(m);
    expect(u.understood).toBe(true);
    expect(u.souls).toBe(7);
    expect(m.understood).toBeUndefined();
  });
});
