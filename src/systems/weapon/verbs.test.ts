import { describe, expect, it } from 'vitest';
import { VERB_KEYS } from '../../core/Constants';
import { WEAPONS } from '../../data';
import { WeaponState } from './weapons';
import { VERB_SLOTS, verbsLine, weaponVerbs } from './verbs';

describe('61라운드 P1 4동사 표시 (스냅샷 weaponVerbs)', () => {
  it('무기 4종 모두 좌·우·Space·좌 홀드 4칸, 키캡은 Constants', () => {
    for (const [id, def] of Object.entries(WEAPONS)) {
      const v = weaponVerbs(id, def, []);
      expect(v.weapon).toBe(id);
      expect(v.verbs.map((x) => x.slot)).toEqual([...VERB_SLOTS]);
      expect(v.verbs.map((x) => x.key)).toEqual(VERB_SLOTS.map((s) => VERB_KEYS[s]));
      for (const x of v.verbs) {
        expect(x.name.length).toBeGreaterThan(0);
        expect(x.branch).toBeNull();
      }
    }
  });

  it('칼 좌 홀드 = 발도 (F 넣기 흡수) — 선풍이면 회전 베기로 바뀌고 branch 에 갈래 이름', () => {
    const w = new WeaponState('katana', WEAPONS.katana);
    expect(weaponVerbs(w.id, w.def, w.nodes).verbs[3].name).toBe('발도');
    w.choose('iai');
    const hold = weaponVerbs(w.id, w.def, w.nodes).verbs[3];
    expect(hold.name).toContain('회전 베기');
    expect(hold.branch).toBe(w.evolution!.name);
    // 2단을 골라도 1단이 바꾼 칸은 그대로
    w.choose('vortex');
    expect(weaponVerbs(w.id, w.def, w.nodes).verbs[3].name).toContain('회전 베기');
  });

  it('갈래마다 바꾸는 칸: 대검 파쇄 = 대쉬, 중압 = 시그니처 · 단검 질풍 = 대쉬 · 활 속사 = 홀드, 저격 = 시그니처', () => {
    const slotOf = (id: string, branch: string) =>
      weaponVerbs(id, WEAPONS[id], [WEAPONS[id].personality.branches.find((b) => b.id === branch)!]).verbs.find(
        (x) => x.branch !== null,
      )?.slot;
    expect(slotOf('greatsword', 'crush')).toBe('dash');
    expect(slotOf('greatsword', 'weight')).toBe('signature');
    expect(slotOf('dagger', 'twin')).toBe('signature');
    expect(slotOf('dagger', 'gale')).toBe('dash');
    expect(slotOf('bow', 'rapid')).toBe('hold');
    expect(slotOf('bow', 'snipe')).toBe('signature');
  });

  it('시험장 한 줄 요약', () => {
    const line = verbsLine(weaponVerbs('bow', WEAPONS.bow, []));
    expect(line).toContain('홀드 화살비');
    expect(line.split(' · ').length).toBeGreaterThanOrEqual(4);
  });
});
