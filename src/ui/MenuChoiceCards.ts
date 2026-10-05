import Phaser from 'phaser';
import { UI_SCREEN, type UiBuildState, type UiMenu } from '../contract/ui';
import { choiceCards, choiceHint, type ChoiceCardData } from './choiceCardView';
import { GlowText } from './glow';
import { KIT, NinePanel, SLICE, accentHex, book, inkPanel, rule } from './kit';
import { cancelText, menuCloseButton, CardRow, type CardPage, type CardPageCtx, type CardSlot } from './MenuCards';
import { r60Text } from './text';
import { GRAY, LAYOUT, SEPIA, hexToNum } from './theme';
import { CHOICE_CARD } from './themeBuild';

/** 가로 여백 (페이지 안) · 줄 사이 */
const PAD_X = 24;
const GAP = { afterTab: 10, afterName: 6, afterPips: 4, afterMeta: 8, afterRule: 10, beforeBottom: 8 } as const;

/** 카드 한 장의 글 (재고 놓기 전) */
interface Face {
  data: ChoiceCardData;
  head: GlowText;
  key: GlowText;
  name: GlowText;
  meta: GlowText | null;
  detail: GlowText | null;
  bottom: GlowText | null;
}

/**
 * 60라운드 Q38 개성·보상·패시브 3지선다 = 카드 3장. 일기장 한 페이지(제목·괘선·footer) 위에 잉크 탁자 깔개(panel_ink)를 펴고
 * 종이 카드(panel_paper + paper_tile) 3장을 나란히 놓는다 — 패 탁자 분위기, 키트만 사용.
 * 카드: 위 가운데 머리표 탭(잉크 + 종류 띠 색, 〔강화〕·〔피의 계약〕·〔각성〕·〔이중 개성〕 …) · 왼쪽 위 키 [1] · 이름(2배) ·
 * 희귀도 마름모 · 희귀도·태그 · 괘선 · 설명 · 아래 잠김 조건(자물쇠)·못 고르는 까닭.
 * 고름 자리 = 카드가 들리고(그림자 멀어짐) 층 강조 테 2px, 이름 page_selected. 못 고르는 카드는 흐림, 고르면 좌우로 흔들림.
 * 조작은 CardRow(1·2·3 / ←→ / Enter / 마우스, 그만두기 줄이 있으면 ↓·키·Esc). 페이지가 화면을 넘으면 null(목록으로 그린다).
 */
export function showChoiceCards(
  scene: Phaser.Scene,
  m: UiMenu,
  build: UiBuildState | null | undefined,
  ctx: CardPageCtx,
  maxPageH: number,
): CardPage | null {
  const W = UI_SCREEN.WIDTH;
  const H = UI_SCREEN.HEIGHT;
  const C = CHOICE_CARD;
  const { stageIndex } = ctx;
  const data = choiceCards(m, build, r60Text);
  const n = data.length;
  const cw = C.w;
  const innerW = cw - C.pad * 2;
  const rowW = n * cw + (n - 1) * C.gap;
  const matW = rowW + C.matPad * 2;

  // ---- 글을 먼저 만들어 높이를 잰다
  const faces: Face[] = data.map((d) => ({
    data: d,
    head: new GlowText(scene, 0, 0, d.head, 'ink_body', { stageIndex }),
    key: new GlowText(scene, 0, 0, `[${d.hotkey}]`, 'page_body', { stageIndex }),
    name: new GlowText(scene, 0, 0, d.name, 'page_unsel', {
      scale: C.nameScale,
      wrap: Math.floor(innerW / C.nameScale),
      align: 'center',
      stageIndex,
    }),
    meta: d.meta ? new GlowText(scene, 0, 0, d.meta, 'page_faint', { wrap: innerW, align: 'center' }) : null,
    detail: d.detail
      ? new GlowText(scene, 0, 0, d.detail, 'page_body', { wrap: innerW, align: 'center', stageIndex })
      : null,
    bottom:
      d.locked || d.note
        ? new GlowText(scene, 0, 0, d.locked || d.note, 'page_faint', { wrap: innerW - 12, align: 'center' })
        : null,
  }));
  const max = (f: (x: Face) => number) => Math.max(0, ...faces.map(f));
  const nameH = max((f) => f.name.displayHeight);
  const pipsH = faces.some((f) => f.data.rarityRank > 0) ? C.pipR * 2 + 1 + GAP.afterPips : 0;
  const metaH = max((f) => (f.meta ? f.meta.displayHeight : 0));
  const detailH = max((f) => (f.detail ? f.detail.displayHeight : 0));
  const bottomH = max((f) => (f.bottom ? f.bottom.displayHeight : 0));
  // 이름·괘선·설명 줄을 세 장이 같은 높이에 두도록 칸마다 가장 큰 값으로
  const ruleY = C.tabTop + C.tabH + GAP.afterTab + nameH + GAP.afterName + pipsH + metaH + GAP.afterMeta;
  const detailY = ruleY + 4 + GAP.afterRule;
  const ch = Math.max(C.minH, detailY + detailH + (bottomH ? GAP.beforeBottom + bottomH : 0) + C.pad);

  const title = new GlowText(scene, 0, 0, m.title, 'page_title', { scale: 2, stageIndex }).setDepth(1);
  const footer = m.footer
    ? new GlowText(scene, 0, 0, m.footer, 'page_faint', { wrap: matW, align: 'center' }).setDepth(1)
    : null;
  const hint = new GlowText(scene, 0, 0, choiceHint(m, r60Text), 'page_faint').setDepth(1);
  const close = m.cancelKey ? menuCloseButton(scene, stageIndex, () => ctx.send(m.cancelKey!)) : null;
  const cancel = cancelText(scene, m, stageIndex);
  const closeRoom = close ? (close.width + 8) * 2 : 0;
  const contentW = Math.max(matW, title.displayWidth + closeRoom, footer?.displayWidth ?? 0, hint.displayWidth);
  const pageW = Math.min(W - 64, Math.max(420, contentW + PAD_X * 2));
  const footerH = footer ? footer.displayHeight + 8 : 0;
  const matH = ch + C.matPad * 2;
  const cancelH = cancel ? 18 + 6 : 0;
  const pageH = 16 + title.displayHeight + 8 + 4 + 14 + footerH + matH + 10 + cancelH + hint.displayHeight + 14;
  if (pageH > maxPageH || matW > W - 64 - PAD_X * 2) return null;

  // ---- 페이지
  const bk = book(scene, Math.round(W / 2), Math.round(H / 2), pageW, pageH, 1, `menu:${m.id}`);
  const pg = bk.pages[0];
  let y = pg.y + 16;
  title.placeCenter(pg.x + pageW / 2, y);
  close?.setPosition(pg.x + pageW - 12 - close.width, pg.y + 12);
  y += title.displayHeight + 8;
  rule(scene, pg.x + PAD_X, y, pageW - PAD_X * 2).setDepth(1);
  y += 4 + 14;
  if (footer) {
    footer.placeCenter(pg.x + pageW / 2, y);
    y += footerH;
  }
  // 탁자 깔개
  const matX = Math.round(pg.x + pageW / 2 - matW / 2);
  inkPanel(scene, matX, y, matW, matH).setDepth(1);
  const x0 = matX + C.matPad;
  const top = y + C.matPad;
  const slots: CardSlotWithBox[] = faces.map((f, i) =>
    buildCard(scene, f, x0 + i * (cw + C.gap), top, ch, { ruleY, detailY, nameH, pipsH }, stageIndex),
  );
  y += matH + 10;
  if (cancel) {
    cancel.text.placeCenter(pg.x + pageW / 2, y);
    y += cancelH;
  }
  hint.placeCenter(pg.x + pageW / 2, y);
  const row = new CardRow(scene, slots, cancel, ctx.send, ctx.keepCursor);
  slots.forEach((s, i) => s.box.on('pointerover', () => row.hover(i)).on('pointerdown', () => row.choose(i)));
  return { row, bottom: { x: pg.x + pageW / 2, y: pg.y + pageH } };
}

type CardSlotWithBox = CardSlot & { box: Phaser.GameObjects.Container };

/**
 * 카드 한 장: 그림자(바깥) → Container[종이 9-slice · 질감 · 머리표 탭 · 띠 · 글 · 희귀도 마름모 · 괘선 · 고름 테] (버튼 규약 —
 * Container 가 입력을 받는다) → 아래 잠김 글·자물쇠(바깥, 흐리지 않음). 못 고르는 카드는 들리지 않는다.
 */
function buildCard(
  scene: Phaser.Scene,
  f: Face,
  x: number,
  y: number,
  ch: number,
  rows: { ruleY: number; detailY: number; nameH: number; pipsH: number },
  stageIndex: number,
): CardSlotWithBox {
  const C = CHOICE_CARD;
  const cw = C.w;
  const d = f.data;
  const accent = (slot: number) => hexToNum(accentHex(scene, stageIndex, slot));
  const shadow = scene.add.graphics().setDepth(1);

  const paper = new NinePanel(scene, 0, 0, KIT.panelPaper, SLICE.panelPaper, cw, ch);
  const inset = SLICE.panelPaper.inner;
  const tile = scene.add.tileSprite(inset, inset, cw - inset * 2, ch - inset * 2, KIT.paperTile).setOrigin(0, 0);
  // 머리표: 잉크 탭(가운데) + 왼쪽 종류 띠
  const tabW = f.head.displayWidth + 16 + C.stripe;
  const tabX = Math.round(cw / 2 - tabW / 2);
  const tab = inkPanel(scene, tabX, C.tabTop, tabW, C.tabH);
  const marks = scene.add.graphics();
  marks.fillStyle(accent(d.headSlot), 1).fillRect(tabX + 3, C.tabTop + 4, C.stripe, C.tabH - 8);
  f.head.setPosition(tabX + 6 + C.stripe + 2, C.tabTop + Math.round((C.tabH - f.head.displayHeight) / 2));
  f.key.setPosition(C.pad - 6, C.tabTop + Math.round((C.tabH - f.key.displayHeight) / 2));
  let ny = C.tabTop + C.tabH + GAP.afterTab;
  f.name.placeCenter(cw / 2, ny + Math.round((rows.nameH - f.name.displayHeight) / 2));
  ny += rows.nameH + GAP.afterName;
  // 희귀도 마름모 (찬 칸 = 희귀도, 전설은 밝은 슬롯)
  if (d.rarityRank > 0) {
    const r = C.pipR;
    const step = r * 2 + C.pipGap;
    const total = C.rarityMax * step - C.pipGap;
    const px0 = Math.round(cw / 2 - total / 2) + r;
    const full = accent(d.rarityRank >= C.rarityMax ? C.rarityTopSlot : C.raritySlot);
    for (let k = 0; k < C.rarityMax; k++) {
      const cx = px0 + k * step;
      const cy = ny + r;
      const pts = [cx, cy - r, cx + r, cy, cx, cy + r, cx - r, cy];
      if (k < d.rarityRank) marks.fillStyle(full, 1).fillPoints(toPoints(pts), true);
      else marks.lineStyle(1, hexToNum(SEPIA[4]), 1).strokePoints(toPoints(pts), true);
    }
  }
  ny += rows.pipsH;
  f.meta?.placeCenter(cw / 2, ny);
  const ruleLine = scene.add.tileSprite(C.pad, rows.ruleY, cw - C.pad * 2, 4, KIT.rule).setOrigin(0, 0);
  f.detail?.placeCenter(cw / 2, rows.detailY);
  // 고름 테는 카드 바깥(흐림과 별개, 잠긴 카드도 또렷하게)
  const frame = scene.add.graphics().setDepth(3);
  const parts: Phaser.GameObjects.GameObject[] = [paper, tile, tab, marks, f.head, f.key, f.name, ruleLine];
  if (f.meta) parts.push(f.meta);
  if (f.detail) parts.push(f.detail);
  // 버튼 규약: Container 가 입력을 받는다 (판정은 지역 좌표 + 폭·높이 절반)
  const box = scene.add.container(x, y, parts).setSize(cw, ch).setDepth(2);
  box.setInteractive(new Phaser.Geom.Rectangle(cw / 2, ch / 2, cw, ch), Phaser.Geom.Rectangle.Contains);
  if (box.input) box.input.cursor = d.enabled ? 'pointer' : 'default';

  // 아래 잠김 조건·못 고르는 까닭 (카드 흐림과 별개로 읽히게 바깥에)
  const lock = scene.add.graphics().setDepth(3);
  if (f.bottom) {
    const by = y + ch - C.pad - f.bottom.displayHeight;
    const lockW = d.locked ? 12 : 0;
    f.bottom.setDepth(3).placeCenter(x + cw / 2 + lockW / 2, by);
    if (d.locked) drawPadlock(lock, f.bottom.x - lockW, by + 3, hexToNum(SEPIA[5]));
  }

  let shakeTween: Phaser.Tweens.Tween | null = null;
  const slot: CardSlotWithBox = {
    key: d.key,
    hotkey: d.hotkey,
    enabled: d.enabled,
    box,
    paint: (sel) => {
      const lifted = sel && d.enabled;
      const top = lifted ? y - C.lift : y;
      box.setY(top).setAlpha(d.enabled ? 1 : LAYOUT.disabledAlpha);
      const off = lifted ? C.shadowLift : C.shadow;
      shadow
        .clear()
        .fillStyle(hexToNum(SEPIA[0]), C.shadowAlpha)
        .fillRect(x + off, top + off, cw, ch);
      frame.clear();
      if (sel) frame.lineStyle(2, accent(C.focusSlot), 1).strokeRect(x - 1, top - 1, cw + 2, ch + 2);
      else frame.lineStyle(1, hexToNum(GRAY[0]), 1).strokeRect(x - 0.5, top - 0.5, cw + 1, ch + 1);
      f.name.setGlowStyle(!d.enabled ? 'page_faint' : sel ? 'page_selected' : 'page_unsel');
    },
    reject: () => {
      shakeTween?.stop();
      box.setX(x);
      shakeTween = scene.tweens.add({
        targets: box,
        x: { from: x - C.shakePx, to: x + C.shakePx },
        duration: C.shakeMs,
        yoyo: true,
        repeat: 1,
        onComplete: () => box.setX(x),
      });
    },
  };
  return slot;
}

function toPoints(xy: number[]): Phaser.Math.Vector2[] {
  const out: Phaser.Math.Vector2[] = [];
  for (let i = 0; i < xy.length; i += 2) out.push(new Phaser.Math.Vector2(xy[i], xy[i + 1]));
  return out;
}

/** 작은 자물쇠 (몸통 7×5 + 고리 5×4 테), 왼쪽 위 (x,y) */
function drawPadlock(g: Phaser.GameObjects.Graphics, x: number, y: number, color: number): void {
  g.fillStyle(color, 1).fillRect(x, y + 4, 7, 5);
  g.lineStyle(1, color, 1).strokeRect(x + 1.5, y + 0.5, 4, 4);
}
