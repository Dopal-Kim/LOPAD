import { describe, expect, it } from 'vitest';
import type { UiSnapshot } from '../contract/ui';
import { isTutorialNode, parseNoticeKeys, shouldWarn, tutorialKey, tutorialRows } from './tutorialView';

const route = (type: string) =>
  ({
    floor: 1,
    currentId: 'n0',
    choosing: false,
    nodes: [{ id: 'n0', type, name: '탄생지', col: 0, row: 0, links: [], state: 'current' }],
  }) as unknown as UiSnapshot['route'];

const T = (k: string, v?: Record<string, string>) =>
  ({ tutMove: '이동', keyLeftClick: '좌클릭', keyRightClick: '우클릭', keySpace: 'Space' })[k] ??
  `${k}${v ? JSON.stringify(v) : ''}`;

describe('tutorialView (53라운드 튜토리얼 안내)', () => {
  it('여정 노드만 튜토리얼 (시험장 제외)', () => {
    expect(isTutorialNode({ route: route('journey'), lab: false })).toBe(true);
    expect(isTutorialNode({ route: route('battle'), lab: false })).toBe(false);
    expect(isTutorialNode({ route: route('journey'), lab: true })).toBe(false);
    expect(isTutorialNode({ route: null, lab: false })).toBe(false);
  });
  it('한 번 띄우기 열쇠', () => {
    expect(tutorialKey({ route: route('journey'), lab: false, seed: 'abc' })).toBe('abc|n0');
    expect(tutorialKey({ route: route('battle'), lab: false, seed: 'abc' })).toBe('');
  });
  it('안내 줄: 넣고 뽑는 무기면 F 줄', () => {
    const weapon = { name: '대검', evolutionName: null, personality: 0, threshold: 1, secondaryName: '가드' };
    const withF = tutorialRows({ weapon, carry: { drawn: false, firstStrike: '끌어내기', key: 'F' } }, T);
    expect(withF.map((r) => r.keys.join(''))).toEqual(['WASD', '좌클릭', '우클릭', 'Space', 'F']);
    expect(withF[4].text).toContain('끌어내기');
    expect(tutorialRows({ weapon, carry: null }, T).some((r) => r.keys[0] === 'F')).toBe(false);
  });
  it('경고: 튜토리얼에서 전투가 막 시작될 때만', () => {
    const s = { inCombat: true, route: route('journey'), lab: false };
    expect(shouldWarn(false, s)).toBe(true);
    expect(shouldWarn(true, s)).toBe(false);
    expect(shouldWarn(false, { ...s, route: route('battle') })).toBe(false);
  });
  it('공지 끝 괄호의 키', () => {
    expect(parseNoticeKeys('땅의 표식까지 걸어가 보자. (WASD)')).toEqual({
      text: '땅의 표식까지 걸어가 보자.',
      keys: ['W', 'A', 'S', 'D'],
    });
    expect(parseNoticeKeys('허수아비를 베어 보자 (좌클릭)').keys).toEqual(['좌클릭']);
    expect(parseNoticeKeys('대쉬로 피하자 (Space · Shift)').keys).toEqual(['Space', 'Shift']);
    expect(parseNoticeKeys('그냥 문장')).toEqual({ text: '그냥 문장', keys: [] });
  });
});
