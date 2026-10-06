/**
 * 경제: 처치 드랍 · 줍기 · 골드 · 물약 · 상점 타일(메뉴 열기/닫기·구매).
 */
import { DROP_ART } from '../../core/Constants';
import { EventBus, Events, type GoldChangedPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { ECONOMY, STORY } from '../../data';
import type { Mob } from '../../objects/Mob';
import type { Pickup, PickupMagnet } from '../../objects/Pickup';
import { goldCost, rollGold, shopPrice } from '../../systems/economy';
import { kindDef } from '../../systems/route';
import type { UiInteractable } from '../../contract/ui';
import type { Game } from '../Game';
import { ShopKeeper } from './ShopKeeper';

/** 53라운드 UI 요청 B1: 상점 메뉴 그만두기 key (UI 가 Esc·닫기를 select('shop', '0') 으로 보낸다) */
export const SHOP_CANCEL_KEY = '0';

export class Economy {
  shopOpen = false;
  /** Esc 로 닫은 뒤 상점 칸을 벗어날 때까지 다시 열지 않는다 */
  private shopDismissed = false;
  /** 61라운드 단계 2: 상점 노드 상인 (E 로 연다) · 상인 E 로 연 상점인지 (상인 곁을 떠나면 닫는다) */
  private keeper: ShopKeeper | null = null;
  private keeperOpened = false;

  constructor(private readonly g: Game) {}

  dropLoot(mob: Mob, goldMult = 1): void {
    const G = ECONOMY.gold;
    const gold = Math.round(rollGold(mob.goldValue, G.variance, this.g.rng) * goldMult);
    // 57라운드 외상 저주: 처치 전표 0 → 드랍 없음
    if (gold > 0) this.spawnPickup(mob.x, mob.y, 'gold', gold);
    // 57라운드 허리춤 호리병: 독주 드랍 +%p
    if (this.g.rng.chance(ECONOMY.drops.potion.chance + (this.g.build?.potionDropAdd() ?? 0)))
      this.spawnPickup(mob.x + 10, mob.y, 'potion', 1);
  }

  spawnPickup(x: number, y: number, kind: 'gold' | 'potion', value: number): void {
    const g = this.g;
    const pk = g.pickups.get() as Pickup | null;
    if (!pk) return;
    // 61 P13 §4: 떨군 자리에서 흩뿌려져 떨어진다 (그림만 날아가고 판정은 떨어질 자리)
    const ang = g.rng.next() * Math.PI * 2;
    const r = DROP_ART.SCATTER_MIN_PX + g.rng.next() * (DROP_ART.SCATTER_MAX_PX - DROP_ART.SCATTER_MIN_PX);
    const to = this.g.world?.isWalkableAt(x + Math.cos(ang) * r, y + Math.sin(ang) * r)
      ? { x: x + Math.cos(ang) * r, y: y + Math.sin(ang) * r }
      : { x, y };
    pk.spawn(to.x, to.y, kind, value, ECONOMY.gold.dropLifeMs, g.time.now, { x, y });
  }

  onPickup(pk: Pickup): void {
    if (!pk.active) return;
    if (pk.kind === 'gold') {
      pk.collect(this.g.time.now);
      // 47라운드 1-3: 빚이 있으면 일부 자동 상환
      const kept = this.g.structures.onGoldPickup(pk.value);
      if (kept > 0) this.addGold(kept, 'pickup');
    } else if (gameState.potions < this.potionCarry) {
      pk.collect(this.g.time.now);
      gameState.potions += 1;
      EventBus.emit(Events.ITEM_PICKED, { kind: pk.kind, value: pk.value });
      EventBus.emit(Events.POTION_CHANGED, { potions: gameState.potions });
    }
  }

  /** 61 P13 §4 자석 흡수 대상: 주인공 바디 중심 · 물약은 가득이면 끌지 않는다 */
  magnet(): PickupMagnet | null {
    const pl = this.g.player;
    if (!pl?.active || gameState.gameOver) return null;
    const c = pl.body.center;
    return { x: c.x, y: c.y, ok: (kind) => kind === 'gold' || gameState.potions < this.potionCarry };
  }

  /** 물약 최대 소지 = 기본 + 영구 강화 */
  get potionCarry(): number {
    return ECONOMY.drops.potion.maxCarry + gameState.meta.potionCarry + (this.g.build?.potionMaxAdd() ?? 0);
  }

  addGold(amount: number, source?: GoldChangedPayload['source']): void {
    gameState.gold += amount;
    EventBus.emit(Events.GOLD_CHANGED, {
      gold: gameState.gold,
      delta: amount,
      ...(source ? { source } : {}),
    } satisfies GoldChangedPayload);
  }

  /** 47라운드 구조물 지불 (궤짝·잔·판돈 등) */
  spendGold(amount: number): void {
    if (amount <= 0) return;
    gameState.gold = Math.max(0, gameState.gold - amount);
    EventBus.emit(Events.GOLD_CHANGED, { gold: gameState.gold, delta: -amount });
  }

  usePotion(): void {
    if (gameState.potions <= 0 || gameState.hp >= gameState.maxHp) return;
    // 57라운드 깨진 잔 저주: 독주 사용 불가
    if (this.g.build && !this.g.build.potionAllowed()) return;
    gameState.potions -= 1;
    EventBus.emit(Events.POTION_USED, { potions: gameState.potions });
    this.g.player.heal(ECONOMY.drops.potion.heal, 'potion');
    EventBus.emit(Events.POTION_CHANGED, { potions: gameState.potions });
  }

  // --- 상점 ---

  /** 상점 타일 위에 서 있으면 메뉴를 열고, 벗어나면 닫는다 · 61라운드: 상점 노드 상인 곁에서 E 로도 연다 */
  updateShop(interactPressed = false): void {
    const g = this.g;
    // 48라운드: 상점 노드는 들어서면 바로 (보스 뒤 상점은 출구가 열린 뒤)
    const shopNode = g.nodeKind !== null && Boolean(kindDef(g.nodeKind).shopTiles);
    if (!gameState.exitOpen && !shopNode) return;
    if (shopNode && !this.keeper && g.layout?.arena) this.keeper = new ShopKeeper(g, g.layout.arena.shop);
    if (gameState.route?.choosing) return;
    const onTile = g.world.isShopAt(g.player.x, g.player.y);
    const nearKeeper = this.keeper?.near() ?? false;
    if (!nearKeeper) this.keeperOpened = false;
    if (interactPressed && nearKeeper && !this.shopOpen && !g.menu.isOpen) {
      this.keeperOpened = true;
      this.shopDismissed = false;
      this.openShop();
      return;
    }
    const here = onTile || this.keeperOpened;
    // 53라운드 UI 요청 B1: Esc(cancelKey)로 닫았으면 상점 칸을 벗어났다 다시 들어설 때 연다
    if (!onTile) this.shopDismissed = false;
    if (onTile && !this.shopOpen && !this.shopDismissed && !g.menu.isOpen) this.openShop();
    else if (!here && this.shopOpen) this.closeShop();
  }

  /** 61라운드 단계 2: 상점 상인 E 안내 (상인 반경 밖·상점 노드가 아니면 null) */
  keeperInteractable(): UiInteractable | null {
    const g = this.g;
    if (!this.keeper) return null;
    return this.keeper.interactable(g.layout?.rooms[0]?.id ?? '', !this.shopOpen && !g.menu.isOpen);
  }

  /** 고정 4칸 가격 (60라운드: 2차 묶음 상점이 있으면 E9 할인까지 — ShopMenu.fixedPrice) */
  private price(it: (typeof ECONOMY.shop.items)[number]): number {
    return (
      this.g.bundle?.shop.fixedPrice(it) ??
      Math.round(shopPrice(it, gameState.stageIndex) * this.g.build.shopPriceMult())
    );
  }

  private openShop(): void {
    this.shopOpen = true;
    EventBus.emit(Events.SHOP_OPENED);
    const shop = this.g.bundle?.shop;
    shop?.onOpen();
    const render = () => {
      const fixed = ECONOMY.shop.items.map((it, i) => {
        const price = this.price(it);
        const full = it.id === 'potion' && gameState.potions >= this.potionCarry;
        const name = it.id === 'potion' ? `${STORY.names.potion} +1` : it.name;
        return {
          key: String(i + 1),
          label: name,
          enabled: gameState.gold >= price && !full,
          price: goldCost(price, gameState.gold, STORY.names.gold),
        };
      });
      // 60라운드 (e) 진열 3칸 · 진열 바꾸기 · 궤짝 덤 · 지도 정보 (계약 §14.6 group)
      const lines = shop ? shop.lines(fixed) : fixed;
      this.g.menu.open(
        'shop',
        `${STORY.names.shop}  (${STORY.names.gold} ${gameState.gold}, ${STORY.names.potion} ${gameState.potions})`,
        lines,
        (key) => {
          if (key === SHOP_CANCEL_KEY) {
            this.shopDismissed = true;
            return this.closeShop();
          }
          if (shop?.select(key, render, () => this.closeShop())) return;
          const item = ECONOMY.shop.items[Number(key) - 1];
          if (item) this.buy(item.id, render);
        },
        STORY.ui.hud.shopFooter,
        { cancelKey: SHOP_CANCEL_KEY },
      );
    };
    render();
  }

  closeShop(): void {
    this.shopOpen = false;
    this.keeperOpened = false;
    this.g.menu.close();
    EventBus.emit(Events.SHOP_CLOSED);
  }

  private buy(id: 'heal' | 'sense' | 'stat' | 'potion', rerender: () => void): void {
    const item = ECONOMY.shop.items.find((i) => i.id === id)!;
    const price = this.price(item);
    if (gameState.gold < price) return;
    gameState.gold -= price;
    EventBus.emit(Events.GOLD_CHANGED, { gold: gameState.gold, delta: -price });
    EventBus.emit(Events.SHOP_BOUGHT, { id, price });
    switch (id) {
      case 'heal':
        this.g.player.heal(Math.round(gameState.maxHp * ECONOMY.shop.healFraction), 'shop');
        rerender();
        break;
      case 'potion':
        gameState.potions = Math.min(this.potionCarry, gameState.potions + 1);
        EventBus.emit(Events.POTION_CHANGED, { potions: gameState.potions });
        rerender();
        break;
      case 'sense':
        gameState.senses.sense += 1;
        gameState.pointsPending += 1;
        this.closeShop();
        this.g.progress.openStatChooser(() => {});
        break;
      case 'stat':
        gameState.pointsPending += 1;
        this.closeShop();
        this.g.progress.openStatChooser(() => {});
        break;
    }
  }
}
