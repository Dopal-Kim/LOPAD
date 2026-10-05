import { describe, expect, it } from 'vitest';
import { ROUTE, entries } from '../route';
import { arenaVariety, pickPropScene, pickSetPiece } from '../routeArena';
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

  it('전투 노드 세트: 같은 길의 이웃 단은 다른 후보, 크기·뒤집기도 노드마다 바뀐다', () => {
    const list = ROUTE.kinds.battle.setPieceVariants!;
    expect(list.length).toBeGreaterThanOrEqual(4);
    for (const id of list) expect(entries(ROUTE.setPieces)[id], id).toBeDefined();
    for (const seed of ['a', 'b', 'c']) {
      for (const r1 of [0, 1])
        for (const r2 of [0, 1]) {
          const a = pickSetPiece({ kind: 'battle', col: 3, row: r1 }, null, seed);
          const b = pickSetPiece({ kind: 'battle', col: 4, row: r2 }, null, seed);
          expect(a).not.toBe(b);
        }
      const looks = new Set(
        [3, 4, 5].flatMap((col) =>
          [0, 1].map((row) => {
            const v = arenaVariety({ id: `c${col}r${row}`, kind: 'battle', col, row }, seed);
            return `${pickSetPiece({ kind: 'battle', col, row }, null, seed)}|${v.size}|${v.mirror.x}${v.mirror.y}`;
          }),
        ),
      );
      expect(looks.size).toBe(6);
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
