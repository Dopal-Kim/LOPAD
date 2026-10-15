/** 적·보스 공격 양상 연출·소환 예고 (57라운드 B6: core/Constants.ts 에서 분리) */

/**
 * 53라운드 Q49 적 소환 예고 (UI 는 튜토리얼에서만 '주의' 경고): 예고 뒤 소환까지 ms. 임시값.
 * 61라운드 단계 2: 일반 시련 웨이브도 같은 숨(0 → 900) — 1층 노드가 웨이브 3개라 웨이브 사이 박자를 둔다
 */
/**
 * 53라운드 Q49 소환 예고 → 62라운드 P0-8 입장 유예: 예고(바닥 문양) 길이 · 노드 첫 웨이브에 더하는 숨 돌릴 틈 ·
 * 나온 직후 일어서는 시간(움직임·공격 없음, 맞을 수는 있다). 데드셀·하데스의 등장 연출 0.8~1.5초 기준
 */
export const ENEMY_INCOMING = {
  TUTORIAL_DELAY_MS: 1000,
  /** P19 ④D: 등장 연출 0.6초 (1000 → 600 — 웨이브 사이 '적 0' 공백 ≤ 1.5초) */
  WAVE_DELAY_MS: 600,
  /** P19 ④D 겹치는 웨이브: 살아 있는 적이 이번 웨이브 수의 이 비율 이하가 되면 다음 웨이브를 바로 예고 (마지막만 전멸 = 클리어) */
  WAVE_OVERLAP: 0.3,
  FIRST_WAVE_EXTRA_MS: 500,
  ARRIVE_MS: 350,
  /** 바닥 문양 (SpawnMarks): 먹 번짐 반경(월드 px)·불씨 고리 색·광원 */
  MARK: {
    INK: 0x0c0a09,
    INK_ALPHA: 0.72,
    EMBER: 0xd0582c,
    R_FROM: 3,
    R_TO: 10,
    RING_PX: 1,
    FADE_MS: 220,
    LIGHT: { color: '#d0582c', radius: 22, intensity: 0.55, flicker: 0.2 },
  },
};

/**
 * 62라운드 P1-4 적 가독성 (MobReadability — 엔터 더 건전·Dungeon Survivors 의 차가운 림 + 피해 입은 적만 작은 HP 막대):
 * - RIM: 일반 적 둘레 외곽선 시트를 차가운 채움색으로 적 바로 아래 (주인공 빛은 따뜻하다 — 반대 색). 알파는 적 알파와 곱
 * - HP_BAR: 머리 위 GAP 월드 px, 폭 W·높이 H (월드 px — 화면 ×4), 바탕 PAD. 방금 깎인 몫(TRAIL)은 초당 TRAIL_PER_S 비율로 줄어든다
 */
export const ENEMY_READABILITY = {
  RIM: { ON: true, COLOR: 0x9db8e8, ALPHA: 0.6 },
  HP_BAR: {
    ON: true,
    W: 14,
    H: 1,
    PAD: 0.5,
    GAP: 3,
    MIN_FILL: 0.5,
    BACK: 0x120c0a,
    BACK_ALPHA: 0.8,
    FILL: 0xd8443a,
    TRAIL: 0xf2dcc0,
    TRAIL_PER_S: 0.9,
  },
};

/**
 * P19 적 무리 (방향 문서 ④C · 계약 free-combat §2): 접촉 피해 폐지 — 모든 일반 적은 '예고 → 공격'으로만 때린다.
 * - TOKENS: 동시에 예고·공격 중인 일반 적 최대 수 (정예는 ELITE_TOKENS 따로) · KIND_MAX: 종류별 상한 (징집병은 2마리만 동시에 휘두른다)
 * - RING_TILES: 토큰이 없는 근접 적이 도는 '포위 자리' 반경 [최소, 최대] · ORBIT_RAD_PER_S: 도는 각속도
 * - RETREAT_MS: 공격한 적이 물러나는 시간 [최소, 최대] · COMMIT_MS: 토큰을 받고 붙으러 가는 최대 시간 (못 붙으면 반납)
 * - ENGAGE_TILES: 이 거리 안이어야 토큰을 청한다 · RETRY_MS: 토큰을 못 받았을 때 다시 청하는 간격
 */
export const ENEMY_SQUAD = {
  TOKENS: 3,
  ELITE_TOKENS: 1,
  KIND_MAX: { dummy: 2 } as Record<string, number>,
  RING_TILES: [2, 3.5] as [number, number],
  ORBIT_RAD_PER_S: 0.6,
  RETREAT_MS: [300, 500] as [number, number],
  COMMIT_MS: 1600,
  ENGAGE_TILES: 6,
  RETRY_MS: 250,
};

/**
 * P19 예고 색 언어 (계약 free-combat §2 — 시스템이 그리고 UI·아트가 같은 색): 경고(막기·회피 가능) 호박 · 위험(막을 수 없음) 적 ·
 * 원거리(조준·투척 궤적) 청백 · 기회(버팀 깨짐·띄움) 금. 최소 예고 ms: 일반 350 · 위험 500
 */
export const TELEGRAPH_TIER = {
  warn: 0xffb347,
  danger: 0xff4a3a,
  ranged: 0x9fd8ff,
  chance: 0xffe08a,
  MIN_MS: 350,
  DANGER_MIN_MS: 500,
} as const;
export type TelegraphTier = 'warn' | 'danger' | 'ranged';

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
