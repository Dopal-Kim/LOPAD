import { describe, expect, it } from 'vitest';
import { WEAPONS, WEAPON_RULES } from '../data';
import { WeaponState } from './weapons';
import { LAB_CANCEL_KEY, labBranchMenu, labWeaponMenu, nextReinforce } from './weaponLab';

describe('49라운드 무기 시험장 메뉴', () => {
  it('lab: 무기 4종 + 개성 갈래 + 닫기', () => {
    const { lines, choices } = labWeaponMenu(WEAPONS, 'katana');
    expect(choices.map((c) => c.weaponId)).toEqual(Object.keys(WEAPONS));
    expect(lines.length).toBe(Object.keys(WEAPONS).length + 2);
    expect(lines.find((l) => l.label.includes('(지금)'))?.key).toBe('1');
    expect(lines[lines.length - 1].key).toBe(LAB_CANCEL_KEY);
  });

  it('labBranch: 기본 + 1차 2 + 2차 4 → 고른 경로가 트리에서 유효하다', () => {
    for (const [id, def] of Object.entries(WEAPONS)) {
      const { lines, actions } = labBranchMenu(def, [], 0, WEAPON_RULES.reinforceMax);
      const paths = [...actions.values()].filter((a) => a.kind === 'path');
      expect(paths.length).toBe(7);
      expect(new Set(lines.map((l) => l.key)).size).toBe(lines.length);
      for (const a of paths) {
        if (a.kind !== 'path') continue;
        const w = new WeaponState(id, def);
        w.restore({ path: a.path });
        expect(w.path).toEqual(a.path);
      }
    }
  });

  it('현재 경로·강화 표시, 강화는 최대 뒤 0', () => {
    const def = WEAPONS.greatsword;
    const b = def.personality.branches[0];
    const { lines } = labBranchMenu(def, [b.id], 3, 3);
    expect(lines.some((l) => l.label === `└ ${b.name} (지금)`)).toBe(true);
    expect(lines.filter((l) => l.label.startsWith('  └ ')).length).toBe(4);
    expect(lines.filter((l) => l.label.startsWith('└ ')).length).toBe(2);
    expect(lines.some((l) => l.label.includes('3/3 → 0'))).toBe(true);
    expect(nextReinforce(3, 3)).toBe(0);
    expect(nextReinforce(1, 3)).toBe(2);
  });
});
