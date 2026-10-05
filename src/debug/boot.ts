/**
 * 61라운드 P9: 게임 씬과 무관한 디버그 훅 (`?debug` 일 때만). 타이틀에서도 쓰도록 main.ts 가 부팅 때 `window.__lopad` 에 붙이고,
 * 게임 씬이 `__lopad` 를 새로 만들 때(debug/index.ts `exposeDebug`)도 같은 것을 다시 붙인다.
 * - `__lopad.runlog.dump()` 런 로그 (진행 중·마지막·저장 목록·노드 종류별 평균) · `runlog.clear()` 저장 목록 비우기
 * - `__lopad.vram()` 텍스처 VRAM 추정 (수·합·4096 초과·상위·분류·중복 업로드)
 * - `__lopad.settings()` / `__lopad.setSettings({...})` 계약 §15 설정 (UI 명령과 같은 경로) · `__lopad.hold(true|false)` 안내 패널 멈춤
 */
import type Phaser from 'phaser';
import { uiCommands, type UiSettings } from '../contract/ui';
import { runLogRecorder, type RunLogDebug } from '../systems/runlog/runLogRecorder';
import { settings } from '../systems/settings';
import { vramOfTextures, type VramReport } from '../systems/vram';

export interface BootDebugApi {
  runlog: { dump: () => RunLogDebug; clear: () => void };
  /** `vram({ all: true })` = 전체 키 목록 포함 */
  vram: (opts?: { all?: boolean }) => VramReport | null;
  settings: () => UiSettings;
  setSettings: (s: Partial<UiSettings>) => UiSettings;
  /** 61라운드 플레이 점검 #2: 안내 패널 멈춤 (UI 명령 setGameHold 와 같은 경로, reason 'debug') */
  hold: (on: boolean) => boolean;
}

let bootGame: Phaser.Game | null = null;

function debugOn(): boolean {
  return typeof location !== 'undefined' && new URLSearchParams(location.search).has('debug');
}

export function bootDebugApi(): BootDebugApi {
  return {
    runlog: { dump: () => runLogRecorder.dump(), clear: () => runLogRecorder.clearSaved() },
    vram: (opts) => (bootGame ? vramOfTextures(bootGame.textures, opts) : null),
    settings: () => settings.current(),
    setSettings: (s) => {
      uiCommands.setSettings({ ...settings.current(), ...s });
      return settings.current();
    },
    hold: (on) => {
      uiCommands.setGameHold('debug', on);
      return uiCommands.isGameHeld();
    },
  };
}

export function installBootDebug(game: Phaser.Game): void {
  bootGame = game;
  if (!debugOn()) return;
  const w = window as unknown as { __lopad?: Record<string, unknown> };
  w.__lopad = Object.assign(w.__lopad ?? {}, bootDebugApi());
}
