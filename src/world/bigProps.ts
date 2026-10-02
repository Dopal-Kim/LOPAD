/**
 * 52라운드 Q11 · 계약 art §12: 쿼터뷰 타일셋의 큰 소품(`bigProps` — 가로등·좌판·우물·상자 더미, + 화로 소품) 배치 규칙.
 * Phaser 의존 없음 · 시드 결정적. 그림·충돌·광원은 QuarterView / TileWorld.
 *
 * 규칙 (수치는 QUARTER.BIG_PROPS, 임시값):
 * - 가로등: 북쪽 벽 앞(바로 북쪽이 벽인 첫 바닥 줄)에 간격을 두고
 * - 화로: 광장(전투장 중앙 둘레 고리)에 1~2개
 * - 우물·좌판: 아래쪽 구석(남서·남동)부터, 나머지는 위쪽 구석
 * - 상자 더미: 서·동 벽가에
 * 피하는 칸: 이미 막힌 칸(구조물·세트 소품) · 시작점·출구·상점 둘레 · 다른 큰 소품 둘레 1칸. 놓을 때마다 바닥 연결을 확인하고
 * 길을 끊으면 놓지 않는다 (플레이어 길 보장). 적 생성 지점은 막힌 칸을 피하므로(TileWorld.isWalkableAt) 따로 볼 필요가 없다.
 */
import { QUARTER } from '../core/Constants';
import { Rng, hashSeed } from '../systems/rng';
import { TileId, type FloorLayout } from '../systems/mapgen';

export interface BigPropPlacement {
  name: string;
  /** 발자국 왼쪽 위 칸 */
  tx: number;
  ty: number;
  /** 발자국 크기 (칸) */
  w: number;
  h: number;
}

export interface BigPropShape {
  name: string;
  footprint: [number, number];
}

const key = (x: number, y: number) => `${x},${y}`;

/**
 * 큰 소품 배치. `shapes` = 쓸 수 있는 소품(이름·발자국), `blocked` = 이미 막힌 칸(`"x,y"`).
 * 쓸 수 있는 이름: lamp_post · brazier · well · stall · crate_stack (없는 이름은 건너뛴다)
 */
export function planBigProps(
  layout: FloorLayout,
  shapes: readonly BigPropShape[],
  blocked: ReadonlySet<string>,
  seed: number | string,
): BigPropPlacement[] {
  const B = QUARTER.BIG_PROPS;
  const room = layout.rooms[0];
  if (!room || !layout.arena) return [];
  const rng = new Rng(hashSeed(`${String(seed)}:bigprops`));
  const shape = new Map(shapes.map((s) => [s.name, s]));
  const I = room.interior;
  const taken = new Set(blocked);
  // 시작점·출구·상점 둘레 비움
  const A = layout.arena;
  const clear = (cx: number, cy: number, w: number, h: number) => {
    const r = B.CLEAR_TILES;
    for (let y = cy - r; y < cy + h + r; y++) for (let x = cx - r; x < cx + w + r; x++) taken.add(key(x, y));
  };
  clear(A.spawn.x, A.spawn.y, 1, 1);
  clear(A.exit.x, A.exit.y, 2, 2);
  clear(A.shop.x, A.shop.y, 2, 2);
  const isFloor = (x: number, y: number) => layout.tiles[y]?.[x] === TileId.Floor;
  const out: BigPropPlacement[] = [];
  const solid = new Set<string>();

  /** 발자국 + 둘레 1칸이 다 바닥이고 비어 있는지 (wallSide = 벽 쪽 둘레는 벽이어도 됨) */
  const fits = (x: number, y: number, w: number, h: number, ring: boolean): boolean => {
    for (let yy = y; yy < y + h; yy++)
      for (let xx = x; xx < x + w; xx++) if (!isFloor(xx, yy) || taken.has(key(xx, yy))) return false;
    if (!ring) return true;
    for (let yy = y - 1; yy <= y + h; yy++)
      for (let xx = x - 1; xx <= x + w; xx++) if (solid.has(key(xx, yy))) return false;
    return true;
  };
  /** 놓아도 바닥이 한 덩어리로 이어지는지 */
  const keepsPath = (x: number, y: number, w: number, h: number): boolean => {
    const extra = new Set<string>();
    for (let yy = y; yy < y + h; yy++) for (let xx = x; xx < x + w; xx++) extra.add(key(xx, yy));
    return floorConnected(
      layout,
      (cx, cy) => solid.has(key(cx, cy)) || extra.has(key(cx, cy)) || blocked.has(key(cx, cy)),
    );
  };
  const place = (name: string, x: number, y: number): boolean => {
    const s = shape.get(name);
    if (!s) return false;
    const [w, h] = s.footprint;
    if (!fits(x, y, w, h, true) || !keepsPath(x, y, w, h)) return false;
    for (let yy = y; yy < y + h; yy++)
      for (let xx = x; xx < x + w; xx++) {
        solid.add(key(xx, yy));
        taken.add(key(xx, yy));
      }
    out.push({ name, tx: x, ty: y, w, h });
    return true;
  };

  // 가로등: 북쪽 벽 앞 첫 바닥 줄, 간격 LAMP_SPACING
  if (shape.has('lamp_post')) {
    const cand: { x: number; y: number }[] = [];
    for (let x = I.x + 1; x < I.x + I.w - 1; x++)
      for (let y = I.y; y < I.y + B.NORTH_SEARCH_TILES; y++)
        if (isFloor(x, y) && layout.tiles[y - 1]?.[x] === TileId.Wall) {
          cand.push({ x, y });
          break;
        }
    let lastX = -Infinity;
    let n = 0;
    const offset = rng.int(0, B.LAMP_SPACING - 1);
    for (const c of cand) {
      if (n >= B.LAMP_MAX) break;
      if (c.x - I.x < offset || c.x - lastX < B.LAMP_SPACING) continue;
      if (place('lamp_post', c.x, c.y)) {
        lastX = c.x;
        n++;
      }
    }
  }
  // 화로: 광장 (중앙 둘레 고리)
  if (shape.has('brazier')) {
    const c = A.center ?? { x: I.x + Math.floor(I.w / 2), y: I.y + Math.floor(I.h / 2) };
    const want = rng.int(B.BRAZIER_COUNT[0], B.BRAZIER_COUNT[1]);
    const base = rng.next() * Math.PI * 2;
    let n = 0;
    for (let i = 0; i < B.BRAZIER_TRIES && n < want; i++) {
      const a = base + (Math.PI * 2 * i) / B.BRAZIER_TRIES + (n > 0 ? Math.PI : 0);
      const r = B.BRAZIER_RING[0] + (B.BRAZIER_RING[1] - B.BRAZIER_RING[0]) * rng.next();
      const x = Math.round(c.x + Math.cos(a) * r * B.BRAZIER_X_STRETCH);
      const y = Math.round(c.y + Math.sin(a) * r);
      if (place('brazier', x, y)) n++;
    }
  }
  // 우물·좌판: 구석 (아래 먼저)
  const inset = B.CORNER_INSET_TILES;
  const corners = [
    { x: I.x + inset, y: I.y + I.h - 1 - inset, dx: 1, dy: -1 },
    { x: I.x + I.w - 1 - inset, y: I.y + I.h - 1 - inset, dx: -1, dy: -1 },
    { x: I.x + inset, y: I.y + inset + B.NORTH_KEEP_TILES, dx: 1, dy: 1 },
    { x: I.x + I.w - 1 - inset, y: I.y + inset + B.NORTH_KEEP_TILES, dx: -1, dy: 1 },
  ];
  const bottom = rng.chance(0.5) ? [0, 1] : [1, 0];
  const order = [...bottom, 2, 3].map((i) => corners[i]);
  for (const name of ['well', 'stall']) {
    const s = shape.get(name);
    if (!s) continue;
    const [w] = s.footprint;
    let done = false;
    for (const k of order) {
      for (let step = 0; step < B.CORNER_SEARCH_TILES && !done; step++) {
        const x = k.dx > 0 ? k.x + step : k.x - step - (w - 1);
        const y = k.y + Math.floor(step / 2) * k.dy;
        done = place(name, x, y);
      }
      if (done) break;
    }
  }
  // 상자 더미: 서·동 벽가
  if (shape.has('crate_stack')) {
    let n = 0;
    for (let i = 0; i < B.CRATE_TRIES && n < B.CRATE_MAX; i++) {
      const west = rng.chance(0.5);
      const y = rng.int(I.y + B.NORTH_KEEP_TILES, I.y + I.h - 2);
      let x = west ? I.x : I.x + I.w - 1;
      while (x > I.x - 1 && x < I.x + I.w && !isFloor(x, y)) x += west ? 1 : -1;
      if (place('crate_stack', x, y)) n++;
    }
  }
  return out;
}

/** 바닥(막힌 칸 빼고)이 한 덩어리인지 */
function floorConnected(layout: FloorLayout, isBlocked: (x: number, y: number) => boolean): boolean {
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
  const seen = new Set<string>([key(...start)]);
  const stack = [start];
  while (stack.length > 0) {
    const [x, y] = stack.pop()!;
    for (const [dx, dy] of [
      [1, 0],
      [-1, 0],
      [0, 1],
      [0, -1],
    ]) {
      const nx = x + dx;
      const ny = y + dy;
      const k = key(nx, ny);
      if (seen.has(k) || !open(nx, ny)) continue;
      seen.add(k);
      stack.push([nx, ny]);
    }
  }
  return seen.size === total;
}
