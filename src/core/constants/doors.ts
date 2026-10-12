/**
 * 62 루프 2 시스템 E — 문 나가기 (발판 출구 대체) · 메뉴 입력 가드. 전부 임시값 (CHANGELOG 62 루프 2 E 절).
 * 길이 단위: 타일(TILE) 또는 월드 px 를 이름에 적는다.
 */
export const DOORS = {
  /** 문 폭 (칸) — 외벽 문 그림의 통로 폭 openingW/H 96 논리 px = 3칸 */
  OPEN_TILES: 3,
  /** 나갈 때: 문턱(벽 안쪽 1칸 띠)에서 문 쪽으로 걸어 들어가는 끝 = 바닥 끝에서 바깥으로 이만큼 (칸) */
  OUT_WALK_TILES: 2.5,
  /** 몸이 흐려지기 시작하는 곳 = 바닥 끝 · 다 흐려지는 거리 (칸) */
  FADE_TILES: 2,
  /** 들어올 때: 0.6초 자동 걸음 (주인공 기본 걸음 속도로 이만큼 — 시작점은 바닥 끝 바깥 문 안) */
  ENTER_WALK_MS: 600,
  /** 들어올 때 목표: 시작점(spawn)이 문에서 이 칸보다 멀면 문에서 ENTER_STOP_TILES 안쪽에서 멈춘다 (수련장 방) */
  ENTER_SPAWN_MAX_TILES: 4.5,
  ENTER_STOP_TILES: 2.6,
  /** 걸음 안전장치: 이 시간 안에 못 닿으면 그 자리에서 끝낸다 (ms) */
  WALK_TIMEOUT_MS: 1600,
  /** 닿음 판정 (월드 px) */
  ARRIVE_PX: 2,
  /** 지도 고르기 취소 때 문 안에서 문턱 안쪽으로 걸어 나오는 거리 (바닥 끝에서 안쪽, 칸) */
  STEP_BACK_TILES: 1.8,
  /** 열림 연출: 막힘(어둠 판)이 걷히는 시간 · 빛이 차오르는 시간 (ms) */
  OPEN_MS: 520,
  LIGHT_MS: 700,
  /** 닫힌 문 막힘 판: 색 · 알파 · 문 그림 통로 깊이 (칸, 바닥 끝에서 바깥으로) · 널문 판자 수 · 색 · 두께 · 사이 (월드 px) */
  BARRIER_COLOR: 0x07070a,
  BARRIER_ALPHA: 0.9,
  BARRIER_DEPTH_TILES: 1.6,
  BARRIER_PLANKS: 2,
  BARRIER_PLANK_COLOR: 0x3a2716,
  PLANK_PX: 2,
  PLANK_GAP_PX: 2,
  /** 열린 문 빛 (호박 — art §28 무기 색과 다른 따뜻한 등불) */
  LIGHT_COLOR: '#eeb46a',
  LIGHT_RADIUS_PX: 64,
  LIGHT_INTENSITY: 0.95,
  LIGHT_FLICKER: 0.05,
  /** '오르는 길' 방향 표시: 문턱 앞 바닥 갈매기 3개 (월드 px · 색 · 알파 맥박 · 주기 ms) */
  CHEVRON_COUNT: 3,
  CHEVRON_GAP_PX: 7,
  CHEVRON_HALF_PX: 5,
  CHEVRON_LEN_PX: 4,
  CHEVRON_LINE_PX: 1.5,
  CHEVRON_COLOR: 0xf2c46e,
  CHEVRON_ALPHA: [0.25, 0.9] as [number, number],
  CHEVRON_PERIOD_MS: 900,
  /** 문 그림이 없을 때(테두리 없음·로드 실패) 문 자리 어둠 (월드 px, 바닥 끝에서 바깥으로) */
  FALLBACK_DARK_PX: 22,
  /** 그림 깊이: 막힘 판·어둠 = 테두리 문 조각 위 · 갈매기 = 바닥 데칼 위 */
  DEPTH_BARRIER: 0.275,
  DEPTH_CHEVRON: 0.03,
} as const;

/**
 * 62 루프 2 시스템 E: 메뉴 입력 가드 — 메뉴가 열린 뒤 ARM_MS 동안 선택 명령(메뉴 select · chooseNode)을 무시한다.
 * 시계는 performance.now() (UI 와 같은 시계 — `UiMenu.openedAt`). `?menuguard=0` 이면 끔(검증용)
 */
export const MENU_GUARD = {
  ARM_MS: 400,
  PARAM: 'menuguard',
  /**
   * '인터페이스 뜨기 전 렉' (헤드리스 측정 — CHANGELOG): 방을 비운 순간 성과 등급(완)이 게이지를 넘기면 개성 발현 메뉴가 곧장 게임을
   * 멈췄는데, UI 는 성과 카드(2.86초)가 끝날 때까지(최대 1.2초) 메뉴를 미뤄 그동안 화면이 멈춘 것처럼 보였다 → 등급 뒤 카드가 거의
   * 끝날 때까지 눈금 메뉴를 열지 않는다 (게임은 그대로 — 방은 이미 비었고, 남은 눈금이 있으면 문은 열려도 나가지 않는다).
   * 막타 슬로모 중에도 열지 않는다
   */
  GRADE_HOLD_MS: 2700,
  /** 다음 눈금이 각성이면 게이지가 이 비율을 넘을 때 각성 연출 시트를 미리 받는다 (메뉴가 뜨는 순간 로드·업로드가 겹치지 않게) */
  AWAKEN_PREFETCH_AT: 0.5,
  /** 가드 없는 메뉴 id — 'meta'(영혼 강화)는 고를 것이 없으면 UI 가 40ms 뒤 스스로 'enter' 를 보낸다 */
  EXEMPT: ['meta'] as readonly string[],
} as const;
