import { describe, expect, it } from 'vitest';
import { ARENA_SHAPES } from '../data/arenas';
import { generateArena } from '../systems/mapgen/arena';
import { buildShape } from '../systems/mapgen/shape';
import { TileId } from '../systems/mapgen';
import { dropFillIndex, floorMacroIndex, groundV4, planTerrainOverlay, terrainCellsOf, terrainV4Of } from './terrainV4';

const seq = (a: number, n: number) => Array.from({ length: n }, (_, i) => a + i);
const V4 = {
  floor: { macro: seq(96, 64) },
  drop: {
    fill: seq(408, 16),
    fillRule: { kind: 'water', frames: 4, frameMs: 170 },
    banks: seq(424, 16),
    innerCorners: { nw: 440, ne: 441, sw: 442, se: 443 },
    bridge: { h: 450, hEndW: 451, hEndE: 452, v: 453, vEndN: 454, vEndS: 455 },
  },
  terrace: {
    lip: seq(456, 16),
    face: { mid: 472, endL: 473, endR: 474, single: 475 },
    stairS: { mid: 476, endL: 477, endR: 478, single: 479 },
  },
};

const layoutOf = (id: string) =>
  generateArena({
    roomId: 'n',
    type: 'trial',
    floor: 'trial',
    w: 0,
    h: 0,
    margin: 2,
    spawnInset: 3,
    exitInset: 3,
    shape: buildShape(ARENA_SHAPES.get(id)!, { scale: 1, flipX: false, flipY: false }),
  });

describe('P19 1-A 타일셋 v4 지형 (art §34)', () => {
  const v = terrainV4Of({ v4: V4 })!;

  it('표가 모자라면 null · 바닥 매크로는 칸 위치 규칙 (8칸 주기) · 물은 2×2×프레임, 낭떠러지는 4×4', () => {
    expect(terrainV4Of({})).toBeNull();
    expect(terrainV4Of({ v4: { ...V4, floor: { macro: [1] } } })).toBeNull();
    expect(floorMacroIndex(v, 3, 2)).toBe(96 + 2 * 8 + 3);
    expect(floorMacroIndex(v, 11, 10)).toBe(floorMacroIndex(v, 3, 2));
    expect(dropFillIndex(v, 1, 1, 2)).toBe(408 + 2 * 4 + 3);
    const chasm = terrainV4Of({ v4: { ...V4, drop: { ...V4.drop, fillRule: { kind: 'chasm' } } } })!;
    expect(dropFillIndex(chasm, 5, 6)).toBe(408 + 2 * 4 + 1);
  });

  it('부두: 물 칸 둑·다리(남북으로 건너는 다리 = 세로) · 바닥 = 매크로', () => {
    const L = layoutOf('dock_quay');
    const c = terrainCellsOf(L);
    const over = planTerrainOverlay(v, c, L);
    const at = new Map(over.map((o) => [`${o.x},${o.y}`, o.index]));
    const b = L.arena!.bridges![0];
    expect([453, 454, 455]).toContain(at.get(`${b.x},${b.y}`));
    // 수로 북쪽 줄 물 칸(다리 옆이 아닌)은 북쪽이 땅 → 둑 N 비트
    const d = L.arena!.drops!.find(
      (p) =>
        p.kind === 'water' &&
        L.tiles[p.y - 1][p.x] === TileId.Floor &&
        !c.bridge.has(`${p.x - 1},${p.y}`) &&
        !c.bridge.has(`${p.x + 1},${p.y}`) &&
        L.tiles[p.y][p.x - 1] === TileId.Void &&
        L.tiles[p.y][p.x + 1] === TileId.Void,
    )!;
    expect(at.get(`${d.x},${d.y}`)).toBe(424 + 1);
    const f = L.arena!.spawn;
    expect(groundV4(v, c, TileId.Floor, f.x, f.y, 0)).toBe(floorMacroIndex(v, f.x, f.y));
  });

  it('테라스: 단 끝 칸 = 앞면(가운데·끝) · 위 단 남쪽 테 · 계단 앞 = 계단 그림', () => {
    const L = layoutOf('terrace');
    const c = terrainCellsOf(L);
    const at = new Map(planTerrainOverlay(v, c, L).map((o) => [`${o.x},${o.y}`, o.index]));
    const ledge = [...c.ledge].map((k) => k.split(',').map(Number));
    expect(ledge.length).toBeGreaterThan(0);
    for (const [x, y] of ledge) expect([472, 473, 474, 475]).toContain(at.get(`${x},${y}`));
    const [lx, ly] = ledge.find(([x, y]) => c.high.has(`${x},${y - 1}`) && !c.stairs.has(`${x},${y - 1}`))!;
    expect(((at.get(`${lx},${ly - 1}`) ?? 0) - 456) & 4).toBe(4);
    expect([...c.stairs].some((k) => [476, 477, 478, 479].includes(at.get(k) ?? -1))).toBe(true);
    // 단 끝 칸 바닥은 아래 단 바닥 매크로 (검은 빈 칸 아님)
    expect(groundV4(v, c, TileId.Void, lx, ly, 0)).toBe(floorMacroIndex(v, lx, ly));
  });
});
