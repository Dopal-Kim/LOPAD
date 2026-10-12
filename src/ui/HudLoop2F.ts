import Phaser from 'phaser';
import {
  UI_EVENTS,
  UI_SCREEN,
  type UiEnemyIncoming,
  type UiEventResult,
  type UiHiddenReward,
  type UiMenu,
  type UiShopPurchased,
  type UiSnapshot,
} from '../contract/ui';
import { debugExpose } from './debug';
import { EventCutPanel, hiddenRewardAlert, type CutHeads } from './EventCut';
import { ensureEventIcons } from './eventIcons';
import { fill } from './fmt';
import { GlowText } from './glow';
import type { AlertSpec } from './HudAlerts';
import { accentHex } from './kit';
import { ShopOfferCard } from './ShopOfferCard';
import { GRAY, hexToNum } from './theme';
import { SHOP_BUY_FX as FX } from './themeLoop2F';
import { l2fText } from './textLoop2F';
import { WaveArrows } from './WaveArrows';
import { WorldSigns } from './WorldSigns';

export interface Loop2FDeps {
  alert: (spec: AlertSpec) => void;
  stageIndex: () => number;
  /** 전투 묶음 전표 숫자 자리 (없으면 null) */
  goldAt: () => { x: number; y: number } | null;
  snapshot: () => UiSnapshot;
}

/**
 * 62 루프 2 UI F — 시스템 D 계약 2차 패스의 HUD 몫 (HudScene 은 이 층 하나만 부른다):
 *  - 장터 노점 카드 (`snapshot.shopOffer`, ShopOfferCard) · 산 물건 반짝임 + 전표 '−n' (`ui:shop-purchased`)
 *  - 사연 결과 컷 (`ui:event-result`, EventCut) · 숨은 보상 알림 (`ui:hidden-reward` → 알림 줄 '개성' 급)
 *  - 수련장·시험장 허수아비 나무 팻말 (`snapshot.signs`, WorldSigns)
 *  - 무리 들어오는 쪽 가장자리 화살촉 (`ui:enemy-incoming` side, WaveArrows)
 */
export class HudLoop2F {
  private card: ShopOfferCard;
  private signs: WorldSigns;
  private cut: EventCutPanel;
  private arrows: WaveArrows;
  /** 마지막 사연 메뉴 머리말 (결과 컷의 '내준다'·'얻는다') */
  private heads: CutHeads = { costHead: l2fText('costHead'), gainHead: l2fText('gainHead') };
  /** 마지막으로 본 노점 카드 자리 (산 직후 카드가 사라져도 반짝임 시작점) */
  private lastCard: { stallId: string; key: string; x: number; y: number; at: number } | null = null;

  constructor(
    private scene: Phaser.Scene,
    private deps: Loop2FDeps,
  ) {
    ensureEventIcons(scene);
    this.card = new ShopOfferCard(scene);
    this.signs = new WorldSigns(scene);
    this.cut = new EventCutPanel(scene);
    this.arrows = new WaveArrows(scene);
  }

  subscribe(on: <T>(event: string, h: (p: T) => void) => void): void {
    on(UI_EVENTS.MENU_OPEN, (m: UiMenu) => {
      const h = m?.event?.heads;
      if (h) this.heads = { costHead: h.costHead || this.heads.costHead, gainHead: h.gainHead || this.heads.gainHead };
    });
    on(UI_EVENTS.EVENT_RESULT, (r: UiEventResult) => {
      const s = this.deps.snapshot();
      this.cut.show(r, this.heads, this.deps.stageIndex(), s.settings?.keys?.interact ?? s.interactable?.key ?? 'E');
    });
    on(UI_EVENTS.HIDDEN_REWARD, (p: UiHiddenReward) => {
      const spec = hiddenRewardAlert(p, this.deps.stageIndex());
      if (spec) this.deps.alert(spec);
    });
    on(UI_EVENTS.SHOP_PURCHASED, (p: UiShopPurchased) => this.purchased(p));
    on(UI_EVENTS.ENEMY_INCOMING, (p: UiEnemyIncoming) => this.arrows.show(p?.side, this.deps.stageIndex()));
    for (const e of [UI_EVENTS.TRANSITION_BEGIN, UI_EVENTS.RUN_ENDED, UI_EVENTS.ROUTE_NODE_ENTERED])
      on(e, () => {
        this.cut.clear();
        this.arrows.clear();
      });
  }

  /** 매 프레임 — overlay = 메뉴·지도·일시정지가 떠 있음 · walking = 문으로 걸어 나가고 들어오는 중 */
  render(s: UiSnapshot, overlay: boolean, walking: boolean): void {
    const si = Math.max(0, s.stageIndex);
    const offer = s.shopOffer ?? null;
    this.card.update(offer, !overlay && !walking, s.build, si);
    // 물건 자리 (카드 아래 꼬리가 가리키는 물건 윗변 가운데 → 물건 몸 가운데 쯤)
    if (offer && this.card.current)
      this.lastCard = {
        stallId: offer.stallId,
        key: offer.line.key,
        x: Math.round(offer.screen.x),
        y: Math.round(offer.screen.y) + FX.itemDy,
        at: this.scene.time.now,
      };
    this.signs.update(s.signs, !overlay);
  }

  /** 노점 카드가 떠 있는가 (떠 있으면 같은 노점의 E 말풍선은 숨긴다 — 카드에 '[E] 산다') */
  get cardOpen(): boolean {
    return this.card.current !== '';
  }

  destroy(): void {
    this.card.destroy();
    this.signs.destroy();
    this.cut.destroy();
    this.arrows.clear();
  }

  /** 산 물건이 주인공 쪽으로 빨려 드는 반짝임 + 전표 '−n' */
  private purchased(p: UiShopPurchased): void {
    const sc = this.scene;
    const si = this.deps.stageIndex();
    const W = UI_SCREEN.WIDTH;
    const H = UI_SCREEN.HEIGHT;
    const last = this.lastCard;
    const fresh =
      last && sc.time.now - last.at < 1500 && (p.stallId === last.stallId || p.key === last.key || !p.stallId);
    const from = fresh ? { x: last!.x, y: last!.y } : null;
    const to = { x: Math.round(W / 2), y: Math.round(H / 2) + FX.heroDy };
    if (from) {
      const color = hexToNum(accentHex(sc, si, 24));
      const core = hexToNum(accentHex(sc, si, 27));
      for (let i = 0; i < FX.sparks; i++) {
        const g = sc.add.graphics().setDepth(FX.depth);
        const big = i === 0;
        g.fillStyle(hexToNum(GRAY[0]), 0.6).fillRect(-2, -2, big ? 5 : 4, big ? 5 : 4);
        g.fillStyle(big ? core : color, 1).fillRect(-1, -1, big ? 3 : 2, big ? 3 : 2);
        const ox = (i % 3) * 6 - 6;
        const oy = Math.floor(i / 3) * 4 - 2;
        g.setPosition(from.x + ox, from.y + oy);
        // 위로 살짝 떴다가 주인공 쪽으로 (곡선 대신 두 구간)
        sc.tweens.chain({
          targets: g,
          tweens: [
            { y: from.y + oy - 8, duration: 120, ease: 'Sine.Out', delay: i * FX.stagger },
            { x: to.x, y: to.y, scale: 0.5, duration: FX.flyMs, ease: 'Cubic.In' },
          ],
          onComplete: () => g.destroy(),
        });
      }
    }
    // 전표 '−n' (전투 묶음 전표 숫자 옆에서 떠오르며 사라진다)
    const at = this.deps.goldAt();
    if (at && p.price > 0) {
      const t = new GlowText(sc, at.x, at.y, fill(l2fText('goldSpent'), { n: p.price }), 'ink_accent', {
        stageIndex: si,
      }).setDepth(FX.depth);
      sc.tweens.add({
        targets: t,
        y: at.y - FX.goldRise,
        alpha: 0,
        duration: FX.goldMs,
        ease: 'Sine.In',
        onComplete: () => t.destroy(),
      });
    }
    debugExpose('shopBuyFx', { p, from, to, gold: at });
  }
}
