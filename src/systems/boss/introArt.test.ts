import { describe, expect, it } from 'vitest';
import { introArtPlan } from './introArt';

/** 아트 2 stage1_intro 메타 (16열 · 걸음 0~7 · 건배 유지 10~11 · 포효 12) */
const META = {
  frames: 16,
  frameDurationsMs: [150, 150, 150, 150, 150, 150, 150, 150, 220, 170, 170, 170, 220, 220, 150, 150],
  walkLoop: [0, 7],
  toastLoop: [10, 11],
  roarFrame: 12,
  stride: { px: 86, cycleMs: 1200 },
};

describe('61 E 보스 등장 동작 시간표', () => {
  it('걸음 2바퀴 → 딸꾹·건배 올림 → 건배 유지 → 포효 (데이터 시각)', () => {
    const p = introArtPlan(META, { walkLoops: 2, roarAtMs: 3800, speechAtMs: 3100 })!;
    expect(p.walkCols).toEqual([0, 1, 2, 3, 4, 5, 6, 7]);
    expect(p.walkMs).toBe(2400);
    expect(p.walkDots).toBe(172);
    expect(p.raiseCols).toEqual([8, 9]);
    expect(p.toastCols).toEqual([10, 11]);
    expect(p.roarCols).toEqual([12, 13, 14, 15]);
    expect(p.roarAtMs).toBe(3800);
    // 포효·대기가 전투 시작(5200) 전에 끝난다
    expect(p.roarAtMs + p.roarMs).toBeLessThan(5200);
  });

  it('포효 시각이 건배 올림보다 이르면 올림 뒤로 미룬다 · 데이터가 없으면 대사 0.7초 뒤', () => {
    expect(introArtPlan(META, { walkLoops: 2, roarAtMs: 1000, speechAtMs: 3100 })!.roarAtMs).toBe(2400 + 390);
    expect(introArtPlan(META, { speechAtMs: 3100 })!.roarAtMs).toBe(3800);
  });

  it('열 표가 없거나 순서가 틀리면 null', () => {
    expect(introArtPlan({ frames: 16 }, { speechAtMs: 0 })).toBeNull();
    expect(introArtPlan({ ...META, roarFrame: 9 }, { speechAtMs: 0 })).toBeNull();
  });
});
