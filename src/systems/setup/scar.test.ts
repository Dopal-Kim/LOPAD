import { describe, expect, it } from 'vitest';
import { SCAR, encodeScar, sanitizeScar, simplify } from './scar';

const rect = { x: 100, y: 50, w: 400, h: 200 };

describe('상흔 저장 형식 (53라운드 Q4 준비)', () => {
  it('기준 사각형으로 정규화, 밖은 0~1 로 잘라 붙임, 2점 미만 획은 버림', () => {
    const d = encodeScar(
      [
        [
          { x: 100, y: 50 },
          { x: 300, y: 150 },
          { x: 600, y: 300 },
        ],
        [{ x: 1, y: 1 }],
      ],
      rect,
    );
    expect(d.v).toBe(1);
    expect(d.aspect).toBe(2);
    expect(d.strokes).toHaveLength(1);
    expect(d.strokes[0]).toEqual([0, 0, 1, 1]); // 가운데 점은 직선 위라 줄여짐, 끝은 잘림
  });
  it('직선 위 점은 줄이고 꺾인 점은 남긴다', () => {
    const pts = [
      { x: 0, y: 0 },
      { x: 5, y: 0.1 },
      { x: 10, y: 0 },
      { x: 10, y: 10 },
    ];
    expect(simplify(pts, 0.5)).toEqual([pts[0], pts[2], pts[3]]);
  });
  it('점이 많으면 MAX_POINTS 로 다시 찍는다', () => {
    const wave = Array.from({ length: 400 }, (_, i) => ({ x: 100 + i, y: 150 + 40 * Math.sin(i / 6) }));
    const d = encodeScar([wave], rect);
    expect(d.strokes[0].length).toBe(SCAR.MAX_POINTS * 2);
  });
  it('세이브 값 검사: 틀린 형식은 null, 범위 밖 획은 버림', () => {
    expect(sanitizeScar(null)).toBeNull();
    expect(sanitizeScar({ v: 2, aspect: 1, strokes: [] })).toBeNull();
    const ok = sanitizeScar({ v: 1, aspect: 1.1, strokes: [[0, 0, 1, 1], [0, 2, 1, 1], [0.5]] });
    expect(ok?.strokes).toEqual([[0, 0, 1, 1]]);
  });
});

describe('상흔 런 상태 (GameState·세이브)', () => {
  it('Setup 이 맡긴 상흔은 새 런에 들어가고, 세이브·이어하기에 유지, 다음 새 런은 비운다', async () => {
    const { gameState } = await import('../../core/GameState');
    const scar = encodeScar(
      [
        [
          { x: 300, y: 100 },
          { x: 350, y: 200 },
          { x: 300, y: 240 },
        ],
      ],
      rect,
    );
    gameState.queueScar(scar);
    gameState.startRun('scar-a', 'katana');
    expect(gameState.scar).toEqual(scar);
    const save = JSON.parse(JSON.stringify(gameState.toSave()));
    expect(save.scar).toEqual(scar);
    gameState.startRun('scar-b', 'katana');
    expect(gameState.scar).toBeNull();
    gameState.applySave(save);
    expect(gameState.scar).toEqual(scar);
    gameState.applySave({ ...save, scar: undefined });
    expect(gameState.scar).toBeNull();
  });
});
