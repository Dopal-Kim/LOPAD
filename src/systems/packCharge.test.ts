import { describe, expect, it } from 'vitest';
import { PackCharge } from './packCharge';

const P = { minCount: 3, rangeTiles: 6, speedMult: 1.4, durationMs: 2000, cooldownMs: 4000 };

describe('집단 돌격 (35라운드 2단계)', () => {
  it('3마리 이상 + 6칸 안이면 발동, 2초 유지, 그 뒤 쿨타임', () => {
    const pack = new PackCharge();
    expect(pack.report('dummy', P, 2, 3, 1000)).toBe(false); // 수 부족
    expect(pack.report('dummy', P, 3, 8, 1000)).toBe(false); // 거리 밖
    expect(pack.report('dummy', P, 3, 5, 1000)).toBe(true); // 발동
    expect(pack.startedAt('dummy', P)).toBe(1000);
    expect(pack.report('dummy', P, 3, 20, 2500)).toBe(true); // 멀어져도 유지
    expect(pack.isActive('dummy', 2999)).toBe(true);
    expect(pack.report('dummy', P, 3, 2, 3000)).toBe(false); // 끝 → 쿨타임
    expect(pack.report('dummy', P, 3, 2, 6999)).toBe(false);
    expect(pack.report('dummy', P, 3, 2, 7000)).toBe(true); // 쿨타임 끝 → 재발동
  });

  it('적 종류별로 따로 관리하고 reset 으로 비운다', () => {
    const pack = new PackCharge();
    expect(pack.report('dummy', P, 3, 1, 0)).toBe(true);
    expect(pack.isActive('archer', 0)).toBe(false);
    pack.reset();
    expect(pack.isActive('dummy', 100)).toBe(false);
  });
});
