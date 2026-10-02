/** 시스템 파트: 계약 명령 구현 (씬 제어·세이브·메뉴 라우팅). UI 파트는 import 금지. */
import type Phaser from 'phaser';
import { SCENES } from '../core/Constants';
import { STORY } from '../data';
import { SaveSlot, browserStorage } from '../systems/save';
import { audio } from '../systems/audio';
import { UI_EVENTS, __system, type UiMenuId, type UiSnapshot, type UiWarpDenied, type UiWarpDenyReason } from './ui';
import { UI_SCENES } from '../ui';

const saveSlot = new SaveSlot(browserStorage());

/** 현재 열려 있는 메뉴 브로커 (Game 또는 Setup 이 등록) */
let menuSelect: ((menuId: UiMenuId, key: string) => void) | null = null;

/** 45라운드 워프: Game 이 등록. check = 판정만, run = 판정 후 시작 (null 이면 시작됨) */
export interface WarpHandler {
  check: (roomId: string) => UiWarpDenyReason | null;
  run: (roomId: string) => UiWarpDenyReason | null;
}
let warpHandler: WarpHandler | null = null;

/** 48라운드 노드 선택: Game 이 등록 (계약 §10.2) */
let nodeChooser: ((id: string) => boolean) | null = null;

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
        audio.setPaused(true);
        __system.emit(UI_EVENTS.PAUSED, {});
      }
    },
    resume: () => {
      if (game.scene.isPaused(SCENES.GAME)) {
        game.scene.resume(SCENES.GAME);
        audio.setPaused(false);
        __system.emit(UI_EVENTS.RESUMED, {});
      }
    },
    startNewRun: () => {
      saveSlot.clear();
      stopAllUiAndGame();
      audio.setPaused(false);
      audio.setState('title');
      game.scene.start(SCENES.SETUP);
    },
    continueRun: () => {
      stopAllUiAndGame();
      audio.setPaused(false);
      if (saveSlot.read()) game.scene.start(SCENES.GAME);
      else game.scene.start(SCENES.SETUP);
    },
    hasSave: () => saveSlot.read() !== null,
    warpTo: (roomId) => {
      const deny = (reason: UiWarpDenyReason) => {
        __system.emit(UI_EVENTS.WARP_DENIED, { roomId, reason } satisfies UiWarpDenied);
        return false;
      };
      if (!warpHandler) return deny('busy');
      // 선택 화면이 게임을 멈춰 뒀다면, 허용될 때만 재개하고 워프한다 (계약 §8.2)
      const pre = warpHandler.check(roomId);
      if (pre) return deny(pre);
      if (game.scene.isPaused(SCENES.GAME)) {
        game.scene.resume(SCENES.GAME);
        audio.setPaused(false);
        __system.emit(UI_EVENTS.RESUMED, {});
      }
      const reason = warpHandler.run(roomId);
      return reason ? deny(reason) : true;
    },
    chooseNode: (id) => nodeChooser?.(id) ?? false,
    getText: () => ({ ...STORY.ui, controls: STORY.controls }),
    toTitle: () => {
      stopAllUiAndGame();
      audio.setPaused(false);
      audio.stopAllLoops();
      audio.setState('title');
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

export function setWarpHandler(h: WarpHandler | null): void {
  warpHandler = h;
}

export function setNodeChooser(fn: ((id: string) => boolean) | null): void {
  nodeChooser = fn;
}
