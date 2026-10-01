/** 맵 생성기의 순수 데이터 타입. Phaser 의존 없음. */

export type RoomType = 'start' | 'trial' | 'rest' | 'boss';
export type Dir = 'N' | 'S' | 'E' | 'W';

export const DIRS: Dir[] = ['N', 'S', 'E', 'W'];
export const DIR_VEC: Record<Dir, [number, number]> = { N: [0, -1], S: [0, 1], E: [1, 0], W: [-1, 0] };
export const DIR_OPP: Record<Dir, Dir> = { N: 'S', S: 'N', E: 'W', W: 'E' };

/** 셀 하나 = 화면 하나 (타일 단위) */
export const CELL_W = 40;
export const CELL_H = 22;

export interface Cell {
  cx: number;
  cy: number;
}

export interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface Room {
  id: string;
  type: RoomType;
  /** 차지하는 셀들 (보스는 2×2) */
  cells: Cell[];
  /** 내부 바닥 사각형 (타일 좌표) */
  interior: Rect;
  /** 방향별 문 타일 (방 벽선 위의 corridorWidth 개 타일) */
  doors: Door[];
}

export interface Door {
  roomId: string;
  dir: Dir;
  tiles: { x: number; y: number }[];
  /** 이 문 너머가 보스 방이면 true (잠금 문) */
  toBoss: boolean;
}

export interface Hallway {
  cell: Cell;
  dirs: Dir[];
}

export interface Connection {
  a: Cell;
  b: Cell;
}

export const enum TileId {
  Void = 0,
  Floor = 1,
  Wall = 2,
  DoorOpen = 3,
  DoorClosed = 4,
  DoorLocked = 5,
  Corridor = 6,
  /** 보스 처치 후 생기는 다음 층 출구 (런타임에만 놓임) */
  Exit = 7,
}

export interface FloorLayout {
  seed: number;
  gridW: number;
  gridH: number;
  rooms: Room[];
  hallways: Hallway[];
  connections: Connection[];
  /** tiles[y][x] */
  tiles: TileId[][];
  widthTiles: number;
  heightTiles: number;
  /** 셀 → 방 id (복도 셀은 없음) */
  cellRoom: Map<string, string>;
}

export function cellKey(c: Cell): string {
  return `${c.cx},${c.cy}`;
}
