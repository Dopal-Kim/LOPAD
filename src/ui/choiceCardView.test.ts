import { describe, expect, it } from 'vitest';
import type { UiMenu } from '../contract/ui';
import { choiceCards, choiceHint, isChoiceCardMenu } from './choiceCardView';

const evolve: UiMenu = {
  id: 'evolve',
  title: '개성이 깊어진다',
  lines: [
    { key: '1', label: '더 깊게 — 공격 +15%', detail: '공격 +15%', enabled: true, kind: 'reinforce', tags: ['vital'] },
    { key: '2', label: '피의 계약', detail: '저주 1개 · 이득 1.5배', enabled: true, kind: 'bloodPact' },
    {
      key: '3',
      label: '만월',
      detail: '최종 각성',
      enabled: false,
      kind: 'awaken',
      locked: { condition: '2단 + 그 2단 태그 6점 + 5층 보스 이후' },
    },
  ],
};

describe('choiceCardView (60라운드 Q38 3지선다 카드 3장)', () => {
  it('개성·보상·패시브 중 그만두기를 뺀 칸이 3이면 카드, 아니면 목록', () => {
    expect(isChoiceCardMenu(evolve)).toBe(true);
    expect(isChoiceCardMenu({ ...evolve, lines: evolve.lines.slice(0, 2) })).toBe(false);
    const withCancel: UiMenu = {
      ...evolve,
      id: 'reward',
      cancelKey: '0',
      lines: [...evolve.lines, { key: '0', label: '그만둔다', enabled: true }],
    };
    expect(isChoiceCardMenu(withCancel)).toBe(true);
    expect(isChoiceCardMenu({ ...evolve, id: 'passive' })).toBe(true);
    // 3칸이어도 다른 메뉴(저주·이벤트·상점 등)는 목록
    expect(isChoiceCardMenu({ ...evolve, id: 'event' })).toBe(false);
    expect(isChoiceCardMenu({ ...evolve, id: 'curse' })).toBe(false);
  });

  it('카드 글: 종류 머리표·이름(설명 중복 제거)·태그·잠김', () => {
    const cs = choiceCards(evolve);
    expect(cs[0]).toMatchObject({
      key: '1',
      head: '강화',
      headSlot: 22,
      name: '더 깊게',
      meta: '급소',
      detail: '공격 +15%',
      enabled: true,
      note: '',
      locked: '',
    });
    expect(cs[1]).toMatchObject({ head: '피의 계약', headSlot: 19, meta: '' });
    expect(cs[2]).toMatchObject({
      head: '각성',
      headSlot: 25,
      enabled: false,
      note: '(잠김)',
      locked: '잠김 — 2단 + 그 2단 태그 6점 + 5층 보스 이후',
      detail: '최종 각성',
    });
  });

  it('kind 가 없으면 메뉴 id 로 머리표, 희귀도 칸 수, 못 고르는 칸 (불가)', () => {
    const m: UiMenu = {
      id: 'passive',
      title: '패시브',
      lines: [
        { key: '1', label: '칼날 바람', enabled: true, rarity: 'rare', tags: ['insight', 'breach'] },
        { key: '2', label: '강철 피부', enabled: true, rarity: 'legendary' },
        { key: '3', label: '독한 술', enabled: false },
      ],
    };
    const cs = choiceCards(m);
    expect(cs.map((c) => c.head)).toEqual(['패시브', '패시브', '패시브']);
    expect(cs.map((c) => c.rarityRank)).toEqual([2, 4, 0]);
    expect(cs[0].meta).toBe('희귀 · 간파·돌파');
    expect(cs[2]).toMatchObject({ enabled: false, note: '(불가)' });
  });

  it('보상 3택에 이중 개성 칸이 끼면 그 카드만 〔이중 개성〕', () => {
    const m: UiMenu = {
      id: 'reward',
      title: '보상',
      lines: [
        { key: '1', label: '칼날 바람', enabled: true, kind: 'passive' },
        { key: '2', label: '선풍 쌍격', enabled: true, kind: 'dual' },
        { key: '3', label: '강철 피부', enabled: true, kind: 'passive' },
      ],
    };
    expect(choiceCards(m).map((c) => c.head)).toEqual(['패시브', '이중 개성', '패시브']);
  });

  it('조작 안내: 카드 키 · 그만두기 키', () => {
    expect(choiceHint(evolve)).toBe('1·2·3 또는 ←→ 고르기 · Enter 고른다');
    const m: UiMenu = {
      ...evolve,
      id: 'reward',
      cancelKey: '0',
      lines: [...evolve.lines, { key: '0', label: '건너뛴다', enabled: true }],
    };
    expect(choiceHint(m)).toBe('1·2·3 또는 ←→ 고르기 · Enter 고른다 · 0·Esc 그만두기');
  });
});
