/**
 * 큰 소품 배치 격자 (Phaser 없음): 빈 칸·테두리 회피·길 보장 검사와 놓기. 규칙별 자리 고르기는 `bigProps.planBigProps`.
 *
 * 피하는 칸: 이미 막힌 칸(구조물·세트 소품) · 예약 칸(양조 다리) · 시작점·상점 둘레 · 출구 둘레(출구 좌우 규칙만 넘음) ·
 * 문(벽의 열린 틈) 앞 · 다른 큰 소품 둘레 1칸. 놓을 때마다 바닥이 한 덩어리로 이어지는지 확인한다(플레이어 길 보장).
 * 걷기 통과 소품(solid: false)도 자리·둘레 간격은 똑같이 차지하지만, 길 보장 검사에서는 막힌 칸으로 세지 않는다.
 */
import { QUARTER } from '../core/Constants';
import { TileId, type FloorLayout } from '../systems/mapgen';
import type { BigPropShape } from './bigPropRules';

export interface BigPropPlacement {
  name: string;
  /** 발자국 왼쪽 위 칸 */
  tx: number;
  ty: number;
  /** 발자국 크기 (칸) */
  w: number;
  h: number;
  /** 걷기 막힘 여부 (아트 JSON solid: false 면 false — 통과) */
  solid: boolean;
}

export type Side = 'north' | 'south' | 'west' | 'east';

export interface PropAt {
  s: BigPropShape;
  x: number;
  y: number;
}

export const tileKey = (x: number, y: number) => `${x},${y}`;

const DIR4: readonly [number, number][] = [
  [1, 0],
  [-1, 0],
  [0, 1],
  [0, -1],
];

export class PropGrid {
  readonly out: BigPropPlacement[] = [];
  /** 방 안 바닥 칸의 바깥 경계 (테두리 기준선) */
  readonly edge: Record<Side, number>;
  private readonly taken: Set<string>;
  /** 출구 둘레 비움 (출구 좌우 규칙만 넘는다) */
  private readonly exitZone = new Set<string>();
  /** 큰 소품이 놓인 칸 (둘레 1칸 간격용 — 통과 소품 포함) */
  private readonly occupied = new Set<string>();
  /** 걷기를 막는 큰 소품 칸 (길 보장 검사용) */
  private readonly walkBlocked = new Set<string>();

  constructor(
    readonly layout: FloorLayout,
    private readonly blocked: ReadonlySet<string>,
    reserved: ReadonlySet<string>,
    readonly interior: { x: number; y: number; w: number; h: number },
  ) {
    const B = QUARTER.BIG_PROPS;
    this.taken = new Set([...blocked, ...reserved]);
    this.edge = floorEdges(layout, interior);
    const A = layout.arena;
    if (A) {
      this.clearAround(this.taken, A.spawn.x, A.spawn.y, 1, 1, B.CLEAR_TILES);
      this.clearAround(this.exitZone, A.exit.x, A.exit.y, 2, 2, B.CLEAR_TILES);
      this.clearAround(this.taken, A.shop.x, A.shop.y, 2, 2, B.CLEAR_TILES);
    }
    for (const d of doorMouths(layout)) this.clearAround(this.taken, d.x, d.y, 1, 1, B.DOOR_CLEAR_TILES);
  }

  isFloor(x: number, y: number): boolean {
    return this.layout.tiles[y]?.[x] === TileId.Floor;
  }

  /** 놓아 보고 되면 전부 놓는다 (짝은 둘 다 되거나 둘 다 안 됨) */
  tryPlace(items: readonly PropAt[], opts: { overExitZone?: boolean } = {}): boolean {
    const extra = new Set<string>();
    const extraBlocked = new Set<string>();
    for (const { s, x, y } of items) {
      const [w, h] = s.footprint;
      if (this.nearAvoided(s, x, y, w, h) || !this.fits(x, y, w, h, opts.overExitZone ?? false)) return false;
      // 같은 묶음끼리도 둘레 1칸
      for (let yy = y - 1; yy <= y + h; yy++)
        for (let xx = x - 1; xx <= x + w; xx++) if (extra.has(tileKey(xx, yy))) return false;
      for (let yy = y; yy < y + h; yy++)
        for (let xx = x; xx < x + w; xx++) {
          extra.add(tileKey(xx, yy));
          if (isSolid(s)) extraBlocked.add(tileKey(xx, yy));
        }
    }
    const isBlocked = (cx: number, cy: number) => {
      const k = tileKey(cx, cy);
      return this.walkBlocked.has(k) || extraBlocked.has(k) || this.blocked.has(k);
    };
    if (extraBlocked.size > 0 && !floorConnected(this.layout, isBlocked)) return false;
    for (const { s, x, y } of items) {
      const [w, h] = s.footprint;
      const solid = isSolid(s);
      for (let yy = y; yy < y + h; yy++)
        for (let xx = x; xx < x + w; xx++) {
          this.occupied.add(tileKey(xx, yy));
          this.taken.add(tileKey(xx, yy));
          if (solid) this.walkBlocked.add(tileKey(xx, yy));
        }
      this.out.push({ name: s.name, tx: x, ty: y, w, h, solid });
    }
    return true;
  }

  private clearAround(set: Set<string>, cx: number, cy: number, w: number, h: number, r: number): void {
    for (let y = cy - r; y < cy + h + r; y++) for (let x = cx - r; x < cx + w + r; x++) set.add(tileKey(x, y));
  }

  /** 테두리 회피: 그쪽 바닥 끝에서 AVOID_BORDER_TILES 칸 안에 발자국이 걸치는지 */
  private nearAvoided(s: BigPropShape, x: number, y: number, w: number, h: number): boolean {
    const n = QUARTER.BIG_PROPS.AVOID_BORDER_TILES;
    const e = this.edge;
    for (const side of s.avoidNearBorder ?? []) {
      if (side === 'north' && y < e.north + n) return true;
      if (side === 'south' && y + h - 1 > e.south - n) return true;
      if (side === 'west' && x < e.west + n) return true;
      if (side === 'east' && x + w - 1 > e.east - n) return true;
    }
    return false;
  }

  /** 발자국이 다 바닥이고 비어 있으며, 둘레 1칸에 다른 큰 소품이 없는지 */
  private fits(x: number, y: number, w: number, h: number, overExitZone: boolean): boolean {
    for (let yy = y; yy < y + h; yy++)
      for (let xx = x; xx < x + w; xx++) {
        const k = tileKey(xx, yy);
        if (!this.isFloor(xx, yy) || this.taken.has(k) || (!overExitZone && this.exitZone.has(k))) return false;
      }
    for (let yy = y - 1; yy <= y + h; yy++)
      for (let xx = x - 1; xx <= x + w; xx++) if (this.occupied.has(tileKey(xx, yy))) return false;
    return true;
  }
}

/** 아트 JSON solid 가 false 일 때만 통과 (없거나 true 면 막힘) */
export const isSolid = (s: Pick<BigPropShape, 'solid'>): boolean => s.solid !== false;

/** 문 앞 = 4방향으로 빈 칸(벽의 열린 틈 · 원경 void)에 닿는 바닥 칸 */
export function doorMouths(layout: FloorLayout): { x: number; y: number }[] {
  const out: { x: number; y: number }[] = [];
  for (let y = 0; y < layout.heightTiles; y++)
    for (let x = 0; x < layout.widthTiles; x++)
      if (
        layout.tiles[y][x] === TileId.Floor &&
        DIR4.some(([dx, dy]) => (layout.tiles[y + dy]?.[x + dx] ?? TileId.Void) === TileId.Void)
      )
        out.push({ x, y });
  return out;
}

/** 방 안 바닥 칸의 바깥 경계 (테두리 기준선 = 각 쪽 바닥 끝 칸). 바닥이 없으면 방 경계 */
function floorEdges(layout: FloorLayout, I: { x: number; y: number; w: number; h: number }): Record<Side, number> {
  let north = Infinity;
  let south = -Infinity;
  let west = Infinity;
  let east = -Infinity;
  for (let y = I.y; y < I.y + I.h; y++)
    for (let x = I.x; x < I.x + I.w; x++)
      if (layout.tiles[y]?.[x] === TileId.Floor) {
        north = Math.min(north, y);
        south = Math.max(south, y);
        west = Math.min(west, x);
        east = Math.max(east, x);
      }
  if (!Number.isFinite(north)) return { north: I.y, south: I.y + I.h - 1, west: I.x, east: I.x + I.w - 1 };
  return { north, south, west, east };
}

/** 바닥(막힌 칸 빼고)이 한 덩어리인지 */
export function floorConnected(layout: FloorLayout, isBlocked: (x: number, y: number) => boolean): boolean {
  const open = (x: number, y: number) => layout.tiles[y]?.[x] === TileId.Floor && !isBlocked(x, y);
  let start: [number, number] | null = null;
  let total = 0;
  for (let y = 0; y < layout.heightTiles; y++)
    for (let x = 0; x < layout.widthTiles; x++)
      if (open(x, y)) {
        total++;
        start ??= [x, y];
      }
  if (!start) return true;
  const seen = new Set<string>([tileKey(...start)]);
  const stack = [start];
  while (stack.length > 0) {
    const [x, y] = stack.pop()!;
    for (const [dx, dy] of DIR4) {
      const nx = x + dx;
      const ny = y + dy;
      const k = tileKey(nx, ny);
      if (seen.has(k) || !open(nx, ny)) continue;
      seen.add(k);
      stack.push([nx, ny]);
    }
  }
  return seen.size === total;
}
