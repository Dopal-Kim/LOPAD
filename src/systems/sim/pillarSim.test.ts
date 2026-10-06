import { describe, expect, it } from 'vitest';
import { ECONOMY, PLAYER_DATA, WEAPONS } from '../../data';
import { simPlayerOf, weaponDps } from './nodeSim';
import { pillarSimTable, simulatePillarFight } from './pillarSim';

describe('61 P13 §3 기둥 숨기 전략 시뮬 (1층 만취 · 돌진·내리찍기만)', () => {
  it('결정적: 같은 시드면 같은 결과', () => {
    const o = { rules: 'new' as const, strategy: 'hider' as const, dps: 20, seed: 7 };
    expect(simulatePillarFight(o)).toEqual(simulatePillarFight(o));
  });

  it('새 규칙(무너짐·포물선 술병·우회)에서 기둥 숨기의 승률이 떨어지거나 받는 피해·시간이 늘어난다 — 표 출력', () => {
    const p = simPlayerOf(PLAYER_DATA.stats, ECONOMY.critDamageMult);
    const lines: string[] = [];
    for (const id of ['katana', 'greatsword', 'dagger']) {
      const dps = weaponDps(p, WEAPONS[id]).dps;
      const rows = pillarSimTable(dps, 24, 0.7);
      for (const r of rows)
        lines.push(
          `${id.padEnd(10)} ${r.strategy.padEnd(7)} ${r.rules} | 승률 ${(r.winRate * 100).toFixed(0).padStart(3)}% · 이긴 판 ${r.winSec}초 · 받은 피해 ${r.damage} · 가려짐 ${(r.hidden * 100).toFixed(0)}% · 벽 경직 ${r.wallStuns} · 무너짐 ${r.collapsed} · 술병 ${r.lobs}`,
        );
      const oldH = rows.find((r) => r.strategy === 'hider' && r.rules === 'old')!;
      const newH = rows.find((r) => r.strategy === 'hider' && r.rules === 'new')!;
      // 기둥은 잠깐의 피난처 — 숨기만으로는 더 쉽지 않다
      expect(newH.hidden).toBeLessThan(oldH.hidden);
      expect(
        newH.winRate <= oldH.winRate &&
          (newH.damage > oldH.damage || newH.winSec > oldH.winSec || newH.winRate < oldH.winRate),
      ).toBe(true);
      expect(newH.lobs).toBeGreaterThan(0);
      // 기둥 없이 싸우는 길(brawler)은 거의 그대로 (술병은 숨을 때만)
      const oldB = rows.find((r) => r.strategy === 'brawler' && r.rules === 'old')!;
      const newB = rows.find((r) => r.strategy === 'brawler' && r.rules === 'new')!;
      expect(newB.lobs).toBeLessThan(1);
      expect(Math.abs(newB.winRate - oldB.winRate)).toBeLessThanOrEqual(0.15);
    }
    console.log(`[sim] 기둥 숨기 (24판, 피하기 0.7)\n${lines.join('\n')}`);
  });
});
