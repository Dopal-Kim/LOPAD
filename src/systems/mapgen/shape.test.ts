import { describe, expect, it } from 'vitest';
import { ARENA_SHAPES } from '../../data/arenas';
import { ROUTE, generateRoute } from '../route';
import { SCREEN_TILES, SHAPE_AREA_SCREENS, planNodeArena, shapeAssignments } from '../routeArena';
import { planStructures, solidStructureTiles } from '../structures/placement';
import { arenaDoors } from '../doors/doorPlan';
import { buildShape, resizeAxis, validateShape, type ArenaShapeDef } from './shape';
import { TileId, type FloorLayout } from './types';

const BATTLE_SHAPES = [
  'cellar',
  'crossroad',
  'distillery',
  'dock_quay',
  'plaza_fountain',
  'rampart',
  'terrace',
] as const;

/** 걸을 수 있는 칸 (바닥 − 단단한 구조물) 에서 from 으로부터 4방향 BFS */
function reach(L: FloorLayout, blocked: ReadonlySet<string>, from: { x: number; y: number }): Set<string> {
  const ok = (x: number, y: number) => L.tiles[y]?.[x] === TileId.Floor && !blocked.has(`${x},${y}`);
  const seen = new Set<string>();
  if (!ok(from.x, from.y)) return seen;
  const stack = [from];
  seen.add(`${from.x},${from.y}`);
  while (stack.length) {
    const p = stack.pop()!;
    for (const [dx, dy] of [
      [1, 0],
      [-1, 0],
      [0, 1],
      [0, -1],
    ]) {
      const x = p.x + dx;
      const y = p.y + dy;
      const k = `${x},${y}`;
      if (seen.has(k) || !ok(x, y)) continue;
      seen.add(k);
      stack.push({ x, y });
    }
  }
  return seen;
}

describe('P19 S2 형태 틀 데이터 (계약 free-combat §3)', () => {
  it('1층 형태 7종 + 보스 연회장 56×34, 소품 세트는 route.json setPieces 에 있다', () => {
    const battle = [...ARENA_SHAPES.values()].filter((d) => d.stage === 'battle').map((d) => d.id);
    expect(battle.sort()).toEqual([...BATTLE_SHAPES]);
    const boss = ARENA_SHAPES.get('banquet_hall')!;
    expect(boss.stage).toBe('boss');
    const g = buildShape(boss, { scale: 1, flipX: false, flipY: false });
    expect([g.w, g.h]).toEqual([56, 34]);
    for (const d of ARENA_SHAPES.values()) for (const p of d.props) expect(ROUTE.setPieces?.[p]).toBeTruthy();
  });

  it('형태마다 위험물 3종 이상(보스 제외) · 낙하 구역은 부두·테라스·회랑에', () => {
    for (const id of BATTLE_SHAPES) {
      const d = ARENA_SHAPES.get(id)!;
      expect(new Set(d.hazards.map((h) => h.kind)).size).toBeGreaterThanOrEqual(3);
    }
    for (const id of ['dock_quay', 'terrace', 'rampart']) {
      const g = buildShape(ARENA_SHAPES.get(id)!, { scale: 1, flipX: false, flipY: false });
      expect(g.cells.flat().some((t) => t === 'water' || t === 'drop' || t === 'ledge')).toBe(true);
    }
  });

  it('검증: 폭이 다른 줄 · 모르는 문자 · 없는 h 자리 · 같은 면 문은 거부', () => {
    const base = ARENA_SHAPES.get('crossroad')!;
    const bad = (patch: Partial<ArenaShapeDef>) => () => validateShape({ ...base, ...patch });
    expect(bad({ mask: [...base.mask.slice(0, -1), '...'] })).toThrow();
    expect(bad({ mask: base.mask.map((r, i) => (i === 3 ? 'Q' + r.slice(1) : r)) })).toThrow();
    expect(bad({ hazards: [{ kind: 'cask', slot: 99 }] })).toThrow();
    expect(
      bad({
        doors: [
          { side: 'west', at: 0.5 },
          { side: 'west', at: 0.2 },
        ],
      }),
    ).toThrow();
  });

  it('이음매 변형: 이웃과 같은 줄만 지우고(유일한 줄은 남는다), 늘릴 때는 같은 줄을 복제', () => {
    const rows = ['a', 'a', 'b', 'c', 'c', 'c', 'd'].map((s) => [s]);
    const down = resizeAxis(rows, 4);
    expect(down.rows.map((r) => r[0])).toEqual(['a', 'b', 'c', 'd']);
    // 더 지울 줄이 없으면 거기서 멈춘다
    expect(resizeAxis(rows, 2).rows.map((r) => r[0])).toEqual(['a', 'b', 'c', 'd']);
    const up = resizeAxis(rows, 9).rows.map((r) => r[0]);
    expect(up).toHaveLength(9);
    expect(up.filter((s) => s === 'b' || s === 'd')).toEqual(['b', 'd']);
  });

  it('뒤집기: 입구는 늘 서쪽 · 출구는 동쪽, 위험물 수 그대로', () => {
    for (const d of ARENA_SHAPES.values())
      for (const flipX of [false, true])
        for (const flipY of [false, true]) {
          const g = buildShape(d, { scale: 1, flipX, flipY });
          expect(g.hazards).toHaveLength(d.hazards.length);
          for (const r of [g.entryRow - 1, g.entryRow, g.entryRow + 1]) expect(g.cells[r][0]).not.toBe('wall');
          for (const r of [g.exitRow - 1, g.exitRow, g.exitRow + 1]) expect(g.cells[r][g.w - 1]).not.toBe('wall');
        }
  });
});

describe('P19 S2 1층 시드 50개: 형태 배정 · 넓이 · 도달 가능 · 문 사이 경로', { timeout: 60_000 }, () => {
  const SEEDS = Array.from({ length: 50 }, (_, i) => `p19s2:${i}`);
  const screen = SCREEN_TILES.w * SCREEN_TILES.h;

  it('한 판 전투 노드(여정 전투 포함) 형태 ≥ 5종 · 중복 ≤ 1회 · 버려진 길 = 회랑 · 같은 단 두 갈래는 다른 형태 · 보스 = 연회장', () => {
    for (const seed of SEEDS) {
      const graph = generateRoute('stage1', seed);
      const map = shapeAssignments('stage1', seed);
      const battles = graph.nodes.filter((n) => n.kind === 'battle' || n.kind === 'road');
      const ids = battles.map((n) => map.get(n.id)!);
      expect(ids.every(Boolean)).toBe(true);
      expect(new Set(ids).size).toBeGreaterThanOrEqual(5);
      expect(ids.length - new Set(ids).size).toBeLessThanOrEqual(1);
      // 버려진 길(황무지 첫 전투) = 성벽 회랑 (스토리 65 팩 노드 이름 기준)
      expect(map.get(battles.find((n) => n.kind === 'road')!.id)).toBe('rampart');
      for (const a of battles)
        for (const b of battles) if (a !== b && a.col === b.col) expect(map.get(a.id)).not.toBe(map.get(b.id));
      const boss = graph.nodes.find((n) => n.kind === 'boss')!;
      expect(map.get(boss.id)).toBe('banquet_hall');
    }
  });

  it('넓이 화면 1.8~3.0배 · 모든 바닥 칸 도달 가능(BFS, 단단한 구조물 포함) · 입구 ↔ 출구 문 경로', () => {
    let checked = 0;
    for (const seed of SEEDS) {
      const graph = generateRoute('stage1', seed);
      for (const n of graph.nodes.filter((x) => x.kind === 'battle' || x.kind === 'road' || x.kind === 'boss')) {
        const p = planNodeArena(n, 'stage1', seed);
        expect(p.shape).not.toBeNull();
        const L = p.layout;
        const I = L.rooms[0].interior;
        const ratio = (I.w * I.h) / screen;
        expect(ratio).toBeGreaterThanOrEqual(SHAPE_AREA_SCREENS[0]);
        expect(ratio).toBeLessThanOrEqual(SHAPE_AREA_SCREENS[1]);
        const placed = planStructures(L, 'stage1', `${seed}:${n.id}`, { node: p.structureNode });
        const blocked = solidStructureTiles(placed);
        const doors = arenaDoors(L, 16, 3, true);
        expect(doors.entry && doors.exit).toBeTruthy();
        const from = { x: doors.entry!.threshold.x, y: doors.entry!.threshold.y + 1 };
        const seen = reach(L, blocked, from);
        let floor = 0;
        for (let y = 0; y < L.heightTiles; y++)
          for (let x = 0; x < L.widthTiles; x++)
            if (L.tiles[y][x] === TileId.Floor && !blocked.has(`${x},${y}`)) {
              floor++;
              if (!seen.has(`${x},${y}`)) throw new Error(`${seed} ${n.id} ${p.shape!.id}: (${x},${y}) 도달 불가`);
            }
        expect(seen.size).toBe(floor);
        const t = doors.exit!.threshold;
        expect(seen.has(`${t.x},${t.y + 1}`)).toBe(true);
        checked++;
      }
    }
    expect(checked).toBeGreaterThanOrEqual(50 * 7);
  });

  it('형태 틀 위험물은 구조물 자리로 먼저 놓이고(술통·증류기·흉벽) 웅덩이는 따로 · 낙하 칸은 걷기 막힘(빈 칸)', () => {
    const seed = 'p19s2:hz';
    const graph = generateRoute('stage1', seed);
    for (const n of graph.nodes.filter((x) => x.kind === 'battle')) {
      const p = planNodeArena(n, 'stage1', seed);
      const placed = planStructures(p.layout, 'stage1', seed, { node: p.structureNode });
      const fixed = p.setPiece.fixed.filter((f) => f.kind === 'cask' || f.kind === 'still' || f.kind === 'crate');
      expect(fixed.length).toBeGreaterThan(0);
      const at = new Set(placed.map((s) => `${s.kind}:${s.tx},${s.ty}`));
      expect(fixed.filter((f) => at.has(`${f.kind}:${f.tx},${f.ty}`)).length).toBe(fixed.length);
      for (const d of p.layout.arena!.drops ?? []) expect(p.layout.tiles[d.y][d.x]).toBe(TileId.Void);
    }
  });
});
