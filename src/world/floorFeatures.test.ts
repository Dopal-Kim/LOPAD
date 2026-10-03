import { describe, expect, it } from 'vitest';
import { ROUTE, type RouteNode } from '../systems/route';
import { planNodeArena } from '../systems/routeArena';
import { TileId, type FloorLayout } from '../systems/mapgen';
import { planBigProps } from './bigProps';
import { planCanal, planDecals, type CanalJson } from './floorFeatures';

const arena = (seed: string) => {
  const n = { id: 'c3r0', kind: 'battle', type: 'battle', name: '', col: 3, row: 0, links: [] } as unknown as RouteNode;
  return planNodeArena(n, 'stage1', seed, ROUTE, { quarterTileset: () => true, border: () => true }).layout;
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
  it('수로: 가로 한 줄, 다리 2칸만 걷기 가능, 다리 좌우는 밝은 판, 시작점·출구 줄 피함, 바닥 연결 유지', () => {
    for (const seed of ['a', 'b', 'c', 'd']) {
      const L = arena(seed);
      const plan = planCanal(L, canal, new Set())!;
      expect(plan).not.toBeNull();
      expect(new Set(plan.tiles.map((t) => t.y)).size).toBe(1);
      expect(plan.tiles.filter((t) => t.kind === 'bridgeL')).toHaveLength(1);
      expect(plan.tiles.filter((t) => t.kind === 'bridgeR')).toHaveLength(1);
      expect(plan.tiles.filter((t) => t.kind === 'lit').length).toBeGreaterThan(0);
      const A = L.arena!;
      expect(plan.row).not.toBe(A.spawn.y);
      expect([A.exit.y, A.exit.y + 1]).not.toContain(plan.row);
      const water = new Set(plan.tiles.filter((t) => !t.kind.startsWith('bridge')).map((t) => `${t.x},${t.y}`));
      expect(connected(L, water)).toBe(true);
      // 가운데가 막혀 있어도 다리는 걸을 수 있는 칸에
      const c = L.arena!.center!;
      const blocked = new Set([`${c.x - 1},${plan.row}`, `${c.x},${plan.row}`]);
      const moved = planCanal(L, canal, blocked)!;
      const b2 = moved.tiles.find((t) => t.kind === 'bridgeL')!;
      expect(blocked.has(`${b2.x},${b2.y}`) || blocked.has(`${b2.x + 1},${b2.y}`)).toBe(false);
      // 큰 소품은 수로·다리에 놓이지 않는다
      const bridges = new Set(plan.tiles.filter((t) => t.kind.startsWith('bridge')).map((t) => `${t.x},${t.y}`));
      const big = planBigProps(L, [{ name: 'crate_stack', footprint: [1, 1] }], water, seed, bridges);
      for (const b of big) expect(water.has(`${b.tx},${b.ty}`) || bridges.has(`${b.tx},${b.ty}`)).toBe(false);
    }
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
