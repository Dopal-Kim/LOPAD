import Phaser from 'phaser';
import { UI_EVENTS, uiBus, uiCommands, type UiMenu } from '../contract/ui';
import { UI_SCENE_KEYS } from './keys';
import { THEME } from './theme';
import { SelectList, label, panel } from './widgets';

/**
 * 보상·패시브·상점·메타·개성 3지선다(evolve) 공용 오버레이. MENU_OPEN 으로 열리고 MENU_CLOSE 로 닫힌다.
 * 선택지 detail 은 항목 아래 작은 글씨, 비활성은 흐리게, footer 는 패널 하단 (29라운드).
 */
export class MenuScene extends Phaser.Scene {
  private menu?: UiMenu;
  private list?: SelectList;
  private pendingClose = false;
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

  update(): void {
    if (this.pendingClose) {
      this.pendingClose = false;
      this.scene.stop();
    }
  }

  create(data: UiMenu): void {
    this.pendingClose = false;
    uiBus.on(UI_EVENTS.MENU_OPEN, this.onOpen);
    uiBus.on(UI_EVENTS.MENU_CLOSE, this.onClose);
    this.events.once('shutdown', () => {
      uiBus.off(UI_EVENTS.MENU_OPEN, this.onOpen);
      uiBus.off(UI_EVENTS.MENU_CLOSE, this.onClose);
      this.list?.destroy();
    });
    this.show(data);
  }

  private show(m: UiMenu): void {
    this.menu = m;
    const W = this.scale.width;
    const H = this.scale.height;
    const footerLines = m.footer ? m.footer.split('\n').length : 0;
    // evolve 의 라벨은 '이름 — 설명' 형식으로 오고 detail 에 같은 설명이 들어 있다 (시스템 29라운드).
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
    const listH = SelectList.measure(lines);
    const h = 52 + listH + (footerLines ? 14 * footerLines + 14 : 6);
    this.children.removeAll(true);
    this.list?.destroy();
    // 항목을 먼저 그려 폭을 재고, 패널은 그 뒤에 깔아 (depth 0) 설명이 길어도 잘리지 않게 한다
    const top = (H - h) / 2;
    this.list = new SelectList(this, 0, top + 36, (key) => uiCommands.select(m.id, key));
    this.list.setLines(lines);
    const titleText = label(this, 0, top + 10, m.title, THEME.fontHeading).setDepth(1);
    const footerText = m.footer
      ? label(this, 0, top + h - 14 * footerLines - 8, m.footer, THEME.font, THEME.textDim)
          .setAlign('center')
          .setDepth(1)
      : null;
    const minW = m.id === 'evolve' ? 520 : 420;
    const content = Math.max(this.list.maxWidth() + 28, titleText.width + 28, (footerText?.width ?? 0) + 28, minW);
    const w = Math.min(W - 40, content);
    const left = (W - w) / 2;
    panel(this, left, top, w, h).setDepth(0);
    titleText.setPosition(W / 2, top + 10).setOrigin(0.5, 0);
    footerText?.setPosition(W / 2, top + h - 14 * footerLines - 8).setOrigin(0.5, 0);
    this.list.setPosition(left + 14, top + 36).setDepth(1);
    if (m.id === 'meta') this.input.keyboard?.once('keydown-ENTER', () => uiCommands.select('meta', 'enter'));
  }
}
