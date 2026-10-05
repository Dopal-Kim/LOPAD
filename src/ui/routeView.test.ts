import { describe, expect, it } from 'vitest';
import type { UiRouteNode } from '../contract/ui';
import { routeNode, routeOf } from './fixtures';
import { cycle, dottedPoints, hasRoute, layoutRoute, linkKind, remainingSteps, sortNodes } from './routeView';

const n = (id: string, col: number, row: number, state: UiRouteNode['state'] = 'locked'): UiRouteNode =>
  routeNode({ id, col, row, state });

describe('routeView', () => {
  const nodes = [n('a', 0, 0, 'cleared'), n('b', 1, 0, 'current'), n('c', 2, 0), n('d', 2, 1), n('e', 3, 0)];

  it('단계는 영역 가운데로, 같은 단계의 줄은 세로 가운데 정렬', () => {
    const L = layoutRoute(nodes, { x: 0, y: 0, w: 400, h: 200 }, 120, 80);
    expect(L.colStep).toBe(100);
    expect(L.rowStep).toBe(80);
    expect(L.pos.get('a')).toEqual({ x: 50, y: 100 });
    expect(L.pos.get('e')).toEqual({ x: 350, y: 100 });
    expect(L.pos.get('c')).toEqual({ x: 250, y: 60 });
    expect(L.pos.get('d')).toEqual({ x: 250, y: 140 });
  });

  it('단계 간격은 colMax 를 넘지 않고 영역 안에 든다', () => {
    const many = Array.from({ length: 10 }, (_, i) => n(`n${i}`, i, 0));
    const L = layoutRoute(many, { x: 20, y: 0, w: 800, h: 100 }, 120, 80);
    expect(L.colStep).toBe(80);
    const xs = many.map((m) => L.pos.get(m.id)!.x);
    expect(Math.min(...xs)).toBeGreaterThanOrEqual(20);
    expect(Math.max(...xs)).toBeLessThanOrEqual(820);
  });

  it('정렬·순환 고르기', () => {
    expect(sortNodes([n('x', 1, 1), n('y', 1, 0), n('z', 0, 3)]).map((m) => m.id)).toEqual(['z', 'y', 'x']);
    expect(cycle(['a', 'b', 'c'], 'c', 1)).toBe('a');
    expect(cycle(['a', 'b', 'c'], 'a', -1)).toBe('c');
    expect(cycle(['a', 'b'], null, 1)).toBe('a');
    expect(cycle([], null, 1)).toBeNull();
  });

  it('남은 단계', () => {
    const r = routeOf({ floor: 1, nodes, currentId: 'b', choosing: false });
    expect(remainingSteps(r)).toBe(2);
    expect(remainingSteps({ ...r, currentId: null })).toBe(4);
    expect(hasRoute(r)).toBe(true);
    expect(hasRoute(null)).toBe(false);
    expect(hasRoute({ ...r, nodes: [] })).toBe(false);
  });

  it('연결선 종류', () => {
    expect(linkKind('cleared', 'current')).toBe('walked');
    expect(linkKind('current', 'available')).toBe('option');
    expect(linkKind('cleared', 'passed')).toBe('faint');
  });

  it('점선은 양 끝을 비우고 정수 좌표로', () => {
    const pts = dottedPoints(0, 0, 100, 0, 20, 20, 10);
    expect(pts.length).toBe(7);
    expect(pts[0]).toEqual({ x: 20, y: 0 });
    expect(pts[6]).toEqual({ x: 80, y: 0 });
    expect(dottedPoints(0, 0, 10, 0, 6, 6, 4)).toEqual([]);
  });
});
