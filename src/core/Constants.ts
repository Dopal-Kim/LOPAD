/** 모든 설정값. 게임 수치(스탯·적·보스·스테이지)는 data/*.json, 엔진·화면·연출 값은 여기. */
import { CELL_H, CELL_W } from '../systems/mapgen/types';

export const TILE = 16;

export const CELL = {
  W_TILES: CELL_W,
  H_TILES: CELL_H,
  W_PX: CELL_W * TILE,
  H_PX: CELL_H * TILE,
};

/** 내부 해상도 (32라운드 Q1: 960×540). 창 크기에 맞춘 정수 배율은 main.ts (1280×720 창 = 1배, 1920×1080 = 2배) */
export const GAME = {
  WIDTH: 960,
  HEIGHT: 540,
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
  /** 음향 산출물 폴더와 매니페스트 (`assets/audio/manifest.json`, 음향↔시스템 계약 초안) */
  AUDIO_DIR: 'audio',
  AUDIO_MANIFEST: 'manifest.json',
  /** 매니페스트 entry.file 이 저장소 루트 기준(`assets/...`)이므로 이 접두를 떼고 서빙 URL 에 붙인다 */
  AUDIO_FILE_PREFIX: 'assets/',
};

/** 오디오 재생 규칙 (29라운드 임시값, 결정 로그 K). 버스·크로스페이드 수치는 매니페스트 `mixing` 이 우선 */
export const AUDIO = {
  /** 같은 효과음이 이 시간 안에 다시 요청되면 1회만 재생 */
  DEDUPE_MS: 20,
  /** swing·hit 류 랜덤 피치 폭 (±비율) */
  PITCH_VARIANCE: 0.04,
  /** 피치 변주를 적용하는 효과음 id 접두 */
  PITCH_VARIANCE_PREFIXES: ['sfx/swing_', 'sfx/hit_enemy', 'sfx/enemy_hurt'],
  /** 동시 재생 효과음 상한. 넘치면 가장 오래된 것을 끊는다 */
  MAX_SFX_VOICES: 8,
  /** 매니페스트에 mixing 이 없을 때의 기본값 */
  DEFAULT_MIXING: { masterDb: 0, sfxBusDb: 0, bgmBusDb: -8, bgmCrossfadeMs: 1200, bgmBossDuckDb: -3 },
  /** 일시정지 중 BGM 추가 감쇠 (음향 바이블 §3 '선택') */
  PAUSE_DUCK_DB: -6,
  /** 런 종료(사망·엔딩) 시 BGM 페이드아웃 */
  RUN_END_FADE_MS: 1200,
  /** 음소거 토글 키 (KeyboardEvent.code) 와 저장 키 */
  MUTE_KEY_CODE: 'KeyM',
  MUTE_STORAGE_KEY: 'lopad.mute',
  /** 디버그 요약에 남기는 최근 효과음 수 */
  RECENT_SFX: 12,
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
  /** 자기 시트가 없는 보스가 대신 쓰는 시트 이름 (층 램프 스왑은 그대로 적용) — 결정 로그 J */
  BOSS_FALLBACK_SHEET: 'stage1',
  /** 보스 attack `phaseFrames.dash` 프레임 반복 간격 */
  BOSS_DASH_FRAME_MS: 150,
};

export const DEPTH = {
  TILES: 0,
  /** 소품 오버레이 (바닥 위, 개체 아래) */
  PROPS: 0.5,
  /** 발밑 그림자 (개체 아래) */
  SHADOW: 0.9,
  /** 바닥 이펙트 (그림자 위, 개체 아래): 파쇄 링·발도 속도선·질풍 바람 */
  FX_GROUND: 0.95,
  /** 개체(플레이어·적)는 ENTITY + y × ENTITY_Y_SCALE 로 발 위치 기준 정렬 */
  ENTITY: 1,
  ENTITY_Y_SCALE: 1e-5,
  /** 개체에 겹치는 레이어 간격 (무기 오버레이 ±1, 베기 이펙트 +2). 발 y 반 픽셀 차이보다 작다 */
  OVERLAY_STEP: 2.5e-6,
  PICKUP: 2.5,
  PROJECTILE: 3,
  ATTACK: 4,
  /** 피격 이펙트 (타격 섬광·피·치명 버스트): 개체·공격 판정 위 */
  HIT_FX: 4.5,
  /** 데미지 숫자: 월드 요소 중 가장 위 */
  DAMAGE_TEXT: 5,
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
  /** 피격 플레이스홀더 이펙트 (시트가 없을 때): 타격 섬광 흰 원, 넉백 먼지 회색(G7) */
  HIT_SPARK: 0xffffff,
  KNOCK_DUST: 0x6c6f73,
  /** 피 점 폴백 색 (층 램프를 못 찾을 때, 1층 base 호박색) */
  HIT_BLOOD_FALLBACK: 0xd67a11,
  /** 데미지 숫자 (34라운드 글꼴 규칙·팔레트 무채색 G13 / G11). 치명타 색은 층 램프 23(light1) 을 런타임에 고른다 */
  DAMAGE_TEXT: '#d8d9db',
  DAMAGE_TEXT_PLAYER: '#b2b4b8',
  DAMAGE_TEXT_FALLBACK_CRIT: '#e2a33c',
  PROJECTILE: 0xf0e060,
  DEBUG_TEXT: '#9ad',
  GAMEOVER_TEXT: '#eee',
};

/**
 * 카메라 (32라운드 Q2: 방 고정이 아니라 플레이어 부드러운 추종).
 * 목표 스크롤 = 플레이어 중심(데드존 적용) → 현재 영역(방 셀 사각형 + 서 있는 복도의 이웃 셀)으로 클램프 → lerp.
 * 클램프를 목표에만 적용하므로 영역이 바뀌어도 카메라가 튀지 않고 옆 방으로 미끄러진다.
 */
export const CAMERA = {
  /** 프레임당 보간 비율 (60fps 기준) */
  FOLLOW_LERP: 0.1,
  /** 플레이어가 화면 중심에서 이만큼(px) 벗어나야 카메라가 따라간다 */
  DEADZONE_X: 12,
  DEADZONE_Y: 8,
  /** 보간이 이 거리(px) 안이면 목표에 붙인다 (미세 진동 방지) */
  SNAP_PX: 0.25,
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
  /** 이펙트 스프라이트 풀 크기 */
  FX_POOL: 48,
  /** 루프 이펙트(잔월 꼬리) 종료 페이드 */
  FX_FADE_MS: 150,
  /** 중압 이펙트: 히트박스 중심에서 아래로 (계약 §3.1 pivotNote) */
  WEIGHT_FX_DROP_PX: 6,
};

/**
 * 피격 피드백 (35라운드 1단계 임시값, 결정 로그 round-35 "시스템 반영 기록").
 * 강도 배율은 런타임 `feelSettings`(systems/feel.ts) 로 조절 — 디버그 `__lopad.setFeel({ shake: 0 })` (접근성 대비).
 */
export const FEEL = {
  /** 히트스톱: 물리·개체 애니·적 AI 정지 ms (UI·데미지 숫자·흔들림은 계속) */
  HITSTOP: {
    HIT_MS: 40,
    CRIT_MS: 70,
    BOSS_MS: 60,
    PLAYER_HURT_MS: 90,
    /** 연속 적중 중첩 금지: 마지막 시작 뒤 이 시간 안의 요청은 무시 */
    MIN_GAP_MS: 80,
  },
  /** 화면 흔들림: 진폭 px(정수 반올림, 선형 감쇠) · 지속 ms. 스크롤 반올림 뒤에 더한다 */
  SHAKE: {
    HIT: { PX: 2, MS: 60 },
    CRIT: { PX: 4, MS: 100 },
    PLAYER_HURT: { PX: 5, MS: 140 },
    BOSS_WALL: { PX: 6, MS: 160 },
    SHOCKWAVE: { PX: 4, MS: 100 },
  },
  /** 넉백: 공격 방향으로 거리 px, 선형 감쇠 ms (벽은 Arcade 충돌이 막는다) */
  KNOCKBACK: {
    HIT_PX: 6,
    CRIT_PX: 10,
    MS: 100,
    /** 보스는 1/4 거리, AI 를 멈추지 않고 속도에 더한다 */
    BOSS_MULT: 0.25,
    PLAYER_PX: 8,
    PLAYER_MS: 100,
  },
  /** 데미지 숫자 */
  DAMAGE_TEXT: {
    POOL: 24,
    DURATION_MS: 600,
    RISE_PX: 14,
    FADE_MS: 200,
    /** 적중점 위 시작 오프셋 · 겹침 방지 가로 흔들림 */
    OFFSET_Y: -10,
    JITTER_X: 4,
    CRIT_SCALE: 1.5,
    TICK_SCALE: 0.8,
    FONT_PX: 11,
    FONT_FAMILY: 'Galmuri11',
    FONT_FALLBACK: 'monospace',
    /** 글꼴 로드 대기 상한 (넘으면 폴백) */
    FONT_TIMEOUT_MS: 3000,
    /** 치명타 색: 층 램프 index (accent roles: 7 = light1 → 전체 슬롯 23) */
    CRIT_RAMP_INDEX: 7,
  },
  /** 플레이스홀더 피격 이펙트 (시트가 없을 때) */
  PLACEHOLDER: {
    SPARK_RADIUS: 3,
    SPARK_MS: 120,
    SPARK_SCALE_TO: 2.2,
    BLOOD_DOTS: 4,
    BLOOD_MS: 180,
    BLOOD_DIST_PX: 14,
    BLOOD_SPREAD_RAD: 0.7,
    /** 피 점 색: 현재 층 램프 index (5 = base, 1층 호박색) */
    BLOOD_RAMP_INDEX: 5,
    CRIT_RING_FROM: 6,
    CRIT_RING_TO: 18,
    CRIT_RING_MS: 160,
    DUST_DOTS: 3,
    DUST_MS: 200,
    DUST_DIST_PX: 8,
  },
  /** 피격 이펙트 시트 이름 (계약 §3, anchor hitbox_center). 없으면 플레이스홀더 */
  FX_IDS: { SPARK: 'hit_spark', BLOOD: 'blood', CRIT: 'crit_burst', DUST: 'knock_dust', PLAYER_HIT: 'player_hit' },
  /** 피 시트 마지막 프레임(바닥 얼룩) 유지 시간 (아트 권장 300~800ms) 후 페이드 */
  BLOOD_STAIN_MS: 500,
};

export const DEBUG = {
  /** 시스템 파트 임시 디버그 텍스트. HUD는 UI 파트 소유이므로 이것은 HUD가 아니다. */
  SHOW_TEXT: true,
  FONT: '12px monospace',
};

/** 시스템 임시 화면(개성 선택·결과·임시 메뉴)의 글꼴. 960×540 기준 (32라운드). UI 파트 산출물로 교체 대상 */
export const PLACEHOLDER_UI = {
  FONT_TITLE: '32px monospace',
  FONT_BODY: '14px monospace',
  FONT_SMALL: '12px monospace',
  FONT_CAPTION: '11px monospace',
  /** 개성 선택 라벨 상단 여백 */
  LABEL_Y: 36,
  /** 획 예시 패널 (strokes 단계): 상단 y, 높이, 예시 사이 간격, 반복 전 멈춤 */
  EXAMPLE_PANEL: { y: 392, h: 126, gap: 18, pauseMs: 700 },
  /** 결과 화면 제목·부제·영혼 줄 간격 */
  RESULT_TITLE_DY: -18,
  RESULT_SUB_DY: 24,
  RESULT_SOULS_DY: 56,
  /** 이름 입력 DOM input 폭(px, 캔버스 좌표계) */
  NAME_INPUT_WIDTH: 240,
};

/** 개성 선택 리듬 단계의 하얀 점 (31라운드 1): 플레이어 표식. 이동 속도·대쉬 거리는 data/player.json 값을 그대로 쓴다 */
export const RHYTHM_DOT = {
  RADIUS: 6,
  COLOR: 0xffffff,
  /** 화면 가장자리 여백 (점이 라벨·패널을 가리지 않게) */
  MARGIN: 24,
  /** 대쉬 잔상: 개수·지속 */
  TRAIL_COUNT: 3,
  TRAIL_MS: 220,
  TRAIL_ALPHA: 0.5,
  /** 클릭 시 점 주변 원 번쩍: 시작 반지름 → 끝 반지름, 지속 */
  RING_FROM: 8,
  RING_TO: 20,
  RING_MS: 180,
  RING_WIDTH: 2,
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
