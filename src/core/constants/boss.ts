/**
 * 54라운드 1층 보스 '만취' 연출 상수 (Constants.ts 가 커져서 분리 — `core/constants/index.ts` 에서 다시 내보낸다).
 * 게임 수치(시간·피해·거리)는 data/bosses.json, 여기는 그림이 없을 때의 임시 그림·연출 값.
 */
export const BOSS_FX = {
  /**
   * 54라운드 아트 보스방 시트 (계약 §15, 아트 커밋 090459f): 구조물 `structures/v3/<이름>` · 이펙트 `fx/v3/<이름>` — 없으면 임시 그림.
   * 횃불 착지 불은 기존 fire_pool
   */
  SHEETS: {
    CASK: 'boss1_rolling_barrel',
    CASK_BREAK: 'boss1_barrel_break',
    TORCH: 'boss1_torch',
    CUP_SHATTER: 'boss1_cup_shatter',
    SPLASH: 'boss1_liquor_splash',
    GLOB: 'boss1_liquor_glob',
    /** 54라운드 Q18 보스 불타기 오버레이 (phaseFrames ignite·loop·out, light·lightByPhase) */
    ONFIRE: 'boss1_onfire',
    /** 54라운드 Q23·Q28 누운 자세 불길 (boss1_onfire JSON lyingSheet 의 기본값 — useFor·standFor·frameOffsets) */
    ONFIRE_DOWN: 'boss1_onfire_down',
  },
  /**
   * 54라운드 Q18 보스 불타기: 오버레이 시트가 없을 때 임시 — 기존 불 이펙트(fire_pool)를 발 위 LIFT_PX 에 배율 SCALE 로 얹고,
   * 국면 길이(ms)는 아래 값. 시트 light 가 없을 때 불빛 (월드 px, offsetY = 발에서 위로)
   */
  ONFIRE: {
    FALLBACK_FX: 'fire_pool',
    FALLBACK_LIFT_PX: 10,
    FALLBACK_SCALE: 1,
    FALLBACK_IGNITE_MS: 260,
    FALLBACK_OUT_MS: 420,
    LIGHT: { color: '#e8b858', radius: 57, intensity: 0.85, flicker: 0.22, offsetY: 17 },
  },
  /** 술통 깨짐 시트 마지막 프레임 유지·사라짐 ms */
  BREAK_HOLD_MS: 600,
  BREAK_FADE_MS: 400,
  /** 술 뿌리기 방울 (liquor_glob): 개수 · 비행 ms */
  GLOBS: { COUNT: 4, FLIGHT_MS: 260 },
  /** 쓰러짐 임시 연출: 회전·색 */
  LIE_ROTATION: Math.PI / 2,
  /**
   * 약점 잔: 임시 잔 색 · 테두리 강조(깜빡임) · 맞힘 판정 여유 (둘레 HIT_PAD_PX, 아래로는 보스 바디 윗변 + 바디 높이 × HIT_DOWN_RATIO
   * 까지 — 임시값. 54라운드 2차: 192×240 그림(바디 36)에 맞춰 고정 14px(바디 29 의 약 절반) → 바디 높이 비례 0.5).
   * 좌우는 잔 폭(+여유)과 보스 바디 폭 중 넓은 쪽 (54라운드 Q24 — 몸에 맞닿은 옆에서도 닿게)
   */
  CUP: {
    HIT_PAD_PX: 4,
    HIT_DOWN_RATIO: 0.5,
    FILL: 0xe0a830,
    LIQUOR: 0x8a3a10,
    EDGE: 0xfff2c0,
    EDGE_WIDTH: 1,
    BLINK_MS: 140,
    DEPTH_ABOVE: 0.002,
  },
  /** 잔 깨짐 파편 (임시): 개수·속도·수명 */
  SHARDS: { COUNT: 8, SPEED_PX: 60, LIFE_MS: 450, COLOR: 0xf0d080, SIZE: 2 },
  /** 기둥 임시 그림 (지역 소품 시트에 pillar 가 없을 때): 몸·윗면·높이(월드 px) */
  PILLAR: { BODY: 0x5b4a44, TOP: 0x7c6a5e, EDGE: 0x2a2220, HEIGHT_PX: 40 },
  /** 촛대 임시 그림: 받침·불꽃·쓰러진 색, 크기(월드 px) · 다시 켜기 안내 깜빡임 */
  CANDLE: {
    STAND: 0x8a6a3a,
    FLAME: 0xffc060,
    FALLEN: 0x5a4a30,
    W: 6,
    H: 22,
    FLAME_R: 3,
    HINT_COLOR: 0xffd890,
    HINT_MS: 600,
    HINT_RADIUS: 9,
    /**
     * 61라운드 점검 #6: 쓰러진(다시 켤 수 있는) 촛대 반짝임 — 어둠 위 네 갈래 별. 크기(월드 px)·발에서 위로·한 번 반짝이는 주기 ms·
     * 촛대마다 어긋나는 위상 ms·최소 배율
     */
    GLINT: { COLOR: 0xfff0c0, SIZE: 6, LIFT_PX: 12, PERIOD_MS: 1100, STAGGER_MS: 270, MIN_SCALE: 0.45 },
  },
  /** 61라운드 처치 연출: 시체(죽음 그림)를 보상 메뉴까지 남겨 두는 여유 ms (show.defeat.rewardAtMs 에 더한다) */
  CORPSE_EXTRA_HOLD_MS: 1500,
  /** 61라운드 계약 §17: 파훼·결정타 짧은 이름 (UI_EVENTS.BOSS_BREAK label) */
  BREAK_LABELS: { cup: '잔 깨기', pillar: '기둥 충돌', cask: '술통 되치기', stumble: '넘어뜨림', finisher: '결정타' },
  /** 61라운드 처치 연출 섬광 색 */
  DEFEAT_FLASH: 0xfff4e0,
  /** 굴러가는 술통 임시 그림 · 회전(라디안/px) */
  CASK: { BODY: 0x7a4a1a, BAND: 0x3a2410, SPIN_PER_PX: 0.12, DEPTH_LIFT: 0 },
  /** 횃불 투사체: 색 · 포물선 높이(월드 px) · 크기 */
  TORCH: { COLOR: 0xffa040, CORE: 0xfff0b0, ARC_PX: 26, R: 3 },
  /** 번지기 직전 불씨 (도화선): 색·반경·광원 */
  EMBER: { COLOR: 0xffe080, R: 2.5, LIGHT: { color: '#ffb040', radius: 26, intensity: 0.8, flicker: 0.4 } },
  /** 불붙은 웅덩이 칸 광원 (fire_pool 시트 광원이 없을 때) */
  FIRE_LIGHT: { color: '#ff7a1a', radius: 40, intensity: 0.75, flicker: 0.3 },
  /** 보스가 쓰러지면 주변광 복구 ms */
  DEATH_RESTORE_MS: 900,
  /** 세상이 돈다: 타일맵 컬링 여유(타일) · 가장자리 흐림(TiltShift)·비네팅 세기 */
  TILT: {
    /** 흐림을 떼는 실제 fps · 이어진 프레임 수 */
    MIN_FPS: 40,
    LOW_FRAMES: 20,
    CULL_PADDING_TILES: 4,
    VIGNETTE_RADIUS: 0.62,
    VIGNETTE_STRENGTH: 0.35,
    BLUR_RADIUS: 0.55,
    BLUR_AMOUNT: 0.6,
    BLUR_STRENGTH: 0.55,
  },
} as const;
