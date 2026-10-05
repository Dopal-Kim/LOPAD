import { describe, expect, it } from 'vitest';
import { intelLine, isSmudged, nodeInfoLines, nodeLook, nodeSig, rewardLegend } from './bundleView';
import { routeNode } from './fixtures';

describe('bundleView (60라운드 §14.5 노드 지도)', () => {
  it('숨은 노드 얼룩은 보상·위험을 숨긴다 (found 는 보통 노드)', () => {
    const smudge = routeNode({ id: 'h', hidden: 'smudge', reward: 'gold', risk: 'elite', state: 'locked' });
    expect(nodeLook(smudge)).toEqual({ hidden: 'smudge', reward: null, risk: null, grade: null });
    expect(isSmudged(smudge)).toBe(true);
    expect(isSmudged(routeNode({ id: 'h', hidden: 'located' }))).toBe(true);
    expect(isSmudged(routeNode({ id: 'h', hidden: 'found' }))).toBe(false);
    // 계약 코드가 아직 선택 필드라 없을 수 있다
    expect(nodeLook({ id: 'x' })).toEqual({ hidden: null, reward: null, risk: null, grade: null });
  });

  it('오른쪽 칸 줄: 보상·위험(+ 위험 한 줄)·접두어·이벤트 내용·도장', () => {
    const n = routeNode({
      id: 'e',
      reward: 'passive',
      risk: 'elite',
      riskText: '엘리트 둘이 기다린다',
      prefixes: ['불붙은'],
      grade: 'good',
    });
    expect(nodeInfoLines(n)).toEqual([
      '보상 패시브',
      '위험 엘리트 길',
      '엘리트 둘이 기다린다',
      '접두어 불붙은',
      '도장 양',
    ]);
    expect(nodeInfoLines(routeNode({ id: 'v', type: 'event', reward: 'unknown', eventName: '마지막 잔' }))).toEqual([
      '보상 알 수 없음',
      '내용 마지막 잔',
    ]);
    expect(nodeInfoLines(routeNode({ id: 'h', hidden: 'smudge' }))).toEqual(['얼룩진 자국 — 어딘가 숨은 길이 있다']);
    expect(nodeInfoLines(routeNode({ id: 'h', hidden: 'found' }))[0]).toBe('숨은 길');
  });

  it('산 지도 정보 한 줄', () => {
    expect(intelLine(undefined)).toBe('');
    expect(intelLine({ nextTier: false, fullFloor: false, hiddenLocated: false })).toBe('');
    expect(intelLine({ nextTier: true, fullFloor: false, hiddenLocated: true })).toBe(
      '산 지도 정보 · 다음 단 · 숨은 길 위치',
    );
  });

  it('보상 글리프 범례는 지도에 보이는 것만, 처음 나온 차례로', () => {
    const nodes = [
      routeNode({ id: 'a', reward: 'gold' }),
      routeNode({ id: 'b', reward: 'curse' }),
      routeNode({ id: 'c', reward: 'gold' }),
      routeNode({ id: 'd', hidden: 'smudge', reward: 'passive' }),
    ];
    expect(rewardLegend(nodes)).toBe('전 전표 주머니 · 저 저주');
    expect(rewardLegend([])).toBe('');
  });

  it('서명에 §14.5 필드가 들어간다 (도장이 찍히면 노드 띠를 다시 그린다)', () => {
    const a = routeNode({ id: 'a', state: 'cleared' });
    expect(nodeSig(a)).not.toBe(nodeSig({ ...a, grade: 'perfect' }));
    expect(nodeSig(a)).not.toBe(nodeSig({ ...a, hidden: 'found' }));
  });
});
