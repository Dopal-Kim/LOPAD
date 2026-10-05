/** 적·보스 공격 양상 연출·소환 예고 (57라운드 B6: core/Constants.ts 에서 분리) */

/**
 * 53라운드 Q49 적 소환 예고 (UI 는 튜토리얼에서만 '주의' 경고): 예고 뒤 소환까지 ms. 임시값.
 * 61라운드 단계 2: 일반 시련 웨이브도 같은 숨(0 → 900) — 1층 노드가 웨이브 3개라 웨이브 사이 박자를 둔다
 */
export const ENEMY_INCOMING = { TUTORIAL_DELAY_MS: 900, WAVE_DELAY_MS: 900 };

/**
 * 61라운드 플레이 점검 '공격 토큰': 일반 적의 접촉 공격은 무리 전체에서 이 간격에 한 번만 (무리에 둘러싸여도 한꺼번에 맞지 않는다 —
 * 첫 전투가 '배우는 전투'가 되게). 보스·패링 창은 예외. 돌진·탄은 따로 (예고가 있다)
 */
export const ENEMY_CONTACT_TOKEN = { GAP_MS: 900 };

/**
 * 적·보스 공격 양상 (35라운드 2단계 임시값, 결정 로그 round-35 "시스템 반영 기록 2단계").
 * 수치(예고 시간·사거리·재장전 등)는 data/enemies.json·bosses.json, 여기는 연출·시트 이름만.
 */
export const ENEMY_FX = {
  /**
   * 61라운드 점검 #6: 보스 등불 끄기 동안 예고를 바닥 깊이(DEPTH.FX_GROUND 0.95)에서 라이트맵(DEPTH.LIGHTMAP 2) 바로 위로
   * 올리는 깊이 차 (0.95 + 1.07 = 2.02 — 빛 번짐 2.01 위, 촛대 안내 2.05 아래)
   */
  DARK_LIFT: 1.07,
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
