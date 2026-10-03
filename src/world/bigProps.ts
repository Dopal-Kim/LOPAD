/**
 * 52라운드 Q11 · 계약 art §12·§14: 쿼터뷰 타일셋의 큰 소품(`bigProps`) 배치. Phaser 의존 없음 · 시드 결정적.
 * 그림·충돌·광원은 QuarterView / TileWorld. 힌트 → 규칙은 `bigPropRules`, 빈 칸·길 보장 검사는 `bigPropGrid`.
 *
 * 규칙별 자리 (수치는 QUARTER.BIG_PROPS, 임시값):
 * - north  : 북쪽 벽 앞(바로 북쪽이 벽인 첫 바닥 줄)에 간격을 두고 (같은 규칙 소품끼리 번갈아, 합계 상한)
 * - ring   : 광장 중앙 둘레 고리 (화로)
 * - corner : 구석 (아래쪽 구석부터), 소품마다 1
 * - cover  : 서·동 벽가, 소품마다 최대 CRATE_MAX (피하는 쪽 벽은 빼고)
 * - exit   : 출구 좌우 한 짝 (Q69 '문·길 양옆')
 * - column : 서·동 벽가 세로, 쪽마다 COLUMN_PER_SIDE (Q69 '측면 세로')
 * - mirror : 가운데 세로 축 좌우 대칭 짝 MIRROR_PAIRS (Q69 '내부 장애물 대칭')
 * - table  : column 으로 놓인 탁자 끝·옆 (Q69 '탁자 끝·단상 양옆')
 * 한 규칙에서 하나도 못 놓은 소품은 다음 규칙으로 넘어간다(규칙 순서와 상관없이 — 단계 묶음을 규칙 수만큼 되풀이).
 * `avoidNearBorder`(테두리 그림에 같은 물건이 있는 쪽): 그쪽 바닥 끝에서 AVOID_BORDER_TILES 칸 안에 발자국이 걸치지 않게.
 * 적 생성 지점은 막힌 칸을 피하므로(TileWorld.isWalkableAt) 따로 볼 필요가 없다.
 */
import { QUARTER } from '../core/Constants';
import { Rng, hashSeed } from '../systems/rng';
import { TileId, type FloorLayout } from '../systems/mapgen';
import { PropGrid, type BigPropPlacement } from './bigPropGrid';
import { bigPropRules, type BigPropRule, type BigPropShape } from './bigPropRules';

export { bigPropRules, type BigPropRule, type BigPropShape } from './bigPropRules';
export type { BigPropPlacement } from './bigPropGrid';

interface Ctx {
  grid: PropGrid;
  rng: Rng;
  layout: FloorLayout;
  I: { x: number; y: number; w: number; h: number };
  /** column 규칙으로 놓인 탁자 (table 규칙의 기준) */
  anchors: BigPropPlacement[];
}

type Step = (ctx: Ctx, shapes: BigPropShape[]) => Set<BigPropShape>;

/** 단계 순서: 자리가 좁은 것(출구 좌우·벽가 세로)부터, 탁자 옆은 탁자 뒤 */
const STEPS: [BigPropRule, Step][] = [
  ['exit', stepExit],
  ['column', stepColumn],
  ['north', stepNorth],
  ['ring', stepRing],
  ['mirror', stepMirror],
  ['corner', stepCorner],
  ['cover', stepCover],
  ['table', stepTable],
];

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
  const room = layout.rooms[0];
  if (!room || !layout.arena) return [];
  const I = room.interior;
  const ctx: Ctx = {
    grid: new PropGrid(layout, blocked, reserved, I),
    rng: new Rng(hashSeed(`${String(seed)}:bigprops`)),
    layout,
    I,
    anchors: [],
  };
  // 규칙별 소품 (JSON 순서). 앞 규칙에서 하나도 못 놓은 소품은 다음 규칙으로
  const queue = shapes
    .filter((s) => Array.isArray(s.footprint) && s.footprint[0] > 0 && s.footprint[1] > 0)
    .map((s) => ({ s, rules: bigPropRules(s) }));
  const passes = Math.max(0, ...queue.map((e) => e.rules.length));
  for (let pass = 0; pass < passes; pass++)
    for (const [rule, step] of STEPS) {
      const mine = queue.filter((e) => e.rules[0] === rule);
      if (mine.length === 0) continue;
      const placed = step(
        ctx,
        mine.map((e) => e.s),
      );
      for (const e of mine) e.rules = placed.has(e.s) ? [] : e.rules.slice(1);
    }
  return ctx.grid.out;
}

/** 출구 좌우: 출구 2×2 아래 줄(→ 윗줄)에 EXIT_SIDE_GAP_TILES 만큼 띄워 한 짝 */
function stepExit({ grid, layout }: Ctx, shapes: BigPropShape[]): Set<BigPropShape> {
  const B = QUARTER.BIG_PROPS;
  const E = layout.arena!.exit;
  const done = new Set<BigPropShape>();
  for (const s of shapes) {
    const [w] = s.footprint;
    const h = s.footprint[1];
    search: for (let gap = B.EXIT_SIDE_GAP_TILES[0]; gap <= B.EXIT_SIDE_GAP_TILES[1]; gap++)
      for (const row of [E.y + 1, E.y]) {
        const y = row - (h - 1);
        const pair = [
          { s, x: E.x - gap - w, y },
          { s, x: E.x + 2 + gap, y },
        ];
        if (grid.tryPlace(pair, { overExitZone: true })) {
          done.add(s);
          break search;
        }
      }
  }
  return done;
}

/** 서·동 벽가 세로: 쪽마다 COLUMN_PER_SIDE, 벽에 붙여 (세로 자리는 시드로 섞어 차례로) */
function stepColumn(ctx: Ctx, shapes: BigPropShape[]): Set<BigPropShape> {
  const B = QUARTER.BIG_PROPS;
  const { grid, rng, I } = ctx;
  const done = new Set<BigPropShape>();
  for (const s of shapes) {
    const [w, h] = s.footprint;
    for (const side of wallSides(s)) {
      const ys: number[] = [];
      for (let y = I.y + B.NORTH_KEEP_TILES; y + h - 1 <= I.y + I.h - 1; y++) ys.push(y);
      shuffle(rng, ys);
      let n = 0;
      for (const y of ys) {
        if (n >= B.COLUMN_PER_SIDE) break;
        const x = wallX(ctx, side, y, w, h);
        if (x === null || !grid.tryPlace([{ s, x, y }])) continue;
        ctx.anchors.push(grid.out[grid.out.length - 1]);
        done.add(s);
        n++;
      }
    }
  }
  return done;
}

/** 북쪽 벽 앞: 첫 바닥 줄, 간격 LAMP_SPACING, 같은 규칙 소품끼리 번갈아 합계 LAMP_MAX */
function stepNorth({ grid, rng, layout, I }: Ctx, north: BigPropShape[]): Set<BigPropShape> {
  const B = QUARTER.BIG_PROPS;
  const done = new Set<BigPropShape>();
  const cand: { x: number; y: number }[] = [];
  for (let x = I.x + 1; x < I.x + I.w - 1; x++)
    for (let y = I.y; y < I.y + B.NORTH_SEARCH_TILES; y++)
      if (grid.isFloor(x, y) && layout.tiles[y - 1]?.[x] === TileId.Wall) {
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
      if (!grid.tryPlace([{ s, x: c.x, y: c.y }])) continue;
      done.add(s);
      lastX = c.x;
      lastW = s.footprint[0];
      turn = (turn + k + 1) % north.length;
      n++;
      break;
    }
  }
  return done;
}

/** 화로: 광장 (중앙 둘레 고리) — 못 놓아도 다음 규칙으로 넘기지 않는다 */
function stepRing({ grid, rng, layout, I }: Ctx, shapes: BigPropShape[]): Set<BigPropShape> {
  const B = QUARTER.BIG_PROPS;
  const A = layout.arena!;
  for (const s of shapes) {
    const c = A.center ?? { x: I.x + Math.floor(I.w / 2), y: I.y + Math.floor(I.h / 2) };
    const want = rng.int(B.BRAZIER_COUNT[0], B.BRAZIER_COUNT[1]);
    const base = rng.next() * Math.PI * 2;
    let n = 0;
    for (let i = 0; i < B.BRAZIER_TRIES && n < want; i++) {
      const a = base + (Math.PI * 2 * i) / B.BRAZIER_TRIES + (n > 0 ? Math.PI : 0);
      const r = B.BRAZIER_RING[0] + (B.BRAZIER_RING[1] - B.BRAZIER_RING[0]) * rng.next();
      const x = Math.round(c.x + Math.cos(a) * r * B.BRAZIER_X_STRETCH);
      const y = Math.round(c.y + Math.sin(a) * r);
      if (grid.tryPlace([{ s, x, y }])) n++;
    }
  }
  return new Set(shapes);
}

/** 가운데 세로 축 좌우 대칭 짝: 왼쪽 자리를 시드로 고르고 거울 자리와 함께 (둘 다 되어야) */
function stepMirror({ grid, rng, I }: Ctx, shapes: BigPropShape[]): Set<BigPropShape> {
  const B = QUARTER.BIG_PROPS;
  const done = new Set<BigPropShape>();
  const e = grid.edge;
  for (const s of shapes) {
    const [w, h] = s.footprint;
    let n = 0;
    for (let i = 0; i < B.MIRROR_TRIES && n < B.MIRROR_PAIRS; i++) {
      const dx = Math.round(I.w * (B.MIRROR_DX_FRAC[0] + (B.MIRROR_DX_FRAC[1] - B.MIRROR_DX_FRAC[0]) * rng.next()));
      const y = rng.int(
        e.north + B.MIRROR_EDGE_TILES,
        Math.max(e.north + B.MIRROR_EDGE_TILES, e.south - B.MIRROR_EDGE_TILES - h + 1),
      );
      // 축 = 내부 가운데. 왼쪽 소품의 오른쪽 끝이 축에서 dx 칸
      const x = Math.floor(I.x + I.w / 2) - dx - w;
      const mx = mirrorX(I, x, w);
      if (mx <= x + w) continue;
      if (
        grid.tryPlace([
          { s, x, y },
          { s, x: mx, y },
        ])
      )
        n++;
    }
    if (n > 0) done.add(s);
  }
  return done;
}

/** 구석 (아래 먼저): 소품마다 1개 */
function stepCorner({ grid, rng, I }: Ctx, shapes: BigPropShape[]): Set<BigPropShape> {
  const B = QUARTER.BIG_PROPS;
  const inset = B.CORNER_INSET_TILES;
  const corners = [
    { x: I.x + inset, y: I.y + I.h - 1 - inset, dx: 1, dy: -1 },
    { x: I.x + I.w - 1 - inset, y: I.y + I.h - 1 - inset, dx: -1, dy: -1 },
    { x: I.x + inset, y: I.y + inset + B.NORTH_KEEP_TILES, dx: 1, dy: 1 },
    { x: I.x + I.w - 1 - inset, y: I.y + inset + B.NORTH_KEEP_TILES, dx: -1, dy: 1 },
  ];
  const bottom = rng.chance(0.5) ? [0, 1] : [1, 0];
  const order = [...bottom, 2, 3].map((i) => corners[i]);
  const done = new Set<BigPropShape>();
  for (const s of shapes) {
    const [w] = s.footprint;
    let ok = false;
    for (const k of order) {
      for (let step = 0; step < B.CORNER_SEARCH_TILES && !ok; step++) {
        const x = k.dx > 0 ? k.x + step : k.x - step - (w - 1);
        const y = k.y + Math.floor(step / 2) * k.dy;
        ok = grid.tryPlace([{ s, x, y }]);
      }
      if (ok) break;
    }
    if (ok) done.add(s);
  }
  return done;
}

/** 서·동 벽가 (엄폐): 소품마다 최대 CRATE_MAX, 피하는 쪽 벽은 빼고 */
function stepCover(ctx: Ctx, shapes: BigPropShape[]): Set<BigPropShape> {
  const B = QUARTER.BIG_PROPS;
  const { grid, rng, I } = ctx;
  const done = new Set<BigPropShape>();
  for (const s of shapes) {
    const sides = wallSides(s);
    if (sides.length === 0) continue;
    const [w] = s.footprint;
    let n = 0;
    for (let i = 0; i < B.CRATE_TRIES && n < B.CRATE_MAX; i++) {
      const west = sides.length === 2 ? rng.chance(0.5) : sides[0] === 'west';
      const y = rng.int(I.y + B.NORTH_KEEP_TILES, I.y + I.h - 2);
      const x = wallX(ctx, west ? 'west' : 'east', y, w, 1);
      if (x !== null && grid.tryPlace([{ s, x, y }])) n++;
    }
    if (n > 0) done.add(s);
  }
  return done;
}

/** 탁자 옆: column 으로 놓인 탁자마다 TABLE_SIDE_PER_ANCHOR (끝 남 → 끝 북 → 안쪽 옆, 둘레 1칸 띄움) */
function stepTable({ grid, anchors, I }: Ctx, shapes: BigPropShape[]): Set<BigPropShape> {
  const B = QUARTER.BIG_PROPS;
  const done = new Set<BigPropShape>();
  const midX = I.x + I.w / 2;
  for (const t of anchors)
    for (const s of shapes) {
      const [w, h] = s.footprint;
      const inward = t.tx + t.w / 2 < midX ? 1 : -1;
      // 탁자 안쪽(방 가운데 쪽) 끝 칸에 맞춰
      const endX = inward > 0 ? t.tx + t.w - w : t.tx;
      const cand = [
        { x: endX, y: t.ty + t.h + 1 },
        { x: endX, y: t.ty - 1 - h },
        { x: inward > 0 ? t.tx + t.w + 1 : t.tx - 1 - w, y: t.ty + Math.floor((t.h - h) / 2) },
      ];
      let n = 0;
      for (const c of cand) {
        if (n >= B.TABLE_SIDE_PER_ANCHOR) break;
        if (grid.tryPlace([{ s, x: c.x, y: c.y }])) {
          done.add(s);
          n++;
        }
      }
    }
  return done;
}

/** 소품이 놓일 수 있는 서·동 벽 (avoidNearBorder 쪽은 빼고) */
function wallSides(s: BigPropShape): ('west' | 'east')[] {
  return (['west', 'east'] as const).filter((d) => !(s.avoidNearBorder ?? []).includes(d));
}

/** 서·동 벽에 붙는 발자국 왼쪽 x (rows h 줄이 다 바닥인 가장 바깥 열), 없으면 null */
function wallX({ grid, I }: Ctx, side: 'west' | 'east', y: number, w: number, h: number): number | null {
  let edge = side === 'west' ? -Infinity : Infinity;
  for (let yy = y; yy < y + h; yy++) {
    let x = side === 'west' ? I.x : I.x + I.w - 1;
    while (x > I.x - 1 && x < I.x + I.w && !grid.isFloor(x, yy)) x += side === 'west' ? 1 : -1;
    if (x <= I.x - 1 || x >= I.x + I.w) return null;
    edge = side === 'west' ? Math.max(edge, x) : Math.min(edge, x);
  }
  return side === 'west' ? edge : edge - (w - 1);
}

/** 내부 가운데 세로 축 거울 자리 (발자국 왼쪽 x) */
export function mirrorX(I: { x: number; w: number }, x: number, w: number): number {
  return 2 * I.x + I.w - x - w;
}

function shuffle<T>(rng: Rng, a: T[]): void {
  for (let i = a.length - 1; i > 0; i--) {
    const j = rng.int(0, i);
    [a[i], a[j]] = [a[j], a[i]];
  }
}
