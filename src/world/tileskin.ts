/**
 * 아트 타일셋 (계약 contracts/art-assets.md §2) → 게임 TileId 매핑. Phaser 의존 없음.
 * - tiles: TileId → 시트 인덱스 목록 (여러 개면 좌표 해시로 변형 선택)
 * - walls: 상/하/좌/우/모서리 자동타일 (있으면)
 * - props: 방 바닥 소품 (시드 결정적 배치)
 */
import { ASSETS, TEXTURES } from '../core/Constants';
import { TileId, type FloorLayout, type Room } from '../systems/mapgen';
import type { RoomType } from '../systems/mapgen/types';
import { Rng, hashSeed } from '../systems/rng';

export interface PropDef {
  index: number;
  name: string;
  solid: boolean;
  /** 40라운드: 방당 최대 개수 (없으면 제한 없음) */
  maxPerRoom?: number;
  /** 40라운드: 배치 가중치 (기본 1, 0 이면 놓지 않음) */
  weight?: number;
}

export const ROOM_TYPES: readonly RoomType[] = ['start', 'trial', 'rest', 'boss'];

export type WallKey = 'top' | 'bottom' | 'left' | 'right' | 'corner_tl' | 'corner_tr' | 'corner_bl' | 'corner_br';

/** 계약 §2 JSON (아트가 추가한 보조 필드는 무시) */
export interface TilesetJson {
  image: string;
  tileWidth?: number;
  tileHeight?: number;
  tiles: Record<string, number[]>;
  walls?: Partial<Record<WallKey, number>>;
  props?: PropDef[];
  /** 37라운드: 방 종류별 바닥 인덱스 목록. 키가 없거나 비면 tiles["1"] */
  roomFloors?: Partial<Record<RoomType, number[]>>;
}

export interface PropPlacement {
  x: number;
  y: number;
  index: number;
  solid: boolean;
}

/** 소품 배치 규칙 (29라운드 임시값 → 32라운드 방 확대에 맞춰 방당 개수·시도 횟수 상향) */
export const PROPS_RULES = {
  MIN_PER_ROOM: 6,
  MAX_PER_ROOM: 14,
  /** 시작 지점(방 중심) 반경 — 체비셰프 거리(타일) */
  START_CLEAR: 3,
  /** 문 타일 주변 반경 */
  DOOR_CLEAR: 2,
  /** 보스 방 중심 기준 출구(2×2, 중심-1..0)·상점(중심+3..+4) 자리 여유 */
  BOSS_CLEAR: { left: 2, right: 5, up: 2, down: 2 },
  /** 배치 시도 횟수 상한 */
  TRIES: 160,
};

const ALL_IDS: TileId[] = [
  TileId.Void,
  TileId.Floor,
  TileId.Wall,
  TileId.DoorOpen,
  TileId.DoorClosed,
  TileId.DoorLocked,
  TileId.Corridor,
  TileId.Exit,
  TileId.Shop,
];

export const SOLID_IDS: TileId[] = [TileId.Wall, TileId.DoorClosed, TileId.DoorLocked];

/** 걸을 수 있는(열린) 타일인지 */
export function isOpenId(id: TileId | undefined): boolean {
  return id !== undefined && id !== TileId.Void && !SOLID_IDS.includes(id);
}

/** 좌표 해시 → [0, n) */
export function pickVariant(x: number, y: number, n: number, salt = 0): number {
  if (n <= 1) return 0;
  let h = (x * 73856093) ^ (y * 19349663) ^ (salt * 83492791);
  h = Math.imul(h ^ (h >>> 13), 0x5bd1e995);
  h ^= h >>> 15;
  return (h >>> 0) % n;
}

/**
 * 벽 타일의 종류. 아래가 열려 있으면 top(정면이 보이는 북쪽 벽), 위가 열려 있으면 bottom,
 * 좌우, 그 다음 대각선으로 모서리. 아무것도 아니면 null (단일 벽).
 */
export function wallKind(isOpen: (x: number, y: number) => boolean, x: number, y: number): WallKey | null {
  if (isOpen(x, y + 1)) return 'top';
  if (isOpen(x, y - 1)) return 'bottom';
  if (isOpen(x + 1, y)) return 'left';
  if (isOpen(x - 1, y)) return 'right';
  if (isOpen(x + 1, y + 1)) return 'corner_tl';
  if (isOpen(x - 1, y + 1)) return 'corner_tr';
  if (isOpen(x + 1, y - 1)) return 'corner_bl';
  if (isOpen(x - 1, y - 1)) return 'corner_br';
  return null;
}

export class TileSkin {
  private readonly variants = new Map<TileId, number[]>();
  private readonly reverse = new Map<number, TileId>();
  /** 방 종류별 바닥 변형 (비어 있지 않은 것만) */
  readonly roomFloors = new Map<RoomType, number[]>();
  readonly solidIndices: number[];
  readonly props: PropDef[];

  constructor(
    /** 타일셋 텍스처 키 */
    readonly textureKey: string,
    readonly def: TilesetJson,
    /** 아트 타일셋인지 (false 면 플레이스홀더 항등 매핑) */
    readonly isArt: boolean,
  ) {
    for (const id of ALL_IDS) {
      const list = def.tiles[String(id)];
      const idx = Array.isArray(list) && list.length > 0 ? list : [this.fallbackIndex(id)];
      this.variants.set(id, idx);
      for (const i of idx) if (!this.reverse.has(i)) this.reverse.set(i, id);
    }
    for (const i of Object.values(def.walls ?? {})) if (typeof i === 'number') this.reverse.set(i, TileId.Wall);
    for (const type of ROOM_TYPES) {
      const list = def.roomFloors?.[type];
      if (!Array.isArray(list) || list.length === 0) continue;
      const idx = list.filter((i) => typeof i === 'number');
      if (idx.length === 0) continue;
      this.roomFloors.set(type, idx);
      for (const i of idx) if (!this.reverse.has(i)) this.reverse.set(i, TileId.Floor);
    }
    this.solidIndices = [...this.reverse.entries()].filter(([, id]) => SOLID_IDS.includes(id)).map(([i]) => i);
    this.props = (def.props ?? []).filter((p) => typeof p.index === 'number');
  }

  /** 플레이스홀더: 인덱스 = TileId */
  static placeholder(): TileSkin {
    const tiles: Record<string, number[]> = {};
    for (const id of ALL_IDS) tiles[String(id)] = [id];
    return new TileSkin(TEXTURES.TILES, { image: '', tiles }, false);
  }

  /** 아트 타일셋이 어떤 ID 를 빠뜨렸을 때 쓸 인덱스: 바닥 → 그 외는 void 자리 */
  private fallbackIndex(id: TileId): number {
    const floor = this.def.tiles[String(TileId.Floor)];
    const voidIdx = this.def.tiles[String(TileId.Void)];
    if (id === TileId.Corridor && floor?.length) return floor[0];
    if (voidIdx?.length) return voidIdx[0];
    return floor?.[0] ?? 0;
  }

  /**
   * 좌표에 놓을 시트 인덱스. 벽은 이웃(isOpen)으로 자동타일 — 자동타일 인덱스가 `tiles["2"]` 목록의 첫 항목이면
   * (정면 벽) 그 목록을 좌표 해시로 섞는다(37라운드 벽 변형 19·20). 바닥은 `roomType` 이 있고 `roomFloors` 에
   * 그 종류가 있으면 그 목록에서 고른다(37라운드 방 종류별 바닥), 아니면 `tiles["1"]`
   */
  indexFor(id: TileId, x: number, y: number, isOpen?: (x: number, y: number) => boolean, roomType?: RoomType): number {
    if (id === TileId.Wall && this.def.walls && isOpen) {
      const kind = wallKind(isOpen, x, y);
      const w = kind ? this.def.walls[kind] : undefined;
      if (typeof w === 'number') {
        const wallList = this.variants.get(TileId.Wall)!;
        if (wallList.length > 1 && wallList[0] === w) return wallList[pickVariant(x, y, wallList.length, id)];
        return w;
      }
    }
    if (id === TileId.Floor && roomType) {
      const rf = this.roomFloors.get(roomType);
      if (rf) return rf[pickVariant(x, y, rf.length, id)];
    }
    const list = this.variants.get(id)!;
    return list[pickVariant(x, y, list.length, id)];
  }

  /** 시트 인덱스 → 게임 타일 ID (모르는 인덱스는 void) */
  idOf(index: number): TileId {
    return this.reverse.get(index) ?? TileId.Void;
  }

  get solidPropIndices(): number[] {
    return this.props.filter((p) => p.solid).map((p) => p.index);
  }

  get stageTextureKey(): string {
    return this.textureKey;
  }
}

/** Preloader 가 채우는 층 → 타일셋 (없는 층은 플레이스홀더) */
export const tileSkins = new Map<number, TileSkin>();

export function tilesetTextureKey(floor: number): string {
  return `${TEXTURES.TILESET_PREFIX}${ASSETS.STAGE_PREFIX}${floor}`;
}

export function tilesetJsonPath(floor: number): string {
  return `${ASSETS.TILES_DIR}/${ASSETS.STAGE_PREFIX}${floor}.json`;
}

/**
 * 방마다 소품을 시드 결정적으로 배치한다. 문·출구·상점·시작 지점 주변은 비운다.
 * 단단한 소품은 벽에 붙은 안쪽 테두리에만 두어 전투 공간을 막지 않는다.
 */
export function planProps(
  layout: FloorLayout,
  props: PropDef[],
  seed: number | string,
  rules = PROPS_RULES,
): PropPlacement[] {
  if (props.length === 0) return [];
  const out: PropPlacement[] = [];
  const weighted = props.filter((p) => (p.weight ?? 1) > 0);
  if (weighted.length === 0) return out;
  for (const room of layout.rooms) {
    const rng = new Rng(hashSeed(`${String(seed)}:props:${room.id}`));
    const blocked = blockedTiles(room, rules);
    const I = room.interior;
    const want = rng.int(rules.MIN_PER_ROOM, rules.MAX_PER_ROOM);
    const used = new Set<string>();
    const perProp = new Map<number, number>();
    let placed = 0;
    for (let t = 0; t < rules.TRIES && placed < want; t++) {
      // 40라운드: 방당 상한에 닿은 소품은 후보에서 빼고, 가중치로 고른다
      const candidates = weighted.filter((p) => (perProp.get(p.index) ?? 0) < (p.maxPerRoom ?? Infinity));
      if (candidates.length === 0) break;
      const prop = pickWeighted(rng, candidates);
      const x = rng.int(I.x, I.x + I.w - 1);
      const y = rng.int(I.y, I.y + I.h - 1);
      const key = `${x},${y}`;
      if (used.has(key) || blocked.has(key)) continue;
      if (layout.tiles[y]?.[x] !== TileId.Floor) continue;
      const onRing = x === I.x || x === I.x + I.w - 1 || y === I.y || y === I.y + I.h - 1;
      if (prop.solid && !onRing) continue;
      used.add(key);
      perProp.set(prop.index, (perProp.get(prop.index) ?? 0) + 1);
      out.push({ x, y, index: prop.index, solid: prop.solid });
      placed++;
    }
  }
  return out;
}

/** 가중치(기본 1) 비례 선택 */
export function pickWeighted(rng: Rng, props: readonly PropDef[]): PropDef {
  const total = props.reduce((a, p) => a + (p.weight ?? 1), 0);
  let r = rng.next() * total;
  for (const p of props) {
    r -= p.weight ?? 1;
    if (r < 0) return p;
  }
  return props[props.length - 1];
}

/** 타일 좌표 → 그 타일이 속한 방의 종류 (방 내부 바닥만, 복도·벽은 undefined) */
export function roomTypeMap(layout: FloorLayout): Map<string, RoomType> {
  const m = new Map<string, RoomType>();
  for (const room of layout.rooms) {
    const I = room.interior;
    for (let y = I.y; y < I.y + I.h; y++) for (let x = I.x; x < I.x + I.w; x++) m.set(`${x},${y}`, room.type);
  }
  return m;
}

function blockedTiles(room: Room, rules: typeof PROPS_RULES): Set<string> {
  const b = new Set<string>();
  const mark = (x0: number, y0: number, x1: number, y1: number) => {
    for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) b.add(`${x},${y}`);
  };
  const I = room.interior;
  const cx = I.x + Math.floor(I.w / 2);
  const cy = I.y + Math.floor(I.h / 2);
  if (room.type === 'start')
    mark(cx - rules.START_CLEAR, cy - rules.START_CLEAR, cx + rules.START_CLEAR, cy + rules.START_CLEAR);
  if (room.type === 'boss') {
    const B = rules.BOSS_CLEAR;
    mark(cx - B.left, cy - B.up, cx + B.right, cy + B.down);
  }
  for (const d of room.doors)
    for (const t of d.tiles)
      mark(t.x - rules.DOOR_CLEAR, t.y - rules.DOOR_CLEAR, t.x + rules.DOOR_CLEAR, t.y + rules.DOOR_CLEAR);
  return b;
}
