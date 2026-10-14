import { describe, expect, it } from 'vitest';
import { TRAITS } from '../../data/growth';
import { MEMORY } from '../../data/memory';
import { traitIconCandidates, traitIconKey } from './traitArt';
import { traitDetail, uiTrait } from './uiGrowth';

/** 62 루프 4: 기억 '떠올릴 개성' 8장 (스토리 64 팩) */
describe('62 루프 4 기억 개성', () => {
  const mem = TRAITS.filter((t) => t.memory);

  it('무기당 2장 · 기억 칸 하나에 그 무기 2장 · effect.kind 8종', () => {
    expect(mem.map((t) => t.id).sort()).toEqual(
      [
        'b_mem_bottleShot',
        'b_mem_quiverShake',
        'd_mem_pickpocket',
        'd_mem_slipDash',
        'g_mem_blockCharge',
        'g_mem_caskRoll',
        'k_mem_fireLine',
        'k_mem_sheathBlock',
      ].sort(),
    );
    for (const m of MEMORY.items.filter((x) => x.kind === 'pool')) {
      expect(m.traits).toHaveLength(2);
      for (const id of m.traits ?? []) expect(mem.find((t) => t.id === id)?.weapon).toBe(m.weapon);
    }
    expect(new Set(mem.map((t) => t.effect.kind)).size).toBe(8);
  });

  it('상세 줄: ms → 초 · 비율% → ×100 · 배율·칸은 그대로 (자리표시가 남지 않는다)', () => {
    const fire = mem.find((t) => t.id === 'k_mem_fireLine')!;
    expect(traitDetail(fire)).toBe('일섬 길 전체 불줄 2.5초 · 0.5초마다 공격 ×0.3');
    const slide = mem.find((t) => t.id === 'd_mem_slipDash')!;
    expect(traitDetail(slide)).toBe('대쉬 거리 +60% · 술 자국 4초 · 넘어짐 0.7초');
    for (const t of mem) {
      expect(traitDetail(t)).not.toMatch(/\{/);
      const ui = uiTrait(t);
      expect(ui.detail).toBe(traitDetail(t));
      expect(ui.flavor).toBe(t.flavor);
    }
    // 기본 개성은 상세 줄이 없다 (계약 §18 — 있는 카드만)
    expect(uiTrait(TRAITS.find((t) => !t.memory)!).detail).toBeUndefined();
  });

  it('카드 그림 후보: 자기 그림 → 같은 태그(기본 → 갈래) → 같은 동사 칸 (그림이 들어오기 전 대체)', () => {
    for (const t of mem) {
      const c = traitIconCandidates(t.weapon, t.id);
      expect(c[0]).toBe(traitIconKey(t.weapon, t.id));
      expect(c.length, t.id).toBeGreaterThan(1);
    }
    // 칼은 기본 풀에 취기 개성이 없다 → 취기 갈래 개성 그림이 먼저
    const c = traitIconCandidates('katana', 'k_mem_fireLine');
    const branchDrunk = TRAITS.filter((t) => t.weapon === 'katana' && t.tag === 'drunk' && t.branch && !t.memory);
    expect(branchDrunk.length).toBeGreaterThan(0);
    expect(c[1]).toBe(traitIconKey('katana', branchDrunk[0].id));
  });
});
