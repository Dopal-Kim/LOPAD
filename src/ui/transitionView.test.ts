import { describe, expect, it } from 'vitest';
import { TRANSITION } from './themeTransition';
import {
  brushOrder,
  coverAt,
  diveFocus,
  diveZoom,
  doorShape,
  edgeBleed,
  fallbackDoorRect,
  freezeAlpha,
  paintPixels,
  planFor,
  planTotal,
  readBegin,
  readDoorMeta,
  readId,
  regionKeyart,
  revealAlpha,
  skipAction,
  worldTransform,
} from './transitionView';
import {
  noteTransitionOrigin,
  setTransitionBusy,
  setTransitionCovered,
  takeTransitionOrigin,
  transitionOpening,
} from './transitionState';

describe('transitionView (61 단계 6 그림 속 입구 전환)', () => {
  it('시작 페이로드 읽기: id·mode 필수, 나머지 기본', () => {
    expect(readBegin(null)).toBeNull();
    expect(readBegin({ id: 1, mode: 'nope' })).toBeNull();
    expect(readBegin({ mode: 'enterNode' })).toBeNull();
    const b = readBegin({
      id: 3,
      mode: 'enterNode',
      region: 'gate',
      nodeKind: 'battle',
      from: { x: 10, y: 20 },
      nodeId: 'n4',
      skippable: true,
    });
    expect(b).toEqual({
      id: 3,
      mode: 'enterNode',
      region: 'gate',
      nodeKind: 'battle',
      doorKey: null,
      from: { x: 10, y: 20 },
      nodeId: 'n4',
      skippable: true,
    });
    const c = readBegin({ id: 4, mode: 'exitRoom', from: { x: 'a' }, doorKey: '' });
    expect(c?.from).toBeNull();
    expect(c?.doorKey).toBeNull();
    expect(c?.skippable).toBe(true);
    expect(readBegin({ id: 5, mode: 'floor', skippable: false })?.skippable).toBe(false);
    expect(readId({ id: 7 })).toBe(7);
    expect(readId({})).toBeNull();
  });

  it('단계 길이: 덮기까지 + 걷힘 = 1.2~1.8초', () => {
    for (const m of ['enterNode', 'exitRoom', 'floor', 'training'] as const) {
      const p = planFor(m);
      const total = planTotal(p);
      expect(total).toBeGreaterThanOrEqual(1200);
      expect(total).toBeLessThanOrEqual(1800);
      expect(coverAt(p)).toBeLessThan(total);
      // 시스템 안전장치(덮임 3초)보다 한참 먼저 덮는다
      expect(coverAt(p)).toBeLessThan(2000);
    }
    expect(planFor('exitRoom').frameMs).toBeGreaterThan(0);
    expect(planFor('enterNode').frameMs).toBe(0);
  });

  it('파고들기: 배율은 1 → zEnd, 목표는 제자리에서 화면 가운데로', () => {
    const C = { x: 480, y: 270 };
    const T = { x: 700, y: 120 };
    expect(diveZoom(0, 50)).toBeCloseTo(1);
    expect(diveZoom(1, 50)).toBeCloseTo(50);
    expect(diveZoom(0.5, 50)).toBeGreaterThan(1);
    expect(diveZoom(0.5, 50)).toBeLessThan(50);
    const screenOf = (pan: number, z: number) => {
      const f = diveFocus(pan, z, T, C);
      const tr = worldTransform(f, z, C);
      return { x: T.x * tr.scale + tr.x, y: T.y * tr.scale + tr.y };
    };
    const s0 = screenOf(0, 1);
    expect(s0.x).toBeCloseTo(T.x);
    expect(s0.y).toBeCloseTo(T.y);
    const s1 = screenOf(1, 40);
    expect(s1.x).toBeCloseTo(C.x);
    expect(s1.y).toBeCloseTo(C.y);
    const sm = screenOf(0.5, 6);
    expect(sm.x).toBeCloseTo((T.x + C.x) / 2);
  });

  it('입구 메타: doorRect 사각형·배열, light 색, 그림 밖은 자름', () => {
    expect(readDoorMeta(null, 640, 360)).toEqual({ rect: null, light: null });
    expect(readDoorMeta({ doorRect: { x: 280, y: 150, w: 80, h: 160 }, light: '#E2A33C' }, 640, 360)).toEqual({
      rect: { x: 280, y: 150, w: 80, h: 160 },
      light: '#e2a33c',
    });
    expect(readDoorMeta({ meta: { doorRect: [600, 300, 100, 100], light: [255, 0, 16] } }, 640, 360)).toEqual({
      rect: { x: 600, y: 300, w: 40, h: 60 },
      light: '#ff0010',
    });
    expect(readDoorMeta({ doorRect: { x: 1, y: 2, width: 3, height: 4 } }, 640, 360).rect).toEqual({
      x: 1,
      y: 2,
      w: 3,
      h: 4,
    });
  });

  it('대체 입구: 노드 종류별 모양, 그림 안 사각형', () => {
    expect(doorShape('boss')).toBe('gate');
    expect(doorShape('shop')).toBe('door');
    expect(doorShape('training')).toBe('door');
    expect(doorShape('rest')).toBe('cave');
    expect(doorShape('battle')).toBe('arch');
    expect(doorShape('')).toBe('arch');
    for (const s of ['arch', 'gate', 'door', 'cave'] as const) {
      const r = fallbackDoorRect(s, 640, 360);
      expect(r.x).toBeGreaterThan(0);
      expect(r.y).toBeGreaterThan(0);
      expect(r.x + r.w).toBeLessThan(640);
      expect(r.y + r.h).toBeLessThan(360);
    }
  });

  it('지역 코드 → 키아트', () => {
    expect(regionKeyart('gate')).toBe('gate');
    expect(regionKeyart('boss')).toBe('hall');
    expect(regionKeyart('training')).toBeNull();
    expect(regionKeyart('')).toBeNull();
  });

  it('붓질 걷힘: 0~1 순서, 시작엔 다 덮임 · 끝엔 다 걷힘, 앞쪽은 부드럽게', () => {
    const w = 48;
    const h = 27;
    const o = brushOrder(w, h, 11);
    expect(o.length).toBe(w * h);
    let min = 1;
    let max = 0;
    for (const v of o) {
      min = Math.min(min, v);
      max = Math.max(max, v);
    }
    expect(min).toBeGreaterThanOrEqual(0);
    expect(max).toBeLessThanOrEqual(1);
    expect(max - min).toBeGreaterThan(0.6);
    // 같은 시드는 같은 결과
    expect(brushOrder(w, h, 11)).toEqual(o);
    for (const v of [0, 0.3, 1]) {
      expect(revealAlpha(v, 0)).toBe(1);
      expect(revealAlpha(v, 1)).toBe(0);
    }
    expect(revealAlpha(0.2, 0.5)).toBe(0);
    expect(revealAlpha(0.9, 0.5)).toBe(1);
  });

  it('굳음: 출구에서부터 번지고 끝엔 다 그림', () => {
    expect(freezeAlpha(0, 0.5, 0)).toBe(0);
    expect(freezeAlpha(1, 0.5, 1)).toBe(1);
    expect(freezeAlpha(0.05, 0.5, 0.5)).toBe(1);
    expect(freezeAlpha(0.95, 0.5, 0.3)).toBe(0);
  });

  it('붓 그림 처리: 알파 채움, 가장자리는 종이 색으로, 색 단계 줄임', () => {
    const w = 40;
    const h = 24;
    const px = new Uint8ClampedArray(w * h * 4);
    for (let i = 0; i < w * h; i++) {
      px[i * 4] = (i * 7) % 256;
      px[i * 4 + 1] = (i * 13) % 256;
      px[i * 4 + 2] = (i * 3) % 256;
      px[i * 4 + 3] = 0;
    }
    const paper: [number, number, number] = [48, 38, 30];
    paintPixels(px, w, h, { levels: 4, keepSat: 0.6, warm: 0, inkEdge: 0, grain: 0, bleed: 0.2, paper, seed: 3 });
    for (let i = 0; i < w * h; i++) expect(px[i * 4 + 3]).toBe(255);
    // 모서리 = 종이
    expect(px[0]).toBe(paper[0]);
    expect(px[1]).toBe(paper[1]);
    expect(edgeBleed(0, 0, w, h, 0.5)).toBe(1);
    expect(edgeBleed(w / 2, h / 2, w, h, 0.5)).toBe(0);
  });

  it('건너뛰기: 덮기 전 → 바로 덮음, 덮인 뒤(READY) · 걷힘 → 짧게 걷음', () => {
    expect(skipAction('intro', false)).toBe('toCovered');
    expect(skipAction('move', false)).toBe('toCovered');
    expect(skipAction('covered', false)).toBe('none');
    expect(skipAction('covered', true)).toBe('fastReveal');
    expect(skipAction('reveal', true)).toBe('fastReveal');
    expect(skipAction('idle', true)).toBe('none');
    expect(TRANSITION.skipRevealMs).toBeLessThan(TRANSITION.revealMs);
  });

  it('전환 상태: 파고들 자리는 같은 종류·id·시간 안에서 한 번', () => {
    noteTransitionOrigin('route', 'n1', 100, 200, 1000);
    expect(takeTransitionOrigin('training', null, 1100)).toBeNull();
    noteTransitionOrigin('route', 'n1', 100, 200, 1000);
    expect(takeTransitionOrigin('route', 'n2', 1100)).toBeNull();
    noteTransitionOrigin('route', 'n1', 100, 200, 1000);
    expect(takeTransitionOrigin('route', 'n1', 1100)).toEqual({ x: 100, y: 200 });
    expect(takeTransitionOrigin('route', 'n1', 1100)).toBeNull();
    noteTransitionOrigin('training', 'r2', 5, 6, 1000);
    expect(takeTransitionOrigin('training', undefined, 1000 + 99999)).toBeNull();
    setTransitionBusy(true);
    expect(transitionOpening()).toBe(true);
    setTransitionCovered();
    expect(transitionOpening()).toBe(false);
    setTransitionBusy(false);
    expect(transitionOpening()).toBe(false);
  });
});
