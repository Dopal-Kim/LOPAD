/** 씬 키·탄생 연출·노드 전환·시험장·디버그·임시 화면 글꼴 (57라운드 B6: core/Constants.ts 에서 분리) */

export const SCENES = {
  BOOT: 'Boot',
  PRELOADER: 'Preloader',
  SETUP: 'Setup',
  GAME: 'Game',
  GAME_OVER: 'GameOver',
  /** 49라운드 계약 §11.4: 무기 시험장 (host.startWeaponLab 이 이 키로 시작) */
  WEAPON_LAB: 'WeaponLab',
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

/**
 * 57라운드 A2 무기 시트 로드 표시 (런 시작·이어하기·시험장 무기 교체 — Game preload). 전환 암전 안 화면 가운데에 작게,
 * 로드가 끝나면(create 전) 지운다. 문구·글꼴 임시값
 */
export const WEAPON_LOAD = {
  TEXT: '불러오는 중…',
  FONT: '12px monospace',
  COLOR: '#8a8a96',
};
