import { describe, expect, it } from 'vitest';
import { COVER_PILLAR } from '../core/Constants';
import { coverColumn, coverFrameIndex, coverRow } from './coverFrame';

describe('62 I 엄폐 칸 돌기둥 프레임 (art §31-9 pillar_stone)', () => {
  it('지역 행: waste·outer·gate·hall, 양조 = outer, 모르는·없는 지역 = 0행', () => {
    expect(['waste', 'outer', 'gate', 'hall'].map((r) => coverRow(r))).toEqual([0, 1, 2, 3]);
    expect(coverRow('brewery')).toBe(1);
    expect(coverRow(null)).toBe(0);
    expect(coverRow('nowhere')).toBe(0);
  });

  it('상태 열은 결정적이고 0..2, 온전이 가장 많다', () => {
    const n = [0, 0, 0];
    for (let x = 0; x < 40; x++)
      for (let y = 0; y < 40; y++) {
        const c = coverColumn(x, y, 7);
        expect(c).toBe(coverColumn(x, y, 7));
        n[c]++;
      }
    expect(n[0]).toBeGreaterThan(n[1]);
    expect(n[1]).toBeGreaterThan(n[2]);
    expect(n[2]).toBeGreaterThan(0);
  });

  it('프레임 = 행 × 3 + 열', () => {
    const cols = COVER_PILLAR.STATE_WEIGHTS.length;
    expect(coverFrameIndex('hall', 3, 4, 1)).toBe(3 * cols + coverColumn(3, 4, 1));
  });
});
