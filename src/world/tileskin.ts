/**
 * 아트 타일셋 (계약 contracts/art-assets.md §2) → 게임 TileId 매핑. Phaser 의존 없음.
 * - tiles: TileId → 시트 인덱스 목록 (여러 개면 좌표 해시로 변형 선택)
 * - walls: 상/하/좌/우/모서리 자동타일 (있으면)
 * - props: 방 바닥 소품 (시드 결정적 배치)
 */
import { ASSETS, QUARTER, RENDER, TEXTURES, TILE } from '../core/Constants';
import type { LightSpec } from '../systems/sprites/spriteDefs';
import type { CanalJson, DecalJson } from './floorFeatures';

/** 방 종류 바닥 섞기 해시 소금 (변형 선택과 다른 해시) */
const ROOM_FLOOR_SALT = 977;
import { TileId, type FloorLayout, type Room } from '../systems/mapgen';
import type { RoomType } from '../systems/mapgen/types';
import { Rng, hashSeed } from '../systems/rng';

/** 52라운드 Q11 큰 소품 JSON (계약 §12, 시트 도트 px) */
export interface BigPropJson {
  name: string;
  rect: { x: number; y: number; w: number; h: number };
  pivot: { x: number; y: number };
  footprint?: [number, number];
  solid?: boolean;
  occludeAbove?: number;
  light?: LightSpec & { offset?: LightOffset };
  /** 53라운드 v3 소품 시트: 여러 광원 (연회 탁자 촛대 — 있으면 light 대신) */
  lights?: (LightSpec & { offset?: LightOffset })[];
  /** 계약 §14 배치 힌트 ('floor (벽 앞)' 등 — `bigPropRules`) */
  placement?: string;
  /** 계약 §14: 테두리 그림에 같은 물건이 있는 쪽 (north·south·west·east) — 그쪽 바닥 끝 3칸 회피 */
  avoidNearBorder?: string[];
}

export interface PropDef {
  index: number;
  name: string;
  solid: boolean;
  /** 50라운드 계약 §9: 광원 (반경·offset = 시트 도트 px, offset = 타일 칸 안 좌표) */
  light?: LightSpec & { offset?: LightOffset };
  /** 40라운드: 방당 최대 개수 (없으면 제한 없음) */
  maxPerRoom?: number;
  /** 40라운드: 배치 가중치 (기본 1, 0 이면 놓지 않음) */
  weight?: number;
  /**
   * 53라운드 v3 소품 시트(`tiles/v3/<지역>_props`): 시트 영역·피벗(도트) — 피벗을 놓일 칸의 논리 (16, 30) 자리에.
   * occludeAbove = 피벗 위 이 높이부터 Y 정렬(캐릭터를 가림), depth 'floor' = 바닥 데칼(Y 정렬 없음)
   */
  rect?: { x: number; y: number; w: number; h: number };
  pivot?: { x: number; y: number };
  footprint?: [number, number];
  occludeAbove?: number;
  depth?: string;
  lights?: (LightSpec & { offset?: LightOffset })[];
}

export const ROOM_TYPES: readonly RoomType[] = ['start', 'trial', 'rest', 'boss'];

export type WallKey = 'top' | 'bottom' | 'left' | 'right' | 'corner_tl' | 'corner_tr' | 'corner_bl' | 'corner_br';

/** 타일셋 소품의 아트 v2 추가 필드 (pivot·occludeAbove) */
interface BigPropExtra {
  pivot?: { x: number; y: number };
  occludeAbove?: number;
}

/** 계약 §2 JSON (아트가 추가한 보조 필드는 무시) */
export interface TilesetJson {
  image: string;
  tileWidth?: number;
  tileHeight?: number;
  tiles: Record<string, number[]>;
  /**
   * 자동타일 벽(기존) — 50라운드 쿼터뷰(wallHeightTiles 가 있을 때)는 의미가 다르다: front = 벽 앞면(아랫단, 배열이면
   * [아랫단, 윗단]), frontUpper = 앞면 윗단, top = 윗면(벽 꼭대기)
   */
  walls?: Partial<Record<WallKey | 'front' | 'frontUpper', number | number[]>>;
  /** 50라운드 계약 §9: 도트 배율 (새 2배 도트 = 1) */
  pixelScale?: number;
  /** 50라운드 계약 §9: 벽 앞면 높이(칸). 있으면 쿼터뷰 벽으로 그린다 */
  wallHeightTiles?: number;
  /** 50라운드: 앞면 윗단 인덱스 (walls.frontUpper 와 같은 뜻, 둘 중 하나) */
  wallFrontUpper?: number;
  /** 50라운드 아트 v2: 바닥 그늘 겹침 인덱스 (북쪽 벽 발치·서·동·모서리) */
  floorShadows?: { n?: number; w?: number; e?: number; nw?: number; ne?: number };
  /** 50라운드 아트 v2: 벽 앞면 타일의 광원 (창·문틈) — 키 = 시트 인덱스, 반경·offset = 시트 도트 px */
  tileLights?: Record<string, LightSpec & { offset?: LightOffset }>;
  /** 52라운드 Q11 계약 §12: 큰 소품 (rect 로 자르는 시트 영역 · 발자국 · 피벗 · 가림 · 광원) */
  bigProps?: BigPropJson[];
  /** 아트 메모: 인덱스 → 이름 (골목 입구 `void_gap` 찾기) */
  names?: Record<string, string>;
  /** 52라운드 계약 §12: 쿼터뷰 타일셋 표시 (wallHeightTiles 가 없으면 2칸) */
  quarter?: boolean;
  /** 시트 열 수 (아트 메모 columns) */
  columns?: number;
  /** 53라운드 v3 소품 시트: 인덱스 격자 칸 크기 (도트, tileWidth 대신) */
  cell?: number;
  /** 53라운드 4지역 바닥(art floors_v2): v3 소품 시트 상대 경로(시스템은 `tiles/v3/<이름>_props` 로 찾는다) · 데칼 · 양조 수로 */
  propsSheet?: string;
  decals?: DecalJson[];
  canal?: CanalJson;
  /** 52라운드 계약 §12: 바탕 판석에 방 종류 바닥(roomFloors.*)을 섞는 비율 0~1 (없으면 QUARTER.ROOM_FLOOR_MIX) */
  roomFloorMix?: number;
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

/** 걸을 수 있는 칸에 8방향으로 닿는 빈(void) 칸 — 들쭉날쭉한 전투장의 열린 틈 */
export function edgeVoidTiles(layout: FloorLayout): { x: number; y: number }[] {
  const out: { x: number; y: number }[] = [];
  for (let y = 0; y < layout.heightTiles; y++)
    for (let x = 0; x < layout.widthTiles; x++) {
      if (layout.tiles[y][x] !== TileId.Void) continue;
      let touch = false;
      for (let oy = -1; oy <= 1 && !touch; oy++)
        for (let ox = -1; ox <= 1 && !touch; ox++) touch = isOpenId(layout.tiles[y + oy]?.[x + ox]);
      if (touch) out.push({ x, y });
    }
  return out;
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
  /** 50라운드 쿼터뷰 벽 (wallHeightTiles 가 있는 타일셋만) */
  readonly quarter: QuarterWalls | null;

  constructor(
    /** 타일셋 텍스처 키 */
    readonly textureKey: string,
    readonly def: TilesetJson,
    /** 아트 타일셋인지 (false 면 플레이스홀더 항등 매핑) */
    readonly isArt: boolean,
  ) {
    for (const id of ALL_IDS) {
      // 53라운드 v3 소품 시트(`tiles/v3/<이름>_props`)는 tiles 가 없을 수 있다
      const list = def.tiles?.[String(id)];
      const idx = Array.isArray(list) && list.length > 0 ? list : [this.fallbackIndex(id)];
      this.variants.set(id, idx);
      for (const i of idx) if (!this.reverse.has(i)) this.reverse.set(i, id);
    }
    for (const v of Object.values(def.walls ?? {}))
      for (const i of Array.isArray(v) ? v : [v]) if (typeof i === 'number') this.reverse.set(i, TileId.Wall);
    this.quarter = quarterWallsOf(def);
    if (this.quarter)
      for (const i of [
        ...this.quarter.frontLower,
        ...this.quarter.frontUpper,
        this.quarter.top,
        this.quarter.topAboveFront,
        ...Object.values(this.quarter.edges),
        ...(this.quarter.stone
          ? [...this.quarter.stone.lower, ...this.quarter.stone.upper, this.quarter.stone.top]
          : []),
      ])
        this.reverse.set(i, TileId.Wall);
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
    const floor = this.def.tiles?.[String(TileId.Floor)];
    const voidIdx = this.def.tiles?.[String(TileId.Void)];
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
      // 50라운드 쿼터뷰(v2) 타일셋: 방 종류 바닥(배수구·금 같은 장식 포함)은 가끔만 — 바탕은 판석 tiles["1"] (아트 목업과 같게)
      const mix = this.quarter ? pickVariant(x, y, 1000, ROOM_FLOOR_SALT) < this.roomFloorMix * 1000 : true;
      if (rf && mix) return rf[pickVariant(x, y, rf.length, id)];
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

  /** 52라운드 계약 §12: 쿼터뷰 바닥에 방 종류 바닥을 섞는 비율 (JSON roomFloorMix, 없으면 기본값) */
  get roomFloorMix(): number {
    const m = this.def.roomFloorMix;
    return typeof m === 'number' && m >= 0 && m <= 1 ? m : QUARTER.ROOM_FLOOR_MIX;
  }

  /**
   * 52라운드 Q11: 배치할 큰 소품 — JSON bigProps 중 바닥에 서는 것(placement 'floor…', 발자국 있음) + 타일셋 소품 'brazier'(화로, 1칸).
   * 벽 윗단에 거는 것(빨래줄 등)은 아직 쓰지 않는다
   */
  get bigProps(): BigPropJson[] {
    const out = (this.def.bigProps ?? []).filter(
      (b) => b && b.rect && b.pivot && Array.isArray(b.footprint) && (b.placement ?? 'floor').startsWith('floor'),
    );
    const brazier = this.props.find((p) => p.name === 'brazier') as (PropDef & BigPropExtra) | undefined;
    if (brazier && !out.some((b) => b.name === 'brazier')) {
      const px = this.tilePx;
      const cols = this.def.columns ?? 8;
      out.push({
        name: 'brazier',
        // 53라운드 v3 소품 시트는 소품마다 rect 가 있다
        rect: brazier.rect ?? {
          x: (brazier.index % cols) * px,
          y: Math.floor(brazier.index / cols) * px,
          w: px,
          h: px,
        },
        // 피벗 기본 = 칸 아래 가운데, 바닥 위 2 논리 px (32칸 2도트 · 64칸 4도트)
        pivot: brazier.pivot ?? {
          x: px / 2,
          y: px - QUARTER.V3_PIVOT_LIFT_LOGICAL / RENDER.WORLD_TO_SCREEN / this.worldScale,
        },
        footprint: [1, 1],
        solid: true,
        occludeAbove: brazier.occludeAbove,
        light: brazier.light,
        lights: brazier.lights,
        placement: 'floor',
      });
    }
    return out;
  }

  /** 골목 입구(북쪽 벽 틈) 인덱스: 아트 이름 'void_gap' → 없으면 null (호출 쪽이 빈 칸으로) */
  get alleyIndex(): number | null {
    const n = this.def.names;
    if (!n) return null;
    const hit = Object.entries(n).find(([, v]) => v === 'void_gap');
    return hit ? Number(hit[0]) : null;
  }

  /** 시트 타일 한 칸 크기 (px). 50라운드 새 타일셋 = 32 */
  get tilePx(): number {
    if (this.def.tileWidth && this.def.tileWidth > 0) return this.def.tileWidth;
    return this.def.cell && this.def.cell > 0 ? this.def.cell : TILE;
  }

  /**
   * 시트 도트 → 월드 배율. JSON `pixelScale` 이 있으면 그것(계약 §11: v2 1 → 0.5, v3 0.5 → 0.25), 없으면 칸 크기로
   * (TILE / tilePx — 32px 타일셋 = 0.5, 기존 16px = 1)
   */
  get worldScale(): number {
    const ps = this.def.pixelScale;
    return typeof ps === 'number' && ps > 0 ? ps / RENDER.WORLD_TO_SCREEN : TILE / this.tilePx;
  }

  /** 시트 열 수 (JSON columns, 없으면 이미지 폭 ÷ 칸 — 호출 쪽이 텍스처 폭을 준다) */
  columnsOf(textureWidth: number): number {
    const c = this.def.columns;
    return typeof c === 'number' && c > 0 ? c : Math.max(1, Math.floor(textureWidth / this.tilePx));
  }

  /** 빈 칸(void) 인덱스 */
  get voidIndex(): number {
    return this.variants.get(TileId.Void)![0];
  }
}

/** 50라운드 쿼터뷰 벽 인덱스 (목록 안 중복 = 가중치, 좌표 해시로 고른다) */
export interface QuarterWalls {
  /** 벽 앞면 높이 (칸) */
  heightTiles: number;
  /** 앞면 아랫단 (바닥과 맞닿은 벽 칸) */
  frontLower: number[];
  /** 앞면 윗단 (아랫단 위 heightTiles-1 칸) */
  frontUpper: number[];
  /** 윗면 (기본) */
  top: number;
  /** 앞면 바로 위 칸 (처마). 없으면 top */
  topAboveFront: number;
  /** 앞면이 보이지 않는 경계 벽의 윗면 가장자리 (wallKind → 인덱스: 서쪽 경계 left · 동쪽 right · 남쪽 bottom · 모서리) */
  edges: Partial<Record<WallKey, number>>;
  /** 돌담 세트 (아트 walls.stoneSet — 구간 전체를 이 세트로): 경계에 닿지 않는 벽 섬(엄폐 담)에 쓴다. 없으면 null */
  stone: { lower: number[]; upper: number[]; top: number } | null;
  /** 바닥 그늘 겹침 (북쪽 벽 발치·서·동, 없으면 null) */
  shadows: { n?: number; w?: number; e?: number; nw?: number; ne?: number } | null;
}

/** 계약 art §9 인덱스 표 v3 의 벽 앞면 · 윗면 기본 자리 */
const V3_WALL_FRONT = 5;
const V3_WALL_TOP = 6;
/** 계약 §12: quarter: true 인데 wallHeightTiles 가 없을 때 */
const DEFAULT_WALL_HEIGHT = 2;

/** 광원 offset (계약 §12 정식 = [x, y] 도트, 아트 v2 초기 산출물은 { x, y }) */
export type LightOffset = [number, number] | { x: number; y: number };

/** offset → { x, y } (없으면 null) */
export function lightOffsetOf(o: LightOffset | undefined): { x: number; y: number } | null {
  if (!o) return null;
  if (Array.isArray(o)) return typeof o[0] === 'number' && typeof o[1] === 'number' ? { x: o[0], y: o[1] } : null;
  return typeof o.x === 'number' && typeof o.y === 'number' ? { x: o.x, y: o.y } : null;
}
const EDGE_KEYS: readonly WallKey[] = ['left', 'right', 'bottom', 'corner_tl', 'corner_tr', 'corner_bl', 'corner_br'];

/**
 * 쿼터뷰 벽 읽기 (계약 art §9 + 아트 JSON walls.stacking 규칙). wallHeightTiles 가 없으면 null (기존 평면 벽).
 * - 앞면: `walls.front` = 숫자 · 배열 [아랫단, 윗단] · 객체 { lower: [...], upper: [...] } (목록 중복 = 가중치).
 *   아랫단이 숫자 하나이고 tiles["2"] 첫 항목이면 tiles["2"] 목록을 변형으로. 윗단 = front.upper · walls.frontUpper ·
 *   wallFrontUpper · front 배열 둘째 · 없으면 아랫단
 * - 윗면 `walls.top`(기본 6) · 처마 `walls.topAboveFront` · 경계 가장자리 `walls.left/right/bottom/corner_*`
 * - 바닥 그늘 `floorShadows { n, w, e, nw, ne }`
 */
export function quarterWallsOf(def: TilesetJson): QuarterWalls | null {
  const h = def.wallHeightTiles ?? (def.quarter === true ? DEFAULT_WALL_HEIGHT : undefined);
  if (typeof h !== 'number' || !(h >= 1)) return null;
  const w = (def.walls ?? {}) as Record<string, unknown>;
  const num = (v: unknown): number | undefined => (typeof v === 'number' ? v : undefined);
  const list = (v: unknown): number[] =>
    Array.isArray(v) ? v.filter((x): x is number => typeof x === 'number') : typeof v === 'number' ? [v] : [];
  const fr = w.front;
  const frObj = fr && typeof fr === 'object' && !Array.isArray(fr) ? (fr as Record<string, unknown>) : null;
  const frArr = list(fr);
  let frontLower = frObj ? list(frObj.lower) : frArr.slice(0, 1);
  if (frontLower.length === 0) frontLower = [V3_WALL_FRONT];
  const wallList = def.tiles[String(TileId.Wall)] ?? [];
  if (frontLower.length === 1 && wallList.length > 1 && wallList[0] === frontLower[0]) frontLower = [...wallList];
  let frontUpper = frObj ? list(frObj.upper) : [];
  if (frontUpper.length === 0) frontUpper = list(w.frontUpper);
  if (frontUpper.length === 0) frontUpper = list(def.wallFrontUpper);
  if (frontUpper.length === 0 && frArr.length > 1) frontUpper = [frArr[1]];
  if (frontUpper.length === 0) frontUpper = [frontLower[0]];
  const top = num(w.top) ?? V3_WALL_TOP;
  const edges: Partial<Record<WallKey, number>> = {};
  for (const k of EDGE_KEYS) {
    const v = num(w[k]);
    if (v !== undefined) edges[k] = v;
  }
  const st = w.stoneSet && typeof w.stoneSet === 'object' ? (w.stoneSet as Record<string, unknown>) : null;
  const stoneLower = st ? list(st.lower) : [];
  const stone =
    st && stoneLower.length > 0
      ? {
          lower: stoneLower,
          upper: list(st.upper).length > 0 ? list(st.upper) : stoneLower,
          top: num(st.top) ?? top,
        }
      : null;
  const sh = def.floorShadows;
  const shadows = sh ? { n: num(sh.n), w: num(sh.w), e: num(sh.e), nw: num(sh.nw), ne: num(sh.ne) } : null;
  return {
    heightTiles: Math.max(1, Math.floor(h)),
    frontLower,
    frontUpper,
    top,
    topAboveFront: num(w.topAboveFront) ?? top,
    edges,
    stone,
    shadows,
  };
}

/** Preloader 가 채우는 층 → 타일셋 (없는 층은 플레이스홀더) */
export const tileSkins = new Map<number, TileSkin>();

/** 49라운드 art §7.3: Preloader 가 채우는 지역 타일셋 이름(`stage1_waste`) → 타일셋 */
export const regionSkins = new Map<string, TileSkin>();

/**
 * 53라운드 v3 바닥 소품: Preloader 가 채우는 지역 타일셋 이름 → 소품 시트 (`tiles/v3/stage1_outer_props.json`).
 * 있으면 그 지역의 큰 소품(bigProps)·작은 소품(props)을 바닥 타일셋 대신 이 시트에서 쓴다 (쿼터뷰 바닥일 때)
 */
export const propSkins = new Map<string, TileSkin>();

/** v3 소품 시트 이름 (`stage1_outer_props`) */
export function propSheetName(tileset: string): string {
  return `${tileset}${ASSETS.PROPS_SUFFIX}`;
}

/** v3 소품 시트 JSON 경로 (`tiles/v3/stage1_outer_props.json`) */
export function propSheetJsonPath(tileset: string): string {
  return `${ASSETS.TILES_DIR}/${ASSETS.V3_DIR}/${propSheetName(tileset)}.json`;
}

/** 지역 타일셋의 v3 소품 시트 (없으면 null) */
export function propSkinFor(tileset: string | null | undefined): TileSkin | null {
  return (tileset ? propSkins.get(tileset) : undefined) ?? null;
}

/** 지역 타일셋 텍스처 키 (`tiles_stage1_waste`) */
export function namedTilesetTextureKey(name: string): string {
  return `${TEXTURES.TILESET_PREFIX}${name}`;
}

/** 지역 타일셋 JSON 경로 (`tiles/stage1_waste.json`) */
export function namedTilesetJsonPath(name: string): string {
  return `${ASSETS.TILES_DIR}/${name}.json`;
}

/** 50라운드 새 2배 도트 지역 타일셋 경로 (`tiles/v2/stage1_outer.json`) — 있으면 기존보다 먼저 */
export function namedTilesetJsonPathV2(name: string): string {
  return `${ASSETS.TILES_DIR}/${ASSETS.V2_DIR}/${name}.json`;
}

/**
 * 노드 전투장 타일셋: 지역 타일셋(로드됐으면) → 층 타일셋 → 플레이스홀더.
 * 지역 타일셋은 인덱스 표 v3 그대로라(계약 §7.3) 같은 TileSkin 규칙으로 읽는다
 */
export function skinFor(floor: number, tileset?: string | null): TileSkin {
  return (tileset ? regionSkins.get(tileset) : undefined) ?? tileSkins.get(floor) ?? TileSkin.placeholder();
}

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
  /** 47라운드: 구조물이 먼저 차지한 칸 (`"x,y"`) — 소품을 놓지 않는다 */
  exclude: ReadonlySet<string> = new Set(),
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
      if (used.has(key) || blocked.has(key) || exclude.has(key)) continue;
      if (layout.tiles[y]?.[x] !== TileId.Floor) continue;
      // 벽가: 방 사각형 테두리 또는 (49라운드 들쭉날쭉한 가장자리·엄폐 담) 4방향 이웃에 바닥이 아닌 칸
      const onRing =
        x === I.x ||
        x === I.x + I.w - 1 ||
        y === I.y ||
        y === I.y + I.h - 1 ||
        [
          [1, 0],
          [-1, 0],
          [0, 1],
          [0, -1],
        ].some(([dx, dy]) => {
          const t = layout.tiles[y + dy]?.[x + dx];
          return t === TileId.Wall || t === TileId.Void;
        });
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
    const t = room.floor ?? room.type;
    for (let y = I.y; y < I.y + I.h; y++) for (let x = I.x; x < I.x + I.w; x++) m.set(`${x},${y}`, t);
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
