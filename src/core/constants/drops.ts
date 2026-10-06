/**
 * 61 단계 5 (P13 §4) 바닥 줍기 물건 그림 (연출 값 — 자석 거리·전표 무더기 크기 경계는 data/economy.json `pickup`).
 * 아트 `items/v3/<id>`(idle 반짝임 루프 · spawn 튀어나옴 · pickup 흡수 팝, 전표는 무더기 행 small·mid·large, 메타 `shadow` = 그림자 포함)
 * 이 있으면 그것, 없으면 임시 도형(원형 동전 무더기·병 모양)을 씬에서 한 번 만들어 쓴다.
 */
export const DROP_ART = {
  /** 아트 시트 id (`items/v3/<id>`) — 전표·물약·1층 소모품 3종 */
  SHEETS: ['voucher', 'potion', 'fire_bottle', 'strong_swig', 'cold_water'] as readonly string[],
  /** 임시 도형 텍스처 해상도 (월드 1px = 이 배 — 2배 캔버스에서 선명하게) */
  FALLBACK_RES: 2,
  /** 임시 원형 동전 무더기: 동전 수(무더기 크기별) · 동전 지름(월드 px) · 색 */
  COIN: {
    COUNT: { small: 1, mid: 3, large: 5 } as Record<'small' | 'mid' | 'large', number>,
    D: 5,
    FACE: 0xf0c830,
    RIM: 0x8a6418,
    SHINE: 0xfff2b0,
    /** 전표 띠 (종이 전표 느낌 — 동전 위 작은 붉은 띠) */
    TAG: 0xb04030,
  },
  /** 임시 병: 몸통 지름 · 목 · 마개 (월드 px) · 종류별 몸통 색 */
  BOTTLE: {
    BODY_D: 5,
    NECK_W: 2,
    NECK_H: 3,
    CORK: 0x8a5a30,
    GLASS_EDGE: 0x203028,
    SHINE: 0xe8fff0,
    COLOR: { potion: 0x60e080, fire_bottle: 0xe07a2a, strong_swig: 0xc8a040, cold_water: 0x70b8e8 } as Record<
      string,
      number
    >,
  },
  /** 바닥 그림자 (그림에 그림자가 없을 때): 폭·높이 비(그림 폭 대비) · 알파 */
  SHADOW: { W_MULT: 1.1, H_RATIO: 0.38, ALPHA: 0.35, MIN_W: 5 },
  /** 튀어나옴 (spawn 그림이 없을 때): 높이(월드 px) · 올라감·떨어짐 ms · 착지 튕김 높이 */
  HOP: { HEIGHT: 9, UP_MS: 140, DOWN_MS: 220, BOUNCE: 2.5, BOUNCE_MS: 120 },
  /** 임시 반짝임 루프: 주기 ms · 반짝 길이 · 반짝일 때 밝기(틴트) · 둥실 높이 */
  SHIMMER: { PERIOD_MS: 1400, FLASH_MS: 160, TINT: 0xffffe0, BOB_PX: 1, BOB_MS: 700 },
  /** 자석 흡수: 늘어남 최대 비율(속도 비례) · 흡수 속도 가속(속도 / ms) */
  MAGNET: { STRETCH: 0.45, ACCEL_TILES_PER_S2: 40, START_TILES_PER_S: 2 },
  /** 흡수 팝 (pickup 그림이 없을 때): 커짐 배율 · ms · 반짝 고리 반지름(월드 px) */
  POP: { SCALE: 1.7, MS: 150, RING_R: 6, RING_COLOR: 0xfff2b0 },
  /** 떨군 자리에서 흩뿌려지는 거리 (월드 px — 아트 spawn 그림의 수평 이동을 시스템이 준다) */
  SCATTER_MIN_PX: 4,
  SCATTER_MAX_PX: 12,
  /** 사라지기 전 깜빡임 (수명 끝 ms 전부터) */
  EXPIRE_BLINK_MS: 2000,
} as const;
