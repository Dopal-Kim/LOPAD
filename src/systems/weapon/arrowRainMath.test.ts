import { describe, expect, it } from 'vitest';
import { markColumn, rainPoints } from './arrowRainMath';

describe('56라운드 2단계 화살비 규칙', () => {
  it('낙하점은 모두 원 안 (Q52: 원 안 무작위 9곳)', () => {
    let s = 1;
    const rand = () => (s = (s * 16807) % 2147483647) / 2147483647;
    const pts = rainPoints(100, 50, 32, 9, rand);
    expect(pts).toHaveLength(9);
    for (const p of pts) expect(Math.hypot(p.x - 100, p.y - 50)).toBeLessThanOrEqual(32 + 1e-9);
  });

  it('예고 원: 등장 → 첫 낙하까지 대기 루프 → 낙하 → 식음 → 끝', () => {
    const d = [50, 60, 90, 90, 90, 90, 60, 60, 70, 90];
    expect(markColumn(0, 560, 900, d)).toBe(0);
    expect(markColumn(55, 560, 900, d)).toBe(1);
    expect(markColumn(110, 560, 900, d)).toBe(2);
    // 대기 루프 (2~5 반복: 110 + 360 = 470 에서 다시 2)
    expect(markColumn(470, 560, 900, d)).toBe(2);
    expect(markColumn(560, 560, 900, d)).toBe(6);
    expect(markColumn(640, 560, 900, d)).toBe(7);
    expect(markColumn(890, 560, 900, d)).toBe(7);
    expect(markColumn(900, 560, 900, d)).toBe(8);
    expect(markColumn(1000, 560, 900, d)).toBe(9);
    expect(markColumn(1100, 560, 900, d)).toBe(-1);
  });
});
