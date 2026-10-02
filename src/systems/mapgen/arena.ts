/**
 * 48라운드 Q3·Q10: 노드 전투장 (방 하나, 복도 없음). 같은 spec(시드 포함)이면 같은 결과.
 * 셀 하나(CELL_W×CELL_H) 안에 [빈 공간 여백 → 벽 1칸 → 내부 w×h] 를 놓는다. 여백은 숨은 벽 저장고 자리
 * (47라운드 hiddenWall `minMarginTiles`)라 비워 둔다. 시작점은 왼쪽, 출구는 오른쪽 가운데.
 *
 * 49라운드 4-2(실내 느낌 제거): `edge` 가 있으면 사각 벽 대신 가장자리가 안쪽으로 들쭉날쭉 파고드는 담·잔해
 * (깊이 0..maxInset, run 칸마다 바뀜)가 되고, 위·아래 벽 일부는 열린 틈(원경 void)으로 남는다.
 * 시작점·출구·keepClear 사각형은 깎지 않는다. 방 내부 사각형(`interior`)은 그대로라 방 판정·카메라는 변하지 않는다.
 */
import { Rng, hashSeed } from '../rng';
import { CELL_H, CELL_W, TileId, cellKey, type FloorLayout, type Rect, type Room, type RoomType } from './types';

/** 49라운드: 가장자리 모양 (data/route.json arena.edge + 지역 edge) */
export interface ArenaEdge {
  /** 안쪽으로 파고드는 최대 깊이 (타일) */
  maxInset: number;
  /** 같은 깊이가 이어지는 길이 [min, max] (타일) */
  run: [number, number];
  /** 위·아래 벽의 열린 틈 개수 [min, max] */
  gaps: [number, number];
  /** 틈 폭 [min, max] (타일) */
  gapWidth: [number, number];
  /** 틈을 모서리에서 떨어뜨리는 칸 */
  cornerMarginTiles: number;
  /** 시작점·출구 둘레 보호 반경 (타일) */
  keepClearTiles: number;
}

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
  /** 49라운드: 들쭉날쭉한 가장자리 (없으면 48라운드 사각 벽) */
  edge?: ArenaEdge;
  /** 가장자리가 깎지 않을 사각형 (타일, 시작점·출구는 자동) */
  keepClear?: readonly Rect[];
  seed?: number;
}

/** 48라운드 spawnCenter: 중앙에서 왼쪽으로 떨어진 칸 (기존 동작 유지) */
const SPAWN_CENTER_OFFSET = 4;

/** 전투장 내부 중앙 타일 */
export function arenaCenter(interior: Rect): { x: number; y: number } {
  return { x: interior.x + Math.floor(interior.w / 2), y: interior.y + Math.floor(interior.h / 2) };
}

export function generateArena(spec: ArenaSpec): FloorLayout {
  const widthTiles = spec.w + 2 + spec.margin * 2;
  const heightTiles = spec.h + 2 + spec.margin * 2;
  if (widthTiles > CELL_W || heightTiles > CELL_H)
    throw new Error(`[arena] 전투장(${widthTiles}×${heightTiles})이 셀(${CELL_W}×${CELL_H})보다 큼`);
  const tiles: TileId[][] = Array.from({ length: heightTiles }, () => new Array<TileId>(widthTiles).fill(TileId.Void));
  const ix = spec.margin + 1;
  const iy = spec.margin + 1;
  const interior: Rect = { x: ix, y: iy, w: spec.w, h: spec.h };
  const center = arenaCenter(interior);
  const midY = iy + Math.floor(spec.h / 2);
  const spawn = {
    x: spec.spawnExactCenter ? center.x : spec.spawnCenter ? center.x - SPAWN_CENTER_OFFSET : ix + spec.spawnInset,
    y: midY,
  };
  const exit = { x: ix + spec.w - spec.exitInset - 2, y: midY - 1 };
  const shop = spec.shopCenter ? { x: center.x - 1, y: center.y - 1 } : { x: center.x - 1, y: iy + 2 };

  for (let y = iy; y < iy + spec.h; y++) for (let x = ix; x < ix + spec.w; x++) tiles[y][x] = TileId.Floor;
  if (spec.edge) {
    const k = spec.edge.keepClearTiles;
    const keep: Rect[] = [
      { x: spawn.x - k, y: spawn.y - k, w: k * 2 + 1, h: k * 2 + 1 },
      { x: exit.x - k, y: exit.y - k, w: k * 2 + 2, h: k * 2 + 2 },
      ...(spec.keepClear ?? []),
    ];
    carveEdge(tiles, interior, spec.edge, keep, new Rng(hashSeed(`${spec.seed ?? 0}:edge`)));
  } else {
    // 48라운드 사각 벽
    for (let y = iy - 1; y <= iy + spec.h; y++)
      for (let x = ix - 1; x <= ix + spec.w; x++) if (tiles[y][x] === TileId.Void) tiles[y][x] = TileId.Wall;
  }

  const room: Room = {
    id: spec.roomId,
    type: spec.type,
    floor: spec.floor,
    cells: [{ cx: 0, cy: 0 }],
    interior,
    doors: [],
  };
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
      spawn,
      exit,
      shop,
      center,
      camera: { x: ix - 1, y: iy - 1, w: spec.w + 2, h: spec.h + 2 },
    },
  };
}

/** 깊이 프로필: 길이 n, 값 0..max, run 칸마다 ±1~2 로 바뀌는 계단 */
export function insetProfile(rng: Rng, n: number, max: number, run: [number, number]): number[] {
  const out: number[] = [];
  let d = rng.int(0, max);
  while (out.length < n) {
    const len = rng.int(run[0], run[1]);
    for (let i = 0; i < len && out.length < n; i++) out.push(d);
    const step = rng.int(1, 2) * (rng.chance(0.5) ? 1 : -1);
    d = Math.max(0, Math.min(max, d + step));
  }
  return out;
}

/**
 * 가장자리 깎기: 네 변마다 깊이 프로필만큼 내부 바닥을 비우고(keep 안은 보존), 바닥에 8방향으로 닿는 빈 칸을 벽으로.
 * 그다음 위·아래 변의 벽 일부를 열린 틈(void)으로 되돌린다. 틈은 바닥 경계 바로 바깥 한 줄이며 런타임에 충돌한다.
 */
function carveEdge(tiles: TileId[][], I: Rect, E: ArenaEdge, keep: readonly Rect[], rng: Rng): void {
  const inKeep = (x: number, y: number) => keep.some((r) => x >= r.x && x < r.x + r.w && y >= r.y && y < r.y + r.h);
  const top = insetProfile(rng, I.w, E.maxInset, E.run);
  const bottom = insetProfile(rng, I.w, E.maxInset, E.run);
  const left = insetProfile(rng, I.h, E.maxInset, E.run);
  const right = insetProfile(rng, I.h, E.maxInset, E.run);
  for (let y = I.y; y < I.y + I.h; y++)
    for (let x = I.x; x < I.x + I.w; x++) {
      const i = x - I.x;
      const j = y - I.y;
      const cut = j < top[i] || I.h - 1 - j < bottom[i] || i < left[j] || I.w - 1 - i < right[j];
      if (cut && !inKeep(x, y)) tiles[y][x] = TileId.Void;
    }
  // 모서리에서 두 변의 깊이가 엇갈려 떨어져 나간 바닥 조각은 비운다 (중앙에서 4방향으로 닿는 바닥만 남김)
  pruneUnreachable(tiles, arenaCenter(I));
  // 바닥에 8방향으로 닿는 빈 칸 = 벽 (담·잔해·건물 앞면)
  const H = tiles.length;
  const W = tiles[0].length;
  const touchesFloor = (x: number, y: number) => {
    for (let oy = -1; oy <= 1; oy++)
      for (let ox = -1; ox <= 1; ox++) if (tiles[y + oy]?.[x + ox] === TileId.Floor) return true;
    return false;
  };
  for (let y = 0; y < H; y++)
    for (let x = 0; x < W; x++) if (tiles[y][x] === TileId.Void && touchesFloor(x, y)) tiles[y][x] = TileId.Wall;
  // 열린 틈: 위·아래 변, 모서리·keep 열을 피해서
  const nGaps = rng.int(E.gaps[0], E.gaps[1]);
  const used: { side: number; x0: number; x1: number }[] = [];
  for (let g = 0; g < nGaps; g++) {
    for (let t = 0; t < 20; t++) {
      const side = rng.int(0, 1); // 0 위 · 1 아래
      const gw = rng.int(E.gapWidth[0], E.gapWidth[1]);
      const lo = I.x + E.cornerMarginTiles;
      const hi = I.x + I.w - E.cornerMarginTiles - gw;
      if (hi < lo) break;
      const x0 = rng.int(lo, hi);
      const x1 = x0 + gw - 1;
      if (used.some((u) => u.side === side && x0 <= u.x1 + 2 && x1 >= u.x0 - 2)) continue;
      let ok = true;
      const cells: { x: number; y: number }[] = [];
      for (let x = x0; x <= x1 && ok; x++) {
        // 그 열에서 바닥 경계 바로 바깥 벽 칸 (위 = 첫 바닥 위, 아래 = 마지막 바닥 아래)
        let fy = -1;
        if (side === 0) {
          for (let y = I.y; y < I.y + I.h; y++)
            if (tiles[y][x] === TileId.Floor) {
              fy = y - 1;
              break;
            }
        } else {
          for (let y = I.y + I.h - 1; y >= I.y; y--)
            if (tiles[y][x] === TileId.Floor) {
              fy = y + 1;
              break;
            }
        }
        if (fy < 0 || tiles[fy][x] !== TileId.Wall || inKeep(x, fy)) ok = false;
        else cells.push({ x, y: fy });
      }
      if (!ok || cells.length === 0) continue;
      for (const c of cells) tiles[c.y][c.x] = TileId.Void;
      used.push({ side, x0, x1 });
      break;
    }
  }
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

function pruneUnreachable(tiles: TileId[][], from: { x: number; y: number }): void {
  const ok = reachableFloor(tiles, from);
  for (let y = 0; y < tiles.length; y++)
    for (let x = 0; x < tiles[y].length; x++)
      if (tiles[y][x] === TileId.Floor && !ok.has(`${x},${y}`)) tiles[y][x] = TileId.Void;
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
