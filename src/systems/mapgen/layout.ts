import type { LayoutParams } from '../../data/types';
import { Rng } from '../rng';
import {
  DIRS,
  DIR_VEC,
  type Cell,
  type Connection,
  type Dir,
  type Hallway,
  type Room,
  type RoomType,
  cellKey,
} from './types';

/** 셀 격자 위 방·복도 배치 (타일 좌표는 아직 없음). 실패하면 null → 호출자가 재시도. */
export interface CellPlan {
  rooms: { id: string; type: RoomType; cells: Cell[]; entryDir?: Dir }[];
  hallways: Hallway[];
  connections: Connection[];
}

export function planCells(rng: Rng, P: LayoutParams): CellPlan | null {
  const occupied = new Map<string, string>(); // cellKey → room id | 'hall'
  const rooms: CellPlan['rooms'] = [];
  const hallways: Hallway[] = [];
  const connections: Connection[] = [];

  const inBounds = (c: Cell) => c.cx >= 0 && c.cy >= 0 && c.cx < P.gridW && c.cy < P.gridH;
  const free = (c: Cell) => inBounds(c) && !occupied.has(cellKey(c));
  const step = (c: Cell, d: Dir, n = 1): Cell => ({ cx: c.cx + DIR_VEC[d][0] * n, cy: c.cy + DIR_VEC[d][1] * n });

  const addRoom = (id: string, type: RoomType, cells: Cell[]) => {
    for (const c of cells) occupied.set(cellKey(c), id);
    rooms.push({ id, type, cells });
  };
  const addHall = (c: Cell, dirs: Dir[]) => {
    occupied.set(cellKey(c), 'hall');
    hallways.push({ cell: c, dirs });
  };
  const connect = (a: Cell, b: Cell) => connections.push({ a, b });

  // 시작 방: 격자 안쪽 어딘가
  const start: Cell = { cx: rng.int(1, P.gridW - 2), cy: rng.int(1, P.gridH - 2) };
  addRoom('start', 'start', [start]);

  // 시련 방: 시작 방에서 최소 거리를 두고, 기존 방에서 자라나는 트리
  const roomCells = (): Cell[] => rooms.filter((r) => r.type !== 'boss').flatMap((r) => r.cells);
  const manhattan = (a: Cell, b: Cell) => Math.abs(a.cx - b.cx) + Math.abs(a.cy - b.cy);

  for (let i = 0; i < P.trialCount; i++) {
    let placed = false;
    for (let tries = 0; tries < 60 && !placed; tries++) {
      const from = rng.pick(roomCells());
      const d = rng.pick(DIRS);
      const fromIsStart = occupied.get(cellKey(from)) === 'start';
      const needHall = fromIsStart && P.trialMinDistFromStart >= 2;
      const dist = needHall ? 2 : rng.chance(0.4) ? 2 : 1;
      const target = step(from, d, dist);
      if (!free(target)) continue;
      if (manhattan(target, start) < P.trialMinDistFromStart) continue;
      if (dist === 2) {
        const mid = step(from, d, 1);
        const midKey = cellKey(mid);
        const midOcc = occupied.get(midKey);
        if (midOcc && midOcc !== 'hall') continue;
        if (!midOcc) addHall(mid, [d, oppositeOf(d)]);
        else hallways.find((h) => cellKey(h.cell) === midKey)!.dirs.push(d, oppositeOf(d));
        connect(from, mid);
        connect(mid, target);
      } else {
        connect(from, target);
      }
      addRoom(`trial${i + 1}`, 'trial', [target]);
      placed = true;
    }
    if (!placed) return null;
  }

  // 휴식 방: 기존 방 옆 아무 곳 (보스 입구일 필요 없음 — 10라운드)
  for (let i = 0; i < P.restCount; i++) {
    let placed = false;
    for (let tries = 0; tries < 80 && !placed; tries++) {
      const from = rng.pick(roomCells());
      const d = rng.pick(DIRS);
      const target = step(from, d, 1);
      if (!free(target)) continue;
      addRoom(`rest${i + 1}`, 'rest', [target]);
      connect(from, target);
      placed = true;
    }
    if (!placed) return null;
  }

  // 보스 2×2 블록: 시작 방을 제외한 아무 방(시련·휴식)에 인접
  {
    const candidates = rng.shuffle(rooms.filter((r) => r.type !== 'start' && r.type !== 'boss').map((r) => r.cells[0]));
    let placed = false;
    for (const anchor of candidates) {
      const options = bossBlockOptions(anchor, free, step);
      if (options.length === 0) continue;
      const chosen = rng.pick(options);
      addRoom('boss', 'boss', chosen.cells);
      const bossEntry = chosen.cells.find((c) => manhattan(c, anchor) === 1)!;
      connect(anchor, bossEntry);
      placed = true;
      break;
    }
    if (!placed) return null;
  }

  // 열린 구조: 인접한 방끼리 추가 연결 (보스 제외)
  const nonBoss = rooms.filter((r) => r.type !== 'boss');
  const hasConn = (a: Cell, b: Cell) =>
    connections.some(
      (c) =>
        (cellKey(c.a) === cellKey(a) && cellKey(c.b) === cellKey(b)) ||
        (cellKey(c.a) === cellKey(b) && cellKey(c.b) === cellKey(a)),
    );
  for (const r of nonBoss) {
    for (const d of ['E', 'S'] as Dir[]) {
      const nb = step(r.cells[0], d);
      const occ = occupied.get(cellKey(nb));
      if (!occ || occ === 'hall' || occ === 'boss') continue;
      if (hasConn(r.cells[0], nb)) continue;
      if (rng.chance(P.extraLoopChance)) connect(r.cells[0], nb);
    }
  }

  return { rooms, hallways, connections };
}

function oppositeOf(d: Dir): Dir {
  return d === 'N' ? 'S' : d === 'S' ? 'N' : d === 'E' ? 'W' : 'E';
}

function bossBlockOptions(rest: Cell, free: (c: Cell) => boolean, step: (c: Cell, d: Dir, n?: number) => Cell) {
  const options: { cells: Cell[] }[] = [];
  for (const d of DIRS) {
    const adj = step(rest, d);
    // 블록의 한 셀이 adj 가 되도록 2×2 블록 두 가지 (수직/수평 오프셋)
    const horizontal = d === 'E' || d === 'W';
    for (const off of [0, -1]) {
      const cells: Cell[] = [];
      for (let i = 0; i < 2; i++) {
        for (let j = 0; j < 2; j++) {
          const cx = horizontal ? adj.cx + (d === 'E' ? i : -i) : adj.cx + off + j;
          const cy = horizontal ? adj.cy + off + j : adj.cy + (d === 'S' ? i : -i);
          cells.push({ cx, cy });
        }
      }
      if (cells.every(free)) options.push({ cells });
    }
  }
  return options;
}

export type { Room };
