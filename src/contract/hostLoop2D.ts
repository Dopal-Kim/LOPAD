/**
 * 62 루프 2 시스템 D 계약 명령 구현 (계약 UI §22 — host.ts 를 덜 건드리려 따로): 전체화면 · 런 포기 · 저장하고 나가기 ·
 * 창을 닫을 때 자동 저장. Game 이 `setRunExit` 로 런 나가기 처리기를 등록한다(시험장·수련장은 null). UI 파트는 import 금지.
 */
import type Phaser from 'phaser';
import { SCENES } from '../core/Constants';
import { installFullscreen, type FullscreenControl } from '../systems/fullscreen';
import { UI_EVENTS, __system, uiCommands } from './ui';
import { setFullscreenProbe } from './snapshotLoop2D';
import { settings } from '../systems/settings';
import { EventBus, Events, type UiSettingToggledPayload } from '../core/EventBus';

/** 켜기/끄기 설정 칸 (ui_toggle 소리) */
const TOGGLE_KEYS = ['flash', 'tilt', 'damageNumbers', 'hitstop'] as const;

export interface RunExitHandler {
  suspend(): boolean;
  abandon(): boolean;
}

let runExit: RunExitHandler | null = null;
let fullscreen: FullscreenControl | null = null;

/** Game 이 등록 (shutdown 에서 null) */
export function setRunExit(h: RunExitHandler | null): void {
  runExit = h;
}

/** 지금 런을 이어하기로 저장 (런 중이 아니면 false) — host.toTitle 이 먼저 부른다 */
export function suspendRun(): boolean {
  return runExit?.suspend() ?? false;
}

export function installLoop2DHost(game: Phaser.Game): void {
  fullscreen = installFullscreen(game, (on) => __system.emit(UI_EVENTS.FULLSCREEN, { on }));
  const fs = fullscreen;
  setFullscreenProbe(() => fs.is());
  __system.patchImpl({
    loop2D: {
      setFullscreen: (on) => fs.set(on),
      isFullscreen: () => fs.is(),
      abandonRun: () => {
        if (!runExit) return false;
        // 일시정지 메뉴에서 고르면 게임을 다시 돌린 뒤 쓰러뜨린다 (사망 연출·결산이 게임 시계로 돈다)
        if (game.scene.isPaused(SCENES.GAME)) uiCommands.resume();
        return runExit.abandon();
      },
      saveAndQuit: () => {
        const saved = suspendRun();
        uiCommands.toTitle();
        return saved;
      },
    },
  });
  // 음향 sound §13 ui_toggle: 설정의 켜기/끄기 칸이 바뀌면 (흔들림·음량 슬라이더는 제외)
  let prev = settings.current();
  settings.onChange((next) => {
    for (const key of TOGGLE_KEYS)
      if (prev[key] !== next[key])
        EventBus.emit(Events.UI_SETTING_TOGGLED, { key, on: Boolean(next[key]) } satisfies UiSettingToggledPayload);
    prev = next;
    // 일시정지 중에도 UI 가 새 키캡(weaponVerbs·E 안내)을 바로 받게 스냅샷 한 장 (게임 씬이 멈춰 STATE 가 오지 않는다)
    __system.emit(UI_EVENTS.STATE, uiCommands.getUiSnapshot());
  });
  // 창·탭을 닫아도 이어하기가 남는다 (pagehide — 모바일·bfcache 포함)
  window.addEventListener('pagehide', () => {
    suspendRun();
  });
}
