import { describe, expect, it } from 'vitest';
import {
  ROUTE,
  RouteState,
  entryNodes,
  generateRoute,
  maxBattleWaves,
  minBattlesOnAnyPath,
  nodeWaves,
  routeEnabled,
  type RouteGraph,
} from './route';
import { ENEMIES } from '../data';
import { generateArena } from './mapgen/arena';
import { TileId } from './mapgen/types';
import { planStructures } from './structures/placement';
import { STRUCTURE_DEFS, availableOn } from './structures/data';

/** 진입 노드에서 링크로 닿는 노드 */
function reachable(g: RouteGraph): Set<string> {
  const byId = new Map(g.nodes.map((n) => [n.id, n]));
  const seen = new Set<string>();
  const stack = entryNodes(g).map((n) => n.id);
  while (stack.length) {
    const id = stack.pop()!;
    if (seen.has(id)) continue;
    seen.add(id);
    stack.push(...byId.get(id)!.links);
  }
  return seen;
}

describe('48라운드 노드 지도 (route)', () => {
  it('1~2층만 노드 지도', () => {
    expect(routeEnabled('stage1')).toBe(true);
    expect(routeEnabled('stage2')).toBe(true);
    expect(routeEnabled('stage3')).toBe(false);
  });

  it('같은 시드면 같은 지도, 다른 시드면 대개 다르다 (결정성)', () => {
    const a = generateRoute('stage1', 'seed-a:0');
    const b = generateRoute('stage1', 'seed-a:0');
    expect(b).toEqual(a);
    const kinds = new Set<string>();
    for (let i = 0; i < 20; i++)
      kinds.add(
        generateRoute('stage1', `s${i}:0`)
          .nodes.map((n) => n.kind)
          .join(','),
      );
    expect(kinds.size).toBeGreaterThan(1);
  });

  it('1층: 여정 3(탄생지→버려진 길→국경 초소) + 잔 4단×2(61 P3: 전투/전투 · 전투/이벤트 · 전투/전투 · 상점/쉼터) + 보스', () => {
    const want = [
      ['battle', 'battle'],
      ['battle', 'event'],
      ['battle', 'battle'],
      ['rest', 'shop'],
    ];
    for (let i = 0; i < 30; i++) {
      const g = generateRoute('stage1', `run${i}:0`);
      expect(g.nodes).toHaveLength(12);
      expect(g.nodes.filter((n) => n.col < 3).map((n) => n.kind)).toEqual(['birth', 'road', 'post']);
      expect(g.nodes.filter((n) => n.col < 3).every((n) => n.type === 'journey')).toBe(true);
      for (let c = 0; c < 4; c++)
        expect(
          g.nodes
            .filter((n) => n.col === 3 + c)
            .map((n) => n.kind)
            .sort(),
        ).toEqual(want[c]);
      const boss = g.nodes.filter((n) => n.kind === 'boss');
      expect(boss).toHaveLength(1);
      expect(boss[0].col).toBe(7);
      expect(entryNodes(g).map((n) => n.kind)).toEqual(['birth']);
      expect(g.nodes.every((n) => n.name.length > 0)).toBe(true);
    }
  });

  it('61 P3: 잔 구간 전투 웨이브 = 그 단 웨이브 (새 적은 단마다 처음 나온다) · 버려진 길은 징집병만', () => {
    const g = generateRoute('stage1', 'waves:0');
    const enemiesAt = (col: number) =>
      new Set((nodeWaves('stage1', { kind: 'battle', col }) ?? []).flatMap((w) => w.map((e) => e.enemy)));
    expect([...new Set((nodeWaves('stage1', { kind: 'road', col: 1 }) ?? []).flat().map((e) => e.enemy))]).toEqual([
      'dummy',
    ]);
    expect(enemiesAt(3).has('archer')).toBe(true);
    expect(enemiesAt(3).has('charger')).toBe(false);
    expect(enemiesAt(4).has('charger')).toBe(true);
    expect(enemiesAt(5).has('peddler') && enemiesAt(5).has('porter')).toBe(true);
    // 61 단계 5 (P13 §5): 1층 추정 9분 미만 → 단1·단3 웨이브 4 (처치 상한 20)
    for (const col of [3, 4, 5]) {
      const waves = nodeWaves('stage1', { kind: 'battle', col })!;
      expect(waves.length).toBeGreaterThanOrEqual(2);
      expect(waves.length).toBeLessThanOrEqual(col === 4 ? 3 : 4);
      const kills = waves.flat().reduce((a, e) => a + e.count, 0);
      expect(kills).toBeGreaterThanOrEqual(12);
      expect(kills).toBeLessThanOrEqual(20);
      for (const e of waves.flat()) expect(ENEMIES[e.enemy], e.enemy).toBeDefined();
    }
    expect(maxBattleWaves('stage1', 2)).toBe(4);
    expect(g.nodes.filter((n) => n.kind === 'battle')).toHaveLength(5);
  });

  it('2층: 여정 없이 갈래 6 + 보스, 진입은 두 갈래', () => {
    const g = generateRoute('stage2', 'x:1');
    expect(g.nodes).toHaveLength(7);
    expect(entryNodes(g)).toHaveLength(2);
    expect(g.nodes.find((n) => n.kind === 'boss')!.col).toBe(3);
  });

  it('연결성: 모든 노드에 닿고, 보스 말고는 다음 단계로만 이어지며, 어느 길로 가도 전투가 있다', () => {
    for (const stage of ['stage1', 'stage2'])
      for (let i = 0; i < 40; i++) {
        const g = generateRoute(stage, `c${i}`);
        expect(reachable(g).size).toBe(g.nodes.length);
        const byId = new Map(g.nodes.map((n) => [n.id, n]));
        for (const n of g.nodes) {
          if (n.kind === 'boss') expect(n.links).toEqual([]);
          else {
            expect(n.links.length).toBeGreaterThan(0);
            for (const l of n.links) expect(byId.get(l)!.col).toBe(n.col + 1);
          }
        }
        expect(minBattlesOnAnyPath(g)).toBeGreaterThanOrEqual(1);
      }
  });

  it('진행 상태: 고를 수 있는 노드만 들어가고, 상태(current·cleared·available·passed·locked)를 계약대로 낸다', () => {
    const g = generateRoute('stage1', 'state:0');
    const r = new RouteState(g, 1);
    expect(r.canChoose('c0r0')).toBe(true);
    expect(r.enter('c3r0')).toBe(false);
    expect(r.enter('c0r0')).toBe(true);
    r.markCleared();
    r.choosing = true;
    let ui = r.toUi();
    expect(ui.currentId).toBe('c0r0');
    expect(ui.choosing).toBe(true);
    expect(ui.nodes.find((n) => n.id === 'c1r0')!.state).toBe('available');
    expect(ui.nodes.find((n) => n.id === 'c0r0')!.state).toBe('current');
    expect(ui.nodes.find((n) => n.id === 'c6r0')!.state).toBe('locked');
    r.enter('c1r0');
    r.enter('c2r0');
    expect(r.nextOptions().map((n) => n.col)).toEqual([3, 3]);
    r.enter('c3r0');
    ui = r.toUi();
    expect(ui.nodes.find((n) => n.id === 'c3r1')!.state).toBe('passed');
    expect(ui.nodes.find((n) => n.id === 'c1r0')!.state).toBe('cleared');
    expect(ui.choosing).toBe(false);
  });
});

describe('48라운드 노드 전투장 (arena)', () => {
  it('약 40×24 내부 + 벽 1칸 + 빈 여백, 시작점은 왼쪽·출구는 오른쪽, 카메라 경계 = 내부 + 벽', () => {
    const L = generateArena({
      roomId: 'c3r0',
      type: 'trial',
      floor: 'trial',
      w: 40,
      h: 24,
      margin: 8,
      spawnInset: 3,
      exitInset: 3,
    });
    const room = L.rooms[0];
    expect(room.interior).toEqual({ x: 9, y: 9, w: 40, h: 24 });
    expect(room.doors).toEqual([]);
    expect(L.hallways).toEqual([]);
    expect(L.tiles[room.interior.y][room.interior.x]).toBe(TileId.Floor);
    expect(L.tiles[room.interior.y - 1][room.interior.x]).toBe(TileId.Wall);
    expect(L.tiles[0][0]).toBe(TileId.Void);
    const A = L.arena!;
    expect(A.spawn.x).toBeLessThan(A.exit.x);
    expect(L.tiles[A.exit.y][A.exit.x + 1]).toBe(TileId.Floor);
    expect(A.camera).toEqual({ x: 8, y: 8, w: 42, h: 26 });
    expect(L.cellRoom.get('0,0')).toBe('c3r0');
  });

  it('노드 구조물: 허용 종류만, 층 테마 제한 유지, forceAll = 허용 종류 전부 (Q11)', () => {
    const arena = (type: 'trial' | 'rest' | 'start' | 'boss') =>
      generateArena({ roomId: 'n', type, floor: type, w: 40, h: 24, margin: 8, spawnInset: 3, exitInset: 3 });
    for (const [kind, room] of [
      ['battle', 'trial'],
      ['rest', 'rest'],
      ['shop', 'start'],
      ['event', 'start'],
    ] as const) {
      const d = ROUTE.kinds[kind];
      for (const stage of ['stage1', 'stage2']) {
        const plan = planStructures(arena(room), stage, `${kind}:${stage}`, {
          forceAll: true,
          node: { kinds: d.structures, budget: d.budget },
        });
        const allowed = d.structures.filter((k) => availableOn(STRUCTURE_DEFS.get(k)!, stage));
        for (const p of plan) expect(allowed).toContain(p.kind);
        // 숨은 벽은 여백이 있을 때 자리를 잡는다 (1층 이벤트)
        const kinds = new Set(plan.map((p) => p.kind));
        for (const k of allowed) expect(kinds.has(k)).toBe(true);
      }
    }
    // 예산: 확률 배치는 budget 안 (filler 짐·술통 제외)
    const d = ROUTE.kinds.battle;
    for (let i = 0; i < 20; i++) {
      const plan = planStructures(arena('trial'), 'stage1', `b${i}`, {
        node: { kinds: d.structures, budget: d.budget },
      });
      const nonFiller = new Set(plan.filter((p) => p.kind !== 'crate' && p.kind !== 'cask').map((p) => p.kind));
      expect(nonFiller.size).toBeLessThanOrEqual(d.budget[1]);
    }
  });

  it('노드 구조물은 시작점·출구 비움 칸에 놓이지 않는다', () => {
    const L = generateArena({
      roomId: 'n',
      type: 'trial',
      floor: 'trial',
      w: 40,
      h: 24,
      margin: 8,
      spawnInset: 3,
      exitInset: 3,
    });
    const A = L.arena!;
    const reserve = [
      { x: A.spawn.x - 3, y: A.spawn.y - 3, w: 7, h: 7 },
      { x: A.exit.x - 3, y: A.exit.y - 3, w: 8, h: 8 },
    ];
    const d = ROUTE.kinds.battle;
    const plan = planStructures(L, 'stage1', 'r', {
      forceAll: true,
      node: { kinds: d.structures, budget: d.budget, reserve },
    });
    for (const p of plan)
      for (const r of reserve) {
        const overlap = p.tx < r.x + r.w && p.tx + p.w > r.x && p.ty < r.y + r.h && p.ty + p.h > r.y;
        expect(overlap).toBe(false);
      }
  });
});
