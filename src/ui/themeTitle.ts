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
export const TITLE_JSONS = ['title', 'title_fx_embers', 'title_fx_fog', 'title_menu_frame'] as const;
export type TitleJson = (typeof TITLE_JSONS)[number];
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
  /** 등장: 그림이 다 읽힌 뒤 기준 (ms). 3초 안에 메뉴까지 */
  intro: {
    blackMs: 150,
    revealMs: 1400,
    /** 모션 줄이기: 붓질 대신 걷히는 페이드 */
    fadeMs: 600,
    logoAt: 850,
    logoMs: 1100,
    subAt: 1450,
    subMs: 600,
    dotsAt: 1900,
    dotGapMs: 140,
    dotMs: 240,
    menuAt: 1900,
    menuMs: 400,
    /** 메뉴 줄 하나씩 늦게 */
    menuStaggerMs: 40,
    endMs: 2600,
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
  dive: { ms: 900, zoom: 3.4, pull: 1, lightHex: '#e8b858' },
  /** '아무 키나 누른다' (점검 T3): 숨쉬듯 깜빡임 주기 */
  promptBlinkMs: 1800,
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

export interface TitleSpec {
  layers: { far: number; mid: number; near: number };
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
  menu: { x: number; y: number; w: number; h: number; slice: number; insetX: number; insetY: number };
  fog: FogSpec[];
  embers: { frameW: number; frameH: number; perRow: number; pivot: [number, number]; fps: number; rowNames: string[] };
  emitters: EmitterSpec[];
  /** art §30: 성문(첫 생으로 파고들 자리) — 화면 px · 그 층 */
  gate: { x: number; y: number; layer: 'far' | 'mid' | 'near' };
  /** art §30 로고 쓰기 마스크 (title.json logoReveal) — ms · 붓 머리 빛 띠(0~1). null = 마스크 없이 알파 */
  logoReveal: { ms: number; softBand: number; embersAt: number } | null;
}

export const EMBER_ROWS = ['amber_s', 'amber_m', 'amber_l', 'katana', 'greatsword', 'dagger', 'bow'];

export const DEFAULT_TITLE_SPEC: TitleSpec = {
  layers: { far: 0.15, mid: 0.4, near: 1.0 },
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
