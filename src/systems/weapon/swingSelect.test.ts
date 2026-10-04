import { describe, expect, it } from 'vitest';
import { WEAPON_FX } from '../core/Constants';
import type { TierSheetFields } from './fxTier';
import { pickSwingFx, type SwingPickInput } from './swingSelect';

const base: SwingPickInput = {
  weaponId: 'katana',
  comboN: 1,
  finisher: false,
  path: [],
  heat: 0,
  reuseId: null,
  evoId: null,
};

function lookup(loaded: string[], sheets: Record<string, TierSheetFields> = {}) {
  return { has: (id: string) => loaded.includes(id), sheet: (id: string) => sheets[id] ?? null };
}

describe('swingSelect: 휘두름 이펙트 고르기 (2단 → 1단 → 기본, 55라운드 Q16)', () => {
  const all = ['katana_combo1', 'katana_combo1_iai', 'katana_combo1_iai_wide', 'katana_combo3', 'katana_slash'];

  it('갈래 없음 → 기본 연격', () => {
    expect(pickSwingFx(base, lookup(all))).toMatchObject({ id: 'katana_combo1', tier: 'base', heatScale: 1 });
  });

  it('1단 갈래 → 갈래 시트, 2단 → 2단 전용 시트', () => {
    expect(pickSwingFx({ ...base, path: ['iai'] }, lookup(all))).toMatchObject({
      id: 'katana_combo1_iai',
      tier: 'branch',
    });
    expect(pickSwingFx({ ...base, path: ['iai', 'wide'] }, lookup(all))).toMatchObject({
      id: 'katana_combo1_iai_wide',
      tier: 'secondary',
    });
  });

  it('2단 전용 시트가 없으면 1단 + colorSwap 대체', () => {
    const sheets = {
      katana_combo1_iai: { secondaryVariants: { zangetsu: { colorSwap: [{ from: '#eecc78', to: '#90857a' }] } } },
    };
    const p = pickSwingFx({ ...base, path: ['iai', 'zangetsu'] }, lookup(all, sheets));
    expect(p.id).toBe('katana_combo1_iai');
    expect(p.variant?.swaps).toHaveLength(1);
  });

  it('대검 대쉬 공격 재사용: 갈래 시트·2단 시트 우선', () => {
    const gs = ['greatsword_combo2', 'greatsword_combo2_crush', 'greatsword_combo2_crush_quake'];
    const input = { ...base, weaponId: 'greatsword', comboN: 3, reuseId: 'greatsword_combo2' };
    expect(pickSwingFx(input, lookup(gs)).id).toBe('greatsword_combo2');
    expect(pickSwingFx({ ...input, path: ['crush'] }, lookup(gs)).id).toBe('greatsword_combo2_crush');
    expect(pickSwingFx({ ...input, path: ['crush', 'quake'] }, lookup(gs)).id).toBe('greatsword_combo2_crush_quake');
  });

  it('가열: 단계 시트가 있으면 그것, 없으면 기본 시트를 키운다. 갈래 시트 heatVariants 면 키우지 않는다', () => {
    const d = { ...base, weaponId: 'dagger', heat: 2 };
    expect(pickSwingFx(d, lookup(['dagger_combo1', 'dagger_combo1_heat2']))).toMatchObject({
      id: 'dagger_combo1_heat2',
      heatScale: 1,
    });
    expect(pickSwingFx(d, lookup(['dagger_combo1'])).heatScale).toBeCloseTo(1 + WEAPON_FX.HEAT_SCALE_PER_STAGE * 2);
    const sheets = {
      dagger_combo1_twin: { heatVariants: { colorSwap: { '2': [{ from: '#8b4d22', to: '#d67a11' }] } } },
    };
    const p = pickSwingFx({ ...d, path: ['twin'] }, lookup(['dagger_combo1', 'dagger_combo1_twin'], sheets));
    expect(p).toMatchObject({ id: 'dagger_combo1_twin', heatScale: 1 });
    expect(p.variant?.swaps).toHaveLength(1);
  });

  it('마지막 타 + 진화 베기(갈래 시트 없음) → 진화 베기, 연격 시트가 없으면 slash', () => {
    expect(pickSwingFx({ ...base, comboN: 3, finisher: true, evoId: 'iai' }, lookup(['katana_combo3', 'iai'])).id).toBe(
      'iai',
    );
    expect(pickSwingFx({ ...base, comboN: null }, lookup(['katana_slash'])).id).toBe('katana_slash');
  });
});
