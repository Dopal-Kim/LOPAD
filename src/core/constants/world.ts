/** 쿼터뷰 벽·외벽·비전투 이동·구조물 연출 (57라운드 B6: core/Constants.ts 에서 분리) */
import { DEPTH } from './display';

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
