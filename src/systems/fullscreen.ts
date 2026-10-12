/**
 * 62 루프 2 시스템 D (P1-16) 전체화면: F11(브라우저 F11 대신 게임 전체화면 — Fullscreen API) · 설정 화면 버튼(계약 `setFullscreen`).
 * 브라우저는 사용자 입력(클릭·키) 처리 안에서만 전체화면을 허락한다 — F11 은 keydown 안에서 바로, UI 버튼은 Phaser 입력 처리(DOM 이벤트
 * 안에서 바로 돈다) 안에서 부른다. 바뀌면 onChange(브라우저 Esc 로 나간 것 포함). 창 크기 배율은 main.ts resize 가 다시 맞춘다.
 */
import Phaser from 'phaser';
import { KEYBIND } from '../core/Constants';

export interface FullscreenControl {
  /** 켜기·끄기 요청 — 바뀌기 시작했으면 true (이미 그 상태이거나 못 쓰면 false) */
  set(on: boolean): boolean;
  is(): boolean;
  destroy(): void;
}

export function installFullscreen(game: Phaser.Game, onChange: (on: boolean) => void): FullscreenControl {
  const sm = game.scale;
  const set = (on: boolean): boolean => {
    if (on === sm.isFullscreen || (on && !sm.fullscreen.available)) return false;
    if (on) sm.startFullscreen();
    else sm.stopFullscreen();
    return true;
  };
  const onKey = (e: KeyboardEvent) => {
    if (e.key !== KEYBIND.FULLSCREEN_KEY && e.code !== KEYBIND.FULLSCREEN_KEY) return;
    e.preventDefault();
    if (!e.repeat) set(!sm.isFullscreen);
  };
  const enter = () => onChange(true);
  const leave = () => onChange(false);
  window.addEventListener('keydown', onKey, true);
  sm.on(Phaser.Scale.Events.ENTER_FULLSCREEN, enter);
  sm.on(Phaser.Scale.Events.LEAVE_FULLSCREEN, leave);
  return {
    set,
    is: () => sm.isFullscreen,
    destroy: () => {
      window.removeEventListener('keydown', onKey, true);
      sm.off(Phaser.Scale.Events.ENTER_FULLSCREEN, enter);
      sm.off(Phaser.Scale.Events.LEAVE_FULLSCREEN, leave);
    },
  };
}
