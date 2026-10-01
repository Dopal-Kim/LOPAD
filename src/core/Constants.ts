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
  SETUP: 'Setup',
  GAME: 'Game',
  GAME_OVER: 'GameOver',
} as const;

export const TEXTURES = {
  /** 플레이스홀더 타일 (아트 타일셋이 없는 층) */
  TILES: 'tiles',
  /** 아트 타일셋 텍스처 키 접두 (`tiles_stage1`) */
  TILESET_PREFIX: 'tiles_',
  /** 스프라이트 시트 텍스처 키 접두 (`sheet_player_idle`) */
  SHEET_PREFIX: 'sheet_',
  /** 플레이스홀더 사각형 텍스처 키 접두 (`ph_16x16`) */
  PLACEHOLDER_PREFIX: 'ph_',
  /** 발밑 그림자 텍스처 키 접두 (`shadow_18`) */
  SHADOW_PREFIX: 'shadow_',
  /** 아트 산출물 매니페스트 (JSON 캐시 키) */
  MANIFEST: 'assets_manifest',
};

/** 아트 산출물 경로 (계약 contracts/art-assets.md). vite.config.ts 플러그인이 `assets/` 를 이 URL 로 서빙한다 */
export const ASSETS = {
  /** 상대 경로 (base './' 배포 호환) */
  URL: 'assets-game',
  MANIFEST: 'manifest.json',
  SPRITES_DIR: 'sprites',
  TILES_DIR: 'tiles',
  /** 층 타일셋 파일 이름 접두 (`stage1.json`) */
  STAGE_PREFIX: 'stage',
};

/** 스프라이트 연출 값 (29라운드 임시값) */
export const SPRITES = {
  /** 발밑 타원 그림자 */
  SHADOW_ALPHA: 0.35,
  SHADOW_COLOR: 0x000000,
  /** 그림자 폭 = 바디 폭 + 여유, 높이 = 폭 × 비율 */
  SHADOW_PAD: 2,
  SHADOW_RATIO: 0.4,
  /** 적 사망 시체: 마지막 프레임 유지 후 사라지는 시간 */
  CORPSE_HOLD_MS: 500,
  CORPSE_FADE_MS: 600,
  /** 플레이어 사망 애니 끝 → 결과 화면까지 추가 대기 */
  DEATH_EXTRA_MS: 400,
  /** 방향 변경 시 걷기 애니 프레임을 이어 간다 */
  KEEP_WALK_FRAME: true,
};

export const DEPTH = {
  TILES: 0,
  /** 소품 오버레이 (바닥 위, 개체 아래) */
  PROPS: 0.5,
  /** 발밑 그림자 (개체 아래) */
  SHADOW: 0.9,
  /** 개체(플레이어·적)는 ENTITY + y × ENTITY_Y_SCALE 로 발 위치 기준 정렬 */
  ENTITY: 1,
  ENTITY_Y_SCALE: 1e-5,
  PICKUP: 2.5,
  PROJECTILE: 3,
  ATTACK: 4,
  DEBUG: 100,
};

/** 발 위치 y 로 깊이를 정한다 (아래쪽이 앞) */
export function entityDepth(y: number): number {
  return DEPTH.ENTITY + y * DEPTH.ENTITY_Y_SCALE;
}

export const COLORS = {
  TILE_VOID: '#0b0b10',
  TILE_FLOOR: '#1c1c28',
  TILE_CORRIDOR: '#17171f',
  TILE_WALL: '#3a3a52',
  DOOR_OPEN: '#26503a',
  DOOR_CLOSED: '#8a4a2a',
  DOOR_LOCKED: '#8a2a4a',
  EXIT: '#d8c860',
  SHOP: '#60a8d8',
  GOLD: 0xf0c830,
  POTION: 0x60e080,
  PLAYER: 0x4a90e2,
  PLAYER_HURT: 0xffffff,
  PLAYER_DASH: 0x9ad0ff,
  PLAYER_PARRY: 0xfff8c0,
  PLAYER_RECOVER: 0x2f5a8a,
  PLAYER_GUARD: 0x8fa8c8,
  PLAYER_AIM: 0xd0b0ff,
  PLAYER_SHADOW: 0x303048,
  GUARD_PUSH: 0xb0c8e8,
  TRAIL_DOT: 0xa0a0ff,
  BLEED: 0xc03030,
  DASH_TRAIL: 0x80d0ff,
  PROJECTILE_REFLECTED: 0x80f0ff,
  PLAYER_SHOT: 0xc0e8ff,
  SHOCKWAVE: 0xffd080,
  STROKE: 0xe0e0ff,
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
  SHOCKWAVE_MS: 260,
  TWIN_DELAY_MS: 80,
  /** 가드 해제 밀쳐내기 연출 */
  GUARD_PUSH_MS: 200,
  /** 그림자 걸음 잔상 연출 */
  SHADOW_STEP_MS: 180,
  /** 조준 사격 차지 선 연출 폭 */
  AIM_LINE_WIDTH: 1,
  /** 개성 강화 알림 */
  REINFORCE_BANNER_MS: 1200,
  FATE_BANNER_MS: 1500,
  BANNER_MS: 1500,
  /** 바닥 드랍 최대 동시 수 */
  PICKUP_POOL: 64,
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
  POTION: 'Q',
} as const;
