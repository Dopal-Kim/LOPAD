import { describe, expect, it } from 'vitest';
import { plateMidW, platePos, readPlateJson, slice3 } from './eliteView';
import { interactWords } from './structView';
import { STRUCT_KIND_TEXT } from './textBuild';

// 아트 elite_nameplate.json 프레임 '0' (트림: 원 192×30 안 (1,3) 190×26)
const json = {
  nineSlice: { leftWidth: 26, rightWidth: 26 },
  textCenterY: 15,
  minWidth: 68,
  pivot: { x: 96, y: 28 },
  frames: {
    '0': {
      frame: { x: 0, y: 0, w: 190, h: 26 },
      spriteSourceSize: { x: 1, y: 3, w: 190, h: 26 },
      sourceSize: { w: 192, h: 30 },
    },
  },
};

describe('eliteView (60라운드 §14.9 엘리트 이름표)', () => {
  it('트림 프레임을 가로 3조각으로 (원 프레임 좌표 → 텍스처 사각형)', () => {
    const m = readPlateJson(json)!;
    expect(m).toMatchObject({ leftW: 26, rightW: 26, textCenterY: 15, minWidth: 68, pivotY: 28 });
    const s = slice3(m.frame, m.leftW, m.rightW);
    expect(s.left).toEqual({ tx: 0, ty: 0, w: 25, h: 26, dx: 1, dy: 3 });
    expect(s.mid).toEqual({ tx: 25, ty: 0, w: 140, h: 26, dx: 0, dy: 3 });
    expect(s.right).toEqual({ tx: 165, ty: 0, w: 25, h: 26, dx: 0, dy: 3 });
    expect([s.leftW, s.midW, s.rightW]).toEqual([26, 140, 26]);
    expect(readPlateJson(null)).toBeNull();
    expect(readPlateJson({ frames: {} })).toBeNull();
  });

  it('가운데 폭 = 글자 폭(도트) + 여백, 최소 폭 아래로는 줄지 않는다', () => {
    const caps = { leftW: 26, rightW: 26 };
    expect(plateMidW(40, 0.5, 6, caps, 68)).toBe(92);
    expect(plateMidW(2, 0.5, 6, caps, 68)).toBe(16);
  });

  it('머리 위 점에서 위로, 화면 안으로', () => {
    expect(platePos(480, 200, 96, 14, 37, 960, 540, 4)).toEqual({ x: 432, y: 149 });
    expect(platePos(10, 20, 96, 14, 37, 960, 540, 4)).toEqual({ x: 4, y: 4 });
    expect(platePos(950, 300, 96, 14, 37, 960, 540, 4).x).toBe(960 - 4 - 96);
  });

  it('E 안내: 시스템 문구 우선, 비면 종류별 기본 (새 kind 는 문자열로)', () => {
    expect(interactWords({ kind: 'warFlag', name: '', action: '' }, STRUCT_KIND_TEXT)).toEqual({
      name: '전장 깃발',
      action: '깃발을 세운다',
    });
    expect(interactWords({ kind: 'clue', name: '금 간 술독', action: '' }, STRUCT_KIND_TEXT)).toEqual({
      name: '금 간 술독',
      action: '살펴본다',
    });
    expect(interactWords({ kind: 'mapSeller', name: '', action: '지도를 산다' }, STRUCT_KIND_TEXT).action).toBe(
      '지도를 산다',
    );
    expect(interactWords({ kind: 'chest', name: '', action: '' }, STRUCT_KIND_TEXT)).toEqual({ name: '', action: '' });
  });
});
