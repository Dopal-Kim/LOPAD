import { describe, expect, it } from 'vitest';
import { BOSSES, RUN, STAGES } from '.';
import { bootSheetRequests, bossSheetRequests } from '../systems/sprites/sheetSets';
import { bossIdsInScope, floorLoaded, loadFloorCount } from './scope';

const raw = (order: string[], loadFloors?: number) => ({
  run: { order, ...(loadFloors !== undefined ? { loadFloors } : {}) },
  stages: Object.fromEntries(order.map((id, i) => [id, { boss: `b${i + 1}` }])),
});

describe('61라운드 로드 범위 (stages.json run.loadFloors)', () => {
  it('범위 계산: 없거나 잘못되면 전체, 전체를 넘지 않음', () => {
    expect(loadFloorCount(raw(['a', 'b', 'c']))).toBe(3);
    expect(loadFloorCount(raw(['a', 'b', 'c'], 1))).toBe(1);
    expect(loadFloorCount(raw(['a', 'b'], 9))).toBe(2);
    expect(loadFloorCount(raw(['a', 'b'], 0))).toBe(2);
    expect(bossIdsInScope(raw(['a', 'b', 'c'], 2))).toEqual(['b1', 'b2']);
    expect(floorLoaded(3, raw(['a', 'b', 'c'], 2))).toBe(false);
  });

  it('지금은 1층만 로드 — 2~8층 데이터는 그대로 남아 있다', () => {
    expect(loadFloorCount()).toBe(1);
    expect(bossIdsInScope()).toEqual([STAGES.stage1.boss]);
    expect(RUN.order).toHaveLength(8);
    expect(Object.keys(BOSSES)).toContain('emperor');
    // 61라운드 단계 2: 보스 시트는 부팅이 아니라 보스 묶음(보스 노드 preload)
    const bossNames = new Set(bossSheetRequests().map((r) => r.name));
    expect(bossNames.has('emperor')).toBe(false);
    expect(bossNames.has(STAGES.stage1.boss)).toBe(true);
    expect(new Set(bootSheetRequests().map((r) => r.name)).has(STAGES.stage1.boss)).toBe(false);
  });
});
