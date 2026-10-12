import { describe, expect, it } from 'vitest';
import type { UiRouteNode } from '../contract/ui';
import {
  fadeIn,
  kenBurnsCrop,
  kenBurnsZoom,
  overlapArea,
  pickPreviewArt,
  placePreview,
  previewText,
  readPreviewKey,
  readPreviewRegion,
  regionIdArt,
  spotCrop,
  type Obstacle,
} from './previewView';

const AREA = { x: 75, y: 123, w: 565, h: 317 };
/** 노드 지도 카드: 그림 256×144 + 테 4·2 + 그늘 3 */
const SIZE = { w: 267, h: 155 };
const node = (p: Partial<UiRouteNode>): UiRouteNode => ({
  id: 'n',
  type: 'battle',
  name: '깨진 술잔 광장',
  col: 1,
  row: 0,
  links: [],
  state: 'available',
  reward: null,
  risk: null,
  riskText: '',
  prefixes: null,
  eventName: null,
  hidden: null,
  grade: null,
  ...p,
});
const tx = (k: string): string =>
  ({ rewardHead: '보상 {name}', riskHead: '위험 {name}', riskElite: '정예 길', riskCurse: '저주 길' })[k] ?? k;
const inside = (r: { x: number; y: number; w: number; h: number }) =>
  r.x >= AREA.x && r.y >= AREA.y && r.x + r.w <= AREA.x + AREA.w && r.y + r.h <= AREA.y + AREA.h;
const anchorBox = (x: number, y: number, weight = 1000): Obstacle => ({
  rect: { x: x - 20, y: y - 20, w: 40, h: 48 },
  weight,
});

describe('62 루프 3 UI G 지도 미리보기 — 자리', () => {
  it('겹침 넓이', () => {
    expect(overlapArea({ x: 0, y: 0, w: 10, h: 10 }, { x: 5, y: 5, w: 10, h: 10 })).toBe(25);
    expect(overlapArea({ x: 0, y: 0, w: 10, h: 10 }, { x: 10, y: 0, w: 5, h: 5 })).toBe(0);
  });

  it('왼쪽에 있는 곳 → 카드는 오른쪽 빈자리, 오른쪽 곳 → 왼쪽 (지도 칸 안, 가리킨 곳을 가리지 않음)', () => {
    const a = { x: 194, y: 206 };
    const p = placePreview(a, SIZE, AREA, [anchorBox(a.x, a.y)], 26);
    expect(p.side).toBe('right');
    expect(inside({ ...p, ...SIZE })).toBe(true);
    expect(overlapArea({ ...p, ...SIZE }, anchorBox(a.x, a.y).rect)).toBe(0);
    const b = { x: 575, y: 230 };
    const q = placePreview(b, SIZE, AREA, [anchorBox(b.x, b.y)], 26);
    expect(q.side).toBe('left');
    expect(inside({ ...q, ...SIZE })).toBe(true);
    expect(overlapArea({ ...q, ...SIZE }, anchorBox(b.x, b.y).rect)).toBe(0);
  });

  it('지도 칸 어디를 가리켜도 그 곳 아이콘을 가리지 않는 자리가 있다 (노드 지도 카드 크기)', () => {
    for (let x = AREA.x + 10; x <= AREA.x + AREA.w - 10; x += 15)
      for (const y of [140, 230, 300, 420]) {
        const icon = { rect: { x: x - 20, y: y - 20, w: 40, h: 40 }, weight: 1000 };
        const p = placePreview({ x, y }, SIZE, AREA, [icon], 26);
        expect(overlapArea({ ...p, ...SIZE }, icon.rect)).toBe(0);
      }
  });

  it('넓은 쪽에 갈 수 있는 곳이 몰려 있으면 덜 겹치는 반대쪽·위아래를 고른다', () => {
    const a = { x: 300, y: 300 };
    const crowd = { rect: { x: 330, y: 160, w: 300, h: 270 }, weight: 6 };
    const p = placePreview(a, SIZE, AREA, [anchorBox(a.x, a.y), crowd], 26);
    expect(p.side).not.toBe('right');
    expect(overlapArea({ ...p, ...SIZE }, anchorBox(a.x, a.y).rect)).toBe(0);
  });

  it('가운데 곳도 지도 칸 밖으로 나가지 않는다 · 정수 좌표', () => {
    for (const a of [
      { x: 80, y: 130 },
      { x: 635, y: 435 },
      { x: 357, y: 281 },
    ]) {
      const p = placePreview(a, SIZE, AREA, [anchorBox(a.x, a.y)], 26);
      expect(inside({ ...p, ...SIZE })).toBe(true);
      expect(Number.isInteger(p.x) && Number.isInteger(p.y)).toBe(true);
    }
  });
});

describe('62 루프 3 UI G 지도 미리보기 — 글·그림', () => {
  it('글: 이름·종류·설명 첫 문장·보상/위험 한 줄·위험 경고, 이벤트 내용이 공개되면 그것', () => {
    const t = previewText(
      node({
        desc: '출병식이 열리던 광장. 바닥에 깨진 잔이 깔렸다.',
        reward: 'gold',
        risk: 'elite',
        riskText: '정예가 지킨다',
      }),
      '전투',
      tx,
    );
    expect(t.name).toBe('깨진 술잔 광장');
    expect(t.kind).toBe('전투');
    expect(t.line).toBe('출병식이 열리던 광장.');
    expect(t.marks).toMatch(/^보상 .+ · 위험 정예 길$/);
    expect(t.warn).toBe('정예가 지킨다');
    expect(previewText(node({ eventName: '낙오한 징집병', desc: '무언가.' }), '사연', tx).line).toBe('낙오한 징집병');
    expect(previewText(node({ reward: 'gold' }), '전투', tx).warn).toBe('');
  });

  it('숨은 노드 얼룩은 아무 것도 보이지 않는다', () => {
    const t = previewText(node({ hidden: 'smudge', reward: 'gold' }), '전투', tx);
    expect(t).toEqual({ name: '', kind: '', line: '', marks: '', warn: '' });
  });

  it('그림: previewKey 가 로드돼 있으면 그것 → 없으면 previewRegion 키아트(받는 중 표시) → 지역 이름 → 종이', () => {
    const has = (k: string) => (k === 'paint/door_gate_battle' ? k : null);
    expect(pickPreviewArt({ previewKey: 'paint/door_gate_battle', previewRegion: 'gate' }, has)).toEqual({
      art: { kind: 'texture', key: 'paint/door_gate_battle' },
      pending: null,
    });
    expect(pickPreviewArt({ previewKey: 'paint/door_hall_boss', previewRegion: 'hall' }, has)).toEqual({
      art: { kind: 'keyart', art: 'hall' },
      pending: 'paint/door_hall_boss',
    });
    expect(pickPreviewArt({ region: '양조 구역' }, has).art).toEqual({ kind: 'keyart', art: 'brewery' });
    expect(pickPreviewArt({ previewRegion: 'training' }, has)).toEqual({ art: { kind: 'paper' }, pending: null });
    expect(regionIdArt('boss')).toBe('hall');
    expect(regionIdArt('training')).toBeNull();
  });

  it('계약 필드 이름으로 읽기 (없거나 빈 글은 null)', () => {
    expect(readPreviewKey({ previewKey: 'paint/door_waste_battle' })).toBe('paint/door_waste_battle');
    expect(readPreviewKey({ previewKey: '' })).toBeNull();
    expect(readPreviewKey(null)).toBeNull();
    expect(readPreviewRegion({ previewRegion: 'waste' })).toBe('waste');
  });

  it('켄번스: 1 → 1.03 → 1 왕복, 자르기는 그림 안 · 가운데', () => {
    expect(kenBurnsZoom(0, 1.03, 9000)).toBeCloseTo(1, 6);
    expect(kenBurnsZoom(9000, 1.03, 9000)).toBeCloseTo(1.03, 6);
    expect(kenBurnsZoom(18000, 1.03, 9000)).toBeCloseTo(1, 6);
    const z = kenBurnsZoom(4500, 1.03, 9000);
    expect(z).toBeGreaterThan(1);
    expect(z).toBeLessThan(1.03);
    const c = kenBurnsCrop(576, 324, 1.03);
    expect(c.w).toBeCloseTo(576 / 1.03, 6);
    expect(c.x).toBeCloseTo((576 - c.w) / 2, 6);
    const l = kenBurnsCrop(576, 324, 1.03, -1);
    expect(l.x).toBe(0);
    const r = kenBurnsCrop(576, 324, 1.03, 1);
    expect(r.x + r.w).toBeCloseTo(576, 6);
  });

  it('교차 페이드 0 → 1 (0.15초)', () => {
    expect(fadeIn(0, 150)).toBe(0);
    expect(fadeIn(75, 150)).toBe(0.5);
    expect(fadeIn(300, 150)).toBe(1);
    expect(fadeIn(10, 0)).toBe(1);
  });

  it('수련장 지도 조각: 16:9 · 그림 밖으로 나가지 않게 민다', () => {
    const c = spotCrop(0.5, 0.5, 960, 540, 0.3);
    expect(c.w).toBe(288);
    expect(c.h).toBe(162);
    expect(c.x).toBe(336);
    const e = spotCrop(0.02, 0.98, 960, 540, 0.3);
    expect(e.x).toBe(0);
    expect(e.y + e.h).toBe(540);
  });
});
