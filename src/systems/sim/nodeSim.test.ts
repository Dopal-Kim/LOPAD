import { describe, expect, it } from 'vitest';
import { ECONOMY, ENEMIES, PLAYER_DATA, WEAPONS } from '../../data';
import { estimateFloor, FLOOR_PATHS } from './floorSim';
import { estimateBattleNode, meleeSequence, simPlayerOf, timeToKill, weaponDps, type SimWeapon } from './nodeSim';

const player = simPlayerOf({ attack: 5, defense: 3, crit: 0, speedTiles: 6 }, 1.5);

describe('헤드리스 수치 추정 (61라운드 P9)', () => {
  it('연격: 타 간격 = cancelFromMs, 마지막 타 = durationMs + 회복, 순환이면 계속 cancelFromMs', () => {
    const w = {
      kind: 'melee',
      damageMult: 1,
      critBonus: 0,
      combo: {
        finisherRecoverMs: 100,
        hits: [
          { damageMult: 1, durationMs: 400, cancelFromMs: 300 },
          { damageMult: 2, durationMs: 500, cancelFromMs: 450 },
        ],
      },
    } as unknown as SimWeapon;
    expect(meleeSequence(player, w)).toEqual([
      { dmg: 5, ms: 300 },
      { dmg: 10, ms: 600 },
    ]);
    expect(weaponDps(player, w).dps).toBeCloseTo((15 / 900) * 1000);
    expect(meleeSequence(player, { ...w, combo: { ...w.combo!, loop: true } } as SimWeapon)[1].ms).toBe(450);
    // HP 12: 5 → 10(죽음) = 300 + 600/2
    expect(timeToKill(player, w, 12)).toBe(600);
  });

  it('치명 기대값: 무기 쪽 expectedHit 와 같음 ((1−p)·보통 + p·치명)', () => {
    const w = {
      kind: 'melee',
      damageMult: 1,
      critBonus: 50,
      combo: { finisherRecoverMs: 0, hits: [{ damageMult: 4, durationMs: 100, cancelFromMs: 100 }] },
    } as unknown as SimWeapon;
    expect(meleeSequence(player, w)[0].dmg).toBe(25); // 20 × 1.25
  });

  it('노드: 처치 수 = 웨이브 적 합, 시간·피해는 양수', () => {
    const e = estimateBattleNode({
      player,
      weapon: WEAPONS.katana,
      enemies: ENEMIES,
      waves: [[{ enemy: 'dummy', count: 4 }]],
      enemyScale: { hp: 1, attack: 1 },
      spawnDistTiles: 10,
    });
    expect(e.kills).toBe(4);
    expect(e.combatMs).toBeGreaterThan(0);
    expect(e.damageTaken).toBeGreaterThan(0);
  });

  it('현재 데이터: 무기 4종 DPS · 1층 노드·층 추정 (표 출력)', () => {
    const p = simPlayerOf(PLAYER_DATA.stats, ECONOMY.critDamageMult);
    const rows: string[] = [];
    for (const id of ['dagger', 'katana', 'greatsword', 'bow']) {
      if (!WEAPONS[id]) continue;
      const d = weaponDps(p, WEAPONS[id]);
      expect(Number.isFinite(d.dps)).toBe(true);
      rows.push(
        `${id.padEnd(10)} DPS ${d.dps.toFixed(1).padStart(5)}  평균 타 ${d.avgHit.toFixed(1)}  최대 대상 ${d.targets.toFixed(2)}`,
      );
      for (const path of Object.keys(FLOOR_PATHS)) {
        const f = estimateFloor(id, 'stage1', path);
        expect(f.totalMs).toBeGreaterThan(0);
        rows.push(
          `   ${path.padEnd(9)} ${(f.totalMs / 60000).toFixed(1)}분 처치 ${f.kills} 받는 피해 ${f.damageTaken} 개성 ${f.personality}(메뉴 ${f.personalityMenus}) | ` +
            f.nodes.map((n) => `${n.kind} ${(n.ms / 1000).toFixed(0)}s/${n.kills}`).join(' · '),
        );
      }
    }
    console.log(`[sim] 1층 추정 (공격 ${p.attack}, 61 P9 — 가정 SIM)\n${rows.join('\n')}`);
  });
});
