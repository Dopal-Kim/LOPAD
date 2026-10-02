/**
 * 스프라이트 시트 정의 (계약 contracts/art-assets.md §1). Phaser 의존 없음.
 * 로드 대상 목록·키 규칙·재생 시간 계산을 담당하고, 실제 로드·애니 등록은 systems/sprites.ts.
 */
import { ASSETS, RENDER, TEXTURES } from '../core/Constants';

/** structures = 47라운드 상호작용 구조물 시트 (계약 art-assets §5, `sprites/structures/<id>.json`) */
export type SpriteCategory = 'player' | 'enemies' | 'bosses' | 'weapons' | 'fx' | 'structures';
export type Facing = 'down' | 'up' | 'left' | 'right';
export const FACINGS: readonly Facing[] = ['down', 'up', 'left', 'right'];

/** 계약 §1 동작 목록 */
export const PLAYER_ACTIONS = ['idle', 'walk', 'attack', 'dash', 'hurt', 'death'] as const;
export const MOB_ACTIONS = ['idle', 'walk', 'attack', 'hurt', 'death'] as const;
/** 계약 §3.1 손에 든 무기 오버레이 동작 */
export const WEAPON_ACTIONS = ['attack'] as const;

/** 48라운드 계약 art §6: 연격 수 · 탄생 동작 · 탄생 흙 이펙트 */
export const COMBO_HITS = 3;
export const BIRTH_ACTION = 'birth';
export const BIRTH_FX = 'birth_dust';

/** 주인공 몸 연격 시트 동작 `player_<무기>_combo<n>` (n 은 1부터) */
export function comboAction(weaponId: string, n: number): string {
  return `${weaponId}_combo${n}`;
}

/** 손에 든 무기 연격 시트 동작 `weapons/<무기>_combo<n>` */
export function weaponComboAction(n: number): string {
  return `combo${n}`;
}

/** 무기를 든 특수 동작 `player_<무기>_special` / 활 조준 `player_bow_aim` (§6.2) */
export function specialAction(weaponId: string): string {
  return `${weaponId}_special`;
}

export function aimAction(weaponId: string): string {
  return `${weaponId}_aim`;
}

/** 연격 베기 이펙트 `fx/<무기>_combo<n>` */
export function comboFxId(weaponId: string, n: number): string {
  return `${weaponId}_combo${n}`;
}

/**
 * 49라운드 계약 art §7.1·7.2: 무기를 든 몸 동작 접미 — 뽑기 · 넣기(납도) · 대검 내리찍기 · 대검 대쉬 공격 · 활 장전.
 * 몸 `player/player_<무기>_<동작>`, 무기 `weapons/<무기>_<동작>` (같은 열·같은 시각, §6.1 겹침 규칙)
 */
export const WEAPON_MOTIONS = ['draw', 'sheathe', 'slam', 'dashslash', 'reload'] as const;
export type WeaponMotion = (typeof WEAPON_MOTIONS)[number];

/** 몸 동작 `<무기>_<motion>` */
export function motionAction(weaponId: string, motion: WeaponMotion): string {
  return `${weaponId}_${motion}`;
}

/** 49라운드 §7.1 휴대 오버레이 동작 `weapons/<무기>_carry_<idle|walk|dash>` */
export type CarryAction = 'idle' | 'walk' | 'dash';
export const CARRY_ACTIONS: readonly CarryAction[] = ['idle', 'walk', 'dash'];
export function carryAction(a: CarryAction): string {
  return `carry_${a}`;
}

/** 49라운드 아트 추가(계약 외 임시): 칼·대검을 뽑아 든 채(넣기 전) `weapons/<무기>_carry_drawn_<a>` */
export function carryDrawnAction(a: CarryAction): string {
  return `carry_drawn_${a}`;
}

/** 몸 동작 → 휴대 오버레이 동작 (idle·walk·dash 그대로, 피격·뽑기·넣기는 idle). 사망·탄생은 null(숨김) */
export function carryActionFor(playerAction: string): CarryAction | null {
  if (playerAction === 'walk' || playerAction === 'dash' || playerAction === 'idle') return playerAction;
  if (playerAction === 'death' || playerAction === BIRTH_ACTION) return null;
  return 'idle';
}

/** 무기별 48·49라운드 주인공 동작 (연격 3 · 특수 · 조준 · 뽑기·넣기·내리찍기·대쉬 공격·장전) */
export function playerWeaponActions(weaponId: string): string[] {
  const out: string[] = [];
  for (let n = 1; n <= COMBO_HITS; n++) out.push(comboAction(weaponId, n));
  out.push(specialAction(weaponId), aimAction(weaponId));
  for (const m of WEAPON_MOTIONS) out.push(motionAction(weaponId, m));
  return out;
}

/** 무기 오버레이 동작 (연격 3 · 특수 · 조준 · 49라운드 휴대 3 · 뽑기·넣기·내리찍기·대쉬 공격·장전) */
export const WEAPON_EXTRA_ACTIONS: readonly string[] = [
  ...Array.from({ length: COMBO_HITS }, (_, i) => weaponComboAction(i + 1)),
  'special',
  'aim',
  ...CARRY_ACTIONS.map(carryAction),
  ...CARRY_ACTIONS.map(carryDrawnAction),
  ...WEAPON_MOTIONS,
];

/**
 * 주인공 애니 동작 → 겹칠 무기 시트 동작 후보 (앞이 우선, 마지막은 기존 attack 폴백).
 * attack · <무기>_combo<n> · <무기>_special · <무기>_aim 만 무기를 보인다. 그 외(idle·walk·dash·hurt·death·birth) 는 []
 */
export function overlayActionsFor(playerAction: string, weaponId: string): string[] {
  if (playerAction === 'attack') return ['attack'];
  const prefix = `${weaponId}_`;
  if (!playerAction.startsWith(prefix)) return [];
  const rest = playerAction.slice(prefix.length);
  if (/^combo\d+$/.test(rest)) return [rest, 'attack'];
  if (rest === 'special' || rest === 'aim') return [rest, 'attack'];
  // 49라운드: 내리찍기·대쉬 공격은 무기 시트가 없으면 3타·attack, 뽑기·넣기·장전은 그 시트만 (없으면 휴대 표시)
  if (rest === 'slam' || rest === 'dashslash') return [rest, weaponComboAction(COMBO_HITS), 'attack'];
  if (rest === 'draw' || rest === 'sheathe' || rest === 'reload') return [rest];
  return [];
}

/** 애니 키 `<이름>_<동작>_<방향>[@f<n>][#…]` 에서 동작·방향을 꺼낸다. 형식이 아니면 null */
export function parseAnimKey(key: string, name: string): { action: string; dir: Facing } | null {
  if (!key.startsWith(`${name}_`)) return null;
  const body = key
    .slice(name.length + 1)
    .split('#')[0]
    .split('@')[0];
  const i = body.lastIndexOf('_');
  if (i <= 0) return null;
  const dir = body.slice(i + 1) as Facing;
  if (!FACINGS.includes(dir)) return null;
  return { action: body.slice(0, i), dir };
}
/**
 * 이펙트 시트(`fx/<이름>.json`)는 파일 이름에 동작 접미가 없으므로 내부 동작 이름을 하나로 고정한다.
 * sheetId = `<이름>_fx`, 애니 키 = `<이름>_fx_<방향>` (directions 가 ["any"] 면 네 방향 모두 0행).
 */
export const FX_ACTION = 'fx';

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

/** 계약 §1 JSON 필드 (+ §3.1 보강 필드는 선택) */
export interface SheetJson {
  image: string;
  /**
   * 50라운드 계약 §9: 도트 배율. 새 2배 도트(32×48 캐릭터·32px 타일) = 1, 기존 도트 = 없음/2.
   * 시스템은 기존 도트를 2배로 그려 화면 크기를 맞춘다 (`artScale`)
   */
  pixelScale?: number;
  /** 50라운드 계약 §9: 높이가 있는 구조물·소품 — 피벗(바닥 접점)에서 이 높이(px, 시트 도트) 위로는 캐릭터를 가린다 */
  occludeAbove?: number;
  /** 50라운드 계약 §9: 광원 */
  light?: LightSpec;
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
  depth?: 'above' | 'below' | 'floor' | 'y' | Partial<Record<Facing, 'above' | 'below' | ('above' | 'below')[]>>;
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
  impactOffsetPx?: Partial<Record<Facing, { x: number; y: number }>>;
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
  /** 가드를 누르는 동안 반복할 열 */
  loopFrames?: number[];
  /** 활 조준: 진행도 프레임 목록 · 발사 프레임 */
  progressFrames?: number[];
  releaseFrame?: number;
  /** 시간 애니가 아닌 상태별 고정 프레임 (aim_line: charging 0 / complete 1) */
  stateFrames?: Record<string, number>;
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
   * 없으면 `fxImpactFrame` 규칙 (attack_frame2 시트는 f0 = 예비 → 1)
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
    const o: Partial<Record<Facing, { x: number; y: number }>> = {};
    for (const [d, v] of Object.entries(json.impactOffsetPx)) if (v) o[d as Facing] = { x: v.x * k, y: v.y * k };
    out.impactOffsetPx = o;
  }
  if (typeof json.impactDistancePx === 'number') out.impactDistancePx = json.impactDistancePx * k;
  if (json.light) out.light = { ...json.light, radius: json.light.radius * k, offsetY: px(json.light.offsetY) };
  if (typeof json.occludeAbove === 'number') out.occludeAbove = json.occludeAbove * k;
  return out;
}

/** 프레임별 시작 시각(ms) 누적. scale 은 재생 배속 (natural / fit) */
export function frameStarts(def: SheetJson, scale = 1): number[] {
  const d = frameDurations(def);
  const out: number[] = [];
  let acc = 0;
  for (const ms of d) {
    out.push(acc / scale);
    acc += ms;
  }
  return out;
}

/** 파생 애니 키: 특정 열만 반복 (`<애니>#p1-2`) */
export function phaseAnimKey(base: string, columns: readonly number[]): string {
  return `${base}#p${columns.join('-')}`;
}

export interface SheetDef extends SheetJson {
  category: SpriteCategory;
  name: string;
  /** 기준 텍스처 키 (`sheet_player_idle`) */
  textureKey: string;
  /** PNG URL */
  imageUrl: string;
}

export interface SheetRequest {
  category: SpriteCategory;
  name: string;
  action: string;
}

/** 로드 대상: 주인공 6동작, 이름 목록(적·보스 id)별 5동작, 무기 id 별 attack 오버레이, 이펙트 id 목록, 구조물 시트 id 목록 */
export function wantedSheets(
  enemyIds: readonly string[],
  bossIds: readonly string[],
  weaponIds: readonly string[] = [],
  fxIds: readonly string[] = [],
  structureIds: readonly string[] = [],
): SheetRequest[] {
  const out: SheetRequest[] = [];
  for (const action of PLAYER_ACTIONS) out.push({ category: 'player', name: 'player', action });
  // 48라운드 §6: 탄생 · 무기별 연격·특수·조준 (매니페스트에 없으면 로더가 건너뛴다)
  out.push({ category: 'player', name: 'player', action: BIRTH_ACTION });
  for (const id of weaponIds)
    for (const action of playerWeaponActions(id)) out.push({ category: 'player', name: 'player', action });
  for (const name of enemyIds) for (const action of MOB_ACTIONS) out.push({ category: 'enemies', name, action });
  for (const name of bossIds) for (const action of MOB_ACTIONS) out.push({ category: 'bosses', name, action });
  for (const name of weaponIds) for (const action of WEAPON_ACTIONS) out.push({ category: 'weapons', name, action });
  for (const name of weaponIds)
    for (const action of WEAPON_EXTRA_ACTIONS) out.push({ category: 'weapons', name, action });
  for (const name of fxIds) out.push({ category: 'fx', name, action: FX_ACTION });
  for (const name of structureIds) out.push({ category: 'structures', name, action: STRUCTURE_ACTION });
  return out;
}

/** 구조물 시트 내부 동작 이름 (파일 이름에 동작 접미가 없다 — 이펙트와 같은 방식). sheetId = `<id>_st` */
export const STRUCTURE_ACTION = 'st';

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

/** 이펙트 id 를 정하는 데 필요한 무기 데이터 최소 형태 (data/weapons.json). 2차 노드는 1차의 `next` */
export interface FxWeaponShape {
  kind: 'melee' | 'ranged';
  personality: { branches: { id: string; next?: { id: string }[] }[] };
  /** 49라운드: 과열 무기면 가열 단계별 연격 이펙트, 내리찍기가 있으면 내리찍기 이펙트 */
  resource?: { kind: string };
  slam?: unknown;
}

/** 49라운드 §7.2 과열 단계 수 (fx/<무기>_combo<n>_heat<k>, k = 1..3) */
export const HEAT_STAGES = 3;

/** 과열 단계별 연격 이펙트 `fx/<무기>_combo<n>_heat<k>` */
export function heatComboFxId(weaponId: string, n: number, k: number): string {
  return `${comboFxId(weaponId, n)}_heat${k}`;
}

/** 대검 내리찍기 이펙트 `fx/<무기>_slam` */
export function slamFxId(weaponId: string): string {
  return `${weaponId}_slam`;
}

/** 베기 이펙트 이름 `<무기id>_slash` */
export function slashFxId(weaponId: string): string {
  return `${weaponId}_slash`;
}

/** 화살 텍스처 이름 `<무기id>_arrow` / `<무기id>_arrow_aimed` */
export function arrowFxId(weaponId: string, aimed: boolean): string {
  return aimed ? `${weaponId}_arrow_aimed` : `${weaponId}_arrow`;
}

/**
 * 계약 §3·§3.1 이펙트 목록: 근접 무기는 `<id>_slash`, 원거리는 `<id>_arrow`·`<id>_arrow_aimed`,
 * 그리고 1차·2차 진화 노드 id 전부(35라운드 3단계: 2차 전용 시트). 데이터에서 유도하므로 무기·트리가 바뀌면 자동 반영.
 */
export function fxSheetIds(weapons: Record<string, FxWeaponShape>): string[] {
  const out = new Set<string>();
  for (const [id, w] of Object.entries(weapons)) {
    if (w.kind === 'melee') {
      out.add(slashFxId(id));
      // 48라운드 §6.1 연격 베기 이펙트
      for (let n = 1; n <= COMBO_HITS; n++) out.add(comboFxId(id, n));
      // 49라운드 §7.2: 단검 가열 단계 · 대검 내리찍기
      if (w.resource?.kind === 'heat')
        for (let n = 1; n <= COMBO_HITS; n++) for (let k = 1; k <= HEAT_STAGES; k++) out.add(heatComboFxId(id, n, k));
      if (w.slam) out.add(slamFxId(id));
    } else {
      out.add(arrowFxId(id, false));
      out.add(arrowFxId(id, true));
    }
    for (const b of w.personality.branches) {
      out.add(b.id);
      for (const n of b.next ?? []) out.add(n.id);
    }
  }
  return [...out];
}

/** 피격 이펙트 시트 (35라운드 1단계, 계약 §3 anchor hitbox_center): 타격 섬광(43라운드 hit_burst 대체 가능)·피 튀김·치명타 버스트·넉백 먼지·플레이어 피격 */
export const HIT_FX_IDS: readonly string[] = [
  'hit_spark',
  'hit_burst',
  'blood',
  'crit_burst',
  'knock_dust',
  'player_hit',
];
/** 적·보스 양상 시트 (35라운드 2단계): 예고 마커 3종(+43라운드 수렴 오라), 46라운드 보스 내리찍기 충격파, 적 탄, 보스 부채꼴 탄, 총구 화염 */
export const ENEMY_FX_IDS: readonly string[] = [
  'telegraph_line',
  'telegraph_circle',
  'telegraph_cone',
  'telegraph_aura',
  'boss_slam',
  'enemy_bullet',
  'boss_fan_shot',
  'muzzle_flash',
];
/** 보조 동작·대쉬 연출 시트 (35라운드 3단계, 계약 §3.2) + 2차 진화 부속(중시 적중) */
export const SECONDARY_FX_IDS: readonly string[] = [
  'parry_flash',
  'guard_wave',
  'shadowstep_ghost',
  'aim_charge',
  'aim_line',
  'dash_dust',
  'dash_trail',
  'heavyarrow_hit',
];

/** 47라운드 구조물 이펙트 (계약 art-assets §5): 1-1 불붙은 독주 웅덩이 루프. 48라운드 §6.3 탄생 흙 */
export const STRUCTURE_FX_IDS: readonly string[] = ['fire_pool', BIRTH_FX, 'soul_wisp'];

/** 무기 유도 이펙트 + 피격 이펙트 + 적 양상 이펙트 + 보조 연출 + 구조물 이펙트 (중복 제거) */
export function allFxSheetIds(weapons: Record<string, FxWeaponShape>): string[] {
  return [
    ...new Set([...fxSheetIds(weapons), ...HIT_FX_IDS, ...ENEMY_FX_IDS, ...SECONDARY_FX_IDS, ...STRUCTURE_FX_IDS]),
  ];
}

/** JSON `scale` 이 양수 숫자면 그 값, 아니면 1 ("allowed" 메모 등) */
export function sheetScale(def: Pick<SheetJson, 'scale'>): number {
  return typeof def.scale === 'number' && def.scale > 0 ? def.scale : 1;
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

/** 이 열 이후 spawn 시점에 맞출 프레임 키 (43라운드: 휘두름 시트 f0 = 40ms 예비 프레임) */
const LEAD_SPAWNS: readonly string[] = ['attack_frame2'];

/**
 * 타격 프레임 = spawn 시점에 보여야 하는 프레임 열. `impactFrame` 이 있으면 그것,
 * 없으면 `spawn: attack_frame2` 이고 2프레임 이상이면 1 (f0 예비, fx-design §4·결정 43 임시 5), 그 외 0
 */
export function fxImpactFrame(def: Pick<SheetJson, 'impactFrame' | 'spawn' | 'frames'>): number {
  if (typeof def.impactFrame === 'number') return Math.max(0, Math.min(def.frames - 1, Math.floor(def.impactFrame)));
  return def.spawn && LEAD_SPAWNS.includes(def.spawn) && def.frames >= 2 ? 1 : 0;
}

/**
 * 연타 판정 간격: `hitFrames` 의 각 프레임 시작 시각을 첫 타격 프레임 기준으로 뺀 값 (ms, 길이 = hits).
 * 시트·hitFrames 가 없거나 짧으면 null → 호출 쪽 기본 간격
 */
export function hitFrameOffsets(def: SheetJson | null | undefined, hits: number): number[] | null {
  const hf = def?.hitFrames;
  if (!def || !hf || hf.length < hits || hits < 1) return null;
  const starts = frameStarts(def);
  const at = (f: number) => starts[Math.max(0, Math.min(def.frames - 1, f))] ?? 0;
  const base = at(hf[0]);
  return hf.slice(0, hits).map((f) => Math.max(0, at(f) - base));
}

/** 진행도 주도 프레임: min(last, floor(progress × divisor)). 예고 원 = (6프레임, ÷6), 조준 차지 = (6프레임, ÷5) */
export function progressFrame(progress: number, frames: number, divisor = frames): number {
  const last = Math.max(0, frames - 1);
  return Math.max(0, Math.min(last, Math.floor(Math.max(0, progress) * divisor)));
}

/**
 * 49라운드 §7.1 무기 오버레이 깊이: JSON `depth` 가 문자열이면 그것, 방향별 값이 문자열이면 그것,
 * 방향별 배열이면 그 열(프레임) 값. 없으면 above (기존 §3.1 처리와 같음)
 */
export function overlayDepthAt(def: Pick<SheetJson, 'depth'>, dir: Facing, column: number): 'above' | 'below' {
  const d = def.depth;
  if (d === 'above' || d === 'below') return d;
  if (d && typeof d === 'object') {
    const v = d[dir];
    if (v === 'above' || v === 'below') return v;
    if (Array.isArray(v) && v.length > 0) {
      const c = v[Math.max(0, Math.min(v.length - 1, column))];
      if (c === 'above' || c === 'below') return c;
    }
  }
  return 'above';
}

/** 이펙트 JSON `depth` 문자열 (무기 오버레이의 방향별 표는 무시) */
export function fxDepthHint(def: Pick<SheetJson, 'depth'>): 'above' | 'below' | null {
  return def.depth === 'above' || def.depth === 'below' ? def.depth : null;
}

/** `sprites/<분류>/<이름>_<동작>.json` (매니페스트·URL 공통 상대 경로). 이펙트는 `sprites/fx/<이름>.json` */
export function sheetJsonPath(r: SheetRequest): string {
  if (r.category === 'fx' || r.category === 'structures') return `${ASSETS.SPRITES_DIR}/${r.category}/${r.name}.json`;
  return `${ASSETS.SPRITES_DIR}/${r.category}/${r.name}_${r.action}.json`;
}

/**
 * 50라운드: 새 2배 도트 시트 경로 `sprites/<분류>/v2/<파일>` (예: `sprites/player/v2/player_idle.json`,
 * `sprites/enemies/v2/charger_walk.json`). 매니페스트에 있으면 기존 경로보다 먼저 쓴다
 */
export function sheetJsonPathV2(r: SheetRequest): string {
  const base = sheetJsonPath(r);
  const i = base.lastIndexOf('/');
  return `${base.slice(0, i)}/${ASSETS.V2_DIR}${base.slice(i)}`;
}

export function sheetId(name: string, action: string): string {
  return `${name}_${action}`;
}

export function sheetTextureKey(name: string, action: string, suffix = ''): string {
  return `${TEXTURES.SHEET_PREFIX}${sheetId(name, action)}${suffix}`;
}

/** 계약 §1 애니메이션 키 `<이름>_<동작>_<방향>` (+ 층 변형 접미) */
export function animKey(name: string, action: string, dir: Facing, suffix = ''): string {
  return `${sheetId(name, action)}_${dir}${suffix}`;
}

/** 프레임별 길이(ms). frameDurationsMs 가 없거나 길이가 다르면 fps 균등 */
export function frameDurations(def: SheetJson): number[] {
  const d = def.frameDurationsMs;
  if (d && d.length === def.frames && d.every((v) => v > 0)) return d;
  const per = 1000 / Math.max(1, def.fps);
  return Array.from({ length: def.frames }, () => per);
}

export function animDurationMs(def: SheetJson): number {
  return frameDurations(def).reduce((a, b) => a + b, 0);
}

/** 방향 행 번호 (JSON directions 순서). 없으면 0 */
export function directionRow(def: SheetJson, dir: Facing): number {
  const i = def.directions.indexOf(dir);
  return i < 0 ? 0 : i;
}

/** 방향 행의 프레임 번호 목록: row * frames + column */
export function frameIndices(def: SheetJson, dir: Facing): number[] {
  const row = directionRow(def, dir);
  return Array.from({ length: def.frames }, (_, c) => row * def.frames + c);
}

/** 방향별 프레임 번호의 열 → 시트 프레임 번호. 다른 시트(무기 오버레이)가 같은 열을 같은 시각에 보일 때 */
export function frameAt(def: SheetJson, dir: Facing, column: number): number {
  const c = Math.max(0, Math.min(def.frames - 1, column));
  return directionRow(def, dir) * def.frames + c;
}

/** 지배 축으로 4방향 결정. 0 벡터면 fallback */
export function facingOf(dx: number, dy: number, fallback: Facing): Facing {
  if (dx === 0 && dy === 0) return fallback;
  if (Math.abs(dx) >= Math.abs(dy)) return dx > 0 ? 'right' : 'left';
  return dy > 0 ? 'down' : 'up';
}
