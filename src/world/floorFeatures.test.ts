import { describe, expect, it } from 'vitest';
import { ROUTE, type RouteNode } from '../systems/route';
import { planNodeArena } from '../systems/routeArena';
import { TileId, type FloorLayout } from '../systems/mapgen';
import { planBigProps } from './bigProps';
import { canalFromArena, planDecals, type CanalJson } from './floorFeatures';

const arena = (seed: string, col = 3) => {
  const n = {
    id: `c${col}r0`,
    kind: 'battle',
    type: 'battle',
    name: '',
    col,
    row: 0,
    links: [],
  } as unknown as RouteNode;
  return planNodeArena(n, 'stage1', seed, ROUTE, { border: () => true }).layout;
};

const canal: CanalJson = {
  frames: [64, 65, 66],
  framesLit: [69, 70, 71],
  frameMs: 180,
  bridge: { left: 67, right: 68 },
  litNearBridge: 2,
  walkable: false,
};

/** 막힌 칸을 빼고 바닥이 한 덩어리인지 */
function connected(L: FloorLayout, blocked: Set<string>): boolean {
  const open = (x: number, y: number) => L.tiles[y]?.[x] === TileId.Floor && !blocked.has(`${x},${y}`);
  const cells: [number, number][] = [];
  for (let y = 0; y < L.heightTiles; y++) for (let x = 0; x < L.widthTiles; x++) if (open(x, y)) cells.push([x, y]);
  const seen = new Set([`${cells[0][0]},${cells[0][1]}`]);
  const stack = [cells[0]];
  while (stack.length) {
    const [x, y] = stack.pop()!;
    for (const [dx, dy] of [
      [1, 0],
      [-1, 0],
      [0, 1],
      [0, -1],
    ]) {
      const k = `${x + dx},${y + dy}`;
      if (!seen.has(k) && open(x + dx, y + dy)) {
        seen.add(k);
        stack.push([x + dx, y + dy]);
      }
    }
  }
  return seen.size === cells.length;
}

describe('53라운드 4지역 바닥 특징 (데칼 · 양조 수로)', () => {
  it('P19 S2 수로 = 형태 틀 물 칸(빈 칸 — 걷기 막힘)·다리 칸(바닥), 다리 같은 줄 가까운 물은 밝은 판, 바닥 연결 유지', () => {
    for (const seed of ['a', 'b', 'c', 'd']) {
      const L = arena(seed, 5); // 양조 구역 전투 노드 — 부두·술창고·증류소 마당
      const plan = canalFromArena(L, canal)!;
      expect(plan).not.toBeNull();
      const A = L.arena!;
      const water = (A.drops ?? []).filter((d) => d.kind === 'water');
      expect(plan.tiles.filter((t) => t.kind === 'water' || t.kind === 'lit')).toHaveLength(water.length);
      for (const w of water) expect(L.tiles[w.y][w.x]).toBe(TileId.Void);
      for (const b of A.bridges ?? []) expect(L.tiles[b.y][b.x]).toBe(TileId.Floor);
      expect(plan.tiles.filter((t) => t.kind.startsWith('bridge'))).toHaveLength((A.bridges ?? []).length);
      expect(connected(L, new Set())).toBe(true);
      // 큰 소품은 다리에 놓이지 않는다
      const bridges = new Set((A.bridges ?? []).map((t) => `${t.x},${t.y}`));
      const big = planBigProps(L, [{ name: 'crate_stack', footprint: [1, 1] }], new Set(), seed, bridges);
      for (const b of big) expect(bridges.has(`${b.tx},${b.ty}`)).toBe(false);
    }
    // 물 칸이 없는 전투장(사각)은 수로 없음
    const n = { id: 'c6r0', kind: 'rest', type: 'rest', name: '', col: 6, row: 0, links: [] } as unknown as RouteNode;
    expect(canalFromArena(planNodeArena(n, 'stage1', 'x').layout, canal)).toBeNull();
  });

  it('데칼: 가운데 이름은 전투장 가운데 한 장, 나머지는 바닥 위·막힌 칸 밖·겹치지 않음·결정적', () => {
    const L = arena('x');
    const decals = [
      { name: 'cup_inlay', rect: { x: 0, y: 256, w: 128, h: 128 }, footprint: [4, 4] as [number, number] },
      { name: 'wine_trail', rect: { x: 128, y: 256, w: 64, h: 32 }, footprint: [2, 1] as [number, number] },
    ];
    const out = planDecals(L, decals, new Set(), 'x');
    expect(out).toEqual(planDecals(L, decals, new Set(), 'x'));
    const cup = out.filter((d) => d.name === 'cup_inlay');
    expect(cup).toHaveLength(1);
    const c = L.arena!.center!;
    expect(cup[0]).toMatchObject({ tx: c.x - 2, ty: c.y - 2 });
    const cells = new Set<string>();
    for (const d of out) {
      const [w, h] = decals.find((x) => x.name === d.name)!.footprint;
      for (let y = d.ty; y < d.ty + h; y++)
        for (let x = d.tx; x < d.tx + w; x++) {
          expect(L.tiles[y][x]).toBe(TileId.Floor);
          expect(cells.has(`${x},${y}`)).toBe(false);
          cells.add(`${x},${y}`);
        }
    }
    expect(planDecals(L, [], new Set(), 'x')).toEqual([]);
  });
});
