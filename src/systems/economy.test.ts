import { describe, expect, it } from 'vitest';
import { ECONOMY } from '../data';
import { EMPTY_BONUS, applyStatReward, findReward, rollCrit, rollGold, shopPrice } from './economy';
import { Rng } from './rng';

describe('economy', () => {
  it('골드는 ±variance 안에서 굴러가고 최소 1', () => {
    const rng = new Rng(1);
    for (let i = 0; i < 200; i++) {
      const g = rollGold(10, 0.3, rng);
      expect(g).toBeGreaterThanOrEqual(7);
      expect(g).toBeLessThanOrEqual(13);
    }
    expect(rollGold(0, 0.3, rng)).toBe(1);
  });
  it('상점 가격은 층마다 오른다', () => {
    const sense = ECONOMY.shop.items.find((i) => i.id === 'sense')!;
    expect(shopPrice(sense, 0)).toBe(40);
    expect(shopPrice(sense, 3)).toBe(70);
  });
  it('능력치 보상 누적', () => {
    let b = EMPTY_BONUS;
    b = applyStatReward(b, findReward(ECONOMY, 'attack'));
    b = applyStatReward(b, findReward(ECONOMY, 'maxHp'));
    b = applyStatReward(b, findReward(ECONOMY, 'maxHp'));
    expect(b).toEqual({ attack: 1, maxHp: 20, defense: 0, crit: 0 });
  });
  it('치명타 0% 는 절대 안 터지고 100% 는 항상', () => {
    const rng = new Rng(7);
    for (let i = 0; i < 50; i++) expect(rollCrit(0, rng)).toBe(false);
    for (let i = 0; i < 50; i++) expect(rollCrit(100, rng)).toBe(true);
  });
});
