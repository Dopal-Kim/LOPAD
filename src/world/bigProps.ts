/**
 * 52라운드 Q11 · 계약 art §12·§14: 쿼터뷰 타일셋의 큰 소품(`bigProps`) 배치 규칙.
 * Phaser 의존 없음 · 시드 결정적. 그림·충돌·광원은 QuarterView / TileWorld.
 *
 * 53라운드 Q59: 지역별 이름 대신 아트 `placement` 힌트로 일반 규칙 (`bigPropRules`, 수치는 QUARTER.BIG_PROPS, 임시값):
 * - '벽 앞' → 북쪽 벽 앞(바로 북쪽이 벽인 첫 바닥 줄)에 간격을 두고 (같은 규칙 소품끼리 번갈아, 합계 상한)
 * - '가장자리'·'구석' → 구석 (아래쪽 구석부터) · '엄폐' → 서·동 벽가
 * - 힌트가 여럿이면 적힌 순서대로 시도 ('벽 앞·구석' = 북쪽 벽 앞에 못 놓으면 구석)
 * - 힌트에 규칙어가 없으면 기존 이름 규칙(가로등·화로·우물·좌판·상자 더미 — `LEGACY_RULES`), 그것도 없으면 놓지 않는다
 * - `avoidNearBorder`(테두리 그림에 같은 물건이 있는 쪽): 그쪽 바닥 끝에서 AVOID_BORDER_TILES 칸 안에 발자국이 걸치지 않게
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
  /** 계약 §14 아트 배치 힌트 ('floor (벽 앞)' 등) */
  placement?: string;
  /** 계약 §14: 테두리 그림에 같은 물건이 이미 있는 쪽 (north·south·west·east) */
  avoidNearBorder?: readonly string[];
}

/** 배치 규칙: 북쪽 벽 앞 · 광장 고리(화로) · 구석 · 서·동 벽가 */
export type BigPropRule = 'north' | 'ring' | 'corner' | 'cover';

type Side = 'north' | 'south' | 'west' | 'east';

const key = (x: number, y: number) => `${x},${y}`;

/**
 * 소품 하나의 규칙 목록 (앞이 우선). 힌트 속 규칙어(QUARTER.BIG_PROPS.HINTS)를 적힌 순서대로, 없으면 이름 규칙, 그것도 없으면 []
 */
export function bigPropRules(s: Pick<BigPropShape, 'name' | 'placement'>): BigPropRule[] {
  const B = QUARTER.BIG_PROPS;
  const hint = s.placement ?? '';
  const found: { rule: BigPropRule; at: number }[] = [];
  for (const [rule, words] of Object.entries(B.HINTS) as [BigPropRule, readonly string[]][]) {
    const at = Math.min(...words.map((w) => hint.indexOf(w)).filter((i) => i >= 0));
    if (Number.isFinite(at)) found.push({ rule, at });
  }
  if (found.length > 0) return found.sort((a, b) => a.at - b.at).map((f) => f.rule);
  const legacy = (B.LEGACY_RULES as Record<string, BigPropRule | undefined>)[s.name];
  return legacy ? [legacy] : [];
}

/**
 * 큰 소품 배치. `shapes` = 쓸 수 있는 소품(이름·발자국·힌트), `blocked` = 이미 막힌 칸(`"x,y"`).
 */
export function planBigProps(
  layout: FloorLayout,
  shapes: readonly BigPropShape[],
  blocked: ReadonlySet<string>,
  seed: number | string,
  /** 53라운드: 소품을 두지 않지만 걸을 수 있는 칸 (양조 수로 다리) */
  reserved: ReadonlySet<string> = new Set(),
): BigPropPlacement[] {
  const B = QUARTER.BIG_PROPS;
  const room = layout.rooms[0];
  if (!room || !layout.arena) return [];
  const rng = new Rng(hashSeed(`${String(seed)}:bigprops`));
  const I = room.interior;
  const taken = new Set([...blocked, ...reserved]);
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
  const edge = floorEdges(layout, I);
  const out: BigPropPlacement[] = [];
  const solid = new Set<string>();

  /** 테두리 회피: 그쪽 바닥 끝에서 AVOID_BORDER_TILES 칸 안에 발자국이 걸치는지 */
  const nearAvoided = (s: BigPropShape, x: number, y: number, w: number, h: number): boolean => {
    const n = B.AVOID_BORDER_TILES;
    for (const side of s.avoidNearBorder ?? []) {
      if (side === 'north' && y < edge.north + n) return true;
      if (side === 'south' && y + h - 1 > edge.south - n) return true;
      if (side === 'west' && x < edge.west + n) return true;
      if (side === 'east' && x + w - 1 > edge.east - n) return true;
    }
    return false;
  };
  /** 발자국이 다 바닥이고 비어 있으며, 둘레 1칸에 다른 큰 소품이 없는지 */
  const fits = (x: number, y: number, w: number, h: number): boolean => {
    for (let yy = y; yy < y + h; yy++)
      for (let xx = x; xx < x + w; xx++) if (!isFloor(xx, yy) || taken.has(key(xx, yy))) return false;
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
  const place = (s: BigPropShape, x: number, y: number): boolean => {
    const [w, h] = s.footprint;
    if (nearAvoided(s, x, y, w, h) || !fits(x, y, w, h) || !keepsPath(x, y, w, h)) return false;
    for (let yy = y; yy < y + h; yy++)
      for (let xx = x; xx < x + w; xx++) {
        solid.add(key(xx, yy));
        taken.add(key(xx, yy));
      }
    out.push({ name: s.name, tx: x, ty: y, w, h });
    return true;
  };

  // 규칙별 소품 (JSON 순서). 앞 규칙에서 하나도 못 놓은 소품은 다음 규칙으로 넘어간다
  const queue = shapes
    .map((s) => ({ s, rules: bigPropRules(s) }))
    .filter((e) => e.rules.length > 0 && Array.isArray(e.s.footprint) && e.s.footprint[0] > 0 && e.s.footprint[1] > 0);
  const pending = (rule: BigPropRule) => queue.filter((e) => e.rules[0] === rule);
  const settle = (rule: BigPropRule, placed: ReadonlySet<BigPropShape>) => {
    for (const e of queue) if (e.rules[0] === rule) e.rules = placed.has(e.s) ? [] : e.rules.slice(1);
  };
  const placedNorth = new Set<BigPropShape>();
  const placedCorner = new Set<BigPropShape>();
  const placedCover = new Set<BigPropShape>();

  // 1) 북쪽 벽 앞: 첫 바닥 줄, 간격 LAMP_SPACING, 같은 규칙 소품끼리 번갈아 합계 LAMP_MAX
  const north = pending('north').map((e) => e.s);
  if (north.length > 0) {
    const cand: { x: number; y: number }[] = [];
    for (let x = I.x + 1; x < I.x + I.w - 1; x++)
      for (let y = I.y; y < I.y + B.NORTH_SEARCH_TILES; y++)
        if (isFloor(x, y) && layout.tiles[y - 1]?.[x] === TileId.Wall) {
          cand.push({ x, y });
          break;
        }
    let lastX = -Infinity;
    let lastW = 1;
    let n = 0;
    let turn = 0;
    const offset = rng.int(0, B.LAMP_SPACING - 1);
    for (const c of cand) {
      if (n >= B.LAMP_MAX) break;
      if (c.x - I.x < offset || c.x - lastX < B.LAMP_SPACING + lastW - 1) continue;
      for (let k = 0; k < north.length; k++) {
        const s = north[(turn + k) % north.length];
        if (!place(s, c.x, c.y)) continue;
        placedNorth.add(s);
        lastX = c.x;
        lastW = s.footprint[0];
        turn = (turn + k + 1) % north.length;
        n++;
        break;
      }
    }
  }
  settle('north', placedNorth);
  // 2) 화로: 광장 (중앙 둘레 고리)
  for (const { s } of pending('ring')) {
    const c = A.center ?? { x: I.x + Math.floor(I.w / 2), y: I.y + Math.floor(I.h / 2) };
    const want = rng.int(B.BRAZIER_COUNT[0], B.BRAZIER_COUNT[1]);
    const base = rng.next() * Math.PI * 2;
    let n = 0;
    for (let i = 0; i < B.BRAZIER_TRIES && n < want; i++) {
      const a = base + (Math.PI * 2 * i) / B.BRAZIER_TRIES + (n > 0 ? Math.PI : 0);
      const r = B.BRAZIER_RING[0] + (B.BRAZIER_RING[1] - B.BRAZIER_RING[0]) * rng.next();
      const x = Math.round(c.x + Math.cos(a) * r * B.BRAZIER_X_STRETCH);
      const y = Math.round(c.y + Math.sin(a) * r);
      if (place(s, x, y)) n++;
    }
  }
  settle('ring', new Set(pending('ring').map((e) => e.s)));
  // 3) 구석 (아래 먼저): 소품마다 1개
  const inset = B.CORNER_INSET_TILES;
  const corners = [
    { x: I.x + inset, y: I.y + I.h - 1 - inset, dx: 1, dy: -1 },
    { x: I.x + I.w - 1 - inset, y: I.y + I.h - 1 - inset, dx: -1, dy: -1 },
    { x: I.x + inset, y: I.y + inset + B.NORTH_KEEP_TILES, dx: 1, dy: 1 },
    { x: I.x + I.w - 1 - inset, y: I.y + inset + B.NORTH_KEEP_TILES, dx: -1, dy: 1 },
  ];
  const bottom = rng.chance(0.5) ? [0, 1] : [1, 0];
  const order = [...bottom, 2, 3].map((i) => corners[i]);
  for (const { s } of pending('corner')) {
    const [w] = s.footprint;
    let done = false;
    for (const k of order) {
      for (let step = 0; step < B.CORNER_SEARCH_TILES && !done; step++) {
        const x = k.dx > 0 ? k.x + step : k.x - step - (w - 1);
        const y = k.y + Math.floor(step / 2) * k.dy;
        done = place(s, x, y);
      }
      if (done) break;
    }
    if (done) placedCorner.add(s);
  }
  settle('corner', placedCorner);
  // 4) 서·동 벽가 (엄폐): 소품마다 최대 CRATE_MAX, 피하는 쪽 벽은 빼고
  for (const { s } of pending('cover')) {
    const sides = (['west', 'east'] as const).filter((d) => !(s.avoidNearBorder ?? []).includes(d as Side));
    if (sides.length === 0) continue;
    let n = 0;
    for (let i = 0; i < B.CRATE_TRIES && n < B.CRATE_MAX; i++) {
      const west = sides.length === 2 ? rng.chance(0.5) : sides[0] === 'west';
      const y = rng.int(I.y + B.NORTH_KEEP_TILES, I.y + I.h - 2);
      let x = west ? I.x : I.x + I.w - 1;
      while (x > I.x - 1 && x < I.x + I.w && !isFloor(x, y)) x += west ? 1 : -1;
      if (!west) x -= s.footprint[0] - 1;
      if (place(s, x, y)) n++;
    }
    if (n > 0) placedCover.add(s);
  }
  settle('cover', placedCover);
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
