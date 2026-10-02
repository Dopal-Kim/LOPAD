import { describe, expect, it } from 'vitest';
import { floorConnected, generateArena, insetProfile, type ArenaEdge, type ArenaSpec } from './arena';
import { TileId } from './types';
import { Rng } from '../rng';
import { edgeVoidTiles } from '../../world/tileskin';

const EDGE: ArenaEdge = {
  maxInset: 4,
  run: [2, 5],
  gaps: [2, 3],
  gapWidth: [2, 4],
  cornerMarginTiles: 3,
  keepClearTiles: 2,
};

const spec = (seed: number, extra: Partial<ArenaSpec> = {}): ArenaSpec => ({
  roomId: 'n',
  type: 'trial',
  floor: 'trial',
  w: 40,
  h: 24,
  margin: 8,
  spawnInset: 3,
  exitInset: 3,
  edge: EDGE,
  seed,
  ...extra,
});

describe('49라운드 들쭉날쭉한 전투장 가장자리 (실내 느낌 제거)', () => {
  it('같은 시드면 같은 모양, 다른 시드면 대개 다른 모양 (결정성)', () => {
    expect(generateArena(spec(7)).tiles).toEqual(generateArena(spec(7)).tiles);
    const shapes = new Set<string>();
    for (let s = 0; s < 10; s++) shapes.add(JSON.stringify(generateArena(spec(s)).tiles));
    expect(shapes.size).toBeGreaterThan(5);
  });

  it('사각형이 아니다: 내부 사각형 테두리 일부가 깎여 담·잔해가 된다', () => {
    for (let s = 0; s < 20; s++) {
      const L = generateArena(spec(s));
      const I = L.rooms[0].interior;
      let cut = 0;
      for (let x = I.x; x < I.x + I.w; x++) {
        if (L.tiles[I.y][x] !== TileId.Floor) cut++;
        if (L.tiles[I.y + I.h - 1][x] !== TileId.Floor) cut++;
      }
      expect(cut).toBeGreaterThan(0);
      // 내부 사각형 바깥에는 바닥이 없다 (방 판정·카메라 그대로)
      for (let y = 0; y < L.heightTiles; y++)
        for (let x = 0; x < L.widthTiles; x++)
          if (L.tiles[y][x] === TileId.Floor) expect(x >= I.x && x < I.x + I.w && y >= I.y && y < I.y + I.h).toBe(true);
    }
  });

  it('바닥은 모두 이어져 있고 시작점·출구·중앙은 바닥', () => {
    for (let s = 0; s < 40; s++) {
      for (const extra of [{}, { spawnCenter: true }, { spawnExactCenter: true }, { shopCenter: true }]) {
        const L = generateArena(spec(s, extra));
        const A = L.arena!;
        expect(floorConnected(L.tiles)).toBe(true);
        expect(L.tiles[A.spawn.y][A.spawn.x]).toBe(TileId.Floor);
        for (let y = A.exit.y; y < A.exit.y + 2; y++)
          for (let x = A.exit.x; x < A.exit.x + 2; x++) expect(L.tiles[y][x]).toBe(TileId.Floor);
        expect(L.tiles[A.center!.y][A.center!.x]).toBe(TileId.Floor);
      }
    }
  });

  it('바닥은 벽 또는 열린 틈(void)으로만 둘러싸이고, 열린 틈은 위·아래에 생긴다', () => {
    let gapsSeen = 0;
    for (let s = 0; s < 20; s++) {
      const L = generateArena(spec(s));
      const I = L.rooms[0].interior;
      const voids = edgeVoidTiles(L);
      gapsSeen += voids.length;
      // 틈은 내부 사각형의 가로 범위 안 (위·아래 변)
      for (const v of voids) expect(v.x >= I.x && v.x < I.x + I.w).toBe(true);
    }
    expect(gapsSeen).toBeGreaterThan(0);
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

  it('edge 가 없으면 48라운드 사각 벽 그대로', () => {
    const L = generateArena(spec(3, { edge: undefined }));
    const I = L.rooms[0].interior;
    for (let x = I.x - 1; x <= I.x + I.w; x++) {
      expect(L.tiles[I.y - 1][x]).toBe(TileId.Wall);
      expect(L.tiles[I.y + I.h][x]).toBe(TileId.Wall);
    }
    expect(edgeVoidTiles(L)).toEqual([]);
  });

  it('깊이 프로필은 0..max 안에서 계단식', () => {
    const p = insetProfile(new Rng(5), 40, 3, [2, 5]);
    expect(p).toHaveLength(40);
    expect(p.every((d) => d >= 0 && d <= 3)).toBe(true);
  });
});
