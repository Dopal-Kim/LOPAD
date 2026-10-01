/** 모든 설정값. 게임 수치(스탯·적·보스·스테이지)는 data/*.json, 엔진·화면·연출 값은 여기. */
import { CELL_H, CELL_W } from '../systems/mapgen/types';

export const TILE = 16;

export const CELL = {
  W_TILES: CELL_W,
  H_TILES: CELL_H,
  W_PX: CELL_W * TILE,
  H_PX: CELL_H * TILE,
};

export const GAME = {
  WIDTH: 640,
  HEIGHT: 360,
  BACKGROUND_COLOR: '#0b0b10',
  MIN_ZOOM: 1,
};

export const SCENES = {
  BOOT: 'Boot',
  PRELOADER: 'Preloader',
  GAME: 'Game',
  GAME_OVER: 'GameOver',
} as const;

export const TEXTURES = {
  TILES: 'tiles',
};

export const DEPTH = {
  TILES: 0,
  ENEMY: 1,
  PLAYER: 2,
  PROJECTILE: 3,
  ATTACK: 4,
  DEBUG: 100,
};

export const COLORS = {
  TILE_VOID: '#0b0b10',
  TILE_FLOOR: '#1c1c28',
  TILE_CORRIDOR: '#17171f',
  TILE_WALL: '#3a3a52',
  DOOR_OPEN: '#26503a',
  DOOR_CLOSED: '#8a4a2a',
  DOOR_LOCKED: '#8a2a4a',
  PLAYER: 0x4a90e2,
  PLAYER_HURT: 0xffffff,
  PLAYER_DASH: 0x9ad0ff,
  PLAYER_PARRY: 0xfff8c0,
  PLAYER_RECOVER: 0x2f5a8a,
  PROJECTILE_REFLECTED: 0x80f0ff,
  ATTACK: 0xf5f5c0,
  MOB_HURT: 0xffffff,
  TELEGRAPH: 0xfff0a0,
  STUN: 0x707090,
  PROJECTILE: 0xf0e060,
  DEBUG_TEXT: '#9ad',
  GAMEOVER_TEXT: '#eee',
};

export const CAMERA = {
  /** 셀 높이(352)가 화면(360)보다 8px 작아서 위아래 4px씩 여백을 둔다 */
  CELL_OFFSET_Y: -4,
  /** 보스 방 추적 카메라 보간 */
  FOLLOW_LERP: 0.12,
};

export const PROTOTYPE = {
  HURT_FLASH_MS: 80,
  /** 보스 처치 후 결과 화면까지 지연 */
  CLEAR_DELAY_MS: 1200,
  SLASH_TRAIL_MS: 220,
  BANNER_MS: 1500,
  /** 투사체 최대 동시 수 */
  PROJECTILE_POOL: 64,
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
  DASH: 'SPACE',
} as const;
