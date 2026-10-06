import { describe, expect, it } from 'vitest';
import { aimDrill, insideDrill, nextDrillShape } from './drills';

const S = { radiusPx: 50, lineLengthPx: 200, lineHalfPx: 20, coneRadiusPx: 100, coneHalfAngle: Math.PI / 6 };

describe('훈련 예고 기하', () => {
  it('모든 모양이 처음에는 주인공을 덮는다', () => {
    for (const shape of ['circle', 'line', 'cone'] as const)
      for (const side of [0, 0.25, 0.6]) expect(insideDrill(aimDrill(shape, 100, 100, side, S), 100, 100)).toBe(true);
  });

  it('비켜서면 밖', () => {
    expect(insideDrill(aimDrill('circle', 0, 0, 0, S), 60, 0)).toBe(false);
    // 선 (오른쪽 방향): 옆으로 30px
    expect(insideDrill(aimDrill('line', 0, 0, 0, S), 0, 30)).toBe(false);
    // 부채 (오른쪽): 뒤로 물러나면 밖
    expect(insideDrill(aimDrill('cone', 0, 0, 0, S), -60, 0)).toBe(false);
    expect(insideDrill(aimDrill('cone', 0, 0, 0, S), 0, 60)).toBe(false);
  });

  it('다음 모양: 아직 피하지 못한 것을 차례로', () => {
    const order = ['circle', 'line', 'cone'] as const;
    expect(nextDrillShape(order, new Set(), -1)).toBe(0);
    expect(nextDrillShape(order, new Set(['line']), 0)).toBe(2);
    expect(nextDrillShape(order, new Set(['circle', 'line', 'cone']), 2)).toBe(0);
  });
});
