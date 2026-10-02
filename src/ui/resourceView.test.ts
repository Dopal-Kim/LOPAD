import { describe, expect, it } from 'vitest';
import type { UiRouteNode } from '../contract/ui';
import {
  ammoCells,
  heatStage,
  menuIndent,
  replaceMuteHint,
  resourceRatio,
  ringLit,
  ringPoints,
  shownValue,
} from './resourceView';
import { ellipseRows, layoutPerspective, perspectiveCurve, trapezoidRows } from './routeView';

describe('resourceView (49라운드 무기 자원)', () => {
  it('비율은 0..1, max 0 은 0', () => {
    expect(resourceRatio({ value: 50, max: 100 })).toBe(0.5);
    expect(resourceRatio({ value: 150, max: 100 })).toBe(1);
    expect(resourceRatio({ value: 5, max: 0 })).toBe(0);
  });

  it('화살 칸: 내림, 상한을 넘으면 막대', () => {
    expect(ammoCells(3.7, 6, 12)).toEqual({ filled: 3, total: 6, compact: false });
    expect(ammoCells(9, 6, 12)).toEqual({ filled: 6, total: 6, compact: false });
    expect(ammoCells(10, 30, 12).compact).toBe(true);
    expect(ammoCells(NaN, NaN, 12)).toEqual({ filled: 0, total: 0, compact: false });
  });

  it('진행 링: 12시부터 시계 방향, 겹치는 점 없음', () => {
    const pts = ringPoints(5);
    expect(pts[0]).toEqual({ x: 0, y: -5 });
    expect(new Set(pts.map((p) => `${p.x},${p.y}`)).size).toBe(pts.length);
    // 1/4 지점 근처는 오른쪽(3시)
    const q = pts[Math.round(pts.length / 4)];
    expect(q.x).toBeGreaterThan(3);
    expect(ringLit(pts.length, 0)).toBe(0);
    expect(ringLit(pts.length, 1)).toBe(pts.length);
    expect(ringLit(pts.length, 2)).toBe(pts.length);
  });

  it('열기 단계: stage 우선, 없으면 비율', () => {
    expect(heatStage({ value: 0, max: 100, stage: 2 })).toBe(2);
    expect(heatStage({ value: 0, max: 100, stage: 9 })).toBe(3);
    expect(heatStage({ value: 0, max: 100 })).toBe(0);
    expect(heatStage({ value: 34, max: 100 })).toBe(1);
    expect(heatStage({ value: 100, max: 100 })).toBe(3);
  });

  it('표시 값: 바닥은 0, 조금 남으면 올림', () => {
    expect(shownValue(0)).toBe(0);
    expect(shownValue(-3)).toBe(0);
    expect(shownValue(0.2)).toBe(1);
    expect(shownValue(42)).toBe(42);
  });
});

describe('menuIndent (무기 시험장 갈래)', () => {
  it('앞 공백·트리 기호·key 구분자로 깊이를 센다', () => {
    expect(menuIndent({ key: '1', label: '사무라이 칼' })).toEqual({ depth: 0, label: '사무라이 칼' });
    expect(menuIndent({ key: '2', label: '  └ 거합' })).toEqual({ depth: 2, label: '거합' });
    expect(menuIndent({ key: '3', label: '└ 거합' })).toEqual({ depth: 1, label: '거합' });
    expect(menuIndent({ key: '4', label: '    잔광' })).toEqual({ depth: 2, label: '잔광' });
    expect(menuIndent({ key: '1.2', label: '갈래' })).toEqual({ depth: 1, label: '갈래' });
    expect(menuIndent({ key: 'a/b/c', label: '갈래' }).depth).toBe(2);
  });
});

describe('replaceMuteHint', () => {
  it("'M 음소거' 를 지도 문구로", () => {
    expect(replaceMuteHint('WASD 이동 · M 음소거 · Esc', 'M 지도')).toBe('WASD 이동 · M 지도 · Esc');
    expect(replaceMuteHint('WASD 이동', 'M 지도')).toBe('WASD 이동');
  });
});

const node = (id: string, col: number, row: number): UiRouteNode => ({
  id,
  type: 'battle',
  name: id,
  col,
  row,
  links: [],
  state: 'locked',
});

describe('layoutPerspective (49라운드 입체 지도)', () => {
  const opts = { rowMax: 150, farScale: 0.6, ease: 0.5, minGap: 30, padTop: 40, padBottom: 20 };
  const area = { x: 0, y: 0, w: 560, h: 360 };

  it('곡선은 0→0, 1→1, 멀수록 촘촘', () => {
    expect(perspectiveCurve(0, 0.5)).toBe(0);
    expect(perspectiveCurve(1, 0.5)).toBeCloseTo(1);
    const a = perspectiveCurve(0.25, 0.5) - perspectiveCurve(0, 0.5);
    const b = perspectiveCurve(1, 0.5) - perspectiveCurve(0.75, 0.5);
    expect(a).toBeGreaterThan(b);
    expect(perspectiveCurve(0.3, 0)).toBeCloseTo(0.3);
  });

  it('첫 단계가 아래(가까움), 마지막이 위(멂). 간격은 멀수록 좁고 좌우 폭이 줄어든다', () => {
    const nodes = [
      node('a', 0, 0),
      node('b', 1, 0),
      node('c', 1, 1),
      node('d', 2, 0),
      node('e', 3, 0),
      node('f', 3, 1),
    ];
    const L = layoutPerspective(nodes, area, opts);
    const a = L.pos.get('a')!;
    const d = L.pos.get('d')!;
    const e = L.pos.get('e')!;
    expect(a.y).toBe(340);
    expect(e.y).toBe(40);
    expect(a.depth).toBe(0);
    expect(e.depth).toBe(1);
    expect(a.scale).toBe(1);
    expect(e.scale).toBeCloseTo(0.6);
    const gapNear = a.y - L.pos.get('b')!.y;
    const gapFar = d.y - e.y;
    expect(gapNear).toBeGreaterThan(gapFar);
    const spreadNear = L.pos.get('c')!.x - L.pos.get('b')!.x;
    const spreadFar = L.pos.get('f')!.x - e.x;
    expect(spreadNear).toBeGreaterThan(spreadFar);
    expect(a.x).toBe(280);
  });

  it('먼 간격이 minGap 보다 좁아지면 고른 간격으로 푼다', () => {
    const many = Array.from({ length: 14 }, (_, i) => node(`n${i}`, i, 0));
    const L = layoutPerspective(many, area, { ...opts, minGap: 25 });
    expect(L.ease).toBe(0);
    const ys = many.map((n) => L.pos.get(n.id)!.y);
    const gaps = ys.slice(1).map((y, i) => ys[i] - y);
    expect(Math.max(...gaps) - Math.min(...gaps)).toBeLessThanOrEqual(1);
  });

  it('사다리꼴·타원 줄은 정수', () => {
    const rows = trapezoidRows(100, 0, 10, 40, 80);
    expect(rows[0]).toEqual({ x: 80, y: 0, w: 40 });
    expect(rows[rows.length - 1]).toEqual({ x: 60, y: 10, w: 80 });
    const el = ellipseRows(0, 0, 10, 3);
    expect(el.every((r) => Number.isInteger(r.x) && Number.isInteger(r.w))).toBe(true);
    expect(Math.max(...el.map((r) => r.w))).toBe(20);
  });
});
