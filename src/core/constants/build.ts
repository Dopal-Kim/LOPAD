/**
 * 57라운드 빌드 축 연출 플레이스홀더 (아트 시트가 오기 전 — 갈래 수단·세트·패시브·저주의 월드 표시).
 * 게임 수치는 data/build.json · passives.json · weapons.json(갈래) · dualTraits.json · curses.json · awakenings.json.
 */
export const BUILD_FX = {
  /** 판정 윤곽·선 (회전 베기·내려베기·균열·진동·기폭·반향) */
  STROKE_PX: 2,
  FADE_MS: 260,
  /** 오래 남는 영역 (불씨·달 궤적) 채움 알파 */
  ZONE_ALPHA: 0.28,
  COLOR: {
    SPIN: 0xd8d0b8,
    UNBLOCKABLE: 0xf2e6c8,
    CRACK: 0xc89a5a,
    RING: 0xb08860,
    THROW: 0xd0d8e0,
    CLONE: 0x6a6a8a,
    ECHO: 0xe0d0a0,
    MARK: 0xd04040,
    BLEED: 0x9a1e1e,
    BURN: 0xe07a2a,
    EMBER: 0xe08a3a,
    LIQUOR: 0x8a6a3a,
    DRUNK_TINT: 0xe8c890,
    MOON: 0xc8d8f0,
    METEOR: 0xf0e0b0,
    /** 61 G 광전 폭주 (몸 깜빡임·포효 고리) */
    RAGE: 0xd8483a,
  },
  LIQUOR_ALPHA: 0.45,
  /** 표식 점 (적 머리 위): 반지름 · 간격 · 머리 위 높이 */
  MARK_DOT_R: 1.5,
  MARK_DOT_GAP: 4,
  MARK_LIFT_PX: 4,
  /** 월드 문구 (56라운드 'PERFECT GUARD'·'PARRY' 와 같은 방식, 영문) */
  TEXT: {
    PERFECT_EVADE: 'PERFECT EVADE',
    STAGGER: 'STAGGER',
    LAST_STAND: 'HOLD ON',
    EXECUTE: 'EXECUTE',
    /** 61 G 광전 폭주 시작 */
    RAGE: 'RAGE',
  },
  /** 정적(간파 6) · 숨 집중과 겹치면 집중이 우선 */
  STILL_FLASH: { COLOR: 0xc8d0e0, MS: 120, ALPHA: 0.18 },
  /** 위기 (버팀 4 단검·활) 섬광 */
  CRISIS_FLASH: { COLOR: 0xe0c070, MS: 140, ALPHA: 0.2 },
  /** 홀드 준비 번쩍임 (칼 회전 베기·내려베기 홀드 완료) */
  HOLD_READY_COLOR: 0xfff0c0,
  /** 그림자 분신 플레이스홀더 알파 · ms */
  CLONE_ALPHA: 0.45,
  CLONE_MS: 220,
  /** 던진 단검·파편·분열 화살 플레이스홀더 판정 크기 px */
  SHOT_SIZE_PX: 5,
  /** 박힌 단검 표시 크기 px (비도) */
  STUCK_KNIFE_PX: 4,
} as const;

/**
 * 60라운드 계약 art §21 빌드 축 시트 id (fx/v3) · 배치 규칙. 무기·갈래 전용 시트는 무기 데이터(노드 `art.fx`)가 로드 목록을 정하고,
 * 상태·세트·저주·완벽 회피처럼 무기와 무관한 시트는 부팅 묶음(`BUILD_STATUS_FX_IDS`).
 */
export const BUILD_ART = {
  // --- 상태·세트 (공용) ---
  STAGGER: 'status_stagger',
  MARK: 'status_mark',
  BURN: 'status_burn',
  BOIL: 'status_boil',
  STASIS_WAVE: 'set_stasis_wave',
  SLOWED: 'status_slowed',
  DRUNK: 'status_drunk',
  DRUNK_SWAY: 'drunk_sway',
  LAST_STAND: 'endure_last_stand',
  BLOODLUST: 'chain_bloodlust',
  SET_FLASH: 'set_flash',
  DUAL_GET: 'dual_trait_get',
  PERFECT_DODGE: 'perfect_dodge',
  CURSE_MARK: 'curse_mark',
  POOL_LIQUOR: 'pool_liquor',
  POOL_LIQUOR_FIRE: 'pool_liquor_fire',
  // --- 60라운드 계약 art §22 2차 묶음 ---
  ELITE_EMBLEM: 'elite_emblem',
  ELITE_NAMEPLATE: 'elite_nameplate',
  // --- §22.1 엘리트 접두어 fx · 화염 술병 ---
  ELITE_BARREL: 'elite_barrel_armor',
  ELITE_BARREL_BREAK: 'elite_barrel_armor_break',
  ELITE_VAPOR: 'elite_drunk_vapor',
  ELITE_LINK: 'elite_ringleader_link',
  ELITE_AURA: 'elite_ringleader_aura',
  ELITE_GUZZLE_TRAIL: 'elite_guzzle_trail',
  ELITE_GUZZLE_DRINK: 'elite_guzzle_drink',
  BOTTLE_THROWN: 'fire_bottle_thrown',
  BOTTLE_BURST: 'fire_bottle_burst',
  // --- 최종 각성 시그니처 (무기당 1) ---
  FULLMOON: 'katana_fullmoon',
  LANDSLIDE: 'greatsword_landslide',
  HUNDRED_GHOSTS: 'dagger_hundred_ghosts',
  METEOR_ARROW: 'bow_meteor_arrow',
  // --- 칼 2단 ---
  WHIRL_LOOP: 'katana_whirl_loop',
  WHIRL_REFLECT: 'katana_whirl_reflect',
  MOON_TRAIL: 'katana_moon_trail',
  CLEAVE_CRACK: 'katana_cleave_crack',
  EXECUTE: 'katana_execute',
  MIRROR_KI: 'katana_mirror_ki',
  MIRROR_PARRY: 'katana_mirror_parry',
  // --- 대검 1단 연격 변화 · 2단 ---
  CLEAVE_COMBO_CRACK: 'greatsword_cleave_crack',
  QUAKE_FORK: 'greatsword_quake_fork',
  ECHO_COUNTER: 'greatsword_echo_counter',
  GIANT_RING: 'greatsword_giant_ring',
  CHARGE_FLASH_LV4: 'greatsword_charge_flash_lv4',
  BRACE_ABSORB: 'greatsword_brace_absorb',
  CONGEST_AURA: 'greatsword_congest_aura',
  CONGEST_BURST: 'greatsword_congest_burst',
  /** 지진 착지 균열 재사용 (계약 §21 재사용 매핑) */
  QUAKE_LANDING: 'greatsword_shatter_crack_t2',
  // --- 단검 ---
  GALE_WIND: 'dagger_gale_wind',
  FRENZY_IN: 'dagger_frenzy_clone_in',
  FRENZY_OUT: 'dagger_frenzy_clone_out',
  BRAND_BLEED: 'dagger_brand_bleed',
  BRAND_HOP: 'dagger_brand_hop',
  STUCK_BLADE: 'dagger_stuck_blade',
  HOTWIND_TRAIL: 'dagger_hotwind_trail',
  /** 비도 투척 = dagger_thrown ×5 · 비도 도착 = shadowstep_ghost (재사용 매핑) */
  THROWN: 'dagger_thrown',
  // --- 활 ---
  SNIPE_FULL: 'bow_snipe_full',
  ARROW_SPLIT: 'bow_arrow_split',
  /** 연궁 분열 화살 = bow_arrow_rapid (재사용 매핑) */
  SPLIT_ARROW: 'bow_arrow_rapid',
  ARROW_STUCK: 'bow_arrow_stuck',
  ARROW_RECALL: 'bow_arrow_recall',
  DEADEYE_SCOPE: 'bow_deadeye_scope',
  LINK_STACK: 'bow_link_stack',
  SKYPIERCE_LINE: 'bow_skypierce_line',
  /** 명경 분신 일섬 = katana_issen_shadow ×2 (+90ms, 선과 수직 ±24 도트 = 6 월드 px) */
  MIRROR_CLONE_DELAY_MS: 90,
  MIRROR_CLONE_OFFSET_PX: 6,
  /** 달 궤적 간격 (48 도트 = 12 월드 px) */
  MOON_TRAIL_GAP_PX: 12,
  /** 질풍 바람 실루엣 간격 */
  GALE_WIND_INTERVAL_MS: 90,
  /** 머리 꼭대기 앵커가 없는 동작: 주인공 피벗 위 124 도트(× 렌더 배율은 호출 쪽) = 31 월드 px · 저주 표시는 취기 위로 24 도트 */
  HEAD_TOP_PX: 31,
  CURSE_ABOVE_DRUNK_PX: 6,
  /** 표식이 낙인과 겹칠 때 위로 18 도트 · 경직 표시가 낙인과 겹칠 때 20 도트 */
  MARK_ABOVE_BRAND_PX: 4.5,
  /** 적 투사체 감속 표시 배율 (아트 권장 0.6) */
  SLOWED_SHOT_SCALE: 0.6,
  /** 낙인 옮겨감 이동 ms (아트 권장 0.2초) */
  BRAND_HOP_MS: 200,
} as const;
