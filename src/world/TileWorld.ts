import Phaser from 'phaser';
import { DEPTH, TILE } from '../core/Constants';
import { Rng } from '../systems/rng';
import { TileId, cellKey, type Cell, type Door, type FloorLayout, type Room } from '../systems/mapgen';
import { CELL_H, CELL_W, type Rect } from '../systems/mapgen/types';
import { findSafeTile } from '../systems/traversal';
import { TileSkin, isOpenId, planProps, roomTypeMap } from './tileskin';

export type DoorState = 'open' | 'closed' | 'locked';

const SOLID: TileId[] = [TileId.Wall, TileId.DoorClosed, TileId.DoorLocked];

/**
 * 생성된 층을 Phaser 타일맵으로 올리고 문 상태·좌표 변환을 담당한다.
 * 타일 인덱스는 `TileSkin` 이 정한다 (아트 타일셋이면 변형·자동타일·소품, 아니면 TileId 그대로).
 */
export class TileWorld {
  readonly map: Phaser.Tilemaps.Tilemap;
  readonly layer: Phaser.Tilemaps.TilemapLayer;
  /** 소품 오버레이 (아트 타일셋에 props 가 있을 때만) */
  readonly propsLayer: Phaser.Tilemaps.TilemapLayer | null = null;
  private roomById: Map<string, Room>;
  private readonly solidPropIndices: number[];
  /** 47라운드: 단단한 구조물이 차지한 칸 (`"x,y"`) — 걸을 수 없는 칸으로 본다 (적 생성·워프 착지 회피) */
  private readonly blocked = new Set<string>();
  /** 48라운드 노드 전투장: 카메라 경계 (px). 숨은 저장고가 열리면 넓힌다 */
  private arenaCamera: Phaser.Geom.Rectangle | null = null;

  constructor(
    scene: Phaser.Scene,
    readonly layout: FloorLayout,
    readonly skin: TileSkin = TileSkin.placeholder(),
    /** 소품 배치 시드 (층 시드) */
    propSeed: number | string = layout.seed,
    /** 47라운드: 구조물이 먼저 차지한 칸 (소품 제외) */
    structureTiles: ReadonlySet<string> = new Set(),
  ) {
    const isOpen = (x: number, y: number) => isOpenId(layout.tiles[y]?.[x]);
    // 방 종류별 바닥(37라운드): 방 내부 바닥은 roomFloors[type], 복도·그 외는 tiles["1"]
    const roomTypes = skin.roomFloors.size > 0 ? roomTypeMap(layout) : null;
    const data = layout.tiles.map((row, y) =>
      row.map((id, x) => skin.indexFor(id, x, y, isOpen, roomTypes?.get(`${x},${y}`))),
    );
    this.map = scene.make.tilemap({ data, tileWidth: TILE, tileHeight: TILE });
    const tileset = this.map.addTilesetImage(skin.textureKey, skin.textureKey, TILE, TILE, 0, 0)!;
    this.layer = this.map.createLayer(0, tileset, 0, 0)!;
    this.layer.setDepth(DEPTH.TILES);
    this.layer.setCollision(skin.solidIndices);
    this.roomById = new Map(layout.rooms.map((r) => [r.id, r]));
    this.solidPropIndices = skin.solidPropIndices;
    const C = layout.arena?.camera;
    if (C) this.arenaCamera = new Phaser.Geom.Rectangle(C.x * TILE, C.y * TILE, C.w * TILE, C.h * TILE);

    if (skin.props.length > 0) {
      const props = this.map.createBlankLayer('props', tileset, 0, 0, layout.widthTiles, layout.heightTiles)!;
      props.setDepth(DEPTH.PROPS);
      for (const p of planProps(layout, skin.props, propSeed, undefined, structureTiles))
        props.putTileAt(p.index, p.x, p.y);
      if (this.solidPropIndices.length > 0) props.setCollision(this.solidPropIndices);
      this.propsLayer = props;
    }
  }

  /** 충돌시킬 레이어 목록 (바닥·벽 + 단단한 소품) */
  get collisionLayers(): Phaser.Tilemaps.TilemapLayer[] {
    return this.propsLayer ? [this.layer, this.propsLayer] : [this.layer];
  }

  get widthPx(): number {
    return this.layout.widthTiles * TILE;
  }

  get heightPx(): number {
    return this.layout.heightTiles * TILE;
  }

  room(id: string): Room {
    const r = this.roomById.get(id);
    if (!r) throw new Error(`[world] 방 없음: ${id}`);
    return r;
  }

  /** 타일 좌표의 게임 타일 ID (범위 밖은 void) */
  tileIdAt(tx: number, ty: number): TileId {
    const t = this.layer.getTileAt(tx, ty);
    return t ? this.skin.idOf(t.index) : TileId.Void;
  }

  /** 월드 좌표의 타일 ID */
  tileIdAtWorld(worldX: number, worldY: number): TileId {
    const t = this.layer.getTileAtWorldXY(worldX, worldY);
    return t ? this.skin.idOf(t.index) : TileId.Void;
  }

  /** 월드 좌표의 타일이 걸을 수 있는 바닥인지 (벽·닫힌 문·빈 공간·단단한 소품이면 false) */
  isWalkableAt(worldX: number, worldY: number): boolean {
    const t = this.layer.getTileAtWorldXY(worldX, worldY);
    if (!t) return false;
    if (!isOpenId(this.skin.idOf(t.index))) return false;
    if (this.propsLayer) {
      const p = this.propsLayer.getTileAtWorldXY(worldX, worldY);
      if (p && this.solidPropIndices.includes(p.index)) return false;
    }
    if (this.blocked.size > 0 && this.blocked.has(`${t.x},${t.y}`)) return false;
    return true;
  }

  /** 47라운드: 단단한 구조물 칸 표시 (on=false 면 해제 — 술통이 굴러가면) */
  setBlocked(tx: number, ty: number, on: boolean): void {
    if (on) this.blocked.add(`${tx},${ty}`);
    else this.blocked.delete(`${tx},${ty}`);
  }

  /**
   * 47라운드 1-6 숨은 벽: 벽선의 입구 칸과 저장고 바닥을 바닥으로, 둘레를 벽으로 바꾼다 (충돌 갱신 포함).
   * 저장고는 방 내부 밖이라 방 판정·적 생성에는 들어가지 않는다
   */
  carveCellar(
    inner: Rect,
    opening: readonly { x: number; y: number }[],
    ring: readonly { x: number; y: number }[],
  ): void {
    for (const r of ring) this.put(TileId.Wall, r.x, r.y);
    for (let y = inner.y; y < inner.y + inner.h; y++)
      for (let x = inner.x; x < inner.x + inner.w; x++) this.put(TileId.Floor, x, y);
    for (const o of opening) this.put(TileId.Floor, o.x, o.y);
  }

  cellAt(worldX: number, worldY: number): Cell {
    return { cx: Math.floor(worldX / (CELL_W * TILE)), cy: Math.floor(worldY / (CELL_H * TILE)) };
  }

  roomAtCell(cell: Cell): Room | undefined {
    const id = this.layout.cellRoom.get(cellKey(cell));
    return id ? this.roomById.get(id) : undefined;
  }

  /** 월드 좌표가 방 내부 바닥 안인지 */
  isInsideRoom(room: Room, worldX: number, worldY: number): boolean {
    const tx = Math.floor(worldX / TILE);
    const ty = Math.floor(worldY / TILE);
    const I = room.interior;
    return tx >= I.x && tx < I.x + I.w && ty >= I.y && ty < I.y + I.h;
  }

  roomCenter(room: Room): Phaser.Math.Vector2 {
    const I = room.interior;
    return new Phaser.Math.Vector2((I.x + I.w / 2) * TILE, (I.y + I.h / 2) * TILE);
  }

  /** 셀 하나의 픽셀 사각형 */
  cellRect(cell: Cell): Phaser.Geom.Rectangle {
    return new Phaser.Geom.Rectangle(cell.cx * CELL_W * TILE, cell.cy * CELL_H * TILE, CELL_W * TILE, CELL_H * TILE);
  }

  /**
   * 카메라 클램프 영역 (32라운드 카메라 추종):
   * - 방 내부에 있으면 그 방의 셀 사각형(보스 2×2 블록 포함)
   * - 복도·문 위(방 내부 밖)면 현재 셀 사각형 + 진행 방향의 이웃 셀 → 방을 나설 때 카메라가 옆 방으로 미끄러진다
   * 영역은 항상 월드 안으로 잘라낸다.
   */
  cameraRegion(worldX: number, worldY: number): Phaser.Geom.Rectangle {
    // 48라운드 노드 전투장: 방 내부 + 벽 (+ 열린 저장고)
    if (this.arenaCamera) return this.arenaCamera;
    const cell = this.cellAt(worldX, worldY);
    const room = this.roomAtCell(cell);
    const base = room ? this.roomCellsRect(room) : this.cellRect(cell);
    const world = new Phaser.Geom.Rectangle(0, 0, this.widthPx, this.heightPx);
    if (room && this.isInsideRoom(room, worldX, worldY)) return Phaser.Geom.Rectangle.Intersection(base, world);
    // 방 밖(복도): 방이면 내부 사각형 기준, 복도 셀이면 셀 중심 기준으로 어느 쪽으로 나가는지 정한다
    let dx = 0;
    let dy = 0;
    if (room) {
      const I = room.interior;
      if (worldX < I.x * TILE) dx = -1;
      else if (worldX >= (I.x + I.w) * TILE) dx = 1;
      else if (worldY < I.y * TILE) dy = -1;
      else dy = 1;
    } else {
      const c = this.cellRect(cell);
      const ox = worldX - c.centerX;
      const oy = worldY - c.centerY;
      if (Math.abs(ox) >= Math.abs(oy)) dx = Math.sign(ox) || 1;
      else dy = Math.sign(oy) || 1;
    }
    const neighbor = this.cellRect({ cx: cell.cx + dx, cy: cell.cy + dy });
    return Phaser.Geom.Rectangle.Intersection(Phaser.Geom.Rectangle.Union(base, neighbor), world);
  }

  /** 48라운드: 노드 전투장 카메라 경계에 타일 사각형을 더한다 (숨은 저장고). 방+복도 층이면 무시 */
  extendCamera(rect: Rect, padTiles = 1): void {
    if (!this.arenaCamera) return;
    const r = new Phaser.Geom.Rectangle(
      (rect.x - padTiles) * TILE,
      (rect.y - padTiles) * TILE,
      (rect.w + padTiles * 2) * TILE,
      (rect.h + padTiles * 2) * TILE,
    );
    this.arenaCamera = Phaser.Geom.Rectangle.Union(this.arenaCamera, r);
  }

  /** 노드 전투장 카메라 경계 (px, 없으면 null) */
  get arenaBounds(): Phaser.Geom.Rectangle | null {
    return this.arenaCamera;
  }

  /** 방 전체(2×2 보스 블록 포함)의 픽셀 사각형 — 카메라 경계용 */
  roomCellsRect(room: Room): Phaser.Geom.Rectangle {
    const xs = room.cells.map((c) => c.cx);
    const ys = room.cells.map((c) => c.cy);
    const x0 = Math.min(...xs) * CELL_W * TILE;
    const y0 = Math.min(...ys) * CELL_H * TILE;
    const x1 = (Math.max(...xs) + 1) * CELL_W * TILE;
    const y1 = (Math.max(...ys) + 1) * CELL_H * TILE;
    return new Phaser.Geom.Rectangle(x0, y0, x1 - x0, y1 - y0);
  }

  /**
   * 워프 착지점 (45라운드): 중앙에서 가장 가까운, 몸 반경 안이 모두 바닥이고 출구·상점 타일에서 hazardTiles 칸 이상 떨어진 타일 중심.
   * 못 찾으면 방 중앙
   */
  safePointInRoom(room: Room, bodyTiles: number, hazardTiles: number): Phaser.Math.Vector2 {
    const t = findSafeTile(
      room.interior,
      (tx, ty) => this.isWalkableAt(tx * TILE + TILE / 2, ty * TILE + TILE / 2),
      (tx, ty) => {
        const id = this.tileIdAt(tx, ty);
        return id === TileId.Exit || id === TileId.Shop;
      },
      bodyTiles,
      hazardTiles,
    );
    return t ? new Phaser.Math.Vector2(t.tx * TILE + TILE / 2, t.ty * TILE + TILE / 2) : this.roomCenter(room);
  }

  /** 방 내부의 무작위 바닥 지점(타일 중심). from 에서 minDistTiles 이상 떨어진 곳. 단단한 소품 위는 피한다 */
  randomPointInRoom(room: Room, rng: Rng, from?: { x: number; y: number }, minDistTiles = 0): Phaser.Math.Vector2 {
    const I = room.interior;
    let best = new Phaser.Math.Vector2((I.x + 1) * TILE + TILE / 2, (I.y + 1) * TILE + TILE / 2);
    for (let tries = 0; tries < 40; tries++) {
      const tx = rng.int(I.x + 1, I.x + I.w - 2);
      const ty = rng.int(I.y + 1, I.y + I.h - 2);
      const p = new Phaser.Math.Vector2(tx * TILE + TILE / 2, ty * TILE + TILE / 2);
      if (!this.isWalkableAt(p.x, p.y)) continue;
      if (!from || Phaser.Math.Distance.Between(p.x, p.y, from.x, from.y) >= minDistTiles * TILE) return p;
      best = p;
    }
    return best;
  }

  private put(id: TileId, tx: number, ty: number): Phaser.Tilemaps.Tile {
    const tile = this.layer.putTileAt(this.skin.indexFor(id, tx, ty), tx, ty);
    tile.setCollision(SOLID.includes(id));
    return tile;
  }

  setDoor(door: Door, state: DoorState): void {
    const id = state === 'open' ? TileId.DoorOpen : state === 'closed' ? TileId.DoorClosed : TileId.DoorLocked;
    for (const t of door.tiles) this.put(id, t.x, t.y);
  }

  /** 보스 방 중앙에 2×2 출구 타일을 놓는다 */
  placeExit(room: Room): { x: number; y: number } {
    const I = room.interior;
    const tx = I.x + Math.floor(I.w / 2) - 1;
    const ty = I.y + Math.floor(I.h / 2) - 1;
    for (let y = ty; y < ty + 2; y++) for (let x = tx; x < tx + 2; x++) this.put(TileId.Exit, x, y);
    return { x: (tx + 1) * TILE, y: (ty + 1) * TILE };
  }

  /** 출구 오른쪽에 2×2 상점 타일 */
  placeShop(room: Room): { x: number; y: number } {
    const I = room.interior;
    const tx = I.x + Math.floor(I.w / 2) + 3;
    const ty = I.y + Math.floor(I.h / 2) - 1;
    for (let y = ty; y < ty + 2; y++) for (let x = tx; x < tx + 2; x++) this.put(TileId.Shop, x, y);
    return { x: (tx + 1) * TILE, y: (ty + 1) * TILE };
  }

  /** 48라운드: 지정 타일(왼쪽 위)에 2×2 출구 · 상점. 중심 px 반환 */
  placeExitAt(tx: number, ty: number): { x: number; y: number } {
    for (let y = ty; y < ty + 2; y++) for (let x = tx; x < tx + 2; x++) this.put(TileId.Exit, x, y);
    return { x: (tx + 1) * TILE, y: (ty + 1) * TILE };
  }

  placeShopAt(tx: number, ty: number): { x: number; y: number } {
    for (let y = ty; y < ty + 2; y++) for (let x = tx; x < tx + 2; x++) this.put(TileId.Shop, x, y);
    return { x: (tx + 1) * TILE, y: (ty + 1) * TILE };
  }

  isShopAt(worldX: number, worldY: number): boolean {
    return this.tileIdAtWorld(worldX, worldY) === TileId.Shop;
  }

  isExitAt(worldX: number, worldY: number): boolean {
    return this.tileIdAtWorld(worldX, worldY) === TileId.Exit;
  }

  setRoomDoors(room: Room, state: DoorState): void {
    for (const d of room.doors) this.setDoor(d, state);
  }
}
