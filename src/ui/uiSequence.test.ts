import { afterEach, describe, expect, it } from 'vitest';
import {
  MENU_WAIT_MAX_MS,
  gradeCardGone,
  gradeCardShown,
  menuWaitMs,
  sequenceActive,
  sequenceExtend,
  sequenceGone,
  sequenceShown,
  setSequenceClock,
} from './uiSequence';

let t = 0;
const tick = (ms: number): void => {
  t += ms;
};

describe('uiSequence', () => {
  afterEach(() => setSequenceClock(null));

  it('도장 카드: 메뉴는 최대 1.2초 기다리고 카드는 그때까지로 줄어든다', () => {
    t = 0;
    setSequenceClock(() => t);
    let shortened = -1;
    gradeCardShown(2800, (ms) => (shortened = ms));
    expect(menuWaitMs()).toBe(MENU_WAIT_MAX_MS);
    expect(shortened).toBe(MENU_WAIT_MAX_MS);
    gradeCardGone();
    expect(menuWaitMs()).toBe(0);
  });

  it('보스 처치 카드: 줄이지 않고 끝까지, 대사가 이어지면 늘이되 deadline 까지', () => {
    t = 0;
    setSequenceClock(() => t);
    sequenceShown('boss', 2800, { deadlineMs: 4500 });
    tick(1000);
    expect(menuWaitMs()).toBe(1800);
    sequenceExtend('boss', 3000);
    expect(menuWaitMs()).toBe(3000);
    sequenceExtend('boss', 9000);
    expect(menuWaitMs()).toBe(3500);
    expect(sequenceActive('boss')).toBe(true);
    tick(3600);
    expect(menuWaitMs()).toBe(0);
    expect(sequenceActive('boss')).toBe(false);
    sequenceGone('boss');
  });

  it('여럿이면 가장 긴 기다림, 시스템이 늦게 열면 0', () => {
    t = 0;
    setSequenceClock(() => t);
    sequenceShown('a', 500);
    sequenceShown('b', 900);
    expect(menuWaitMs()).toBe(900);
    tick(1000);
    expect(menuWaitMs()).toBe(0);
  });
});
