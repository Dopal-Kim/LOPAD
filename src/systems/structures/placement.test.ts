import { describe, expect, it } from 'vitest';
import { STAGES } from '../../data';
import { generateFloor, TileId, type FloorLayout } from '../mapgen';
import { planProps } from '../../world/tileskin';
import { INTERACT_KINDS, STRUCTURE_DEFS, STRUCTURE_RULES, structureDef } from './data';
import { baseBlocked, planStructures, solidStructureTiles, structureTiles, type StructurePlacement } from './placement';

const seeds = [1, 2, 3, 42, 'lopad', 'abc', 9999, 123456, 'r47', 'demo'];

/** 57라운드 D1: 같은 (층, 시드) 의 층·배치는 한 번만 만든다 (테스트는 결과를 바꾸지 않는다) */
const layouts = new Map<string, FloorLayout>();
const plans = new Map<string, { layout: FloorLayout; list: StructurePlacement[] }>();
function layoutOf(stageId: string, seed: string | number): FloorLayout {
  const key = `${seed}:${stageId}`;
  let L = layouts.get(key);
  if (!L) layouts.set(key, (L = generateFloor(key, STAGES[stageId].layout)));
  return L;
}
function floor(stageId: string, seed: string | number) {
  const key = `${seed}:${stageId}`;
  let f = plans.get(key);
  if (!f) {
    const layout = layoutOf(stageId, seed);
    plans.set(key, (f = { layout, list: planStructures(layout, stageId, key) }));
  }
  return f;
}

const budgetKinds = (list: StructurePlacement[], group: 'common' | 'theme') =>
  new Set(list.filter((p) => structureDef(p.kind).group === group).map((p) => p.kind));

describe('planStructures (47라운드 배치)', () => {
  it('같은 시드 → 같은 배치', () => {
    const L = generateFloor('same', STAGES.stage1.layout);
    expect(planStructures(L, 'stage1', 'same')).toEqual(planStructures(L, 'stage1', 'same'));
    const L2 = generateFloor('same', STAGES.stage2.layout);
    expect(planStructures(L2, 'stage2', 'x')).toEqual(planStructures(L2, 'stage2', 'x'));
  });

  it('층별 종류: 1층 = 공통 + 1층 테마, 2층 = 공통 + 2층 테마, 3층 이상 = 공통만', () => {
    for (const s of seeds) {
      for (const [stage, allowed] of [
        ['stage1', ['stage1']],
        ['stage2', ['stage2']],
        ['stage3', []],
        ['stage5', []],
      ] as const) {
        const { list } = floor(stage, s);
        for (const p of list) {
          const d = structureDef(p.kind);
          if (d.floors === 'all') continue;
          expect(allowed as readonly string[]).toEqual(expect.arrayContaining(d.floors));
        }
      }
    }
  });

  it('예산: 공통·테마 종류 수가 [min, max] 안 (filler 제외), 공통 C2·C3·C5 는 매 층', () => {
    const B = STRUCTURE_RULES.budget;
    for (const s of seeds) {
      for (const stage of ['stage1', 'stage2']) {
        const { list } = floor(stage, s);
        const common = budgetKinds(list, 'common');
        const theme = budgetKinds(list, 'theme');
        expect(common.size).toBeLessThanOrEqual(B.common[1]);
        expect(theme.size).toBeLessThanOrEqual(B.theme[1]);
        expect(theme.size).toBeGreaterThanOrEqual(Math.min(B.theme[0], 2));
        expect([...common].sort()).toEqual(['campfire', 'chest', 'grave']);
      }
    }
  });

  it('방당 E형 최대 2, 같은 종류 방당 maxPerRoom, 구조물끼리 겹치지 않음', () => {
    for (const s of seeds) {
      for (const stage of ['stage1', 'stage2', 'stage3']) {
        const { list } = floor(stage, s);
        const perRoom = new Map<string, number>();
        const perKind = new Map<string, number>();
        const seen = new Set<string>();
        for (const p of list) {
          if (INTERACT_KINDS.includes(p.kind)) perRoom.set(p.roomId, (perRoom.get(p.roomId) ?? 0) + 1);
          const k = `${p.roomId}:${p.kind}`;
          perKind.set(k, (perKind.get(k) ?? 0) + 1);
          expect(perKind.get(k)).toBeLessThanOrEqual(structureDef(p.kind).maxPerRoom);
          for (let y = p.ty; y < p.ty + p.h; y++)
            for (let x = p.tx; x < p.tx + p.w; x++) {
              expect(seen.has(`${x},${y}`)).toBe(false);
              seen.add(`${x},${y}`);
            }
        }
        for (const n of perRoom.values()) expect(n).toBeLessThanOrEqual(STRUCTURE_RULES.budget.maxInteractPerRoom);
      }
    }
  });

  it('방 안 바닥에만, 문·시작점·보스 여유 칸을 피한다 (숨은 벽은 벽선 위)', () => {
    for (const s of seeds) {
      for (const stage of ['stage1', 'stage2']) {
        const { layout, list } = floor(stage, s);
        for (const p of list) {
          const room = layout.rooms.find((r) => r.id === p.roomId)!;
          if (p.kind === 'hiddenWall') {
            for (const o of p.cellar!.opening) expect(layout.tiles[o.y][o.x]).toBe(TileId.Wall);
            for (let y = p.cellar!.inner.y; y < p.cellar!.inner.y + p.cellar!.inner.h; y++)
              for (let x = p.cellar!.inner.x; x < p.cellar!.inner.x + p.cellar!.inner.w; x++)
                expect(layout.tiles[y][x]).toBe(TileId.Void);
            continue;
          }
          const blocked = baseBlocked(room);
          for (let y = p.ty; y < p.ty + p.h; y++)
            for (let x = p.tx; x < p.tx + p.w; x++) {
              expect(layout.tiles[y][x]).toBe(TileId.Floor);
              expect(blocked.has(`${x},${y}`)).toBe(false);
            }
          expect(structureDef(p.kind).roomTypes[room.type] ?? 0).toBeGreaterThan(0);
        }
      }
    }
  });

  it('짐(C1)은 시작·시련·휴식 방에 방당 3~6, 보스 방엔 없음. 술통은 1층만', () => {
    for (const s of seeds) {
      const { layout, list } = floor('stage1', s);
      for (const room of layout.rooms) {
        const n = list.filter((p) => p.kind === 'crate' && p.roomId === room.id).length;
        if (room.type === 'boss') expect(n).toBe(0);
        else expect(n).toBeLessThanOrEqual(6);
      }
      expect(list.some((p) => p.kind === 'cask')).toBe(true);
      expect(floor('stage2', s).list.some((p) => p.kind === 'cask')).toBe(false);
    }
  });

  it('층별 시트 id: 짐은 1층 crate_f1 · 2층 crate_f2 · 3층 crate_f1(재사용)', () => {
    expect(floor('stage1', 1).list.find((p) => p.kind === 'crate')?.sprite).toBe('crate_f1');
    expect(floor('stage2', 1).list.find((p) => p.kind === 'crate')?.sprite).toBe('crate_f2');
    expect(floor('stage3', 1).list.find((p) => p.kind === 'crate')?.sprite).toBe('crate_f1');
    expect(floor('stage1', 1).list.find((p) => p.kind === 'campfire')?.sprite).toBe('bonfire');
  });

  it('forceAll: 그 층에 나올 수 있는 종류가 (자리가 있으면) 전부 나온다', () => {
    for (const s of seeds.slice(0, 5)) {
      for (const stage of ['stage1', 'stage2']) {
        const layout = layoutOf(stage, s);
        const list = planStructures(layout, stage, `${s}:${stage}`, { forceAll: true });
        const kinds = new Set(list.map((p) => p.kind));
        const want = [...STRUCTURE_DEFS.values()]
          .filter((d) => d.floors === 'all' || d.floors.includes(stage))
          .map((d) => d.id)
          .filter((k) => k !== 'hiddenWall'); // 저장고 자리가 없는 층도 있다
        for (const k of want) expect(kinds.has(k)).toBe(true);
      }
    }
  });

  it('단단한 칸 목록은 바닥 위 단단한 구조물만 (숨은 벽 제외)', () => {
    const { list } = floor('stage1', 'abc');
    const solid = solidStructureTiles(list);
    const all = structureTiles(list);
    for (const k of solid) expect(all.has(k)).toBe(true);
    const ring = list.find((p) => p.kind === 'roulette' || p.kind === 'dogRing');
    if (ring) expect(solid.has(`${ring.tx},${ring.ty}`)).toBe(false);
  });

  it('소품은 구조물 칸을 피한다 (소품보다 먼저 배치)', () => {
    const { layout, list } = floor('stage1', 'props');
    const tiles = structureTiles(list);
    const props = [
      { index: 30, name: 'a', solid: false },
      { index: 31, name: 'b', solid: true },
    ];
    const placed = planProps(layout, props, 'props', undefined, tiles);
    expect(placed.length).toBeGreaterThan(0);
    for (const p of placed) expect(tiles.has(`${p.x},${p.y}`)).toBe(false);
  });
});
