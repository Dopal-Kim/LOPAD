import { describe, expect, it } from 'vitest';
import { ECONOMY, PLAYER_DATA, WEAPONS, WEAPON_RULES } from '../../data';
import { RESONANCES, TRAITS } from '../../data/growth';
import { baselineDps } from '../weapon/dps';
import { TRAIT_BUDGET, TRAIT_DAMAGE_MODELS, traitAddRatio } from './traitBudget';

/** 61 단계 5 (P13 §1 밸런스 가드): 개성·공명 하나가 P2 기준선 DPS 를 +25% 넘게 올리지 않는다 */
const base = WEAPON_RULES.dpsBaseline!;
const opts = { attack: base.attack, crit: PLAYER_DATA.stats.crit, critMult: ECONOMY.critDamageMult };

function ratioOf(weapon: string, effect: Parameters<typeof traitAddRatio>[0]): number {
  const e = baselineDps(WEAPONS[weapon], opts);
  return traitAddRatio(effect, e.dps, base.attack, Math.max(0.5, e.cycleMs / 1000));
}

describe('61 단계 5 개성 밸런스 가드 (P2 기준선 +25% 이하)', () => {
  for (const t of TRAITS)
    it(`${t.weapon} ${t.id} (${t.effect.kind})`, () => {
      expect(ratioOf(t.weapon, t.effect)).toBeLessThanOrEqual(TRAIT_BUDGET.maxAdd);
    });
  for (const r of RESONANCES)
    it(`공명 ${r.id} (${r.effect.kind})`, () => {
      expect(ratioOf(r.weapon, r.effect)).toBeLessThanOrEqual(TRAIT_BUDGET.maxAdd);
    });

  it('피해를 내는 새 개성 kind 는 모두 추정 모델이 있다 (모델이 없으면 0 으로 빠진다)', () => {
    // 피해가 없는 행동 kind (끌어당김·묶음·밀기·자원·상태·환경 점화) — 여기 없는데 모델도 없으면 실패
    const noDamage = new Set([
      'guardBind',
      'iaiKillDash',
      'swingDeflect',
      'guardPull',
      'crackPull',
      'splitRoad',
      'jarCrush',
      'rageFire',
      'brandKnot',
      'dashBrand',
      'flurryPull',
      'twinBrand',
      'cloneShield',
      'liquorThrow',
      'ghostBind',
      'ghostIgnite',
      'rainSnare',
      'rapidStride',
      'fireArrow',
      'skyGravity',
      'skyIgnite',
      'resDeflectAll',
      'resBindSpread',
      'resShadowPath',
    ]);
    const kinds = [...TRAITS.map((t) => t.effect.kind), ...RESONANCES.map((r) => r.effect.kind)];
    const missing = kinds.filter((k) => !TRAIT_DAMAGE_MODELS[k] && !noDamage.has(k));
    expect(missing).toEqual([]);
  });
});

describe('61 단계 5 개성 추가 피해 표 (npx vitest run src/systems/sim/traitBudget --silent=false)', () => {
  it('무기별 개성·공명 추가 비율 (%)', () => {
    const rows = [...TRAITS, ...RESONANCES].map((t) => ({
      weapon: t.weapon,
      id: t.id,
      kind: t.effect.kind,
      addPct: Math.round(ratioOf(t.weapon, t.effect) * 1000) / 10,
    }));
    console.table(rows.filter((r) => r.addPct > 0));
    expect(rows.length).toBe(TRAITS.length + RESONANCES.length);
  });
});
