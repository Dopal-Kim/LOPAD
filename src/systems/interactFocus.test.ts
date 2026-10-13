import { describe, expect, it } from 'vitest';
import { pickFocus } from './interactFocus';

describe('62 I E 대상 하나 (pickFocus)', () => {
  it('후보가 없으면 null', () => {
    expect(pickFocus([])).toBeNull();
    expect(pickFocus([null, undefined])).toBeNull();
  });

  it('가장 가까운 곳 하나 — 노점 앞에서는 옆 구조물보다 노점 (P0-N2)', () => {
    expect(
      pickFocus([
        { source: 'structure', dist: 30 },
        { source: 'stall', dist: 6 },
      ]),
    ).toBe('stall');
  });

  it('사연 NPC 앞에서는 궤짝보다 NPC (P1-N3)', () => {
    expect(
      pickFocus([
        { source: 'structure', dist: 40 },
        { source: 'prop', dist: 12 },
      ]),
    ).toBe('prop');
    expect(
      pickFocus([
        { source: 'structure', dist: 8 },
        { source: 'prop', dist: 40 },
      ]),
    ).toBe('structure');
  });

  it('같은 거리면 상인 → 노점 → 소품 → 구조물', () => {
    expect(
      pickFocus([
        { source: 'structure', dist: 10 },
        { source: 'prop', dist: 10 },
        { source: 'keeper', dist: 10 },
      ]),
    ).toBe('keeper');
  });

  it('무한·NaN 거리는 버린다', () => {
    expect(
      pickFocus([
        { source: 'keeper', dist: Number.NaN },
        { source: 'structure', dist: Infinity },
        { source: 'prop', dist: 20 },
      ]),
    ).toBe('prop');
  });
});
