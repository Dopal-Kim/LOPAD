/** 텍스처 키·에셋 경로·오디오 재생·스프라이트 연출 (57라운드 B6: core/Constants.ts 에서 분리) */

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
  /** 61라운드: 보스 처치 순간 BGM 페이드아웃 ms — 보상 메뉴가 끝날 때(EXIT_OPENED)까지 정적, 그 뒤 층 곡 */
  BOSS_DEFEAT_FADE_MS: 900,
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
