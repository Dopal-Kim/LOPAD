import { describe, expect, it } from 'vitest';
import {
  BUILD,
  CURSES,
  DUAL_TRAITS,
  curseOn,
  curseSourceOn,
  dualAbsorbOn,
  maxTierOn,
  setThresholdsOn,
  tagOn,
  tagsOn,
} from '../../data/build';
import { floorOfStage, onFloor } from '../../data/floorScope';
import { PASSIVES, PassiveSet } from '../passives';
import { Rng } from '../rng';
import { computeBuildMods } from './buildMods';
import { uiTags } from './BuildState';
import { absorbedDualTraits } from './evolveSlots';
import { emptyScores } from './tagScore';

const F1_TAGS = ['insight', 'breach', 'vital', 'chain', 'weight', 'drunk'];

describe('61라운드 P4 빌드 축 1층판 (floor 필드)', () => {
  it('층 범위 도우미: floor 없으면 1 · null 은 제한 없음 · 층 id → 번호', () => {
    expect(onFloor({}, 1)).toBe(true);
    expect(onFloor({ floor: 2 }, 1)).toBe(false);
    expect(onFloor({ floor: 2 }, null)).toBe(true);
    expect(floorOfStage('stage1')).toBe(1);
    expect(floorOfStage('stage3')).toBe(3);
  });

  it('1층 태그 6 (간파·돌파·급소·연쇄·중량·취기) · 세트는 2·4 단계만 · 2층부터 10태그 6단계', () => {
    expect(tagsOn(1)).toEqual(F1_TAGS);
    expect(tagsOn(2)).toHaveLength(10);
    for (const t of tagsOn(1)) expect(setThresholdsOn(t, 1)).toEqual([2, 4]);
    expect(setThresholdsOn('drunk', 2)).toEqual([2, 4, 6]);
  });

  it('1층 패시브 풀 15 — 태그 1개 이상이 1층 태그, 1층 태그마다 2개 이상 (취기 3)', () => {
    const f1 = PASSIVES.items.filter((p) => onFloor(p, 1));
    expect(f1).toHaveLength(15);
    for (const p of f1)
      expect(
        p.tags.some((t) => tagOn(t, 1)),
        p.id,
      ).toBe(true);
    for (const t of F1_TAGS) expect(f1.filter((p) => p.tags.includes(t as never)).length, t).toBeGreaterThanOrEqual(2);
    expect(f1.filter((p) => p.tags.includes('drunk')).map((p) => p.id)).toEqual([
      'spilledDrink',
      'hipFlask',
      'drunkFist',
    ]);
    // 보상 경로가 요구하는 희귀도가 1층 풀에 있다 (위험 노드 영웅 이상 · 엘리트 희귀 이상 · 시음회 일반)
    for (const r of ['common', 'rare', 'epic', 'legendary'])
      expect(
        f1.some((p) => p.rarity === r),
        r,
      ).toBe(true);
  });

  it('패시브 3지선다는 그 층 풀에서만', () => {
    const set = new PassiveSet();
    const rng = new Rng(11);
    for (let i = 0; i < 60; i++)
      for (const p of set.rollChoices(rng, { common: 50, rare: 30, epic: 15, legendary: 5 }, 3, { floor: 1 }))
        expect(onFloor(p, 1), p.id).toBe(true);
  });

  it('합산: 1층에서 꺼진 태그는 점수 0 · 6단계는 켜지지 않는다 · UI 효과 2칸', () => {
    const passives = new PassiveSet();
    passives.add('lifesteal'); // 연쇄 + 버팀(1층 꺼짐)
    for (let i = 0; i < 3; i++) passives.add('spilledDrink'); // 취기 1 + Lv3 1
    for (let i = 0; i < 3; i++) passives.add('hipFlask'); // 취기 +2
    for (let i = 0; i < 3; i++) passives.add('drunkFist'); // 취기 +2 · 돌파 +2
    const base = {
      data: BUILD,
      passives,
      nodes: [],
      reinforce: 0,
      dual: [],
      awakening: null,
      curse: null,
      permanentTags: {},
    };
    const all = computeBuildMods(base);
    const f1 = computeBuildMods({ ...base, floor: 1 });
    expect(all.scores.endure).toBe(1);
    expect(f1.scores.endure).toBe(0);
    expect(f1.scores.drunk).toBe(6);
    expect(all.stages.drunk).toBe(6);
    expect(f1.stages.drunk).toBe(4);
    expect(f1.rules.some((r) => r.id === 'drunk6')).toBe(false);
    const ui = uiTags(f1, 1);
    expect(ui.map((t) => t.id)).not.toContain('endure');
    const drunk = ui.find((t) => t.id === 'drunk')!;
    expect(drunk.effects.map((e) => e.threshold)).toEqual([2, 4]);
    expect(drunk.next).toBeNull();
  });

  it('저주: 1층 3종 · 얻는 길은 위험 노드와 이벤트만 (구조물·피의 계약은 2층부터)', () => {
    expect(CURSES.items.filter((c) => curseOn(c, 1)).map((c) => c.id)).toEqual(['drunkOath', 'credit', 'brokenCup']);
    expect(curseSourceOn('riskNode', 1)).toBe(true);
    expect(curseSourceOn('event', 1)).toBe(true);
    expect(curseSourceOn('structure', 1)).toBe(false);
    expect(curseSourceOn('pact', 1)).toBe(false);
    expect(curseSourceOn('pact', 2)).toBe(true);
    expect(curseSourceOn('structure', null)).toBe(true);
  });

  it('갈래: 1층 런은 1단까지 · 이중 개성은 갈래에 흡수 (일반 짝 즉시, 취기 짝은 취기 2점)', () => {
    expect(maxTierOn(1)).toBe(1);
    expect(maxTierOn(2)).toBe(Infinity);
    expect(maxTierOn(null)).toBe(Infinity);
    expect(dualAbsorbOn(1)).toBe(true);
    expect(dualAbsorbOn(2)).toBe(false);
    expect(dualAbsorbOn(null)).toBe(false);
    const scores = emptyScores();
    const ids = (s: typeof scores) =>
      absorbedDualTraits(DUAL_TRAITS, 'katana', ['iai'], s, new Set(), BUILD.dual.tier1Score).map((d) => d.id);
    expect(ids(scores)).toEqual(['bloodGale']);
    expect(ids({ ...scores, drunk: 2 })).toEqual(['bloodGale', 'liquorWhirl']);
    expect(absorbedDualTraits(DUAL_TRAITS, 'katana', [], scores, new Set(), 2)).toEqual([]);
    // 8갈래 모두 흡수할 일반 짝이 하나씩 있다
    for (const d of DUAL_TRAITS.filter((x) => x.tag !== 'drunk')) expect(typeof d.branch).toBe('string');
  });
});
