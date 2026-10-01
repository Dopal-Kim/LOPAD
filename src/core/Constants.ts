/** 모든 설정값. 게임 수치(스탯·적)는 data/*.json, 엔진·화면·연출 값은 여기. */

export const TILE = 16;

export const GAME = {
  WIDTH: 640,
  HEIGHT: 360,
  BACKGROUND_COLOR: '#14141c',
  MIN_ZOOM: 1,
};

export const SCENES = {
  BOOT: 'Boot',
  PRELOADER: 'Preloader',
  GAME: 'Game',
  GAME_OVER: 'GameOver',
} as const;

export const DEPTH = {
  GRID: -1,
  ENEMY: 1,
  PLAYER: 2,
  ATTACK: 3,
  DEBUG: 100,
};

export const COLORS = {
  GRID: 0x1e1e2a,
  PLAYER: 0x4a90e2,
  PLAYER_HURT: 0xffffff,
  ATTACK: 0xf5f5c0,
  ENEMY_HURT: 0xffffff,
  DEBUG_TEXT: '#9ad',
  GAMEOVER_TEXT: '#eee',
};

export const PROTOTYPE = {
  /** 1단계 프로토타입에서 한 번에 배치하는 적 수. Claude 임시값, 확인 필요 */
  ENEMY_COUNT: 5,
  /** 적 스폰 시 플레이어와의 최소 거리(px) */
  ENEMY_SPAWN_MIN_DIST: 120,
  HURT_FLASH_MS: 80,
};

export const DEBUG = {
  /** 시스템 파트 임시 디버그 텍스트. HUD는 UI 파트 소유이므로 이것은 HUD가 아니다. */
  SHOW_TEXT: true,
  FONT: '10px monospace',
};

export const KEYS = {
  UP: 'W',
  DOWN: 'S',
  LEFT: 'A',
  RIGHT: 'D',
  RESTART: 'R',
} as const;
