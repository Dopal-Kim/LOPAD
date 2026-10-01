/**
 * 스프라이트 시트 정의 (계약 contracts/art-assets.md §1). Phaser 의존 없음.
 * 로드 대상 목록·키 규칙·재생 시간 계산을 담당하고, 실제 로드·애니 등록은 systems/sprites.ts.
 */
import { ASSETS, TEXTURES } from '../core/Constants';

export type SpriteCategory = 'player' | 'enemies' | 'bosses';
export type Facing = 'down' | 'up' | 'left' | 'right';
export const FACINGS: readonly Facing[] = ['down', 'up', 'left', 'right'];

/** 계약 §1 동작 목록 */
export const PLAYER_ACTIONS = ['idle', 'walk', 'attack', 'dash', 'hurt', 'death'] as const;
export const MOB_ACTIONS = ['idle', 'walk', 'attack', 'hurt', 'death'] as const;

/** 계약 §1 JSON 필드 */
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

/** 로드 대상: 주인공 6동작, 이름 목록(적·보스 id)별 5동작 */
export function wantedSheets(enemyIds: readonly string[], bossIds: readonly string[]): SheetRequest[] {
  const out: SheetRequest[] = [];
  for (const action of PLAYER_ACTIONS) out.push({ category: 'player', name: 'player', action });
  for (const name of enemyIds) for (const action of MOB_ACTIONS) out.push({ category: 'enemies', name, action });
  for (const name of bossIds) for (const action of MOB_ACTIONS) out.push({ category: 'bosses', name, action });
  return out;
}

/** `sprites/<분류>/<이름>_<동작>.json` (매니페스트·URL 공통 상대 경로) */
export function sheetJsonPath(r: SheetRequest): string {
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

/** 지배 축으로 4방향 결정. 0 벡터면 fallback */
export function facingOf(dx: number, dy: number, fallback: Facing): Facing {
  if (dx === 0 && dy === 0) return fallback;
  if (Math.abs(dx) >= Math.abs(dy)) return dx > 0 ? 'right' : 'left';
  return dy > 0 ? 'down' : 'up';
}
