import Phaser from 'phaser';
import { UI_EVENTS, uiBus, type UiMenu, type UiSnapshot } from '../contract/ui';
import { UI_SCENE_KEYS } from './keys';

/**
 * UI 전용 디버그 경로 (47라운드, 헤드리스 화면 확인용). 주소에 `uidebug=1` 이 있을 때만 켜진다.
 * 시스템이 아직 채우지 않은 계약 값(구조물 안내·HUD 상태·구조물 메뉴·이벤트)을 UI 안에서 가짜로 넣어 화면만 본다.
 * 가짜 메뉴의 선택은 시스템으로 보내지 않고 `selects` 에 적는다. 시스템 코드·상태는 건드리지 않는다.
 *
 * window.__lopadUi = {
 *   patch(p | (s) => p | null)  // 매 STATE 스냅샷 위에 얕게 덮어쓴다 (null 이면 해제)
 *   emit(name, payload)         // UI_EVENTS[name] 를 uiBus 로 (STRUCTURE_RESULT·CHALLENGE_* 등 화면 확인용)
 *   openMenu(menu) / closeMenu()// 가짜 메뉴 열기·닫기
 *   selects: [menuId, key][]    // 가짜 메뉴에서 고른 기록
 * }
 */
type Patch = Partial<UiSnapshot> | ((s: UiSnapshot) => Partial<UiSnapshot>);

interface DebugApi {
  patch(p: Patch | null): void;
  emit(name: keyof typeof UI_EVENTS, payload?: unknown): void;
  openMenu(menu: UiMenu): void;
  closeMenu(): void;
  selects: [string, string][];
}

let enabled: boolean | null = null;
let patch: Patch | null = null;
let fakeMenu: UiMenu | null = null;
let scenePlugin: Phaser.Scenes.ScenePlugin | null = null;
const selects: [string, string][] = [];

export function uiDebugEnabled(): boolean {
  if (enabled === null) {
    enabled = typeof location !== 'undefined' && new URLSearchParams(location.search).get('uidebug') === '1';
  }
  return enabled;
}

/** 디버그 덮어쓰기를 적용한 스냅샷 (꺼져 있으면 그대로) */
export function withDebug(s: UiSnapshot): UiSnapshot {
  if (!patch) return s;
  const p = typeof patch === 'function' ? patch(s) : patch;
  return { ...s, ...p };
}

/** 이 메뉴가 디버그 가짜 메뉴인가 (선택을 시스템으로 보내지 않는다) */
export function isDebugMenu(m: UiMenu): boolean {
  return fakeMenu !== null && fakeMenu.id === m.id && (fakeMenu.structureId ?? '') === (m.structureId ?? '');
}

export function debugSelect(m: UiMenu, key: string): void {
  selects.push([m.id, key]);
}

/** HUD 씬 create 에서 호출 */
export function installUiDebug(scene: Phaser.Scene): void {
  if (!uiDebugEnabled()) return;
  scenePlugin = scene.scene;
  const api: DebugApi = {
    patch(p) {
      patch = p;
    },
    emit(name, payload) {
      uiBus.emit(UI_EVENTS[name], payload);
    },
    openMenu(menu) {
      fakeMenu = menu;
      if (!scenePlugin) return;
      if (scenePlugin.isActive(UI_SCENE_KEYS.MENU)) uiBus.emit(UI_EVENTS.MENU_OPEN, menu);
      else scenePlugin.launch(UI_SCENE_KEYS.MENU, menu);
    },
    closeMenu() {
      if (fakeMenu) uiBus.emit(UI_EVENTS.MENU_CLOSE, { id: fakeMenu.id });
      fakeMenu = null;
    },
    selects,
  };
  (window as unknown as { __lopadUi?: DebugApi }).__lopadUi = api;
}
