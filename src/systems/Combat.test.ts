import { describe, expect, it } from 'vitest';
import { applyDefense } from './Combat';

describe('applyDefense', () => {
  it('평면 차감', () => {
    expect(applyDefense(10, 3)).toBe(7);
  });
  it('최소 1', () => {
    expect(applyDefense(2, 5)).toBe(1);
  });
});
