/** 씬 키·탄생 연출·노드 전환·시험장·디버그·임시 화면 글꼴 (57라운드 B6: core/Constants.ts 에서 분리) */

export const SCENES = {
  BOOT: 'Boot',
  PRELOADER: 'Preloader',
  SETUP: 'Setup',
  GAME: 'Game',
  GAME_OVER: 'GameOver',
  /** 49라운드 계약 §11.4: 무기 시험장 (host.startWeaponLab 이 이 키로 시작) */
  WEAPON_LAB: 'WeaponLab',
  /** 61 단계 6 계약 §19: 수련장 (Game 의 시험장 모드 + 수련장 방 — host.startTraining 이 이 키로 시작) */
  TRAINING: 'Training',
  /**
   * 62 §20 시작 의식 대체 화면 (시스템): UI 의식 씬(`UI_SCENES.RITUAL`)이 없을 때 Setup 위에 띄우는 최소 화면 —
   * UI 와 같은 계약(스냅샷 ritual · uiCommands.ritual)만 쓴다
   */
  RITUAL_VIEW: 'RitualView',
} as const;

/**
 * 62 루프 1 (계약 §20, P15) 시작 의식 흐름 시간·대체 화면 (엔진·연출 값 — 문구·과제 수치는 data/narrative.json ritual).
 * 대체 화면 글꼴은 Galmuri11 (34라운드 글꼴 규칙 — 고정폭 글꼴 금지, 로드 전이면 sans-serif)
 */
export const RITUAL = {
  /** 3획째를 뗀 뒤 다음 단계까지 (UI 낙관·스며듦 연출 시간) */
  SEAL_MS: 1400,
  /** 운명 공개를 보여 주는 시간 (ritual.next 로 바로 넘길 수 있다) */
  FATE_MS: 4200,
  /** 회피 시험 끝 → 운명 공개까지 (마지막 과제 결과를 보여 줌) */
  TRIAL_RESULT_MS: 1400,
  /** 62 P1-10: 첫 생에 화면 아래 4동사 키 막대를 보여 주는 노드 단 수 (탄생지·길·초소) */
  KEY_BAR_NODES: 3,
  /** 대체 화면: 글꼴 · 크기(논리 px) · 색 · 종이 바탕 */
  VIEW: {
    FONT_FAMILY: 'Galmuri11',
    FONT_FALLBACK: 'sans-serif',
    BODY_PX: 11,
    TITLE_PX: 22,
    INK: '#2a2018',
    INK_SOFT: '#5a4a38',
    PAPER: 0xd8c8a4,
    PAPER_ALPHA: 0.94,
    PAPER_EDGE: 0x8a7656,
    /** 일기장 종이 (논리 px — 가운데 기준 폭·높이) */
    PAGE_W: 420,
    PAGE_H: 300,
    /** 시험 중 과제 목록 (오른쪽 위) */
    TASK_X: 948,
    TASK_Y: 14,
    HINT_Y: 516,
    LIGHT: '#e8dcc0',
    DIM: '#9a8a70',
  },
} as const;

/** 62 회피 시험(탄생 전장) 손맛·그림 값 (옛 dodgeTrial PLAYER 블록을 옮김 — 과제 수치는 data/narrative.json ritual.trial) */
export const RITUAL_TRIAL_FEEL = {
  PLAYER: {
    /** 판정 원 반지름 (월드 px) · 발 피벗과 판정 중심 사이 */
    HIT_RADIUS_PX: 5,
    FOOT_OFFSET_PX: 7,
    /** 바닥 판정: 발 둘레 4점 거리 (px) */
    FOOT_RADIUS_PX: 4,
    /** 피격 뒤 무적·깜빡임 */
    INVULN_MS: 650,
    BLINK_MS: 70,
    /** 밀려남: 맞은 방향으로 거리·시간 (감속) */
    KNOCK_TILES: 1.6,
    KNOCK_MS: 170,
    FLASH_MS: 80,
    /** 대쉬 잔상 수·지속·알파 */
    GHOSTS: 3,
    GHOST_MS: 220,
    GHOST_ALPHA: 0.45,
    SHADOW: { W: 12, H: 5, ALPHA: 0.35 },
    SHAKE_MS: 110,
    SHAKE_INTENSITY: 0.006,
  },
  /** 화살 판정 반지름 · 그림이 없을 때 원 지름·색 · 동시 최대 수 */
  BULLET_RADIUS_PX: 2.5,
  BULLET_PLACEHOLDER_PX: 5,
  BULLET_PLACEHOLDER_COLOR: 0xe8c070,
  BULLET_POOL: 48,
  /** 사수 몸 (월드 px — enemies.json archer size 와 같게) · 그림 시트 이름 */
  SHOOTER_SHEET: 'archer',
  SHOOTER_BODY: [14, 14] as [number, number],
  SHOOTER_PLACEHOLDER: 0xc08a30,
  /** 겨눔 선: 굵기 · 색 · 알파 (끝으로 갈수록 옅게) · 길이(타일) */
  AIM_LINE_PX: 1,
  AIM_COLOR: 0xffc860,
  AIM_ALPHA: 0.7,
  AIM_TILES: 6,
  /** 화살이 나오는 자리: 사수 발에서 위로 (px) */
  MUZZLE_UP_PX: 8,
} as const;

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
  /**
   * 62 H: 지도에서 노드를 고른 뒤 짧은 먹 번짐 암전 (`ui:transition-begin{mode:'fade', durationMs}` — UI 덮기 시간 힌트, 결정 0.35~0.5초).
   * UI 렌더러가 없으면 FADE_OUT_MS 카메라 암전
   */
  MAP_FADE_MS: 400,
  /** 62 H: 노드 진입 뒤 지도 미리보기 그림을 받기 시작하기까지 (입구 걸음·밝아짐 뒤) */
  PREVIEW_DELAY_MS: 900,
};

export const DEBUG = {
  /** 시스템 파트 임시 디버그 텍스트. HUD는 UI 파트 소유이므로 이것은 HUD가 아니다. */
  SHOW_TEXT: true,
  FONT: '12px monospace',
  /**
   * 55라운드 §17 판정 모양 오버레이 (62라운드 P2-12: `?debug&hitshapes=1` 일 때만 켜짐 — 기본 꺼짐): 판정이 살아 있는 동안 윤곽, 그 뒤 FADE_MS 동안 흐려짐.
   * 색 = 모양별 (호·쐐기·찌르기·고리), 후속 판정(잔상 베기·충격파)은 FOLLOW
   */
  HIT_SHAPES: {
    PARAM: 'hitshapes',
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

/**
 * 시스템 임시 메뉴(UI 렌더러가 없을 때의 TextMenu)·시험장 허수아비 이름표 글꼴. 960×540 기준 (32라운드).
 * 62: 시작 의식·결과 화면은 쓰지 않는다 (RITUAL.VIEW — Galmuri11)
 */
export const PLACEHOLDER_UI = {
  FONT_BODY: '14px monospace',
};

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
  /** 61 단계 6 수련장 바닥·벽 타일셋 (art §28 `tiles/v2/stage1_training` — gate 와 같은 색인·규칙) */
  TRAINING_TILESET: 'stage1_training',
  /** 62 D (P1-17): 수련장 지도 그림을 기다리는 최대 ms (넘으면 그림 없이 연다) */
  TRAINING_MAP_WAIT_MS: 1500,
} as const;

/**
 * 57라운드 A2 무기 시트 로드 표시 (런 시작·이어하기·시험장 무기 교체 — Game preload). 전환 암전 안 화면 가운데에 작게,
 * 로드가 끝나면(create 전) 지운다. 문구·글꼴 임시값
 */
export const WEAPON_LOAD = {
  TEXT: '불러오는 중…',
  FONT: '12px monospace',
  COLOR: '#8a8a96',
};

/** 62 루프 2 시스템 D (P2-6) 다음 노드 미리 읽기: 싸움 없는 노드(장터·쉼터·사연)에서 들어선 뒤 시작까지 ms */
export const NODE_PREFETCH = {
  CALM_DELAY_MS: 2500,
} as const;
