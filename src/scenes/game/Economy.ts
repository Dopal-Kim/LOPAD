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
import type { FocusSource } from '../../systems/interactFocus';
import {
  UI_EVENTS,
  __system,
  type UiEventScene,
  type UiInteractable,
  type UiMenuLine,
  type UiShopOffer,
  type UiShopPurchased,
} from '../../contract/ui';
import { BUNDLE2 } from '../../data/bundle2';
import { curseDef } from '../../data/build';
import { fill } from '../../systems/story';
import { ShopStalls } from './ShopStalls';
import type { Game } from '../Game';
import { ShopKeeper } from './ShopKeeper';
import { creditLine, merchantScene } from './shopTalkUi';

/** 53라운드 UI 요청 B1: 상점 메뉴 그만두기 key (UI 가 Esc·닫기를 select('shop', '0') 으로 보낸다) */
export const SHOP_CANCEL_KEY = '0';
/** 62 D (P1-13): 상인 외상 = 저주 '외상' (data/curses.json credit) */
const SHOP_CREDIT_CURSE = 'credit';

export class Economy {
  shopOpen = false;
  /** Esc 로 닫은 뒤 상점 칸을 벗어날 때까지 다시 열지 않는다 */
  private shopDismissed = false;
  /** 61라운드 단계 2: 상점 노드 상인 (E 로 연다) · 상인 E 로 연 상점인지 (상인 곁을 떠나면 닫는다) */
  private keeper: ShopKeeper | null = null;
  private keeperOpened = false;
  /** 62 I (P0-N2): 이번 프레임 E 대상이 상인인가 (Game.interactFocus) */
  private keeperFocused = true;
  /** 62 D (P1-13): 장터 노점 칸 */
  private stalls: ShopStalls | null = null;

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

  /**
   * 상점 타일 위에 서 있으면 메뉴를 열고, 벗어나면 닫는다 · 61라운드: 상점 노드 상인 곁에서 E 로도 연다.
   * 62 D (P1-13): 상점 노드는 노점 칸(ShopStalls — 다가가면 카드 + E 로 사기)과 종군 상인(E = 말 걸기: 다시 진열·외상)으로 —
   * 칸을 밟아 여는 글자 목록은 노점이 없는 상점(보스 뒤 등)에만 남는다
   */
  updateShop(interactPressed = false): void {
    const g = this.g;
    // 48라운드: 상점 노드는 들어서면 바로 (보스 뒤 상점은 출구가 열린 뒤)
    const shopNode = g.nodeKind !== null && Boolean(kindDef(g.nodeKind).shopTiles);
    if (!gameState.exitOpen && !shopNode) return;
    if (shopNode && !this.keeper && g.layout?.arena) {
      this.keeper = new ShopKeeper(g, g.layout.arena.shop);
      this.g.bundle?.shop.onOpen();
      this.stalls = new ShopStalls(
        g,
        { lines: () => this.shopLines(), pick: (k, after) => this.shopPick(k, after), busy: () => this.stallBusy() },
        g.layout.arena.shop,
      );
    }
    if (gameState.route?.choosing) return;
    this.checkCreditRepaid();
    const nearKeeper = this.keeper?.near() ?? false;
    if (!nearKeeper) this.keeperOpened = false;
    if (interactPressed && nearKeeper && this.keeperFocused && !this.shopOpen && !g.menu.isOpen) {
      this.openTalk();
      return;
    }
    if (this.stalls && this.stalls.count > 0) {
      // 62 I: 노점이 E 대상이 아니면 stalls 가 스스로 쉰다 (상인·구조물·소품이 더 가까움)
      this.stalls.update(interactPressed && !g.menu.isOpen);
      if (this.shopOpen && !nearKeeper && !this.keeperOpened) this.closeShop();
      return;
    }
    const onTile = g.world.isShopAt(g.player.x, g.player.y);
    const here = onTile || this.keeperOpened;
    // 53라운드 UI 요청 B1: Esc(cancelKey)로 닫았으면 상점 칸을 벗어났다 다시 들어설 때 연다
    if (!onTile) this.shopDismissed = false;
    if (onTile && !this.shopOpen && !this.shopDismissed && !g.menu.isOpen) this.openShop();
    else if (!here && this.shopOpen) this.closeShop();
  }

  /** 62 D: 노점에서 지금 살 수 없는가 (메뉴·전환·전투) */
  private stallBusy(): boolean {
    const g = this.g;
    return g.menu.isOpen || g.transitioning || g.director.inCombat || Boolean(gameState.route?.choosing);
  }

  /** 61라운드 단계 2: 상점 상인 E 안내 · 62 D: 상인 반경 밖이면 노점 칸 안내 (상점 노드가 아니면 null) */
  keeperInteractable(): UiInteractable | null {
    const g = this.g;
    if (!this.keeper) return null;
    const roomId = g.layout?.rooms[0]?.id ?? '';
    const keeper = this.keeperFocused ? this.keeper.interactable(roomId, !this.shopOpen && !g.menu.isOpen) : null;
    return keeper ?? this.stalls?.interactable(roomId) ?? null;
  }

  /** 62 I (P0-N2): E 대상 고르기 후보 — 상인 (반경 안이면 거리) */
  keeperFocusDist(): number | null {
    return this.keeper?.near() ? this.keeper.dist() : null;
  }

  /** 62 I: E 대상 고르기 후보 — 노점 칸 */
  stallFocusDist(): number | null {
    return this.stalls?.focusDist() ?? null;
  }

  /** 62 I: 이번 프레임 E 대상 (상인·노점만 받는다) */
  setFocus(src: FocusSource | null): void {
    this.keeperFocused = src === 'keeper';
    if (this.stalls) this.stalls.focused = src === 'stall';
  }

  /** 62 D (P1-13): 노점 카드 (계약 `UiSnapshot.shopOffer`) */
  shopOffer(): UiShopOffer | null {
    // 62 I: 노점이 E 대상일 때만 (상인이 더 가까우면 stalls.focused = false)
    return this.stalls?.offer() ?? null;
  }

  /** 고정 4칸 가격 (60라운드: 2차 묶음 상점이 있으면 E9 할인까지 — ShopMenu.fixedPrice) */
  private price(it: (typeof ECONOMY.shop.items)[number]): number {
    return (
      this.g.bundle?.shop.fixedPrice(it) ??
      Math.round(shopPrice(it, gameState.stageIndex) * this.g.build.shopPriceMult())
    );
  }

  /** 상점 줄 전부 (고정 칸 + 2차 묶음 진열·다시 진열·궤짝·지도 정보 — 계약 §14.6). 62 D: 노점·상인 대사·글자 목록 공용 */
  shopLines(): UiMenuLine[] {
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
    const shop = this.g.bundle?.shop;
    return shop ? shop.lines(fixed) : fixed;
  }

  /** 상점 줄 하나 고르기 (노점 E · 글자 목록 공용). after = 다시 그리기·닫힌 뒤 */
  shopPick(key: string, after: () => void): void {
    const shop = this.g.bundle?.shop;
    const before = gameState.gold;
    const line = this.shopLines().find((l) => l.key === key);
    const done = () => {
      if (gameState.gold < before && line)
        __system.emit(UI_EVENTS.SHOP_PURCHASED, {
          // 62 루프 2 G: 노점 E · 외상 모두 그 줄의 노점 칸 (글자 목록 상점·다시 진열은 null)
          stallId: this.stalls?.stallIdOf(key) ?? null,
          key,
          name: line.label,
          price: before - gameState.gold,
        } satisfies UiShopPurchased);
      after();
    };
    if (shop?.select(key, done, () => (this.shopOpen ? this.closeShop() : done()))) return;
    const item = ECONOMY.shop.items[Number(key) - 1];
    if (item) this.buy(item.id, done);
  }

  private openShop(): void {
    this.shopOpen = true;
    EventBus.emit(Events.SHOP_OPENED);
    this.g.bundle?.shop.onOpen();
    const render = () => {
      this.g.menu.open(
        'shop',
        `${STORY.names.shop}  (${STORY.names.gold} ${gameState.gold}, ${STORY.names.potion} ${gameState.potions})`,
        this.shopLines(),
        (key) => {
          if (key === SHOP_CANCEL_KEY) {
            this.shopDismissed = true;
            return this.closeShop();
          }
          this.shopPick(key, () => (this.shopOpen ? render() : undefined));
        },
        STORY.ui.hud.shopFooter,
        { cancelKey: SHOP_CANCEL_KEY },
      );
    };
    render();
  }

  // --- 62 D (P1-13) 종군 상인 말 걸기: 다시 진열 · 외상 · 그만 ---

  private talks = 0;
  /** 상인 외상(저주 '외상')을 단 뒤 아직 갚지 않음 */
  private creditOpen = false;

  private openTalk(line?: string): void {
    const g = this.g;
    const T = BUNDLE2.shop.talk?.merchant;
    if (!T) return this.openShop();
    if (line === undefined) {
      EventBus.emit(Events.SHOP_TALK);
      this.talks += 1;
    }
    const greet =
      line ??
      (this.talks <= 1
        ? T.greetFirst
        : (T.greetAgain[(this.talks - 2) % Math.max(1, T.greetAgain.length)] ?? T.greetFirst));
    const reroll = this.shopLines().find((l) => l.key === 'reroll');
    const lines: UiMenuLine[] = [];
    if (reroll)
      lines.push({
        ...reroll,
        key: 'reroll',
        label: fill(T.menu.reroll, { n: reroll.price?.amount ?? 0 }),
        group: 'reroll',
      });
    // 62 루프 2 G: 외상 대가 = 저주 아이콘 줄 (detail 글은 '장터' — 용어집)
    lines.push(creditLine(SHOP_CREDIT_CURSE, T.menu.credit));
    lines.push({ key: SHOP_CANCEL_KEY, label: T.menu.leave, enabled: true });
    this.shopOpen = true;
    this.keeperOpened = true;
    g.menu.open(
      'shopTalk',
      T.speaker,
      lines,
      (key) => {
        if (key === SHOP_CANCEL_KEY) {
          this.closeShop();
          this.g.ui.speech(T.speaker, T.leave);
          return;
        }
        if (key === 'reroll') return this.talkReroll();
        if (key === 'credit') return this.talkCredit();
      },
      greet,
      { cancelKey: SHOP_CANCEL_KEY, speaker: T.speaker, event: this.talkScene(greet) },
    );
  }

  /** 62 루프 2 G (UI 요청): 상인 말하기 머리 — 사연 메뉴와 같은 꼴(말하는 이 · 초상 npc_merchant 0프레임 · 첫 마디) */
  private talkScene(greet: string): UiEventScene {
    const T = BUNDLE2.shop.talk!.merchant;
    return merchantScene(T.speaker, greet, this.keeper?.portrait() ?? null);
  }

  private talkReroll(): void {
    const T = BUNDLE2.shop.talk!.merchant;
    const before = gameState.gold;
    const stock = gameState.bundle.shops.find((s) => s.nodeId === (this.g.node?.id ?? ''));
    const maxed = stock !== undefined && stock.rerolls >= BUNDLE2.shop.rerollPrices.length;
    if (maxed) return this.openTalk(T.rerollMax);
    this.shopPick('reroll', () => {});
    this.stalls?.sync();
    this.openTalk(gameState.gold < before ? T.rerollDone : T.poor);
  }

  /** 외상 (62 D 시스템 결정): 노점 물건 하나를 지금 받고, 저주 '외상'(처치 전표 0 · 값 +20%)이 그 노드 수만큼 붙는다 — 저주 하나 동시 규칙 */
  private talkCredit(): void {
    const g = this.g;
    const T = BUNDLE2.shop.talk!.merchant;
    if (gameState.build.curse || !curseDef(SHOP_CREDIT_CURSE)) return this.openTalk(T.creditRefuse);
    const lines = (this.stalls?.creditLines() ?? []).map((l) => ({ ...l, price: undefined }));
    g.menu.open(
      'shopTalk',
      T.speaker,
      [...lines, { key: SHOP_CANCEL_KEY, label: T.menu.leave, enabled: true }],
      (key) => {
        if (key === SHOP_CANCEL_KEY) return this.openTalk(T.creditName);
        const l = this.shopLines().find((x) => x.key === key);
        if (!l?.price) return;
        // 값만큼 상인이 빌려주고 바로 산다 → 저주 '외상'(즉시 전표 이득은 이 외상 몫이라 받지 않는다)
        const price = l.price.amount;
        const card = lines.find((x) => x.key === key)?.label ?? l.label;
        this.addGold(price);
        this.shopPick(key, () => {});
        this.stalls?.sync();
        const goldNow = curseDef(SHOP_CREDIT_CURSE)?.benefits.goldNow ?? 0;
        if (g.build.grantCurse(SHOP_CREDIT_CURSE, { source: 'event' })) {
          if (goldNow > 0) this.spendGold(goldNow);
          this.creditOpen = true;
        }
        this.openTalk(fill(T.creditDone, { item: card }));
      },
      T.creditOffer,
      { cancelKey: SHOP_CANCEL_KEY, speaker: T.speaker, event: this.talkScene(T.creditOffer) },
    );
  }

  /** 외상 저주가 끝났으면 (갚음) 한 줄 */
  private checkCreditRepaid(): void {
    if (!this.creditOpen || gameState.build.curse?.id === SHOP_CREDIT_CURSE) return;
    this.creditOpen = false;
    const T = BUNDLE2.shop.talk?.merchant;
    if (T) this.g.ui.story('notice', T.creditRepaid);
  }

  closeShop(): void {
    if (!this.shopOpen) return;
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
      // 62 D: 감각·능력치 품목은 1층에서 없앴다 (시스템 C — 데이터에 없음)
      default:
        rerender();
        break;
    }
  }
}
