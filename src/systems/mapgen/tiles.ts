import type { LayoutParams } from '../../data/types';
import { Rng } from '../rng';
import type { CellPlan } from './layout';
import {
  CELL_H,
  CELL_W,
  DIR_VEC,
  DOOR_MARGIN,
  ROOM_MARGIN,
  TileId,
  cellKey,
  type Cell,
  type Dir,
  type Door,
  type FloorLayout,
  type Rect,
  type Room,
} from './types';

/** 연결의 한쪽 끝: 복도가 시작하는 축 좌표와, 축에 수직인 위치(문 또는 복도 교차점) */
interface Port {
  /** 축에 수직인 좌표 (수평 연결이면 행, 수직 연결이면 열) */
  perp: number;
  /** 축 좌표: 복도 첫 타일 (방이면 벽선 바로 바깥, 복도 셀이면 교차점 중심) */
  from: number;
  /** 수직 좌표가 고를 수 있는 범위 */
  range: [number, number];
  room?: Room;
  wallLine?: number;
}

/**
 * 셀 계획을 타일 격자로 래스터화하고 문 위치를 기록한다 (32라운드: 방 확대·굽은 복도).
 * - 방 내부는 셀 안에 ROOM_MARGIN 여백을 두고 무작위로 놓인다 (셀 중앙 축을 포함할 필요 없음).
 * - 연결마다 양쪽 문 위치를 벽 위에서 따로 고르고, 두 문 사이 빈 공간에서 한 번 꺾는 Z 자 복도를 판다.
 *   두 방이 직접 이어지면 문 위치가 corridorWidth+1 이상 어긋나게 해 복도가 반드시 굽는다.
 * - 복도 셀(방이 없는 중간 셀)은 중앙에 교차점을 두고 거기서 각 방향 문으로 복도가 뻗는다.
 */
export function rasterize(rng: Rng, P: LayoutParams, plan: CellPlan, seed: number): FloorLayout {
  const widthTiles = P.gridW * CELL_W;
  const heightTiles = P.gridH * CELL_H;
  const tiles: TileId[][] = Array.from({ length: heightTiles }, () => new Array<TileId>(widthTiles).fill(TileId.Void));
  const half = Math.floor(P.corridorWidth / 2);

  const set = (x: number, y: number, id: TileId) => {
    if (x < 0 || y < 0 || x >= widthTiles || y >= heightTiles) return;
    tiles[y][x] = id;
  };
  const fillRect = (r: Rect, id: TileId) => {
    for (let y = r.y; y < r.y + r.h; y++) for (let x = r.x; x < r.x + r.w; x++) set(x, y, id);
  };
  /** 빈 타일만 복도로 (방 바닥·문은 그대로) */
  const carveBox = (x0: number, y0: number, x1: number, y1: number) => {
    for (let y = Math.min(y0, y1); y <= Math.max(y0, y1); y++)
      for (let x = Math.min(x0, x1); x <= Math.max(x0, x1); x++)
        if (tiles[y]?.[x] === TileId.Void) set(x, y, TileId.Corridor);
  };

  // 1) 방 내부 사각형
  const rooms: Room[] = plan.rooms.map((pr) => {
    const interior = pr.type === 'boss' ? bossInterior(rng, P, pr.cells) : roomInterior(rng, P, pr.cells[0]);
    return { id: pr.id, type: pr.type, cells: pr.cells, interior, doors: [] };
  });
  for (const r of rooms) fillRect(r.interior, TileId.Floor);

  const cellRoom = new Map<string, string>();
  for (const r of rooms) for (const c of r.cells) cellRoom.set(cellKey(c), r.id);
  const roomById = new Map(rooms.map((r) => [r.id, r]));
  const hallByKey = new Map(plan.hallways.map((h) => [cellKey(h.cell), h]));

  // 2) 복도 셀의 교차점 (셀 중앙, corridorWidth 정사각형)
  for (const h of plan.hallways) {
    const cx = h.cell.cx * CELL_W + CELL_W / 2;
    const cy = h.cell.cy * CELL_H + CELL_H / 2;
    fillRect({ x: cx - half, y: cy - half, w: P.corridorWidth, h: P.corridorWidth }, TileId.Corridor);
  }

  /** 셀 하나가 연결 방향 dir 로 내보내는 포트 (문 위치 범위, 복도 시작 좌표) */
  const portOf = (cell: Cell, dir: Dir): Port => {
    const [dx, dy] = DIR_VEC[dir];
    const horizontal = dx !== 0;
    const cellX = cell.cx * CELL_W;
    const cellY = cell.cy * CELL_H;
    // 수직 좌표는 이 셀의 띠 안에 있어야 한다 (보스 2×2 방의 문도 입구 셀 쪽에만)
    const bandLo = (horizontal ? cellY : cellX) + 1 + half;
    const bandHi = (horizontal ? cellY + CELL_H : cellX + CELL_W) - 2 - half;
    const roomId = cellRoom.get(cellKey(cell));
    if (roomId) {
      const room = roomById.get(roomId)!;
      const I = room.interior;
      const lo = Math.max(bandLo, (horizontal ? I.y : I.x) + DOOR_MARGIN + half);
      const hi = Math.min(bandHi, (horizontal ? I.y + I.h : I.x + I.w) - 1 - DOOR_MARGIN - half);
      if (lo > hi) throw new Error(`[mapgen] 방 ${roomId} 의 ${dir} 벽에 문을 놓을 자리가 없음`);
      const wallLine = horizontal ? (dx > 0 ? I.x + I.w : I.x - 1) : dy > 0 ? I.y + I.h : I.y - 1;
      return { perp: lo, from: wallLine + (dx + dy), range: [lo, hi], room, wallLine };
    }
    if (!hallByKey.has(cellKey(cell))) throw new Error(`[mapgen] 빈 셀에서 복도를 팔 수 없음 ${cellKey(cell)}`);
    const center = horizontal ? cellY + CELL_H / 2 : cellX + CELL_W / 2;
    const axisCenter = horizontal ? cellX + CELL_W / 2 : cellY + CELL_H / 2;
    return { perp: center, from: axisCenter, range: [center, center] };
  };

  /** a → b 연결 하나를 판다: 문 2개(또는 1개) + Z 자 복도 */
  const carveConnection = (a: Cell, b: Cell) => {
    const dir = dirBetween(a, b);
    const [dx] = DIR_VEC[dir];
    const horizontal = dx !== 0;
    const pa = portOf(a, dir);
    const pb = portOf(b, opposite(dir));
    pa.perp = rng.int(pa.range[0], pa.range[1]);
    pb.perp = rng.int(pb.range[0], pb.range[1]);
    // 양쪽 포트가 corridorWidth+1 이상 어긋나게 다시 고른다 (복도가 반드시 눈에 띄게 한 번 꺾이도록).
    // 복도 셀의 포트는 중앙 고정이므로 방 쪽 포트를 다시 고른다. 범위가 좁아 못 맞추면 그대로 둔다.
    const minGap = P.corridorWidth + 1;
    const movable = pb.room ? pb : pa;
    for (let t = 0; t < 8 && Math.abs(pa.perp - pb.perp) < minGap; t++)
      movable.perp = rng.int(movable.range[0], movable.range[1]);
    // 꺾이는 축 좌표 m: 양쪽 복도 시작점 사이, 수직 구간(폭 corridorWidth)이 벽에 닿지 않게
    const lo = Math.min(pa.from, pb.from) + half;
    const hi = Math.max(pa.from, pb.from) - half;
    if (lo > hi) throw new Error(`[mapgen] ${cellKey(a)} → ${cellKey(b)} 사이가 복도 폭보다 좁음`);
    const m = rng.int(lo, hi);
    const perpLo = Math.min(pa.perp, pb.perp) - half;
    const perpHi = Math.max(pa.perp, pb.perp) + half;
    if (horizontal) {
      carveBox(pa.from, pa.perp - half, m, pa.perp + half); // a 문 → 꺾임
      carveBox(m - half, perpLo, m + half, perpHi); // 꺾임 구간 (수직)
      carveBox(m, pb.perp - half, pb.from, pb.perp + half); // 꺾임 → b 문
    } else {
      carveBox(pa.perp - half, pa.from, pa.perp + half, m);
      carveBox(perpLo, m - half, perpHi, m + half);
      carveBox(pb.perp - half, m, pb.perp + half, pb.from);
    }
    const aBoss = pa.room?.type === 'boss';
    const bBoss = pb.room?.type === 'boss';
    placeDoor(pa, dir, horizontal, aBoss ?? false);
    placeDoor(pb, opposite(dir), horizontal, bBoss ?? false);
  };

  const placeDoor = (p: Port, dir: Dir, horizontal: boolean, toBoss: boolean) => {
    if (!p.room || p.wallLine === undefined) return;
    const tilesOfDoor = range(p.perp - half, p.perp + half).map((k) =>
      horizontal ? { x: p.wallLine!, y: k } : { x: k, y: p.wallLine! },
    );
    const door: Door = { roomId: p.room.id, dir, tiles: tilesOfDoor, toBoss };
    p.room.doors.push(door);
    for (const d of tilesOfDoor) set(d.x, d.y, toBoss ? TileId.DoorLocked : TileId.DoorOpen);
  };

  // 3) 연결마다 (중복 제거) 복도를 판다
  const seen = new Set<string>();
  for (const c of plan.connections) {
    const key = [cellKey(c.a), cellKey(c.b)].sort().join('|');
    if (seen.has(key)) continue;
    seen.add(key);
    carveConnection(c.a, c.b);
  }

  // 4) 바닥에 8방향으로 닿는 빈 타일은 벽
  for (let y = 0; y < heightTiles; y++) {
    for (let x = 0; x < widthTiles; x++) {
      if (tiles[y][x] !== TileId.Void) continue;
      let touch = false;
      for (let oy = -1; oy <= 1 && !touch; oy++) {
        for (let ox = -1; ox <= 1; ox++) {
          const ny = y + oy;
          const nx = x + ox;
          if (ny < 0 || nx < 0 || ny >= heightTiles || nx >= widthTiles) continue;
          const t = tiles[ny][nx];
          if (t !== TileId.Void && t !== TileId.Wall) {
            touch = true;
            break;
          }
        }
      }
      if (touch) tiles[y][x] = TileId.Wall;
    }
  }

  return {
    seed,
    gridW: P.gridW,
    gridH: P.gridH,
    rooms,
    hallways: plan.hallways,
    connections: plan.connections,
    tiles,
    widthTiles,
    heightTiles,
    cellRoom,
  };
}

/** 방 내부: 셀 안에 ROOM_MARGIN 여백을 두고 무작위 위치 */
function roomInterior(rng: Rng, P: LayoutParams, cell: Cell): Rect {
  const cellX = cell.cx * CELL_W;
  const cellY = cell.cy * CELL_H;
  const w = rng.int(P.roomW[0], P.roomW[1]);
  const h = rng.int(P.roomH[0], P.roomH[1]);
  const xLo = cellX + ROOM_MARGIN;
  const xHi = cellX + CELL_W - ROOM_MARGIN - w;
  const yLo = cellY + ROOM_MARGIN;
  const yHi = cellY + CELL_H - ROOM_MARGIN - h;
  if (xLo > xHi || yLo > yHi) throw new Error('[mapgen] roomW/roomH 범위가 셀 크기에 맞지 않음');
  return { x: rng.int(xLo, xHi), y: rng.int(yLo, yHi), w, h };
}

/** 보스 방 내부: 2×2 블록 중앙 */
function bossInterior(rng: Rng, P: LayoutParams, cells: Cell[]): Rect {
  const minX = Math.min(...cells.map((c) => c.cx));
  const minY = Math.min(...cells.map((c) => c.cy));
  const w = rng.int(P.bossRoomW[0], P.bossRoomW[1]);
  const h = rng.int(P.bossRoomH[0], P.bossRoomH[1]);
  if (w > 2 * CELL_W - 2 * ROOM_MARGIN || h > 2 * CELL_H - 2 * ROOM_MARGIN)
    throw new Error('[mapgen] bossRoomW/bossRoomH 범위가 2×2 블록에 맞지 않음');
  const ccx = minX * CELL_W + CELL_W; // 2×2 블록 중심
  const ccy = minY * CELL_H + CELL_H;
  return { x: ccx - Math.floor(w / 2), y: ccy - Math.floor(h / 2), w, h };
}

function dirBetween(a: Cell, b: Cell): Dir {
  if (b.cx === a.cx + 1 && b.cy === a.cy) return 'E';
  if (b.cx === a.cx - 1 && b.cy === a.cy) return 'W';
  if (b.cy === a.cy + 1 && b.cx === a.cx) return 'S';
  if (b.cy === a.cy - 1 && b.cx === a.cx) return 'N';
  throw new Error(`[mapgen] 인접하지 않은 연결 ${cellKey(a)} → ${cellKey(b)}`);
}

function opposite(d: Dir): Dir {
  return d === 'N' ? 'S' : d === 'S' ? 'N' : d === 'E' ? 'W' : 'E';
}

function range(a: number, b: number): number[] {
  const out: number[] = [];
  for (let i = a; i <= b; i++) out.push(i);
  return out;
}
