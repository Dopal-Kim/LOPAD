import { describe, expect, it } from 'vitest';
import { PLAYER_DATA } from '../data';
import { isInCombat, sprintStep, type RoomProgress } from './traversal';

const progressOf = (entries: [string, RoomProgress][]) => new Map<string, RoomProgress>(entries);

describe('비전투 판정 (45라운드)', () => {
  it('활성(active) 방이 하나라도 있으면 전투 중', () => {
    expect(
      isInCombat(
        progressOf([
          ['start', 'cleared'],
          ['t1', 'idle'],
        ]),
      ),
    ).toBe(false);
    expect(
      isInCombat(
        progressOf([
          ['start', 'cleared'],
          ['t1', 'active'],
        ]),
      ),
    ).toBe(true);
    expect(isInCombat(progressOf([['boss', 'active']]))).toBe(true);
    expect(isInCombat(new Map())).toBe(false);
  });
});

describe('달리기 배율 (45라운드)', () => {
  const SP = PLAYER_DATA.sprint;

  it('데이터: 1.8배 (45라운드 Q2)', () => {
    expect(SP.speedMult).toBe(1.8);
    expect(SP.accelMs).toBeGreaterThanOrEqual(0);
    expect(SP.decelMs).toBeGreaterThanOrEqual(0);
  });

  it('accelMs 동안 1 → speedMult 로 선형 가속, 넘치지 않는다', () => {
    const p = { speedMult: 1.8, accelMs: 100, decelMs: 50 };
    expect(sprintStep(1, 1.8, 50, p)).toBeCloseTo(1.4);
    expect(sprintStep(1.4, 1.8, 50, p)).toBeCloseTo(1.8);
    expect(sprintStep(1.7, 1.8, 1000, p)).toBe(1.8);
  });

  it('decelMs 동안 speedMult → 1 로 감속, 1 아래로 내려가지 않는다', () => {
    const p = { speedMult: 1.8, accelMs: 100, decelMs: 50 };
    expect(sprintStep(1.8, 1, 25, p)).toBeCloseTo(1.4);
    expect(sprintStep(1.2, 1, 1000, p)).toBe(1);
  });

  it('시간 0 이면 즉시, 같은 값이면 그대로', () => {
    expect(sprintStep(1, 1.8, 16, { speedMult: 1.8, accelMs: 0, decelMs: 0 })).toBe(1.8);
    expect(sprintStep(1.8, 1, 16, { speedMult: 1.8, accelMs: 0, decelMs: 0 })).toBe(1);
    expect(sprintStep(1, 1, 16, SP)).toBe(1);
  });
});
