import Phaser from 'phaser';
import { COLORS, DEPTH, GAME, PLACEHOLDER_UI } from '../core/Constants';
import { screenFixed } from './display';
import { EventBus, Events, type MenuEventPayload } from '../core/EventBus';
import { UI_EVENTS, __system, type UiMenu, type UiMenuId, type UiMenuLine } from '../contract/ui';
import { UI_SCENES } from '../ui';

export type MenuLine = UiMenuLine;

/**
 * 메뉴 브로커. UI 렌더러가 등록돼 있으면 계약 이벤트(MENU_OPEN/CLOSE)로 넘기고,
 * 아니면 시스템 임시 텍스트로 그린다. 선택은 숫자 키 또는 uiCommands.select 로 들어온다.
 */
export class TextMenu {
  private text?: Phaser.GameObjects.Text;
  private onKey?: (e: KeyboardEvent) => void;
  private current?: { menu: UiMenu; onSelect: (key: string) => void; selected: boolean };

  constructor(private scene: Phaser.Scene) {}

  get isOpen(): boolean {
    return Boolean(this.current);
  }

  get menu(): UiMenu | null {
    return this.current?.menu ?? null;
  }

  open(
    id: UiMenuId,
    title: string,
    lines: MenuLine[],
    onSelect: (key: string) => void,
    footer = '',
    /** 47라운드 구조물 메뉴 (계약 §9.4): 그만두기 key('0') · 연 구조물 id */
    extra: { cancelKey?: string; structureId?: string } = {},
  ): void {
    // 같은 메뉴를 다시 그리는 것(상점·보상 갱신)은 reopen — 열림 효과음을 내지 않는다
    const reopen = this.current?.menu.id === id;
    this.close(reopen);
    const menu: UiMenu = { id, title, footer: footer || undefined, lines };
    if (extra.cancelKey !== undefined) menu.cancelKey = extra.cancelKey;
    if (extra.structureId !== undefined) menu.structureId = extra.structureId;
    this.current = { menu, onSelect, selected: false };
    EventBus.emit(Events.MENU_OPENED, { id, reopen } satisfies MenuEventPayload);
    if (__system.rendererRegistered()) {
      // UI 메뉴 씬이 없으면 띄우고(계약 §5: 씬 키만 사용), 있으면 MENU_OPEN 으로 갱신한다
      const mgr = this.scene.scene.manager;
      if (mgr.keys[UI_SCENES.MENU] && !mgr.isActive(UI_SCENES.MENU)) mgr.start(UI_SCENES.MENU, menu);
      __system.emit(UI_EVENTS.MENU_OPEN, menu);
      return;
    }
    const body = lines.map((l) => `[${l.key}] ${l.label}${l.enabled ? '' : '  (불가)'}`).join('\n');
    const at = screenFixed(this.scene.cameras.main, GAME.WIDTH / 2, GAME.HEIGHT / 2);
    this.text = this.scene.add
      .text(at.x, at.y, `${title}\n\n${body}${footer ? `\n\n${footer}` : ''}`, {
        font: PLACEHOLDER_UI.FONT_BODY,
        color: COLORS.GAMEOVER_TEXT,
        backgroundColor: '#000000c0',
        padding: { x: 10, y: 8 },
        align: 'left',
      })
      .setOrigin(0.5)
      .setScale(at.scale)
      .setScrollFactor(0)
      .setDepth(DEPTH.DEBUG);
    this.onKey = (e: KeyboardEvent) => this.select(e.key);
    this.scene.input.keyboard?.on('keydown', this.onKey);
  }

  /** 계약 명령 또는 숫자 키에서 호출 */
  select(key: string, menuId?: UiMenuId): void {
    if (!this.current) return;
    if (menuId && this.current.menu.id !== menuId) return;
    const line = this.current.menu.lines.find((l) => l.key === key);
    if (!line || !line.enabled) return;
    this.current.selected = true;
    EventBus.emit(Events.MENU_SELECTED, { id: this.current.menu.id, key } satisfies MenuEventPayload);
    this.current.onSelect(key);
  }

  /** 닫기. `silent` 면(같은 메뉴 다시 그리기) 닫힘 이벤트를 내지 않는다 */
  close(silent = false): void {
    const was = this.current;
    if (this.onKey) this.scene.input.keyboard?.off('keydown', this.onKey);
    this.onKey = undefined;
    this.text?.destroy();
    this.text = undefined;
    this.current = undefined;
    if (was) {
      if (!silent)
        EventBus.emit(Events.MENU_CLOSED, { id: was.menu.id, selected: was.selected } satisfies MenuEventPayload);
      __system.emit(UI_EVENTS.MENU_CLOSE, { id: was.menu.id });
    }
  }
}
