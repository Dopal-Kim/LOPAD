import Phaser from 'phaser';
import { UI_EVENTS, UI_SCREEN, uiBus, uiCommands, type UiMenu, type UiMenuLine } from '../contract/ui';
import { buildOf } from './buildView';
import { debugSelect, isDebugMenu, withDebug } from './debug';
import { GlowText } from './glow';
import { accentHex, book, cursor as makeCursor, fontsReady, preloadKit, rule, setupKit } from './kit';
import { UI_SCENE_KEYS } from './keys';
import { resolveMenuEsc } from './escNav';
import { takeKey } from './keyGate';
import { menuLines, wideMenu } from './menuView';
import { cardFocusMove } from './structView';
import { r53Text, structText } from './text';
import { r60Text } from './text';
import { LAYOUT, SEPIA, STRUCT, hexToNum } from './theme';
import { SelectList } from './widgets';

/** 카드 메뉴로 그릴 수 있는 카드 장수 (그 밖이면 일반 목록) */
const CARD_MIN = 2;
const CARD_MAX = 4;
/** 60라운드: 페이지(책 틀 안) 높이 상한 — 넘으면 설명을 접는다 (화면 540 - 틀 32 - 여백) */
const MENU_MAX_PAGE_H = UI_SCREEN.HEIGHT - 32 - 24;
/** 접은 설명 한 칸 높이 (3줄) */
const COMPACT_DETAIL_H = 3 * 16 + 6;
/** Esc 머무름 안내가 떠 있는 시간 (임시값) */
const ESC_STAY_HOLD_MS = 1400;

interface CardView {
  line: UiMenuLine;
  box: Phaser.GameObjects.Container;
  g: Phaser.GameObjects.Graphics;
  label: GlowText;
  detail: GlowText | null;
  baseY: number;
}

/**
 * 보상·패시브·상점·메타·개성 3지선다(evolve)·엔딩 2지선다(ending)·47라운드 구조물 메뉴 공용 일기장 한 페이지.
 * MENU_OPEN 으로 열리고 MENU_CLOSE 로 닫힌다. 제목 page_title(Galmuri11 2배 — 한자 포함 가능) + 괘선,
 * 항목은 SelectList(page_selected/unsel, 커서), detail 은 page_faint, footer 는 page_faint 하단.
 * evolve·ending 은 페이지 최소 폭 520.
 * 47라운드(계약 §9.4): `cancelKey` 가 있으면 Esc·오른쪽 위 닫기 버튼이 `select(id, cancelKey)`.
 * 같은 메뉴(id·structureId)가 다시 오면 커서 자리를 지킨 채 다시 그린다. `cards`(패 탁자)는 엎어진 패 n장으로 그린다.
 * 60라운드(계약 §14.4·§14.6·§14.7): 줄 만들기는 menuView.ts — 칸 종류(〔강화〕·〔피의 계약〕·〔각성〕·〔이중 개성〕)·희귀도·태그·
 * 잠김 조건, 상점 묶음 머리글·가격·팔림. 새 메뉴 id `curse`(필수)·`event`('0')·`mapInfo`('0')·`consumableSwap`(필수)도 같은 목록.
 * 줄이 많아 페이지가 화면을 넘으면 설명을 접고 커서 줄 설명만 목록 아래에 보인다.
 */
export class MenuScene extends Phaser.Scene {
  private menu?: UiMenu;
  private list?: SelectList;
  private pendingClose = false;
  private alive = false;
  // 카드 메뉴 (cards)
  private cards: CardView[] = [];
  private cardFocus = 0;
  private cancelText?: GlowText;
  private cancelLine?: UiMenuLine;
  private cardCursor?: Phaser.GameObjects.Sprite;
  private onCardKey?: (e: KeyboardEvent) => void;
  private onOpen = (m: UiMenu) => {
    this.pendingClose = false;
    this.show(m);
  };
  private onClose = (p: { id: string }) => {
    // 같은 프레임에 다음 메뉴가 열릴 수 있으므로 다음 update 에서 닫는다
    if (this.menu?.id === p.id) this.pendingClose = true;
  };
  /**
   * 51라운드 §6: Esc = 한 단계 뒤로 (`resolveMenuEsc`). 앞 단계가 없는 메뉴는 머무르고 안내 한 줄.
   * cancelKey 는 지금 열린 메뉴(`this.menu` = 마지막 MENU_OPEN)의 값. 같은 Esc 이벤트가 다시 넘어오면 무시한다
   * (53라운드: 갈래 '9' 로 lab 이 다시 열린 뒤 같은 Esc 가 lab 의 '0' 으로 처리돼 메뉴 전체가 닫혔다 — keyGate.ts)
   */
  private onEsc = (e?: KeyboardEvent) => {
    const m = this.menu;
    const a = resolveMenuEsc(m, e, this.pendingClose);
    if (!m || !a) return;
    if (a.kind === 'select') this.send(m, a.key);
    else if (a.kind === 'title') uiCommands.toTitle();
    else this.flashStayHint();
  };
  /** 페이지 아래 가운데 (Esc 머무름 안내 자리) */
  private pageBottom = { x: UI_SCREEN.WIDTH / 2, y: UI_SCREEN.HEIGHT - 40 };
  private stayHint?: GlowText;

  private flashStayHint(): void {
    this.stayHint?.destroy();
    const t = new GlowText(this, 0, 0, r53Text('escStay'), 'ink_faint').setDepth(3);
    t.placeCenter(this.pageBottom.x, this.pageBottom.y + 8);
    this.stayHint = t;
    this.tweens.add({
      targets: t,
      alpha: 0,
      delay: ESC_STAY_HOLD_MS,
      duration: 300,
      onComplete: () => {
        t.destroy();
        if (this.stayHint === t) this.stayHint = undefined;
      },
    });
  }

  constructor() {
    super(UI_SCENE_KEYS.MENU);
  }

  preload(): void {
    preloadKit(this);
  }

  update(): void {
    if (this.pendingClose) {
      this.pendingClose = false;
      this.scene.stop();
    }
  }

  create(data: UiMenu): void {
    this.pendingClose = false;
    this.alive = true;
    this.menu = undefined;
    this.drawn = undefined;
    setupKit(this);
    uiBus.on(UI_EVENTS.MENU_OPEN, this.onOpen);
    uiBus.on(UI_EVENTS.MENU_CLOSE, this.onClose);
    this.input.keyboard?.on('keydown-ESC', this.onEsc);
    this.events.once('shutdown', () => {
      this.alive = false;
      uiBus.off(UI_EVENTS.MENU_OPEN, this.onOpen);
      uiBus.off(UI_EVENTS.MENU_CLOSE, this.onClose);
      this.input.keyboard?.off('keydown-ESC', this.onEsc);
      this.clearCards();
      this.list?.destroy();
      this.list = undefined;
    });
    const first = data;
    fontsReady().then(() => {
      if (this.alive && (this.menu ?? first)) this.show(this.menu ?? first);
    });
    this.menu = first;
  }

  /** 선택 전달 (UI 디버그 가짜 메뉴는 시스템으로 보내지 않는다) */
  private send(m: UiMenu, key: string): void {
    if (isDebugMenu(m)) debugSelect(m, key);
    else uiCommands.select(m.id, key);
  }

  private show(m: UiMenu): void {
    const prev = this.drawn;
    const same = Boolean(prev) && prev!.id === m.id && (prev!.structureId ?? '') === (m.structureId ?? '');
    const keepCursor = same ? (this.list ? this.list.cursorIndex() : this.cardFocus) : 0;
    this.menu = m;
    this.drawn = m;
    this.stayHint = undefined;
    this.children.removeAll(true);
    this.list?.destroy();
    this.list = undefined;
    this.clearCards();
    const cardLines = m.lines.filter((l) => l.key !== m.cancelKey);
    if (m.id === 'cards' && cardLines.length >= CARD_MIN && cardLines.length <= CARD_MAX) {
      this.showCards(m, cardLines, keepCursor);
    } else {
      this.showList(m, keepCursor);
    }
  }
  /** 지금 화면에 그린 메뉴 (show 전에 this.menu 는 create 데이터일 수 있어 따로 둔다) */
  private drawn?: UiMenu;

  private showList(m: UiMenu, keepCursor: number): void {
    const W = UI_SCREEN.WIDTH;
    const H = UI_SCREEN.HEIGHT;
    const snap = withDebug(uiCommands.getUiSnapshot());
    const stageIndex = Math.max(0, snap.stageIndex);
    // 줄 만들기(evolve 설명 중복 제거·시험장 들여쓰기·§14.4 칸 종류·잠김·§14.6 가격·팔림·묶음 머리글)는 menuView.ts
    const lines = menuLines(m, buildOf(snap), r60Text);
    const wide = wideMenu(m);
    const minW = wide ? 520 : 420;
    const maxW = W - 64;
    const padX = 24;
    // 항목·제목·푸터를 먼저 그려 폭을 재고, 페이지는 그 뒤에 깔아(depth 0) 글이 잘리지 않게 한다
    this.list = new SelectList(this, 0, 0, (key) => this.send(m, key), {
      stageIndex,
      detailWrap: maxW - padX * 2 - 40,
    });
    this.list.setLines(lines);
    this.list.setCursorIndex(keepCursor);
    const title = new GlowText(this, 0, 0, m.title, 'page_title', { scale: 2, stageIndex }).setDepth(1);
    const footer = m.footer
      ? new GlowText(this, 0, 0, m.footer, 'page_faint', { wrap: maxW - padX * 2, align: 'center' }).setDepth(1)
      : null;
    const close = m.cancelKey ? this.closeButton(m, stageIndex) : null;
    const closeRoom = close ? (close.width + 8) * 2 : 0;
    const contentW = Math.max(this.list.maxWidth() + 8, title.displayWidth + closeRoom, footer?.displayWidth ?? 0);
    const pageW = Math.min(maxW, Math.max(minW, contentW + padX * 2));
    const titleH = title.displayHeight;
    const footerH = footer ? footer.displayHeight + 10 : 0;
    let listH = this.list.height();
    // 60라운드 §14.6: 상점처럼 줄이 많아 페이지가 화면을 넘으면 설명을 접고, 커서 줄의 설명만 목록 아래 한 칸에 보인다
    let focusDetail: GlowText | null = null;
    let focusH = 0;
    const baseH = 16 + titleH + 8 + 4 + 14 + 10 + footerH + 16;
    if (baseH + listH > MENU_MAX_PAGE_H && lines.some((l) => l.detail)) {
      this.list.setLines(lines.map((l) => ({ ...l, detail: undefined })));
      this.list.setCursorIndex(keepCursor);
      listH = this.list.height();
      focusDetail = new GlowText(this, 0, 0, '', 'page_faint', { wrap: maxW - padX * 2 - 16 }).setDepth(1);
      focusH = COMPACT_DETAIL_H;
    }
    const pageH = baseH + listH + focusH;
    const bk = book(this, Math.round(W / 2), Math.round(H / 2), pageW, pageH, 1, `menu:${m.id}`);
    const pg = bk.pages[0];
    let y = pg.y + 16;
    title.placeCenter(pg.x + pageW / 2, y);
    close?.setPosition(pg.x + pageW - 12 - close.width, pg.y + 12);
    y += titleH + 8;
    rule(this, pg.x + padX, y, pageW - padX * 2).setDepth(1);
    y += 4 + 14;
    this.list.setPosition(pg.x + padX, y).setDepth(1);
    y += listH + 10;
    if (focusDetail) {
      const fd = focusDetail;
      fd.setPosition(pg.x + padX + 16, y - 4);
      this.list.setOnCursor((i) => fd.setText(lines[i]?.detail ?? ''));
      y += focusH;
    }
    footer?.placeCenter(pg.x + pageW / 2, y);
    this.pageBottom = { x: pg.x + pageW / 2, y: pg.y + pageH };
    if (m.id === 'meta') this.input.keyboard?.once('keydown-ENTER', () => uiCommands.select('meta', 'enter'));
  }

  /**
   * 닫기 버튼 (스킬 버튼 규약: Container → Graphics → 글자). 페이지 오른쪽 위. 누르면 select(id, cancelKey).
   * 반환 Container 의 width 는 버튼 폭.
   */
  private closeButton(m: UiMenu, stageIndex: number): Phaser.GameObjects.Container {
    const t = new GlowText(this, 4, 1, structText('menuClose'), 'page_body', { stageIndex });
    const bw = t.displayWidth + 8;
    const bh = t.displayHeight + 2;
    const g = this.add.graphics();
    const draw = (hover: boolean) => {
      g.clear();
      g.fillStyle(hexToNum(SEPIA[1]), 1).fillRect(0, 0, bw, bh);
      g.lineStyle(1, hover ? hexToNum(accentHex(this, stageIndex, 20)) : hexToNum(SEPIA[4]), 1);
      g.strokeRect(0.5, 0.5, bw - 1, bh - 1);
    };
    draw(false);
    const box = this.add.container(0, 0, [g, t]).setSize(bw, bh).setDepth(2);
    // Container 입력 판정은 지역 좌표 + 폭·높이 절반 (glow.ts makeInteractive 참조)
    box.setInteractive(new Phaser.Geom.Rectangle(bw / 2, bh / 2, bw, bh), Phaser.Geom.Rectangle.Contains);
    if (box.input) box.input.cursor = 'pointer';
    box.on('pointerover', () => draw(true));
    box.on('pointerout', () => draw(false));
    box.on('pointerdown', () => {
      if (m.cancelKey) this.send(m, m.cancelKey);
    });
    return box;
  }

  // -------------------------------------------------------------------------------------------
  /** 패 탁자: 엎어진 패 n장(가로) + 아래 그만두기 줄. 1·2·3 / ←→ + Enter / 클릭, 0·Esc 그만두기 */
  private showCards(m: UiMenu, cardLines: UiMenuLine[], keepCursor: number): void {
    const W = UI_SCREEN.WIDTH;
    const H = UI_SCREEN.HEIGHT;
    const stageIndex = Math.max(0, uiCommands.getUiSnapshot().stageIndex);
    const n = cardLines.length;
    const cw = STRUCT.cardW;
    const ch = STRUCT.cardH;
    const gap = STRUCT.cardGap;
    const padX = 24;
    const rowW = n * cw + (n - 1) * gap;

    const title = new GlowText(this, 0, 0, m.title, 'page_title', { scale: 2, stageIndex }).setDepth(1);
    const footer = m.footer
      ? new GlowText(this, 0, 0, m.footer, 'page_faint', { wrap: Math.max(rowW, 372), align: 'center' }).setDepth(1)
      : null;
    const hint = new GlowText(this, 0, 0, structText('cardHint'), 'page_faint').setDepth(1);
    const close = m.cancelKey ? this.closeButton(m, stageIndex) : null;
    this.cancelLine = m.lines.find((l) => l.key === m.cancelKey);
    this.cancelText = this.cancelLine
      ? new GlowText(this, 0, 0, `[${this.cancelLine.key}] ${this.cancelLine.label}`, 'page_unsel', {
          stageIndex,
        })
          .setDepth(1)
          .makeInteractive()
      : undefined;
    // 카드 아래 이름·설명 (카드 폭으로 줄바꿈) — 높이를 먼저 잰다
    const labels = cardLines.map((l) =>
      new GlowText(this, 0, 0, l.label, 'page_unsel', { wrap: cw + gap - 8, align: 'center', stageIndex }).setDepth(1),
    );
    const details = cardLines.map((l) =>
      l.detail
        ? new GlowText(this, 0, 0, l.detail, 'page_faint', { wrap: cw + gap - 8, align: 'center' }).setDepth(1)
        : null,
    );
    const labelH = Math.max(...labels.map((t, i) => t.displayHeight + (details[i]?.displayHeight ?? 0)));
    const closeRoom = close ? (close.width + 8) * 2 : 0;
    const contentW = Math.max(rowW + 8, title.displayWidth + closeRoom, footer?.displayWidth ?? 0, hint.displayWidth);
    const pageW = Math.min(W - 64, Math.max(420, contentW + padX * 2));
    const footerH = footer ? footer.displayHeight + 8 : 0;
    const cancelH = this.cancelText ? 18 + 6 : 0;
    const pageH =
      16 + title.displayHeight + 8 + 4 + 14 + footerH + ch + 8 + labelH + 10 + cancelH + hint.displayHeight + 14;
    const bk = book(this, Math.round(W / 2), Math.round(H / 2), pageW, pageH, 1, `menu:${m.id}`);
    const pg = bk.pages[0];
    let y = pg.y + 16;
    title.placeCenter(pg.x + pageW / 2, y);
    close?.setPosition(pg.x + pageW - 12 - close.width, pg.y + 12);
    y += title.displayHeight + 8;
    rule(this, pg.x + padX, y, pageW - padX * 2).setDepth(1);
    y += 4 + 14;
    if (footer) {
      footer.placeCenter(pg.x + pageW / 2, y);
      y += footerH;
    }
    const x0 = Math.round(pg.x + pageW / 2 - rowW / 2);
    cardLines.forEach((l, i) => {
      const cx = x0 + i * (cw + gap);
      const g = this.add.graphics();
      const back = new GlowText(this, 0, 0, structText('cardBack'), 'page_body', { scale: 2, stageIndex });
      back.setPosition(Math.round(cw / 2 - back.displayWidth / 2), Math.round(ch / 2 - back.displayHeight / 2));
      const key = new GlowText(this, 8, 7, `[${l.key}]`, 'page_body', { stageIndex });
      // 버튼 규약: Container → Graphics → 글자
      const box = this.add.container(cx, y, [g, back, key]).setSize(cw, ch).setDepth(1);
      box.setInteractive(new Phaser.Geom.Rectangle(cw / 2, ch / 2, cw, ch), Phaser.Geom.Rectangle.Contains);
      if (box.input) box.input.cursor = l.enabled ? 'pointer' : 'default';
      box.on('pointerover', () => this.focusCard(i));
      box.on('pointerdown', () => this.chooseCard(i));
      const label = labels[i];
      label.placeCenter(cx + cw / 2, y + ch + 8);
      const detail = details[i];
      detail?.placeCenter(cx + cw / 2, y + ch + 8 + label.displayHeight);
      label
        .makeInteractive()
        .on('pointerover', () => this.focusCard(i))
        .on('pointerdown', () => this.chooseCard(i));
      this.cards.push({ line: l, box, g, label, detail, baseY: y });
    });
    y += ch + 8 + labelH + 10;
    if (this.cancelText) {
      this.cancelText.placeCenter(pg.x + pageW / 2, y);
      this.cancelText.on('pointerover', () => this.focusCard(n)).on('pointerdown', () => this.chooseCard(n));
      y += cancelH;
    }
    hint.placeCenter(pg.x + pageW / 2, y);
    this.cardCursor = makeCursor(this).setDepth(3).setVisible(false);
    this.onCardKey = (e: KeyboardEvent) => {
      if (e.repeat) return;
      // 같은 키 이벤트가 다시 넘어와 다음 메뉴에서 또 고르지 않게 (keyGate.ts)
      if (e.key === 'Enter' || e.key === ' ') {
        if (takeKey(e)) this.chooseCard(this.cardFocus);
        return;
      }
      if (this.cancelLine && e.key === this.cancelLine.key) {
        if (takeKey(e)) this.chooseCard(this.cards.length);
        return;
      }
      const idx = this.cards.findIndex((c) => c.line.key === e.key);
      if (idx >= 0) {
        if (takeKey(e)) this.chooseCard(idx);
        return;
      }
      const next = cardFocusMove(this.cardFocus, this.cards.length, e.key);
      if (next !== this.cardFocus && takeKey(e)) this.focusCard(next);
    };
    this.input.keyboard?.on('keydown', this.onCardKey);
    this.cardFocus = Math.max(0, Math.min(n, keepCursor));
    this.renderCards();
  }

  private focusCard(i: number): void {
    if (i === this.cardFocus) return;
    this.cardFocus = i;
    this.renderCards();
  }

  /** i < n: 카드, i === n: 그만두기 */
  private chooseCard(i: number): void {
    const m = this.menu;
    if (!m) return;
    if (i >= this.cards.length) {
      if (this.cancelLine?.enabled) this.send(m, this.cancelLine.key);
      return;
    }
    const c = this.cards[i];
    if (c?.line.enabled) this.send(m, c.line.key);
  }

  private renderCards(): void {
    const si = Math.max(0, uiCommands.getUiSnapshot().stageIndex);
    const cw = STRUCT.cardW;
    const ch = STRUCT.cardH;
    const accent = hexToNum(accentHex(this, si, 20));
    this.cards.forEach((c, i) => {
      const sel = i === this.cardFocus;
      const g = c.g;
      g.clear();
      // 패 뒷면: 가죽(S1) 바탕 + 안쪽 테 S4 + 격자 무늬 S2 (팔레트 안의 색만)
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
      c.box.setY(sel && c.line.enabled ? c.baseY - 4 : c.baseY).setAlpha(c.line.enabled ? 1 : LAYOUT.disabledAlpha);
      c.label
        .setGlowStyle(!c.line.enabled ? 'page_faint' : sel ? 'page_selected' : 'page_unsel')
        .setAlpha(c.line.enabled ? 1 : LAYOUT.disabledAlpha);
      c.detail?.setAlpha(c.line.enabled ? (sel ? 1 : 0.8) : LAYOUT.disabledAlpha);
    });
    const onCancel = this.cardFocus >= this.cards.length;
    this.cancelText?.setGlowStyle(onCancel ? 'page_selected' : 'page_unsel');
    if (this.cardCursor) {
      if (onCancel && this.cancelText) {
        this.cardCursor.setVisible(true).setPosition(this.cancelText.x - 6, this.cancelText.y + 8);
      } else this.cardCursor.setVisible(false);
    }
  }

  private clearCards(): void {
    if (this.onCardKey) this.input.keyboard?.off('keydown', this.onCardKey);
    this.onCardKey = undefined;
    this.cards = [];
    this.cancelText = undefined;
    this.cancelLine = undefined;
    this.cardCursor = undefined;
  }
}
