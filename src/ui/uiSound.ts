import type Phaser from 'phaser';
import { uiCommands } from '../contract/ui';
import { currentSettings } from './settingsStore';

/**
 * 62 루프 2: UI 만 아는 메뉴 소리 (타이틀 메뉴·일기장 목록·설정 쪽의 커서 이동·고르기·뒤로).
 * 음향 파트가 만드는 `ui_move`·`ui_select`·`ui_back` 을 부른다 — 매니페스트에 없어 로드되지 않았으면 **조용히 건너뛴다**
 * (시스템이 그리는 메뉴의 열림·고르기 소리는 시스템 오디오가 낸다 — 같은 순간에 두 번 울리지 않게 UI 전용 목록에서만 부른다).
 * 전체 음량·음소거는 사운드 매니저(시스템이 맞춤)가, 효과음 버스 배율은 여기서 설정 `sfx` 를 곱한다.
 */
export type UiSoundId = 'move' | 'select' | 'back';

/** 찾는 순서 (음향 매니페스트 id 꼴 `sfx/<이름>` 먼저) */
export const UI_SOUND_KEYS: Readonly<Record<UiSoundId, readonly string[]>> = Object.freeze({
  move: ['sfx/ui_move', 'ui_move'],
  select: ['sfx/ui_select', 'ui_select'],
  back: ['sfx/ui_back', 'ui_back'],
});

/** 기본 크기 (매니페스트 gainDb 는 시스템 버스 몫이라 여기서는 고정 배율) */
const BASE_VOLUME = 0.6;
/** 같은 소리를 너무 촘촘히 겹치지 않게 (키 자동 반복) */
const MIN_GAP_MS = 45;
const lastAt: Partial<Record<UiSoundId, number>> = {};

export function playUiSound(scene: Phaser.Scene, id: UiSoundId): void {
  try {
    const cache = scene.cache?.audio;
    if (!cache) return;
    const key = UI_SOUND_KEYS[id].find((k) => cache.exists(k));
    if (!key) return;
    const now = performance.now();
    if (now - (lastAt[id] ?? -1e9) < MIN_GAP_MS) return;
    lastAt[id] = now;
    if (uiCommands.getUiSnapshot().muted) return;
    const sfx = currentSettings().sfx;
    if (!(sfx > 0)) return;
    scene.sound.play(key, { volume: BASE_VOLUME * sfx });
  } catch {
    /* 소리는 없어도 된다 */
  }
}
