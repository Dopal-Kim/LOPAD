import { describe, expect, it } from 'vitest';
import { BOSSES, validateBosses } from './index';
import { mergeParams, phaseIndexFor, resolvePatternParams } from './bossPatterns';
import type { BossTable } from './types';

describe('보스 패턴 수치 해석 (54라운드 Q4)', () => {
  it('공통 → 페이즈 → 강화 순으로 덮어쓴다', () => {
    const d = BOSSES.stage1;
    expect(resolvePatternParams(d, 0, 'dash')).toMatchObject({ telegraphMs: 700, speedTiles: 16 });
    expect(resolvePatternParams(d, 1, 'dash')).toMatchObject({ telegraphMs: 600, speedTiles: 18 });
    expect(resolvePatternParams(d, 0, 'dash', true)).toMatchObject({ telegraphMs: 550, speedTiles: 20 });
    expect(resolvePatternParams(d, 0, 'dash', true)).not.toHaveProperty('empowered');
    expect(resolvePatternParams(d, 2, 'drunkDash')).toMatchObject({ telegraphSeqMs: [500, 300, 300] });
    expect(resolvePatternParams(d, 0, 'volley')).toBeNull();
  });
  it('얕은 객체는 한 단계 더 합친다', () => {
    expect(mergeParams({ a: 1, o: { x: 1, y: 2 } }, { o: { y: 3 } })).toEqual({ a: 1, o: { x: 1, y: 3 } });
  });
  it('페이즈 판정', () => {
    const ph = BOSSES.stage1.phases;
    expect(phaseIndexFor(1, ph)).toBe(0);
    expect(phaseIndexFor(0.6, ph)).toBe(1);
    expect(phaseIndexFor(0.2, ph)).toBe(2);
  });
  it('검증: 모르는 패턴·빠진 수치·잘못된 다음 패턴은 오류', () => {
    const base = JSON.parse(JSON.stringify({ x: BOSSES.stage1 })) as BossTable;
    expect(() => validateBosses(base)).not.toThrow();
    const a = JSON.parse(JSON.stringify(base)) as BossTable;
    (a.x.phases[0].pick as string[]).push('nope');
    expect(() => validateBosses(a)).toThrow(/알 수 없는 패턴/);
    const b = JSON.parse(JSON.stringify(base)) as BossTable;
    delete (b.x.patterns.slam as Record<string, unknown>).radiusTiles;
    expect(() => validateBosses(b)).toThrow(/radiusTiles/);
    const c = JSON.parse(JSON.stringify(base)) as BossTable;
    (c.x.patterns.spin as Record<string, unknown>).next = 'nope';
    expect(() => validateBosses(c)).toThrow();
  });
});
