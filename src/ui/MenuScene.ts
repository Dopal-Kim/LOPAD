import Phaser from 'phaser';
import { UI_EVENTS, uiBus, uiCommands, type UiMenu } from '../contract/ui';
import { UI_SCENE_KEYS } from './keys';
import { THEME } from './theme';
import { SelectList, label, panel } from './widgets';

/** 보상·패시브·상점·메타 메뉴 공용 오버레이. MENU_OPEN 으로 열리고 MENU_CLOSE 로 닫힌다. */
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
    const rows = m.lines.length;
    const footerLines = m.footer ? m.footer.split('\n').length : 0;
    const h = 60 + rows * 16 + (footerLines ? 14 * footerLines + 16 : 0);
    const w = Math.min(W - 40, 420);
    this.children.removeAll(true);
    this.list?.destroy();
    panel(this, (W - w) / 2, (H - h) / 2, w, h);
    label(this, W / 2, (H - h) / 2 + 10, m.title, THEME.fontHeading).setOrigin(0.5, 0);
    this.list = new SelectList(this, (W - w) / 2 + 14, (H - h) / 2 + 36, (key) => uiCommands.select(m.id, key));
    this.list.setLines(m.lines.map((l) => ({ key: l.key, label: l.label, enabled: l.enabled })));
    if (m.footer)
      label(this, W / 2, (H + h) / 2 - 14 * footerLines - 10, m.footer, THEME.font, THEME.textDim)
        .setOrigin(0.5, 0)
        .setAlign('center');
    if (m.id === 'meta') this.input.keyboard?.once('keydown-ENTER', () => uiCommands.select('meta', 'enter'));
  }
}
