/**
 * 62 루프 2 시스템 C (P16 §1) 장터 품목 목록 (Phaser 의존 없음) — 진열·카드·사기 흐름은 시스템 D(장터 노점).
 * 유품 · 잔의 독주 · 뜨끈한 국밥 · 먹물 한 병(다시 뽑기 — 기억 inkBottle) · 풀무질 한 번(단련 — 기억 bellows). 능력치·감각 품목은 없다.
 * 사기 효과: 유품 = `BuildMenus.grantRelic(id, 'shop')` · 먹물 = `GrowthFlow.addRerolls(1)` · 풀무 = `GrowthFlow.temper()`(더 못 하면 false).
 */
import { RUN_END, type ShopGoodDef } from '../data/runEnd';
import type { MetaData } from './meta';
import { isUnlocked } from './memory/memory';

/** 이 메타에서 진열 후보에 오르는 품목 (기억이 필요한 것은 떠올렸을 때만) */
export function shopGoodsFor(meta: Pick<MetaData, 'memory'>): ShopGoodDef[] {
  return RUN_END.shopGoods.items.filter((it) => !it.memory || isUnlocked(meta, it.memory));
}

/** 품목 값 (유품은 희귀도별 — 없으면 일반 값) */
export function shopGoodPrice(it: ShopGoodDef, rarity = 'common'): number {
  if (typeof it.price === 'number') return it.price;
  return it.price[rarity] ?? it.price.common ?? 0;
}
