import { describe, expect, it } from 'vitest';
import type { UiBuildState, UiTagState } from '../contract/ui';
import {
  buildOf,
  consumableView,
  curseLeft,
  diaryLines,
  gradeStamp,
  gradedView,
  hudTags,
  perfectText,
  scorePips,
  setChangeToast,
  tagChipValue,
  tagName,
  trialView,
} from './buildView';

const tag = (id: UiTagState['id'], score: number, stage: UiTagState['stage'], name = ''): UiTagState => ({
  id,
  name,
  score,
  stage,
  next: stage >= 6 ? null : stage + 2,
  effects: [
    { threshold: 2, name: '하나', description: '', active: stage >= 2 },
    { threshold: 4, name: '둘', description: '', active: stage >= 4 },
    { threshold: 6, name: '셋', description: '', active: stage >= 6 },
  ],
});

const build = (tags: UiTagState[], curse: UiBuildState['curse'] = null): UiBuildState => ({
  tags,
  dualTraits: [],
  curse,
});

describe('buildView (57·60라운드 §14 빌드 축)', () => {
  it('build 가 없거나 비면 빈 값', () => {
    expect(buildOf({})).toEqual({ tags: [], dualTraits: [], curse: null });
    expect(buildOf({ build: null })).toEqual({ tags: [], dualTraits: [], curse: null });
  });

  it('태그 이름: 스냅샷 이름 → 계약 자리표시 이름 → id', () => {
    expect(tagName('insight', build([tag('insight', 2, 2, '간파!')]))).toBe('간파!');
    expect(tagName('insight')).toBe('간파');
    expect(tagName('drunk')).toBe('취기');
    expect(tagName('unknownTag')).toBe('unknownTag');
  });

  it('세트 임계 2·4·6 칸', () => {
    expect(scorePips(3)).toEqual([1, 0.5, 0]);
  });

  it('HUD 태그 칩: score > 0, 시스템 정렬 그대로, 최대 개수', () => {
    const b = build([tag('chain', 5, 4), tag('vital', 2, 2), tag('mark', 0, 0), tag('scar', 1, 0)]);
    expect(hudTags(b, 2).map((t) => t.id)).toEqual(['chain', 'vital']);
    expect(hudTags(b, 9).map((t) => t.id)).toEqual(['chain', 'vital', 'scar']);
    expect(tagChipValue({ score: 5, stage: 4 })).toBe('5 · 4단');
    expect(tagChipValue({ score: 1, stage: 0 })).toBe('1');
  });

  it('저주 남은 기간: 처치 수 기준이 먼저', () => {
    expect(curseLeft(null)).toBe('');
    expect(curseLeft({ nodesLeft: 3, killsLeft: null })).toBe('3노드 남음');
    expect(curseLeft({ nodesLeft: null, killsLeft: 12 })).toBe('12처치 남음');
    expect(curseLeft({ nodesLeft: null, killsLeft: null })).toBe('');
  });

  it('세트 단계 바뀜 토스트: 오름·내림·꺼짐, 이전을 모르거나 같으면 오름', () => {
    expect(setChangeToast({ tag: 'insight', name: '간파', stage: 2, effectName: '눈썰미' }, 0)).toEqual({
      tone: 'gain',
      text: '간파 세트 2단 — 눈썰미',
    });
    expect(setChangeToast({ tag: 'insight', name: '간파', stage: 4, effectName: '' }, undefined)?.tone).toBe('gain');
    expect(setChangeToast({ tag: 'insight', name: '간파', stage: 2, effectName: 'x' }, 2)?.tone).toBe('gain');
    expect(setChangeToast({ tag: 'insight', name: '간파', stage: 2, effectName: 'x' }, 4)).toEqual({
      tone: 'loss',
      text: '간파 세트가 2단으로 내려갔다',
    });
    expect(setChangeToast({ tag: 'chain', name: '', stage: 0, effectName: '' }, 2)).toEqual({
      tone: 'loss',
      text: '연쇄 세트가 꺼졌다',
    });
    expect(setChangeToast(null, 0)).toBeNull();
  });

  it('완벽 성공 문구', () => {
    expect(perfectText({ kind: 'perfectEvade' })).toBe('PERFECT EVADE');
    expect(perfectText({ kind: 'parry' })).toBe('PARRY');
    expect(perfectText(null)).toBe('');
  });

  it('성과 도장·진행', () => {
    expect(gradeStamp('perfect')).toBe('完');
    expect(gradeStamp('good')).toBe('良');
    expect(gradeStamp(null)).toBe('');
    const v = trialView({ timeLimitMs: 50000, elapsedMs: 18100, hitTaken: false })!;
    expect(v.text).toBe('32초');
    expect(v.ratio).toBeCloseTo(0.638);
    expect(v.hitText).toBe('무피격');
    expect(trialView({ timeLimitMs: 50000, elapsedMs: 60000, hitTaken: true })).toMatchObject({
      text: '시간 지남',
      over: true,
      hit: true,
      ratio: 0,
    });
    expect(trialView(null)).toBeNull();
    const g = gradedView(
      { nodeId: 'n', grade: 'perfect', noHit: true, inTime: false, deltas: { gold: 20, personality: 15 }, text: '' },
      '전표',
    )!;
    expect(g.stamp).toBe('完');
    expect(g.text).toBe('');
    expect(g.conds).toBe('무피격 ○  ·  제한 시간 ×');
    expect(g.deltas).toBe('+20 전표  +15 각성');
  });

  it('소모품 칸', () => {
    expect(consumableView(null)).toBeNull();
    expect(consumableView({ key: 'C', item: null })).toMatchObject({ empty: true, key: 'C', name: '빈 칸' });
    expect(
      consumableView({
        key: '',
        item: { id: 'fire_bottle', name: '화염 술병', description: '', kind: 'throw', count: 2, max: 2 },
      }),
    ).toMatchObject({ empty: false, key: 'C', count: '2/2', kind: 'throw' });
  });

  it('일기장 빌드 쪽: 넘치면 효과·설명 줄을 접는다', () => {
    const s = {
      passives: [{ name: '칼날 바람', level: 2, description: '', tags: ['insight' as const], maxLevel: 3 }],
      consumable: { key: 'C', item: null },
      build: build([tag('insight', 3, 2, '간파')], {
        id: 'c',
        name: '만취 서약',
        benefit: '공격 +20%',
        penalty: '받는 피해 +15%',
        nodesLeft: 2,
        killsLeft: null,
      }),
    };
    const full = diaryLines(s, 0).map((l) => l.text);
    expect(full).toContain('간파  3 · 2단  (다음 4)');
    expect(full).toContain('  2 하나');
    expect(full).toContain('만취 서약  2노드 남음');
    expect(full).toContain('  − 받는 피해 +15%');
    expect(full).toContain('칼날 바람  Lv2/3  간파');
    expect(full).toContain('빈 칸  (C)');
    const mid = diaryLines(s, 1).map((l) => l.text);
    expect(mid).toContain('  2 하나');
    expect(mid).not.toContain('  4 둘 · 6 셋');
    expect(mid).toContain('  − 받는 피해 +15%');
    const compact = diaryLines(s, 2).map((l) => l.text);
    expect(compact).not.toContain('  2 하나');
    expect(compact).not.toContain('  − 받는 피해 +15%');
    expect(compact.length).toBeLessThan(mid.length);
    expect(diaryLines({ passives: [], consumable: null }, 0).map((l) => l.text)).toEqual([
      '태그·세트',
      '―',
      '패시브',
      '―',
    ]);
  });
});
