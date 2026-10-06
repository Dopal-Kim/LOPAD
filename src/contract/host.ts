/** 시스템 파트: 계약 명령 구현 (씬 제어·세이브·메뉴 라우팅). UI 파트는 import 금지. */
import type Phaser from 'phaser';
import { SCENES } from '../core/Constants';
import { gameState } from '../core/GameState';
import { trainingRoom } from '../data/training';
import { STORY } from '../data';
import { SaveSlot, browserStorage } from '../systems/save';
import { audio } from '../systems/audio/audio';
import { settings } from '../systems/settings';
import { runLogRecorder } from '../systems/runlog/runLogRecorder';
import { EventBus, Events } from '../core/EventBus';
import { transitionGate, TRANSITION_UI } from '../systems/transition/transitionGate';
import { restoreRun, trainingSession, type RunStash, type TrainingOrigin } from '../scenes/game/training/session';
import {
  UI_EVENTS,
  __system,
  uiBus,
  type UiMenuId,
  type UiSnapshot,
  type UiTrainingStart,
  type UiWarpDenied,
  type UiWarpDenyReason,
} from './ui';
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

/** 48라운드 노드 선택: Game 이 등록 (계약 §10.2) · 53라운드 Q47 고르기 취소 */
let nodeChooser: ((id: string) => boolean) | null = null;
let chooseCanceler: (() => boolean) | null = null;

/** 61 단계 6 §19: 런 중 수련장 — Game 이 등록 (맡길 수 있으면 RunStash, 아니면 거부 이유) */
let trainingLeaver: (() => Exclude<UiTrainingStart, 'ok'> | RunStash) | null = null;

/** 일시정지 대상 게임 씬 (일반 게임 · 무기 시험장 · 61 단계 6 수련장) — 53라운드 UI 요청 B3: 시험장 Esc 도 UI 일시정지가 받는다 */
const PAUSABLE = [SCENES.GAME, SCENES.WEAPON_LAB, SCENES.TRAINING];

export function installContractHost(game: Phaser.Game): void {
  const stopAllUiAndGame = () => {
    // 61 단계 6: 진행 중인 그림 속 입구 전환은 버린다 (덮개가 남지 않게 READY)
    transitionGate.cancel();
    for (const key of [
      SCENES.GAME,
      SCENES.WEAPON_LAB,
      SCENES.TRAINING,
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
  /** 수련장에 맡겨 둔 런을 버린다 (타이틀·새 런·이어하기·시험장 — 맡긴 런은 보통의 '런 중 나가기'와 같다) */
  const dropStash = () => {
    if (!trainingSession.stash) return;
    trainingSession.stash = null;
    runLogRecorder.hold(false);
  };
  // 61 단계 6 §19 그림 속 입구 전환 (UI → 시스템: covered · end)
  transitionGate.attach({
    emitUi: (event, payload) => __system.emit(event, payload),
    emitInternal: (p) => EventBus.emit(Events.TRANSITION_BEGIN, p),
    rendererRegistered: () => __system.rendererRegistered(),
    setTimer: (ms, fn) => setTimeout(fn, ms),
    clearTimer: (h) => clearTimeout(h as ReturnType<typeof setTimeout>),
  });
  uiBus.on(TRANSITION_UI.COVERED, (p: { id?: number }) => transitionGate.onUiCovered(p));
  uiBus.on(TRANSITION_UI.END, (p: { id?: number }) => transitionGate.onUiEnd(p));
  const busyScene = (key: string) => game.scene.isActive(key) || game.scene.isPaused(key);
  /** 수련장 시작 (origin = 어디서 왔나 · room = 바로 갈 방) */
  const openTraining = (origin: TrainingOrigin, stash: RunStash | null, room?: string) => {
    trainingSession.origin = origin;
    trainingSession.stash = stash;
    trainingSession.weapon = stash ? ((stash.fields.weapon as { id?: string } | undefined)?.id ?? null) : null;
    if (stash) runLogRecorder.hold(true);
    else runLogRecorder.abandon();
    stopAllUiAndGame();
    audio.setPaused(false);
    audio.stopAllLoops();
    const roomWeapon = room ? trainingRoom(room)?.weapon : null;
    game.scene.start(SCENES.TRAINING, {
      trainingRoom: room,
      labWeapon: roomWeapon ?? trainingSession.weapon ?? undefined,
    });
  };
  __system.setImpl({
    getSnapshot: () => null,
    select: (menuId, key) => menuSelect?.(menuId, key),
    pause: () => {
      const key = PAUSABLE.find((k) => game.scene.keys[k] && game.scene.isActive(k));
      if (key) {
        game.scene.pause(key);
        audio.setPaused(true);
        __system.emit(UI_EVENTS.PAUSED, {});
      }
    },
    resume: () => {
      const key = PAUSABLE.find((k) => game.scene.keys[k] && game.scene.isPaused(k));
      if (key) {
        game.scene.resume(key);
        audio.setPaused(false);
        __system.emit(UI_EVENTS.RESUMED, {});
      }
    },
    startNewRun: () => {
      dropStash();
      runLogRecorder.abandon();
      saveSlot.clear();
      stopAllUiAndGame();
      audio.setPaused(false);
      audio.setState('title');
      game.scene.start(SCENES.SETUP);
    },
    continueRun: () => {
      dropStash();
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
    cancelChoose: () => chooseCanceler?.() ?? false,
    setMuted: (muted) => audio.setMute(muted),
    // 61라운드 §15: 설정 — 즉시 적용(감각 배율·음량 버스) + 메타 세이브
    getSettings: () => settings.current(),
    setSettings: (s) => {
      settings.set(s);
    },
    startWeaponLab: () => {
      // 49라운드 계약 §11.4: 시스템 무기 시험장 씬 (scenes/WeaponLab.ts — Game 의 lab 모드). Esc = 타이틀
      if (!game.scene.keys[SCENES.WEAPON_LAB]) return;
      dropStash();
      runLogRecorder.abandon();
      stopAllUiAndGame();
      audio.setPaused(false);
      game.scene.start(SCENES.WEAPON_LAB);
    },
    getText: () => ({ ...STORY.ui, controls: STORY.controls }),
    // 61 단계 6 §19 수련장: 타이틀 · 첫 생 선택(Setup) · 런 중 일기장
    startTraining: (room) => {
      if (!game.scene.keys[SCENES.TRAINING]) return 'busy';
      if (busyScene(SCENES.TRAINING) || transitionGate.locked) return 'busy';
      if (busyScene(SCENES.GAME)) {
        if (!trainingLeaver) return 'busy';
        const r = trainingLeaver();
        if (typeof r === 'string') return r;
        openTraining('run', r, room);
        return 'ok';
      }
      openTraining(busyScene(SCENES.SETUP) ? 'setup' : 'title', null, room);
      return 'ok';
    },
    leaveTraining: () => {
      const s = trainingSession;
      const stash = s.stash;
      s.stash = null;
      stopAllUiAndGame();
      audio.setPaused(false);
      audio.stopAllLoops();
      if (stash) {
        // 맡긴 런 그대로: 같은 노드로 돌아온다 (마친 노드면 출구가 열린 채로)
        restoreRun(stash);
        if (gameState.route) gameState.route.choosing = false;
        runLogRecorder.hold(false);
        audio.setState(null);
        game.scene.start(SCENES.GAME, { mode: 'node', resume: true });
        return;
      }
      if (s.origin === 'setup') {
        audio.setState('title');
        game.scene.start(SCENES.SETUP);
        return;
      }
      audio.setState('title');
      if (game.scene.keys[UI_SCENES.TITLE]) game.scene.start(UI_SCENES.TITLE);
      else game.scene.start(SCENES.SETUP);
    },
    toTitle: () => {
      dropStash();
      runLogRecorder.abandon();
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

export function setChooseCanceler(fn: (() => boolean) | null): void {
  chooseCanceler = fn;
}

/** 61 단계 6 §19: Game 이 등록 (시험장·수련장은 null) */
export function setTrainingLeaver(fn: (() => Exclude<UiTrainingStart, 'ok'> | RunStash) | null): void {
  trainingLeaver = fn;
}
