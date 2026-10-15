/**
 * 48라운드 Q3·Q10: 노드 전투장 (방 하나, 복도 없음). 같은 spec(시드 포함)이면 같은 결과.
 * [빈 공간 여백 → 벽 1칸 → 내부 w×h] 를 놓는다. 여백은 숨은 벽 저장고 자리(47라운드 hiddenWall `minMarginTiles`)라 비워 둔다.
 * 시작점은 왼쪽, 출구는 오른쪽.
 *
 * P19 S2 (계약 free-combat §3): `shape` 가 있으면 사각 대신 형태 틀(`mapgen/shape`) 격자로 내부를 채운다 — 벽 · 엄폐(벽) ·
 * 낙하 구역(빈 칸 = 걷기 막힘, `arena.drops`) · 다리 · 높은 단 · 계단. 시작 줄 = 서쪽 입구 문 줄, 출구 줄 = 동쪽 출구 문 줄.
 * (49라운드 들쭉날쭉한 가장자리 · 열린 틈은 형태 틀로 교체해 지웠다)
 */
import {
  CELL_H,
  CELL_W,
  TileId,
  cellKey,
  type Cell,
  type DropKind,
  type FloorLayout,
  type Rect,
  type Room,
  type RoomType,
} from './types';
import { DROPS, WALKABLE, type ShapeGrid } from './shape';

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
  /** 시작점을 가운데 근처로 (48라운드 탄생지: 중앙에서 왼쪽으로 SPAWN_CENTER_OFFSET 칸 — 무기 시험장도 사용) */
  spawnCenter?: boolean;
  /** 49라운드 3: 시작점 = 정확히 중앙 (탄생 전장 — 혼불이 모이는 자리). spawnCenter 보다 우선 */
  spawnExactCenter?: boolean;
  /** 49라운드 6: 상점 2×2 를 전투장 중앙에 (특수 노드 기능은 중앙) */
  shopCenter?: boolean;
  /** 61라운드 단계 2 방 다양화: 시작점·출구 줄을 가운데에서 위(−)·아래(+)로 옮기는 칸 (안쪽 3칸 여유를 넘지 않게 자른다) */
  spawnShiftY?: number;
  /** P19 S2: 형태 틀 격자 (있으면 w·h·시작/출구 줄은 격자에서) */
  shape?: ShapeGrid;
  seed?: number;
}

/** 48라운드 spawnCenter: 중앙에서 왼쪽으로 떨어진 칸 (기존 동작 유지) */
const SPAWN_CENTER_OFFSET = 4;
/** 61라운드: 시작·출구 줄 이동의 위아래 여유 (가장자리에서 이만큼 안쪽까지만) */
const SHIFT_MARGIN = 4;

/** 전투장 내부 중앙 타일 */
export function arenaCenter(interior: Rect): { x: number; y: number } {
  return { x: interior.x + Math.floor(interior.w / 2), y: interior.y + Math.floor(interior.h / 2) };
}

export function generateArena(spec: ArenaSpec): FloorLayout {
  const S = spec.shape;
  const w = S ? S.w : spec.w;
  const h = S ? S.h : spec.h;
  const widthTiles = w + 2 + spec.margin * 2;
  const heightTiles = h + 2 + spec.margin * 2;
  const tiles: TileId[][] = Array.from({ length: heightTiles }, () => new Array<TileId>(widthTiles).fill(TileId.Void));
  const ix = spec.margin + 1;
  const iy = spec.margin + 1;
  const interior: Rect = { x: ix, y: iy, w, h };
  const center = arenaCenter(interior);
  const midY = iy + Math.floor(h / 2);
  const maxShift = Math.max(0, Math.floor(h / 2) - SHIFT_MARGIN);
  const shift = S ? 0 : Math.max(-maxShift, Math.min(maxShift, Math.round(spec.spawnShiftY ?? 0)));
  const spawnY = S ? iy + S.entryRow : spec.spawnExactCenter || spec.spawnCenter ? midY : midY + shift;
  const spawn = {
    x: spec.spawnExactCenter ? center.x : spec.spawnCenter ? center.x - SPAWN_CENTER_OFFSET : ix + spec.spawnInset,
    y: spawnY,
  };
  // 출구는 시작 줄과 반대쪽으로 (가로지르는 동선) — 형태 틀은 출구 문 줄이 출구 2×2 의 아래 줄
  const exit = {
    x: ix + w - spec.exitInset - 2,
    y: S ? iy + S.exitRow - 1 : midY - 1 - (spec.spawnExactCenter ? 0 : shift),
  };
  const shop = spec.shopCenter ? { x: center.x - 1, y: center.y - 1 } : { x: center.x - 1, y: iy + 2 };
  // 사각 벽(바깥 1칸) + 내부
  for (let y = iy - 1; y <= iy + h; y++) for (let x = ix - 1; x <= ix + w; x++) tiles[y][x] = TileId.Wall;
  const drops: { x: number; y: number; kind: DropKind }[] = [];
  const bridges: { x: number; y: number }[] = [];
  const high: { x: number; y: number }[] = [];
  const stairs: { x: number; y: number }[] = [];
  const cover: { x: number; y: number }[] = [];
  for (let y = 0; y < h; y++)
    for (let x = 0; x < w; x++) {
      const t = S ? S.cells[y][x] : 'floor';
      const p = { x: ix + x, y: iy + y };
      if (WALKABLE.has(t)) tiles[p.y][p.x] = TileId.Floor;
      else if (DROPS.has(t)) {
        tiles[p.y][p.x] = TileId.Void;
        drops.push({ ...p, kind: t as DropKind });
      }
      if (t === 'bridge') bridges.push(p);
      else if (t === 'high' || t === 'stairs') high.push(p);
      if (t === 'stairs') stairs.push(p);
      else if (t === 'cover') cover.push(p);
    }
  // 시작점이 바닥이 아니면(형태 틀 문 줄이 얕을 때) 문 쪽으로 당긴다
  while (S && spawn.x > ix && tiles[spawn.y][spawn.x] !== TileId.Floor) spawn.x--;

  // 셀 하나보다 큰 전투장도 방 판정(cellRoom)이 닿게 덮는 셀 전부
  const cells: Cell[] = [];
  for (let cy = 0; cy * CELL_H < heightTiles; cy++)
    for (let cx = 0; cx * CELL_W < widthTiles; cx++) cells.push({ cx, cy });
  const room: Room = { id: spec.roomId, type: spec.type, floor: spec.floor, cells, interior, doors: [] };
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
    cellRoom: new Map(cells.map((c) => [cellKey(c), room.id])),
    arena: {
      spawn,
      exit,
      shop,
      center,
      camera: { x: ix - 1, y: iy - 1, w: w + 2, h: h + 2 },
      ...(S
        ? {
            shape: S.id,
            drops,
            bridges,
            high,
            stairs,
            cover,
            enemySpawns: S.spawns.map((p) => ({ x: ix + p.x, y: iy + p.y })),
          }
        : {}),
    },
  };
}

/**
 * 62 루프 2 E 문 줄 (가운데 줄 · 위아래 1칸 = 3칸, `DOORS.OPEN_TILES`): 출구 문 = 오른쪽 벽, 출구 2×2 의 아래 줄이 가운데 ·
 * 입구 문 = 왼쪽 벽, 시작 줄이 가운데 (시작점이 가운데 근처인 전장 — 탄생지·수련장 — 은 입구 문 없음)
 */
export function arenaDoorRows(
  arena: { spawn: { y: number }; exit: { y: number } },
  entry: boolean,
): { exit: number; entry: number | null } {
  return { exit: arena.exit.y + 1, entry: entry ? arena.spawn.y : null };
}

const DIR4: readonly [number, number][] = [
  [1, 0],
  [-1, 0],
  [0, 1],
  [0, -1],
];

/** from 에서 4방향으로 닿는 바닥 칸 (`"x,y"`) */
function reachableFloor(tiles: readonly (readonly TileId[])[], from: { x: number; y: number }): Set<string> {
  const seen = new Set<string>();
  if (tiles[from.y]?.[from.x] !== TileId.Floor) return seen;
  seen.add(`${from.x},${from.y}`);
  const stack = [from];
  while (stack.length) {
    const p = stack.pop()!;
    for (const [dx, dy] of DIR4) {
      const x = p.x + dx;
      const y = p.y + dy;
      const k = `${x},${y}`;
      if (seen.has(k) || tiles[y]?.[x] !== TileId.Floor) continue;
      seen.add(k);
      stack.push({ x, y });
    }
  }
  return seen;
}

/** 바닥 칸이 모두 4방향으로 이어져 있는지 (검증·테스트용) */
export function floorConnected(tiles: readonly (readonly TileId[])[]): boolean {
  let start: { x: number; y: number } | null = null;
  let total = 0;
  for (let y = 0; y < tiles.length; y++)
    for (let x = 0; x < tiles[y].length; x++)
      if (tiles[y][x] === TileId.Floor) {
        total++;
        start ??= { x, y };
      }
  if (!start) return true;
  return reachableFloor(tiles, start).size === total;
}
