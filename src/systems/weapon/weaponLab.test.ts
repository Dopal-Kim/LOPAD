import { describe, expect, it } from 'vitest';
import { WEAPONS } from '../../data';
import { WeaponState } from './weapons';
import { LAB_CANCEL_KEY, labBranchMenu, labWeaponMenu } from './weaponLab';

describe('49라운드 무기 시험장 메뉴', () => {
  it('lab: 무기 4종 + 각성 갈래 + 닫기', () => {
    const { lines, choices } = labWeaponMenu(WEAPONS, 'katana');
    expect(choices.map((c) => c.weaponId)).toEqual(Object.keys(WEAPONS));
    expect(lines.length).toBe(Object.keys(WEAPONS).length + 2);
    expect(lines.find((l) => l.label.includes('(지금)'))?.key).toBe('1');
    expect(lines[lines.length - 1].key).toBe(LAB_CANCEL_KEY);
  });

  it('labBranch: 기본 + 1차 갈래 3 + 2차 길 6 → 고른 경로가 트리에서 유효하다 (61 G)', () => {
    for (const [id, def] of Object.entries(WEAPONS)) {
      const { lines, actions } = labBranchMenu(def, [], {
        gauge: 0,
        next: { at: 30, name: '개성 발현' },
        curseActive: false,
      });
      const paths = [...actions.values()].filter((a) => a.kind === 'path');
      expect(paths.length).toBe(10);
      expect(new Set(lines.map((l) => l.key)).size).toBe(lines.length);
      expect([...actions.values()].some((a) => a.kind === 'gauge')).toBe(true);
      for (const a of paths) {
        if (a.kind !== 'path') continue;
        const w = new WeaponState(id, def);
        w.setPath(a.path);
        expect(w.path).toEqual(a.path);
      }
    }
  });

  it('현재 경로 표시 · 갈래·길 이름 바꿔 쓰기 · 게이지 줄', () => {
    const def = WEAPONS.greatsword;
    const b = def.personality.branches[0];
    const { lines } = labBranchMenu(def, [b.id], {
      gauge: 95,
      next: { at: 150, name: '개성 발현' },
      curseActive: true,
      names: { [b.id]: { name: '파쇄', line: '땅을 부수며 뛰어드는 대검' } },
    });
    expect(lines.some((l) => l.label === `└ 파쇄 (지금)`)).toBe(true);
    expect(lines.filter((l) => l.label.startsWith('  └ ')).length).toBe(6);
    expect(lines.filter((l) => l.label.startsWith('└ ')).length).toBe(3);
    expect(lines.some((l) => l.label.includes('지금 95'))).toBe(true);
    expect(lines.find((l) => l.kind === 'curse')?.enabled).toBe(false);
  });
});
