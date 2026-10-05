/**
 * 60라운드 (e) 상점 진열 확장 (data/bundle2.json shop — 57 Q38 확정안 A안): 고정 4칸(13 Q3) + 진열 3칸(패시브 2·층 소모품 1) +
 * 진열 바꾸기(상점 안 전표 리롤만 — 토큰 아님, 15 → 25 → 35) + 종군 상인의 궤짝 덤 1회(35전표 → 패시브 2택, 상점 노드) +
 * 지도 정보 3품목(상점 노드 — 계약 §14.5·§14.6 group 'mapInfo'). 가격 = × 저주 외상(+20%) × E9 '돌려줌' 할인(다음 상점 1회).
 * 메뉴는 계약 §14.6 `shop` 줄 확장(group·price·soldOut). 진열은 층 안에서 그 상점 노드마다 유지.
 */
import { EventBus, Events } from '../../../core/EventBus';
import { gameState } from '../../../core/GameState';
import { ECONOMY, STORY } from '../../../data';
import { BUNDLE2, consumableDef } from '../../../data/bundle2';
import type { MapInfoId } from '../../../data/bundle2Types';
import type { UiCost, UiMenuLine } from '../../../contract/ui';
import type { ShopStock } from '../../../systems/bundle2/BundleState';
import { buyIntel } from '../../../systems/bundle2/routeExtras';
import { rerollPrice, rollDisplay } from '../../../systems/bundle2/shopStock';
import { shopPrice } from '../../../systems/economy';
import type { Game } from '../../Game';

export type ShopBoughtPayload = {
  id: string;
  price: number;
  group?: 'fixed' | 'display' | 'reroll' | 'chest' | 'mapInfo';
};

const label = (k: string): string => {
  const v = BUNDLE2.shop.labels[k];
  return typeof v === 'string' ? v : k;
};

export class ShopMenu {
  /** 이번 상점에 적용한 일회 할인 (E9) */
  private discount = 0;

  constructor(private readonly g: Game) {}

  /** 상점 노드 (궤짝 덤·지도 정보는 상점 노드만) */
  private get atShopNode(): boolean {
    return this.g.nodeKind === 'shop';
  }

  private get key(): string {
    return this.g.node?.id ?? `floor:${gameState.stageIndex}`;
  }

  private priceMult(): number {
    return (this.g.build?.shopPriceMult() ?? 1) * (1 - this.discount);
  }

  private stock(): ShopStock {
    const B = gameState.bundle;
    let s = B.shops.find((x) => x.nodeId === this.key);
    if (!s) {
      s = { nodeId: this.key, display: this.roll(), rerolls: 0, chestUsed: false };
      B.shops.push(s);
    }
    return s;
  }

  private roll(): ShopStock['display'] {
    const P = gameState.passives;
    const pool = P.defs
      .filter((d) => P.level(d.id) < P.maxLevel && BUNDLE2.shop.passivePrices[d.rarity] !== undefined)
      .map((d) => ({ id: d.id, rarity: d.rarity }));
    return rollDisplay(this.g.rng, pool, this.priceMult());
  }

  private cost(amount: number): UiCost {
    return {
      kind: 'gold',
      amount,
      label: `${amount}${STORY.names.gold}`,
      affordable: gameState.gold >= amount,
    };
  }

  /** 상점을 열 때 (Economy.openShop): 다음 상점 할인을 이 상점에 쓴다 */
  onOpen(): void {
    const B = gameState.bundle;
    if (B.shopDiscount > 0) {
      this.discount = B.shopDiscount;
      B.shopDiscount = 0;
    }
  }

  /** 계약 §14.6 줄: 고정 4칸 다음에 붙는다. 키 = 'd1'… / 'reroll' / 'chest' / 'm:<id>' */
  lines(fixed: UiMenuLine[]): UiMenuLine[] {
    const s = this.stock();
    const out: UiMenuLine[] = fixed.map((l) => ({ ...l, group: 'fixed' as const }));
    s.display.forEach((d, i) => {
      const name =
        d.kind === 'passive' ? (gameState.passives.def(d.id)?.name ?? d.id) : (consumableDef(d.id)?.name ?? d.id);
      const lv = d.kind === 'passive' ? gameState.passives.level(d.id) : 0;
      const detail =
        d.kind === 'passive'
          ? (gameState.passives.def(d.id)?.description ?? '')
          : (consumableDef(d.id)?.description ?? '');
      out.push({
        key: `d${i + 1}`,
        label: d.sold
          ? `${name}  ${label('soldOut')}`
          : `${d.kind === 'passive' ? `[${d.rarity}] ` : ''}${name}${lv > 0 ? ` (Lv${lv} → ${lv + 1})` : ''}  ${d.price} ${STORY.names.gold}`,
        enabled: !d.sold && gameState.gold >= d.price,
        detail,
        group: 'display',
        price: this.cost(d.price),
        soldOut: d.sold,
        ...(d.kind === 'passive' && d.rarity ? { kind: 'passive' as const, rarity: d.rarity as never } : {}),
      });
    });
    const rp = rerollPrice(s.rerolls, this.priceMult());
    out.push({
      key: 'reroll',
      label: `${label('reroll')}  ${rp} ${STORY.names.gold}`,
      enabled: gameState.gold >= rp,
      group: 'reroll',
      price: this.cost(rp),
    });
    if (this.atShopNode) {
      const cp = Math.round(BUNDLE2.shop.chest.price * this.priceMult());
      out.push({
        key: 'chest',
        label: s.chestUsed ? `${label('chest')}  ${label('soldOut')}` : `${label('chest')}  ${cp} ${STORY.names.gold}`,
        enabled: !s.chestUsed && gameState.gold >= cp,
        detail: `패시브 ${BUNDLE2.shop.chest.choices}택`,
        group: 'chest',
        price: this.cost(cp),
        soldOut: s.chestUsed,
      });
      out.push(...this.mapInfoLines('m:'));
    }
    return out;
  }

  /** 지도 정보 줄 (상점 노드 · 국경 초소 지도 장수 메뉴 공용) */
  mapInfoLines(prefix: string): UiMenuLine[] {
    const ex = gameState.bundle.floor;
    if (!ex) return [];
    return BUNDLE2.mapInfo.items.map((it) => {
      const bought = ex.intel[it.id];
      const price = Math.round(it.price * (this.g.build?.shopPriceMult() ?? 1));
      return {
        key: `${prefix}${it.id}`,
        label: bought ? `${it.name}  ${label('soldOut')}` : `${it.name}  ${price} ${STORY.names.gold}`,
        enabled: !bought && gameState.gold >= price,
        group: 'mapInfo',
        price: this.cost(price),
        soldOut: bought,
      };
    });
  }

  /** 줄 고르기. 처리했으면 true (rerender = 같은 메뉴 다시 그리기, close = 상점 닫기) */
  select(key: string, rerender: () => void, close: () => void): boolean {
    const s = this.stock();
    if (key.startsWith('d')) {
      const d = s.display[Number(key.slice(1)) - 1];
      if (!d || d.sold || !this.pay(d.price, d.id, 'display')) return true;
      d.sold = true;
      if (d.kind === 'passive') {
        gameState.passives.add(d.id);
        EventBus.emit(Events.PASSIVE_GAINED, { id: d.id, level: gameState.passives.level(d.id) });
        this.g.build?.record('passive', { id: d.id, source: 'shop' });
        rerender();
      } else {
        close();
        this.g.bundle?.consumables.gain(d.id as never);
      }
      return true;
    }
    if (key === 'reroll') {
      const price = rerollPrice(s.rerolls, this.priceMult());
      if (!this.pay(price, 'reroll', 'reroll')) return true;
      s.rerolls += 1;
      s.display = this.roll();
      rerender();
      return true;
    }
    if (key === 'chest') {
      const price = Math.round(BUNDLE2.shop.chest.price * this.priceMult());
      if (s.chestUsed || !this.pay(price, 'chest', 'chest')) return true;
      s.chestUsed = true;
      close();
      this.g.buildMenus.openPassiveMenu('chest', { choices: BUNDLE2.shop.chest.choices });
      return true;
    }
    if (key.startsWith('m:')) {
      this.buyMapInfo(key.slice(2) as MapInfoId);
      rerender();
      return true;
    }
    return false;
  }

  /** 지도 정보 사기 (지도 장수·상점 공용). 샀으면 true */
  buyMapInfo(id: MapInfoId): boolean {
    const ex = gameState.bundle.floor;
    const it = BUNDLE2.mapInfo.items.find((x) => x.id === id);
    if (!ex || !it || ex.intel[id]) return false;
    const price = Math.round(it.price * (this.g.build?.shopPriceMult() ?? 1));
    if (!this.pay(price, `mapInfo:${id}`, 'mapInfo')) return false;
    buyIntel(ex, id);
    return true;
  }

  private pay(price: number, id: string, group: ShopBoughtPayload['group']): boolean {
    if (gameState.gold < price) return false;
    gameState.gold -= price;
    EventBus.emit(Events.GOLD_CHANGED, { gold: gameState.gold, delta: -price });
    EventBus.emit(Events.SHOP_BOUGHT, { id, price, group } satisfies ShopBoughtPayload);
    return true;
  }

  /** 고정 4칸 가격 (13 Q3 — 층 가산 · 배율) */
  fixedPrice(item: (typeof ECONOMY.shop.items)[number]): number {
    return Math.round(shopPrice(item, gameState.stageIndex) * this.priceMult());
  }
}
