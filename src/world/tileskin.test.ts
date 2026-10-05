import { describe, expect, it } from 'vitest';
import { STAGES } from '../data';
import { TILE } from '../core/Constants';
import { TileId, generateFloor } from '../systems/mapgen';
import { PROPS_RULES, TileSkin, pickVariant, planProps, roomTypeMap, wallKind, type TilesetJson } from './tileskin';

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

describe('37·40라운드: 방 종류별 바닥 · 벽 변형 · 소품 상한·가중치 · 시트 크기 비의존', () => {
  // 37라운드 아트 JSON (128×64, 인덱스 0~28)
  const v37: TilesetJson = {
    ...stage1,
    tiles: { ...stage1.tiles, '2': [5, 19, 20] },
    roomFloors: { start: [21, 22], trial: [23, 24], rest: [25, 26], boss: [27, 28] },
    props: [
      { index: 13, name: 'barrel', solid: true, maxPerRoom: 1 },
      { index: 14, name: 'bottle', solid: false, weight: 3 },
      { index: 15, name: 'puddle', solid: false, weight: 0 },
    ],
  };
  // 40라운드 재배치 가정 (128×80, 소품 13~20, 벽 변형 21~22, 방 바닥 23~38 각 4변형)
  const v40: TilesetJson = {
    ...stage1,
    tiles: { ...stage1.tiles, '2': [5, 21, 22] },
    roomFloors: { start: [23, 24, 25, 26], trial: [27, 28, 29, 30], rest: [31, 32, 33, 34], boss: [35, 36, 37, 38] },
  };
  const layout = generateFloor('lopad:0', STAGES.stage1.layout);

  it('roomFloors 가 있으면 방 종류별 목록에서, 없거나 비면 tiles["1"] 에서 고른다', () => {
    const skin = new TileSkin('tiles_stage1', v37, true);
    const seen = new Map<string, Set<number>>();
    for (const type of ['start', 'trial', 'rest', 'boss'] as const) {
      const s = new Set<number>();
      for (let x = 0; x < 16; x++)
        for (let y = 0; y < 16; y++) s.add(skin.indexFor(TileId.Floor, x, y, undefined, type));
      seen.set(type, s);
    }
    expect([...seen.get('start')!].sort()).toEqual([21, 22]);
    expect([...seen.get('trial')!].sort()).toEqual([23, 24]);
    expect([...seen.get('rest')!].sort()).toEqual([25, 26]);
    expect([...seen.get('boss')!].sort()).toEqual([27, 28]);
    // 방 종류 없음(복도 근처) → 공통 바닥
    expect([0, 1, 2, 3]).toContain(skin.indexFor(TileId.Floor, 3, 3));
    // 방 바닥 인덱스는 게임 ID 로 되돌리면 바닥
    expect(skin.idOf(24)).toBe(TileId.Floor);
    expect(skin.idOf(28)).toBe(TileId.Floor);
    // 옛 형식(roomFloors 없음)·빈 목록은 공통 바닥
    const old = new TileSkin('tiles_stage1', stage1, true);
    expect([0, 1, 2, 3]).toContain(old.indexFor(TileId.Floor, 5, 5, undefined, 'boss'));
    const empty = new TileSkin('tiles_stage1', { ...stage1, roomFloors: { boss: [] } }, true);
    expect(empty.roomFloors.size).toBe(0);
    expect([0, 1, 2, 3]).toContain(empty.indexFor(TileId.Floor, 5, 5, undefined, 'boss'));
  });

  it('벽 변형: 정면(top) 벽은 tiles["2"] 목록을 섞고, 윗면 벽은 단일', () => {
    const skin = new TileSkin('tiles_stage1', v37, true);
    const open = (_x: number, y: number) => y === 1;
    const tops = new Set<number>();
    for (let x = 0; x < 40; x++) tops.add(skin.indexFor(TileId.Wall, x, 0, open));
    expect([...tops].sort()).toEqual([19, 20, 5]);
    for (let x = 0; x < 10; x++) expect(skin.indexFor(TileId.Wall, x, 2, open)).toBe(6);
    expect(skin.idOf(19)).toBe(TileId.Wall);
    expect(skin.solidIndices).toContain(20);
  });

  it('인덱스 범위는 JSON 값으로만 결정된다 (128×80 재배치: 바닥 23~38, 벽 변형 21~22)', () => {
    const skin = new TileSkin('tiles_stage1', v40, true);
    const s = new Set<number>();
    for (let x = 0; x < 24; x++)
      for (let y = 0; y < 24; y++) s.add(skin.indexFor(TileId.Floor, x, y, undefined, 'boss'));
    expect([...s].sort((a, b) => a - b)).toEqual([35, 36, 37, 38]);
    expect(skin.idOf(38)).toBe(TileId.Floor);
    expect(skin.idOf(22)).toBe(TileId.Wall);
    const open = (_x: number, y: number) => y === 1;
    const tops = new Set<number>();
    for (let x = 0; x < 40; x++) tops.add(skin.indexFor(TileId.Wall, x, 0, open));
    expect([...tops].sort((a, b) => a - b)).toEqual([5, 21, 22]);
  });

  it('소품 maxPerRoom=1 은 방마다 최대 1개, weight 0 은 놓지 않는다', () => {
    const skin = new TileSkin('tiles_stage1', v37, true);
    const list = planProps(layout, skin.props, 'lopad:0');
    expect(list.length).toBeGreaterThan(0);
    for (const room of layout.rooms) {
      const I = room.interior;
      const inRoom = list.filter((p) => p.x >= I.x && p.x < I.x + I.w && p.y >= I.y && p.y < I.y + I.h);
      expect(inRoom.filter((p) => p.index === 13).length).toBeLessThanOrEqual(1);
    }
    expect(list.some((p) => p.index === 15)).toBe(false);
    expect(list.some((p) => p.index === 14)).toBe(true);
  });

  it('TileWorld 와 같은 방식으로 방 종류를 찾아 바닥 인덱스를 나눈다', () => {
    const skin = new TileSkin('tiles_stage1', v37, true);
    const types = roomTypeMap(layout);
    const trial = layout.rooms.find((r) => r.type === 'trial')!;
    const boss = layout.rooms.find((r) => r.type === 'boss')!;
    const tx = trial.interior.x + 1;
    const ty = trial.interior.y + 1;
    const bx = boss.interior.x + 1;
    const by = boss.interior.y + 1;
    expect(types.get(`${tx},${ty}`)).toBe('trial');
    expect([23, 24]).toContain(skin.indexFor(TileId.Floor, tx, ty, undefined, types.get(`${tx},${ty}`)));
    expect([27, 28]).toContain(skin.indexFor(TileId.Floor, bx, by, undefined, types.get(`${bx},${by}`)));
    // 복도 타일은 방 종류가 없다
    const corridor = layout.tiles.findIndex((row) => row.includes(TileId.Corridor));
    const cx = layout.tiles[corridor].indexOf(TileId.Corridor);
    expect(types.get(`${cx},${corridor}`)).toBeUndefined();
  });
});

describe('60라운드 Q9 B안: 64도트 = 1칸 (pixelScale 0.5)', () => {
  it('pixelScale 0.5 시트의 한 칸(64 도트)이 월드 한 칸(TILE)', () => {
    const v3 = { ...stage1, pixelScale: 0.5, tileWidth: 64, tileHeight: 64 } as TilesetJson;
    const skin = new TileSkin('tiles_stage1', v3, true);
    expect(64 * skin.worldScale).toBe(TILE);
    // pixelScale 이 없으면 칸 크기로 (64px 칸 = 0.25)
    const noPs = new TileSkin('tiles_stage1', { ...stage1, tileWidth: 64 } as TilesetJson, true);
    expect(64 * noPs.worldScale).toBe(TILE);
  });
});
