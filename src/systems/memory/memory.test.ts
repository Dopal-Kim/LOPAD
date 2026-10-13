import { describe, expect, it } from 'vitest';
import { MEMORY } from '../../data/memory';
import { META_CONFIG, emptyMeta, type MetaData } from '../meta';
import {
  canUnlockAny,
  defaultKeepsake,
  keepsakeEffect,
  lockedTraits,
  memoryBook,
  nextUnlock,
  openAspect,
  openKeepsakes,
  openShopGoods,
  setKeepsake,
  unlockMemory,
} from './memory';
import { RunMemory } from './runMemory';
import { shopGoodsFor } from '../shopGoods';
import { growthMenu } from '../growth/growthMenu';
import { WeaponState } from '../weapon/weapons';
import { WEAPONS } from '../../data';

const meta = (souls: number, extra: Partial<MetaData> = {}): MetaData => ({ ...emptyMeta(), souls, ...extra });

describe('62 루프 2 C 기억 (P1-8)', () => {
  it('14종 — 소품 4 · 모양 4 · 떠올릴 개성 4 · 장터 2, 가장 싼 것 10 (첫 사망 직후)', () => {
    const count = (k: string) => MEMORY.items.filter((m) => m.kind === k).length;
    expect([count('keepsake'), count('aspect'), count('pool'), count('shop')]).toEqual([4, 4, 4, 2]);
    expect(Math.min(...MEMORY.items.map((m) => m.cost))).toBe(10);
    expect(nextUnlock(meta(0), META_CONFIG)).toMatchObject({ cost: 10, left: 10 });
    expect(nextUnlock(meta(12), META_CONFIG)).toMatchObject({ cost: 10, left: 0 });
  });

  it('떠올리기: 영혼을 쓰고 한 번만 · 모자라면 null · 첫 소품은 바로 지닌다', () => {
    expect(unlockMemory(meta(5), 'oldVoucher')).toBeNull();
    const m = unlockMemory(meta(15), 'oldVoucher')!;
    expect(m.souls).toBe(5);
    expect(m.memory?.unlocked).toEqual(['oldVoucher']);
    expect(defaultKeepsake(m)).toBe('oldVoucher');
    expect(unlockMemory({ ...m, souls: 99 }, 'oldVoucher')).toBeNull();
    expect(openKeepsakes(m).map((k) => k.id)).toEqual(['oldVoucher']);
    // 빈손을 고르면 다음 기본값도 빈손
    expect(defaultKeepsake(setKeepsake(m, null)!)).toBeNull();
    expect(setKeepsake(m, 'knotCord')).toBeNull(); // 안 떠올린 소품
  });

  it('몸의 기억(stat:) 은 능력치 강화 한 단계', () => {
    const m = unlockMemory(meta(100), 'stat:maxHp')!;
    expect(m.upgrades.maxHp).toBe(1);
    expect(m.souls).toBe(60);
  });

  it('떠올릴 개성: 떠올리기 전에는 그 무기 개성 두 장이 풀에 없다', () => {
    expect([...lockedTraits(meta(0), 'katana')].sort()).toEqual(['k_edgeLift', 'k_iaiChain']);
    const m = unlockMemory(meta(50), 'pool_katana')!;
    expect(lockedTraits(m, 'katana').size).toBe(0);
    const w = new WeaponState('katana', WEAPONS.katana);
    const rnd = () => 0.5;
    for (let i = 0; i < 20; i++) {
      const menu = growthMenu(w, 'trait', 1, () => (i * 0.37) % 1, undefined, undefined, {
        locked: lockedTraits(meta(0), 'katana'),
      })!;
      for (const l of menu.lines) expect(['k_edgeLift', 'k_iaiChain']).not.toContain(l.trait?.id);
    }
    expect(growthMenu(w, 'trait', 1, rnd, undefined, undefined, { traitCards: 4 })!.lines).toHaveLength(4);
  });

  it('모양 · 장터 품목은 떠올린 것만', () => {
    expect(openAspect(meta(0), 'bow')).toBeNull();
    const m = unlockMemory(meta(30), 'aspect_bow')!;
    expect(openAspect(m, 'bow')?.trait).toBe('b_perfectPin');
    expect(openShopGoods(m)).toEqual([]);
    const s = unlockMemory(meta(20), 'inkBottle')!;
    expect(openShopGoods(s)).toEqual(['inkBottle']);
    expect(shopGoodsFor(meta(0)).map((g) => g.id)).toEqual(['relic', 'potion', 'heal']);
    expect(shopGoodsFor(s).map((g) => g.id)).toContain('inkBottle');
  });

  it('62 I: 장터의 것·몸의 기억 칸 그림 = 아트 ui_relics/memory_* (받은 것만)', () => {
    const none = memoryBook(meta(10), META_CONFIG);
    expect(none.chapters[3].entries.every((e) => e.iconKey === undefined)).toBe(true);
    const book = memoryBook(meta(10), META_CONFIG, (k) => k.startsWith('ui_relics/memory_'));
    expect(book.chapters[3].entries.map((e) => e.iconKey)).toEqual([
      'ui_relics/memory_ink',
      'ui_relics/memory_bellows',
    ]);
    expect(book.chapters[4].entries.map((e) => e.iconKey)).toEqual([
      'ui_relics/memory_hp',
      'ui_relics/memory_attack',
      'ui_relics/memory_dash',
    ]);
    expect(MEMORY.icons?.none).toBe('memory_empty');
  });

  it('기억 장: 다섯 칸 · 상태 한 줄 · 귀퉁이 canBuy', () => {
    const book = memoryBook(meta(10), META_CONFIG);
    expect(book.chapters.map((c) => c.kind)).toEqual(['keepsake', 'aspect', 'pool', 'shop', 'stat']);
    expect(book.chapters[4].entries).toHaveLength(3);
    const voucher = book.chapters[0].entries.find((e) => e.id === 'oldVoucher')!;
    expect(voucher.affordable).toBe(true);
    expect(voucher.state).toBe('떠올린다 · 영혼 10');
    expect(voucher.detail).toBe('시작 전표 +30');
    expect(book.chapters[1].entries[0].detail).toContain("'흘려 밀기'");
    expect(canUnlockAny(meta(9), META_CONFIG)).toBe(false);
    expect(canUnlockAny(meta(10), META_CONFIG)).toBe(true);
  });

  it('이번 생 기억: 첫 개성 카드(시험 등급 + 붓, 상한) · 투구 한 번 · 다시 뽑기 · 세이브', () => {
    const r = new RunMemory();
    r.begin({ keepsake: 'inkBrush', trialCards: 4, baseCards: 3, maxCards: 5 });
    expect(r.takeTraitCards(3)).toBe(5);
    expect(r.takeTraitCards(3)).toBe(3);
    r.begin({ keepsake: 'brokenCup', baseCards: 3, maxCards: 5 });
    expect(r.takeTraitCards(3)).toBe(3);
    expect(r.takeHitBlock()).toBe(true);
    expect(r.takeHitBlock()).toBe(false);
    r.rerolls = 2;
    const b = new RunMemory();
    b.restore(r.toSave());
    expect(b.toSave()).toEqual(r.toSave());
    expect(keepsakeEffect('knotCord').dashCharges).toBe(1);
    expect(keepsakeEffect('aspect_bow')).toEqual({});
  });
});
