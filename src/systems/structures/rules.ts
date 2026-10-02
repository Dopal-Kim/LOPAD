/**
 * 구조물 규칙 순수 함수 (47라운드, 전부 임시값 — 수치는 data/structures.json). Phaser 의존 없음.
 */
import type { Rng } from '../rng';

/** C2 궤짝 가격: (기본 + 이번 층에 연 수 × 상승 + 층 계수 × 층 index) × 할인 */
export function chestPrice(
  p: { basePrice: number; stepPrice: number; perFloorPrice: number },
  openedThisFloor: number,
  stageIndex: number,
  discount = 1,
): number {
  return Math.max(
    0,
    Math.round((p.basePrice + p.stepPrice * openedThisFloor + p.perFloorPrice * stageIndex) * discount),
  );
}

/** 1-3 빚: 주운 골드 amount 중 자동 상환분 (올림, 빚·획득량을 넘지 않음) */
export function repaySplit(amount: number, debt: number, ratio: number): { kept: number; repaid: number } {
  if (debt <= 0 || amount <= 0) return { kept: amount, repaid: 0 };
  const repaid = Math.min(debt, amount, Math.ceil(amount * ratio));
  return { kept: amount - repaid, repaid };
}

/** 1-3 보스 처치 정산: 남은 빚 10G 당(올림) 최대 HP -n */
export function debtPenalty(debt: number, maxHpPer10: number): number {
  return debt > 0 ? Math.ceil(debt / 10) * maxHpPer10 : 0;
}

export interface DrunkParams {
  maxLevel: number;
  attackPerLevel: number;
  defensePerLevel: number;
  swayDegPerLevel: number;
  swayPeriodMs: number;
  dashAttackBonusAtMax: number;
}

/** 1-5 취기 단계별 효과 */
export function drunkMods(
  level: number,
  p: DrunkParams,
): { attackMult: number; defense: number; swayDeg: number; dashAttackMult: number } {
  const L = Math.max(0, Math.min(p.maxLevel, level));
  return {
    attackMult: 1 + p.attackPerLevel * L,
    defense: p.defensePerLevel * L,
    swayDeg: p.swayDegPerLevel * L,
    dashAttackMult: L >= p.maxLevel && L > 0 ? 1 + p.dashAttackBonusAtMax : 1,
  };
}

/** 1-5 조준 흔들림 각도(rad): 느린 사인파 ±swayDeg */
export function swayAngle(level: number, timeMs: number, p: DrunkParams): number {
  const deg = drunkMods(level, p).swayDeg;
  if (deg === 0) return 0;
  return ((deg * Math.PI) / 180) * Math.sin((2 * Math.PI * timeMs) / p.swayPeriodMs);
}

/** 2-4 판돈 종: 울린 횟수별 남은 시련 배율 (누적 가산) */
export function stakeMods(
  rings: number,
  p: { hpPerRing: number; extraPerRing: number; goldPerRing: number; personalityPerRing: number },
): { hpMult: number; extra: number; goldMult: number; personalityMult: number } {
  return {
    hpMult: 1 + p.hpPerRing * rings,
    extra: p.extraPerRing * rings,
    goldMult: 1 + p.goldPerRing * rings,
    personalityMult: 1 + p.personalityPerRing * rings,
  };
}

/** 웨이브 구성 배율: 각 항목 count × countMult(반올림, 최소 1) + 첫 항목에 extra */
export function scaleWave<T extends { count: number }>(entries: readonly T[], countMult: number, extra: number): T[] {
  return entries.map((e, i) => ({
    ...e,
    count: Math.max(1, Math.round(e.count * countMult)) + (i === 0 ? Math.max(0, extra) : 0),
  }));
}

export type CardOutcome = { kind: 'gold'; gold: number } | { kind: 'potion' } | { kind: 'point' } | { kind: 'bad' };

/**
 * 2-1 패 3장: 길패 2(가중치로 골드·물약·포인트) + 흉패 1, 섞음.
 * 골드 길패 = 판돈 × goldMult × (1 + boost × (판 번호 - 1))
 */
export function dealCards(
  rng: Rng,
  stake: number,
  round: number,
  p: { goodGoldMult: number; goodBoostPerRound: number; goodWeights: Record<string, number> },
): CardOutcome[] {
  const boost = 1 + p.goodBoostPerRound * Math.max(0, round - 1);
  const pickGood = (): CardOutcome => {
    const entries = Object.entries(p.goodWeights).filter(([, w]) => w > 0);
    const total = entries.reduce((a, [, w]) => a + w, 0);
    let r = rng.next() * total;
    let id = entries[entries.length - 1][0];
    for (const [k, w] of entries) {
      r -= w;
      if (r < 0) {
        id = k;
        break;
      }
    }
    if (id === 'potion') return { kind: 'potion' };
    if (id === 'point') return { kind: 'point' };
    return { kind: 'gold', gold: Math.round(stake * p.goodGoldMult * boost) };
  };
  return rng.shuffle([pickGood(), pickGood(), { kind: 'bad' }]);
}

/** 2-1 판 번호(1부터)의 판돈 */
export function cardStake(round: number, p: { stake: number; stakeStep: number }): number {
  return p.stake + p.stakeStep * Math.max(0, round - 1);
}

/** 2-6 패시브 맡김 값: 희귀도 값 × (1 + 레벨당 보너스 × (레벨 - 1)) */
export function pawnValue(
  rarity: string,
  level: number,
  p: { rarityValue: Record<string, number>; levelBonus: number },
): number {
  const base = p.rarityValue[rarity] ?? p.rarityValue.common ?? 0;
  return Math.round(base * (1 + p.levelBonus * Math.max(0, level - 1)));
}

/** 2-6 되찾는 값 = 받은 금액 × 배율 */
export function redeemCost(received: number, redeemMult: number): number {
  return Math.round(received * redeemMult);
}

/** 2-2 피 판매: 현재 HP 의 ratio (올림, 최소 1). 현재 HP 가 최대의 minRatio 이상일 때만 */
export function bloodCost(hp: number, ratio: number): number {
  return Math.max(1, Math.ceil(hp * ratio));
}

export function canSellBlood(hp: number, maxHp: number, minRatio: number): boolean {
  return maxHp > 0 && hp / maxHp >= minRatio && hp > 1;
}

/** C5 불씨 회복량 */
export function emberHeal(embers: number, maxHp: number, perEmber: number): number {
  return Math.round(maxHp * perEmber * Math.max(0, embers));
}

/** 1-4 숙성 진행: 넣은 뒤 깬 시련 수 (0..needed) 와 다 익었는지 */
export function agingProgress(
  trialsAtPut: number,
  trialsNow: number,
  needed: number,
): { done: number; ready: boolean } {
  const done = Math.max(0, Math.min(needed, trialsNow - trialsAtPut));
  return { done, ready: done >= needed };
}

/** 2-3 투견 링 결과 배율: 시간 안 전멸이면 clear/flawless, 아니면 0 */
export function ringPayout(
  stake: number,
  outcome: 'clear' | 'flawless' | 'timeout',
  p: { clearMult: number; flawlessMult: number },
): number {
  if (outcome === 'timeout') return 0;
  return Math.round(stake * (outcome === 'flawless' ? p.flawlessMult : p.clearMult));
}
