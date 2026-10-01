import { describe, expect, it } from 'vitest';
import { STAGES } from '../data';
import { TileId, generateFloor } from '../systems/mapgen';
import { PROPS_RULES, TileSkin, pickVariant, planProps, wallKind, type TilesetJson } from './tileskin';

// 아트 1층 타일셋 JSON 과 같은 구조 (계약 §2)
const stage1: TilesetJson = {
  image: 'stage1.png',
  tiles: { '0': [7], '1': [0, 1, 2, 3], '2': [5], '3': [8], '4': [9], '5': [10], '6': [4], '7': [11], '8': [12] },
  walls: { top: 5, bottom: 6, left: 6, right: 6, corner_tl: 6, corner_tr: 6, corner_bl: 6, corner_br: 6 },
  props: [
    { index: 13, name: 'barrel', solid: true },
    { index: 14, name: 'broken_bottle', solid: false },
    { index: 15, name: 'puddle', solid: false },
    { index: 16, name: 'lantern', solid: true },
  ],
};

describe('TileSkin (계약 art-assets.md §2)', () => {
  const skin = new TileSkin('tiles_stage1', stage1, true);

  it('ID → 인덱스, 바닥 변형은 좌표 해시로 결정적', () => {
    const a = skin.indexFor(TileId.Floor, 3, 4);
    expect(a).toBe(skin.indexFor(TileId.Floor, 3, 4));
    expect([0, 1, 2, 3]).toContain(a);
    const seen = new Set<number>();
    for (let x = 0; x < 20; x++) for (let y = 0; y < 20; y++) seen.add(skin.indexFor(TileId.Floor, x, y));
    expect(seen.size).toBe(4);
    expect(skin.indexFor(TileId.Exit, 0, 0)).toBe(11);
    expect(pickVariant(5, 5, 1)).toBe(0);
  });

  it('역매핑과 충돌 인덱스 (벽 변형 포함)', () => {
    expect(skin.idOf(6)).toBe(TileId.Wall);
    expect(skin.idOf(5)).toBe(TileId.Wall);
    expect(skin.idOf(9)).toBe(TileId.DoorClosed);
    expect(skin.idOf(2)).toBe(TileId.Floor);
    expect(skin.solidIndices.sort()).toEqual([10, 5, 6, 9].sort());
    expect(skin.solidPropIndices).toEqual([13, 16]);
  });

  it('자동타일: 아래가 열려 있으면 top(벽돌 정면), 그 외는 윗면', () => {
    const open = (_x: number, y: number) => y === 1; // y=1 행이 바닥
    expect(wallKind(open, 0, 0)).toBe('top');
    expect(wallKind(open, 0, 2)).toBe('bottom');
    expect(skin.indexFor(TileId.Wall, 0, 0, open)).toBe(5);
    expect(skin.indexFor(TileId.Wall, 0, 2, open)).toBe(6);
    expect(skin.indexFor(TileId.Wall, 0, 5, () => false)).toBe(5); // 고립 벽 → 단일 벽
  });

  it('플레이스홀더는 항등 매핑', () => {
    const ph = TileSkin.placeholder();
    expect(ph.indexFor(TileId.Wall, 1, 1)).toBe(TileId.Wall);
    expect(ph.idOf(TileId.Shop)).toBe(TileId.Shop);
    expect(ph.props).toHaveLength(0);
  });
});

describe('소품 배치', () => {
  const layout = generateFloor('lopad:0', STAGES.stage1.layout);
  const skin = new TileSkin('tiles_stage1', stage1, true);

  it('시드 결정적이고 방당 2~5개', () => {
    const a = planProps(layout, skin.props, 'lopad:0');
    const b = planProps(layout, skin.props, 'lopad:0');
    expect(a).toEqual(b);
    for (const room of layout.rooms) {
      const I = room.interior;
      const n = a.filter((p) => p.x >= I.x && p.x < I.x + I.w && p.y >= I.y && p.y < I.y + I.h).length;
      expect(n).toBeGreaterThanOrEqual(0);
      expect(n).toBeLessThanOrEqual(PROPS_RULES.MAX_PER_ROOM);
    }
    expect(a.length).toBeGreaterThan(0);
  });

  it('바닥 위에만, 문 주변·시작 지점·보스 방 출구 자리는 비우고, 단단한 소품은 벽가에만', () => {
    const list = planProps(layout, skin.props, 'lopad:0');
    const keys = new Set(list.map((p) => `${p.x},${p.y}`));
    expect(keys.size).toBe(list.length);
    for (const p of list) expect(layout.tiles[p.y][p.x]).toBe(TileId.Floor);
    for (const room of layout.rooms) {
      const I = room.interior;
      const cx = I.x + Math.floor(I.w / 2);
      const cy = I.y + Math.floor(I.h / 2);
      for (const d of room.doors)
        for (const t of d.tiles)
          for (const p of list)
            expect(Math.max(Math.abs(p.x - t.x), Math.abs(p.y - t.y))).toBeGreaterThan(PROPS_RULES.DOOR_CLEAR);
      if (room.type === 'start')
        for (const p of list)
          expect(Math.max(Math.abs(p.x - cx), Math.abs(p.y - cy))).toBeGreaterThan(PROPS_RULES.START_CLEAR);
      if (room.type === 'boss') {
        const B = PROPS_RULES.BOSS_CLEAR;
        for (const p of list) {
          const inside = p.x >= cx - B.left && p.x <= cx + B.right && p.y >= cy - B.up && p.y <= cy + B.down;
          expect(inside).toBe(false);
        }
      }
      for (const p of list.filter((q) => q.solid)) {
        if (p.x < I.x || p.x >= I.x + I.w || p.y < I.y || p.y >= I.y + I.h) continue;
        const ring = p.x === I.x || p.x === I.x + I.w - 1 || p.y === I.y || p.y === I.y + I.h - 1;
        expect(ring).toBe(true);
      }
    }
  });
});
