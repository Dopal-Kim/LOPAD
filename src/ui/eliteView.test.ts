import { describe, expect, it } from 'vitest';
import { plateMidW, platePos, plateTextCenter, readPlateJson, slice3 } from './eliteView';
import { interactWords } from './structView';
import { STRUCT_KIND_TEXT } from './textBuild';

// 아트 elite_nameplate.json 프레임 '0' — 60 Q36 글자 칸 24도트 판 (트림: 원 192×40 안 (1,3) 190×36)
const json = {
  nineSlice: { leftWidth: 26, rightWidth: 26 },
  textArea: { x: 26, y: 7, w: 140, h: 24 },
  textCenterY: 19,
  textBand: { y: 5, h: 29 },
  minWidth: 68,
  pivot: { x: 96, y: 38 },
  frames: {
    '0': {
      frame: { x: 0, y: 0, w: 190, h: 36 },
      spriteSourceSize: { x: 1, y: 3, w: 190, h: 36 },
      sourceSize: { w: 192, h: 40 },
    },
  },
};

describe('eliteView (60라운드 §14.9 엘리트 이름표)', () => {
  it('트림 프레임을 가로 3조각으로 (원 프레임 좌표 → 텍스처 사각형)', () => {
    const m = readPlateJson(json)!;
    expect(m).toMatchObject({ leftW: 26, rightW: 26, textCenterY: 19, minWidth: 68, pivotY: 38 });
    expect(m.textArea).toEqual({ x: 26, y: 7, w: 140, h: 24 });
    const s = slice3(m.frame, m.leftW, m.rightW);
    expect(s.left).toEqual({ tx: 0, ty: 0, w: 25, h: 36, dx: 1, dy: 3 });
    expect(s.mid).toEqual({ tx: 25, ty: 0, w: 140, h: 36, dx: 0, dy: 3 });
    expect(s.right).toEqual({ tx: 165, ty: 0, w: 25, h: 36, dx: 0, dy: 3 });
    expect([s.leftW, s.midW, s.rightW]).toEqual([26, 140, 26]);
    expect(readPlateJson(null)).toBeNull();
    expect(readPlateJson({ frames: {} })).toBeNull();
    expect(readPlateJson({ ...json, textArea: { x: 1, y: 2 } })!.textArea).toBeNull();
    // textCenterY 가 없으면 글자 칸 가운데
    expect(readPlateJson({ ...json, textCenterY: undefined })!.textCenterY).toBe(19);
  });

  it('가운데 폭 = 글자 폭(도트) + 여백, 최소 폭 아래로는 줄지 않는다', () => {
    const caps = { leftW: 26, rightW: 26, midW: 140 };
    expect(plateMidW(40, 0.5, 6, caps, 68)).toBe(92);
    expect(plateMidW(2, 0.5, 6, caps, 68)).toBe(16);
    // 지금 바탕: 글자 칸 = 가운데 조각 전체 → 같은 값
    expect(plateMidW(40, 0.5, 6, caps, 68, { x: 26, y: 7, w: 140, h: 24 })).toBe(92);
    // 글자 칸이 가운데보다 좁으면(좌우 10도트씩 장식) 그만큼 더 넓힌다
    expect(plateMidW(40, 0.5, 6, caps, 68, { x: 36, y: 3, w: 120, h: 24 })).toBe(112);
  });

  it('글자 자리: 가로 = textArea 가운데(가운데를 늘린 만큼 칸도 넓어진다), 세로 = textCenterY (60 Q36 새 판 19)', () => {
    const s = { leftW: 26, midW: 140 };
    const ta = { x: 26, y: 7, w: 140, h: 24 };
    expect(plateTextCenter(s, 140, 19, ta)).toEqual({ x: 96, y: 19 });
    expect(plateTextCenter(s, 180, 19, ta)).toEqual({ x: 116, y: 19 });
    // 글자 칸이 왼쪽으로 치우친 판
    expect(plateTextCenter(s, 140, 19, { x: 30, y: 4, w: 132, h: 24 })).toEqual({ x: 96, y: 19 });
    expect(plateTextCenter(s, 100, 15, null)).toEqual({ x: 76, y: 15 });
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
