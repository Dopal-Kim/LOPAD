/**
 * 경제: 처치 드랍 · 줍기 · 골드 · 물약 · 상점 타일(메뉴 열기/닫기·구매).
 */
import { EventBus, Events } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { ECONOMY, STORY } from '../../data';
import type { Mob } from '../../objects/Mob';
import type { Pickup } from '../../objects/Pickup';
import { rollGold, shopPrice } from '../../systems/economy';
import { kindDef } from '../../systems/route';
import type { Game } from '../Game';

export class Economy {
  shopOpen = false;

  constructor(private readonly g: Game) {}

  dropLoot(mob: Mob, goldMult = 1): void {
    const G = ECONOMY.gold;
    const gold = Math.round(rollGold(mob.goldValue, G.variance, this.g.rng) * goldMult);
    this.spawnPickup(mob.x, mob.y, 'gold', gold);
    if (this.g.rng.chance(ECONOMY.drops.potion.chance)) this.spawnPickup(mob.x + 10, mob.y, 'potion', 1);
  }

  spawnPickup(x: number, y: number, kind: 'gold' | 'potion', value: number): void {
    const g = this.g;
    const pk = g.pickups.get() as Pickup | null;
    if (!pk) return;
    const jx = (g.rng.next() - 0.5) * 12;
    const jy = (g.rng.next() - 0.5) * 12;
    pk.spawn(x + jx, y + jy, kind, value, ECONOMY.gold.dropLifeMs, g.time.now);
  }

  onPickup(pk: Pickup): void {
    if (!pk.active) return;
    if (pk.kind === 'gold') {
      pk.deactivate();
      // 47라운드 1-3: 빚이 있으면 일부 자동 상환
      const kept = this.g.structures.onGoldPickup(pk.value);
      if (kept > 0) this.addGold(kept);
    } else if (gameState.potions < this.potionCarry) {
      pk.deactivate();
      gameState.potions += 1;
      EventBus.emit(Events.ITEM_PICKED, { kind: pk.kind, value: pk.value });
      EventBus.emit(Events.POTION_CHANGED, { potions: gameState.potions });
    }
  }

  /** 물약 최대 소지 = 기본 + 영구 강화 */
  get potionCarry(): number {
    return ECONOMY.drops.potion.maxCarry + gameState.meta.potionCarry;
  }

  addGold(amount: number): void {
    gameState.gold += amount;
    EventBus.emit(Events.GOLD_CHANGED, { gold: gameState.gold, delta: amount });
  }

  /** 47라운드 구조물 지불 (궤짝·잔·판돈 등) */
  spendGold(amount: number): void {
    if (amount <= 0) return;
    gameState.gold = Math.max(0, gameState.gold - amount);
    EventBus.emit(Events.GOLD_CHANGED, { gold: gameState.gold, delta: -amount });
  }

  usePotion(): void {
    if (gameState.potions <= 0 || gameState.hp >= gameState.maxHp) return;
    gameState.potions -= 1;
    EventBus.emit(Events.POTION_USED, { potions: gameState.potions });
    this.g.player.heal(ECONOMY.drops.potion.heal);
    EventBus.emit(Events.POTION_CHANGED, { potions: gameState.potions });
  }

  // --- 상점 ---

  /** 상점 타일 위에 서 있으면 메뉴를 열고, 벗어나면 닫는다 */
  updateShop(): void {
    const g = this.g;
    // 48라운드: 상점 노드는 들어서면 바로 (보스 뒤 상점은 출구가 열린 뒤)
    const shopNode = g.nodeKind !== null && Boolean(kindDef(g.nodeKind).shopTiles);
    if (!gameState.exitOpen && !shopNode) return;
    if (gameState.route?.choosing) return;
    const onTile = g.world.isShopAt(g.player.x, g.player.y);
    if (onTile && !this.shopOpen && !g.menu.isOpen) this.openShop();
    else if (!onTile && this.shopOpen) this.closeShop();
  }

  private openShop(): void {
    this.shopOpen = true;
    EventBus.emit(Events.SHOP_OPENED);
    const render = () => {
      const lines = ECONOMY.shop.items.map((it, i) => {
        const price = shopPrice(it, gameState.stageIndex);
        const full = it.id === 'potion' && gameState.potions >= this.potionCarry;
        const name = it.id === 'potion' ? `${STORY.names.potion} +1` : it.name;
        return {
          key: String(i + 1),
          label: `${name}  ${price} ${STORY.names.gold}`,
          enabled: gameState.gold >= price && !full,
        };
      });
      this.g.menu.open(
        'shop',
        `${STORY.names.shop}  (${STORY.names.gold} ${gameState.gold}, ${STORY.names.potion} ${gameState.potions})`,
        lines,
        (key) => this.buy(ECONOMY.shop.items[Number(key) - 1].id, render),
        STORY.ui.hud.shopFooter,
      );
    };
    render();
  }

  closeShop(): void {
    this.shopOpen = false;
    this.g.menu.close();
    EventBus.emit(Events.SHOP_CLOSED);
  }

  private buy(id: 'heal' | 'sense' | 'stat' | 'potion', rerender: () => void): void {
    const item = ECONOMY.shop.items.find((i) => i.id === id)!;
    const price = shopPrice(item, gameState.stageIndex);
    if (gameState.gold < price) return;
    gameState.gold -= price;
    EventBus.emit(Events.GOLD_CHANGED, { gold: gameState.gold, delta: -price });
    EventBus.emit(Events.SHOP_BOUGHT, { id, price });
    switch (id) {
      case 'heal':
        this.g.player.heal(Math.round(gameState.maxHp * ECONOMY.shop.healFraction));
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
