import { describe, expect, it } from 'vitest';
import { WEAPONS } from '../../data';
import { RESONANCES, TRAITS, plainLine, traitDef } from '../../data/growth';
import { TRAIT_ACTS, type TraitDef } from '../../data/growthTypes';
import { WeaponState } from '../weapon/weapons';
import { pickTraits, traitPool } from './growth';
import { growthMenu } from './growthMenu';
import { activeResonances, newlyActive, partnerTags, resonancesOf } from './resonance';
import { traitFxId, traitIconKey, traitProcSfx } from './traitArt';
import { uiGrowth } from './uiGrowth';

const defs = (...ids: string[]) => ids.map((id) => traitDef(id)!) as TraitDef[];

describe('61 단계 5 (P13) 개성 데이터', () => {
  it('무기마다 14장 · 환경 개성 2장 이상 · act 는 정해진 갈래 · 문구에 숫자 없음', () => {
    for (const w of ['katana', 'greatsword', 'dagger', 'bow']) {
      const mine = TRAITS.filter((t) => t.weapon === w);
      expect(mine).toHaveLength(14);
      expect(mine.filter((t) => t.env).length).toBeGreaterThanOrEqual(2);
      for (const t of mine) {
        expect(TRAIT_ACTS).toContain(t.act);
        expect(plainLine(t.line)).toBe(true);
      }
    }
  });

  it('카드 문구 = 조건 → 행동 한 문장 (마침표·줄바꿈 없음)', () => {
    for (const t of TRAITS) expect(t.line).not.toMatch(/[.\n]/);
  });
});

describe('61 단계 5 (P13) 공명', () => {
  it('무기마다 2~3개, 태그는 기본 개성 두 장 이상', () => {
    for (const w of ['katana', 'greatsword', 'dagger', 'bow']) {
      const list = resonancesOf(w);
      expect(list.length).toBeGreaterThanOrEqual(2);
      expect(list.length).toBeLessThanOrEqual(3);
      for (const r of list)
        expect(TRAITS.filter((t) => t.weapon === w && t.tag === r.tag && !t.branch).length).toBeGreaterThanOrEqual(2);
    }
    expect(RESONANCES).toHaveLength(9);
  });

  it('같은 태그 두 장이면 켜진다 · 한 장이면 짝 태그 · 새로 켜짐', () => {
    expect(activeResonances('katana', defs('k_parryShove'))).toEqual([]);
    expect(partnerTags('katana', defs('k_parryShove'))).toEqual(['insight']);
    const both = defs('k_parryShove', 'k_bladeBind');
    expect(activeResonances('katana', both).map((r) => r.id)).toEqual(['res_katana_insight']);
    expect(newlyActive('katana', defs('k_parryShove'), both).map((r) => r.id)).toEqual(['res_katana_insight']);
    expect(newlyActive('katana', both, both)).toEqual([]);
  });

  it('개성 제시: 한 장 모자란 공명 태그 카드를 한 장 넣는다', () => {
    const pool = traitPool('katana', null, ['k_parryShove']);
    for (let s = 0; s < 20; s++) {
      let i = s;
      const rnd = () => ((i = (i * 9301 + 49297) % 233280) / 233280) % 1;
      const out = pickTraits(pool, 3, rnd, ['insight']);
      expect(out.some((t) => t.tag === 'insight')).toBe(true);
    }
  });

  it('스냅샷 resonance (켜짐 표시) · 메뉴 줄 trait·resonance', () => {
    const w = new WeaponState('katana', WEAPONS.katana);
    w.addTrait('k_parryShove');
    const ui = uiGrowth(w, 1, { guides: [] });
    expect(ui.resonance?.map((r) => [r.tag, r.active])).toEqual([
      ['insight', false],
      ['breach', false],
      ['chain', false],
    ]);
    const menu = growthMenu(
      w,
      'trait',
      1,
      () => 0.1,
      undefined,
      (wid, id) => `icon:${wid}_${id}`,
    );
    const insight = menu!.lines.find((l) => l.trait?.tag === 'insight');
    expect(insight?.trait?.iconKey).toBe(`icon:katana_${insight?.trait?.id}`);
    expect(insight?.resonance?.name).toBe('되받는 달');
  });
});

describe('61 단계 5 개성 그림·소리 이름 규칙', () => {
  it('카드 그림 키 · fx · 발동음 후보', () => {
    expect(traitIconKey('bow', 'b_arrowTrap')).toBe('ui_traits/bow_b_arrowTrap');
    expect(traitFxId('bow', 'b_arrowTrap')).toBe('trait_bow_b_arrowTrap');
    expect(traitFxId('bow', 'b_arrowTrap', 'snap')).toBe('trait_bow_b_arrowTrap_snap');
    expect(traitProcSfx('bow', 'b_arrowTrap', 'bind')).toEqual(['sfx/trait_bow_b_arrowTrap', 'sfx/trait_bind']);
  });
});
