/** 시트 JSON 형식 (계약 art-assets §1 + §3.1 보강)과 도트 → 월드 단위 변환 (57라운드 B7: spriteDefs 에서 분리). Phaser 의존 없음. */
import type { BranchSheetFields } from '../fx/branchFx';
import { RENDER, SPRITES } from '../../core/Constants';
import type { AnchorPoint, BladeLocal, HandAnchor, StrideSpec } from './spriteMeta';
import { type SpriteCategory, STRUCTURE_ACTION } from './spriteActions';
import type { Dir8, Facing } from './spriteDirs';

/** 계약 §3.1 이펙트 앵커 */
export type FxAnchor = 'player_pivot' | 'hitbox_center' | 'projectile' | 'ui';

/**
 * 50라운드 계약 art §9 광원: 이 시트(소품·구조물·이펙트)를 그리는 동안 주변을 밝힌다.
 * color = '#rrggbb' 또는 팔레트 경로, radius = 반경 px(시트 도트 기준 — pixelScale 로 월드 환산), intensity 0..1,
 * flicker = 깜빡임 세기 0..1 (없으면 고정)
 */
export interface LightSpec {
  color?: string;
  radius: number;
  intensity?: number;
  /** 깜빡임 세기 0..1 — 아트 v2 는 { amp, hz } 로도 적는다 (amp 를 쓴다) */
  flicker?: number | { amp: number; hz?: number };
  /** 광원 중심: 피벗에서 위로 px (시트 도트 기준, 없으면 프레임 세로 중앙) — 시스템 확장 필드 */
  offsetY?: number;
  /** 계약 §12: 광원 중심 = 시트 프레임 안 [x, y] 도트 좌표 (있으면 offsetY 대신) */
  offset?: [number, number] | { x: number; y: number };
}

/** 계약 §1 JSON 필드 (+ §3.1 보강 필드는 선택). 51·52라운드 갈래 메모(secondaryVariants·heatVariants·tailSheets)는 `branchFx` */
export interface SheetJson extends BranchSheetFields {
  image: string;
  /**
   * 50라운드 계약 §9: 도트 배율. 새 2배 도트(32×48 캐릭터·32px 타일) = 1, 기존 도트 = 없음/2.
   * 시스템은 기존 도트를 2배로 그려 화면 크기를 맞춘다 (`artScale`)
   */
  pixelScale?: number;
  /**
   * 53라운드 Q62 (계약 §13): `"none"` 이면 층(지역) 바닥 램프 교체에서 뺀다 — 주인공 재·호박 고정색. 이펙트(`fx`)는 값이 없어도 뺀다
   * (`paletteSwapExempt`)
   */
  paletteSwap?: string;
  /** 52라운드 Q10 (계약 §12): 걷기·달리기 한 주기 이동 도트·주기 ms — 재생 배속을 실제 속도에 맞춘다 (`spriteMeta.strideRate`) */
  stride?: StrideSpec;
  /** 52라운드 Q13 v3 몸: 프레임별 양손 중심 (시트 도트, 방향 → 열 목록) */
  handAnchors?: Partial<Record<Dir8, HandAnchor[]>>;
  /** 52라운드 Q13 v3 무기: 칼을 쥔 손 (무기 시트 도트, 방향 → 열 목록) · 몸 기준 칼 방향 (열 목록) */
  gripAnchors?: Partial<Record<Dir8, AnchorPoint[]>>;
  bladeLocal?: BladeLocal[];
  /**
   * 53라운드 Q4 (계약 §13) v3 몸: 프레임별 등 상흔 사각형 {x, y, w, h, rot, visible} (도트, x·y = 중심). 형식은 handAnchors 처럼
   * 방향 → 열 목록 (또는 시트 프레임 순서 배열) — `spriteMeta.scarAt` 이 읽는다
   */
  scarAnchor?: unknown;
  /**
   * 53라운드 Q19 (아트 제안, v3 몸 변형·휴대 시트): 무기별 이동 몸 시트 — 무기 id → `player_<동작>[_free]`
   * (값이 객체면 기본 동작 → 시트). `spriteMeta.bodyActionFor` 가 읽는다
   */
  bodySheetByWeapon?: Record<string, string | Record<string, string>>;
  /** 53라운드 적 v3 (사수): 발사 프레임 · 프레임별 총구 도트 좌표 (총을 놓친 프레임은 null) */
  fireFrame?: number;
  muzzleAnchors?: Partial<Record<Dir8, (AnchorPoint | null)[]>>;
  /** 52라운드 v3 무기: 무기 시트 좌표 = 몸 시트 좌표 + 이 값 (피벗 정렬) */
  playerFrameOffset?: { x: number; y: number };
  /** 52라운드 v3 무기: 몸 뒤로 가는 픽셀을 시트에서 지웠다 → 늘 몸 위(above) */
  occlusionBaked?: boolean;
  /** 52라운드 v3 칼 연격: 연격 동안 휴대 시트를 숨긴다 (값은 메모 문자열일 수 있다 — 참이면 숨김) */
  carryHidden?: boolean | string;
  /** 52라운드 v3 무기: 방향·프레임별 깊이 (있으면 depth 보다 우선) */
  depthByFrame?: Partial<Record<Dir8, ('above' | 'below')[]>>;
  /** 50라운드 계약 §9: 높이가 있는 구조물·소품 — 피벗(바닥 접점)에서 이 높이(px, 시트 도트) 위로는 캐릭터를 가린다 */
  occludeAbove?: number;
  /** 50라운드 계약 §9: 광원 */
  light?: LightSpec;
  /** 54라운드 아트 boss1_onfire: 국면별 광원 (phaseFrames 이름 → light 형식) */
  lightByPhase?: Record<string, LightSpec>;
  /** 54라운드 Q23·Q28 boss1_onfire: 누운 자세 불길 시트 이름 (`boss1_onfire_down`) */
  lyingSheet?: string;
  /**
   * 54라운드 Q23·Q28 boss1_onfire_down: 보스 동작 → 이 시트를 쓰는 보스 프레임 열 (useFor) · 서 있는 불길을 쓰는 열 (standFor) ·
   * 그 보스 프레임에서 오버레이를 옮길 [dx, dy] 도트 (frameOffsets, 동작 → 열 → [dx, dy]) — `systems/boss/onfireMap`
   */
  useFor?: Record<string, number[]>;
  standFor?: Record<string, number[]>;
  frameOffsets?: Record<string, Record<string, [number, number]>>;
  action: string;
  frameWidth: number;
  frameHeight: number;
  frames: number;
  directions: string[];
  fps: number;
  frameDurationsMs?: number[];
  loop: boolean;
  pivot: { x: number; y: number };
  /** §3.1 이펙트 앵커 */
  anchor?: FxAnchor;
  /** §3.1 투사체 앵커: 진행 각도로 회전 (drawnFacing 기준) */
  rotate?: boolean;
  drawnFacing?: 'right' | 'left' | 'up' | 'down';
  /**
   * 깊이. 무기 오버레이(§3.1)는 방향별 above / below, 이펙트(§3.2)는 문자열 above(개체 위) / below(개체 아래·바닥).
   * 이펙트의 기본 깊이를 정할 때 쓴다 (호출 쪽이 깊이를 주면 그쪽이 우선)
   */
  depth?: 'above' | 'below' | 'floor' | 'y' | Partial<Record<Dir8, 'above' | 'below' | ('above' | 'below')[]>>;
  // --- 계약 §5 구조물 시트 (47라운드) ---
  /** 단단한 영역 타일 수 [가로, 세로] */
  footprint?: [number, number];
  /** 지나갈 수 없음 */
  solid?: boolean;
  /** 상태별 프레임: idle · used · broken(마지막 프레임 유지) · active(루프) · hit(1프레임) + 시트별 추가 상태 */
  states?: Record<string, number[]>;
  /** 상태별 반복 여부 (없으면 active·ready 만 반복) */
  stateLoop?: Record<string, boolean>;
  /** 1-1 술통 구르기: 그려진 방향 · 다른 방향은 회전 */
  rollDrawnFacing?: 'down' | 'up' | 'left' | 'right';
  rollRotate?: boolean;
  /** 1-2 화로 불꽃 영역 (프레임 좌표) */
  fireBox?: { x: number; y: number; w: number; h: number };
  /** 2-3 투견 링 말뚝 중심 (프레임 좌표) · 판돈 깃대 (E 기준점) */
  stakes?: [number, number][];
  flagpost?: { x: number; y: number };
  /** 2-5 룰렛: 칸 i 를 가리키는 프레임 */
  stopFrames?: Record<string, number>;
  /** 층 테마 구조물 메모 ('stage1' | 'stage2') */
  floor?: string;
  /** §3.1 재생 시점 메모 (코드가 읽지 않음) */
  spawn?: string;
  /** 35라운드 피격 시트: 마지막 n 프레임이 잔류(바닥 얼룩) — 시스템이 유지 후 페이드할 수 있다 */
  tailFrames?: number;
  /** 35라운드 예고 마커(telegraph_line)·조준 점선(aim_line): 길이 방향으로 타일 반복 */
  tile?: boolean;
  /** 보스 attack 국면별 프레임 열 (결정 로그 J): 예고 유지 / 돌진 반복 / 멈춤·벽 경직·부채꼴 */
  phaseFrames?: PhaseFrames;
  /** 54라운드 계약 §15 보스 v3 drink: 프레임별 약점 잔 사각형 {x, y, w, h} (시트 도트) — 방향 → 열 목록 또는 열 목록 */
  cupAnchors?: unknown;
  /** 54라운드 계약 §15 보스 v3 kick: 프레임별 발 좌표 (술통 시작점) */
  footAnchors?: unknown;
  /** 61라운드 E 아트 2 `fx/v3/boss1_break_daze`: 보스 동작 → 방향 → 열별 머리 꼭대기 [x, y] (보스 시트 도트) */
  headTopAnchors?: unknown;
  /** 61라운드 E 아트 2 구조물(허수아비 `tutorial_dummy`): 이름 → 점 {x, y} (시트 도트 — hitCenter·headTop) */
  anchors?: unknown;
  /** 61라운드 E 아트 2: 등장 걸음 반복 열 [처음, 끝] · 건배 유지 열 [처음, 끝] · 포효 열 (보스 intro — 보폭은 stride) */
  walkLoop?: number[];
  toastLoop?: number[];
  roarFrame?: number;
  /** 54라운드 아트 v3 보스: 예고 동안 유지할 열 (attack·stagger_dash). 55라운드 적중 스파크: 히트스톱 중 정지 프레임 */
  holdFrame?: number;
  // --- 55라운드 계약 §16 (타격감·움직임·갈래) ---
  /** 판정 순간 백열 프레임 (연격·적중 시트) */
  glowFrames?: number[];
  /** 적중 시트 흔들림 제안 {px, ms} (아트 임시값 — 시스템 hitFeel 이 읽는다) */
  shakeHint?: unknown;
  /** 회전 시트 위아래 뒤집기 허용 ("allowed") */
  flipY?: string | boolean;
  /** 방향별 깊이 (ironwall {"up": "below"}) */
  depthByDirection?: Partial<Record<Dir8, 'above' | 'below'>>;
  /** 재 파편 입자 묶음 (particles_ash — `ashParticleMath` 가 읽는다) */
  kinds?: unknown;
  recipes?: unknown;
  /** 잔상 리본 텍스처 메모 (ribbon_ash — 나이 프레임 ageFrames 등) */
  ribbon?: { ageFrames?: number[]; widthDots?: number };
  /** 53라운드 Q63 연격 궤적 메모: 칼끝 반경(도트, 판정 원점 기준) — 칼끝 메모가 없는 무기의 리본 반경 */
  trailFill?: { bladeTipRadiusDots?: number };
  /** 55라운드 v3 무기: 프레임별 칼끝 (무기 시트 도트, 방향 → 열 목록) */
  bladeTipAnchors?: Partial<Record<Dir8, AnchorPoint[]>>;
  // --- 56라운드 (무기 피드백 — 아트 JSON 메모, 시스템이 읽는 것만) ---
  /** Q11 붓획 이펙트 (히트스톱 정지 = 붓획이 다 그어진 다음 칸, Q37) */
  brushStroke?: boolean;
  /** 프레임 역할 (Q51 정지 칸 계산 — 문자열 배열, 종류별 시트는 표) */
  frameRoles?: unknown[] | Record<string, unknown[]>;
  /** Q5 대검 무게: 선딜 버팀 열 · 휘두른 뒤 끌림 열 · 끌림 이동 참고값 (world = 월드 px, frames = 몸이 끌리는 열) */
  holdFrames?: number[];
  dragFrames?: number[];
  dragStepPx?: { world?: number; frames?: number[]; startMs?: number };
  /** Q10 꽂아내리기: 칼이 바닥에 꽂힌 점 (몸 시트 도트, 방향 → 열 목록, 꽂히지 않은 열은 null) */
  plantAnchors?: Partial<Record<Dir8, ([number, number] | null)[]>>;
  /** 58라운드 Q3 차지 휘둘러 내리찍기: 칼끝이 바닥에 닿은 점 (몸 시트 도트, slamFrames 만 값) — 균열 선·땅 충격 자리 */
  slamAnchors?: Partial<Record<Dir8, ([number, number] | null)[]>>;
  /** Q9 활: 가득 열 · 유지 반복 [시작, 끝] · 흔들림 반복 [시작, 끝] · 화살이 생기는 점 (무기 시트 도트) */
  fullFrame?: number;
  holdLoop?: [number, number];
  strainLoop?: [number, number];
  arrowSpawnAnchors?: Partial<Record<Dir8, (AnchorPoint | null)[]>>;
  /** Q2 일섬 그림자 분신: 출발→도착 이동 열 · 이동 ms · 베기 열 */
  travelFrames?: number[];
  travelMs?: number;
  /** 54라운드 아트 v3 술통 회전 시트: 한 바퀴 굴림 둘레 (**논리 px** = 도트 × 0.5 — 아트 rotationNote, `caskCircumferenceWorld`) */
  circumferencePx?: number;
  /** 54라운드 아트 2차 술통: 그림 지름 · 길이 (논리 px) — 판정 반경 (`caskRadiusFromArt`) */
  diameterPx?: number;
  lengthPx?: number;
  // --- §3.2 (42·43라운드 양산 필드). 있으면 시스템이 쓰고 없으면 기본값 ---
  /** 이 이펙트가 속한 무기 id · 보조 동작 종류 (메모) */
  weapon?: string;
  secondary?: string;
  /** 재생 중 궤적(호·스프라이트 위치)을 잇는 리본 트레일: 색·알파·수명 ms·시작 프레임·폭 비율 */
  trail?: FxTrailSpec;
  /** 특정 프레임에 화면 섬광 */
  flash?: FxFlashSpec;
  /** 화면 흔들림. 시각 = flash.atFrame (없으면 타격 프레임) 시작 */
  shake?: FxShakeSpec;
  /** 2단 판정이 같은 시트 안에 있는 경우 (quake): 그 프레임에 섬광·흔들림을 한 번 더 */
  secondStage?: { frame?: number; atMs?: number; flash?: FxFlashSpec; shake?: FxShakeSpec };
  /** 연타 시트(twin·dance): 각 타격이 보이는 프레임 열. 시스템이 추가 타격 판정 간격을 이 프레임 시작 시각에 맞춘다 */
  hitFrames?: number[];
  // --- 48라운드 계약 art §6 메모 필드 (있으면 시스템이 쓴다) ---
  /** 연격 번호 (1부터) */
  comboIndex?: number;
  /** 다음 타로 넘어갈 수 있는 프레임 (이 프레임 시작 = 다음 타 허용). 마지막 타는 null */
  cancelFromFrame?: number | null;
  /** 베기 호 각도(도) — 판정 부채꼴 각도. from→to = 휘두름 방향 (right 기준 화면각, + = 아래) */
  arcDeg?: number;
  arcFromDeg?: number;
  arcToDeg?: number;
  /** 판정 구간 프레임 (첫 열 시작 ~ 마지막 열 끝) */
  activeFrames?: number[];
  /** 찌르기 판정 (단검): 길이·폭, 방향 비틀림(도), 몸에서 떨어진 시작 거리 */
  thrust?: { lengthPx: number; widthPx: number; angleDeg?: number; fromPx?: number };
  /** 탄생 시트: 잔불이 터지는 프레임 */
  burstFrame?: number;
  /** 49라운드 §7.2 대검 내리찍기: 도약 프레임 열 (첫 열 시작 ~ 마지막 열 끝 = 공중) · 대쉬 공격·내리찍기 회복 프레임 */
  leapFrames?: number[];
  recoverFrames?: number[];
  /** 49라운드: 이펙트 f0 재생 시각 ms (몸 시트 기준, 재생 배속 반영 전) */
  fxSpawnAtMs?: number;
  /** 49라운드 내리찍기: 발 피벗에서 착지(충격파 중심)까지 — 방향별 오프셋 px 우선, 없으면 조준 방향 거리 */
  impactOffsetPx?: Partial<Record<Dir8, { x: number; y: number }>>;
  impactDistancePx?: number;
  /** 49라운드 내리찍기 도약 프레임별 몸 띄우기 px (제안 메모 — 시스템 미적용) */
  leapOffsetsPx?: Record<string, number>;
  /** 49라운드 대쉬 공격: 재사용 이펙트 id · 재생 시각 ms */
  fxReuse?: { id: string; spawnAtMs?: number };
  /** 49라운드 활 장전: 탄창이 차는 프레임 */
  refillFrame?: number;
  /** 49라운드 탄생(혼불 버전): 바닥 이펙트(under, underOptional = 없어도 됨) · 둘레 혼불(ambient) */
  fx?: { under?: string; underOptional?: boolean; ambient?: string };
  /** 특수 자세 구간 (패링 ready/window/riposte/recover · 가드 enter/hold/release/recover · 그림자 걸음 depart/arrive/primed) */
  phases?: Record<string, number[]>;
  /** 가드를 누르는 동안 반복할 열 (55라운드: 대검 차지 유지 루프도) */
  loopFrames?: number[];
  /** 55라운드 §17 연격 몸 메모: 내딛기 참고값 (world = 월드 px, frames = 몸이 앞으로 나가는 열) — 시스템은 frames 시간만 쓴다 */
  stepPx?: { world?: number; frames?: number[] };
  /** 활 조준: 진행도 프레임 목록 · 발사 프레임 */
  progressFrames?: number[];
  releaseFrame?: number;
  /** 시간 애니가 아닌 상태별 고정 프레임 (aim_line: charging 0 / complete 1) */
  stateFrames?: Record<string, number | number[]>;
  /** 시스템 틴트 메모 (dash_trail): method 에 'setTintFill' 이 있으면 평면 틴트 */
  tint?: { when?: string; color?: string; method?: string };
  /** 같은 그림의 대체 시트 id (hit_spark → hit_burst) */
  alias?: string;
  /** 예비 프레임 메모 (코드가 읽지 않음 — 규칙은 `fxImpactFrame`) */
  spawnNote?: string;
  /** 시간이 아니라 진행도(0..1)로 프레임을 정한다 (aim_charge·telegraph_circle·telegraph_cone) */
  progressDriven?: boolean;
  /** 적중한 대상에 붙어 따라간다 (bleed) / 플레이어를 따라간다 (longinvuln·giant) */
  followsTarget?: boolean;
  followsPlayer?: boolean;
  /** 표시 배율 (숫자면 기본 배율, "allowed" 같은 문자열은 '호출 쪽이 배율을 정해도 됨' 메모 → 1) */
  scale?: number | string;
  /** 시트가 그린 판정 반경 px (boss_slam: 40). `scale: "allowed"` 시트의 배율 기준 */
  hitRadiusPx?: number;
  pivotNote?: string;
  /**
   * (시스템 제안, 계약 외) 예비 프레임이 앞에 있을 때 이 프레임이 spawn 시점에 오도록 그만큼 먼저 재생한다.
   * 없으면 `fxImpactFrame` 규칙 (attack_frame2 시트는 f0 = 예비 → 1). 54라운드 계약 §15 보스 v3: 타격 프레임 (slam·kick)
   */
  impactFrame?: number;
}

export interface FxTrailSpec {
  /** '#rrggbb' 또는 팔레트 참조 'fx.weapons.<무기>.ramp[i]' · 'fx.core[i]' */
  color?: string;
  alpha?: number;
  ms?: number;
  fromFrame?: number;
  /** 리본 폭 = 본 띠 두께 × 비율 (없으면 FEEL.TRAIL.WIDTH_RATIO) */
  widthRatio?: number;
}

export interface FxShakeSpec {
  px: number;
  ms: number;
}

export interface FxFlashSpec {
  color?: string;
  alpha?: number;
  ms?: number;
  atFrame?: number;
}

export interface PhaseFrames {
  telegraph?: number[];
  dash?: number[];
  recover_or_fan?: number[];
  /** 54라운드 계약 §15 보스 v3 동작 국면 (drink lift·gulp·finish · fall fall·down·rise · drink_break break·stagger 등) */
  [phase: string]: number[] | undefined;
}

/**
 * 50라운드 계약 §9: 시트 도트 1px 이 월드 몇 단위인지. 월드 1단위 = 화면 RENDER.WORLD_TO_SCREEN px 이므로
 * 기존 도트(pixelScale 없음 = 2) → 1, 새 2배 도트(pixelScale 1) → 0.5 (도트 1px = 화면 1px)
 */
export function artScale(def: Pick<SheetJson, 'pixelScale'>): number {
  const ps = typeof def.pixelScale === 'number' && def.pixelScale > 0 ? def.pixelScale : RENDER.LEGACY_PIXEL_SCALE;
  return ps / RENDER.WORLD_TO_SCREEN;
}

/**
 * 시트 메모 중 월드 길이 필드(판정 반경·찌르기·착지 오프셋·광원 반경 등)를 월드 단위로 바꾼 사본.
 * 프레임 크기·피벗·프레임 좌표 필드(fireBox·stakes·flagpost)는 텍스처 좌표라 그대로 둔다. 기존 도트는 그대로(배율 1)
 */
export function sheetToWorldUnits<T extends SheetJson>(json: T): T {
  const k = artScale(json);
  if (k === 1) return json;
  const out: T = { ...json };
  const px = (v: number | undefined) => (typeof v === 'number' ? v * k : v);
  if (typeof json.hitRadiusPx === 'number') out.hitRadiusPx = json.hitRadiusPx * k;
  if (json.thrust)
    out.thrust = {
      ...json.thrust,
      lengthPx: json.thrust.lengthPx * k,
      widthPx: json.thrust.widthPx * k,
      fromPx: px(json.thrust.fromPx),
    };
  if (json.impactOffsetPx) {
    const o: Partial<Record<Dir8, { x: number; y: number }>> = {};
    for (const [d, v] of Object.entries(json.impactOffsetPx)) if (v) o[d as Facing] = { x: v.x * k, y: v.y * k };
    out.impactOffsetPx = o;
  }
  if (typeof json.impactDistancePx === 'number') out.impactDistancePx = json.impactDistancePx * k;
  if (json.light) out.light = { ...json.light, radius: json.light.radius * k, offsetY: px(json.light.offsetY) };
  if (json.lightByPhase) {
    const byPhase: Record<string, LightSpec> = {};
    for (const [ph, l] of Object.entries(json.lightByPhase))
      if (l) byPhase[ph] = { ...l, radius: l.radius * k, offsetY: px(l.offsetY) };
    out.lightByPhase = byPhase;
  }
  if (typeof json.occludeAbove === 'number') out.occludeAbove = json.occludeAbove * k;
  return out;
}

/** 53라운드 Q62: 바닥 램프 교체 제외 시트 — 이펙트 분류 전체 또는 JSON `paletteSwap: "none"` */
export function paletteSwapExempt(def: Pick<SheetJson, 'paletteSwap'> & { category?: SpriteCategory }): boolean {
  return def.category === 'fx' || def.category === 'items' || def.paletteSwap === 'none';
}

export interface SheetDef extends SheetJson {
  category: SpriteCategory;
  name: string;
  /** 기준 텍스처 키 (`sheet_player_idle`) */
  textureKey: string;
  /** PNG URL */
  imageUrl: string;
}

/**
 * 구조물 시트 JSON 보정 (계약 §5 는 fps·loop·directions·pivot 을 생략할 수 있다): 없는 값은
 * frameDurationsMs 평균 fps(없으면 8) · loop false · directions ["any"] · pivot = 발판 아래 가운데
 */
export function normalizeStructureSheet(json: SheetJson): SheetJson {
  const d = json.frameDurationsMs;
  const avg = d && d.length > 0 ? d.reduce((a, b) => a + b, 0) / d.length : 0;
  return {
    ...json,
    action: json.action ?? STRUCTURE_ACTION,
    fps: json.fps > 0 ? json.fps : avg > 0 ? 1000 / avg : 8,
    loop: Boolean(json.loop),
    directions: Array.isArray(json.directions) && json.directions.length > 0 ? json.directions : ['any'],
    pivot: json.pivot ?? { x: Math.floor(json.frameWidth / 2), y: json.frameHeight },
  };
}

/** 구조물 상태의 프레임 목록. 없는 상태면 idle 첫 프레임 (계약 §5) */
export function structureStateFrames(def: Pick<SheetJson, 'states' | 'frames'>, state: string): number[] {
  const list = def.states?.[state];
  if (Array.isArray(list) && list.length > 0) return list.filter((f) => f >= 0 && f < def.frames);
  const idle = def.states?.idle;
  return [Array.isArray(idle) && idle.length > 0 ? idle[0] : 0];
}

/** JSON `scale` 이 양수 숫자면 그 값, 아니면 1 ("allowed" 메모 등) */
export function sheetScale(def: Pick<SheetJson, 'scale'>): number {
  return typeof def.scale === 'number' && def.scale > 0 ? def.scale : 1;
}

/**
 * 53라운드 v3 적(주인공과 같은 1.5배 그림): 피격 연출(섬광·숫자)을 바디 중심에서 그림 중심(피벗 높이의 절반)으로 올리는
 * 거리(월드). 판정·바디는 그대로. v3 가 아니면 0 (구 시트·v2 는 기존 자리)
 */
export function v3HitLift(def: Pick<SheetJson, 'pivot' | 'pixelScale'>, bodyH: number, drawScale = 1): number {
  if (!(typeof def.pixelScale === 'number' && def.pixelScale <= SPRITES.V3_PIXEL_SCALE)) return 0;
  return Math.max(0, (def.pivot.y * artScale(def) * drawScale) / 2 - bodyH / 2);
}

/**
 * 이펙트·투사체 시트를 그리는 배율 = JSON scale × 도트 배율(`artScale`). 53라운드 이펙트 v3(`fx/v3/<이름>`, pixelScale 0.5)는
 * 기존 크기 ×2 도트라 0.25 배로 그려 화면 크기·판정 자리를 기존과 같게 한다 (구 시트 = 1)
 */
export function fxDrawScale(def: Pick<SheetJson, 'scale' | 'pixelScale'>): number {
  return sheetScale(def) * artScale(def);
}

/**
 * `scale: "allowed"` 시트를 판정 반경에 맞추는 배율 (계약 §3.2 boss_slam: R / 기준 반경, 정수 배율만).
 * 비율이 정수(1e-6 오차)이고 1 이상이면 그 값, 아니면 1 — 픽셀아트를 비정수로 늘리지 않는다
 */
export function radiusFitScale(radiusPx: number, baseRadiusPx: number): number {
  if (!(radiusPx > 0) || !(baseRadiusPx > 0)) return 1;
  const r = radiusPx / baseRadiusPx;
  const n = Math.round(r);
  return n >= 1 && Math.abs(r - n) < 1e-6 ? n : 1;
}
