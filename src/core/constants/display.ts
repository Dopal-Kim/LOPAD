/** 모든 설정값. 게임 수치(스탯·적·보스·스테이지)는 data/*.json, 엔진·화면·연출 값은 여기. */
import { CELL_H, CELL_W } from '../systems/mapgen/types';

/** 월드 타일 크기(월드 단위). 50라운드: 판정·이동·데이터 수치는 이 단위 그대로 (RENDER 참고) */
export const TILE = 16;

/**
 * 50라운드 렌더 배율 (결정 round-50 Q2 '캐릭터 32×48·타일 32×32·카메라 확대 1배(화면상 크기 유사)', 계약 art §9).
 * 설계: 월드 좌표·판정·속도는 그대로 두고 **렌더 배율만** 바꾼다. 월드 1단위 = 논리 화면 WORLD_TO_SCREEN px (= 게임 카메라 논리
 * 배율 CAMERA.ZOOM). 근거는 parts/system/README.md 50라운드 절.
 *
 * 52라운드 Q8 (계약 art §11): 내부 렌더 1920×1080. 논리 화면(UI 배치·좌표 기준)은 960×540 그대로이고 캔버스만 RESOLUTION 배 —
 * 모든 카메라가 RESOLUTION 배를 더 곱한다(`systems/display.ts`). 도트 1개 = 실제 px: 기존(pixelScale 없음) 4 · v2(1) 2 · v3(0.5) 1.
 * 화면상 크기는 셋 다 같다 (`artScale = pixelScale / WORLD_TO_SCREEN` 은 그대로, 카메라 실제 배율이 2 → 4)
 */
export const RENDER = {
  WORLD_TO_SCREEN: 2,
  /** JSON pixelScale 이 없는 기존 도트의 배율 */
  LEGACY_PIXEL_SCALE: 2,
  /** 52라운드: 논리 px 1개 = 실제 캔버스 px (960×540 → 1920×1080) */
  RESOLUTION: 2,
} as const;

export const CELL = {
  W_TILES: CELL_W,
  H_TILES: CELL_H,
  W_PX: CELL_W * TILE,
  H_PX: CELL_H * TILE,
};

/**
 * 논리 해상도 (32라운드 Q1: 960×540 — UI 배치·좌표 기준). 52라운드: 실제 캔버스는 × RENDER.RESOLUTION (1920×1080).
 * 창 표시 배율은 main.ts (1280×720 창 = 960×540 표시, 1920×1080 창 = 1920×1080 — 52라운드 전과 같은 표시 크기)
 */
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
  /** 49라운드 계약 §11.4: 무기 시험장 (host.startWeaponLab 이 이 키로 시작) */
  WEAPON_LAB: 'WeaponLab',
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

/**
 * 53라운드 Q49 적 소환 예고 (UI 는 튜토리얼에서만 '주의' 경고): 예고 뒤 소환까지 ms. 임시값 —
 * 튜토리얼 전투(탄생 전장)만 기다리고, 일반 시련 웨이브는 0(예고와 동시에 소환 — 전투 박자 그대로)
 */
export const ENEMY_INCOMING = { TUTORIAL_DELAY_MS: 900, WAVE_DELAY_MS: 0 };

/** 아트 산출물 경로 (계약 contracts/art-assets.md). vite.config.ts 플러그인이 `assets/` 를 이 URL 로 서빙한다 */
export const ASSETS = {
  /** 상대 경로 (base './' 배포 호환) */
  URL: 'assets-game',
  MANIFEST: 'manifest.json',
  SPRITES_DIR: 'sprites',
  TILES_DIR: 'tiles',
  /** 50라운드 새 2배 도트 하위 폴더 (`sprites/player/v2/…`, `tiles/v2/…`) — 있으면 기존보다 먼저 */
  V2_DIR: 'v2',
  /** 52라운드 도트 세분화 하위 폴더 (`sprites/player/v3/…`) — v3 → v2 → 기존 순 (계약 art §11) */
  V3_DIR: 'v3',
  /** 53라운드 v3 바닥 소품 시트 접미 (`tiles/v3/stage1_outer_props.json`) */
  PROPS_SUFFIX: '_props',
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
  /** 음소거 저장 키. 49라운드 계약 §11.3: M 키 토글은 없앴다 (M = UI 지도, 음소거는 Esc 메뉴 → uiCommands.setMuted) */
  MUTE_STORAGE_KEY: 'lopad.mute',
  /** 디버그 요약에 남기는 최근 효과음 수 */
  RECENT_SFX: 12,
};

/** 스프라이트 연출 값 (29라운드 임시값) */
export const SPRITES = {
  /** 55라운드: fps·frameDurationsMs 가 없는 정지 시트(입자·리본)의 애니 등록용 fps (재생하지 않음) */
  STATIC_SHEET_FPS: 10,
  /** 발밑 타원 그림자 */
  /** 53라운드 Q22~25: 바닥이 밝아진 만큼 발밑 대비를 올림 (0.35 → 0.5, 임시) */
  SHADOW_ALPHA: 0.5,
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
  /**
   * 52라운드 Q10 (계약 art §12) 걷기·달리기 보폭 맞춤: 재생 배속 = 실제 이동 속도 ÷ (stride.px → 월드 / cycleMs) 를 이 범위로 자른다.
   * 임시값 — v3 stride(걷기 36도트/800ms · 달리기 45도트/560ms)를 그대로 쓰면 실제 속도 대비 약 8.5배라 상한에 걸린다(README 52라운드 절)
   */
  STRIDE_RATE_MIN: 0.5,
  STRIDE_RATE_MAX: 2,
  /** 53라운드 Q10: Shift 달리기는 run 을 기준 배속 × (실제/평소 속도)로 — 그 상한 = STRIDE_RATE_MAX × 이 값 */
  SPRINT_RATE_HEADROOM: 2,
  /** 53라운드 Q10: 감속 배율(Player.moveSlowMult)이 이보다 낮으면 걷기(walk) 그림, 아니면 달리기(run) 그림 */
  WALK_BELOW_MULT: 0.85,
  /**
   * 53라운드 4번 피드백: v3 만 로드하는 시트 묶음 (name 이 없으면 분류 전체). 구 주인공(sprites/player/*, player/v2)과
   * 구 칼 오버레이(weapons/katana_*, weapons/v2/katana_*)는 더 이상 읽지 않는다.
   * 53라운드 후속: v3 적 시트가 갖춰진 허수아비·사수·결사병도 구 시트(enemies/<id>_*, enemies/v2/<id>_*)를 읽지 않는다
   */
  V3_ONLY: [
    { category: 'player' },
    { category: 'weapons', name: 'katana' },
    { category: 'enemies', name: 'dummy' },
    { category: 'enemies', name: 'archer' },
    { category: 'enemies', name: 'charger' },
  ] as readonly {
    category: string;
    name?: string;
  }[],
  /** 53라운드 v3 시트 판별: JSON pixelScale 이 이 값 이하 (계약 §11 v3 = 0.5) */
  V3_PIXEL_SCALE: 0.5,
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
  /** 잔상 궤적 리본 (42라운드): 공격 판정 위·피격 이펙트 아래 */
  TRAIL: 4.2,
  /** 피격 이펙트 (타격 섬광·피·치명 버스트): 개체·공격 판정 위 */
  HIT_FX: 4.5,
  /**
   * 50라운드 동적 조명: 라이트맵(곱하기)이 덮는 깊이. 이보다 아래(바닥·벽·개체·구조물·개체 위 이펙트)는 어둠에 잠기고,
   * 위(드랍·투사체·공격 판정·잔상·피격 이펙트·데미지 숫자·화면 섬광)는 그대로 읽힌다. 빛 번짐·비네팅은 그 바로 위
   */
  LIGHTMAP: 2,
  LIGHT_LAYER_STEP: 0.01,
  /**
   * 53라운드 Q64: 이펙트(FxPool)는 라이트맵 위에 — 라이트맵 아래 깊이 d 를 FX_LIT_BASE + d × FX_LIT_SPAN 으로 옮긴다
   * (빛 번짐 +0.01 위, 드랍 2.5 아래: d < 2 이면 2.02 ~ 2.22)
   */
  FX_LIT_BASE: 2.02,
  FX_LIT_SPAN: 0.1,
  /** 데미지 숫자: 월드 요소 중 가장 위 */
  DAMAGE_TEXT: 5,
  /** 화면 섬광·색 오버레이 (42라운드): 월드 최상. UI 는 별도 씬이라 덮지 않는다 */
  SCREEN_FX: 50,
  DEBUG: 100,
};

/**
 * 50라운드 쿼터뷰 벽 (계약 art §9: 벽 앞면 세로 wallHeightTiles 칸 + 윗면, 출입·충돌은 바닥 격자 기준). 임시값
 */
export const QUARTER = {
  /** 캐릭터가 벽 뒤에 가려지면 그 벽 그림을 이만큼 비친다 (가려진 채 길을 잃지 않게, 임시) */
  OCCLUDE_ALPHA: 0.55,
  /** 가림 판정 여유 (월드 px) */
  OCCLUDE_PAD_PX: 2,
  /**
   * v2 타일셋 바닥: 방 종류 바닥(roomFloors)을 섞는 비율 기본값 — 타일셋 JSON roomFloorMix 가 없을 때 (계약 §12: 0.06)
   */
  ROOM_FLOOR_MIX: 0.06,
  /** 53라운드 v3 소품 시트 (아트 anchorRule): 작은 소품 피벗 = 놓일 칸의 논리 (16, 30) · 큰 소품 피벗 = 발자국 아래 바닥 위 2 논리 px */
  V3_PROP_ANCHOR_LOGICAL: { x: 16, y: 30 },
  V3_PIVOT_LIFT_LOGICAL: 2,
  /** 52라운드 Q9: 쿼터뷰 타일셋 노드 전투장의 가장자리 깊이 상한 (0~1칸 — 북쪽 집 앞면이 거의 한 줄로) */
  EDGE_MAX_INSET: 1,
  /**
   * 52라운드 Q11 큰 소품(bigProps) 배치 (임시값): 가로등 = 북쪽 벽 앞 간격 6칸·최대 4 · 화로 1~2 = 중앙 둘레 고리 4~7칸(가로 1.6배) ·
   * 우물·좌판 = 구석(안쪽 2칸, 위쪽 구석은 북쪽 3칸 비움) · 상자 더미 = 서·동 벽가 최대 2 · 시작점·출구·상점 둘레 3칸 비움
   */
  BIG_PROPS: {
    CLEAR_TILES: 3,
    LAMP_SPACING: 6,
    LAMP_MAX: 4,
    NORTH_SEARCH_TILES: 3,
    BRAZIER_COUNT: [1, 2] as [number, number],
    BRAZIER_RING: [4, 7] as [number, number],
    BRAZIER_X_STRETCH: 1.6,
    BRAZIER_TRIES: 16,
    CORNER_INSET_TILES: 2,
    NORTH_KEEP_TILES: 3,
    CORNER_SEARCH_TILES: 8,
    CRATE_MAX: 2,
    CRATE_TRIES: 12,
    /**
     * 53라운드 Q59·Q69: 아트 placement 힌트 속 규칙어 → 배치 규칙 ('벽 앞' → 북쪽 벽 앞, '가장자리'·'구석' → 구석, '엄폐' → 서·동 벽가,
     * '문·길 양옆' → 출구 좌우, '측면 세로' → 서·동 벽가 세로, '대칭' → 가운데 축 좌우 짝, '탁자 끝'·'단상 양옆' → 탁자 옆).
     * 규칙어가 없으면 LEGACY_RULES(52라운드 이름 규칙), 그것도 없으면 DEFAULT_RULE(Q69 '그 외 = 벽가')
     */
    HINTS: {
      north: ['벽 앞'],
      corner: ['가장자리', '구석'],
      cover: ['엄폐'],
      exit: ['문·길 양옆', '문 양옆', '길 양옆'],
      column: ['측면 세로'],
      mirror: ['대칭'],
      table: ['탁자 끝', '탁자 옆', '단상 양옆', '단상 옆'],
    },
    LEGACY_RULES: { lamp_post: 'north', brazier: 'ring', well: 'corner', stall: 'corner', crate_stack: 'cover' },
    DEFAULT_RULE: 'cover',
    /** 53라운드 Q57: avoidNearBorder 쪽 바닥 끝에서 이 칸 수 안에 발자국이 걸치지 않게 */
    AVOID_BORDER_TILES: 3,
    /** Q69 출구 좌우 (임시): 출구 2×2 에서 띄우는 칸 [최소, 최대] — 출구 둘레 비움(CLEAR_TILES)은 이 규칙만 넘는다 */
    EXIT_SIDE_GAP_TILES: [1, 2] as [number, number],
    /** Q69 서·동 벽가 세로 (임시): 쪽마다 개수 */
    COLUMN_PER_SIDE: 1,
    /** Q69 가운데 축 좌우 짝 (임시): 짝 수 · 축에서 떨어진 거리(내부 폭 비율) · 북·남 바닥 끝에서 비울 칸 · 시도 */
    MIRROR_PAIRS: 2,
    MIRROR_DX_FRAC: [0.15, 0.35] as [number, number],
    MIRROR_EDGE_TILES: 3,
    MIRROR_TRIES: 24,
    /** Q69 탁자 옆 (임시): 탁자마다 개수 (끝 남 → 끝 북 → 안쪽 옆 순으로, 다른 큰 소품 둘레 1칸 규칙 때문에 한 칸 띄움) */
    TABLE_SIDE_PER_ANCHOR: 1,
    /** 문(벽의 열린 틈) 앞 바닥에서 비울 칸 (임시) */
    DOOR_CLEAR_TILES: 1,
  },
  /** 53라운드 4지역 바닥 데칼 (art floors_v2 decals[], 임시): 가운데 1장 이름 · 그 밖 이름마다 장 수 · 시도 · 북쪽 비움 */
  DECALS: {
    CENTER: ['cup_inlay'] as readonly string[],
    COUNT: [1, 2] as [number, number],
    TRIES: 40,
    NORTH_KEEP_TILES: 2,
  },
  /** 53라운드 양조 수로 (art floors_v2 canal, 임시): 북쪽 끝에서 몇 칸 아래 줄부터 · 남쪽 남길 줄 · 시작점·출구·상점 둘레 피할 줄 */
  CANAL: { ROW_FROM_NORTH: 8, SOUTH_KEEP_ROWS: 3, ANCHOR_CLEAR_ROWS: 1 },
  /** 바닥 데칼 깊이 (바닥·그늘 위, 테두리·소품 아래) */
  DECAL_DEPTH: 0.02,
} as const;

/**
 * 53라운드 Q6~Q8 Gemini 외벽 테두리 (`assets/tiles/border/<지역>/border.json`, 계약 art §13). 길이는 **논리 px**(960×540 기준,
 * 월드 = 논리 ÷ RENDER.WORLD_TO_SCREEN). 깊이: 서·동·북 띠 = 바닥 위·소품 아래 배경, 남 띠 = Y 정렬 층 위(라이트맵 아래 — 조명을 받는다),
 * 발광 = 라이트맵 위 가산. 전부 임시값(README 53라운드 절)
 */
export const BORDER = {
  DIR: 'tiles/border',
  JSON: 'border.json',
  DEPTH_SIDE: 0.2,
  DEPTH_NORTH: 0.25,
  /** 문·출구 자리 어둠 조각 · 골목 입구 그림 (북 띠 위) */
  DEPTH_DOOR: 0.27,
  /** 남 띠(전경): 개체(1 + y·1e-5) 위, 라이트맵(2) 아래 */
  DEPTH_SOUTH: 1.9,
  DEPTH_SOUTH_DOOR: 1.91,
  /** 발광(가산): 라이트맵 바로 위 · 빛 번짐(+0.01) 아래 */
  DEPTH_EMISSIVE: DEPTH.LIGHTMAP + 0.005,
  /** 남 띠가 주인공과 겹칠 때 알파 (border.json south.occlusion.fadeAlpha 가 우선) · 바뀌는 빠르기 (60fps 프레임당) */
  SOUTH_FADE_ALPHA: 0.45,
  SOUTH_FADE_LERP: 0.25,
  /** 남 띠 하늘 판정: 이 알파(0~255) 이상이면 불투명 */
  SOUTH_OPAQUE_ALPHA: 24,
  /** 카메라 좌우 한계 = 바닥 끝 ± (border.json camera.bounds.left 가 없을 때) */
  CAMERA_SIDE_PX: 200,
  /** Q8: 주인공이 바닥 북쪽 끝에서 ZONE 안이면 카메라 중심을 최대 LOOKUP 위로 (선형), 보간 비율 (60fps 프레임당) */
  LOOKUP_ZONE_PX: 200,
  LOOKUP_PX: 110,
  LOOKUP_LERP: 0.06,
  /** 문 조각이 없을 때 문 자리 어둠: 높이(바닥 끝에서 위로) · 색 · 위쪽 흐림 비율 */
  DOOR_DARK_HEIGHT_PX: 150,
  DOOR_DARK_COLOR: 0x07070a,
  DOOR_DARK_FADE: 0.35,
  /** 53라운드 Q22~25: 지역별 북쪽 치우침 덮어쓰기 (논리 px) — 연회장(보스 방)만 160, 나머지는 border.json northLookUp(110) */
  LOOKUP_BY_REGION: { hall: 160 } as Record<string, number>,
  /**
   * 53라운드 Q22~25 황무지: 북 띠 둑 위 혼불 (soul_wisp 시트·빛). 개수 [min,max] · 바닥 북쪽 끝 위 높이 [min,max] 논리 px ·
   * 가로 자리 = 바닥 폭 비율 + 흔들림 논리 px
   */
  WISPS: {
    waste: { COUNT: [2, 3], ABOVE_PX: [96, 150], X_FRACS: [0.2, 0.5, 0.8], JITTER_PX: 60 },
  } as Record<string, { COUNT: [number, number]; ABOVE_PX: [number, number]; X_FRACS: number[]; JITTER_PX: number }>,
  /** 테두리 기준 주변광 (border.json ambient 가 없을 때) — 53라운드 Q9 중립 숯빛. 실제 주변광이 더 밝으면 테두리를 이만큼 눌러 명도 유지 */
  REF_AMBIENT: '#575761',
  /** 성문 북 띠(repeat 'sides'): 바닥 가운데 ± 이만큼(논리 px)에 걸친 북쪽 문 칸은 띠에 그려진 성문이 곧 출구 */
  GATE_CENTER_TOL_PX: 48,
  /** 혼불 깊이 (북 띠·문 조각 위, 개체 아래) */
  DEPTH_WISP: 0.28,
} as const;

/**
 * 53라운드 Q4 등 상흔 (계약 §13 scarAnchor): 런 시작 때 획을 작은 텍스처 2장(균열 = 보통 합성 · 빛 = 가산)으로 굽고,
 * 몸 바로 위·무기 아래에 겹친다. 빛은 조명 영향을 받지 않도록 라이트맵 위(조명이 켜진 지역). 전부 임시값
 */
export const SCAR_FX = {
  /** 구울 때 기준 사각형 높이 (캔버스 px) · 여백 */
  TEX_H: 96,
  PAD: 10,
  /** 균열: 어두운 틈 + 호박 심 */
  CRACK_COLOR: '#140b07',
  CRACK_ALPHA: 0.85,
  CRACK_WIDTH: 5,
  CORE_COLOR: '#c8641e',
  CORE_WIDTH: 1.6,
  /** 빛: 번진 호박빛 + 뜨거운 심 */
  GLOW_COLOR: 'rgba(255,140,50,0.85)',
  GLOW_BLUR: 7,
  GLOW_WIDTH: 2.4,
  GLOW_HOT: '#ffcf86',
  GLOW_HOT_WIDTH: 0.9,
  /** 깜빡임: 알파 = ALPHA × (1 − PULSE_AMP·(0.5 − 0.5 sin) − FLICKER_AMP·잡음) */
  ALPHA: 0.9,
  PULSE_AMP: 0.25,
  PULSE_HZ: 0.55,
  FLICKER_AMP: 0.08,
  /** 측면: 어깨 쪽 빛 점만 (앵커 사각형 짧은 변 × SIDE_SIZE, 알파 × SIDE_ALPHA) */
  SIDE_SIZE: 1.2,
  SIDE_ALPHA: 0.6,
  /** 깊이: 몸 위 (OVERLAY_STEP × 이 값 — 앞 무기 +1 보다 아래) · 빛 = 라이트맵 위 */
  DEPTH_STEP: 0.4,
  GLOW_DEPTH: DEPTH.LIGHTMAP + 0.004,
} as const;

/** 발 위치 y 로 깊이를 정한다 (아래쪽이 앞) */
export function entityDepth(y: number): number {
  return DEPTH.ENTITY + y * DEPTH.ENTITY_Y_SCALE;
}

/**
 * 53라운드 Q64: 이펙트 깊이 → 라이트맵 위 띠. 라이트맵 아래 깊이 d 는 FX_LIT_BASE + d × FX_LIT_SPAN 으로 옮겨
 * 이펙트끼리의 앞뒤(바닥 이펙트 < 개체에 붙은 이펙트)는 지키고 어둠에는 묻히지 않게 한다. 이미 위(투사체·판정·피격)면 그대로
 */
export function fxLitDepth(d: number): number {
  return d < DEPTH.LIGHTMAP ? DEPTH.FX_LIT_BASE + Math.max(0, d) * DEPTH.FX_LIT_SPAN : d;
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
  /** 55라운드 Q22 대검 차지 단계 번쩍임 (팔레트 호박 #e2a33c) */
  CHARGE_FLASH: 0xe2a33c,
  GUARD_PUSH: 0xb0c8e8,
  TRAIL_DOT: 0xa0a0ff,
  BLEED: 0xc03030,
  DASH_TRAIL: 0x80d0ff,
  PROJECTILE_REFLECTED: 0x80f0ff,
  PLAYER_SHOT: 0xc0e8ff,
  SHOCKWAVE: 0xffd080,
  STROKE: 0xe0e0ff,
  ATTACK: 0xf5f5c0,
  /** 56라운드 Q36: 적 피격 번쩍임 = 호박 반투명 (흰 채움 → 흰 막대 주원인이었다). 알파·시간은 FEEDBACK.MOB_HURT */
  MOB_HURT: 0xe2a33c,
  TELEGRAPH: 0xfff0a0,
  STUN: 0x707090,
  /** 54라운드 보스 마시는 중 (호박색 곱 틴트) */
  BOSS_DRINK: 0xffd8a0,
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
  /**
   * 48라운드 Q1: 게임 월드 카메라 확대 (논리 960×540 → 한 화면 약 30×17타일). UI 씬은 별도 카메라라 무관.
   * 데드존·흔들림 px 는 논리 화면 px 기준이라 월드 px 로는 ÷ZOOM 해서 쓴다 (흔들림 체감 유지, 임시).
   * 52라운드: 이 값은 **논리** 배율 — 실제 카메라 zoom = ZOOM × RENDER.RESOLUTION (`display.worldZoom`)
   */
  ZOOM: RENDER.WORLD_TO_SCREEN,
};

/**
 * 48라운드 Q6 탄생 연출 (임시값). 새 런 첫 노드(황폐한 탄생지)에서 1회, 아무 키로 건너뛴다.
 * 카메라를 ZOOM 배로 당겨 player_birth(+fx/birth_dust) 재생 → burstFrame 에 잔불 터짐·약한 흔들림 → 2배로 부드럽게 복귀.
 * 시트가 없으면 흙 파티클이 모이며 플레이어가 서서히 나타나는 폴백
 */
export const BIRTH = {
  ZOOM: 4,
  /** 2→4배 확대 (시작) — 시트 3.67초 + 확대·복귀 ≈ 5초 */
  ZOOM_IN_MS: 450,
  /** 시트가 없을 때 폴백 길이 · 잔불 터짐 시점 비율 */
  FALLBACK_MS: 3400,
  FALLBACK_BURST_AT: 0.72,
  /** 연출 뒤 4→2배 복귀 */
  ZOOM_OUT_MS: 750,
  /** 복귀 전 잠깐 멈춤 */
  HOLD_MS: 150,
  /** 잔불 터짐: 섬광 · 흔들림(화면 px) */
  BURST_FLASH: { COLOR: 0xffb050, MS: 160, ALPHA: 0.35 },
  BURST_SHAKE: { PX: 2, MS: 180 },
  /** 폴백 흙 파티클: 수 · 시작 반경(px) · 색(G7 흙 회갈) · 크기 */
  DUST_COUNT: 22,
  DUST_RADIUS_PX: 26,
  DUST_COLOR: 0x6c5a48,
  DUST_SIZE: 2,
  /** 폴백 잔불 불티 */
  EMBER_COUNT: 10,
  EMBER_COLOR: 0xff9a3c,
  EMBER_DIST_PX: 18,
  EMBER_MS: 420,
  /** 이 시간이 지나기 전 입력은 건너뛰기로 보지 않는다 (씬 진입 직후 눌린 키 무시) */
  SKIP_GRACE_MS: 250,
};

/** 48라운드 노드 지도 전환 연출 (임시값) */
export const ROUTE_FX = {
  /** 53라운드 Q47: 노드 고르기 취소(Esc) 때 출구에서 물러나는 거리 (타일, 임시) */
  CANCEL_STEP_TILES: 1.5,
  /** 노드를 고른 뒤 암전 · 새 노드에서 밝아짐 */
  FADE_OUT_MS: 280,
  FADE_IN_MS: 320,
  /** 새 노드 진입 직후 입력 잠금·전투 시작 지연 (밝아지는 동안) */
  ENTER_LOCK_MS: 450,
  /** 노드를 마친 뒤 출구가 열리기까지 */
  EXIT_DELAY_MS: 500,
  /** 출구에서 이만큼 떨어져야(px) 다시 선택을 연다 (UI 없이 메뉴로 고를 때 재진입 방지) */
  EXIT_REARM_PX: 24,
  /** 암전 색 */
  FADE_COLOR: { R: 0, G: 0, B: 0 },
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
    /**
     * 55라운드 Q6: 무기 적중 히트스톱 = data/weapons.json `feel.hitstopMs`(단검 30·칼 45·대검 80·활 25) ×
     * 막타(연격 마지막 타·대쉬 공격)·치명타 배율. 동시 다수 적중은 한 번만 (MIN_GAP_MS)
     */
    HEAVY_MULT: 1.8,
    /** 무기 데이터에 feel.hitstopMs 가 없을 때 */
    WEAPON_FALLBACK_MS: 40,
  },
  /** 화면 흔들림: 진폭 px(정수 반올림, 선형 감쇠) · 지속 ms. 스크롤 반올림 뒤에 더한다 */
  SHAKE: {
    HIT: { PX: 2, MS: 60 },
    CRIT: { PX: 4, MS: 100 },
    PLAYER_HURT: { PX: 5, MS: 140 },
    BOSS_WALL: { PX: 6, MS: 160 },
    SHOCKWAVE: { PX: 4, MS: 100 },
    /** 55라운드 Q8: 막타·대검·치명타 적중 흔들림 — 적중 시트 JSON `shakeHint` 가 없을 때 (임시) */
    HEAVY_HIT: { PX: 3, MS: 90 },
  },
  /** 55라운드 Q8 방향성 흔들림: 타격 방향으로 밀렸다가 반대로 튕기는 진동 횟수 (임시) */
  SHAKE_DIR: { CYCLES: 1.5 },
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
    CRIT_SCALE: 2,
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
  /** 피격 이펙트 시트 이름 (계약 §3, anchor hitbox_center). 없으면 플레이스홀더. 43라운드: `hit_burst` 가 있으면 `hit_spark` 대신 */
  FX_IDS: {
    SPARK: 'hit_spark',
    SPARK_ALT: 'hit_burst',
    BLOOD: 'blood',
    CRIT: 'crit_burst',
    DUST: 'knock_dust',
    PLAYER_HIT: 'player_hit',
    /** 55라운드 Q8·Q10 (계약 §16): 무기별 적중 스파크 `hit_<무기>` · 막타 `hit_<무기>_heavy` (없으면 hit_burst) */
    WEAPON_HIT_PREFIX: 'hit_',
    WEAPON_HIT_HEAVY_SUFFIX: '_heavy',
    /** 재 파편 입자 묶음 (kinds·recipes) */
    PARTICLES: 'particles_ash',
  },
  /**
   * 43라운드 B: 연타 시트(twin·dance) `hitFrames` 가 있으면 추가 타격 판정 간격을 그 프레임 시작 시각에 맞춘다
   * (쌍격 2타 40ms, 난무 0/40/90ms). false 면 기존 PROTOTYPE.TWIN_DELAY_MS 간격 + 그림만 겹침. 임시값
   */
  SYNC_HIT_FRAMES: true,
  /** 피 시트 마지막 프레임(바닥 얼룩) 유지 시간 (아트 권장 300~800ms) 후 페이드 */
  BLOOD_STAIN_MS: 500,
  /**
   * 55라운드 Q7·Q14 ④ 칼끝 잔상 리본 (계약 §16 `fx/v3/ribbon_ash`·`ribbon_ash_thin`): 칼끝(무기 v3 bladeTipAnchors) 궤적을
   * 텍스처 띠로 잇는다. 가는 호박 선 → LIFE_MS 안에 재색으로 식으며 소멸, 반투명 없음, 도트 궤적(연격 시트) 아래 깊이.
   * 시간은 플레이 시계(히트스톱 동안 멈춤). `feelSettings.trail` 로 끔
   */
  RIBBON: {
    /** 리본 수명 (Q7: 100ms 안에 식으며 소멸) */
    LIFE_MS: 100,
    /** 기본 텍스처 (3도트) · 가는 텍스처 (2도트). 무기별은 data/weapons.json feel.ribbon */
    SHEET: 'ribbon_ash',
    THIN_SHEET: 'ribbon_ash_thin',
    /** 칼끝 위치를 찍는 간격 (플레이 시계 ms — 프레임 사이도 보간해서 찍는다) */
    SAMPLE_MS: 4,
    /** 리본에 남기는 최대 점 수 */
    MAX_POINTS: 40,
    /** 판정 첫 프레임 몇 프레임 전부터 · 판정 끝 몇 프레임 뒤까지 칼끝을 찍는다 (임시) */
    LEAD_FRAMES: 1,
    TAIL_FRAMES: 1,
    /** 칼끝 메모가 없는 무기(칼 v3 등): 판정 호 반경 × 이 비율 위를 훑는다 (아트 trailFill.bladeTipRadiusDots 가 있으면 그것) */
    FALLBACK_RADIUS_RATIO: 0.65,
    /** 55라운드 내려찍기 쐐기(칼끝 메모 없음): 쐐기 길이 × 이 비율에서 끝점까지 앞으로 떨어진다 (임시) */
    WEDGE_START_RATIO: 0.3,
    /** 텍스처가 없을 때(캔버스 렌더러 등) 선 색: 머리 호박 A25 · 꼬리 재 S2 */
    FALLBACK_HEAD: 0xeecc78,
    FALLBACK_TAIL: 0x756c62,
  },
  /**
   * 55라운드 Q8 재 파편 입자 (계약 §16 `fx/v3/particles_ash` kinds·recipes). 속도·중력·흔들림 길이는 시트 도트 단위 → pixelScale 환산.
   * 위치는 도트 격자에 맞춘다. 동시 다수 적중이면 적마다 MULTI_HIT_FACTOR 배 (아트 제안 절반)
   */
  PARTICLES: {
    POOL: 160,
    MULTI_HIT_FACTOR: 0.5,
    /** 한 프레임 dt 상한 ms (탭 전환 뒤 튐 방지) */
    MAX_STEP_MS: 50,
  },
  /**
   * 화면 섬광·색 오버레이 (42라운드 Q3 임시값). 카메라 위 풀스크린 사각형(scrollFactor 0). 채도 감소는 WebGL 이면 camera.postFX
   * ColorMatrix, 캔버스면 회색 사각형 SATURATION 블렌드. `feelSettings.flash` 로 끔
   */
  SCREEN: {
    /** JSON flash 에 값이 빠졌을 때 기본 (코어 X1 #fff4dc, fx-design §6.2 거합 값) */
    DEFAULT_FLASH: { COLOR: 0xfff4dc, MS: 40, ALPHA: 0.18 },
    /** 치명타 섬광: 설계표(§6.2) 밖 추가 연출 → 기본 꺼짐(ALPHA 0). 켜려면 인터뷰 */
    CRIT: { COLOR: 0xffffff, MS: 40, ALPHA: 0 },
    /** 진화 선택: 층 강조색(램프 index). 설계표 밖 추가 연출 (드묾) */
    EVOLVE: { MS: 200, ALPHA: 0.35, RAMP_INDEX: 7 },
    /** 보스 페이즈 전환: fx-design §6.2 X0 0.35→0 120ms (+ 채도 감소는 설계표 밖 추가) */
    BOSS_PHASE: { COLOR: 0xffffff, MS: 120, ALPHA: 0.35, DESAT_MS: 400, DESAT: 1 },
    /** 히트스톱 중 채도 감소 (0~1): 설계표 밖 추가 연출 → 기본 0(꺼짐) */
    HITSTOP_DESAT: 0,
    /** 사망: 서서히 어둡게 (지속 = 사망 애니 + 추가 대기) */
    DEATH: { COLOR: 0x000000, ALPHA: 0.75, MIN_MS: 600 },
    /** 캔버스 폴백 채도 감소 색 (SATURATION 블렌드) */
    DESAT_FALLBACK_COLOR: 0x808080,
  },
  /** 보조 동작·대쉬 연출 (35라운드 3단계 임시값) */
  SECONDARY: {
    /** 패링 성공 히트스톱 (parry_flash 1프레임이 멈춤 동안 보이도록) */
    PARRY_HITSTOP_MS: 60,
    /** 조준 점선 길이 (칸) */
    AIM_LINE_TILES: 8,
    /** 조준 차지 완료(5프레임) 후 발사되어도 이만큼 유지 */
    AIM_CHARGE_HOLD_MS: 60,
    /** 차지 프레임 = min(마지막, floor(progress × AIM_CHARGE_DIVISOR)) — 아트 B 표 `min(5, floor(progress*5))` (6프레임) */
    AIM_CHARGE_DIVISOR: 5,
    /** 대쉬 잔상 간격 (아트 권장 40~50) */
    DASH_TRAIL_INTERVAL_MS: 45,
    /** 플레이어 몸 중심 = 발 피벗에서 위로 (aim_charge pivotNote). 53라운드 Q1: 주인공 화면 1.5배(48×72) → 11 × 1.5 (임시) */
    BODY_CENTER_UP_PX: 17,
    /** dash_trail 틴트 = 팔레트 fx.weapons[무기].ramp index (1 = W1 body dark). fx 블록이 없으면 틴트 없음 */
    DASH_TRAIL_RAMP_INDEX: 1,
    /** dash_trail 을 틴트하는 개성 노드 (JSON tint.when: 발도술·허보·잔상). 경로에 하나라도 있으면 */
    DASH_TRAIL_TINT_NODES: ['batto', 'longinvuln', 'afterimage'] as readonly string[],
    /** 55라운드 Q13: v3 대쉬 잔상은 따뜻한 재 그대로 — 노드 틴트(평면 채움)를 끈다 */
    DASH_TRAIL_TINT: false,
  },
};

/**
 * 적·보스 공격 양상 (35라운드 2단계 임시값, 결정 로그 round-35 "시스템 반영 기록 2단계").
 * 수치(예고 시간·사거리·재장전 등)는 data/enemies.json·bosses.json, 여기는 연출·시트 이름만.
 */
export const ENEMY_FX = {
  /** 예고 마커 시트 (계약 §3, anchor hitbox_center). 없으면 Graphics 점선/원 플레이스홀더 */
  TELEGRAPH_IDS: { LINE: 'telegraph_line', CIRCLE: 'telegraph_circle', CONE: 'telegraph_cone' },
  /** 적 탄·보스 탄·총구 화염 시트 */
  BULLET: 'enemy_bullet',
  FAN_SHOT: 'boss_fan_shot',
  MUZZLE: 'muzzle_flash',
  /** telegraph_circle·cone 시트의 기준 반지름(px): 실제 범위 R 이면 scale = R / 15 (아트 JSON pivotNote) */
  MARKER_BASE_RADIUS: 15,
  /** 원 마커로 대신 그리는 부채꼴 각도 하한 (cone 시트 반각 32° 를 크게 넘는 광각 부채꼴) */
  CONE_MAX_SPREAD_DEG: 120,
  /** 54라운드 꺾은선 예고: 경고광을 다는 마디 수 (어둠 속 경로 판독) */
  PATH_LIGHT_POINTS: 5,
  /** 플레이스홀더 마커: 깜빡 주기·선 두께·점선 간격·색(G13 / 층 램프는 안 씀) */
  PLACEHOLDER: { BLINK_MS: 120, LINE_WIDTH: 2, DASH_PX: 6, GAP_PX: 4, COLOR: 0xd8d9db, ALPHA: 0.85 },
  /** 총구 화염 위치: 사수 바디 중심에서 바라보는 방향으로 전방·위 (아트 JSON pivotNote ±8px, -2px) */
  MUZZLE_FORWARD_PX: 8,
  MUZZLE_UP_PX: 2,
  /** 내리찍기 충격파 플레이스홀더(boss_slam 시트가 없을 때) 링 지속 */
  SLAM_RING_MS: 260,
  /**
   * 보스 내리찍기 충격파 시트 (46라운드 Q2, 계약 §3.2): 96×96 피벗 = 슬램 지점. 층 램프 + 코어만(보조색 없음)이라
   * JSON flash·shake 훅을 그대로 쓴다(이때 BOSS_WALL 흔들림은 생략). 배율 = 판정 반경 / 기준 반경(JSON hitRadiusPx,
   * 없으면 SLAM_BASE_RADIUS_PX) 이 정수일 때만, 아니면 1
   */
  SLAM_ID: 'boss_slam',
  SLAM_BASE_RADIUS_PX: 40,
  /** 소환 위치: 보스 바디 반폭 + 이 거리(px) 양옆 */
  SUMMON_GAP_PX: 12,
  /** 수렴 오라 시트 (43라운드 신규, 없으면 Graphics 원) */
  AURA_ID: 'telegraph_aura',
  /**
   * 굵은 예고 (42라운드 Q3 · fx-design §6.3). 43라운드 시트는 선 4px(기존 2px 의 2배)·원/부채꼴 진행도 6프레임이라
   * 시트가 굵기·닫히는 원을 그린다. 시스템은 화살촉·수렴 오라·마감 직전 깜빡임 가속을 더하고, 시트가 없으면 Graphics 로 같은 구조
   */
  BOLD: {
    /** 선 시트 세로 배율 (43라운드 시트는 이미 4px → 1) */
    LINE_SCALE_Y: 1,
    /** 화살촉: 선 끝 삼각형 길이·반폭 px. 색 = 층 램프 [몸, 테두리] index (22 → 6, 18 → 2) */
    TIP_LENGTH: 6,
    TIP_HALF_WIDTH: 4,
    TIP_RAMP_INDEX: 6,
    TIP_EDGE_RAMP_INDEX: 2,
    /** 플레이스홀더 닫히는 원 (시트가 없을 때만) */
    CLOSING_FILL_ALPHA: 0.18,
    CLOSING_LINE_ALPHA: 0.9,
    CLOSING_LINE_WIDTH: 1,
    CLOSING_MIN_RATIO: 0.1,
    /** 진행도 프레임 = min(마지막, floor(progress × PROGRESS_DIVISOR)) — telegraph_circle pivotNote */
    PROGRESS_DIVISOR: 6,
    /** 43라운드 시트 기준 반지름 px (pivotNote: 원 r22 → scale R/22, 부채꼴 r27 → scale R/27) */
    CIRCLE_BASE_RADIUS: 22,
    CONE_BASE_RADIUS: 27,
    /** 수렴 오라 배율 (64 시트 r30 → 정수 배율 1 유지, 픽셀 보존) · 플레이스홀더 반지름 */
    AURA_SCALE: 1,
    AURA_PLACEHOLDER_RADIUS: 10,
    /** 마감 직전 구간 ms · 깜빡임 가속 배수 · 깜빡일 때 낮은 알파 */
    FINAL_MS: 160,
    FINAL_BLINK_DIV: 3,
    FINAL_LOW_ALPHA: 0.45,
    /** 플레이스홀더 선 두께 (기존 2 의 2배) */
    PLACEHOLDER_LINE_WIDTH: 4,
  },
};

export const DEBUG = {
  /** 시스템 파트 임시 디버그 텍스트. HUD는 UI 파트 소유이므로 이것은 HUD가 아니다. */
  SHOW_TEXT: true,
  FONT: '12px monospace',
  /**
   * 55라운드 §17 판정 모양 오버레이 (`?debug` 에서 켜짐, `&hitshapes=0` 끔): 판정이 살아 있는 동안 윤곽, 그 뒤 FADE_MS 동안 흐려짐.
   * 색 = 모양별 (호·쐐기·찌르기·고리), 후속 판정(잔상 베기·충격파)은 FOLLOW
   */
  HIT_SHAPES: {
    PARAM_OFF: 'hitshapes',
    LINE_PX: 1,
    LINE_ALPHA: 0.95,
    FILL_ALPHA: 0.18,
    FADE_MS: 220,
    COLORS: { arc: 0x7fe0ff, wedge: 0xffb040, thrust: 0x9cff7a, ring: 0xff6ad5, follow: 0xffffff } as Record<
      string,
      number
    >,
  },
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
  /** 45라운드 Q2: 비전투 중 누르는 동안 달리기 (배율은 data/player.json sprint) */
  SPRINT: 'SHIFT',
  /** 47라운드 Q5: 구조물 상호작용 (E 누르기, 묘는 2초 누르기). 키 이름은 data/structures.json rules.interactKey 와 같다 */
  INTERACT: 'E',
  /** 49라운드: 활 수동 장전 (임시). 게임 중 R 은 다른 용도가 없다 — 재시작 R 은 결과 화면(GameOver) 전용 */
  RELOAD: 'R',
  /** 49라운드 계약 §11.4: 무기 시험장 메뉴(무기·개성 갈래) 열기 (임시) */
  LAB_MENU: 'L',
  /** 51라운드 Q4: 무기 넣기/뽑기 (칼·대검 — 넣은 채 첫 타 보너스, 넣은 동안 기력 회복↑) */
  CARRY: 'F',
} as const;

/**
 * 49라운드 Q3·Q5 무기 휴대 폴백 (임시값): 휴대 시트(weapons/<w>_carry_<동작>)가 없을 때
 * 기존 attack 무기 시트 0프레임을 휴대 위치에 작게 겹친다. 오프셋은 발 피벗 기준 월드 px, 방향별
 */
export const CARRY = {
  /** 칼집·등에 넣은 무기 축소 배율 · 손에 든 무기(단검·활·뽑은 칼·대검) 배율 */
  STOWED_SCALE: 0.6,
  HAND_SCALE: 0.8,
  /** 허리 칼집 (칼): 오프셋 · 기울기(도) · 몸 뒤(below) 여부 */
  SHEATH: {
    down: { x: 5, y: -8, angle: 70, below: false },
    up: { x: -5, y: -8, angle: 110, below: true },
    left: { x: 2, y: -8, angle: 160, below: false },
    right: { x: -2, y: -8, angle: 20, below: false },
  },
  /** 등 (대검): 대각선으로 멘 모습 */
  BACK: {
    down: { x: 0, y: -14, angle: -45, below: true },
    up: { x: 0, y: -14, angle: -45, below: false },
    left: { x: 4, y: -14, angle: -60, below: true },
    right: { x: -4, y: -14, angle: -120, below: true },
  },
  /** 손 (단검·활·뽑아 든 칼·대검) */
  HAND: {
    down: { x: 5, y: -6, angle: 0, below: false },
    up: { x: -5, y: -6, angle: 0, below: true },
    left: { x: -4, y: -6, angle: 0, below: false },
    right: { x: 4, y: -6, angle: 0, below: false },
  },
} as const;

/**
 * 49라운드 계약 §11.4 무기 시험장 (임시값). 작은 아레나 · 중앙 허수아비(무한 체력) ·
 * 일정 방향으로 투사체를 쏘는 허수아비 · 플레이어는 죽지 않는다(HP 자동 회복)
 */
export const LAB = {
  /** 아레나 내부 크기(타일) */
  ARENA_W: 22,
  ARENA_H: 14,
  /** 허수아비 크기 px · 색 (색은 시트가 없을 때의 단색 사각형) */
  DUMMY_SIZE: [16, 20] as [number, number],
  DUMMY_COLOR: '#b08850',
  TURRET_COLOR: '#8a6db0',
  /**
   * 그림 시트 이름 (= 적 id, v3 전용 SPRITES.V3_ONLY). 허수아비 = dummy, 사수 허수아비 = archer.
   * 49라운드 이후 'lab_dummy'·'lab_turret' 시트는 없어 늘 단색 사각형이었다 — 53라운드 후속 수정
   */
  DUMMY_SHEET: 'dummy',
  TURRET_SHEET: 'archer',
  /** 사수 허수아비: 아레나 중심에서의 위치(타일) · 발사 방향 · 간격 · 탄 */
  TURRET_OFFSET_TILES: { x: 7, y: -4 },
  TURRET_DIR: { x: -1, y: 0 },
  TURRET_INTERVAL_MS: 1400,
  TURRET_SHOT: { speedPx: 110, attack: 8, size: 5, lifeMs: 3500 },
  /** 플레이어 HP 가 이 비율 아래로 내려가면 가득 채운다 (시험장은 죽지 않음) */
  HEAL_BELOW_RATIO: 0.5,
  /** 시험장 시드 (지도 생성용 고정값) */
  SEED: 'weapon-lab',
} as const;

/** 49라운드 무기 동작 연출 (임시값) */
export const WEAPON_FX = {
  /** 단검 과열: 가열 단계 시트가 없을 때 연격 이펙트 배율 = 1 + 단계 × 값 */
  HEAT_SCALE_PER_STAGE: 0.12,
} as const;

/**
 * 비전투 이동 연출 (45라운드 임시값). 달리기 배율·가속은 data/player.json `sprint`.
 * 달리기와 대쉬: 대쉬는 거리·속도 그대로(배율 미적용), 대쉬 동안 달리기 배율을 유지해 끝나면 이어서 달린다.
 */
export const TRAVERSAL = {
  /** 달리기 발밑 먼지: dash_dust 시트를 작게·옅게 주기적으로 (시트가 없으면 작은 회색 점) */
  SPRINT_DUST: {
    SHEET: 'dash_dust',
    INTERVAL_MS: 140,
    SCALE_MULT: 0.75, // 45라운드 Q11 (0.5 → 0.75)
    ALPHA: 0.85, // 45라운드 Q11 (0.6 → 0.85)
    /** 시트 없을 때 점 반지름·지속·색 (넉백 먼지 G7) */
    DOT_RADIUS: 1.5,
    DOT_MS: 220,
    DOT_COLOR: 0x6c6f73,
  },
};

/**
 * 47라운드 상호작용 구조물 연출 (임시값). 규칙·수치는 data/structures.json, 여기는 그림·깊이만.
 * 아트 시트(계약 art-assets §5)가 없으면 플레이스홀더 도형(데이터 placeholder.color + 짧은 글자)으로 그린다.
 */
export const STRUCTURE_FX = {
  /** 시트 이펙트 내부 동작 이름 (`sheet_<id>_st`) */
  SHEET_ACTION: 'st',
  /** 바닥형(링·룰렛) 깊이: 소품 위, 그림자 아래 */
  FLOOR_DEPTH: 0.6,
  /** 50라운드 occludeAbove 받침(피벗~occludeAbove 높이) 깊이: 바닥형 위, 그림자·개체 아래 */
  OCCLUDE_BASE_DEPTH: 0.7,
  /** 플레이스홀더: 채움 알파 · 바닥형 채움 알파 · 테두리 · 글자 */
  FILL_ALPHA: 0.9,
  FLOOR_FILL_ALPHA: 0.22,
  STROKE_COLOR: 0x101014,
  STROKE_WIDTH: 1,
  LABEL_FONT: '10px monospace',
  LABEL_COLOR: '#f0e8d8',
  /** 다 쓴 구조물 알파 (시트에 used 상태가 없을 때) */
  USED_ALPHA: 0.45,
  /** 맞음 깜빡임 */
  HIT_FLASH_MS: 80,
  HIT_FLASH_COLOR: 0xffffff,
  /** 부서짐 파편 (시트에 broken 이 없을 때) */
  DEBRIS_COUNT: 4,
  DEBRIS_MS: 260,
  DEBRIS_DIST_PX: 10,
  /** 독주 웅덩이·불바다 (fire_pool 시트가 없을 때) */
  PUDDLE_COLOR: 0xb06a20,
  PUDDLE_ALPHA: 0.35,
  FIRE_COLOR: 0xff7a1a,
  FIRE_ALPHA: 0.45,
  /** 화상 표시 (적 깜빡임) · 불붙은 무기(플레이어 틴트 깜빡임 간격) */
  BURN_COLOR: 0xff8a2a,
  FIRE_WEAPON_BLINK_MS: 240,
  /** 숨은 벽 단서: 호박 빛 1px 선 */
  CRACK_COLOR: 0xe0a040,
  /** 투견 링 시작: 플레이어를 링 중심에서 아래로 이 칸만큼 (링 안) */
  RING_ENTER_TILES: 2,
} as const;

/**
 * 56라운드 무기 피드백 (결정 2026-10-04-round-56) 연출 상수. 수치·게임 규칙은 data/weapons.json·player.json (임시값 표는 보고서)
 */
export const FEEDBACK = {
  /** Q36: 적 피격 번쩍임 — 호박 반투명, 80ms, 히트스톱으로 늘어나지 않음(트윈 시계) */
  MOB_HURT: { ALPHA: 0.55, MS: 80 },
  /**
   * Q12·Q50: 적중 순간 무기 그림이 크게 번쩍 — 판정 1프레임(WHITE_MS)만 백열 X1 #fff4dc, 그다음 호박 A25 #eecc78 로 식으며 사라짐
   * (더하기 혼합 사본, 트윈 시계 — 히트스톱 동안에도 진행)
   */
  BLADE_FLASH: { COLOR: 0xfff4dc, AMBER: 0xeecc78, WHITE_MS: 34, ALPHA: 0.85, SCALE: 1.12, MS: 110 },
  /** Q7·Q8: 월드 문구 (PERFECT GUARD · PARRY) — 몸 위에서 떠올라 사라짐 */
  CALLOUT: {
    FONT_PX: 11,
    COLOR: '#f4de9b',
    STROKE: '#2a1e17',
    STROKE_PX: 3,
    OFFSET_Y: -22,
    RISE_PX: 10,
    HOLD_MS: 420,
    FADE_MS: 260,
    POOL: 4,
  },
  /** 칼 검기 3단 칼날 빛 (아트 오버레이가 오기 전 임시 곱 틴트: 재 → 호박 → 백열) */
  KENKI_TINT: [0xb8aca0, 0xeecc78, 0xfff4dc] as readonly number[],
  /** 그로기 몸 틴트 (아트 그로기 자세가 오기 전 임시) */
  GROGGY_TINT: 0x8a8070,
  /**
   * 단검 낙인: 표식 fx (행 = 스택, 적 시트 윗변 + 여백 4 월드 px, 찍힘 뒤 2~5 반복) · 폭발 fx (행 s·m·l) ·
   * 시트가 없을 때 작은 마름모(Graphics)
   */
  BRAND: {
    MARK_SHEET: 'dagger_brand_mark',
    BURST_SHEET: 'dagger_brand_burst',
    MARK_LOOP_FROM: 2,
    HEAD_GAP_PX: 4,
    COLOR: 0xe2a33c,
    EDGE: 0x2a1e17,
    SIZE_PX: 2,
    GAP_PX: 5,
    OFFSET_Y: 6,
  },
  /** 단검 과열 100%: 전용 폭발 fx (주인공 발) · 식는 동안 루프 · 낙인 적 연쇄 간격 */
  OVERHEAT: { SHEET: 'dagger_overheat_burst', COOL_SHEET: 'dagger_overheat_cool', CHAIN_MS: 40 },
  /** 퍼펙트 가드·패링 fx (행 guard·parry, 맞닿은 점 = 판정 원점에서 공격자 쪽 6 월드 px, 공격자 방향 회전) */
  GUARD_FX: { SHEET: 'guard_perfect_fx', CONTACT_PX: 6 },
  /** 그로기: 몸 루프 · 머리 위 소용돌이 (머리 꼭대기 = 몸 JSON headTopAnchors, 없으면 OFFSET) */
  GROGGY: { SWIRL_SHEET: 'player_groggy_swirl', SWIRL_FALLBACK_Y: -29 },
  /** 대검 울분 가득 몸 틴트 깜빡임 (임시) */
  GRUDGE_FULL_TINT: 0xe2a33c,
  /** 활 숨 집중(감속 정밀 조준) 시작 화면 섬광 (임시) — 물리 배속은 data bow.gauge.focusTimeScale */
  FOCUS_FLASH: { COLOR: 0xeecc78, MS: 320, ALPHA: 0.14 },
  /** 일섬 선 깊이: 바닥 바로 위 (주인공·적 아래) — 아트 depth below_player */
  ISSEN_LINE_DEPTH: 0.96,
  /** 그림자 걸음 리본 (Q38 돌진류만): 출발 → 도착을 이 시간에 긋는다 */
  SHADOWSTEP_RIBBON_MS: 90,
} as const;

export { BOSS_FX } from './BossConstants';
export { MOVE_FX } from './MoveConstants';
