import Phaser from 'phaser';
import { UI_EVENTS, uiBus, uiCommands, type UiMenu } from '../contract/ui';
import { GlowText } from './glow';
import { book, fontsReady, preloadKit, rule, setupKit } from './kit';
import { UI_SCENE_KEYS } from './keys';
import { SelectList } from './widgets';

/**
 * 보상·패시브·상점·메타·개성 3지선다(evolve)·엔딩 2지선다(ending) 공용 일기장 한 페이지.
 * MENU_OPEN 으로 열리고 MENU_CLOSE 로 닫힌다. 제목 page_title(Galmuri11 2배 — 한자 포함 가능) + 괘선,
 * 항목은 SelectList(page_selected/unsel, 커서), detail 은 page_faint, footer 는 page_faint 하단.
 * evolve·ending 은 페이지 최소 폭 520.
 */
export class MenuScene extends Phaser.Scene {
  private menu?: UiMenu;
  private list?: SelectList;
  private pendingClose = false;
  private alive = false;
  private onOpen = (m: UiMenu) => {
    this.pendingClose = false;
    this.show(m);
  };
  private onClose = (p: { id: string }) => {
    // 같은 프레임에 다음 메뉴가 열릴 수 있으므로 다음 update 에서 닫는다
    if (this.menu?.id === p.id) this.pendingClose = true;
  };

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
    setupKit(this);
    uiBus.on(UI_EVENTS.MENU_OPEN, this.onOpen);
    uiBus.on(UI_EVENTS.MENU_CLOSE, this.onClose);
    this.events.once('shutdown', () => {
      this.alive = false;
      uiBus.off(UI_EVENTS.MENU_OPEN, this.onOpen);
      uiBus.off(UI_EVENTS.MENU_CLOSE, this.onClose);
      this.list?.destroy();
    });
    this.menu = data;
    fontsReady().then(() => {
      if (this.alive && this.menu) this.show(this.menu);
    });
  }

  private show(m: UiMenu): void {
    this.menu = m;
    const W = this.scale.width;
    const H = this.scale.height;
    const stageIndex = Math.max(0, uiCommands.getUiSnapshot().stageIndex);
    // evolve 의 라벨은 '이름 — 설명' 형식으로 올 수 있고 detail 에 같은 설명이 들어 있다 (시스템 29라운드).
    // 설명을 두 번 보이지 않도록 라벨 끝의 ' — 설명' 을 떼고 아래 줄(detail)로만 보인다.
    const lines = m.lines.map((l) => {
      const suffix = l.detail ? ` — ${l.detail}` : '';
      const dup = Boolean(suffix) && l.label.endsWith(suffix);
      return {
        key: l.key,
        label: dup ? l.label.slice(0, -suffix.length) : l.label,
        enabled: l.enabled,
        detail: l.detail && (dup || !l.label.includes(l.detail)) ? l.detail : undefined,
      };
    });
    this.children.removeAll(true);
    this.list?.destroy();

    const wide = m.id === 'evolve' || m.id === 'ending';
    const minW = wide ? 520 : 420;
    const maxW = W - 64;
    const padX = 24;
    // 항목·제목·푸터를 먼저 그려 폭을 재고, 페이지는 그 뒤에 깔아(depth 0) 글이 잘리지 않게 한다
    this.list = new SelectList(this, 0, 0, (key) => uiCommands.select(m.id, key), {
      stageIndex,
      detailWrap: maxW - padX * 2 - 40,
    });
    this.list.setLines(lines);
    const title = new GlowText(this, 0, 0, m.title, 'page_title', { scale: 2, stageIndex }).setDepth(1);
    const footer = m.footer
      ? new GlowText(this, 0, 0, m.footer, 'page_faint', { wrap: maxW - padX * 2, align: 'center' }).setDepth(1)
      : null;
    const contentW = Math.max(this.list.maxWidth() + 8, title.displayWidth, footer?.displayWidth ?? 0);
    const pageW = Math.min(maxW, Math.max(minW, contentW + padX * 2));
    const titleH = title.displayHeight;
    const listH = this.list.height();
    const footerH = footer ? footer.displayHeight + 10 : 0;
    const pageH = 16 + titleH + 8 + 4 + 14 + listH + 10 + footerH + 16;
    const bk = book(this, Math.round(W / 2), Math.round(H / 2), pageW, pageH, 1, `menu:${m.id}`);
    const pg = bk.pages[0];
    let y = pg.y + 16;
    title.placeCenter(pg.x + pageW / 2, y);
    y += titleH + 8;
    rule(this, pg.x + padX, y, pageW - padX * 2).setDepth(1);
    y += 4 + 14;
    this.list.setPosition(pg.x + padX, y).setDepth(1);
    y += listH + 10;
    footer?.placeCenter(pg.x + pageW / 2, y);
    if (m.id === 'meta') this.input.keyboard?.once('keydown-ENTER', () => uiCommands.select('meta', 'enter'));
  }
}
