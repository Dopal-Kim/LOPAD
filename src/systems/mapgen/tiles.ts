import type { LayoutParams } from '../../data/types';
import { Rng } from '../rng';
import type { CellPlan } from './layout';
import {
  CELL_H,
  CELL_W,
  DIR_VEC,
  TileId,
  cellKey,
  type Cell,
  type Dir,
  type Door,
  type FloorLayout,
  type Rect,
  type Room,
} from './types';

/** 셀 계획을 타일 격자로 래스터화하고 문 위치를 기록한다. */
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

  // 2) 복도 junction (복도 셀 중앙)
  for (const h of plan.hallways) {
    const cx = h.cell.cx * CELL_W + CELL_W / 2;
    const cy = h.cell.cy * CELL_H + Math.floor(CELL_H / 2);
    fillRect({ x: cx - half, y: cy - half, w: P.corridorWidth, h: P.corridorWidth }, TileId.Corridor);
  }

  // 3) 연결마다 양쪽 셀에서 공유 변까지 복도를 판다
  const carveToEdge = (cell: Cell, dir: Dir, toBoss: boolean) => {
    const [dx, dy] = DIR_VEC[dir];
    const cellX = cell.cx * CELL_W;
    const cellY = cell.cy * CELL_H;
    // 복도 축: 수평 연결이면 셀 중앙 행, 수직 연결이면 셀 중앙 열
    const axisRow = cellY + Math.floor(CELL_H / 2);
    const axisCol = cellX + CELL_W / 2;
    const roomId = cellRoom.get(cellKey(cell));
    let from: number; // 축을 따라 파기 시작하는 좌표(벽선 바로 다음)
    let doorTiles: { x: number; y: number }[] = [];
    if (roomId) {
      const room = roomById.get(roomId)!;
      const I = room.interior;
      let wallLine: number;
      if (dx !== 0) {
        wallLine = dx > 0 ? I.x + I.w : I.x - 1;
        if (axisRow - half < I.y || axisRow + half > I.y + I.h - 1)
          throw new Error(`[mapgen] 방 ${roomId} 가 복도 축을 포함하지 않음`);
        doorTiles = range(axisRow - half, axisRow + half).map((y) => ({ x: wallLine, y }));
      } else {
        wallLine = dy > 0 ? I.y + I.h : I.y - 1;
        if (axisCol - half < I.x || axisCol + half > I.x + I.w - 1)
          throw new Error(`[mapgen] 방 ${roomId} 가 복도 축을 포함하지 않음`);
        doorTiles = range(axisCol - half, axisCol + half).map((x) => ({ x, y: wallLine }));
      }
      from = wallLine + (dx + dy);
      const door: Door = { roomId, dir, tiles: doorTiles, toBoss };
      room.doors.push(door);
    } else {
      if (!hallByKey.has(cellKey(cell))) throw new Error(`[mapgen] 빈 셀에서 복도를 팔 수 없음 ${cellKey(cell)}`);
      from = dx !== 0 ? axisCol : axisRow;
    }
    const edge = dx > 0 ? cellX + CELL_W - 1 : dx < 0 ? cellX : dy > 0 ? cellY + CELL_H - 1 : cellY;
    const lo = Math.min(from, edge);
    const hi = Math.max(from, edge);
    for (let t = lo; t <= hi; t++) {
      for (let k = -half; k <= half; k++) {
        if (dx !== 0) {
          if (tiles[axisRow + k][t] === TileId.Void) set(t, axisRow + k, TileId.Corridor);
        } else if (tiles[t][axisCol + k] === TileId.Void) set(axisCol + k, t, TileId.Corridor);
      }
    }
    for (const d of doorTiles) set(d.x, d.y, toBoss ? TileId.DoorLocked : TileId.DoorOpen);
  };

  const seen = new Set<string>();
  for (const c of plan.connections) {
    const key = [cellKey(c.a), cellKey(c.b)].sort().join('|');
    if (seen.has(key)) continue;
    seen.add(key);
    const dir = dirBetween(c.a, c.b);
    const aBoss = cellRoom.get(cellKey(c.a)) === 'boss';
    const bBoss = cellRoom.get(cellKey(c.b)) === 'boss';
    carveToEdge(c.a, dir, aBoss);
    carveToEdge(c.b, opposite(dir), bBoss);
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

function roomInterior(rng: Rng, P: LayoutParams, cell: Cell): Rect {
  const cellX = cell.cx * CELL_W;
  const cellY = cell.cy * CELL_H;
  const ccx = cellX + CELL_W / 2;
  const ccy = cellY + Math.floor(CELL_H / 2);
  const w = rng.int(P.roomW[0], P.roomW[1]);
  const h = rng.int(P.roomH[0], P.roomH[1]);
  const half = Math.floor(P.corridorWidth / 2);
  // 내부가 셀 중앙 행·열(복도 축 ± half)을 포함하고, 셀 경계에서 2타일 이상 떨어지도록
  const xLo = Math.max(cellX + 2, ccx + half - w + 1);
  const xHi = Math.min(cellX + CELL_W - 2 - w, ccx - half);
  const yLo = Math.max(cellY + 2, ccy + half - h + 1);
  const yHi = Math.min(cellY + CELL_H - 2 - h, ccy - half);
  if (xLo > xHi || yLo > yHi) throw new Error('[mapgen] roomW/roomH 범위가 셀 크기에 맞지 않음');
  return { x: rng.int(xLo, xHi), y: rng.int(yLo, yHi), w, h };
}

function bossInterior(rng: Rng, P: LayoutParams, cells: Cell[]): Rect {
  const minX = Math.min(...cells.map((c) => c.cx));
  const minY = Math.min(...cells.map((c) => c.cy));
  const w = rng.int(P.bossRoomW[0], P.bossRoomW[1]);
  const h = rng.int(P.bossRoomH[0], P.bossRoomH[1]);
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
