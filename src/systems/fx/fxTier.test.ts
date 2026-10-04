import { describe, expect, it } from 'vitest';
import { WEAPONS } from '../../data';
import { pickTierSheet, secondarySheetId, tier2FxSheetIds, type TierSheetFields } from './fxTier';
import { mergeVariants, runtimeFxVariant } from './fxVariants';

/** 아트 v3 1단·2단 JSON 을 줄인 예 (계약 §10 55라운드 Q16) */
const sheets: Record<string, TierSheetFields> = {
  katana_combo1_iai: {
    secondarySheets: { wide: 'fx/katana_combo1_iai_wide' },
    secondaryVariants: {
      wide: { colorSwap: [{ from: '#d67a11', to: '#e2a33c' }], sheet: 'fx/katana_combo1_iai_wide' },
      zangetsu: { colorSwap: [{ from: '#eecc78', to: '#90857a' }], holdLastFrameMs: 160 },
    },
  },
  katana_combo1_iai_wide: { runtime: { flashOverride: { atFrame: 1, alpha: 0.14 } } },
  bow_arrow_snipe: {
    secondaryVariants: { pierce: { overlay: { sheet: 'fx/pierce', loop: true }, sheet: 'fx/bow_arrow_snipe_pierce' } },
  },
  bow_arrow_snipe_pierce: { runtime: {} },
  dagger_combo1_twin_dance: {
    runtime: {},
    heatVariants: { colorSwap: { '1': [{ from: '#8b4d22', to: '#d67a11' }] }, playbackRateHint: { '1': 1.15 } },
  },
};

function lookup(loaded: string[]) {
  return {
    has: (id: string) => loaded.includes(id),
    sheet: (id: string) => sheets[id] ?? null,
  };
}

describe('fxTier: 2단 전용 시트 → 1단 → 기본 (55라운드 Q16)', () => {
  it('2단 시트 id 는 secondarySheets → secondaryVariants.sheet → 이름 규칙', () => {
    expect(secondarySheetId('katana_combo1_iai', sheets.katana_combo1_iai, 'wide')).toBe('katana_combo1_iai_wide');
    expect(secondarySheetId('bow_arrow_snipe', sheets.bow_arrow_snipe, 'pierce')).toBe('bow_arrow_snipe_pierce');
    expect(secondarySheetId('katana_combo1_iai', sheets.katana_combo1_iai, 'zangetsu')).toBe(
      'katana_combo1_iai_zangetsu',
    );
  });

  it('2단 시트가 로드돼 있으면 그 시트 + runtime (colorSwap 은 쓰지 않음)', () => {
    const p = pickTierSheet('katana_combo1_iai', true, { secondary: 'wide' }, lookup(['katana_combo1_iai_wide']));
    expect(p.id).toBe('katana_combo1_iai_wide');
    expect(p.tier).toBe('secondary');
    expect(p.variant?.swaps).toEqual([]);
    expect(p.variant?.flash?.alpha).toBe(0.14);
  });

  it('2단 시트가 없으면 1단 시트 + colorSwap 대체', () => {
    const p = pickTierSheet('katana_combo1_iai', true, { secondary: 'zangetsu' }, lookup([]));
    expect(p.id).toBe('katana_combo1_iai');
    expect(p.tier).toBe('branch');
    expect(p.variant?.swaps).toEqual([{ from: '#eecc78', to: '#90857a' }]);
    expect(p.variant?.holdLastMs).toBe(160);
  });

  it('관통 2단: 2단 꼬리 시트가 있으면 구 fx/pierce 겹침 없음 (Q17), 없으면 대체 경로로 겹침', () => {
    const withSheet = pickTierSheet(
      'bow_arrow_snipe',
      true,
      { secondary: 'pierce' },
      lookup(['bow_arrow_snipe_pierce']),
    );
    expect(withSheet.id).toBe('bow_arrow_snipe_pierce');
    expect(withSheet.variant).toBeNull();
    const fallback = pickTierSheet('bow_arrow_snipe', true, { secondary: 'pierce' }, lookup([]));
    expect(fallback.variant?.followOverlays).toEqual(['pierce']);
  });

  it('기본 시트(갈래 시트 없음)는 2단 시트를 찾지 않는다', () => {
    const p = pickTierSheet('katana_combo1', false, { secondary: 'wide' }, lookup(['katana_combo1_wide']));
    expect(p).toEqual({ id: 'katana_combo1', tier: 'base', variant: null });
  });

  it('2단 단검 시트의 가열 변주는 그 시트 heatVariants', () => {
    const v = runtimeFxVariant(sheets.dagger_combo1_twin_dance, 1);
    expect(v?.swaps).toEqual([{ from: '#8b4d22', to: '#d67a11' }]);
    expect(v?.playbackRate).toBe(1.15);
    expect(runtimeFxVariant(sheets.dagger_combo1_twin_dance, 0)).toBeNull();
  });

  it('변주 합치기: 빈 것은 버리고, 색 교체는 순서대로 합성', () => {
    const a = { swaps: [{ from: '#000001', to: '#000002' }], followOverlays: [], playbackRate: null };
    const b = { swaps: [{ from: '#000002', to: '#000003' }], followOverlays: ['x'], playbackRate: 1.2 };
    expect(mergeVariants(null, null)).toBeNull();
    expect(mergeVariants(a, null)).toBe(a);
    const m = mergeVariants(a, b)!;
    expect(m.swaps).toEqual([
      { from: '#000001', to: '#000003' },
      { from: '#000002', to: '#000003' },
    ]);
    expect(m.followOverlays).toEqual(['x']);
    expect(m.playbackRate).toBe(1.2);
  });

  it('로드 목록: 근접 2단 연격 · 활 2단 화살·꼬리', () => {
    const ids = tier2FxSheetIds(WEAPONS);
    // 57라운드 갈래 재설계: 2단 id 가 바뀐 노드는 새 id 로 (그림이 없으면 1단 → 기본으로 내려간다)
    expect(ids).toContain('katana_combo1_iai_vortex');
    expect(ids).toContain('greatsword_combo3_weight_giant');
    expect(ids).toContain('dagger_combo2_gale_flyknife');
    expect(ids).toContain('bow_arrow_snipe_skypierce');
    expect(ids).toContain('bow_arrow_aimed_rapid_volley');
    expect(ids).toContain('bow_arrow_snipe_lv3_deadeye');
  });
});
