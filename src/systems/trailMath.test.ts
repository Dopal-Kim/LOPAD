import { describe, expect, it } from 'vitest';
import { flashAlphaAt } from './trailMath';

describe('화면 섬광 감쇠', () => {
  it('섬광 알파는 선형 감쇠, 끝나면 0', () => {
    expect(flashAlphaAt(0.2, 40, 0)).toBeCloseTo(0.2, 6);
    expect(flashAlphaAt(0.2, 40, 20)).toBeCloseTo(0.1, 6);
    expect(flashAlphaAt(0.2, 40, 40)).toBe(0);
    expect(flashAlphaAt(0.2, 40, 99)).toBe(0);
    expect(flashAlphaAt(0.2, 0, 0)).toBe(0);
  });
});
