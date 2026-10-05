import Phaser from 'phaser';
import { UI_SCREEN, type UiMenu, type UiMenuLine } from '../contract/ui';
import { GlowText } from './glow';
import { accentHex, book, cursor as makeCursor, rule } from './kit';
import { takeKey } from './keyGate';
import { cardFocusMove } from './structView';
import { structText } from './text';
import { LAYOUT, SEPIA, STRUCT, hexToNum } from './theme';

/**
 * 메뉴 카드 화면 공용 (MenuScene 에서 분리, 60라운드 Q38).
 * - `CardRow`: 카드 n장 + 그만두기 한 칸의 고르기 — 1·2·3 / ←→(A·D) / ↓ 그만두기 칸 + Enter·스페이스 / 마우스(올리면 고름 자리,
 *   누르면 선택), 그만두기 키. 못 고르는 카드는 `reject`(흔들림 등).
 * - `menuCloseButton`: 페이지 오른쪽 위 닫기 버튼 (스킬 버튼 규약 Container → Graphics → 글자).
 * - `showFaceDownCards`: 47라운드 패 탁자(`cards`) — 엎어진 패 n장.
 * 개성·보상·패시브 3지선다 카드는 `MenuChoiceCards.ts`.
 */

/** 카드 한 장 (그리기는 각 화면이, 고르기는 CardRow 가) */
export interface CardSlot {
  key: string;
  /** 61라운드: 누르는 단축키 (없으면 key) */
  hotkey?: string;
  enabled: boolean;
  /** 고름 자리가 이 카드인지에 따라 다시 칠한다 */
  paint(sel: boolean): void;
  /** 못 고르는 카드를 골랐을 때 (선택) */
  reject?(): void;
}

/** 그만두기 칸 (카드 아래 한 줄) */
export interface CardCancel {
  line: UiMenuLine;
  text: GlowText;
}

/** 카드 화면을 그린 결과 */
export interface CardPage {
  row: CardRow;
  /** 페이지 아래 가운데 (Esc 머무름 안내 자리) */
  bottom: { x: number; y: number };
}

/** 카드 화면에 넘기는 것 */
export interface CardPageCtx {
  stageIndex: number;
  /** 같은 메뉴를 다시 그릴 때 지킬 고름 자리 */
  keepCursor: number;
  send(key: string): void;
}

export class CardRow {
  private focus = 0;
  private cursor?: Phaser.GameObjects.Sprite;
  private onKey: (e: KeyboardEvent) => void;

  constructor(
    private scene: Phaser.Scene,
    private slots: CardSlot[],
    private cancel: CardCancel | null,
    private send: (key: string) => void,
    keepCursor: number,
  ) {
    const n = slots.length;
    if (cancel) {
      cancel.text
        .makeInteractive()
        .on('pointerover', () => this.hover(n))
        .on('pointerdown', () => this.choose(n));
      this.cursor = makeCursor(scene).setDepth(4).setVisible(false);
    }
    this.onKey = (e: KeyboardEvent) => {
      if (e.repeat) return;
      // 같은 키 이벤트가 다시 넘어와 다음 메뉴에서 또 고르지 않게 (keyGate.ts)
      if (e.key === 'Enter' || e.key === ' ') {
        if (takeKey(e)) this.choose(this.focus);
        return;
      }
      if (this.cancel && e.key === this.cancel.line.key) {
        if (takeKey(e)) this.choose(n);
        return;
      }
      const idx = this.slots.findIndex((c) => (c.hotkey ?? c.key) === e.key);
      if (idx >= 0) {
        if (takeKey(e)) this.choose(idx);
        return;
      }
      // 그만두기 칸이 없으면 ↓ 로 n 에 가지 않는다
      const next = cardFocusMove(this.focus, n, e.key);
      const to = !this.cancel && next >= n ? this.focus : next;
      if (to !== this.focus && takeKey(e)) this.hover(to);
    };
    scene.input.keyboard?.on('keydown', this.onKey);
    this.focus = Math.max(0, Math.min(this.cancel ? n : n - 1, keepCursor));
    this.render();
  }

  /** 지금 고름 자리 (0..n-1 = 카드, n = 그만두기) */
  focusIndex(): number {
    return this.focus;
  }

  hover(i: number): void {
    if (i === this.focus) return;
    this.focus = i;
    this.render();
  }

  /** i < n: 카드, i === n: 그만두기 */
  choose(i: number): void {
    if (i >= this.slots.length) {
      if (this.cancel?.line.enabled) this.send(this.cancel.line.key);
      return;
    }
    const c = this.slots[i];
    if (!c) return;
    if (c.enabled) this.send(c.key);
    else {
      this.hover(i);
      c.reject?.();
    }
  }

  destroy(): void {
    this.scene.input.keyboard?.off('keydown', this.onKey);
  }

  private render(): void {
    this.slots.forEach((c, i) => c.paint(i === this.focus));
    const onCancel = this.focus >= this.slots.length;
    const t = this.cancel?.text;
    t?.setGlowStyle(onCancel ? 'page_selected' : 'page_unsel');
    if (this.cursor) {
      if (onCancel && t) this.cursor.setVisible(true).setPosition(t.x - 6, t.y + 8);
      else this.cursor.setVisible(false);
    }
  }
}

/**
 * 닫기 버튼 (스킬 버튼 규약: Container → Graphics → 글자). 페이지 오른쪽 위. 누르면 onPress.
 * 반환 Container 의 width 는 버튼 폭.
 */
export function menuCloseButton(
  scene: Phaser.Scene,
  stageIndex: number,
  onPress: () => void,
): Phaser.GameObjects.Container {
  const t = new GlowText(scene, 4, 1, structText('menuClose'), 'page_body', { stageIndex });
  const bw = t.displayWidth + 8;
  const bh = t.displayHeight + 2;
  const g = scene.add.graphics();
  const draw = (hover: boolean) => {
    g.clear();
    g.fillStyle(hexToNum(SEPIA[1]), 1).fillRect(0, 0, bw, bh);
    g.lineStyle(1, hover ? hexToNum(accentHex(scene, stageIndex, 20)) : hexToNum(SEPIA[4]), 1);
    g.strokeRect(0.5, 0.5, bw - 1, bh - 1);
  };
  draw(false);
  const box = scene.add.container(0, 0, [g, t]).setSize(bw, bh).setDepth(2);
  // Container 입력 판정은 지역 좌표 + 폭·높이 절반 (glow.ts makeInteractive 참조)
  box.setInteractive(new Phaser.Geom.Rectangle(bw / 2, bh / 2, bw, bh), Phaser.Geom.Rectangle.Contains);
  if (box.input) box.input.cursor = 'pointer';
  box.on('pointerover', () => draw(true));
  box.on('pointerout', () => draw(false));
  box.on('pointerdown', onPress);
  return box;
}

/** 그만두기 줄 글 ('[0] 그만둔다', 없으면 null) */
export function cancelText(scene: Phaser.Scene, m: UiMenu, stageIndex: number): CardCancel | null {
  const line = m.lines.find((l) => l.key === m.cancelKey);
  if (!line) return null;
  const text = new GlowText(scene, 0, 0, `[${line.key}] ${line.label}`, 'page_unsel', { stageIndex }).setDepth(1);
  return { line, text };
}

// -------------------------------------------------------------------------------------------
/** 패 탁자: 엎어진 패 n장(가로) + 아래 그만두기 줄. 1·2·3 / ←→ + Enter / 클릭, 0·Esc 그만두기 */
export function showFaceDownCards(scene: Phaser.Scene, m: UiMenu, cardLines: UiMenuLine[], ctx: CardPageCtx): CardPage {
  const W = UI_SCREEN.WIDTH;
  const H = UI_SCREEN.HEIGHT;
  const { stageIndex } = ctx;
  const n = cardLines.length;
  const cw = STRUCT.cardW;
  const ch = STRUCT.cardH;
  const gap = STRUCT.cardGap;
  const padX = 24;
  const rowW = n * cw + (n - 1) * gap;

  const title = new GlowText(scene, 0, 0, m.title, 'page_title', { scale: 2, stageIndex }).setDepth(1);
  const footer = m.footer
    ? new GlowText(scene, 0, 0, m.footer, 'page_faint', { wrap: Math.max(rowW, 372), align: 'center' }).setDepth(1)
    : null;
  const hint = new GlowText(scene, 0, 0, structText('cardHint'), 'page_faint').setDepth(1);
  const close = m.cancelKey ? menuCloseButton(scene, stageIndex, () => ctx.send(m.cancelKey!)) : null;
  const cancel = cancelText(scene, m, stageIndex);
  // 카드 아래 이름·설명 (카드 폭으로 줄바꿈) — 높이를 먼저 잰다
  const labels = cardLines.map((l) =>
    new GlowText(scene, 0, 0, l.label, 'page_unsel', { wrap: cw + gap - 8, align: 'center', stageIndex }).setDepth(1),
  );
  const details = cardLines.map((l) =>
    l.detail
      ? new GlowText(scene, 0, 0, l.detail, 'page_faint', { wrap: cw + gap - 8, align: 'center' }).setDepth(1)
      : null,
  );
  const labelH = Math.max(...labels.map((t, i) => t.displayHeight + (details[i]?.displayHeight ?? 0)));
  const closeRoom = close ? (close.width + 8) * 2 : 0;
  const contentW = Math.max(rowW + 8, title.displayWidth + closeRoom, footer?.displayWidth ?? 0, hint.displayWidth);
  const pageW = Math.min(W - 64, Math.max(420, contentW + padX * 2));
  const footerH = footer ? footer.displayHeight + 8 : 0;
  const cancelH = cancel ? 18 + 6 : 0;
  const pageH =
    16 + title.displayHeight + 8 + 4 + 14 + footerH + ch + 8 + labelH + 10 + cancelH + hint.displayHeight + 14;
  const bk = book(scene, Math.round(W / 2), Math.round(H / 2), pageW, pageH, 1, `menu:${m.id}`);
  const pg = bk.pages[0];
  let y = pg.y + 16;
  title.placeCenter(pg.x + pageW / 2, y);
  close?.setPosition(pg.x + pageW - 12 - close.width, pg.y + 12);
  y += title.displayHeight + 8;
  rule(scene, pg.x + padX, y, pageW - padX * 2).setDepth(1);
  y += 4 + 14;
  if (footer) {
    footer.placeCenter(pg.x + pageW / 2, y);
    y += footerH;
  }
  const x0 = Math.round(pg.x + pageW / 2 - rowW / 2);
  const slots: CardSlot[] = [];
  const hovers: (() => void)[] = [];
  const picks: (() => void)[] = [];
  cardLines.forEach((l, i) => {
    const cx = x0 + i * (cw + gap);
    const g = scene.add.graphics();
    const back = new GlowText(scene, 0, 0, structText('cardBack'), 'page_body', { scale: 2, stageIndex });
    back.setPosition(Math.round(cw / 2 - back.displayWidth / 2), Math.round(ch / 2 - back.displayHeight / 2));
    const key = new GlowText(scene, 8, 7, `[${l.key}]`, 'page_body', { stageIndex });
    // 버튼 규약: Container → Graphics → 글자
    const box = scene.add.container(cx, y, [g, back, key]).setSize(cw, ch).setDepth(1);
    box.setInteractive(new Phaser.Geom.Rectangle(cw / 2, ch / 2, cw, ch), Phaser.Geom.Rectangle.Contains);
    if (box.input) box.input.cursor = l.enabled ? 'pointer' : 'default';
    box.on('pointerover', () => hovers[i]());
    box.on('pointerdown', () => picks[i]());
    const label = labels[i];
    label.placeCenter(cx + cw / 2, y + ch + 8);
    const detail = details[i];
    detail?.placeCenter(cx + cw / 2, y + ch + 8 + label.displayHeight);
    label
      .makeInteractive()
      .on('pointerover', () => hovers[i]())
      .on('pointerdown', () => picks[i]());
    const baseY = y;
    slots.push({
      key: l.key,
      enabled: l.enabled,
      paint: (sel) => {
        paintFaceDown(scene, g, sel, stageIndex);
        box.setY(sel && l.enabled ? baseY - 4 : baseY).setAlpha(l.enabled ? 1 : LAYOUT.disabledAlpha);
        label
          .setGlowStyle(!l.enabled ? 'page_faint' : sel ? 'page_selected' : 'page_unsel')
          .setAlpha(l.enabled ? 1 : LAYOUT.disabledAlpha);
        detail?.setAlpha(l.enabled ? (sel ? 1 : 0.8) : LAYOUT.disabledAlpha);
      },
    });
  });
  y += ch + 8 + labelH + 10;
  if (cancel) {
    cancel.text.placeCenter(pg.x + pageW / 2, y);
    y += cancelH;
  }
  hint.placeCenter(pg.x + pageW / 2, y);
  const row = new CardRow(scene, slots, cancel, ctx.send, ctx.keepCursor);
  slots.forEach((_, i) => {
    hovers[i] = () => row.hover(i);
    picks[i] = () => row.choose(i);
  });
  return { row, bottom: { x: pg.x + pageW / 2, y: pg.y + pageH } };
}

/** 패 뒷면: 가죽(S1) 바탕 + 안쪽 테 S4 + 격자 무늬 S2 (팔레트 안의 색만) */
function paintFaceDown(scene: Phaser.Scene, g: Phaser.GameObjects.Graphics, sel: boolean, stageIndex: number): void {
  const cw = STRUCT.cardW;
  const ch = STRUCT.cardH;
  const accent = hexToNum(accentHex(scene, stageIndex, 20));
  g.clear();
  g.fillStyle(hexToNum(SEPIA[1]), 1).fillRect(0, 0, cw, ch);
  g.lineStyle(1, hexToNum(SEPIA[2]), 1);
  // 45° 격자: 내려가는 선 (d,0)→(d+ch,ch) 과 올라가는 선 (d,ch)→(d+ch,0) 을 카드 안으로 자른다
  for (let d = -ch; d < cw; d += 12) {
    const ax = Math.max(0, d);
    const bx = Math.min(cw, d + ch);
    g.lineBetween(ax, ax - d, bx, bx - d);
    g.lineBetween(ax, ch - (ax - d), bx, ch - (bx - d));
  }
  g.fillStyle(hexToNum(SEPIA[1]), 1).fillRect(cw / 2 - 18, ch / 2 - 18, 36, 36);
  g.lineStyle(1, hexToNum(SEPIA[4]), 1).strokeRect(4.5, 4.5, cw - 9, ch - 9);
  g.lineStyle(sel ? 2 : 1, sel ? accent : hexToNum(SEPIA[0]), 1);
  if (sel) g.strokeRect(1, 1, cw - 2, ch - 2);
  else g.strokeRect(0.5, 0.5, cw - 1, ch - 1);
}
