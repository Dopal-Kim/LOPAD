import { describe, expect, it } from 'vitest';
import { ARENA_SHAPES } from '../../data/arenas';
import { generateArena } from '../mapgen/arena';
import { buildShape } from '../mapgen/shape';
import { TileId } from '../mapgen/types';
import { alongDoor, arenaDoors, entryWalk, inThreshold, pastMouth, planDoor } from './doorPlan';

const T = 16;
const arena = (seed: number, o: { shift?: number; center?: boolean } = {}) =>
  generateArena({
    roomId: 'n',
    type: 'trial',
    floor: 'trial',
    w: 32,
    h: 20,
    margin: 8,
    spawnInset: 3,
    exitInset: 3,
    spawnShiftY: o.shift ?? 0,
    spawnExactCenter: o.center,
    seed,
  });

describe('62 루프 2 E 문 나가기 — 문 자리', () => {
  it('출구 문 = 동쪽 벽, 출구 2×2 아래 줄이 가운데 (3칸) · 입구 문 = 서쪽 벽, 시작 줄이 가운데', () => {
    const L = arena(7);
    const A = L.arena!;
    const I = L.rooms[0].interior;
    const d = arenaDoors(L, T, 3, true);
    expect(d.exit?.side).toBe('east');
    expect(d.entry?.side).toBe('west');
    expect(d.exit!.threshold).toEqual({ x: I.x + I.w - 1, y: A.exit.y, w: 1, h: 3 });
    expect(d.entry!.threshold).toEqual({ x: I.x, y: A.spawn.y - 1, w: 1, h: 3 });
    // 문 칸 = 벽 열 3칸
    expect(d.exit!.cells).toEqual([0, 1, 2].map((i) => ({ x: I.x + I.w, y: A.exit.y + i })));
    expect(d.exit!.mouth).toEqual({ x: (I.x + I.w) * T, y: (A.exit.y + 1.5) * T });
    expect(d.entry!.mouth).toEqual({ x: I.x * T, y: (A.spawn.y + 0.5) * T });
  });

  it('P19 형태 틀 전장(모든 형태 · 뒤집기 · 배율)도 문 칸 = 벽, 문 줄 바닥이 벽까지 곧게', () => {
    for (const def of ARENA_SHAPES.values())
      for (const [flipX, flipY, scale] of [
        [false, false, 1],
        [true, true, def.variants.scale[0]],
        [true, false, def.variants.scale[1]],
      ] as const) {
        const L = generateArena({
          roomId: 'n',
          type: 'trial',
          floor: 'trial',
          w: 0,
          h: 0,
          margin: 8,
          spawnInset: 3,
          exitInset: 3,
          shape: buildShape(def, { flipX, flipY, scale }),
        });
        const I = L.rooms[0].interior;
        const d = arenaDoors(L, T, 3, true);
        expect(d.exit).not.toBeNull();
        expect(d.entry).not.toBeNull();
        for (const spot of [d.exit!, d.entry!]) {
          expect(spot.threshold.w).toBe(1);
          for (const c of spot.cells) expect(L.tiles[c.y][c.x]).toBe(TileId.Wall);
        }
        // 바닥이 벽까지 곧게
        for (let y = d.exit!.threshold.y; y < d.exit!.threshold.y + 3; y++)
          expect(L.tiles[y][I.x + I.w - 1]).toBe(TileId.Floor);
      }
  });

  it('탄생 전장(가운데 시작)은 입구 문이 없다', () => {
    const L = arena(3, { center: true });
    const d = arenaDoors(L, T, 3, false);
    expect(d.entry).toBeNull();
    expect(d.exit?.side).toBe('east');
  });

  it('문턱 판정: 벽 안쪽 1칸 띠만 (그 앞 칸·문 칸은 아님)', () => {
    const L = arena(11);
    const spot = arenaDoors(L, T, 3, true).exit!;
    const t = spot.threshold;
    expect(inThreshold(spot, (t.x + 0.5) * T, (t.y + 1.5) * T, T)).toBe(true);
    expect(inThreshold(spot, (t.x - 0.5) * T, (t.y + 1.5) * T, T)).toBe(false);
    expect(inThreshold(spot, (t.x + 1.5) * T, (t.y + 1.5) * T, T)).toBe(false);
    expect(inThreshold(spot, (t.x + 0.5) * T, (t.y + 3.5) * T, T)).toBe(false);
  });

  it('문 따라 거리 · 바닥 끝에서 나간 거리', () => {
    const L = arena(5);
    const spot = arenaDoors(L, T, 3, true).exit!;
    const p = alongDoor(spot, 40);
    expect(p).toEqual({ x: spot.mouth.x + 40, y: spot.mouth.y });
    expect(pastMouth(spot, p.x, p.y)).toBe(40);
    expect(pastMouth(spot, spot.sill.x, spot.sill.y)).toBe(-T / 2);
  });

  it('들어오는 걸음: 시작점은 늘 문 안(바닥 끝 바깥), 목표는 가까운 시작점 · 먼 시작점이면 문 앞', () => {
    const L = arena(9);
    const A = L.arena!;
    const spot = arenaDoors(L, T, 3, true).entry!;
    const spawn = { x: (A.spawn.x + 0.5) * T, y: (A.spawn.y + 0.5) * T };
    const near = entryWalk(spot, spawn, { walkDist: 57.6, maxSpawnDist: 72, stopDist: 41.6, minOut: 12 });
    expect(near.to).toEqual(spawn);
    expect(pastMouth(spot, near.from.x, near.from.y)).toBeGreaterThanOrEqual(12);
    expect(near.from.y).toBe(spawn.y);
    const far = entryWalk(
      spot,
      { x: spawn.x + 200, y: spawn.y },
      { walkDist: 57.6, maxSpawnDist: 72, stopDist: 41.6, minOut: 12 },
    );
    expect(-pastMouth(spot, far.to.x, far.to.y)).toBeCloseTo(41.6);
    expect(pastMouth(spot, far.from.x, far.from.y)).toBeGreaterThanOrEqual(12);
  });

  it('북·남 문도 같은 규칙 (방향만 바뀜)', () => {
    const L = arena(2);
    const I = L.rooms[0].interior;
    const n = planDoor(L, 'north', I.x + 10, 3, T)!;
    expect(n.threshold).toEqual({ x: I.x + 9, y: I.y, w: 3, h: 1 });
    expect(n.out).toEqual({ x: 0, y: -1 });
    expect(n.mouth.y).toBe(I.y * T);
    expect(n.cells.every((c) => c.y === I.y - 1)).toBe(true);
  });
});
