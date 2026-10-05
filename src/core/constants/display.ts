/** 화면·렌더 배율·카메라·깊이 (57라운드 B6: core/Constants.ts 에서 분리) */

/** 월드 타일 크기(월드 단위). 50라운드: 판정·이동·데이터 수치는 이 단위 그대로 (RENDER 참고) */
export const TILE = 16;

/**
 * 50라운드 렌더 배율 (결정 round-50 Q2 '캐릭터 32×48·타일 32×32·카메라 확대 1배(화면상 크기 유사)', 계약 art §9).
 * 설계: 월드 좌표·판정·속도는 그대로 두고 **렌더 배율만** 바꾼다. 월드 1단위 = 논리 화면 WORLD_TO_SCREEN px (= 게임 카메라 논리
 * 배율 CAMERA.ZOOM). 근거는 parts/system/CHANGELOG.md 50라운드 절.
 *
 * 52라운드 Q8 (계약 art §11): 내부 렌더 1920×1080. 논리 화면(UI 배치·좌표 기준)은 960×540 그대로이고 캔버스만 RESOLUTION 배 —
 * 모든 카메라가 RESOLUTION 배를 더 곱한다(`systems/display.ts`). 도트 1개 = 실제 px: 기존(pixelScale 없음) 4 · v2(1) 2 · v3(0.5) 1.
 * 화면상 크기는 셋 다 같다 (`artScale = pixelScale / WORLD_TO_SCREEN` 은 그대로, 카메라 실제 배율이 2 → 4)
 */
export const RENDER = {
  WORLD_TO_SCREEN: 2,
  /** JSON pixelScale 이 없는 기존 도트의 배율 */
  LEGACY_PIXEL_SCALE: 2,
  /** 52라운드: 논리 px 1개 = 실제 캔버스 px (960×540 → 1920×1080) */
  RESOLUTION: 2,
} as const;

/**
 * 논리 해상도 (32라운드 Q1: 960×540 — UI 배치·좌표 기준). 52라운드: 실제 캔버스는 × RENDER.RESOLUTION (1920×1080).
 * 창 표시 배율은 main.ts (1280×720 창 = 960×540 표시, 1920×1080 창 = 1920×1080 — 52라운드 전과 같은 표시 크기)
 */
export const GAME = {
  WIDTH: 960,
  HEIGHT: 540,
  BACKGROUND_COLOR: '#0b0b10',
  MIN_ZOOM: 1,
};

export const DEPTH = {
  TILES: 0,
  /** 소품 오버레이 (바닥 위, 개체 아래) */
  PROPS: 0.5,
  /** 발밑 그림자 (개체 아래) */
  SHADOW: 0.9,
  /** 바닥 이펙트 (그림자 위, 개체 아래): 파쇄 링·발도 속도선·질풍 바람 */
  FX_GROUND: 0.95,
  /** 개체(플레이어·적)는 ENTITY + y × ENTITY_Y_SCALE 로 발 위치 기준 정렬 */
  ENTITY: 1,
  ENTITY_Y_SCALE: 1e-5,
  /** 개체에 겹치는 레이어 간격 (무기 오버레이 ±1, 베기 이펙트 +2). 발 y 반 픽셀 차이보다 작다 */
  OVERLAY_STEP: 2.5e-6,
  PICKUP: 2.5,
  PROJECTILE: 3,
  ATTACK: 4,
  /** 잔상 궤적 리본 (42라운드): 공격 판정 위·피격 이펙트 아래 */
  TRAIL: 4.2,
  /** 피격 이펙트 (타격 섬광·피·치명 버스트): 개체·공격 판정 위 */
  HIT_FX: 4.5,
  /**
   * 50라운드 동적 조명: 라이트맵(곱하기)이 덮는 깊이. 이보다 아래(바닥·벽·개체·구조물·개체 위 이펙트)는 어둠에 잠기고,
   * 위(드랍·투사체·공격 판정·잔상·피격 이펙트·데미지 숫자·화면 섬광)는 그대로 읽힌다. 빛 번짐·비네팅은 그 바로 위
   */
  LIGHTMAP: 2,
  LIGHT_LAYER_STEP: 0.01,
  /**
   * 53라운드 Q64: 이펙트(FxPool)는 라이트맵 위에 — 라이트맵 아래 깊이 d 를 FX_LIT_BASE + d × FX_LIT_SPAN 으로 옮긴다
   * (빛 번짐 +0.01 위, 드랍 2.5 아래: d < 2 이면 2.02 ~ 2.22)
   */
  FX_LIT_BASE: 2.02,
  FX_LIT_SPAN: 0.1,
  /** 데미지 숫자: 월드 요소 중 가장 위 */
  DAMAGE_TEXT: 5,
  /** 화면 섬광·색 오버레이 (42라운드): 월드 최상. UI 는 별도 씬이라 덮지 않는다 */
  SCREEN_FX: 50,
  DEBUG: 100,
};

/** 발 위치 y 로 깊이를 정한다 (아래쪽이 앞) */
export function entityDepth(y: number): number {
  return DEPTH.ENTITY + y * DEPTH.ENTITY_Y_SCALE;
}

/**
 * 53라운드 Q64: 이펙트 깊이 → 라이트맵 위 띠. 라이트맵 아래 깊이 d 는 FX_LIT_BASE + d × FX_LIT_SPAN 으로 옮겨
 * 이펙트끼리의 앞뒤(바닥 이펙트 < 개체에 붙은 이펙트)는 지키고 어둠에는 묻히지 않게 한다. 이미 위(투사체·판정·피격)면 그대로
 */
export function fxLitDepth(d: number): number {
  return d < DEPTH.LIGHTMAP ? DEPTH.FX_LIT_BASE + Math.max(0, d) * DEPTH.FX_LIT_SPAN : d;
}

/**
 * 카메라 (32라운드 Q2: 방 고정이 아니라 플레이어 부드러운 추종).
 * 목표 스크롤 = 플레이어 중심(데드존 적용) → 현재 영역(방 셀 사각형 + 서 있는 복도의 이웃 셀)으로 클램프 → lerp.
 * 클램프를 목표에만 적용하므로 영역이 바뀌어도 카메라가 튀지 않고 옆 방으로 미끄러진다.
 */
export const CAMERA = {
  /** 프레임당 보간 비율 (60fps 기준) */
  FOLLOW_LERP: 0.1,
  /** 플레이어가 화면 중심에서 이만큼(px) 벗어나야 카메라가 따라간다 */
  DEADZONE_X: 12,
  DEADZONE_Y: 8,
  /** 보간이 이 거리(px) 안이면 목표에 붙인다 (미세 진동 방지) */
  SNAP_PX: 0.25,
  /**
   * 48라운드 Q1: 게임 월드 카메라 확대 (논리 960×540 → 한 화면 약 30×17타일). UI 씬은 별도 카메라라 무관.
   * 데드존·흔들림 px 는 논리 화면 px 기준이라 월드 px 로는 ÷ZOOM 해서 쓴다 (흔들림 체감 유지, 임시).
   * 52라운드: 이 값은 **논리** 배율 — 실제 카메라 zoom = ZOOM × RENDER.RESOLUTION (`display.worldZoom`)
   */
  ZOOM: RENDER.WORLD_TO_SCREEN,
};
