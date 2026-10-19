/**
 * P21 어두운 톤 · 잔혹 전투 · 상흔 (계약 dark-brutal.md — 1차 값, 2차 측정 뒤 CHANGELOG P21 절에 조정 기록).
 * 색 보정 수치는 data/grade.json (아트 A 가 값을 낸다), 여기는 규칙·연출 값.
 */
export const BRUTAL = {
  /** §3 주인공 상처: HP 비율 경계 (이하 → 그 단계) · 박힌 화살 상한 · 앵커 순서 */
  HERO: {
    STAGES: [0.75, 0.5, 0.25] as readonly number[],
    MAX_ARROWS: 5,
    ARROW_ANCHORS: ['back', 'shoulderL', 'shoulderR', 'thigh', 'arm'] as readonly string[],
    /** 저HP 신호 (≤ 25%) */
    LOW_HP_RATIO: 0.25,
    /** 상흔 오버레이가 없을 때의 몸 틴트 (단계 1·2·3 — 숯빛 망령이 재처럼 바래 간다) */
    STAGE_TINT: [0xffffff, 0xe6ded8, 0xd4c6bc, 0xc2aa9c] as readonly number[],
    /** 박힌 화살 임시 그림 (stuck_arrow 시트가 없을 때 — 짧은 선, 월드 px) */
    ARROW_LEN_PX: 7,
    ARROW_COLOR: 0x2a2420,
    /** 앵커 → 몸 피벗(발) 기준 임시 오프셋 (월드 px, 오른쪽 보기 기준 · 왼쪽이면 x 반전) */
    ARROW_OFFSETS: {
      back: [-3, -26, -2.4],
      shoulderL: [-5, -30, -2.0],
      shoulderR: [5, -30, -1.0],
      thigh: [2, -12, -0.6],
      arm: [6, -22, -0.3],
    } as Record<string, readonly [number, number, number]>,
    /** 피격 타르·불씨·재 (tar_ember_hit 시트가 없을 때 — 점 개수·거리·시간) */
    TAR_DOTS: 7,
    EMBER_DOTS: 4,
    TAR_COLOR: 0x0d0b0a,
    EMBER_COLOR: 0xff8a3a,
    ASH_COLOR: 0x8a8580,
    SPLASH_PX: 14,
    SPLASH_MS: 420,
  },
  /** §3 적 상처 */
  ENEMY: {
    /** HP 비율 경계 (≤ 66% → 1, ≤ 33% → 2) */
    STAGES: [0.66, 0.33] as readonly number[],
    /** 단계별 스탬프 수 [최소, 최대] */
    STAMPS: [
      [0, 0],
      [2, 3],
      [4, 6],
    ] as readonly (readonly [number, number])[],
    /** 옷 피 젖음 곱 틴트 (1·2단계) */
    WET_TINT: [0xffffff, 0xd8b8b0, 0xb88880] as readonly number[],
    /** stage 2 피 방울: 걸을 때 이 간격(ms)마다 바닥 데칼 · 이동 배율 (절뚝) */
    DRIP_MS: 400,
    LIMP_MULT: 0.9,
    /** 스탬프 임시 그림 (wound_cut 시트가 없을 때 — 짧은 검붉은 선, 월드 px) */
    STAMP_LEN_PX: [3, 6] as readonly [number, number],
    STAMP_COLOR: 0x4a0a0a,
  },
  /** §4 처형 */
  EXEC: {
    HP_RATIO: 0.15,
    /** 버팀이 깨진 뒤 처형을 받는 시간 (움찔 FLINCH_MS 가 짧아 따로 — 1차) */
    BROKEN_WINDOW_MS: 700,
    RANGE_TILES: 1.2,
    /** 부채꼴 반각 (rad) */
    HALF_ANGLE: Math.PI / 3,
    INVULN_MS: 450,
    /** 동작 길이 (처형 시트·연격 시트를 이 길이에 맞춘다) · 적중 순간 (비율) */
    MS: 450,
    IMPACT_AT: 0.55,
    /** 결정타 뒤 이만큼 지나면 이동·대쉬로 회복을 끊는다 (봇 정지 % 24~40 → 1차 손잡이, 무적은 그대로) */
    RECOVER_CANCEL_MS: 80,
    SLOW: { SCALE: 0.3, MS: 120 },
    PUNCH: { AMOUNT: 0.08, MS: 260 },
    /** 각성 게이지 배율 (일반 처치의 2배) */
    GROWTH_MULT: 2,
    /** 처형 막타 피해 = 남은 HP + 최대 HP × 이 값 (넘친 피해 — 분출을 크게) */
    OVERKILL_RATIO: 0.4,
  },
  /** §5 사망 변형 */
  DEATH: {
    OVERKILL_RATIO: 0.3,
    PIN_WALL_TILES: 1.5,
  },
  /** §6 피·시체 지속 */
  DECAL: {
    MAX: 160,
    FADE_MS: 1000,
    /** 바닥 깊이 (그림자 0.9 위, 바닥 이펙트 0.95 아래) */
    DEPTH: 0.92,
    POOL_DEPTH: 0.915,
    POOL_MS: 1500,
    POOL_SCALE0: 0.3,
    WALL_TILES: 1,
    /** 임시 그림 (blood_decal_floor 시트가 없을 때 — 반지름 월드 px [최소, 최대]) */
    RADIUS_PX: [1.5, 4] as readonly [number, number],
    POOL_RADIUS_PX: 11,
    COLOR: 0x5a0808,
    DARK_COLOR: 0x2a0606,
    /** 적중 하나에 흘리는 바닥 데칼 수 (amount 1·2·3) */
    PER_HIT: [0, 2, 3, 5] as readonly number[],
    SPRAY_PX: 22,
  },
  CORPSE: {
    MAX: 24,
    FADE_MS: 3000,
    /** 잘린 조각: 날아가는 시간 [최소, 최대] · 거리 (월드 px) */
    PART_MS: [500, 900] as readonly [number, number],
    PART_PX: [14, 30] as readonly [number, number],
    PART_LIFT_PX: 10,
  },
  /** §1 고어 1: 피 양 배율 · 색 (곱 틴트) */
  GORE1: { AMOUNT: 1 / 3, TINT: 0x8a7070 },
  /** §1 고어 0: 피 대신 먹·재 입자 색 */
  GORE0: { INK: 0x101012, ASH: 0x7a7672 },
  /** §7 그레인 텍스처 한 변 (px) */
  GRAIN_TEX: 128,
} as const;
