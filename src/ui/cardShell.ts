import Phaser from 'phaser';
import { GlowText } from './glow';
import { UI_SCREEN, type UiMenu } from '../contract/ui';
import { KIT, NinePanel, SLICE, book, inkPanel, rule } from './kit';
import { CardRow, cancelText, menuCloseButton, type CardPage, type CardPageCtx, type CardSlot } from './MenuCards';
import { swatch } from './StructureHud';
import { GRAY, LAYOUT, SEPIA, hexToNum } from './theme';

/** 카드 껍데기 수치 (CHOICE_CARD · GROWTH_CARD 가 같은 이름으로 갖는다) */
export interface ShellSpec {
  pad: number;
  tabH: number;
  tabTop: number;
  stripe: number;
  lift: number;
  shadow: number;
  shadowLift: number;
  shadowAlpha: number;
  focusSlot: number;
  shakePx: number;
  shakeMs: number;
}

export interface ShellOpts {
  key: string;
  hotkey: string;
  enabled: boolean;
  /** 머리표 탭 글 · 띠 색(강조 슬롯) */
  head: string;
  headSlot: number;
  /** 고름 자리가 바뀔 때 (이름 글자 스타일 등) */
  onPaint?: (sel: boolean) => void;
}

export type ShellSlot = CardSlot & { box: Phaser.GameObjects.Container };

/**
 * 선택 카드 한 장의 껍데기 (60 Q38 3지선다 카드에서 떼어 냄 — 61 단계 4 P12 성장 카드와 같이 쓴다).
 * 그림자(바깥) → Container[종이 9-slice · 질감 · 머리표 탭(잉크 + 띠) · 왼쪽 위 키 [1] · 내용] → 고름 테(바깥).
 * 버튼 규약: Container 가 입력을 받는다. 고름 자리 = 들림 + 강조 테 2px, 못 고르는 카드는 흐림·흔들림.
 * `content` 는 카드 왼쪽 위 기준 지역 좌표로 놓은 것들.
 */
export function cardShell(
  scene: Phaser.Scene,
  C: ShellSpec,
  x: number,
  y: number,
  cw: number,
  ch: number,
  o: ShellOpts,
  content: Phaser.GameObjects.GameObject[],
): ShellSlot {
  const shadow = scene.add.graphics().setDepth(1);
  const paper = new NinePanel(scene, 0, 0, KIT.panelPaper, SLICE.panelPaper, cw, ch);
  const inset = SLICE.panelPaper.inner;
  const tile = scene.add.tileSprite(inset, inset, cw - inset * 2, ch - inset * 2, KIT.paperTile).setOrigin(0, 0);
  const head = new GlowText(scene, 0, 0, o.head, 'ink_body');
  const key = new GlowText(scene, 0, 0, `[${o.hotkey}]`, 'page_body');
  const tabW = head.displayWidth + 16 + C.stripe;
  const tabX = Math.round(cw / 2 - tabW / 2);
  const tab = inkPanel(scene, tabX, C.tabTop, tabW, C.tabH);
  const marks = scene.add.graphics();
  marks.fillStyle(swatch(scene, 0, { slot: o.headSlot }), 1).fillRect(tabX + 3, C.tabTop + 4, C.stripe, C.tabH - 8);
  head.setPosition(tabX + 6 + C.stripe + 2, C.tabTop + Math.round((C.tabH - head.displayHeight) / 2));
  key.setPosition(C.pad - 6, C.tabTop + Math.round((C.tabH - key.displayHeight) / 2));
  const frame = scene.add.graphics().setDepth(3);
  const box = scene.add
    .container(x, y, [paper, tile, tab, marks, head, key, ...content])
    .setSize(cw, ch)
    .setDepth(2);
  box.setInteractive(new Phaser.Geom.Rectangle(cw / 2, ch / 2, cw, ch), Phaser.Geom.Rectangle.Contains);
  if (box.input) box.input.cursor = o.enabled ? 'pointer' : 'default';
  let shakeTween: Phaser.Tweens.Tween | null = null;
  return {
    key: o.key,
    hotkey: o.hotkey,
    enabled: o.enabled,
    box,
    paint: (sel) => {
      const lifted = sel && o.enabled;
      const top = lifted ? y - C.lift : y;
      box.setY(top).setAlpha(o.enabled ? 1 : LAYOUT.disabledAlpha);
      const off = lifted ? C.shadowLift : C.shadow;
      shadow
        .clear()
        .fillStyle(hexToNum(SEPIA[0]), C.shadowAlpha)
        .fillRect(x + off, top + off, cw, ch);
      frame.clear();
      if (sel)
        frame.lineStyle(2, swatch(scene, 0, { slot: C.focusSlot }), 1).strokeRect(x - 1, top - 1, cw + 2, ch + 2);
      else frame.lineStyle(1, hexToNum(GRAY[0]), 1).strokeRect(x - 0.5, top - 0.5, cw + 1, ch + 1);
      o.onPaint?.(sel);
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
}

/**
 * 카드 화면 페이지 틀: 일기장 한 쪽(제목 · 괘선 · footer) + 잉크 탁자 깔개(matW×matH) + 그만두기 줄 · 조작 안내.
 * 깔개 안 카드 자리를 돌려주고, 카드를 다 만든 뒤 `done(slots)` 가 고르기(CardRow)를 붙인다. 화면을 넘으면 null.
 */
export function cardPage(
  scene: Phaser.Scene,
  m: UiMenu,
  ctx: CardPageCtx,
  mat: { w: number; h: number; pad: number },
  hintText: string,
  maxPageH: number,
): { left: number; top: number; done(slots: ShellSlot[]): CardPage } | null {
  const W = UI_SCREEN.WIDTH;
  const H = UI_SCREEN.HEIGHT;
  const { stageIndex } = ctx;
  const title = new GlowText(scene, 0, 0, m.title, 'page_title', { scale: 2 }).setDepth(1);
  const footer = m.footer
    ? new GlowText(scene, 0, 0, m.footer, 'page_faint', { wrap: mat.w, align: 'center' }).setDepth(1)
    : null;
  const hint = new GlowText(scene, 0, 0, hintText, 'page_faint').setDepth(1);
  const close = m.cancelKey ? menuCloseButton(scene, stageIndex, () => ctx.send(m.cancelKey!)) : null;
  const cancel = cancelText(scene, m, stageIndex);
  const closeRoom = close ? (close.width + 8) * 2 : 0;
  const contentW = Math.max(mat.w, title.displayWidth + closeRoom, footer?.displayWidth ?? 0, hint.displayWidth);
  const pageW = Math.min(W - 64, Math.max(420, contentW + PAGE_PAD_X * 2));
  const footerH = footer ? footer.displayHeight + 8 : 0;
  const cancelH = cancel ? 18 + 6 : 0;
  const pageH = 16 + title.displayHeight + 8 + 4 + 14 + footerH + mat.h + 10 + cancelH + hint.displayHeight + 14;
  if (pageH > maxPageH || mat.w > W - 64 - PAGE_PAD_X * 2) return null;
  const bk = book(scene, Math.round(W / 2), Math.round(H / 2), pageW, pageH, 1, `menu:${m.id}`);
  const pg = bk.pages[0];
  let y = pg.y + 16;
  title.placeCenter(pg.x + pageW / 2, y);
  close?.setPosition(pg.x + pageW - 12 - close.width, pg.y + 12);
  y += title.displayHeight + 8;
  rule(scene, pg.x + PAGE_PAD_X, y, pageW - PAGE_PAD_X * 2).setDepth(1);
  y += 4 + 14;
  if (footer) {
    footer.placeCenter(pg.x + pageW / 2, y);
    y += footerH;
  }
  const matX = Math.round(pg.x + pageW / 2 - mat.w / 2);
  inkPanel(scene, matX, y, mat.w, mat.h).setDepth(1);
  const matY = y;
  return {
    left: matX + mat.pad,
    top: matY + mat.pad,
    done: (slots) => {
      let yy = matY + mat.h + 10;
      if (cancel) {
        cancel.text.placeCenter(pg.x + pageW / 2, yy);
        yy += cancelH;
      }
      hint.placeCenter(pg.x + pageW / 2, yy);
      const row = new CardRow(scene, slots, cancel, ctx.send, ctx.keepCursor);
      slots.forEach((s, i) => s.box.on('pointerover', () => row.hover(i)).on('pointerdown', () => row.choose(i)));
      return { row, bottom: { x: pg.x + pageW / 2, y: pg.y + pageH } };
    },
  };
}

/** 페이지 안 가로 여백 */
const PAGE_PAD_X = 24;
