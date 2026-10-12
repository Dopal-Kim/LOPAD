/**
 * 62 루프 2 시스템 E — 문 나가기 (발판 출구 대체, Phaser 없음 · 시드 무관 결정적).
 * 노드 전투장은 방을 비우면 바닥 안 2×2 발판 대신 **외벽의 문**이 열린다. 출구 문 = 진행 방향(노드 지도 다음 열 = 동쪽) 벽,
 * 입구 문 = 반대편(서쪽) 벽. 문 줄은 `arenaDoorRows` (전장 생성기가 그 줄 앞 가장자리를 깎지 않는다).
 *
 * - 문 칸(cells): 문 줄(3칸)마다 마지막 바닥 칸 바깥 ~ 내부 사각형 바깥 벽 열까지 (보통 벽 1칸)
 * - 문턱(threshold): 벽 안쪽 1칸 띠 (문 줄의 마지막 바닥 칸) — 주인공 발이 여기 들어서면 나가기 걸음 시작
 * - mouth: 바닥 끝 선 위 문 가운데 (월드) · inside: 문 안 걸음 끝 · sill: 문턱 가운데
 */
import { TileId, type FloorLayout, type Rect } from '../mapgen/types';
import { arenaDoorRows } from '../mapgen/arena';

export type DoorSide = 'north' | 'south' | 'east' | 'west';

export interface DoorPoint {
  x: number;
  y: number;
}

export interface DoorSpot {
  side: DoorSide;
  /** 문 칸 (타일) — 바닥이 아닌 칸 (벽·빈 칸) */
  cells: DoorPoint[];
  /** 문턱 띠 (타일 사각형) */
  threshold: Rect;
  /** 바깥 방향 (단위) */
  out: DoorPoint;
  /** 문 가운데 — 바닥 끝 선 위 (월드) */
  mouth: DoorPoint;
  /** 문턱 가운데 (월드) */
  sill: DoorPoint;
  /** 문을 가로지르는 방향 범위 (동·서 문 = 월드 y, 북·남 문 = 월드 x) */
  span: [number, number];
}

const OUT: Record<DoorSide, DoorPoint> = {
  north: { x: 0, y: -1 },
  south: { x: 0, y: 1 },
  east: { x: 1, y: 0 },
  west: { x: -1, y: 0 },
};

/**
 * 한 벽의 문 (동·서 = 줄 center 의 위아래, 북·남 = 열 center 의 좌우, 폭 width 칸). 문 줄 어디에도 바닥이 없으면 null.
 * 줄마다 바깥쪽 끝 바닥 칸을 찾아 그 바깥(내부 사각형 경계 벽까지)을 문 칸으로, 가장 안쪽 끝 바닥 칸들을 문턱으로 둔다
 */
export function planDoor(
  layout: FloorLayout,
  side: DoorSide,
  center: number,
  width: number,
  tile: number,
): DoorSpot | null {
  const I = layout.rooms[0]?.interior;
  if (!I) return null;
  const half = Math.floor(width / 2);
  const lines: number[] = [];
  for (let i = center - half; i < center - half + width; i++) lines.push(i);
  const floor = (x: number, y: number) => isFloorish(layout.tiles[y]?.[x]);
  const horizontal = side === 'east' || side === 'west';
  // 줄마다: 바깥쪽 끝 바닥 (동 = 가장 오른쪽 바닥 …)
  const ends: number[] = [];
  for (const l of lines) {
    let end: number | null = null;
    if (side === 'east') for (let x = I.x + I.w - 1; x >= I.x && end === null; x--) end = floor(x, l) ? x : null;
    else if (side === 'west') for (let x = I.x; x < I.x + I.w && end === null; x++) end = floor(x, l) ? x : null;
    else if (side === 'north') for (let y = I.y; y < I.y + I.h && end === null; y++) end = floor(l, y) ? y : null;
    else for (let y = I.y + I.h - 1; y >= I.y && end === null; y--) end = floor(l, y) ? y : null;
    if (end === null) return null;
    ends.push(end);
  }
  const wall = side === 'east' ? I.x + I.w : side === 'west' ? I.x - 1 : side === 'north' ? I.y - 1 : I.y + I.h;
  const dir = side === 'east' || side === 'south' ? 1 : -1;
  const cells: DoorPoint[] = [];
  lines.forEach((l, i) => {
    for (let a = ends[i] + dir; dir > 0 ? a <= wall : a >= wall; a += dir)
      cells.push(horizontal ? { x: a, y: l } : { x: l, y: a });
  });
  // 문턱 = 가장 안쪽 끝 (동 = 끝 바닥 중 가장 왼쪽) 에서 1칸
  const inner = dir > 0 ? Math.min(...ends) : Math.max(...ends);
  const outer = dir > 0 ? Math.max(...ends) : Math.min(...ends);
  const a0 = Math.min(inner, outer);
  const a1 = Math.max(inner, outer);
  const l0 = lines[0];
  const threshold: Rect = horizontal
    ? { x: a0, y: l0, w: a1 - a0 + 1, h: width }
    : { x: l0, y: a0, w: width, h: a1 - a0 + 1 };
  // 바닥 끝 선 = 바깥쪽 끝 바닥 칸의 바깥 경계
  const edge = (dir > 0 ? outer + 1 : outer) * tile;
  const mid = (l0 + width / 2) * tile;
  const mouth = horizontal ? { x: edge, y: mid } : { x: mid, y: edge };
  const sillA = ((a0 + a1 + 1) / 2) * tile;
  const sill = horizontal ? { x: sillA, y: mid } : { x: mid, y: sillA };
  return {
    side,
    cells,
    threshold,
    out: OUT[side],
    mouth,
    sill,
    span: [l0 * tile, (l0 + width) * tile],
  };
}

/**
 * 노드 전투장의 출구 문(동) · 입구 문(서). entry = false 면 입구 문 없음 (탄생 전장 — 가운데에서 태어난다).
 * 전장 정보가 없으면 둘 다 null
 */
export function arenaDoors(
  layout: FloorLayout,
  tile: number,
  width: number,
  entry: boolean,
): { exit: DoorSpot | null; entry: DoorSpot | null } {
  const A = layout.arena;
  if (!A) return { exit: null, entry: null };
  const rows = arenaDoorRows(A, entry);
  return {
    exit: planDoor(layout, 'east', rows.exit, width, tile),
    entry: rows.entry !== null ? planDoor(layout, 'west', rows.entry, width, tile) : null,
  };
}

/** 월드 점이 문턱 띠 안인가 */
export function inThreshold(spot: DoorSpot, x: number, y: number, tile: number): boolean {
  const T = spot.threshold;
  return x >= T.x * tile && x < (T.x + T.w) * tile && y >= T.y * tile && y < (T.y + T.h) * tile;
}

/** mouth 에서 바깥(+)/안쪽(−)으로 dist 만큼 (문 가운데 줄 위) */
export function alongDoor(spot: DoorSpot, dist: number): DoorPoint {
  return { x: spot.mouth.x + spot.out.x * dist, y: spot.mouth.y + spot.out.y * dist };
}

/** 점이 바닥 끝 선에서 바깥으로 얼마나 나갔는가 (월드, 안쪽이면 음수) */
export function pastMouth(spot: DoorSpot, x: number, y: number): number {
  return (x - spot.mouth.x) * spot.out.x + (y - spot.mouth.y) * spot.out.y;
}

/**
 * 들어오는 걸음: 시작점(문 안) → 목표. 목표 = spawn 이 문에서 maxSpawnDist 안이면 spawn, 아니면 문에서 stopDist 안쪽.
 * 시작점 = 목표에서 문 쪽으로 walkDist (단, 바닥 끝 바깥 minOut 보다 안쪽이면 거기까지 물린다 — 늘 문 안에서 시작)
 */
export function entryWalk(
  spot: DoorSpot,
  spawn: DoorPoint,
  o: { walkDist: number; maxSpawnDist: number; stopDist: number; minOut: number },
): { from: DoorPoint; to: DoorPoint } {
  const spawnIn = -pastMouth(spot, spawn.x, spawn.y);
  const onLine = Math.abs((spawn.x - spot.mouth.x) * spot.out.y) + Math.abs((spawn.y - spot.mouth.y) * spot.out.x);
  const toDist =
    spawnIn > 0 && spawnIn <= o.maxSpawnDist && onLine <= spot.span[1] - spot.span[0] ? spawnIn : o.stopDist;
  const to = toDist === spawnIn ? { x: spawn.x, y: spawn.y } : alongDoor(spot, -toDist);
  const fromOut = Math.max(o.minOut, o.walkDist - toDist);
  const from = alongDoor(spot, fromOut);
  // spawn 이 문 줄에서 조금 비켜 있으면 시작점도 그만큼 (가로지르는 방향은 목표와 같게)
  if (toDist === spawnIn) {
    if (spot.out.x !== 0) from.y = spawn.y;
    else from.x = spawn.x;
  }
  return { from, to };
}

function isFloorish(id: TileId | undefined): boolean {
  return id === TileId.Floor || id === TileId.Shop || id === TileId.Exit || id === TileId.Corridor;
}
