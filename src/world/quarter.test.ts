import { describe, expect, it } from 'vitest';
import { TileId } from '../systems/mapgen';
import { TileSkin, quarterWallsOf, type TilesetJson } from './tileskin';

const tiles = { '0': [7], '1': [0, 1, 2, 3], '2': [5, 21, 22], '6': [4], '7': [11], '8': [12] };

describe('쿼터뷰 벽 타일셋 (50라운드 계약 art §9)', () => {
  it('wallHeightTiles 가 없으면 기존 평면 벽 (null)', () => {
    expect(quarterWallsOf({ image: 'a.png', tiles })).toBeNull();
  });

  it('walls.front·frontUpper·top + 앞면 변형(tiles["2"] 첫 항목이 앞면이면 그 목록)', () => {
    const q = quarterWallsOf({
      image: 'a.png',
      tiles,
      wallHeightTiles: 2,
      walls: { front: 5, frontUpper: 39, top: 6 },
    });
    expect(q).toMatchObject({ heightTiles: 2, frontLower: [5, 21, 22], frontUpper: [39], top: 6, topAboveFront: 6 });
  });

  it('윗단 표기 변형: walls.front 배열 [아랫단, 윗단] · wallFrontUpper · 없으면 아랫단', () => {
    expect(quarterWallsOf({ image: '', tiles, wallHeightTiles: 2, walls: { front: [5, 40] } })?.frontUpper).toEqual([
      40,
    ]);
    expect(quarterWallsOf({ image: '', tiles, wallHeightTiles: 2, wallFrontUpper: 41 })?.frontUpper).toEqual([41]);
    const q = quarterWallsOf({ image: '', tiles: { '2': [9] }, wallHeightTiles: 2 })!;
    expect(q.frontLower).toEqual([5]);
    expect(q.frontUpper).toEqual([5]);
    expect(q.top).toBe(6);
  });

  it('아트 v2 표기: front { lower, upper } 가중치 목록 · 처마 · 경계 가장자리 · 바닥 그늘', () => {
    const def = {
      image: '',
      tiles,
      wallHeightTiles: 2,
      walls: {
        front: { lower: [5, 5, 21], upper: [40, 41, 42] },
        wallFrontUpper: 40,
        top: 6,
        topAboveFront: 47,
        left: 48,
        right: 49,
        bottom: 50,
        corner_bl: 51,
        corner_br: 52,
        stoneSet: { lower: [43] },
      },
      floorShadows: { n: 53, w: 54, e: 55, nw: 56, ne: 57 },
    } as unknown as TilesetJson;
    const q = quarterWallsOf(def)!;
    expect(q.frontLower).toEqual([5, 5, 21]);
    expect(q.frontUpper).toEqual([40, 41, 42]);
    expect(q.topAboveFront).toBe(47);
    expect(q.edges).toEqual({ left: 48, right: 49, bottom: 50, corner_bl: 51, corner_br: 52 });
    expect(q.shadows).toEqual({ n: 53, w: 54, e: 55, nw: 56, ne: 57 });
    expect(q.stone).toEqual({ lower: [43], upper: [43], top: 6 });
    const skin = new TileSkin('k', def, true);
    for (const i of [40, 41, 42, 47, 48, 52]) expect(skin.idOf(i)).toBe(TileId.Wall);
  });

  it('v2 타일셋 바닥: 방 종류 바닥은 가끔만, 나머지는 판석 tiles["1"]', () => {
    const def = {
      image: '',
      tiles,
      wallHeightTiles: 2,
      roomFloors: { trial: [27, 28, 29, 30] },
    } as unknown as TilesetJson;
    const skin = new TileSkin('k', def, true);
    let room = 0;
    for (let y = 0; y < 40; y++)
      for (let x = 0; x < 40; x++) if (skin.indexFor(TileId.Floor, x, y, undefined, 'trial') >= 27) room++;
    expect(room / 1600).toBeGreaterThan(0.02);
    expect(room / 1600).toBeLessThan(0.25);
    // 기존 타일셋은 방 종류 바닥 그대로
    const old = new TileSkin(
      'k',
      { image: '', tiles, roomFloors: { trial: [27, 28] } } as unknown as TilesetJson,
      true,
    );
    expect(old.indexFor(TileId.Floor, 3, 4, undefined, 'trial')).toBeGreaterThanOrEqual(27);
  });

  it('TileSkin: 쿼터뷰 인덱스(윗단·윗면)는 벽(충돌)으로, 타일 크기 32', () => {
    const def: TilesetJson = {
      image: 'a.png',
      tileWidth: 32,
      pixelScale: 1,
      wallHeightTiles: 2,
      tiles,
      walls: { front: 5, frontUpper: 39, top: 6 },
    };
    const skin = new TileSkin('k', def, true);
    expect(skin.quarter?.heightTiles).toBe(2);
    expect(skin.tilePx).toBe(32);
    expect(skin.idOf(39)).toBe(TileId.Wall);
    expect(skin.idOf(6)).toBe(TileId.Wall);
    expect(skin.solidIndices).toEqual(expect.arrayContaining([5, 6, 21, 22, 39]));
    expect(skin.voidIndex).toBe(7);
  });

  it('기존 타일셋(walls 에 배열·메모 문자열 섞임)도 그대로 읽는다', () => {
    const def = {
      image: 'a.png',
      tiles,
      walls: { top: 5, bottom: 6, variants: [5, 21, 22], note: 'memo' },
    } as unknown as TilesetJson;
    const skin = new TileSkin('k', def, true);
    expect(skin.quarter).toBeNull();
    expect(skin.tilePx).toBe(16);
    expect(skin.idOf(6)).toBe(TileId.Wall);
  });
});
