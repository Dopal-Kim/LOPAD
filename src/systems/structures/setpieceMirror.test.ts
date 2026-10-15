import { describe, expect, it } from 'vitest';
import { ROUTE, entries, generateRoute } from '../route';
import { arenaVariety, pickPropScene, planNodeArena } from '../routeArena';
import { inPropScene } from '../../world/tileskin';
import { mirrorSetPiece } from './setpieceMirror';
import type { SetPieceDef } from './setpiece';

describe('61라운드 단계 2 방 다양화', () => {
  const t: SetPieceDef = {
    slots: [{ kinds: ['still'], at: [3, 1], ring: 4, angle: 30 }],
    decor: [{ name: 'a', at: [-5, -2] }],
    cover: {
      count: [1, 1],
      anchors: [[-7, 4]],
      shapes: [
        [
          [0, 0],
          [1, 0],
        ],
      ],
    },
    pillars: [{ at: [-7, -5], size: [2, 2] }],
    candles: [[0, -8]],
  };

  it('뒤집기 없으면 원본 그대로', () => {
    expect(mirrorSetPiece(t, { x: false, y: false })).toBe(t);
  });

  it('좌우 뒤집기: dx → −dx, 각도 180−a, 모양 칸 · 기둥은 크기만큼 보정', () => {
    const m = mirrorSetPiece(t, { x: true, y: false });
    expect(m.slots![0].at).toEqual([-3, 1]);
    expect(m.slots![0].angle).toBe(150);
    expect(m.decor![0].at).toEqual([5, -2]);
    expect(m.cover!.anchors[0]).toEqual([7, 4]);
    expect(m.cover!.shapes[0]).toEqual([
      [-0, 0],
      [-1, 0],
    ]);
    expect(m.pillars![0].at).toEqual([6, -5]);
    expect(m.candles![0]).toEqual([-0, -8]);
  });

  it('상하 뒤집기: dy → −dy, 각도 −a', () => {
    const m = mirrorSetPiece(t, { x: false, y: true });
    expect(m.slots![0].at).toEqual([3, -1]);
    expect(m.slots![0].angle).toBe(330);
    expect(m.pillars![0].at).toEqual([-7, 4]);
  });

  it('P19 S2 전투 노드 = 형태 틀 변형: 노드마다 형태·크기·뒤집기가 바뀌고, 형태 소품 세트는 setPieces 에 있다', () => {
    for (const seed of ['a', 'b', 'c']) {
      const nodes = generateRoute('stage1', seed).nodes.filter((n) => n.kind === 'battle');
      const looks = new Set(
        nodes.map((n) => {
          const p = planNodeArena(n, 'stage1', seed);
          for (const id of [p.setPiece.template].filter(Boolean)) expect(entries(ROUTE.setPieces)[id!]).toBeDefined();
          return `${p.shape!.id}|${p.variety.size}|${p.variety.mirror.x}${p.variety.mirror.y}`;
        }),
      );
      expect(looks.size).toBe(nodes.length);
    }
  });

  it('보스·탄생(튜토리얼)은 고정 크기·뒤집기 없음', () => {
    const boss = arenaVariety({ id: 'c7r0', kind: 'boss', col: 7, row: 0 }, 's');
    expect(boss).toEqual({ size: ROUTE.arena.boss, shift: 0, mirror: { x: false, y: false } });
    const birth = arenaVariety({ id: 'c0r0', kind: 'birth', col: 0, row: 0 }, 's');
    expect(birth.shift).toBe(0);
    expect(birth.mirror).toEqual({ x: false, y: false });
  });

  it('art §24 방 변주 장면: 장면 없는 소품은 늘, 장면 소품은 고른 장면만 · 이웃 단은 다른 장면 · 보스는 없음', () => {
    const list = [{ name: 'a' }, { name: 'b', variantTag: 'outer_wreck' }, { name: 'c', variantTag: 'outer_backyard' }];
    expect(inPropScene(list, 'outer_wreck').map((p) => p.name)).toEqual(['a', 'b']);
    expect(inPropScene(list, null).map((p) => p.name)).toEqual(['a']);
    const tags = ['outer_backyard', 'outer_wreck'];
    for (const seed of ['a', 'b'])
      for (const r of [0, 1]) {
        const x = pickPropScene(tags, { id: 'x', kind: 'battle', col: 3, row: r }, seed);
        const y = pickPropScene(tags, { id: 'y', kind: 'battle', col: 4, row: r }, seed);
        expect(x).not.toBe(y);
      }
    expect(pickPropScene(tags, { id: 'b', kind: 'boss', col: 7, row: 0 }, 's')).toBeNull();
  });
});
