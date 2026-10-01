/** 시스템 파트: 계약 명령 구현 (씬 제어·세이브·메뉴 라우팅). UI 파트는 import 금지. */
import type Phaser from 'phaser';
import { SCENES } from '../core/Constants';
import { SaveSlot, browserStorage } from '../systems/save';
import { UI_EVENTS, __system, type UiMenuId, type UiSnapshot } from './ui';
import { UI_SCENES } from '../ui';

const saveSlot = new SaveSlot(browserStorage());

/** 현재 열려 있는 메뉴 브로커 (Game 또는 Setup 이 등록) */
let menuSelect: ((menuId: UiMenuId, key: string) => void) | null = null;

export function installContractHost(game: Phaser.Game): void {
  const stopAllUiAndGame = () => {
    for (const key of [
      SCENES.GAME,
      SCENES.SETUP,
      SCENES.GAME_OVER,
      UI_SCENES.HUD,
      UI_SCENES.PAUSE,
      UI_SCENES.MENU,
      UI_SCENES.RESULT,
      UI_SCENES.TITLE,
    ]) {
      if (game.scene.isActive(key) || game.scene.isPaused(key)) game.scene.stop(key);
    }
  };
  __system.setImpl({
    getSnapshot: () => null,
    select: (menuId, key) => menuSelect?.(menuId, key),
    pause: () => {
      if (game.scene.isActive(SCENES.GAME)) {
        game.scene.pause(SCENES.GAME);
        __system.emit(UI_EVENTS.PAUSED, {});
      }
    },
    resume: () => {
      if (game.scene.isPaused(SCENES.GAME)) {
        game.scene.resume(SCENES.GAME);
        __system.emit(UI_EVENTS.RESUMED, {});
      }
    },
    startNewRun: () => {
      saveSlot.clear();
      stopAllUiAndGame();
      game.scene.start(SCENES.SETUP);
    },
    continueRun: () => {
      stopAllUiAndGame();
      if (saveSlot.read()) game.scene.start(SCENES.GAME);
      else game.scene.start(SCENES.SETUP);
    },
    hasSave: () => saveSlot.read() !== null,
    toTitle: () => {
      stopAllUiAndGame();
      if (game.scene.keys[UI_SCENES.TITLE]) game.scene.start(UI_SCENES.TITLE);
      else game.scene.start(SCENES.SETUP);
    },
  });
}

export function setMenuSelect(fn: ((menuId: UiMenuId, key: string) => void) | null): void {
  menuSelect = fn;
}

export function setSnapshotProvider(fn: (() => UiSnapshot | null) | null): void {
  __system.patchImpl({ getSnapshot: () => fn?.() ?? null });
}
