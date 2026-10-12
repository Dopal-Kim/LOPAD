import Phaser from 'phaser';
import { UI_SCREEN, type UiBuildState, type UiShopOffer } from '../contract/ui';
import { tagName } from './buildView';
import { debugExpose } from './debug';
import { portraitFit, shopCardPos, shopCardView, stripPrice, type ShopCardView } from './eventView';
import { GlowText } from './glow';
import { diamond, traitIconBox } from './growthArt';
import { ICON, accentHex, icon } from './kit';
import { GRAY, SEPIA, hexToNum } from './theme';
import { SHOP_CARD as C } from './themeLoop2F';

/**
 * 62 루프 2 UI F (계약 D P1-13 `UiSnapshot.shopOffer`): 노점 칸에 다가가면 물건 위에 뜨는 작은 물건 카드.
 *  [그림] 이름 / (유품이면 희귀도 마름모 · 단계·태그) — 한 줄 설명 — [전표] 값 · '[E] 산다'(또는 못 사는 까닭 · 팔렸다).
 * 종이 카드(S3 바탕 · S4 테 · 먹 외곽) + 물건 쪽 꼬리. 월드 위치(물건 윗변 가운데)를 매 프레임 따라간다.
 * 그림: 유품 = 유품 카드 그림 128 → 64 (`traitIconBox` — UI E 유품 카드와 같은 함수) · 물건 = 드랍 시트 80×96 → 40×48.
 */
export class ShopOfferCard {
  private box: Phaser.GameObjects.Container;
  private sig = '';
  private size = { w: C.w, h: 40 };
  private stallId = '';
  private shownAt = 0;

  constructor(private scene: Phaser.Scene) {
    this.box = scene.add.container(0, 0).setDepth(C.depth).setVisible(false);
  }

  /** 매 프레임 (offer 없음·숨김이면 감춘다) */
  update(
    offer: UiShopOffer | null | undefined,
    show: boolean,
    build: UiBuildState | null | undefined,
    si: number,
  ): void {
    if (!offer || !show) {
      if (this.box.visible) this.box.setVisible(false);
      this.stallId = '';
      return;
    }
    const v = shopCardView(offer, (t) => tagName(t, build));
    const sig = JSON.stringify([offer.stallId, v, si]);
    if (sig !== this.sig) {
      this.sig = sig;
      this.layout(v, si);
    }
    const p = shopCardPos(
      offer.screen,
      this.size.w,
      this.size.h,
      UI_SCREEN.WIDTH,
      UI_SCREEN.HEIGHT,
      C.margin,
      C.gap + C.tail,
    );
    this.box.setPosition(p.x, p.y);
    this.drawTail(p.tailX - p.x, p.below);
    // 나타나기: 실제 시각으로 (씬 트윈은 전환·정지 중 멈출 수 있다)
    if (this.box.alpha < 1) this.box.setAlpha(Math.min(1, (performance.now() - this.shownAt) / C.inMs));
    if (!this.box.visible || offer.stallId !== this.stallId) {
      this.stallId = offer.stallId;
      this.box.setVisible(true).setAlpha(0);
      this.shownAt = performance.now();
      debugExpose('shopCard', {
        stallId: offer.stallId,
        name: v.name,
        action: v.action,
        x: p.x,
        y: p.y,
        w: this.size.w,
        h: this.size.h,
      });
    }
  }

  /** 지금 카드가 떠 있는 물건 칸 ('' = 없음) */
  get current(): string {
    return this.box.visible ? this.stallId : '';
  }

  destroy(): void {
    this.box.destroy(true);
  }

  private tail?: Phaser.GameObjects.Graphics;

  private drawTail(tx: number, below: boolean): void {
    const g = this.tail;
    if (!g) return;
    g.clear();
    const h = this.size.h;
    const t = C.tail;
    const ink = hexToNum(GRAY[0]);
    const paper = hexToNum(SEPIA[3]);
    const edge = hexToNum(SEPIA[4]);
    for (let i = 0; i <= t; i++) {
      const half = t - i;
      const y = below ? -1 - i : h + i;
      g.fillStyle(ink, 1).fillRect(tx - half - 1, y, half * 2 + 3, 1);
      if (half > 0) g.fillStyle(i === 0 ? edge : paper, 1).fillRect(tx - half, y, half * 2 + 1, 1);
    }
  }

  private layout(v: ShopCardView, si: number): void {
    const sc = this.scene;
    this.box.removeAll(true);
    const pad = C.pad;
    const w = C.w;
    const bg = sc.add.graphics();
    this.box.add(bg);
    // 그림 칸
    let artW = 0;
    let artH = 0;
    if (v.art?.kind === 'relic' && sc.textures.exists(v.art.key)) {
      const size = 64;
      const parts = traitIconBox(sc, v.art.key, pad + 1, pad + 1, size, hexToNum(SEPIA[4]), 0, hexToNum(SEPIA[1]));
      if (parts) {
        this.box.add(parts);
        artW = size + 2;
        artH = size + 2;
      }
    } else if (v.art?.kind === 'item' && sc.textures.exists(v.art.key)) {
      // 드랍 시트는 잘린 아틀라스 — 그림(잘린 부분)을 칸에 아래 맞춤. 칸에 1배로 들면 1배(키트 밀도), 아니면 0.5배(월드 밀도)
      const img = sc.add.image(0, 0, v.art.key, v.art.frame).setOrigin(0, 0);
      const f = img.frame;
      const s1 = f.width <= C.artW && f.height <= C.artH - 2;
      const scale = s1 ? 1 : 0.5;
      img.setScale(scale);
      const fit = portraitFit(
        { realW: f.realWidth, realH: f.realHeight, trimX: f.x, trimY: f.y, w: f.width, h: f.height },
        { x: pad, y: pad, w: C.artW, h: C.artH },
        scale,
        1,
      );
      img.setPosition(fit.x, fit.y).setCrop(fit.crop.x, fit.crop.y, fit.crop.w, fit.crop.h);
      // 그림 아래 그늘 한 줄 (노점 위에 놓인 느낌)
      const shade = sc.add.graphics();
      shade.fillStyle(hexToNum(SEPIA[2]), 1).fillRect(pad + 4, pad + C.artH - 1, C.artW - 8, 1);
      this.box.add([shade, img]);
      artW = C.artW;
      artH = C.artH;
    }
    const tx = artW ? pad + artW + 6 : pad;
    const textW = w - tx - pad;
    const name = new GlowText(sc, tx, pad - 2, v.name, 'page_title', { wrap: textW, stageIndex: si });
    this.box.add(name);
    let ty = pad - 2 + name.displayHeight;
    if (v.rarityRank > 0) {
      const marks = sc.add.graphics();
      const r = 3;
      const full = hexToNum(accentHex(sc, si, v.rarityRank >= 4 ? 24 : 21));
      for (let k = 0; k < 4; k++)
        diamond(
          marks,
          tx + r + k * (r * 2 + 2),
          ty + r + 2,
          r,
          k < v.rarityRank ? full : hexToNum(SEPIA[4]),
          k < v.rarityRank,
        );
      this.box.add(marks);
      ty += r * 2 + 4;
    }
    if (v.meta) {
      const meta = new GlowText(sc, tx, ty, v.meta, 'page_faint', { wrap: textW });
      this.box.add(meta);
      ty += meta.displayHeight;
    }
    let y = Math.max(pad + artH, ty) + 4;
    if (v.line) {
      const line = new GlowText(sc, pad - 2, y, v.line, 'page_body', { wrap: w - pad * 2 + 4, stageIndex: si });
      this.box.add(line);
      y += line.displayHeight + 2;
    }
    // 아래 줄: 값 · 사기
    const rowY = y + 2;
    let px = pad - 1;
    if (v.price > 0 && !v.sold) {
      const coin = icon(sc, px, rowY - 1, ICON.gold);
      const amt = new GlowText(sc, px + 17, rowY, String(v.price), v.affordable ? 'page_selected' : 'page_faint', {
        stageIndex: si,
      });
      this.box.add([coin, amt]);
      if (!v.affordable) coin.setAlpha(0.55);
      px += 17 + amt.displayWidth;
    }
    y = rowY + 16;
    if (v.action && v.usable) {
      // '[E] 산다' — 값 줄 오른쪽
      const act = new GlowText(sc, 0, rowY, v.action, 'page_selected', { stageIndex: si });
      act.setPosition(Math.max(px + 8, w - pad + 2 - act.displayWidth), rowY);
      this.box.add(act);
    } else if (v.action) {
      // 못 사는 까닭 · 팔렸다 — 값 줄 아래 한 줄 (까닭 끝의 값은 왼쪽 전표 아이콘과 겹치므로 뗀다)
      const reason = v.price > 0 ? stripPrice(v.action, v.price) : v.action;
      const act = new GlowText(sc, 0, 0, reason, 'page_faint', { wrap: w - pad * 2 + 4, align: 'right' });
      if (v.price > 0 && !v.sold) {
        act.setPosition(w - pad + 2 - act.displayWidth, y);
        y += act.displayHeight;
      } else act.setPosition(w - pad + 2 - act.displayWidth, rowY);
      this.box.add(act);
    }
    const h = y + pad - 2;
    this.size = { w, h };
    // 종이 카드: 먹 외곽 1 · S4 테 1 · S3 바탕 · 아래 그늘 줄
    bg.fillStyle(hexToNum(GRAY[0]), 0.45).fillRect(2, 2, w, h);
    bg.fillStyle(hexToNum(GRAY[0]), 1).fillRect(-1, -1, w + 2, h + 2);
    bg.fillStyle(hexToNum(SEPIA[4]), 1).fillRect(0, 0, w, h);
    bg.fillStyle(hexToNum(SEPIA[3]), 1).fillRect(1, 1, w - 2, h - 2);
    bg.fillStyle(hexToNum(SEPIA[2]), 1).fillRect(1, h - 3, w - 2, 2);
    // 사는 줄 위 괘선
    bg.fillStyle(hexToNum(SEPIA[2]), 1).fillRect(pad, rowY - 3, w - pad * 2, 1);
    this.tail = sc.add.graphics();
    this.box.add(this.tail);
  }
}
