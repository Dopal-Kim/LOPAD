import { describe, expect, it } from 'vitest';
import { ECONOMY, PLAYER_DATA, WEAPONS, WEAPON_RULES } from '../../data';
import { baselineDps, bowPerfectDps, bowTapDps, comboCycleMs, expectedHit, meleeDps, sustainedSpeed } from './dps';

/** 61라운드 P2 수치 기준선 — 데이터를 바꾸면 이 테스트가 목표 대역을 지킨다 */
const base = WEAPON_RULES.dpsBaseline!;
const opts = { attack: base.attack, crit: PLAYER_DATA.stats.crit, critMult: ECONOMY.critDamageMult };

describe('61라운드 P2 DPS 기준선 (공격 5)', () => {
  it('기준선 데이터: 무기 4종 모두 목표 대역이 있다', () => {
    expect(base.attack).toBe(5);
    for (const id of ['katana', 'greatsword', 'dagger', 'bow']) expect(base.targets[id]).toHaveLength(2);
  });

  for (const [id, [lo, hi]] of Object.entries(base.targets)) {
    it(`${id}: 기본 공격 지속 DPS 가 ${lo}~${hi}`, () => {
      const e = baselineDps(WEAPONS[id], opts);
      expect(e.dps).toBeGreaterThanOrEqual(lo);
      expect(e.dps).toBeLessThanOrEqual(hi);
    });
  }

  it('순위: 단검 > 칼 > 대검(단일 대상 — 대신 경직·범위) > 활 짧게 쏘기', () => {
    const d = (id: string) => baselineDps(WEAPONS[id], opts).dps;
    expect(d('dagger')).toBeGreaterThan(d('katana'));
    expect(d('katana')).toBeGreaterThan(d('greatsword'));
    expect(d('greatsword')).toBeGreaterThan(d('bow'));
  });

  it('활 완벽 놓기 반복은 짧게 쏘기보다 세지만 근접 기준선을 넘지 않는다 (기술 상한)', () => {
    const tap = bowTapDps(WEAPONS.bow, opts).dps;
    const perfect = bowPerfectDps(WEAPONS.bow, opts).dps;
    expect(perfect).toBeGreaterThan(tap);
    expect(perfect).toBeLessThan(base.targets.katana[0]);
  });
});

describe('DPS 계산식', () => {
  it('한 타 = 정수 반올림, 치명 기대값', () => {
    expect(expectedHit(5, 1, 1, 0, 1.5)).toBe(5);
    // 5 × 0.9 × 0.66 = 2.97 → 3, 치명 4.455 → 4
    expect(expectedHit(5, 0.9, 0.66, 0.2, 1.5)).toBeCloseTo(0.8 * 3 + 0.2 * 4);
  });

  it('연격 한 바퀴: 마지막 타 = 길이 + 회복 (순환이면 다음 타 허용만), 공속으로 나눈다', () => {
    const c = {
      shape: 'arc' as const,
      bufferMs: 0,
      resetMs: 0,
      finisherRecoverMs: 100,
      hits: [
        { damageMult: 1, sizeMult: 1, durationMs: 300, cancelFromMs: 200, activeMs: 10 },
        { damageMult: 1, sizeMult: 1, durationMs: 400, cancelFromMs: 300, activeMs: 10 },
      ],
    };
    expect(comboCycleMs(c)).toBe(200 + 400 + 100);
    expect(comboCycleMs({ ...c, loop: true })).toBe(200 + 300);
    expect(comboCycleMs(c, 2)).toBe(350);
  });

  it('지속 공속: 단검 = 가속 최대 단 · 대검 = 관성 최대 · 칼 = 1', () => {
    expect(sustainedSpeed(WEAPONS.katana)).toBe(1);
    const r = WEAPONS.dagger.resource!;
    expect(sustainedSpeed(WEAPONS.dagger)).toBe(r.kind === 'heat' ? r.speedMults[r.speedMults.length - 1] : 0);
    expect(sustainedSpeed(WEAPONS.greatsword)).toBeCloseTo(1 + WEAPONS.greatsword.combo!.momentum!.max);
  });

  it('61라운드 SY-3: 단검 가속 상한 ×1.25 (옛 과열 ×1.5)', () => {
    expect(sustainedSpeed(WEAPONS.dagger)).toBeLessThanOrEqual(1.25);
  });

  it('근접 연격이 없으면 0, 활 짧게 쏘기는 장전 시간을 넣는다', () => {
    expect(meleeDps(WEAPONS.bow, opts).dps).toBe(0);
    const b = bowTapDps(WEAPONS.bow, opts);
    const R = WEAPONS.bow.ranged!;
    const res = WEAPONS.bow.resource!;
    expect(b.cycleMs).toBe(
      (res.kind === 'ammo' ? res.max : 1) * R.cooldownMs + (res.kind === 'ammo' ? res.reloadMs : 0),
    );
  });
});
