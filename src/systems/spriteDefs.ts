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
  /** §3.1 무기 오버레이 깊이: 방향별 above / below */
  depth?: Partial<Record<Facing, 'above' | 'below'>>;
  /** §3.1 재생 시점 메모 (코드가 읽지 않음) */
  spawn?: string;
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

/** 이펙트 id 를 정하는 데 필요한 무기 데이터 최소 형태 (data/weapons.json) */
export interface FxWeaponShape {
  kind: 'melee' | 'ranged';
  personality: { branches: { id: string }[] };
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
 * 그리고 1차 진화 노드 id 전부(2차는 부모 1차 이펙트를 재사용). 데이터에서 유도하므로 무기·트리가 바뀌면 자동 반영.
 */
export function fxSheetIds(weapons: Record<string, FxWeaponShape>): string[] {
  const out = new Set<string>();
  for (const [id, w] of Object.entries(weapons)) {
    if (w.kind === 'melee') out.add(slashFxId(id));
    else {
      out.add(arrowFxId(id, false));
      out.add(arrowFxId(id, true));
    }
    for (const b of w.personality.branches) out.add(b.id);
  }
  return [...out];
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
