import { describe, expect, it } from 'vitest';
import { Rng } from '../rng';
import { STRUCTURES_FILE, allStructureSprites, num, spriteFor, structureDef, txt, validateStructures } from './data';
import {
  agingProgress,
  bloodCost,
  canSellBlood,
  cardStake,
  chestPrice,
  dealCards,
  debtPenalty,
  drunkMods,
  emberHeal,
  pawnValue,
  redeemCost,
  repaySplit,
  ringPayout,
  scaleWave,
  stakeMods,
  swayAngle,
} from './rules';

const drunkP = {
  maxLevel: 3,
  attackPerLevel: 0.1,
  defensePerLevel: -1,
  swayDegPerLevel: 3,
  swayPeriodMs: 2400,
  dashAttackBonusAtMax: 0.2,
};

describe('structures 데이터 (47라운드)', () => {
  it('16종 전부 정의, 계약 kind ↔ 아트 시트 id 대응표', () => {
    expect(STRUCTURES_FILE.structures).toHaveLength(16);
    expect(spriteFor(structureDef('crate'), 'stage1')).toBe('crate_f1');
    expect(spriteFor(structureDef('crate'), 'stage2')).toBe('crate_f2');
    expect(spriteFor(structureDef('crate'), 'stage7')).toBe('crate_f1');
    const map: Record<string, string> = {
      chest: 'chest',
      grave: 'grave',
      campfire: 'bonfire',
      cask: 'barrel',
      still: 'still',
      ledger: 'ledger',
      agingBarrel: 'cask',
      counter: 'counter',
      hiddenWall: 'cellar_wall',
      cardTable: 'card_table',
      exchange: 'chip_exchange',
      dogRing: 'dog_ring',
      stakeBell: 'bet_bell',
      roulette: 'roulette',
      pawn: 'pawn',
    };
    for (const [kind, sheet] of Object.entries(map))
      expect(spriteFor(structureDef(kind as Parameters<typeof structureDef>[0]), 'stage1')).toBe(sheet);
    expect(allStructureSprites()).toHaveLength(17);
  });

  it('잘못된 정의는 거부한다', () => {
    const bad = JSON.parse(JSON.stringify(STRUCTURES_FILE));
    bad.structures[0].kind = 'fly';
    expect(() => validateStructures(bad)).toThrow(/kind/);
    const missing = JSON.parse(JSON.stringify(STRUCTURES_FILE));
    missing.structures = missing.structures.filter((s: { id: string }) => s.id !== 'pawn');
    expect(() => validateStructures(missing)).toThrow(/pawn/);
  });

  it('텍스트 치환과 숫자 파라미터', () => {
    const d = structureDef('ledger');
    expect(txt(d, 'borrowed', { loan: 60, debt: 90 })).toContain('60');
    expect(num(d, 'loan')).toBe(60);
    expect(() => num(d, 'nope')).toThrow();
  });
});

describe('구조물 규칙 순수 함수', () => {
  it('C2 궤짝 가격: 35 → 열 때마다 +25, 층 +10, 할인', () => {
    const p = { basePrice: 35, stepPrice: 25, perFloorPrice: 10 };
    expect(chestPrice(p, 0, 0)).toBe(35);
    expect(chestPrice(p, 1, 0)).toBe(60);
    expect(chestPrice(p, 0, 1)).toBe(45);
    expect(chestPrice(p, 0, 0, 0.5)).toBe(18);
  });

  it('1-3 빚: 주운 골드 50% 자동 상환(올림), 빚·획득량 상한, 보스 정산 10G당 -2', () => {
    expect(repaySplit(10, 90, 0.5)).toEqual({ kept: 5, repaid: 5 });
    expect(repaySplit(3, 90, 0.5)).toEqual({ kept: 1, repaid: 2 });
    expect(repaySplit(10, 2, 0.5)).toEqual({ kept: 8, repaid: 2 });
    expect(repaySplit(10, 0, 0.5)).toEqual({ kept: 10, repaid: 0 });
    expect(debtPenalty(90, 2)).toBe(18);
    expect(debtPenalty(1, 2)).toBe(2);
    expect(debtPenalty(0, 2)).toBe(0);
  });

  it('1-5 취기: 단당 공격 +10%·방어 -1·흔들림 3°, 3단 대쉬 공격 +20%', () => {
    expect(drunkMods(0, drunkP)).toEqual({ attackMult: 1, defense: -0, swayDeg: 0, dashAttackMult: 1 });
    const two = drunkMods(2, drunkP);
    expect(two.attackMult).toBeCloseTo(1.2);
    expect(two.defense).toBe(-2);
    expect(two.dashAttackMult).toBe(1);
    expect(drunkMods(3, drunkP).dashAttackMult).toBeCloseTo(1.2);
    expect(drunkMods(9, drunkP).swayDeg).toBe(9);
    expect(swayAngle(0, 600, drunkP)).toBe(0);
    expect(swayAngle(1, 600, drunkP)).toBeCloseTo((3 * Math.PI) / 180);
  });

  it('2-4 판돈 종: 울린 횟수만큼 누적', () => {
    const p = { hpPerRing: 0.25, extraPerRing: 1, goldPerRing: 0.6, personalityPerRing: 0.4 };
    expect(stakeMods(0, p)).toEqual({ hpMult: 1, extra: 0, goldMult: 1, personalityMult: 1 });
    const two = stakeMods(2, p);
    expect(two.hpMult).toBeCloseTo(1.5);
    expect(two.extra).toBe(2);
    expect(two.goldMult).toBeCloseTo(2.2);
  });

  it('웨이브 배율: count × 배율(반올림) + 첫 항목에 extra', () => {
    const wave = [
      { enemy: 'dummy', count: 4 },
      { enemy: 'archer', count: 1 },
    ];
    expect(scaleWave(wave, 1, 0)).toEqual(wave);
    expect(scaleWave(wave, 1.5, 1)).toEqual([
      { enemy: 'dummy', count: 7 },
      { enemy: 'archer', count: 2 },
    ]);
  });

  it('2-1 패: 3장 중 흉패 1, 판돈은 판마다 +10, 골드 길패는 판마다 +20%', () => {
    const p = { goodGoldMult: 2.5, goodBoostPerRound: 0.2, goodWeights: { gold: 1, potion: 0, point: 0 } };
    for (let seed = 1; seed < 30; seed++) {
      const deck = dealCards(new Rng(seed), 20, 1, p);
      expect(deck).toHaveLength(3);
      expect(deck.filter((c) => c.kind === 'bad')).toHaveLength(1);
      for (const c of deck) if (c.kind === 'gold') expect(c.gold).toBe(50);
    }
    const r3 = dealCards(new Rng(5), 40, 3, p).find((c) => c.kind === 'gold');
    expect(r3 && r3.kind === 'gold' && r3.gold).toBe(Math.round(40 * 2.5 * 1.4));
    expect(cardStake(1, { stake: 20, stakeStep: 10 })).toBe(20);
    expect(cardStake(5, { stake: 20, stakeStep: 10 })).toBe(60);
    // 같은 시드면 같은 패
    expect(dealCards(new Rng(9), 20, 1, structureDef('cardTable').params as never)).toEqual(
      dealCards(new Rng(9), 20, 1, structureDef('cardTable').params as never),
    );
  });

  it('2-6 전당포: 희귀도 값 × 레벨 보너스, 되찾기 ×1.5', () => {
    const p = { rarityValue: { common: 40, rare: 60, epic: 90, legendary: 140 }, levelBonus: 0.5 };
    expect(pawnValue('common', 1, p)).toBe(40);
    expect(pawnValue('rare', 2, p)).toBe(90);
    expect(pawnValue('legendary', 3, p)).toBe(280);
    expect(pawnValue('unknown', 1, p)).toBe(40);
    expect(redeemCost(40, 1.5)).toBe(60);
  });

  it('2-2 환전대: 현재 HP 25%(올림), 26% 이상일 때만', () => {
    expect(bloodCost(100, 0.25)).toBe(25);
    expect(bloodCost(3, 0.25)).toBe(1);
    expect(canSellBlood(26, 100, 0.26)).toBe(true);
    expect(canSellBlood(25, 100, 0.26)).toBe(false);
  });

  it('C5 불씨·1-4 숙성·2-3 투견 링 배당', () => {
    expect(emberHeal(2, 100, 0.1)).toBe(20);
    expect(emberHeal(0, 100, 0.1)).toBe(0);
    expect(agingProgress(1, 1, 2)).toEqual({ done: 0, ready: false });
    expect(agingProgress(1, 3, 2)).toEqual({ done: 2, ready: true });
    expect(agingProgress(1, 9, 2)).toEqual({ done: 2, ready: true });
    const rp = { clearMult: 2, flawlessMult: 3 };
    expect(ringPayout(30, 'clear', rp)).toBe(60);
    expect(ringPayout(30, 'flawless', rp)).toBe(90);
    expect(ringPayout(30, 'timeout', rp)).toBe(0);
  });
});
