/**
 * 61라운드 단계 3 E: 아트 2 보스 그림 연결 (등장·림라이트·파훼 표시·결정타·쓰러짐 연출) + 보스방 VRAM 지연 로드.
 * 그림 규격은 각 시트 JSON(계약 art §25 — 프로듀서 작성 중), 여기는 시트 이름과 시스템이 정하는 연출 값.
 */
export const BOSS_ART = {
  /** 이펙트 `fx/v3/<이름>` · 구조물 `structures/v3/<이름>` */
  SHEETS: {
    CUP_GLINT: 'boss1_cup_glint',
    BREAK_DAZE: 'boss1_break_daze',
    CANDLE_GLINT: 'boss1_candle_glint',
    CASK_RIM: 'boss1_rolling_barrel_rim',
    CASK_RETURNED: 'boss1_rolling_barrel_returned',
    FINISHER_SLASH: 'boss1_finisher_slash',
    FINISHER_BURST: 'boss1_finisher_burst',
    DEFEAT_SHATTER: 'boss1_defeat_shatter',
    FLAME_SNUFF: 'boss1_flame_snuff',
  },
  /** 보스 몸 등장 동작 `bosses/v3/<보스>_intro` (보스 묶음 — 전투 시작 때 내린다) */
  INTRO_ACTION: 'intro',
  /** 림라이트 오버레이 `bosses/v3/<보스>_<동작>_rim` 이 있는 동작 (3국면 소등 동안만 로드) */
  RIM_ACTIONS: ['idle', 'walk', 'attack', 'stagger_dash', 'hurt'] as readonly string[],
  RIM_SUFFIX: 'rim',
  /**
   * 림 시트 5장 VRAM 추정 MB (아트 보고 약 42MB — 아틀라스 크기 합 41.5). 소등 시작 때 지금 VRAM + 이 값이 VRAM.BUDGET 을 넘으면
   * 림 시트를 올리지 않고 tintFill 대체만 쓴다
   */
  RIM_EST_MB: 42,
  /**
   * 61 단계 4 가벼운 림 `<동작>_rim_lite` (아트: 반 해상도 144×180·pixelScale 1.0 — 표시 배율 = 보스 × 2, 아틀라스 합 10.6MB).
   * 원 림이 예산을 넘으면(대검 런 등) 이것, 이것도 넘으면 tintFill. _rim 과 둘 중 하나만 올린다
   */
  RIM_LITE_SUFFIX: 'rim_lite',
  RIM_LITE_EST_MB: 11,
  /** 결정타·쓰러짐·불 끄기 fx 4장 VRAM 추정 MB (아틀라스 크기 합 12.9) · 마지막 국면에 소등이 없을 때 그 진입 뒤 올리는 시각 ms */
  FINALE_EST_MB: 13,
  FINALE_DELAY_MS: 5000,
  /** 림 시트가 없는 동작·로드 전·예산 초과: 보스 그림 사본을 호박 채움색으로 조명 위에 더한다 (ADD) */
  RIM_FALLBACK: { COLOR: 0xe2a33c, ALPHA: 0.3 },
  /** 잔 맞음(안 깨짐) struck 행 재생 ms · 파훼 머리 위 고리를 머리 꼭대기에서 위로 (월드 px) */
  CUP_STRUCK_MS: 350,
  DAZE_LIFT_PX: 2,
  /** 기둥 균열 최대 단 (61 P13 §3: 3단 다음 충돌에서 무너짐 — 단 4 = 잔해) · 돌진 충돌을 그 기둥에 매기는 거리 (월드 px) */
  PILLAR_MAX_STAGE: 3,
  PILLAR_HIT_REACH_PX: 20,
  /**
   * 61 P13 §3 기둥 무너짐. 시트에 `collapse`·`rubble` 상태가 있으면 그것(무너짐 1회 → 잔해 유지), 없으면 임시: crack3 그림을
   * 보스 반대쪽으로 TILT_DEG 기울이며 MS 동안 사라지고(FADE_FROM 부터 투명) 낮은 돌무더기(RUBBLE)를 남긴다.
   * 칸은 무너짐이 끝날 때 연다(걷기·투사체 통과). 흔들림은 설정 배율
   */
  PILLAR_COLLAPSE: {
    TILT_DEG: 80,
    MS: 520,
    FADE_FROM: 0.55,
    SHAKE_PX: 6,
    SHAKE_MS: 260,
    RUBBLE: { STONES: 7, BODY: 0x5b4a44, TOP: 0x7c6a5e, EDGE: 0x2a2220, MIN_R: 2.5, MAX_R: 5.5, SQUASH: 0.55 },
  },
  /** 61 P13 §3 가려짐: 보스 바디 중심 → 주인공 바디 중심 선이 서 있는 기둥 발자국(이만큼 부풀림)을 지나면 가려짐 · 보이면 줄어드는 배율 */
  COVER: { PAD_PX: 1, DECAY: 2 },
  /** 61 P13 §3 보스 우회 조향: 기둥을 보스 바디 반폭 + BODY_PAD 만큼 부풀려 모서리(MARGIN 밖)로 돈다 · 모서리 고집 · 닿음 거리 */
  STEER: { BODY_PAD_PX: 2, MARGIN_PX: 3, STICK_PX: 12, REACH_PX: 6 },
  /** 결정타 일섬 중심 = 보스 피벗 위 이 도트 (시트 anchorNote 약 150) */
  FINISHER_LIFT_DOTS: 150,
  /** 방 불 끄기 (시작 시각은 data show.defeat.snuffAtMs): 간격 ms (아트 제안 60~90 — 차례로 번갈아) */
  SNUFF_GAP_MS: [60, 90, 75] as readonly number[],
  /** 결정타 연출 (아트 systemHints 제안 → 시스템 값): 섬광·흔들림·확대. 히트스톱·슬로모는 처치 연출(show.defeat)이 이미 더 길게 건다 */
  FINISHER: { FLASH: 0xfff4dc, FLASH_MS: 70, FLASH_ALPHA: 0.6, SHAKE_PX: 10, SHAKE_MS: 320, ZOOM: 1.08, ZOOM_MS: 260 },
} as const;
