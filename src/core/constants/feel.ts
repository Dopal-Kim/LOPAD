/** 타격감·피드백·임시 전투 연출 (57라운드 B6: core/Constants.ts 에서 분리) */

export const PROTOTYPE = {
  HURT_FLASH_MS: 80,
  /** 보스 처치 후 결과 화면까지 지연 */
  CLEAR_DELAY_MS: 1200,
  SLASH_TRAIL_MS: 220,
  SHOCKWAVE_MS: 260,
  TWIN_DELAY_MS: 80,
  /** 가드 해제 밀쳐내기 연출 */
  GUARD_PUSH_MS: 200,
  /** 그림자 걸음 잔상 연출 */
  SHADOW_STEP_MS: 180,
  /** 조준 사격 차지 선 연출 폭 */
  AIM_LINE_WIDTH: 1,
  /** 개성 강화 알림 */
  REINFORCE_BANNER_MS: 1200,
  FATE_BANNER_MS: 1500,
  BANNER_MS: 1500,
  /** 바닥 드랍 최대 동시 수 */
  PICKUP_POOL: 64,
  /** 투사체 최대 동시 수 */
  PROJECTILE_POOL: 64,
  /** 이펙트 스프라이트 풀 크기 */
  FX_POOL: 48,
  /** 루프 이펙트(잔월 꼬리) 종료 페이드 */
  FX_FADE_MS: 150,
  /** 중압 이펙트: 히트박스 중심에서 아래로 (계약 §3.1 pivotNote) */
  WEIGHT_FX_DROP_PX: 6,
};

/**
 * 피격 피드백 (35라운드 1단계 임시값, 결정 로그 round-35 "시스템 반영 기록").
 * 강도 배율은 런타임 `feelSettings`(systems/feel.ts) 로 조절 — 디버그 `__lopad.setFeel({ shake: 0 })` (접근성 대비).
 */
export const FEEL = {
  /**
   * 61 단계 4 근접 피격 몸통: 판정은 바디(발밑)에서 그림 몸통 중심(`EntityVisual.hitLiftPx`, 일반 적 약 9px)까지.
   * 몸통 높이 상한이자 물리 겹침 영역을 아래로 늘리는 값 (월드 px)
   */
  MELEE_HURT_ZONE_PAD_PX: 24,
  /** 히트스톱: 물리·개체 애니·적 AI 정지 ms (UI·데미지 숫자·흔들림은 계속) */
  HITSTOP: {
    HIT_MS: 40,
    CRIT_MS: 70,
    BOSS_MS: 60,
    PLAYER_HURT_MS: 90,
    /** 연속 적중 중첩 금지: 마지막 시작 뒤 이 시간 안의 요청은 무시 */
    MIN_GAP_MS: 80,
    /**
     * 55라운드 Q6: 무기 적중 히트스톱 = data/weapons.json `feel.hitstopMs`(단검 30·칼 45·대검 80·활 25) ×
     * 막타(연격 마지막 타·대쉬 공격)·치명타 배율. 동시 다수 적중은 한 번만 (MIN_GAP_MS)
     */
    HEAVY_MULT: 1.8,
    /** 무기 데이터에 feel.hitstopMs 가 없을 때 */
    WEAPON_FALLBACK_MS: 40,
  },
  /** 화면 흔들림: 진폭 px(정수 반올림, 선형 감쇠) · 지속 ms. 스크롤 반올림 뒤에 더한다 */
  SHAKE: {
    HIT: { PX: 2, MS: 60 },
    CRIT: { PX: 4, MS: 100 },
    PLAYER_HURT: { PX: 5, MS: 140 },
    BOSS_WALL: { PX: 6, MS: 160 },
    SHOCKWAVE: { PX: 4, MS: 100 },
    /** 55라운드 Q8: 막타·대검·치명타 적중 흔들림 — 적중 시트 JSON `shakeHint` 가 없을 때 (임시) */
    HEAVY_HIT: { PX: 3, MS: 90 },
  },
  /** 61라운드 플레이 점검: 튜토리얼 허수아비 맞음 거리 = 무기 판정 반경 × 이만큼 (대검 쐐기 끝 ×1.3 여유) */
  TUTORIAL_REACH_MULT: 1.3,
  /** 55라운드 Q8 방향성 흔들림: 타격 방향으로 밀렸다가 반대로 튕기는 진동 횟수 (임시) */
  SHAKE_DIR: { CYCLES: 1.5 },
  /** 넉백: 공격 방향으로 거리 px, 선형 감쇠 ms (벽은 Arcade 충돌이 막는다) */
  KNOCKBACK: {
    HIT_PX: 6,
    CRIT_PX: 10,
    MS: 100,
    /** 보스는 1/4 거리, AI 를 멈추지 않고 속도에 더한다 */
    BOSS_MULT: 0.25,
    PLAYER_PX: 8,
    PLAYER_MS: 100,
  },
  /** 데미지 숫자 */
  DAMAGE_TEXT: {
    POOL: 24,
    DURATION_MS: 600,
    RISE_PX: 14,
    FADE_MS: 200,
    /** 적중점 위 시작 오프셋 · 겹침 방지 가로 흔들림 */
    OFFSET_Y: -10,
    JITTER_X: 4,
    CRIT_SCALE: 2,
    TICK_SCALE: 0.8,
    FONT_PX: 11,
    FONT_FAMILY: 'Galmuri11',
    FONT_FALLBACK: 'monospace',
    /** 글꼴 로드 대기 상한 (넘으면 폴백) */
    FONT_TIMEOUT_MS: 3000,
    /** 치명타 색: 층 램프 index (accent roles: 7 = light1 → 전체 슬롯 23) */
    CRIT_RAMP_INDEX: 7,
    /**
     * 61라운드 플레이 점검: 겹침 정리 (임시값). 같은 자리(반경 RADIUS_PX)에 MERGE_MS 안에 또 맞으면 숫자를 합쳐 다시 띄우고(일반·치명은 함께,
     * 틱·주인공 피격은 따로), 합칠 수 없으면 근처 숫자 수만큼 위로 STEP_PX·좌우로 SPREAD_X 씩 비켜 띄운다
     */
    STACK: { RADIUS_PX: 14, MERGE_MS: 260, STEP_PX: 9, SPREAD_X: 7, MAX_STEPS: 4, POP_SCALE: 1.25, POP_MS: 90 },
  },
  /** 플레이스홀더 피격 이펙트 (시트가 없을 때) */
  PLACEHOLDER: {
    SPARK_RADIUS: 3,
    SPARK_MS: 120,
    SPARK_SCALE_TO: 2.2,
    BLOOD_DOTS: 4,
    BLOOD_MS: 180,
    BLOOD_DIST_PX: 14,
    BLOOD_SPREAD_RAD: 0.7,
    /** 피 점 색: 현재 층 램프 index (5 = base, 1층 호박색) */
    BLOOD_RAMP_INDEX: 5,
    CRIT_RING_FROM: 6,
    CRIT_RING_TO: 18,
    CRIT_RING_MS: 160,
    DUST_DOTS: 3,
    DUST_MS: 200,
    DUST_DIST_PX: 8,
  },
  /** 피격 이펙트 시트 이름 (계약 §3, anchor hitbox_center). 없으면 플레이스홀더. 43라운드: `hit_burst` 가 있으면 `hit_spark` 대신 */
  FX_IDS: {
    SPARK: 'hit_spark',
    SPARK_ALT: 'hit_burst',
    BLOOD: 'blood',
    CRIT: 'crit_burst',
    DUST: 'knock_dust',
    PLAYER_HIT: 'player_hit',
    /** 55라운드 Q8·Q10 (계약 §16): 무기별 적중 스파크 `hit_<무기>` · 막타 `hit_<무기>_heavy` (없으면 hit_burst) */
    WEAPON_HIT_PREFIX: 'hit_',
    WEAPON_HIT_HEAVY_SUFFIX: '_heavy',
    /** 재 파편 입자 묶음 (kinds·recipes) */
    PARTICLES: 'particles_ash',
  },
  /**
   * 43라운드 B: 연타 시트(twin·dance) `hitFrames` 가 있으면 추가 타격 판정 간격을 그 프레임 시작 시각에 맞춘다
   * (쌍격 2타 40ms, 난무 0/40/90ms). false 면 기존 PROTOTYPE.TWIN_DELAY_MS 간격 + 그림만 겹침. 임시값
   */
  SYNC_HIT_FRAMES: true,
  /** 피 시트 마지막 프레임(바닥 얼룩) 유지 시간 (아트 권장 300~800ms) 후 페이드 */
  BLOOD_STAIN_MS: 500,
  /**
   * 55라운드 Q7·Q14 ④ 칼끝 잔상 리본 (계약 §16 `fx/v3/ribbon_ash`·`ribbon_ash_thin`): 칼끝(무기 v3 bladeTipAnchors) 궤적을
   * 텍스처 띠로 잇는다. 가는 호박 선 → LIFE_MS 안에 재색으로 식으며 소멸, 반투명 없음, 도트 궤적(연격 시트) 아래 깊이.
   * 시간은 플레이 시계(히트스톱 동안 멈춤). `feelSettings.trail` 로 끔
   */
  RIBBON: {
    /** 리본 수명 (Q7: 100ms 안에 식으며 소멸) */
    LIFE_MS: 100,
    /** 기본 텍스처 (3도트) · 가는 텍스처 (2도트). 무기별은 data/weapons.json feel.ribbon */
    SHEET: 'ribbon_ash',
    THIN_SHEET: 'ribbon_ash_thin',
    /** 칼끝 위치를 찍는 간격 (플레이 시계 ms — 프레임 사이도 보간해서 찍는다) */
    SAMPLE_MS: 4,
    /** 리본에 남기는 최대 점 수 */
    MAX_POINTS: 40,
    /** 판정 첫 프레임 몇 프레임 전부터 · 판정 끝 몇 프레임 뒤까지 칼끝을 찍는다 (임시) */
    LEAD_FRAMES: 1,
    TAIL_FRAMES: 1,
    /** 칼끝 메모가 없는 무기(칼 v3 등): 판정 호 반경 × 이 비율 위를 훑는다 (아트 trailFill.bladeTipRadiusDots 가 있으면 그것) */
    FALLBACK_RADIUS_RATIO: 0.65,
    /** 55라운드 내려찍기 쐐기(칼끝 메모 없음): 쐐기 길이 × 이 비율에서 끝점까지 앞으로 떨어진다 (임시) */
    WEDGE_START_RATIO: 0.3,
    /** 텍스처가 없을 때(캔버스 렌더러 등) 선 색: 머리 호박 A25 · 꼬리 재 S2 */
    FALLBACK_HEAD: 0xeecc78,
    FALLBACK_TAIL: 0x756c62,
  },
  /**
   * 55라운드 Q8 재 파편 입자 (계약 §16 `fx/v3/particles_ash` kinds·recipes). 속도·중력·흔들림 길이는 시트 도트 단위 → pixelScale 환산.
   * 위치는 도트 격자에 맞춘다. 동시 다수 적중이면 적마다 MULTI_HIT_FACTOR 배 (아트 제안 절반)
   */
  PARTICLES: {
    POOL: 160,
    MULTI_HIT_FACTOR: 0.5,
    /** 한 프레임 dt 상한 ms (탭 전환 뒤 튐 방지) */
    MAX_STEP_MS: 50,
  },
  /**
   * 화면 섬광·색 오버레이 (42라운드 Q3 임시값). 카메라 위 풀스크린 사각형(scrollFactor 0). 채도 감소는 WebGL 이면 camera.postFX
   * ColorMatrix, 캔버스면 회색 사각형 SATURATION 블렌드. `feelSettings.flash` 로 끔
   */
  SCREEN: {
    /** JSON flash 에 값이 빠졌을 때 기본 (코어 X1 #fff4dc, fx-design §6.2 거합 값) */
    DEFAULT_FLASH: { COLOR: 0xfff4dc, MS: 40, ALPHA: 0.18 },
    /** 치명타 섬광: 설계표(§6.2) 밖 추가 연출 → 기본 꺼짐(ALPHA 0). 켜려면 인터뷰 */
    CRIT: { COLOR: 0xffffff, MS: 40, ALPHA: 0 },
    /** 진화 선택: 층 강조색(램프 index). 설계표 밖 추가 연출 (드묾) */
    EVOLVE: { MS: 200, ALPHA: 0.35, RAMP_INDEX: 7 },
    /** 보스 페이즈 전환: fx-design §6.2 X0 0.35→0 120ms (+ 채도 감소는 설계표 밖 추가) */
    BOSS_PHASE: { COLOR: 0xffffff, MS: 120, ALPHA: 0.35, DESAT_MS: 400, DESAT: 1 },
    /** 히트스톱 중 채도 감소 (0~1): 설계표 밖 추가 연출 → 기본 0(꺼짐) */
    HITSTOP_DESAT: 0,
    /** 사망: 서서히 어둡게 (지속 = 사망 애니 + 추가 대기) */
    DEATH: { COLOR: 0x000000, ALPHA: 0.75, MIN_MS: 600 },
    /** 캔버스 폴백 채도 감소 색 (SATURATION 블렌드) */
    DESAT_FALLBACK_COLOR: 0x808080,
  },
  /** 보조 동작·대쉬 연출 (35라운드 3단계 임시값) */
  SECONDARY: {
    /** 패링 성공 히트스톱 (parry_flash 1프레임이 멈춤 동안 보이도록) */
    PARRY_HITSTOP_MS: 60,
    /** 조준 점선 길이 (칸) */
    AIM_LINE_TILES: 8,
    /** 조준 차지 완료(5프레임) 후 발사되어도 이만큼 유지 */
    AIM_CHARGE_HOLD_MS: 60,
    /** 차지 프레임 = min(마지막, floor(progress × AIM_CHARGE_DIVISOR)) — 아트 B 표 `min(5, floor(progress*5))` (6프레임) */
    AIM_CHARGE_DIVISOR: 5,
    /** 대쉬 잔상 간격 (아트 권장 40~50) */
    DASH_TRAIL_INTERVAL_MS: 45,
    /** 플레이어 몸 중심 = 발 피벗에서 위로 (aim_charge pivotNote). 53라운드 Q1: 주인공 화면 1.5배(48×72) → 11 × 1.5 (임시) */
    BODY_CENTER_UP_PX: 17,
    /** dash_trail 틴트 = 팔레트 fx.weapons[무기].ramp index (1 = W1 body dark). fx 블록이 없으면 틴트 없음 */
    DASH_TRAIL_RAMP_INDEX: 1,
    /** dash_trail 을 틴트하는 개성 노드 (JSON tint.when: 발도술·허보·잔상). 경로에 하나라도 있으면 */
    DASH_TRAIL_TINT_NODES: ['batto', 'longinvuln', 'afterimage'] as readonly string[],
    /** 55라운드 Q13: v3 대쉬 잔상은 따뜻한 재 그대로 — 노드 틴트(평면 채움)를 끈다 */
    DASH_TRAIL_TINT: false,
  },
};

/**
 * 56라운드 무기 피드백 (결정 2026-10-04-round-56) 연출 상수. 수치·게임 규칙은 data/weapons.json·player.json (임시값 표는 보고서)
 */
export const FEEDBACK = {
  /** Q36: 적 피격 번쩍임 — 호박 반투명, 80ms, 히트스톱으로 늘어나지 않음(트윈 시계) */
  MOB_HURT: { ALPHA: 0.55, MS: 80 },
  /**
   * Q12·Q50: 적중 순간 무기 그림이 크게 번쩍 — 판정 1프레임(WHITE_MS)만 백열 X1 #fff4dc, 그다음 호박 A25 #eecc78 로 식으며 사라짐
   * (더하기 혼합 사본, 트윈 시계 — 히트스톱 동안에도 진행)
   */
  BLADE_FLASH: { COLOR: 0xfff4dc, AMBER: 0xeecc78, WHITE_MS: 34, ALPHA: 0.85, SCALE: 1.12, MS: 110 },
  /** Q7·Q8: 월드 문구 (PERFECT GUARD · PARRY) — 몸 위에서 떠올라 사라짐 */
  CALLOUT: {
    FONT_PX: 11,
    COLOR: '#f4de9b',
    STROKE: '#2a1e17',
    STROKE_PX: 3,
    OFFSET_Y: -22,
    RISE_PX: 10,
    HOLD_MS: 420,
    FADE_MS: 260,
    POOL: 4,
  },
  /** 칼 검기 3단 칼날 빛 (아트 오버레이가 오기 전 임시 곱 틴트: 재 → 호박 → 백열) */
  KENKI_TINT: [0xb8aca0, 0xeecc78, 0xfff4dc] as readonly number[],
  /** 그로기 몸 틴트 (아트 그로기 자세가 오기 전 임시) */
  GROGGY_TINT: 0x8a8070,
  /**
   * 단검 낙인: 표식 fx (행 = 스택, 적 시트 윗변 + 여백 4 월드 px, 찍힘 뒤 2~5 반복) · 폭발 fx (행 s·m·l) ·
   * 시트가 없을 때 작은 마름모(Graphics)
   */
  BRAND: {
    MARK_SHEET: 'dagger_brand_mark',
    BURST_SHEET: 'dagger_brand_burst',
    MARK_LOOP_FROM: 2,
    HEAD_GAP_PX: 4,
    COLOR: 0xe2a33c,
    EDGE: 0x2a1e17,
    SIZE_PX: 2,
    GAP_PX: 5,
    OFFSET_Y: 6,
  },
  /** 단검 가속 가득 폭발 (61라운드: 2단 열풍만 — 기본 과열 폭발·식힘 삭제): 전용 폭발 fx (주인공 발) · 낙인 적 연쇄 간격 */
  OVERHEAT: { SHEET: 'dagger_overheat_burst', CHAIN_MS: 40 },
  /** 퍼펙트 가드·패링 fx (행 guard·parry, 맞닿은 점 = 판정 원점에서 공격자 쪽 6 월드 px, 공격자 방향 회전) */
  GUARD_FX: { SHEET: 'guard_perfect_fx', CONTACT_PX: 6 },
  /** 그로기: 몸 루프 · 머리 위 소용돌이 (머리 꼭대기 = 몸 JSON headTopAnchors, 없으면 OFFSET) */
  GROGGY: { SWIRL_SHEET: 'player_groggy_swirl', SWIRL_FALLBACK_Y: -29 },
  /** 대검 울분 가득 몸 틴트 깜빡임 (임시) */
  GRUDGE_FULL_TINT: 0xe2a33c,
  /** 활 숨 집중(감속 정밀 조준) 시작 화면 섬광 (임시) — 물리 배속은 data bow.gauge.focusTimeScale */
  FOCUS_FLASH: { COLOR: 0xeecc78, MS: 320, ALPHA: 0.14 },
  /** 일섬 선 깊이: 바닥 바로 위 (주인공·적 아래) — 아트 depth below_player */
  ISSEN_LINE_DEPTH: 0.96,
  /** 그림자 걸음 리본 (Q38 돌진류만): 출발 → 도착을 이 시간에 긋는다 */
  SHADOWSTEP_RIBBON_MS: 90,
} as const;
