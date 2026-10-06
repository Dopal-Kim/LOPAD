/**
 * 61 단계 5 (P13 §5 '원격' 태그 1층 표시 확인): 1층 런에서 원격 태그 갈래(대검 파쇄 = 원격·중량)를 골라도 점수·Tab 태그 목록에
 * 원격이 나오지 않는다 (시험장 floor null 은 전부 — 의도).
 */
import { describe, expect, it } from 'vitest';
import { WEAPONS } from '../../data';
import { PassiveSet } from '../passives';
import { WeaponState } from '../weapon/weapons';
import { BuildState, uiTags } from './BuildState';

describe('층 노출: 꺼진 태그는 갈래 태그로도 세지 않는다', () => {
  it('1층 · 대검 파쇄(원격·중량) → 중량만, 시험장(null) → 원격도', () => {
    const w = new WeaponState('greatsword', WEAPONS.greatsword);
    w.setPath(['crush']);
    const b = new BuildState();
    b.setFloor(1);
    const mods = b.mods(new PassiveSet(), w);
    expect(mods.scores.ranged).toBe(0);
    expect(uiTags(mods, 1).map((t) => t.id)).toEqual(['weight']);
    b.setFloor(null);
    const lab = b.mods(new PassiveSet(), w);
    expect(
      uiTags(lab, null)
        .map((t) => t.id)
        .sort(),
    ).toEqual(['ranged', 'weight']);
  });
});
