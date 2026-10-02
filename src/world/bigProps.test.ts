import { describe, expect, it } from 'vitest';
import { ROUTE, type RouteNode } from '../systems/route';
import { planNodeArena } from '../systems/routeArena';
import { TileId } from '../systems/mapgen';
import { planBigProps } from './bigProps';

const shapes = [
  { name: 'lamp_post', footprint: [1, 1] as [number, number] },
  { name: 'brazier', footprint: [1, 1] as [number, number] },
  { name: 'well', footprint: [2, 1] as [number, number] },
  { name: 'stall', footprint: [2, 1] as [number, number] },
  { name: 'crate_stack', footprint: [1, 1] as [number, number] },
];

const arena = (seed: string) => {
  const n = { id: 'c3r0', kind: 'battle', type: 'battle', name: '', col: 3, row: 0, links: [] } as unknown as RouteNode;
  return planNodeArena(n, 'stage1', seed, ROUTE, { quarterTileset: () => true }).layout;
};

describe('52라운드 Q11 큰 소품 배치', () => {
  it('바닥 위·막힌 칸 밖·서로 겹치지 않음·시작점 둘레 비움·가로등은 북쪽 벽 앞·바닥 연결 유지·결정적', () => {
    for (const seed of ['a', 'b', 'c', 'd', 'e']) {
      const L = arena(seed);
      const blocked = new Set(['20,10', '21,10']);
      const out = planBigProps(L, shapes, blocked, seed);
      expect(out).toEqual(planBigProps(L, shapes, blocked, seed));
      const names = out.map((o) => o.name);
      expect(names).toContain('lamp_post');
      expect(names).toContain('brazier');
      const used = new Set<string>();
      for (const o of out)
        for (let y = o.ty; y < o.ty + o.h; y++)
          for (let x = o.tx; x < o.tx + o.w; x++) {
            const k = `${x},${y}`;
            expect(L.tiles[y][x]).toBe(TileId.Floor);
            expect(blocked.has(k)).toBe(false);
            expect(used.has(k)).toBe(false);
            used.add(k);
            const s = L.arena!.spawn;
            expect(Math.max(Math.abs(x - s.x), Math.abs(y - s.y))).toBeGreaterThan(3);
          }
      for (const o of out.filter((p) => p.name === 'lamp_post')) expect(L.tiles[o.ty - 1][o.tx]).toBe(TileId.Wall);
      // 바닥 연결: 막힌 칸을 뺀 바닥이 한 덩어리
      const open = (x: number, y: number) =>
        L.tiles[y]?.[x] === TileId.Floor && !used.has(`${x},${y}`) && !blocked.has(`${x},${y}`);
      const all: string[] = [];
      for (let y = 0; y < L.heightTiles; y++)
        for (let x = 0; x < L.widthTiles; x++) if (open(x, y)) all.push(`${x},${y}`);
      const [sx, sy] = all[0].split(',').map(Number);
      const seen = new Set([all[0]]);
      const st = [[sx, sy]];
      while (st.length) {
        const [x, y] = st.pop()!;
        for (const [dx, dy] of [
          [1, 0],
          [-1, 0],
          [0, 1],
          [0, -1],
        ]) {
          const k = `${x + dx},${y + dy}`;
          if (!seen.has(k) && open(x + dx, y + dy)) {
            seen.add(k);
            st.push([x + dx, y + dy]);
          }
        }
      }
      expect(seen.size).toBe(all.length);
    }
  });

  it('모르는 이름·빈 목록이면 아무것도 놓지 않는다', () => {
    expect(planBigProps(arena('x'), [], new Set(), 'x')).toEqual([]);
  });
});
