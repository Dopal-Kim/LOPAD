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
    expect(q).toEqual({ heightTiles: 2, frontLower: [5, 21, 22], frontUpper: 39, top: 6 });
  });

  it('윗단 표기 변형: walls.front 배열 [아랫단, 윗단] · wallFrontUpper · 없으면 아랫단', () => {
    expect(quarterWallsOf({ image: '', tiles, wallHeightTiles: 2, walls: { front: [5, 40] } })?.frontUpper).toBe(40);
    expect(quarterWallsOf({ image: '', tiles, wallHeightTiles: 2, wallFrontUpper: 41 })?.frontUpper).toBe(41);
    const q = quarterWallsOf({ image: '', tiles: { '2': [9] }, wallHeightTiles: 2 })!;
    expect(q.frontLower).toEqual([5]);
    expect(q.frontUpper).toBe(5);
    expect(q.top).toBe(6);
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
