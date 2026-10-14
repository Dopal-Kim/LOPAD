import { describe, expect, it } from 'vitest';
import { TraitRoll } from './traitRoll';

describe('62 루프 4 술통 굴리기 (TraitRoll)', () => {
  const make = () => {
    const log: string[] = [];
    const roll = new TraitRoll({
      speedPx: 100,
      maxPx: 50,
      trailEveryPx: 20,
      hit: (m) => log.push(`hit:${String(m)}`),
      trail: (x) => log.push(`trail:${x}`),
      burst: (x) => log.push(`burst:${x}`),
    });
    return { roll, log };
  };

  it('적은 한 번씩만 맞고 꿰뚫고 지나간다 · 자국은 간격마다 · 최대 거리에서 끝', () => {
    const { roll, log } = make();
    const d = { x: 1, y: 0 };
    expect(roll.step(10, 0, 10, d, ['a'], false)).toBe('roll');
    expect(roll.step(20, 0, 10, d, ['a', 'b'], false)).toBe('roll');
    expect(roll.step(40, 0, 20, d, [], false)).toBe('roll');
    expect(roll.step(50, 0, 10, d, ['b'], false)).toBe('end');
    expect(log).toEqual(['hit:a', 'hit:b', 'trail:20', 'trail:40']);
  });

  it('불에 닿으면 그 자리에서 터진다 (맞힘·자국 없이)', () => {
    const { roll, log } = make();
    expect(roll.step(5, 0, 5, { x: 1, y: 0 }, ['a'], true)).toBe('burst');
    expect(log).toEqual(['burst:5']);
  });
});
