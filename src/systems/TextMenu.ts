import Phaser from 'phaser';
import { COLORS, DEPTH, GAME, MENU_GUARD, PLACEHOLDER_UI, RARITY_LABEL } from '../core/Constants';
import { screenFixed } from './display';
import { oncePerKeyEvent } from './keyEvents';
import { EventBus, Events, type MenuEventPayload } from '../core/EventBus';
import { UI_EVENTS, __system, type UiMenu, type UiMenuId, type UiMenuLine } from '../contract/ui';
import { UI_SCENES } from '../ui';
import { HeldKeyFilter, MenuGuard, keyTracker } from './input/menuGuard';

export type MenuLine = UiMenuLine;

/**
 * 메뉴 브로커. UI 렌더러가 등록돼 있으면 계약 이벤트(MENU_OPEN/CLOSE)로 넘기고,
 * 아니면 시스템 임시 텍스트로 그린다. 선택은 숫자 키 또는 uiCommands.select 로 들어온다.
 */
export class TextMenu {
  private text?: Phaser.GameObjects.Text;
  private onKey?: (e: KeyboardEvent) => void;
  private current?: { menu: UiMenu; onSelect: (key: string) => void; selected: boolean };
  /** 62 루프 2 E: 열린 뒤 MENU_GUARD.ARM_MS 동안 선택 무시 (`UiMenu.openedAt`·`armMs`) — 같은 메뉴 다시 그리기는 처음 시각 유지 */
  readonly guard = new MenuGuard(MENU_GUARD.ARM_MS, menuGuardEnabled());
  /** 임시 텍스트 메뉴: 열릴 때 누르고 있던 키는 뗐다 다시 눌러야 선택 (HeldKeyFilter) */
  private onKeyUp?: (e: KeyboardEvent) => void;

  constructor(private scene: Phaser.Scene) {
    keyTracker.install();
  }

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
    extra: { cancelKey?: string; structureId?: string; event?: UiMenu['event']; speaker?: string } = {},
  ): void {
    // 같은 메뉴를 다시 그리는 것(상점·보상 갱신)은 reopen — 열림 효과음을 내지 않는다
    const reopen = this.current?.menu.id === id;
    this.close(reopen);
    if (!reopen) this.guard.arm();
    TextMenu.active = this;
    const menu: UiMenu = {
      id,
      title,
      footer: footer || undefined,
      lines,
      openedAt: this.guard.openedAt,
      armMs: this.guard.armMs,
    };
    if (extra.cancelKey !== undefined) menu.cancelKey = extra.cancelKey;
    if (extra.structureId !== undefined) menu.structureId = extra.structureId;
    // 62 D (P1-12·13): 사연 머리 · 말하는 이
    if (extra.event) menu.event = extra.event;
    if (extra.speaker) menu.speaker = extra.speaker;
    this.current = { menu, onSelect, selected: false };
    EventBus.emit(Events.MENU_OPENED, { id, reopen } satisfies MenuEventPayload);
    if (__system.rendererRegistered()) {
      // UI 메뉴 씬이 없으면 띄우고(계약 §5: 씬 키만 사용), 있으면 MENU_OPEN 으로 갱신한다
      const mgr = this.scene.scene.manager;
      if (mgr.keys[UI_SCENES.MENU] && !mgr.isActive(UI_SCENES.MENU)) mgr.start(UI_SCENES.MENU, menu);
      __system.emit(UI_EVENTS.MENU_OPEN, menu);
      return;
    }
    // 61라운드 #3: 임시 텍스트 메뉴만 희귀도·가격을 덧붙인다 (UI 렌더러는 rarity·price 필드로 그린다)
    const body = lines
      .map((l, i) => {
        const r = l.rarity ? `${RARITY_LABEL[l.rarity] ?? ''} ` : '';
        const price = l.price && !l.soldOut ? `  ${l.price.label}` : '';
        return `[${i + 1}] ${r}${l.label}${price}${l.enabled ? '' : '  (불가)'}`;
      })
      .join('\n');
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
    // 53라운드: Phaser 3.90 큐 재처리로 같은 keydown 이 두 번 와도 한 번만 고른다 (keyEvents)
    // 62 루프 2 E: 자동 반복 · 열릴 때 누르고 있던 키는 무시 (뗐다 다시 누른 것만)
    const held = new HeldKeyFilter(keyTracker.down);
    this.onKey = oncePerKeyEvent((e: KeyboardEvent) => {
      if (held.acceptDown(e.code, e.repeat)) this.select(e.key);
    });
    this.onKeyUp = (e: KeyboardEvent) => held.up(e.code);
    this.scene.input.keyboard?.on('keydown', this.onKey);
    this.scene.input.keyboard?.on('keyup', this.onKeyUp);
  }

  /** 62 루프 2 E: 마지막으로 메뉴를 연 브로커 (Game·Setup — `uiCommands.menuShown` 이 찾아간다) */
  private static active: TextMenu | null = null;

  /** 62 루프 2 E: UI 가 이 메뉴를 실제로 화면에 그렸다 (`uiCommands.menuShown`) — 그때부터 다시 armMs */
  static shown(menuId: UiMenuId): void {
    const m = TextMenu.active;
    if (m?.current?.menu.id === menuId) m.guard.shown();
  }

  /** 계약 명령 또는 숫자 키에서 호출 */
  select(key: string, menuId?: UiMenuId): void {
    if (!this.current) return;
    if (menuId && this.current.menu.id !== menuId) return;
    // 62 루프 2 E: 열린 직후(렉·정지 사이 쌓인 입력)는 받지 않는다
    if (!MENU_GUARD.EXEMPT.includes(this.current.menu.id) && !this.guard.accepts()) {
      EventBus.emit(Events.MENU_GUARDED, { id: this.current.menu.id, key } satisfies MenuEventPayload);
      return;
    }
    const line = this.current.menu.lines.find((l) => l.key === key);
    // 53라운드 UI 요청 B1: 그만두기 key(cancelKey)는 줄이 없어도 받는다 (상점 Esc)
    const cancel = key === this.current.menu.cancelKey;
    if (line ? !line.enabled : !cancel) return;
    this.current.selected = true;
    EventBus.emit(Events.MENU_SELECTED, { id: this.current.menu.id, key } satisfies MenuEventPayload);
    this.current.onSelect(key);
  }

  /** 닫기. `silent` 면(같은 메뉴 다시 그리기) 닫힘 이벤트를 내지 않는다 */
  close(silent = false): void {
    const was = this.current;
    if (this.onKey) this.scene.input.keyboard?.off('keydown', this.onKey);
    if (this.onKeyUp) this.scene.input.keyboard?.off('keyup', this.onKeyUp);
    this.onKey = undefined;
    this.onKeyUp = undefined;
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

/** `?menuguard=0` 이면 가드 끔 (검증용) */
function menuGuardEnabled(): boolean {
  return typeof location === 'undefined' || new URLSearchParams(location.search).get(MENU_GUARD.PARAM) !== '0';
}
