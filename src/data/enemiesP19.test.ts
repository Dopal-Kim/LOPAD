import { describe, expect, it } from 'vitest';
import { ENEMIES } from './index';
import { TELEGRAPH_TIER } from '../core/Constants';

/** P19 계약 free-combat §2: 예고 ≥ 350ms (위험 ≥ 500ms) · 접촉 피해 없음 (근접 적은 휘두르기) */
describe('P19 적 예고 규칙', () => {
  it('모든 일반 적 공격에 최소 예고', () => {
    for (const [id, e] of Object.entries(ENEMIES)) {
      if (e.swing) expect(e.swing.telegraphMs, id).toBeGreaterThanOrEqual(TELEGRAPH_TIER.MIN_MS);
      if (e.ranged) expect(e.ranged.telegraphMs ?? 0, id).toBeGreaterThanOrEqual(TELEGRAPH_TIER.MIN_MS);
      if (e.charge) expect(e.charge.telegraphMs, id).toBeGreaterThanOrEqual(TELEGRAPH_TIER.MIN_MS);
      if (e.bomb) {
        expect(e.bomb.fuseMs, id).toBeGreaterThanOrEqual(TELEGRAPH_TIER.DANGER_MIN_MS);
        expect(e.bomb.deathFuseMs, id).toBeGreaterThanOrEqual(TELEGRAPH_TIER.MIN_MS);
      }
      // 화염 술병: 비행만으로도 위험 최소를 넘는다 (놓음 시각은 시트)
      if (e.throw) expect(e.throw.flightMs, id).toBeGreaterThanOrEqual(TELEGRAPH_TIER.DANGER_MIN_MS);
      if (e.behavior === 'chase') expect(e.swing, id).toBeDefined();
    }
  });

  it('새 적 2종 (깃발 고수 · 술배 자폭병)', () => {
    expect(ENEMIES.drummer.behavior).toBe('drum');
    expect(ENEMIES.bomber.behavior).toBe('bomb');
    expect(ENEMIES.dummy.hp).toBe(14);
  });
});
