import type { EconomyData, ShopItem, StatKey, StatReward } from '../data/types';
import type { Rng } from './rng';
import type { UiCost } from '../contract/ui';

/** 61라운드 #3: 메뉴 줄 가격 (줄 label 에는 넣지 않는다 — UI 가 이 값을 한 번 그린다). currency = 서사 이름(전표) */
export function goldCost(amount: number, gold: number, currency: string): UiCost {
  return { kind: 'gold', amount, label: `${amount}${currency}`, affordable: gold >= amount };
}

/** 플레이어가 런 중 얻은 능력치 보너스 (기본 스탯에 더해진다) */
export interface StatBonus {
  attack: number;
  maxHp: number;
  defense: number;
  crit: number;
}

export const EMPTY_BONUS: StatBonus = { attack: 0, maxHp: 0, defense: 0, crit: 0 };

/** 기준 골드에 ±variance 비율의 무작위를 적용 (최소 1) */
export function rollGold(base: number, variance: number, rng: Rng): number {
  const f = 1 + (rng.next() * 2 - 1) * variance;
  return Math.max(1, Math.round(base * f));
}

/** 상점 가격: 기준가 + 층 번호 × 층당 상승분 */
export function shopPrice(item: ShopItem, stageIndex: number): number {
  return item.price + item.pricePerStage * stageIndex;
}

export function applyStatReward(bonus: StatBonus, reward: StatReward): StatBonus {
  return {
    attack: bonus.attack + (reward.attack ?? 0),
    maxHp: bonus.maxHp + (reward.maxHp ?? 0),
    defense: bonus.defense + (reward.defense ?? 0),
    crit: bonus.crit + (reward.crit ?? 0),
  };
}

export function findReward(economy: EconomyData, id: StatKey): StatReward {
  const r = economy.statRewards.find((x) => x.id === id);
  if (!r) throw new Error(`[economy] 보상 없음: ${id}`);
  return r;
}

/** 치명타 판정: crit 은 퍼센트 */
export function rollCrit(critPercent: number, rng: Rng): boolean {
  return critPercent > 0 && rng.next() * 100 < critPercent;
}
