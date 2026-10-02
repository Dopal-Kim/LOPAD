/** 맵 생성기의 순수 데이터 타입. Phaser 의존 없음. */

export type RoomType = 'start' | 'trial' | 'rest' | 'boss';
export type Dir = 'N' | 'S' | 'E' | 'W';

export const DIRS: Dir[] = ['N', 'S', 'E', 'W'];
export const DIR_VEC: Record<Dir, [number, number]> = { N: [0, -1], S: [0, 1], E: [1, 0], W: [-1, 0] };
export const DIR_OPP: Record<Dir, Dir> = { N: 'S', S: 'N', E: 'W', W: 'E' };

/**
 * 셀 하나 = 방 한 칸 (타일 단위). 32라운드 Q5: 80×48 (1280×768px) — 화면 960×540 보다 크고 카메라가 따라간다.
 * 방 내부는 셀 안에 ROOM_MARGIN 이상 여백을 두고 놓이며, 남는 공간을 복도가 지나간다.
 */
export const CELL_W = 80;
export const CELL_H = 48;

/** 방 내부 사각형이 셀 경계에서 떨어지는 최소 타일 수 (벽 1 + 복도 꺾임 공간) */
export const ROOM_MARGIN = 3;
/** 문이 방 모서리에서 떨어지는 최소 타일 수 (문 양옆에 벽이 남도록) */
export const DOOR_MARGIN = 2;

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
  /** 48라운드 노드 전투장: 바닥 타일 종류(roomFloors 키). 없으면 type */
  floor?: RoomType;
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
  /** 보스 처치 후 출구 옆 상점 (런타임에만 놓임) */
  Shop = 8,
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
  /** 48라운드 노드 전투장이면 시작점·출구·카메라 경계 (타일 좌표). 방+복도 층은 없음 */
  arena?: ArenaInfo;
}

/** 48라운드 노드 전투장 부가 정보 (타일 좌표) */
export interface ArenaInfo {
  /** 플레이어 시작 타일 (중심) */
  spawn: { x: number; y: number };
  /** 출구 2×2 의 왼쪽 위 타일 */
  exit: { x: number; y: number };
  /** 상점 2×2 의 왼쪽 위 타일 (상점 노드) */
  shop: { x: number; y: number };
  /** 49라운드: 전투장 내부 중앙 타일 (세트 배치·탄생 자리 기준) */
  center?: { x: number; y: number };
  /** 카메라 경계 (방 내부 + 벽 1칸) */
  camera: Rect;
}

export function cellKey(c: Cell): string {
  return `${c.cx},${c.cy}`;
}
