/**
 * 53라운드 Q69: 1층 5지역(외곽·양조·성문·황무지·연회장) 큰 소품을 게임과 같은 순서(전투장 → 구조물·세트 → 수로 → 큰 소품)로
 * 8시드 배치해 힌트별 규칙과 길 보장(출구·상점·문까지 이어짐)을 확인한다. 소품 목록은 아트 v3 소품 시트의 bigProps
 * (`tiles/v3/stage1_<지역>_props.json`, 계약 art §14 — 이름·발자국·placement·avoidNearBorder 만 옮김).
 */
import { describe, expect, it } from 'vitest';
import { ROUTE, type RouteNode } from '../systems/route';
import { planNodeArena, setPieceTiles } from '../systems/routeArena';
import { planStructures, structureTiles } from '../systems/structures/placement';
import { TileId, type FloorLayout } from '../systems/mapgen';
import { mirrorX, planBigProps, type BigPropPlacement, type BigPropShape } from './bigProps';
import { doorMouths } from './bigPropGrid';
import { planCanal, type CanalJson } from './floorFeatures';

const fp = (w: number, h: number) => [w, h] as [number, number];

const REGIONS: Record<string, { col: number; kind: string; canal?: boolean; shapes: BigPropShape[] }> = {
  outer: {
    col: 3,
    kind: 'battle',
    shapes: [
      { name: 'lamp_post', footprint: fp(1, 1), placement: 'floor (벽 앞 권장)' },
      { name: 'stall', footprint: fp(3, 1), placement: 'floor (방 가장자리 권장)', avoidNearBorder: ['north'] },
      { name: 'crate_stack', footprint: fp(1, 1), placement: 'floor', avoidNearBorder: ['north'] },
      { name: 'well', footprint: fp(2, 1), placement: 'floor' },
      { name: 'brazier', footprint: fp(1, 1) },
    ],
  },
  brewery: {
    col: 5,
    kind: 'battle',
    canal: true,
    shapes: [
      { name: 'crane_barrel', footprint: fp(1, 1), placement: 'floor (벽 앞)', avoidNearBorder: ['north', 'west'] },
      { name: 'steel_vat', footprint: fp(2, 1), placement: 'floor (벽 앞·구석)', avoidNearBorder: ['west'] },
      {
        name: 'barrel_pyramid',
        footprint: fp(3, 1),
        placement: 'floor (벽 앞·구석)',
        avoidNearBorder: ['north', 'west'],
      },
      { name: 'crate_stack', footprint: fp(1, 1), placement: 'floor', avoidNearBorder: ['north'] },
      { name: 'handcart', footprint: fp(2, 1), placement: 'floor', avoidNearBorder: ['north'] },
    ],
  },
  gate: {
    col: 2,
    kind: 'post',
    shapes: [
      { name: 'toll_booth', footprint: fp(2, 1), placement: 'floor (벽 앞 권장)', avoidNearBorder: ['north', 'east'] },
      { name: 'torch_stand', footprint: fp(1, 1), placement: 'floor (문·길 양옆)' },
      { name: 'barrel_cart', footprint: fp(3, 1), placement: 'floor (가장자리 권장)', avoidNearBorder: ['east'] },
      { name: 'crate_stack', footprint: fp(1, 1), placement: 'floor', avoidNearBorder: ['north'] },
      { name: 'barricade_x', footprint: fp(2, 1), placement: 'floor (엄폐)', avoidNearBorder: ['north', 'east'] },
      { name: 'water_trough', footprint: fp(2, 1), placement: 'floor' },
    ],
  },
  waste: {
    col: 1,
    kind: 'road',
    shapes: [
      { name: 'banner_pole', footprint: fp(1, 1), placement: 'floor' },
      { name: 'weapons_stuck', footprint: fp(1, 1), placement: 'floor', avoidNearBorder: ['north'] },
      { name: 'stakes', footprint: fp(2, 1), placement: 'floor (흙둑 앞·엄폐)', avoidNearBorder: ['north'] },
      {
        name: 'broken_cart',
        footprint: fp(2, 1),
        placement: 'floor (가장자리 권장)',
        avoidNearBorder: ['north', 'east'],
      },
      { name: 'cannon', footprint: fp(2, 1), placement: 'floor' },
    ],
  },
  hall: {
    col: 6,
    kind: 'boss',
    shapes: [
      { name: 'banquet_table', footprint: fp(2, 4), placement: 'floor (측면 세로, 막힘 장애물 — 52라운드)' },
      {
        name: 'pillar',
        footprint: fp(1, 1),
        placement: 'floor (내부 장애물, 대칭 배치)',
        avoidNearBorder: ['north'],
      },
      {
        name: 'candelabra_stand',
        footprint: fp(1, 1),
        placement: 'floor (탁자 끝·단상 양옆)',
        avoidNearBorder: ['north'],
      },
      { name: 'bench', footprint: fp(2, 1), placement: 'floor' },
    ],
  },
};

const CANAL: CanalJson = {
  frames: [64, 65, 66],
  framesLit: [69, 70, 71],
  frameMs: 180,
  bridge: { left: 67, right: 68 },
  litNearBridge: 2,
  walkable: false,
};

const SEEDS = ['s0', 's1', 's2', 's3', 's4', 's5', 's6', 's7'];

/** WorldSetup·TileWorld 와 같은 순서로 한 지역 전투장을 꾸린다 */
function build(region: string, seed: string) {
  const r = REGIONS[region];
  const node = { id: `c${r.col}r0`, kind: r.kind, type: r.kind, name: '', col: r.col, row: 0, links: [] };
  const plan = planNodeArena(node as unknown as RouteNode, 'stage1', seed, ROUTE, {
    quarterTileset: () => true,
    border: () => true,
  });
  const L = plan.layout;
  const propSeed = `${seed}:${node.id}`;
  const structures = planStructures(L, 'stage1', propSeed, { node: plan.structureNode });
  const blocked = new Set([...structureTiles(structures), ...setPieceTiles(plan)]);
  const bridges = new Set<string>();
  if (r.canal)
    for (const t of planCanal(L, CANAL, blocked)?.tiles ?? [])
      if (t.kind === 'bridgeL' || t.kind === 'bridgeR') bridges.add(`${t.x},${t.y}`);
      else blocked.add(`${t.x},${t.y}`);
  const props = planBigProps(L, r.shapes, blocked, propSeed, bridges);
  return { L, blocked, bridges, props, propSeed, shapes: r.shapes };
}

const cells = (p: BigPropPlacement) => {
  const out: string[] = [];
  for (let y = p.ty; y < p.ty + p.h; y++) for (let x = p.tx; x < p.tx + p.w; x++) out.push(`${x},${y}`);
  return out;
};

/** 바닥 끝 (방 안 바닥 칸의 경계) */
function floorEdge(L: FloorLayout) {
  const I = L.rooms[0].interior;
  const e = { north: Infinity, south: -Infinity, west: Infinity, east: -Infinity };
  for (let y = I.y; y < I.y + I.h; y++)
    for (let x = I.x; x < I.x + I.w; x++)
      if (L.tiles[y][x] === TileId.Floor) {
        e.north = Math.min(e.north, y);
        e.south = Math.max(e.south, y);
        e.west = Math.min(e.west, x);
        e.east = Math.max(e.east, x);
      }
  return e;
}

/** 시작점에서 4방향으로 닿는 바닥 칸 (막힌 칸·소품 빼고) */
function reach(L: FloorLayout, closed: ReadonlySet<string>): Set<string> {
  const s = L.arena!.spawn;
  const open = (x: number, y: number) => L.tiles[y]?.[x] === TileId.Floor && !closed.has(`${x},${y}`);
  const seen = new Set([`${s.x},${s.y}`]);
  const stack = [[s.x, s.y]];
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
  return seen;
}

describe('53라운드 Q69 큰 소품 힌트별 규칙 · 5지역 8시드', () => {
  for (const region of Object.keys(REGIONS))
    it(`${region}: 결정적 · 바닥 위·겹침 없음 · 테두리 회피 · 출구·상점·문까지 길이 이어짐`, () => {
      for (const seed of SEEDS) {
        const { L, blocked, bridges, props, propSeed, shapes } = build(region, seed);
        expect(planBigProps(L, shapes, blocked, propSeed, bridges)).toEqual(props);
        expect(props.length).toBeGreaterThan(0);
        const A = L.arena!;
        const edge = floorEdge(L);
        const used = new Set<string>();
        for (const p of props) {
          for (const k of cells(p)) {
            const [x, y] = k.split(',').map(Number);
            expect(L.tiles[y][x]).toBe(TileId.Floor);
            expect(blocked.has(k) || bridges.has(k) || used.has(k)).toBe(false);
            used.add(k);
          }
          const avoid = shapes.find((s) => s.name === p.name)!.avoidNearBorder ?? [];
          if (avoid.includes('north')) expect(p.ty).toBeGreaterThanOrEqual(edge.north + 3);
          if (avoid.includes('south')) expect(p.ty + p.h - 1).toBeLessThanOrEqual(edge.south - 3);
          if (avoid.includes('west')) expect(p.tx).toBeGreaterThanOrEqual(edge.west + 3);
          if (avoid.includes('east')) expect(p.tx + p.w - 1).toBeLessThanOrEqual(edge.east - 3);
        }
        // 길 보장: 시작점에서 막힌 칸·소품을 피해 출구 2×2 · 상점 2×2 · 문 앞 칸 · 남은 바닥 전부에 닿는다
        const closed = new Set([...blocked, ...used]);
        const seen = reach(L, closed);
        for (const [x, y] of [
          [0, 0],
          [1, 0],
          [0, 1],
          [1, 1],
        ]) {
          expect(used.has(`${A.exit.x + x},${A.exit.y + y}`)).toBe(false);
          expect(seen.has(`${A.exit.x + x},${A.exit.y + y}`)).toBe(true);
        }
        for (const d of doorMouths(L)) {
          for (let y = d.y - 1; y <= d.y + 1; y++)
            for (let x = d.x - 1; x <= d.x + 1; x++) expect(used.has(`${x},${y}`)).toBe(false);
          if (!blocked.has(`${d.x},${d.y}`)) expect(seen.has(`${d.x},${d.y}`)).toBe(true);
        }
        let open = 0;
        for (let y = 0; y < L.heightTiles; y++)
          for (let x = 0; x < L.widthTiles; x++) if (L.tiles[y][x] === TileId.Floor && !closed.has(`${x},${y}`)) open++;
        expect(seen.size).toBe(open);
      }
    });

  it('성문 횃불대: 출구 좌우 한 짝 (같은 줄, 같은 거리) · 징수소는 북쪽 벽 앞이 아니라 서쪽 벽가', () => {
    for (const seed of SEEDS) {
      const { L, props } = build('gate', seed);
      const E = L.arena!.exit;
      const torches = props.filter((p) => p.name === 'torch_stand');
      expect(torches).toHaveLength(2);
      const [a, b] = [...torches].sort((p, q) => p.tx - q.tx);
      expect(a.ty).toBe(b.ty);
      expect([E.y, E.y + 1]).toContain(a.ty);
      expect(E.x - (a.tx + a.w)).toBe(b.tx - (E.x + 2));
      expect(E.x - (a.tx + a.w)).toBeGreaterThanOrEqual(1);
      for (const p of props.filter((q) => q.name === 'toll_booth')) {
        expect(L.tiles[p.ty][p.tx - 1]).not.toBe(TileId.Floor);
        expect(L.tiles[p.ty - 1][p.tx]).toBe(TileId.Floor);
      }
    }
  });

  it('양조 크레인 통: 북쪽 벽 앞 대신 동쪽 벽가 (서쪽·북쪽 회피)', () => {
    for (const seed of SEEDS) {
      const { L, props } = build('brewery', seed);
      const crane = props.filter((p) => p.name === 'crane_barrel');
      expect(crane.length).toBeGreaterThan(0);
      for (const p of crane) {
        expect(L.tiles[p.ty][p.tx + p.w]).not.toBe(TileId.Floor);
        expect(L.tiles[p.ty - 1][p.tx]).toBe(TileId.Floor);
      }
    }
  });

  it('연회장: 탁자는 서·동 벽가 세로, 기둥은 가운데 축 좌우 짝, 촛대는 탁자 옆(한 칸 띄움)', () => {
    for (const seed of SEEDS) {
      const { L, props } = build('hall', seed);
      const I = L.rooms[0].interior;
      const edge = floorEdge(L);
      const tables = props.filter((p) => p.name === 'banquet_table');
      expect(tables.length).toBeGreaterThan(0);
      for (const t of tables) {
        expect(t.h).toBeGreaterThan(t.w);
        expect(t.tx === edge.west || t.tx + t.w - 1 === edge.east).toBe(true);
      }
      const pillars = props.filter((p) => p.name === 'pillar');
      expect(pillars.length).toBeGreaterThan(0);
      expect(pillars.length % 2).toBe(0);
      for (const p of pillars)
        expect(pillars.some((q) => q.ty === p.ty && q.tx === mirrorX(I, p.tx, p.w) && q !== p)).toBe(true);
      for (const c of props.filter((p) => p.name === 'candelabra_stand')) {
        const near = tables.some((t) => {
          const gx = Math.max(t.tx - (c.tx + c.w), c.tx - (t.tx + t.w));
          const gy = Math.max(t.ty - (c.ty + c.h), c.ty - (t.ty + t.h));
          return Math.max(gx, gy) === 1;
        });
        expect(near).toBe(true);
      }
    }
  });
});
