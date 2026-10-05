import { describe, expect, it } from 'vitest';
import { routeNode, routeOf } from './fixtures';
import { cardAlpha, findNode, firstSentence, regionArtKey, regionChanged } from './regionView';
import { MAP_PATHS, REGION_CARD } from './theme';
import { coverCrop, fitContain, layoutOnPath, pathSampler } from './routeView';

describe('regionView (50라운드 지역 카드)', () => {
  it('지역 이름 → 키아트 키', () => {
    expect(regionArtKey('황무지')).toBe('waste');
    expect(regionArtKey('전장')).toBe('waste');
    expect(regionArtKey('성문')).toBe('gate');
    expect(regionArtKey('외곽 거리')).toBe('outer');
    expect(regionArtKey('양조 구역')).toBe('brewery');
    expect(regionArtKey('지배자의 연회장')).toBe('hall');
    expect(regionArtKey('hall')).toBe('hall');
    expect(regionArtKey('  ')).toBeNull();
    expect(regionArtKey(undefined)).toBeNull();
    expect(regionArtKey('하수도')).toBeNull();
  });

  it('지역이 바뀔 때만 카드', () => {
    expect(regionChanged('성문', null)).toBe(true);
    expect(regionChanged('성문', '성문')).toBe(false);
    expect(regionChanged(' 성문 ', '성문')).toBe(false);
    expect(regionChanged('외곽 거리', '성문')).toBe(true);
    expect(regionChanged('', '성문')).toBe(false);
    expect(regionChanged(undefined, null)).toBe(false);
  });

  it('노드 찾기', () => {
    const r = routeOf({
      floor: 1,
      currentId: 'a',
      choosing: false,
      nodes: [routeNode({ id: 'a', type: 'journey', name: 'A', state: 'current', region: '황무지' })],
    });
    expect(findNode(r, 'a')?.region).toBe('황무지');
    expect(findNode(r, 'x')).toBeNull();
    expect(findNode(null, 'a')).toBeNull();
  });

  it('카드 밝기: 나타남 → 머묾 → 사라짐, 글자는 조금 늦게, 넘기면 짧게', () => {
    const t = REGION_CARD;
    expect(cardAlpha(0, t)).toEqual({ bg: 0, text: 0, done: false });
    const mid = cardAlpha(t.fadeInMs * t.textLag, t);
    expect(mid.bg).toBeCloseTo(t.textLag);
    expect(mid.text).toBe(0);
    expect(cardAlpha(t.fadeInMs + 100, t).bg).toBe(1);
    expect(cardAlpha(t.fadeInMs * (1 + t.textLag), t).text).toBe(1);
    expect(cardAlpha(t.fadeInMs + t.holdMs + t.fadeOutMs, t).done).toBe(true);
    const total = t.fadeInMs + t.holdMs + t.fadeOutMs;
    expect(total).toBeGreaterThanOrEqual(1600);
    expect(total).toBeLessThanOrEqual(2000);
    const skip = { at: 500, fadeMs: 160, from: 1 };
    expect(cardAlpha(580, t, skip).bg).toBeCloseTo(0.5);
    expect(cardAlpha(660, t, skip).done).toBe(true);
  });

  it('설명 첫 문장 (지역 키 문구가 없을 때)', () => {
    expect(firstSentence('술통이 쌓인 좁은 거리. 둘째 문장.')).toBe('술통이 쌓인 좁은 거리.');
    expect(firstSentence('마침표 없음')).toBe('마침표 없음');
    expect(firstSentence('')).toBe('');
    expect(firstSentence(undefined)).toBe('');
  });
});

describe('routeView (50라운드 일러스트 지도)', () => {
  it('길 매개화: 길이·보간·접선', () => {
    const p = pathSampler([
      [0, 0],
      [100, 0],
      [100, 50],
    ]);
    expect(p.length).toBe(150);
    expect(p.at(50)).toEqual({ x: 50, y: 0 });
    expect(p.at(125)).toEqual({ x: 100, y: 25 });
    expect(p.at(-10)).toEqual({ x: 0, y: 0 });
    expect(p.at(999)).toEqual({ x: 100, y: 50 });
    expect(p.tangent(20, 5)).toEqual({ x: 1, y: 0 });
  });

  it('그림 맞추기·덮어 자르기', () => {
    expect(fitContain({ x: 0, y: 0, w: 560, h: 370 }, 960, 540)).toEqual({ x: 0, y: 28, w: 560, h: 315 });
    expect(coverCrop(960, 540, 240, 300)).toEqual({ sx: 264, sy: 0, sw: 432, sh: 540 });
  });

  it('노드는 길을 따라: 첫 단계 = 길 시작, 마지막 = 보스, 갈래는 길에 수직으로 벌어짐', () => {
    const spec = MAP_PATHS[1];
    const rect = { x: 0, y: 0, w: spec.srcW, h: spec.srcH };
    const N = (id: string, col: number, row: number) => routeNode({ id, col, row });
    const nodes = [N('s', 0, 0), N('a', 3, 0), N('b', 3, 1), N('boss', 6, 0)];
    const L = layoutOnPath(nodes, rect, spec);
    const first = spec.points[0];
    const last = spec.points[spec.points.length - 1];
    expect(L.pos.get('s')).toMatchObject({ x: first[0], y: first[1] });
    expect(L.pos.get('boss')).toMatchObject({ x: last[0], y: last[1] });
    const a = L.pos.get('a')!;
    const b = L.pos.get('b')!;
    // 오른쪽 아래로 가는 구간: row 0 은 위쪽, row 1 은 아래쪽, 간격 = rowSpread
    expect(a.y).toBeLessThan(b.y);
    expect(Math.hypot(a.x - b.x, a.y - b.y)).toBeCloseTo(spec.rowSpread, -1);
    // 그림 위쪽(보스)은 더 멀다
    expect(L.pos.get('boss')!.depth).toBeGreaterThan(b.depth);
    for (const p of L.pos.values()) {
      expect(p.x).toBeGreaterThanOrEqual(spec.margin);
      expect(p.x).toBeLessThanOrEqual(spec.srcW - spec.margin);
      expect(p.scale).toBeGreaterThanOrEqual(spec.farScale);
    }
  });

  it('화면 사각형으로 줄이면 좌표도 같은 비율', () => {
    const spec = MAP_PATHS[1];
    const nodes = [routeNode({ id: 'boss', type: 'boss', name: '' })];
    const L = layoutOnPath(nodes, { x: 10, y: 20, w: 480, h: 270 }, { ...spec, points: [[855, 220]] });
    expect(L.pos.get('boss')).toMatchObject({ x: 10 + 428, y: 20 + 110 });
  });
});
