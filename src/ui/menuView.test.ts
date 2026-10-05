import { describe, expect, it } from 'vitest';
import type { UiMenu } from '../contract/ui';
import { choiceMeta, cleanLabel, hasPrice, menuHotkeys, menuLines, wideMenu } from './menuView';

describe('menuView (메뉴 줄 · 60라운드 §14.4·§14.6)', () => {
  it('evolve: 라벨 끝 설명 중복을 떼고, 칸 종류가 섞이면 〔종류〕, 잠긴 칸은 조건 줄 + (잠김)', () => {
    const m: UiMenu = {
      id: 'evolve',
      title: '개성',
      lines: [
        {
          key: '1',
          label: '더 깊게 — 공격 +15%',
          detail: '공격 +15%',
          enabled: true,
          kind: 'reinforce',
          tags: ['vital'],
        },
        { key: '2', label: '피의 계약', detail: '저주 1개 · 이득 1.5배', enabled: true, kind: 'bloodPact' },
        {
          key: '3',
          label: '만월',
          enabled: false,
          kind: 'awaken',
          locked: { condition: '2단 + 그 2단 태그 6점 + 5층 보스 이후' },
        },
      ],
    };
    const ls = menuLines(m);
    expect(ls[0]).toMatchObject({ label: '〔강화〕 더 깊게', detail: '급소\n공격 +15%', enabled: true });
    expect(ls[1].label).toBe('〔피의 계약〕 피의 계약');
    expect(ls[2]).toMatchObject({
      label: '〔각성〕 만월',
      enabled: false,
      note: '(잠김)',
      detail: '잠김 — 2단 + 그 2단 태그 6점 + 5층 보스 이후',
    });
    expect(wideMenu(m)).toBe(true);
  });

  it('칸 종류가 하나뿐이면 〔종류〕를 붙이지 않는다 (패시브·저주 2택)', () => {
    const m: UiMenu = {
      id: 'passive',
      title: '패시브',
      lines: [
        { key: '1', label: '칼날 바람', enabled: true, kind: 'passive', rarity: 'rare', tags: ['insight', 'breach'] },
        { key: '2', label: '강철 피부', enabled: true, kind: 'passive', rarity: 'common' },
      ],
    };
    const ls = menuLines(m);
    expect(ls[0].label).toBe('칼날 바람');
    expect(ls[0].detail).toBe('희귀 · 간파·돌파');
    expect(ls[1].detail).toBe('일반');
    expect(choiceMeta({ key: '1', label: '', enabled: true })).toBe('');
  });

  it('보상 3지선다에 이중 개성 칸이 끼면 〔종류〕', () => {
    const m: UiMenu = {
      id: 'reward',
      title: '보상',
      lines: [
        { key: '1', label: '칼날 바람', enabled: true, kind: 'passive' },
        { key: '2', label: '선풍 쌍격', enabled: true, kind: 'dual' },
      ],
    };
    expect(menuLines(m).map((l) => l.label)).toEqual(['〔패시브〕 칼날 바람', '〔이중 개성〕 선풍 쌍격']);
  });

  it('상점: 묶음 머리글은 묶음이 바뀌는 줄에만, 가격 덧붙임, 팔림', () => {
    const price = (n: number, ok = true) => ({ kind: 'gold' as const, amount: n, label: `${n}전표`, affordable: ok });
    const m: UiMenu = {
      id: 'shop',
      title: '상점',
      cancelKey: '0',
      lines: [
        { key: '1', label: '체력 회복', enabled: true, group: 'fixed', price: price(30) },
        { key: '2', label: '독주 · 25전표', enabled: true, group: 'fixed', price: price(25) },
        { key: '3', label: '칼날 바람', enabled: false, group: 'display', price: price(70), soldOut: true },
        { key: '4', label: '화염 술병', enabled: true, group: 'display', price: price(30) },
        { key: '5', label: '진열 바꾸기', enabled: true, group: 'reroll', price: price(15) },
        { key: '0', label: '그만둔다', enabled: true },
      ],
    };
    const ls = menuLines(m);
    expect(ls.map((l) => l.header)).toEqual([
      '늘 파는 것',
      undefined,
      '오늘의 진열',
      undefined,
      '진열 바꾸기',
      undefined,
    ]);
    expect(ls[0].label).toBe('체력 회복 · 30전표');
    expect(ls[1].label).toBe('독주 · 25전표');
    expect(ls[2]).toMatchObject({ enabled: false, note: '(팔림)' });
    expect(ls[5]).toMatchObject({ label: '그만둔다', enabled: true });
  });

  it('시험장 갈래 들여쓰기 (49라운드, 그만두기 줄 제외)', () => {
    const m: UiMenu = {
      id: 'labBranch',
      title: '갈래',
      cancelKey: '9',
      lines: [
        { key: '1', label: '선풍', enabled: true },
        { key: '2', label: '  └ 회오리', enabled: true },
        { key: '9', label: '뒤로', enabled: true },
      ],
    };
    const ls = menuLines(m);
    expect(ls[0]).toMatchObject({ label: '선풍', indent: 0 });
    expect(ls[1].label).toBe('└ 회오리');
    expect(ls[1].indent).toBeGreaterThan(0);
    expect(ls[2]).toMatchObject({ label: '뒤로', indent: 0 });
  });
});

describe('61라운드 플레이 점검 #4 — 내부 표지·단축키·이중 가격', () => {
  it('라벨 앞 영문 대괄호 표지를 뗀다 (한글 〔〕·가운데 대괄호는 그대로)', () => {
    expect(cleanLabel('[common] 깨진 잔 조각 40 전표')).toBe('깨진 잔 조각 40 전표');
    expect(cleanLabel('[d1] [epic] 끌어내린 무게')).toBe('끌어내린 무게');
    expect(cleanLabel('[m:nextTier] 다음 단 공개')).toBe('다음 단 공개');
    expect(cleanLabel('〔갈래 A〕 선풍')).toBe('〔갈래 A〕 선풍');
    expect(cleanLabel('술잔 [1] 개')).toBe('술잔 [1] 개');
  });

  it('긴 시스템 키는 쓰지 않은 숫자를 단축키로 (이동 키 제외)', () => {
    expect(menuHotkeys(['1', '2', 'd1', 'd2', 'reroll', '0'])).toEqual(['1', '2', '3', '4', '5', '0']);
    expect(menuHotkeys(['give', 'rob'])).toEqual(['1', '2']);
  });

  it('가격이 띄어쓰기만 달라도 다시 붙이지 않는다, 목록 줄에 단축키·희귀도', () => {
    expect(hasPrice('깨진 잔 조각 40 전표', '40전표')).toBe(true);
    const m: UiMenu = {
      id: 'shop',
      title: '상점',
      lines: [
        {
          key: 'd1',
          label: '[common] 깨진 잔 조각 40 전표',
          enabled: true,
          rarity: 'rare',
          price: { kind: 'gold', amount: 40, label: '40전표', affordable: true },
        },
      ],
    };
    const [l] = menuLines(m);
    expect(l.label).toBe('깨진 잔 조각 40 전표');
    expect(l.hotkey).toBe('1');
    expect(l.key).toBe('d1');
    expect(l.rarity).toBe(2);
  });
});
