import { describe, expect, it } from 'vitest';
import { ROUTE, type RouteNode } from '../systems/route';
import { planNodeArena } from '../systems/routeArena';
import { TileId } from '../systems/mapgen';
import { bigPropRules, planBigProps } from './bigProps';
import { PropGrid, isSolid } from './bigPropGrid';
import type { FloorLayout } from '../systems/mapgen';

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

  it('빈 목록이면 아무것도 놓지 않고, 규칙어·이름 규칙이 없으면 서·동 벽가 (53라운드 Q69)', () => {
    expect(planBigProps(arena('x'), [], new Set(), 'x')).toEqual([]);
    const L = arena('x');
    const out = planBigProps(L, [{ name: 'mystery', footprint: [1, 1] }], new Set(), 'x');
    expect(out.length).toBeGreaterThan(0);
    for (const o of out)
      expect(L.tiles[o.ty][o.tx - 1] === TileId.Floor && L.tiles[o.ty][o.tx + 1] === TileId.Floor).toBe(false);
  });
});

describe('53라운드 Q59 placement 힌트 일반 규칙 · avoidNearBorder', () => {
  it('힌트 규칙어 → 규칙 (적힌 순서), 없으면 이름 규칙, 그것도 없으면 벽가 (Q69)', () => {
    expect(bigPropRules({ name: 'crane_barrel', placement: 'floor (벽 앞)' })).toEqual(['north']);
    expect(bigPropRules({ name: 'steel_vat', placement: 'floor (벽 앞·구석)' })).toEqual(['north', 'corner']);
    expect(bigPropRules({ name: 'barrel_cart', placement: 'floor (가장자리 권장)' })).toEqual(['corner']);
    expect(bigPropRules({ name: 'stakes', placement: 'floor (흙둑 앞·엄폐)' })).toEqual(['cover']);
    expect(bigPropRules({ name: 'well', placement: 'floor' })).toEqual(['corner']);
    expect(bigPropRules({ name: 'crate_stack', placement: 'floor' })).toEqual(['cover']);
    expect(bigPropRules({ name: 'cannon', placement: 'floor' })).toEqual(['cover']);
    expect(bigPropRules({ name: 'mystery' })).toEqual(['cover']);
  });

  it('Q69 힌트별 규칙: 문·길 양옆 · 측면 세로 · 대칭 · 탁자 끝, 북쪽 회피 벽 앞 → 벽가', () => {
    expect(bigPropRules({ name: 'torch_stand', placement: 'floor (문·길 양옆)' })).toEqual(['exit']);
    expect(bigPropRules({ name: 'banquet_table', placement: 'floor (측면 세로, 막힘 장애물 — 52라운드)' })).toEqual([
      'column',
    ]);
    expect(bigPropRules({ name: 'pillar', placement: 'floor (내부 장애물, 대칭 배치)' })).toEqual(['mirror']);
    expect(bigPropRules({ name: 'candelabra_stand', placement: 'floor (탁자 끝·단상 양옆)' })).toEqual(['table']);
    const north = ['north'];
    expect(bigPropRules({ name: 'crane_barrel', placement: 'floor (벽 앞)', avoidNearBorder: north })).toEqual([
      'cover',
    ]);
    expect(bigPropRules({ name: 'toll_booth', placement: 'floor (벽 앞 권장)', avoidNearBorder: north })).toEqual([
      'cover',
    ]);
    expect(
      bigPropRules({ name: 'barrel_pyramid', placement: 'floor (벽 앞·구석)', avoidNearBorder: ['north', 'west'] }),
    ).toEqual(['cover', 'corner']);
    expect(bigPropRules({ name: 'steel_vat', placement: 'floor (벽 앞·구석)', avoidNearBorder: ['west'] })).toEqual([
      'north',
      'corner',
    ]);
  });

  it('지역 이름 없이 힌트만으로 놓고, 피하는 쪽 바닥 끝 3칸에는 발자국이 걸치지 않는다 · 결정적', () => {
    const generic = [
      { name: 'a_front', footprint: [2, 1] as [number, number], placement: 'floor (벽 앞 권장)' },
      {
        name: 'b_corner',
        footprint: [3, 1] as [number, number],
        placement: 'floor (가장자리 권장)',
        avoidNearBorder: ['east'],
      },
      {
        name: 'c_cover',
        footprint: [2, 1] as [number, number],
        placement: 'floor (엄폐)',
        avoidNearBorder: ['north', 'east'],
      },
      {
        name: 'd_front_corner',
        footprint: [3, 1] as [number, number],
        placement: 'floor (벽 앞·구석)',
        avoidNearBorder: ['north', 'west'],
      },
    ];
    for (const seed of ['a', 'b', 'c', 'd', 'e']) {
      const L = arena(seed);
      const out = planBigProps(L, generic, new Set(), seed);
      expect(out).toEqual(planBigProps(L, generic, new Set(), seed));
      const names = new Set(out.map((o) => o.name));
      expect(names.has('a_front')).toBe(true);
      expect(names.has('b_corner')).toBe(true);
      for (const o of out.filter((p) => p.name === 'a_front')) expect(L.tiles[o.ty - 1][o.tx]).toBe(TileId.Wall);
      // 바닥 끝 (방 안 바닥 칸의 경계)
      const I = L.rooms[0].interior;
      let north = Infinity;
      let east = -Infinity;
      let west = Infinity;
      for (let y = I.y; y < I.y + I.h; y++)
        for (let x = I.x; x < I.x + I.w; x++)
          if (L.tiles[y][x] === TileId.Floor) {
            north = Math.min(north, y);
            east = Math.max(east, x);
            west = Math.min(west, x);
          }
      for (const o of out) {
        const avoid = generic.find((g) => g.name === o.name)!.avoidNearBorder ?? [];
        if (avoid.includes('north')) expect(o.ty).toBeGreaterThanOrEqual(north + 3);
        if (avoid.includes('east')) expect(o.tx + o.w - 1).toBeLessThanOrEqual(east - 3);
        if (avoid.includes('west')) expect(o.tx).toBeGreaterThanOrEqual(west + 3);
      }
      // 북쪽을 피하는 '벽 앞·구석' 은 북쪽 벽 앞이 아니라 구석으로
      for (const o of out.filter((p) => p.name === 'd_front_corner')) expect(o.ty).toBeGreaterThanOrEqual(north + 3);
    }
  });
});

/** 벽으로 둘러싸인 5×3 바닥 방 — 가운데 줄 (x=3) 만 1칸짜리 통로 (위·아래 줄의 x=3 은 벽) */
function corridorRoom(): FloorLayout {
  const W = TileId.Wall;
  const F = TileId.Floor;
  const tiles = [
    [W, W, W, W, W, W, W],
    [W, F, F, W, F, F, W],
    [W, F, F, F, F, F, W],
    [W, F, F, W, F, F, W],
    [W, W, W, W, W, W, W],
  ];
  return {
    seed: 0,
    gridW: 1,
    gridH: 1,
    rooms: [],
    hallways: [],
    connections: [],
    tiles,
    widthTiles: 7,
    heightTiles: 5,
    cellRoom: new Map(),
  };
}

describe('53라운드 후속: 큰 소품 solid: false = 걷기 통과', () => {
  const I = { x: 1, y: 1, w: 5, h: 3 };
  const fp: [number, number] = [1, 1];

  it('solid 가 없거나 true 면 막힘, false 일 때만 통과', () => {
    expect(isSolid({})).toBe(true);
    expect(isSolid({ solid: true })).toBe(true);
    expect(isSolid({ solid: false })).toBe(false);
  });

  it('막는 소품은 하나뿐인 통로에 못 놓고, 통과 소품은 놓는다 (배치 결과에 solid 표시)', () => {
    const solidGrid = new PropGrid(corridorRoom(), new Set(), new Set(), I);
    expect(solidGrid.tryPlace([{ s: { name: 'cart', footprint: fp }, x: 3, y: 2 }])).toBe(false);
    expect(solidGrid.tryPlace([{ s: { name: 'cart', footprint: fp, solid: true }, x: 3, y: 2 }])).toBe(false);
    const passGrid = new PropGrid(corridorRoom(), new Set(), new Set(), I);
    expect(passGrid.tryPlace([{ s: { name: 'weapons_stuck', footprint: fp, solid: false }, x: 3, y: 2 }])).toBe(true);
    expect(passGrid.out).toEqual([{ name: 'weapons_stuck', tx: 3, ty: 2, w: 1, h: 1, solid: false }]);
  });

  it('통과 소품도 자리와 둘레 1칸 간격은 차지한다', () => {
    const grid = new PropGrid(corridorRoom(), new Set(), new Set(), I);
    expect(grid.tryPlace([{ s: { name: 'weapons_stuck', footprint: fp, solid: false }, x: 1, y: 1 }])).toBe(true);
    expect(grid.tryPlace([{ s: { name: 'weapons_stuck', footprint: fp, solid: false }, x: 1, y: 1 }])).toBe(false);
    expect(grid.tryPlace([{ s: { name: 'banner_pole', footprint: fp }, x: 2, y: 2 }])).toBe(false);
    expect(grid.tryPlace([{ s: { name: 'banner_pole', footprint: fp }, x: 5, y: 3 }])).toBe(true);
    expect(grid.out.map((o) => o.solid)).toEqual([false, true]);
  });
});
