/**
 * 47라운드 상호작용 구조물 데이터 (data/structures.json) 타입·로더·검증. Phaser 의존 없음.
 * id = 계약 `UiStructureKind`, kind = 상호작용 방식. 수치·문구는 전부 임시값·자리표시 (초안 structures-draft.md).
 */
import structuresJson from '../../../data/structures.json';
import type { UiInteractBlockReason, UiStructureKind } from '../../contract/ui';
import type { RoomType } from '../mapgen/types';
import { routeSetPieceSprites } from './setpieceSprites';

/** 상호작용 방식: 타격형 · E형 · 통과형 · 자동 */
export type StructureMode = 'hit' | 'interact' | 'pass' | 'auto';
/** 예산 묶음: filler(짐·술통처럼 방마다 여럿, 예산 밖) · common(공통) · theme(층 테마) */
export type StructureGroup = 'filler' | 'common' | 'theme';
/** 배치 위치: 벽가 · 벽가 우선(wallBias) · 아무 데나 · 방 중앙 · 숨은 저장고 벽 */
export type StructurePlace = 'wall' | 'wallPrefer' | 'any' | 'center' | 'cellar';

export const STRUCTURE_KINDS: readonly UiStructureKind[] = [
  'crate',
  'chest',
  'grave',
  'campfire',
  'cask',
  'still',
  'ledger',
  'agingBarrel',
  'counter',
  'hiddenWall',
  'cardTable',
  'exchange',
  'dogRing',
  'stakeBell',
  'roulette',
  'pawn',
];

/** E형(안내·미니맵 점 대상) 종류 — 계약 §9.1 */
export const INTERACT_KINDS: readonly UiStructureKind[] = [
  'chest',
  'grave',
  'campfire',
  'ledger',
  'agingBarrel',
  'counter',
  'cardTable',
  'exchange',
  'dogRing',
  'pawn',
];

export interface StructureDef {
  id: UiStructureKind;
  /** 초안 번호 (C1, 1-1 …) */
  code: string;
  kind: StructureMode;
  group: StructureGroup;
  /** 'all' 또는 stage id 목록 */
  floors: 'all' | string[];
  /** 방 종류별 가중치 (없는 종류엔 두지 않음) */
  roomTypes: Partial<Record<RoomType, number>>;
  /** 이 층에 나올 확률 */
  chance: number;
  /** 층당 개수 [min, max] (filler 가 아니면 필수) */
  perFloor?: [number, number];
  /** 방 종류별 방당 개수 (filler) */
  perRoom?: Partial<Record<RoomType, [number, number]>>;
  maxPerRoom: number;
  /** 타일 수 [w, h] = 아트 footprint × spriteScale */
  size: [number, number];
  /** 시트 표시 정수 배율 (dog_ring·roulette `scale: allowed`) */
  spriteScale?: number;
  solid: boolean;
  place: StructurePlace;
  /** wallPrefer 일 때 벽가 확률 */
  wallBias?: number;
  /** 방 내부 최소 가로 (투견 링) */
  minRoomW?: number;
  /** 길게 누르기 ms (묘) */
  holdMs?: number;
  /** 'floor' = 바닥에 깔림, 그 외 Y 정렬 */
  depth?: 'floor' | 'y';
  /** 아트 시트 id (계약 art-assets §5). 층별이면 { stage1: …, default: … } */
  sprite: string | Record<string, string>;
  placeholder: { color: string; label: string };
  name: string;
  params: Record<string, unknown>;
  text: Record<string, string>;
}

export interface StructureRules {
  interactKey: string;
  interactRangePx: number;
  budget: {
    common: [number, number];
    theme: [number, number];
    countBy: 'kind' | 'instance';
    maxInteractPerRoom: number;
  };
  clear: {
    doorTiles: number;
    startTiles: number;
    gapTiles: number;
    boss: { left: number; right: number; up: number; down: number };
  };
  hitCooldownMs: number;
  placeTries: number;
}

export interface StructuresFile {
  rules: StructureRules;
  text: { reasons: Record<UiInteractBlockReason, string>; cancel: string; goldUnit: string };
  structures: StructureDef[];
}

function fail(msg: string): never {
  throw new Error(`[data] structures: ${msg}`);
}

function isPair(v: unknown): v is [number, number] {
  return Array.isArray(v) && v.length === 2 && v.every((n) => typeof n === 'number') && v[0] <= v[1];
}

const MODES: readonly StructureMode[] = ['hit', 'interact', 'pass', 'auto'];
const GROUPS: readonly StructureGroup[] = ['filler', 'common', 'theme'];
const PLACES: readonly StructurePlace[] = ['wall', 'wallPrefer', 'any', 'center', 'cellar'];
const REASONS: readonly UiInteractBlockReason[] = [
  'combat',
  'busy',
  'gold',
  'hp',
  'potion',
  'notReady',
  'full',
  'limit',
];

export function validateStructures(f: StructuresFile): StructuresFile {
  const R = f.rules;
  if (!R) fail('rules 없음');
  if (typeof R.interactKey !== 'string' || !R.interactKey) fail('rules.interactKey 없음');
  if (!(R.interactRangePx > 0)) fail('rules.interactRangePx 는 양수');
  if (!isPair(R.budget?.common) || !isPair(R.budget?.theme)) fail('rules.budget.common/theme 는 [min, max]');
  if (R.budget.countBy !== 'kind' && R.budget.countBy !== 'instance') fail('rules.budget.countBy 는 kind|instance');
  if (!(R.budget.maxInteractPerRoom >= 1)) fail('rules.budget.maxInteractPerRoom 는 1 이상');
  for (const k of ['doorTiles', 'startTiles', 'gapTiles'] as const)
    if (typeof R.clear?.[k] !== 'number') fail(`rules.clear.${k} 는 숫자`);
  for (const r of REASONS) if (typeof f.text?.reasons?.[r] !== 'string') fail(`text.reasons.${r} 없음`);
  const ids = new Set<string>();
  for (const s of f.structures) {
    const p = `structures.${s.id}`;
    if (!STRUCTURE_KINDS.includes(s.id)) fail(`${p}: 계약에 없는 id`);
    if (ids.has(s.id)) fail(`${p}: 중복 id`);
    ids.add(s.id);
    if (!MODES.includes(s.kind)) fail(`${p}.kind 알 수 없음: ${s.kind}`);
    if (!GROUPS.includes(s.group)) fail(`${p}.group 알 수 없음: ${s.group}`);
    if (!PLACES.includes(s.place)) fail(`${p}.place 알 수 없음: ${s.place}`);
    if (s.floors !== 'all' && !(Array.isArray(s.floors) && s.floors.length > 0)) fail(`${p}.floors 는 'all' 또는 목록`);
    if (!s.roomTypes || Object.keys(s.roomTypes).length === 0) fail(`${p}.roomTypes 비어 있음`);
    if (!(s.chance >= 0 && s.chance <= 1)) fail(`${p}.chance 는 0..1`);
    if (s.group === 'filler') {
      if (!s.perRoom) fail(`${p}.perRoom 없음 (filler)`);
      for (const [t, v] of Object.entries(s.perRoom)) if (!isPair(v)) fail(`${p}.perRoom.${t} 는 [min, max]`);
    } else if (!isPair(s.perFloor)) fail(`${p}.perFloor 는 [min, max]`);
    if (!(s.maxPerRoom >= 1)) fail(`${p}.maxPerRoom 는 1 이상`);
    if (!Array.isArray(s.size) || s.size.length !== 2 || !s.size.every((n) => Number.isInteger(n) && n >= 1))
      fail(`${p}.size 는 [w, h] (1 이상 정수)`);
    if (typeof s.solid !== 'boolean') fail(`${p}.solid 는 boolean`);
    if (typeof s.sprite === 'string') {
      if (!s.sprite) fail(`${p}.sprite 비어 있음`);
    } else if (!s.sprite || typeof s.sprite.default !== 'string')
      fail(`${p}.sprite 는 문자열 또는 { default, stageN }`);
    if (!/^#[0-9a-fA-F]{6}$/.test(s.placeholder?.color ?? '')) fail(`${p}.placeholder.color 형식`);
    if (typeof s.name !== 'string' || !s.name) fail(`${p}.name 없음`);
    if (!s.params || typeof s.params !== 'object') fail(`${p}.params 없음`);
    if (!s.text || typeof s.text !== 'object') fail(`${p}.text 없음`);
    if (s.kind === 'interact' && !INTERACT_KINDS.includes(s.id)) fail(`${p}: interact 인데 계약 E형 목록에 없음`);
    if (s.holdMs !== undefined && !(s.holdMs > 0)) fail(`${p}.holdMs 는 양수`);
    if (s.spriteScale !== undefined && !(Number.isInteger(s.spriteScale) && s.spriteScale >= 1))
      fail(`${p}.spriteScale 는 1 이상 정수`);
  }
  for (const k of STRUCTURE_KINDS) if (!ids.has(k)) fail(`${k} 정의 없음`);
  return f;
}

export const STRUCTURES_FILE: StructuresFile = validateStructures(structuresJson as unknown as StructuresFile);
export const STRUCTURE_RULES: StructureRules = STRUCTURES_FILE.rules;
export const STRUCTURE_TEXT = STRUCTURES_FILE.text;
export const STRUCTURE_DEFS: ReadonlyMap<UiStructureKind, StructureDef> = new Map(
  STRUCTURES_FILE.structures.map((s) => [s.id, s]),
);

export function structureDef(kind: UiStructureKind): StructureDef {
  const d = STRUCTURE_DEFS.get(kind);
  if (!d) throw new Error(`[structures] 정의 없음: ${kind}`);
  return d;
}

/** 이 층(stage id)에 나올 수 있는 정의인지 */
export function availableOn(def: Pick<StructureDef, 'floors'>, stageId: string): boolean {
  return def.floors === 'all' || def.floors.includes(stageId);
}

/** 이 층에서 쓸 아트 시트 id (층별 표 → default) */
export function spriteFor(def: Pick<StructureDef, 'sprite'>, stageId: string): string {
  if (typeof def.sprite === 'string') return def.sprite;
  return def.sprite[stageId] ?? def.sprite.default;
}

/** 모든 시트 id (Preloader 로드 대상). 49라운드: 기본값으로 세트 배치 소품·전장 소품 시트도 (매니페스트에 없으면 로더가 건너뜀) */
export function allStructureSprites(
  defs: Iterable<StructureDef> = STRUCTURE_DEFS.values(),
  extra: readonly string[] = routeSetPieceSprites(),
): string[] {
  const out = new Set<string>(extra);
  for (const d of defs) {
    if (typeof d.sprite === 'string') out.add(d.sprite);
    else for (const v of Object.values(d.sprite)) out.add(v);
  }
  return [...out].sort();
}

/** 숫자 파라미터 (없으면 예외 — 데이터 오타를 빨리 드러낸다) */
export function num(def: StructureDef, key: string): number {
  const v = def.params[key];
  if (typeof v !== 'number') throw new Error(`[structures] ${def.id}.params.${key} 는 숫자여야 합니다`);
  return v;
}

/** 텍스트 (자리표시). `{key}` 치환 */
export function txt(def: StructureDef, key: string, vars: Record<string, string | number> = {}): string {
  const t = def.text[key] ?? '';
  return t.replace(/\{(\w+)\}/g, (_m, k: string) => (k in vars ? String(vars[k]) : `{${k}}`));
}
