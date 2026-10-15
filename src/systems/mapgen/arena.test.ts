import { describe, expect, it } from 'vitest';
import { floorConnected, generateArena, type ArenaSpec } from './arena';
import { TileId } from './types';
import { edgeVoidTiles } from '../../world/tileskin';

const spec = (seed: number, extra: Partial<ArenaSpec> = {}): ArenaSpec => ({
  roomId: 'n',
  type: 'trial',
  floor: 'trial',
  w: 40,
  h: 24,
  margin: 8,
  spawnInset: 3,
  exitInset: 3,
  seed,
  ...extra,
});

describe('48라운드 사각 전투장 (형태 틀이 아닌 노드)', () => {
  it('바닥은 모두 이어져 있고 시작점·출구·중앙은 바닥 · 사각 벽 · 빈 틈 없음', () => {
    for (const extra of [
      {},
      { spawnCenter: true },
      { spawnExactCenter: true },
      { shopCenter: true },
      { spawnShiftY: 3 },
    ]) {
      const L = generateArena(spec(1, extra));
      const A = L.arena!;
      const I = L.rooms[0].interior;
      expect(floorConnected(L.tiles)).toBe(true);
      expect(L.tiles[A.spawn.y][A.spawn.x]).toBe(TileId.Floor);
      for (let y = A.exit.y; y < A.exit.y + 2; y++)
        for (let x = A.exit.x; x < A.exit.x + 2; x++) expect(L.tiles[y][x]).toBe(TileId.Floor);
      expect(L.tiles[A.center!.y][A.center!.x]).toBe(TileId.Floor);
      for (let x = I.x - 1; x <= I.x + I.w; x++) {
        expect(L.tiles[I.y - 1][x]).toBe(TileId.Wall);
        expect(L.tiles[I.y + I.h][x]).toBe(TileId.Wall);
      }
      expect(edgeVoidTiles(L)).toEqual([]);
      expect(A.shape).toBeUndefined();
    }
  });

  it('탄생지: 시작점 = 정확히 중앙 (혼불이 모이는 자리) · 상점 중앙 배치', () => {
    const L = generateArena(spec(1, { spawnExactCenter: true, shopCenter: true }));
    const A = L.arena!;
    expect(A.spawn).toEqual(A.center);
    expect(A.shop).toEqual({ x: A.center!.x - 1, y: A.center!.y - 1 });
    // 48라운드 spawnCenter(무기 시험장 등)는 그대로 중앙 왼쪽 4칸
    const B = generateArena(spec(1, { spawnCenter: true })).arena!;
    expect(B.spawn).toEqual({ x: B.center!.x - 4, y: B.center!.y });
  });

  it('셀(80×48)보다 큰 전투장도 모든 칸이 방 판정(cellRoom)에 든다', () => {
    const L = generateArena(spec(1, { w: 66, h: 40 }));
    for (let cy = 0; cy * 48 < L.heightTiles; cy++)
      for (let cx = 0; cx * 80 < L.widthTiles; cx++) expect(L.cellRoom.get(`${cx},${cy}`)).toBe('n');
  });
});
