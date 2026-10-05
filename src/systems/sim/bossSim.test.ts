import { describe, expect, it } from 'vitest';
import { BOSSES, ECONOMY, PLAYER_DATA, WEAPONS } from '../../data';
import { estimateBossFight } from './bossSim';
import { simPlayerOf, weaponDps } from './nodeSim';

describe('61라운드 P6 보스 싸움 길이 (1층 만취, 공격 5)', () => {
  it('무기 4종 모두 90~120초 (파훼 창 ×1.5 · 국면 전환 포함, 등장·처치 연출 제외) — 표 출력', () => {
    const p = simPlayerOf(PLAYER_DATA.stats, ECONOMY.critDamageMult);
    const boss = BOSSES.stage1;
    const rows: string[] = [];
    for (const id of ['dagger', 'katana', 'greatsword', 'bow']) {
      const d = weaponDps(p, WEAPONS[id]);
      const e = estimateBossFight(d.dps, d.kind, boss);
      rows.push(
        `${id.padEnd(10)} DPS ${d.dps.toFixed(1)} → 실효 ${e.effectiveDps.toFixed(1)} | 싸움 ${(e.fightMs / 1000).toFixed(0)}초 ` +
          `(국면 ${e.byPhaseMs.map((m) => (m / 1000).toFixed(0)).join(' / ')}) + 연출 ${(e.showMs / 1000).toFixed(1)}초`,
      );
      expect(e.fightMs).toBeGreaterThanOrEqual(90_000);
      expect(e.fightMs).toBeLessThanOrEqual(120_000);
    }
    console.log(`[sim] 1층 보스 '만취' HP ${boss.hp}\n${rows.join('\n')}`);
  });

  it('파훼 배율이 높을수록 짧다 · 국면 몫 합 = HP', () => {
    const base = { hp: 1000, phases: [{ hpFraction: 1 }, { hpFraction: 0.5 }] };
    const a = estimateBossFight(20, 'melee', base);
    const b = estimateBossFight(20, 'melee', { ...base, breakDamageMult: 2 });
    expect(b.fightMs).toBeLessThan(a.fightMs);
    expect(a.byPhaseMs[0]).toBe(a.byPhaseMs[1]);
    expect(estimateBossFight(0, 'melee', base).fightMs).toBe(Infinity);
  });
});
