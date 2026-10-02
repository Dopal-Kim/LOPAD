/**
 * 스프라이트 시트 정의 (계약 contracts/art-assets.md §1). Phaser 의존 없음.
 * 로드 대상 목록·키 규칙·재생 시간 계산을 담당하고, 실제 로드·애니 등록은 systems/sprites.ts.
 */
import { ASSETS, TEXTURES } from '../core/Constants';

export type SpriteCategory = 'player' | 'enemies' | 'bosses' | 'weapons' | 'fx';
export type Facing = 'down' | 'up' | 'left' | 'right';
export const FACINGS: readonly Facing[] = ['down', 'up', 'left', 'right'];

/** 계약 §1 동작 목록 */
export const PLAYER_ACTIONS = ['idle', 'walk', 'attack', 'dash', 'hurt', 'death'] as const;
export const MOB_ACTIONS = ['idle', 'walk', 'attack', 'hurt', 'death'] as const;
/** 계약 §3.1 손에 든 무기 오버레이 동작 */
export const WEAPON_ACTIONS = ['attack'] as const;
/**
 * 이펙트 시트(`fx/<이름>.json`)는 파일 이름에 동작 접미가 없으므로 내부 동작 이름을 하나로 고정한다.
 * sheetId = `<이름>_fx`, 애니 키 = `<이름>_fx_<방향>` (directions 가 ["any"] 면 네 방향 모두 0행).
 */
export const FX_ACTION = 'fx';

/** 계약 §3.1 이펙트 앵커 */
export type FxAnchor = 'player_pivot' | 'hitbox_center' | 'projectile' | 'ui';

/** 계약 §1 JSON 필드 (+ §3.1 보강 필드는 선택) */
export interface SheetJson {
  image: string;
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
  depth?: 'above' | 'below' | Partial<Record<Facing, 'above' | 'below'>>;
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

/** 로드 대상: 주인공 6동작, 이름 목록(적·보스 id)별 5동작, 무기 id 별 attack 오버레이, 이펙트 id 목록 */
export function wantedSheets(
  enemyIds: readonly string[],
  bossIds: readonly string[],
  weaponIds: readonly string[] = [],
  fxIds: readonly string[] = [],
): SheetRequest[] {
  const out: SheetRequest[] = [];
  for (const action of PLAYER_ACTIONS) out.push({ category: 'player', name: 'player', action });
  for (const name of enemyIds) for (const action of MOB_ACTIONS) out.push({ category: 'enemies', name, action });
  for (const name of bossIds) for (const action of MOB_ACTIONS) out.push({ category: 'bosses', name, action });
  for (const name of weaponIds) for (const action of WEAPON_ACTIONS) out.push({ category: 'weapons', name, action });
  for (const name of fxIds) out.push({ category: 'fx', name, action: FX_ACTION });
  return out;
}

/** 이펙트 id 를 정하는 데 필요한 무기 데이터 최소 형태 (data/weapons.json). 2차 노드는 1차의 `next` */
export interface FxWeaponShape {
  kind: 'melee' | 'ranged';
  personality: { branches: { id: string; next?: { id: string }[] }[] };
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
    if (w.kind === 'melee') out.add(slashFxId(id));
    else {
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

/** 무기 유도 이펙트 + 피격 이펙트 + 적 양상 이펙트 + 보조 연출 (중복 제거) */
export function allFxSheetIds(weapons: Record<string, FxWeaponShape>): string[] {
  return [...new Set([...fxSheetIds(weapons), ...HIT_FX_IDS, ...ENEMY_FX_IDS, ...SECONDARY_FX_IDS])];
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

/** 이펙트 JSON `depth` 문자열 (무기 오버레이의 방향별 표는 무시) */
export function fxDepthHint(def: Pick<SheetJson, 'depth'>): 'above' | 'below' | null {
  return def.depth === 'above' || def.depth === 'below' ? def.depth : null;
}

/** `sprites/<분류>/<이름>_<동작>.json` (매니페스트·URL 공통 상대 경로). 이펙트는 `sprites/fx/<이름>.json` */
export function sheetJsonPath(r: SheetRequest): string {
  if (r.category === 'fx') return `${ASSETS.SPRITES_DIR}/${r.category}/${r.name}.json`;
  return `${ASSETS.SPRITES_DIR}/${r.category}/${r.name}_${r.action}.json`;
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
