import { describe, expect, it } from 'vitest';
import { DEPTH, entityDepth, fxLitDepth } from '../core/Constants';
import { WEAPONS } from '../data';
import { branchComboFxId, composeSwaps, meleeBranchFxSheetIds, resolveFxVariant, swapTag } from './fxVariants';
import { paletteSwapExempt } from './spriteDefs';

/** 아트 v3 JSON 형태를 줄인 예 (계약 §10: secondaryVariants · heatVariants) */
const iai = {
  secondaryVariants: {
    wide: {
      colorSwap: [
        { from: '#D67A11', to: '#e2a33c' },
        { from: '#8b4d22', to: '#d67a11' },
      ],
      flashOverride: { atFrame: 1, color: '#fff4dc', alpha: 0.14, ms: 40 },
    },
    zangetsu: { colorSwap: [{ from: '#eecc78', to: '#90857a' }], holdLastFrameMs: 160 },
  },
};
const gale = {
  secondaryVariants: {
    afterimage: {
      colorSwap: [{ from: '#ffffff', to: '#eecc78' }],
      trailOverride: { color: '#8b4d22', alpha: 0.6, ms: 160, fromFrame: 1 },
    },
  },
  heatVariants: {
    colorSwap: { '1': [{ from: '#8b4d22', to: '#d67a11' }], '2': [{ from: '#eecc78', to: '#f4de9b' }] },
    playbackRateHint: { '1': 1.15, '2': 1.3 },
  },
};
const snipe = {
  secondaryVariants: {
    pierce: { overlay: { sheet: 'fx/pierce', loop: true } },
    deadeye: {
      colorSwap: [{ from: '#e2a33c', to: '#eecc78' }],
      overlay: { sheet: 'fx/crit_burst', onHit: true, minLevel: 3 },
    },
  },
};

describe('53라운드 무기 이펙트 v3 변주 (계약 §10)', () => {
  it('근접 1단 갈래 시트 id · 로드 목록 (근접 무기 × 1단 갈래 × 3타, 활 제외)', () => {
    expect(branchComboFxId('katana', 2, 'iai')).toBe('katana_combo2_iai');
    const ids = meleeBranchFxSheetIds(WEAPONS);
    for (const id of ['katana_combo1_iai', 'katana_combo3_batto', 'greatsword_combo2_crush', 'dagger_combo3_gale'])
      expect(ids).toContain(id);
    expect(ids.some((id) => id.startsWith('bow_'))).toBe(false);
  });

  it('2단 갈래: 색 교체(소문자 정규화) · 섬광·잔상 덮어쓰기 · 마지막 프레임 유지', () => {
    const wide = resolveFxVariant(iai, { secondary: 'wide' })!;
    expect(wide.swaps).toEqual([
      { from: '#d67a11', to: '#e2a33c' },
      { from: '#8b4d22', to: '#d67a11' },
    ]);
    expect(wide.flash).toEqual({ atFrame: 1, color: '#fff4dc', alpha: 0.14, ms: 40 });
    expect(resolveFxVariant(iai, { secondary: 'zangetsu' })!.holdLastMs).toBe(160);
    expect(resolveFxVariant(gale, { secondary: 'afterimage' })!.trail?.ms).toBe(160);
  });

  it('없는 노드·필드면 null (원본 그대로), 형식이 틀린 색은 버린다', () => {
    expect(resolveFxVariant(iai, { secondary: 'nope' })).toBeNull();
    expect(resolveFxVariant({}, { secondary: 'wide', heat: 2 })).toBeNull();
    expect(resolveFxVariant(null, { secondary: 'wide' })).toBeNull();
    const bad = { secondaryVariants: { x: { colorSwap: [{ from: 'red', to: '#000000' }] } } };
    expect(resolveFxVariant(bad, { secondary: 'x' })!.swaps).toEqual([]);
  });

  it('가열: 단계별 색 교체 + 배속 힌트, 2단 갈래와 합성(2단 → 가열 순)', () => {
    const h1 = resolveFxVariant(gale, { heat: 1 })!;
    expect(h1.swaps).toEqual([{ from: '#8b4d22', to: '#d67a11' }]);
    expect(h1.playbackRate).toBe(1.15);
    const both = resolveFxVariant(gale, { secondary: 'afterimage', heat: 2 })!;
    // #ffffff → #eecc78 (2단) → #f4de9b (가열 2)
    expect(both.swaps).toEqual([
      { from: '#ffffff', to: '#f4de9b' },
      { from: '#eecc78', to: '#f4de9b' },
    ]);
  });

  it('겹침: 따라가는 루프(관통)만 followOverlays, 적중형(필중 crit_burst)은 기존 치명 연출이 맡는다', () => {
    expect(resolveFxVariant(snipe, { secondary: 'pierce' })!.followOverlays).toEqual(['pierce']);
    expect(resolveFxVariant(snipe, { secondary: 'deadeye' })!.followOverlays).toEqual([]);
  });

  it('교체 합성·태그는 결정적 (순서 무관 태그, 제자리 교체는 뺀다)', () => {
    expect(composeSwaps([{ from: '#000001', to: '#000002' }], [{ from: '#000002', to: '#000001' }])).toEqual([
      { from: '#000002', to: '#000001' },
    ]);
    const a = [
      { from: '#111111', to: '#222222' },
      { from: '#333333', to: '#444444' },
    ];
    expect(swapTag(a)).toBe(swapTag([...a].reverse()));
  });
});

describe('53라운드 Q62·Q64 바닥 팔레트 교체 제외 · 이펙트는 라이트맵 위', () => {
  it('이펙트 분류 전체와 paletteSwap "none" 시트는 층 램프 교체에서 뺀다', () => {
    expect(paletteSwapExempt({ category: 'fx' })).toBe(true);
    expect(paletteSwapExempt({ category: 'enemies', paletteSwap: 'none' })).toBe(true);
    expect(paletteSwapExempt({ category: 'enemies' })).toBe(false);
    expect(paletteSwapExempt({ category: 'player', paletteSwap: 'floor' })).toBe(false);
  });

  it('라이트맵 아래 깊이는 라이트맵·빛 번짐 위로 옮기고 이펙트끼리 앞뒤는 유지, 이미 위면 그대로', () => {
    const ground = fxLitDepth(DEPTH.FX_GROUND);
    const onBody = fxLitDepth(entityDepth(300) + DEPTH.OVERLAY_STEP * 2);
    expect(ground).toBeGreaterThan(DEPTH.LIGHTMAP + DEPTH.LIGHT_LAYER_STEP);
    expect(onBody).toBeGreaterThan(ground);
    expect(onBody).toBeLessThan(DEPTH.PICKUP);
    expect(fxLitDepth(DEPTH.PROJECTILE)).toBe(DEPTH.PROJECTILE);
    expect(fxLitDepth(DEPTH.HIT_FX)).toBe(DEPTH.HIT_FX);
  });
});
