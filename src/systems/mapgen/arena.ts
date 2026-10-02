/**
 * 48라운드 Q3·Q10: 노드 전투장 (방 하나, 복도 없음). 시드와 무관한 고정 모양이라 결정적이다.
 * 셀 하나(CELL_W×CELL_H) 안에 [빈 공간 여백 → 벽 1칸 → 내부 w×h] 를 놓는다. 여백은 숨은 벽 저장고 자리
 * (47라운드 hiddenWall `minMarginTiles`)라 비워 둔다. 시작점은 왼쪽, 출구는 오른쪽 가운데.
 */
import { CELL_H, CELL_W, TileId, cellKey, type FloorLayout, type Room, type RoomType } from './types';

export interface ArenaSpec {
  roomId: string;
  /** 방 상태 머신 종류 */
  type: RoomType;
  /** 바닥 종류 (roomFloors) */
  floor: RoomType;
  /** 내부 크기 (타일) */
  w: number;
  h: number;
  /** 벽 바깥 빈 공간 여백 (타일) */
  margin: number;
  /** 시작점: 왼쪽 벽에서 안쪽으로 · 출구: 오른쪽 벽에서 안쪽으로 (타일) */
  spawnInset: number;
  exitInset: number;
  /** 시작점을 가운데로 (탄생지: 탄생 연출을 화면 가운데에서) */
  spawnCenter?: boolean;
  seed?: number;
}

export function generateArena(spec: ArenaSpec): FloorLayout {
  const widthTiles = spec.w + 2 + spec.margin * 2;
  const heightTiles = spec.h + 2 + spec.margin * 2;
  if (widthTiles > CELL_W || heightTiles > CELL_H)
    throw new Error(`[arena] 전투장(${widthTiles}×${heightTiles})이 셀(${CELL_W}×${CELL_H})보다 큼`);
  const tiles: TileId[][] = Array.from({ length: heightTiles }, () => new Array<TileId>(widthTiles).fill(TileId.Void));
  const ix = spec.margin + 1;
  const iy = spec.margin + 1;
  for (let y = iy - 1; y <= iy + spec.h; y++)
    for (let x = ix - 1; x <= ix + spec.w; x++) {
      const inside = x >= ix && x < ix + spec.w && y >= iy && y < iy + spec.h;
      tiles[y][x] = inside ? TileId.Floor : TileId.Wall;
    }
  const room: Room = {
    id: spec.roomId,
    type: spec.type,
    floor: spec.floor,
    cells: [{ cx: 0, cy: 0 }],
    interior: { x: ix, y: iy, w: spec.w, h: spec.h },
    doors: [],
  };
  const midY = iy + Math.floor(spec.h / 2);
  return {
    seed: spec.seed ?? 0,
    gridW: 1,
    gridH: 1,
    rooms: [room],
    hallways: [],
    connections: [],
    tiles,
    widthTiles,
    heightTiles,
    cellRoom: new Map([[cellKey({ cx: 0, cy: 0 }), room.id]]),
    arena: {
      spawn: { x: spec.spawnCenter ? ix + Math.floor(spec.w / 2) - 4 : ix + spec.spawnInset, y: midY },
      exit: { x: ix + spec.w - spec.exitInset - 2, y: midY - 1 },
      shop: { x: ix + Math.floor(spec.w / 2) - 1, y: iy + 2 },
      camera: { x: ix - 1, y: iy - 1, w: spec.w + 2, h: spec.h + 2 },
    },
  };
}
