/**
 * 62 루프 2 시스템 D (P1-13 · 계약 UI §22 · art §31.8) 장터 노점: 상점 메뉴 줄(품목 목록은 시스템 C — `Economy.shopLines`)마다
 * 노점 칸(`structures/v3/shop_slot` — idle·near·sold)과 물건 그림(itemAnchor 에 `items/v3/shop_goods`·`potion`·`fire_bottle`)을
 * 월드에 세운다. 다가가면 카드(스냅샷 `shopOffer` = 그 줄 + 그림 + 화면 자리) · E 로 산다(같은 줄 선택 `Economy.shopPick`).
 * 다시 진열·외상은 종군 상인에게 말 걸어서(Economy.openTalk). 데드셀·엔터 더 건전 진열대.
 */
import Phaser from 'phaser';
import { BUNDLE_FX, SHOP_STALL, TILE, entityDepth } from '../../core/Constants';
import { EventBus, Events } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { ECONOMY } from '../../data';
import { BUNDLE2 } from '../../data/bundle2';
import type { UiInteractable, UiMenuLine, UiShopOffer } from '../../contract/ui';
import { worldToLogicalScreen } from '../../systems/display';
import { cardIdOf, goodsArtOf, stallPositions } from '../../systems/loop2d/stallRules';
import { ITEM_ACTION } from '../../systems/bundle2/bundleSheets';
import { spriteLibrary } from '../../systems/sprites/sprites';
import { artScale } from '../../systems/sprites/spriteDefs';
import { frameOpaqueTop } from '../../systems/sprites/opaqueTop';
import { fill } from '../../systems/story';
import { StructureView } from '../../world/StructureView';
import type { Game } from '../Game';

/** 노점에 올리는 줄 묶음 (다시 진열·지도 정보는 상인 대사 / 진열 밖) */
const STALL_GROUPS: readonly (UiMenuLine['group'] | undefined)[] = [undefined, 'fixed', 'display', 'chest'];

interface Stall {
  id: string;
  key: string;
  x: number;
  y: number;
  slot: StructureView;
  item: Phaser.GameObjects.Image | null;
  icon: { key: string; frame: string | number; sheet: string } | null;
  sold: boolean;
}

export interface StallHost {
  lines(): UiMenuLine[];
  pick(key: string, after: () => void): void;
  /** 지금 살 수 없게 막힌 사유 (메뉴·연출 중) */
  busy(): boolean;
}

export class ShopStalls {
  private stalls: Stall[] = [];
  private focus: string | null = null;

  constructor(
    private readonly g: Game,
    private readonly host: StallHost,
    private readonly shop: { x: number; y: number },
  ) {
    this.build();
  }

  private stallLines(): UiMenuLine[] {
    return this.host.lines().filter((l) => STALL_GROUPS.includes(l.group) && l.price !== undefined);
  }

  /** 줄이 달라지면(다시 진열) 칸을 새로 세운다 · 같으면 팔림만 갱신 */
  sync(): void {
    const lines = this.stallLines();
    const same = lines.length === this.stalls.length && lines.every((l, i) => this.stalls[i].key === l.key);
    if (!same) {
      this.clear();
      this.build();
      return;
    }
    lines.forEach((l, i) => this.setSold(this.stalls[i], Boolean(l.soldOut)));
  }

  private build(): void {
    const lines = this.stallLines();
    const pos = stallPositions(this.shop, lines.length);
    lines.forEach((l, i) => {
      const p = pos[i];
      const half = TILE / 2;
      const slot = new StructureView(this.g, {
        sheet: SHOP_STALL.SLOT_SHEET,
        rect: new Phaser.Geom.Rectangle(p.x - half, p.y - TILE, TILE, TILE),
        color: BUNDLE_FX.PROP_COLOR,
        label: '',
        floor: false,
        unlit: true,
      });
      const icon = this.iconOf(l);
      const item = icon ? this.itemSprite(icon, p, slot) : null;
      const st: Stall = { id: `stall:${i + 1}`, key: l.key, x: p.x, y: p.y, slot, item, icon, sold: false };
      this.stalls.push(st);
      this.setSold(st, Boolean(l.soldOut));
    });
  }

  /** 물건 그림 텍스처·프레임 (로드돼 있을 때만) */
  private iconOf(l: UiMenuLine): { key: string; frame: string | number; sheet: string } | null {
    const card = this.cardOf(l);
    // 유품(시스템 C 품목 — 줄 kind 가 무엇이든 카드 문장이 없는 진열 칸)은 꾸러미 그림
    const known = BUNDLE2.shop.cards?.items[card] !== undefined;
    const passive =
      l.kind === 'passive' ||
      Boolean(l.trait) ||
      (l.group === 'display' && (this.displayKind(l.key) === 'passive' || !known));
    const art = goodsArtOf(card, passive);
    if (!art) return null;
    const def = spriteLibrary.sheet(art.sheet, ITEM_ACTION);
    const tex = spriteLibrary.textureKey(art.sheet, ITEM_ACTION);
    if (!def || !tex || !this.g.textures.exists(tex)) return null;
    const dirs = (def as unknown as { directions?: string[] }).directions ?? [];
    const rowIdx = art.row ? Math.max(0, dirs.indexOf(art.row)) : 0;
    const idle = (def.states as Record<string, number[]> | undefined)?.idle?.[0] ?? 0;
    return { key: tex, frame: String(rowIdx * def.frames + idle), sheet: art.sheet };
  }

  private itemSprite(
    icon: { key: string; frame: string | number; sheet: string },
    p: { x: number; y: number },
    slot: StructureView,
  ): Phaser.GameObjects.Image {
    // 노점 itemAnchor (art §31.8 — 피벗 기준 도트) 에 물건 발을 세운다
    const sd = slot.def as unknown as
      { pivot: { x: number; y: number }; itemAnchor?: { x: number; y: number } } | undefined;
    const k = slot.def ? artScale(slot.def) : 1;
    const ax = sd?.itemAnchor ? (sd.itemAnchor.x - sd.pivot.x) * k : 0;
    const ay = sd?.itemAnchor ? (sd.itemAnchor.y - sd.pivot.y) * k : -SHOP_STALL.ITEM_LIFT_PX;
    const def = spriteLibrary.sheet(icon.sheet, ITEM_ACTION);
    const img = this.g.add
      .image(p.x + ax, p.y + ay, icon.key, icon.frame)
      .setDepth(entityDepth(p.y) + 0.5)
      .setScale(def ? artScale(def) : SHOP_STALL.ITEM_SCALE);
    if (def) img.setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight);
    else img.setOrigin(0.5, 1);
    this.g.tweens.add({
      targets: img,
      y: img.y - SHOP_STALL.BOB_PX,
      duration: SHOP_STALL.BOB_MS,
      yoyo: true,
      repeat: -1,
      ease: Phaser.Math.Easing.Sine.InOut,
    });
    return img;
  }

  private cardOf(l: UiMenuLine): string {
    const fixedIds = ECONOMY.shop.items.map((it) => it.id as string);
    const disp = l.group === 'display' ? this.displayId(l.key) : undefined;
    return cardIdOf(l, fixedIds, disp);
  }

  /** 진열 칸 키('d1'…) → 품목 (상점 진열 상태) */
  private displayItem(key: string): { id: string; kind: string } | undefined {
    const B = gameState.bundle;
    const stock = B.shops.find((s) => s.nodeId === (this.g.node?.id ?? ''));
    return stock?.display[Number(key.slice(1)) - 1];
  }

  private displayId(key: string): string | undefined {
    return this.displayItem(key)?.id;
  }

  private displayKind(key: string): string | undefined {
    return this.displayItem(key)?.kind;
  }

  private setSold(s: Stall, sold: boolean): void {
    s.sold = sold;
    if (s.slot.hasState('sold')) s.slot.setState(sold ? 'sold' : this.focus === s.id ? 'near' : 'idle');
    s.item?.setVisible(!sold);
  }

  private nearest(): Stall | null {
    const pl = this.g.player;
    let best: Stall | null = null;
    let bd = SHOP_STALL.RADIUS_TILES * TILE;
    for (const s of this.stalls) {
      const d = Math.hypot(pl.x - s.x, pl.y - s.y);
      if (d <= bd) {
        bd = d;
        best = s;
      }
    }
    return best;
  }

  private lineOf(s: Stall): UiMenuLine | undefined {
    return this.stallLines().find((l) => l.key === s.key);
  }

  /** 매 프레임: 가까운 칸 표지(near) · E 로 사기 */
  update(interactPressed: boolean): void {
    const s = this.nearest();
    const id = s?.id ?? null;
    if (id !== this.focus) {
      const prev = this.stalls.find((x) => x.id === this.focus);
      this.focus = id;
      if (prev && !prev.sold && prev.slot.hasState('near')) prev.slot.setState('idle');
      if (s && !s.sold && s.slot.hasState('near')) s.slot.setState('near');
      EventBus.emit(Events.STALL_FOCUS, { stallId: id });
    }
    if (!interactPressed || !s || s.sold || this.host.busy()) return;
    const l = this.lineOf(s);
    if (!l || !l.enabled) return;
    this.host.pick(l.key, () => this.sync());
  }

  /** 계약 §22 노점 카드 (반경 밖이면 null) */
  offer(): UiShopOffer | null {
    const s = this.nearest();
    if (!s) return null;
    const l = this.lineOf(s);
    if (!l) return null;
    const card = this.cardText(l);
    const usable = l.enabled && !l.soldOut && !this.host.busy();
    const reason = l.soldOut
      ? 'limit'
      : !l.enabled
        ? l.price && !l.price.affordable
          ? 'gold'
          : 'full'
        : this.host.busy()
          ? 'busy'
          : null;
    const T = BUNDLE2.shop.talk?.stall;
    const reasonText =
      reason === 'gold'
        ? fill(T?.short ?? '', { n: l.price?.amount ?? 0 })
        : reason === 'limit'
          ? (T?.sold ?? '')
          : reason
            ? BUNDLE_FX.NOT_READY_TEXT
            : '';
    const top = this.itemTop(s);
    const sc = worldToLogicalScreen(this.g.cameras.main, s.x, top);
    return {
      stallId: s.id,
      line: { ...l, ...card },
      ...(s.icon ? { icon: { key: s.icon.key, frame: s.icon.frame } } : {}),
      buyKey: 'E',
      usable,
      reason,
      reasonText,
      screen: { x: Math.round(sc.x), y: Math.round(sc.y) },
    };
  }

  /**
   * 카드 자리 = 보이는 물건 그림 윗변 (62 루프 2 G — UI 요청: 드랍 시트 칸 80×96 윗변이라 그림보다 약 26 논리 px 위였다).
   * 칸 윗변 + 칸 위쪽 투명 줄 × 배율. 물건 그림이 없으면 노점 칸 윗변
   */
  private itemTop(s: Stall): number {
    if (!s.item || !s.icon) return s.slot.topY;
    const cell = s.item.getTopCenter().y ?? s.slot.topY;
    return cell + frameOpaqueTop(this.g.textures, s.icon.key, s.icon.frame) * Math.abs(s.item.scaleY);
  }

  /** 줄 key → 노점 칸 id (SHOP_PURCHASED.stallId — 노점에 없는 줄이면 null) */
  stallIdOf(key: string): string | null {
    return this.stalls.find((s) => s.key === key)?.id ?? null;
  }

  /** 63 팩 물건 카드 문장 (유품 칸은 시스템 C 줄 그대로) */
  private cardText(l: UiMenuLine): Partial<UiMenuLine> {
    if (l.kind === 'passive' || l.trait) return {};
    const c = BUNDLE2.shop.cards?.items[this.cardOf(l)];
    if (!c) return {};
    return { label: c.name, detail: c.line };
  }

  /** 계약 §9.1 E 안내 (shopStall) */
  interactable(roomId: string): UiInteractable | null {
    const o = this.offer();
    if (!o) return null;
    const T = BUNDLE2.shop.talk?.stall;
    return {
      id: o.stallId,
      kind: 'shopStall',
      name: o.line.label,
      roomId,
      key: 'E',
      actionKey: 'stall.buy',
      action: (T?.buy ?? '[E] 산다').replace(/^\[E\]\s*/, '').replace(/\s*·.*$/, ''),
      cost: o.line.price ? { ...o.line.price } : null,
      hold: null,
      usable: o.usable,
      reason: o.reason,
      reasonText: o.reasonText,
      screen: { ...o.screen },
    };
  }

  /** 외상 고르기 줄 (팔리지 않은 노점 줄 — 전표와 무관하게 고를 수 있다) */
  creditLines(): UiMenuLine[] {
    return this.stallLines()
      .filter((l) => !l.soldOut)
      .map((l) => ({ ...l, ...this.cardText(l), enabled: true }));
  }

  get count(): number {
    return this.stalls.length;
  }

  private clear(): void {
    for (const s of this.stalls) {
      s.slot.destroy();
      if (s.item) {
        this.g.tweens.killTweensOf(s.item);
        s.item.destroy();
      }
    }
    this.stalls = [];
    this.focus = null;
  }

  debug(): Record<string, unknown> {
    return {
      stalls: this.stalls.map((s) => ({ id: s.id, key: s.key, sold: s.sold, icon: s.icon })),
      focus: this.focus,
    };
  }

  destroy(): void {
    this.clear();
  }
}
