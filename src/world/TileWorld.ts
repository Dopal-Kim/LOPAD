import Phaser from 'phaser';
import { TEXTURES, TILE } from '../core/Constants';
import { Rng } from '../systems/rng';
import { TileId, cellKey, type Cell, type Door, type FloorLayout, type Room } from '../systems/mapgen';
import { CELL_H, CELL_W } from '../systems/mapgen/types';

export type DoorState = 'open' | 'closed' | 'locked';

const SOLID: TileId[] = [TileId.Wall, TileId.DoorClosed, TileId.DoorLocked];

/** 생성된 층을 Phaser 타일맵으로 올리고 문 상태·좌표 변환을 담당한다. */
export class TileWorld {
  readonly map: Phaser.Tilemaps.Tilemap;
  readonly layer: Phaser.Tilemaps.TilemapLayer;
  private roomById: Map<string, Room>;

  constructor(
    scene: Phaser.Scene,
    readonly layout: FloorLayout,
  ) {
    this.map = scene.make.tilemap({ data: layout.tiles as number[][], tileWidth: TILE, tileHeight: TILE });
    const tileset = this.map.addTilesetImage(TEXTURES.TILES, TEXTURES.TILES, TILE, TILE, 0, 0)!;
    this.layer = this.map.createLayer(0, tileset, 0, 0)!;
    this.layer.setCollision(SOLID);
    this.roomById = new Map(layout.rooms.map((r) => [r.id, r]));
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

  /** 방 내부의 무작위 바닥 지점(타일 중심). from 에서 minDistTiles 이상 떨어진 곳 */
  randomPointInRoom(room: Room, rng: Rng, from?: { x: number; y: number }, minDistTiles = 0): Phaser.Math.Vector2 {
    const I = room.interior;
    let best = new Phaser.Math.Vector2((I.x + 1) * TILE + TILE / 2, (I.y + 1) * TILE + TILE / 2);
    for (let tries = 0; tries < 40; tries++) {
      const tx = rng.int(I.x + 1, I.x + I.w - 2);
      const ty = rng.int(I.y + 1, I.y + I.h - 2);
      const p = new Phaser.Math.Vector2(tx * TILE + TILE / 2, ty * TILE + TILE / 2);
      if (!from || Phaser.Math.Distance.Between(p.x, p.y, from.x, from.y) >= minDistTiles * TILE) return p;
      best = p;
    }
    return best;
  }

  setDoor(door: Door, state: DoorState): void {
    const id = state === 'open' ? TileId.DoorOpen : state === 'closed' ? TileId.DoorClosed : TileId.DoorLocked;
    for (const t of door.tiles) {
      const tile = this.layer.putTileAt(id, t.x, t.y);
      tile.setCollision(SOLID.includes(id));
    }
  }

  /** 보스 방 중앙에 2×2 출구 타일을 놓는다 */
  placeExit(room: Room): { x: number; y: number } {
    const I = room.interior;
    const tx = I.x + Math.floor(I.w / 2) - 1;
    const ty = I.y + Math.floor(I.h / 2) - 1;
    for (let y = ty; y < ty + 2; y++)
      for (let x = tx; x < tx + 2; x++) this.layer.putTileAt(TileId.Exit, x, y).setCollision(false);
    return { x: (tx + 1) * TILE, y: (ty + 1) * TILE };
  }

  /** 출구 오른쪽에 2×2 상점 타일 */
  placeShop(room: Room): { x: number; y: number } {
    const I = room.interior;
    const tx = I.x + Math.floor(I.w / 2) + 3;
    const ty = I.y + Math.floor(I.h / 2) - 1;
    for (let y = ty; y < ty + 2; y++)
      for (let x = tx; x < tx + 2; x++) this.layer.putTileAt(TileId.Shop, x, y).setCollision(false);
    return { x: (tx + 1) * TILE, y: (ty + 1) * TILE };
  }

  isShopAt(worldX: number, worldY: number): boolean {
    return this.layer.getTileAtWorldXY(worldX, worldY)?.index === TileId.Shop;
  }

  isExitAt(worldX: number, worldY: number): boolean {
    const t = this.layer.getTileAtWorldXY(worldX, worldY);
    return t?.index === TileId.Exit;
  }

  setRoomDoors(room: Room, state: DoorState): void {
    for (const d of room.doors) this.setDoor(d, state);
  }
}
