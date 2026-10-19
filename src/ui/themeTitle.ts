/**
 * 62라운드 타이틀 화면 수치 (아트 계약 `art-assets.md` §29 — `assets/sprites/title/title.json` 이 기준).
 * 그림 좌표는 모두 **1920×1080 화면 px**(아트 단위)로 적고, 씬이 논리 960×540 로 바꾼다(÷2).
 * JSON 을 못 읽으면 이 기본값(= title62-1 JSON 의 값)으로 그린다. UI 판단 값(타이밍·상한·메뉴 줄 자리)은 아래 `TITLE_UI`.
 */

export type TitleWeapon = 'katana' | 'greatsword' | 'dagger' | 'bow';
export const TITLE_WEAPONS: readonly TitleWeapon[] = ['katana', 'greatsword', 'dagger', 'bow'];

/** 아트 파일 (assets/sprites/title/ → 게임 주소 assets-game/sprites/title/) */
export const TITLE_URL = 'assets-game/sprites/title/';
export const TITLE_IMAGES = [
  'title_bg_far',
  'title_bg_mid',
  'title_bg_near',
  'title_hero',
  'title_fx_glow_hero',
  'title_fx_voice_katana',
  'title_fx_voice_greatsword',
  'title_fx_voice_dagger',
  'title_fx_voice_bow',
  'title_fx_fog',
  'title_logo',
  'title_logo_reveal',
  'title_menu_frame',
] as const;
export type TitleImage = (typeof TITLE_IMAGES)[number];
export const TITLE_EMBERS = 'title_fx_embers';
/** P21 날씨 그림 (title.json rain·crows·ash 가 쓴다 — 없으면 404 로 건너뜀) */
export const TITLE_WEATHER = ['title_fx_rain', 'title_fx_crow', 'title_fx_ash'] as const;
export const TITLE_JSONS = ['title', 'title_fx_embers', 'title_fx_fog', 'title_menu_frame'] as const;
/** UI 가 읽는 텍스처·JSON 키 (시스템 키와 겹치지 않게 접두어) */
export const titleKey = (name: string): string => `ui-title-${name}`;
export const titleJsonKey = (name: string): string => `ui-title-json-${name}`;

/** 화면 크기 (아트 단위) */
export const ART_W = 1920;
export const ART_H = 1080;
/** 아트 단위 → 논리 px */
export const ART_TO_LOGIC = 0.5;

/** UI 판단 값 (62라운드 — 데모 검토 대상) */
export const TITLE_UI = {
  /**
   * 등장: 그림이 다 읽힌 뒤 기준 (ms). P21: 느리게 — 어둠이 오래 머물다 걷히고, 글이 늦게 떠오른다(5초 안에 메뉴까지,
   * 아무 키·클릭이면 바로). 옛 값: 검은 150 · 걷힘 1400 · 로고 850 · 메뉴 1900 · 끝 2600
   */
  intro: {
    blackMs: 600,
    revealMs: 2800,
    /** 모션 줄이기: 붓질 대신 걷히는 페이드 */
    fadeMs: 800,
    logoAt: 1600,
    logoMs: 1600,
    subAt: 2700,
    subMs: 1000,
    dotsAt: 3400,
    dotGapMs: 260,
    dotMs: 500,
    menuAt: 3600,
    menuMs: 900,
    endMs: 4800,
  },
  /** 붓질 덮개 해상도 (논리 960×540 의 절반) */
  veilW: 480,
  veilH: 270,
  /** 그림 마스크 앞쪽 번짐 (TransitionScene 과 같은 값) */
  maskSoft: 0.05,
  /** 마스크가 이만큼 안 오면 코드 붓질로 */
  maskWaitMs: 700,
  /** 불티 수 상한 (모든 방출기 합) */
  emberCap: 84,
  /** 한 프레임 방출 시간 상한 (탭 전환 뒤 몰아 뿜기 방지) */
  emberMaxDtMs: 100,
  /** 레이어 사이 깊이 (안개·도시 불티 패럴랙스) */
  parallax: { fogFar: 0.25, cityEmbers: 0.25, fogMid: 0.7, fogNear: 1.0 },
  /** 메뉴: 줄 간격·글자 들여쓰기·불씨 커서 자리 (아트 단위, 틀 왼쪽 위 기준) */
  menu: { rowH: 48, textX: 64, cursorX: 44, minPadY: 39, padExtra: 24, bandInset: 22, bandH: 40, chooseMs: 130 },
  /** 선택한 줄 글자가 오른쪽으로 비켜 서는 거리 (논리 px) */
  selectNudge: 3,
  /** 안내 한 줄이 머무는 시간 (수련장 거부 사유 등) */
  noticeMs: 2600,
  /** 깊이 */
  depth: { far: 0, fogFar: 1, city: 2, mid: 3, fogMid: 4, near: 5, fogNear: 10, logo: 11, menu: 12, veil: 50 },
  /**
   * 첫 생으로 들어가기 (점검 T8): 키아트 안 성문(아트 그림 속 불 켜진 문 — UI 가 미리보기에서 잰 자리, 아트 px)으로
   * 파고들며 가장자리부터 먹이 덮는다. 덮인 뒤 시스템 명령.
   */
  /** 파고들기 (중심 = spec.gate — art §30 title.json gate) */
  /** P21: 성문 빛은 금빛 대신 검붉은 잉걸 (밝은 섬광 없음) */
  dive: { ms: 1100, zoom: 3.4, pull: 1, lightHex: '#741d12', lightAlpha: 0.1 },
  /** '아무 키나 누른다' (점검 T3): 숨쉬듯 깜빡임 주기 */
  promptBlinkMs: 1800,
  /**
   * P21 어두운 연출 (UI 몫 — 그림 자체의 명도는 아트 A):
   *  - 안개·재 흐름 배율(느리게) · 불티 속도 배율
   *  - 불씨 깜빡임(무기 불씨·발광·메뉴 커서): 두 사인 겹친 느린 일렁임 + 가끔 꺼질 듯 잦아듦
   *  - 비·까마귀·젖은 재 (title.json rain·crows·ash — 아트 A P21)
   *  - 가장자리 먹 비네트: 안개 앞·로고 뒤
   */
  dark: {
    fogSpeedK: 0.45,
    emberSpeedK: 0.6,
    flicker: { amp: 0.28, msA: 1700, msB: 610, dipEveryMs: 5300, dipMs: 260, dip: 0.55 },
    /** 점등 순간 반짝임 (옛 0.6 — 밝은 섬광 줄임) */
    dotPop: 0.15,
    /** 까마귀는 로고가 다 써진 뒤부터 */
    crowStartMs: 4500,
    /** 모션 줄이기: 먼 비 정지 알파 · 재 초당 */
    reducedRainAlpha: 0.25,
    reducedAshRate: 1,
    vignette: { alpha: 0.82, depth: 10.5 },
    /** 메뉴 족자 위 먹 한 겹 알파 (족자 그림이 아직 밝은 세피아 — 아트가 어둡게 다시 그리면 0 으로) */
    frameShade: 0.45,
  },
  /** 메뉴 고른 줄 띠 색 (P21: 호박 대신 마른 피) */
  bandHex: '#5a110c',
  /** 버전 표기 (오른쪽 아래) */
  version: 'v0.62 데모',
} as const;

// ---------------------------------------------------------------------------------------------
// 아트 JSON 기본값 (title62-1)

export interface VoiceSpec {
  weapon: TitleWeapon;
  x: number;
  y: number;
  ember: [number, number];
  periodMs: number;
  offsetMs: number;
  onMs: number;
  alpha: [number, number];
}

export interface FogSpec {
  name: string;
  y: number;
  scaleY: number;
  alpha: number;
  speed: number;
}

export interface EmitterSpec {
  name: string;
  /** 시트 행 번호 */
  rows: number[];
  weights: number[];
  area: { x: number; y: number; w: number; h: number } | null;
  /** 목소리 방출기: 무기별 원점 (켜진 무기에서만) */
  voice: boolean;
  rate: [number, number];
  life: [number, number];
  vx: [number, number];
  vy: [number, number];
  driftAmp: [number, number];
  driftMs: [number, number];
  alphaMax: number;
  /** 'city' = 먼 층(far 와 mid 사이), 'near' = 주인공 층 */
  layer: 'city' | 'near';
}

/**
 * P21: title.json `layers[]` 에 아트가 새로 넣은 그림 층 (비·재·까마귀·피 웅덩이 등 — 아는 파일 밖의 `image`).
 * 화면 px 왼쪽 위 (x,y) · Phaser 깊이 = title.json depth(기존 층과 같은 번호 체계) · 패럴랙스 · 블렌드 · 알파 ·
 * `speedPxPerSec` 이 0 이 아니면 가로로 흐르는 반복 그림(안개와 같은 방식) · `flicker` 면 불씨처럼 일렁인다.
 */
export interface ExtraLayerSpec {
  /** 텍스처 이름 = image 파일 이름 (.png 뺌) */
  image: string;
  depth: number;
  parallax: number;
  blend: 'NORMAL' | 'ADD' | 'MULTIPLY' | 'SCREEN';
  x: number;
  y: number;
  alpha: number;
  speed: number;
  flicker: boolean;
}

/** 작은 그림 시트 (불티·젖은 재) */
export interface SheetSpec {
  frameW: number;
  frameH: number;
  perRow: number;
  pivot: [number, number];
  fps: number;
  rowNames: string[];
}

/** P21 비 (title.json `rain.instances` — 가로·세로로 흐르는 반복 그림) */
export interface RainSpec {
  depth: number;
  /** far = 먼 층 패럴랙스 · near = 주인공 층 */
  layer: 'far' | 'near';
  scale: number;
  alpha: number;
  vx: number;
  vy: number;
}

/** P21 까마귀 떼 (title.json `crows`) */
export interface CrowSpec {
  frameW: number;
  frameH: number;
  frames: number;
  fps: number;
  pivot: [number, number];
  intervalMs: [number, number];
  count: [number, number];
  spread: [number, number];
  y: [number, number];
  swayPx: number;
  swayMs: number;
  speed: [number, number];
  scale: [number, number];
  /** 이 배율 미만 = 먼 층 */
  nearScale: number;
  depthFar: number;
  depthNear: number;
}

/** P21 젖은 재 (title.json `ash`) */
export interface AshSpec {
  sheet: SheetSpec;
  emitters: EmitterSpec[];
  scale: [number, number];
  inMs: number;
  outMs: number;
  depth: number;
}

export interface TitleSpec {
  layers: { far: number; mid: number; near: number };
  /** P21: title.json 의 새 층 (없으면 []) */
  extras: ExtraLayerSpec[];
  parallax: { maxX: number; maxY: number; lerp: number; cover: number; driftMs: number; driftAmp: number };
  hero: { x: number; y: number; w: number; h: number; feetY: number; breathMs: number; scaleY: [number, number] };
  glow: { x: number; y: number; alpha: [number, number] };
  voices: VoiceSpec[];
  logo: {
    x: number;
    y: number;
    w: number;
    h: number;
    /** 글자와 부제를 나누는 가로줄 (로고 그림 안 y) */
    splitY: number;
    /** 무기 불씨 4개 (화면 좌표) */
    dots: Record<TitleWeapon, [number, number]>;
  };
  /** 로고 글자 상자 (로고 그림 안 [x0, y0, x1, y1] — title.json logo.lettersBox, 까마귀가 피한다). 없으면 null */
  logoBox: [number, number, number, number] | null;
  menu: { x: number; y: number; w: number; h: number; slice: number; insetX: number; insetY: number };
  fog: FogSpec[];
  embers: SheetSpec;
  /** P21 날씨 층 (title.json rain·crows·ash — 없으면 빈 값) */
  rain: RainSpec[];
  crows: CrowSpec | null;
  ash: AshSpec | null;
  emitters: EmitterSpec[];
  /** art §30: 성문(첫 생으로 파고들 자리) — 화면 px · 그 층 */
  gate: { x: number; y: number; layer: 'far' | 'mid' | 'near' };
  /** art §30 로고 쓰기 마스크 (title.json logoReveal) — ms · 붓 머리 빛 띠(0~1). null = 마스크 없이 알파 */
  logoReveal: { ms: number; softBand: number; embersAt: number } | null;
}

export const EMBER_ROWS = ['amber_s', 'amber_m', 'amber_l', 'katana', 'greatsword', 'dagger', 'bow'];

export const DEFAULT_TITLE_SPEC: TitleSpec = {
  layers: { far: 0.15, mid: 0.4, near: 1.0 },
  extras: [],
  logoBox: null,
  rain: [],
  crows: null,
  ash: null,
  parallax: { maxX: 28, maxY: 10, lerp: 0.035, cover: 1.03, driftMs: 24000, driftAmp: 0.35 },
  hero: { x: 1359, y: 450, w: 237, h: 567, feetY: 1014, breathMs: 4200, scaleY: [1.0, 1.008] },
  glow: { x: 1323, y: 408, alpha: [0.55, 1.0] },
  voices: [
    {
      weapon: 'katana',
      x: 1643,
      y: 670,
      ember: [1737, 690],
      periodMs: 9600,
      offsetMs: 0,
      onMs: 1700,
      alpha: [0.25, 1],
    },
    {
      weapon: 'greatsword',
      x: 1164,
      y: 656,
      ember: [1224, 675],
      periodMs: 9600,
      offsetMs: 2400,
      onMs: 1700,
      alpha: [0.25, 1],
    },
    {
      weapon: 'dagger',
      x: 1302,
      y: 820,
      ember: [1370, 840],
      periodMs: 9600,
      offsetMs: 4800,
      onMs: 1700,
      alpha: [0.25, 1],
    },
    {
      weapon: 'bow',
      x: 1735,
      y: 662,
      ember: [1820, 681],
      periodMs: 9600,
      offsetMs: 7200,
      onMs: 1700,
      alpha: [0.25, 1],
    },
  ],
  logo: {
    x: 40,
    y: 20,
    w: 1200,
    h: 399,
    splitY: 295,
    dots: { katana: [553, 407], greatsword: [607, 407], dagger: [661, 407], bow: [715, 407] },
  },
  menu: { x: 110, y: 650, w: 400, h: 350, slice: 48, insetX: 36, insetY: 39 },
  gate: { x: 901, y: 680, layer: 'far' },
  logoReveal: { ms: 2600, softBand: 0.02, embersAt: 0.96 },
  fog: [
    { name: 'fog_far', y: 600, scaleY: 0.75, alpha: 0.55, speed: -4 },
    { name: 'fog_mid', y: 760, scaleY: 1, alpha: 0.7, speed: 9 },
    { name: 'fog_near', y: 930, scaleY: 0.62, alpha: 0.35, speed: 16 },
  ],
  embers: { frameW: 24, frameH: 24, perRow: 8, pivot: [10, 13], fps: 10, rowNames: EMBER_ROWS },
  emitters: [
    {
      name: 'mound',
      rows: [0, 1, 2],
      weights: [5, 3, 1],
      area: { x: 1080, y: 900, w: 720, h: 140 },
      voice: false,
      rate: [6, 9],
      life: [4500, 8000],
      vx: [8, 30],
      vy: [-46, -22],
      driftAmp: [6, 14],
      driftMs: [1600, 2600],
      alphaMax: 1,
      layer: 'near',
    },
    {
      name: 'back_crack',
      rows: [0, 1],
      weights: [3, 1],
      area: { x: 1440, y: 600, w: 60, h: 150 },
      voice: false,
      rate: [1, 2],
      life: [2500, 4500],
      vx: [10, 26],
      vy: [-40, -18],
      driftAmp: [6, 14],
      driftMs: [1600, 2600],
      alphaMax: 1,
      layer: 'near',
    },
    {
      name: 'voices',
      rows: [3, 4, 5, 6],
      weights: [1, 1, 1, 1],
      area: null,
      voice: true,
      rate: [2, 3],
      life: [1800, 3200],
      vx: [-6, 10],
      vy: [-34, -16],
      driftAmp: [6, 14],
      driftMs: [1600, 2600],
      alphaMax: 1,
      layer: 'near',
    },
    {
      name: 'city',
      rows: [0],
      weights: [1],
      area: { x: 560, y: 520, w: 520, h: 120 },
      voice: false,
      rate: [1, 1],
      life: [3000, 5000],
      vx: [2, 8],
      vy: [-10, -4],
      driftAmp: [3, 6],
      driftMs: [1600, 2600],
      alphaMax: 0.5,
      layer: 'city',
    },
  ],
};
