import { describe, expect, it } from 'vitest';
import { cameraZoom, comboText, edgePoint, offscreenMarks, offscreenOf, popOf, popScreen } from './p19View';
import { OFFSCREEN, TELL } from './themeP19';

describe('P19 화면 밖 적 표식', () => {
  it('가장자리 점: 오른쪽·위·왼쪽 아래 모서리 쪽', () => {
    expect(edgePoint(0, 960, 540, 10, 30, 14)).toEqual({ x: 950, y: 270 });
    expect(edgePoint(-Math.PI / 2, 960, 540, 10, 30, 14)).toEqual({ x: 480, y: 30 });
    const p = edgePoint(Math.atan2(526 - 270, 10 - 480), 960, 540, 10, 30, 14);
    expect(p).toEqual({ x: 10, y: 526 });
  });

  it('모든 적에 하나씩 · 위협 색 · 가까울수록 크고 진하다 · 위험이 맨 위(마지막)', () => {
    const list = offscreenOf({
      offscreen: [
        { id: 'a', angle: 0, distTiles: 2, threat: 'danger' },
        { id: 'b', angle: 1, distTiles: 30, threat: null },
        { id: 'c', angle: 2, distTiles: 8, threat: 'ranged' },
        { id: 'bad', angle: 'x' },
      ],
    });
    const marks = offscreenMarks(list, 960, 540);
    expect(marks.map((m) => m.id)).toEqual(['b', 'c', 'a']);
    const a = marks.find((m) => m.id === 'a')!;
    const b = marks.find((m) => m.id === 'b')!;
    expect(a.color).toBe(TELL.danger);
    expect(b.color).toBeNull();
    expect(a.size).toBe(OFFSCREEN.sizeMax);
    expect(b.size).toBe(OFFSCREEN.sizeMin);
    expect(a.alpha).toBe(1);
    expect(b.alpha).toBe(OFFSCREEN.farAlpha);
  });

  it('필드가 없으면 빈 목록 · 옛 배율', () => {
    expect(offscreenOf({})).toEqual([]);
    expect(cameraZoom({})).toBe(2);
    expect(cameraZoom({ camera: { zoom: 1.6, combat: true } })).toBe(1.6);
  });
});

describe('P19 반응 팝', () => {
  it('벽꽝·볼링은 숫자, 낙하는 그림만, 폭발은 연쇄부터', () => {
    expect(popOf('wall', { bonusDamage: 17.6 }, true)).toEqual({ kind: 'wall', num: '18' });
    expect(popOf('wall', { bonusDamage: 17.6 }, false)).toEqual({ kind: 'wall', num: '' });
    expect(popOf('bowl', { damage: 9 }, true)?.num).toBe('9');
    expect(popOf('fell', { zone: 'water' }, true)).toEqual({ kind: 'fell', num: '' });
    expect(popOf('blast', { chain: 0 }, true)).toBeNull();
    expect(popOf('blast', { chain: 2 }, true)?.num).toBe('×3');
  });

  it('자리: screen 우선, 없으면 camera.view 로 월드 → 화면, 둘 다 없으면 없음', () => {
    const cam = { zoom: 1.6, combat: true, view: { x: 100, y: 50, w: 600, h: 337.5 } };
    expect(popScreen({ x: 1, y: 2, screen: { x: 30, y: 40 } }, cam, 960, 540)).toEqual({ x: 30, y: 40 });
    expect(popScreen({ x: 400, y: 50 + 337.5 / 2 }, cam, 960, 540)).toEqual({ x: 480, y: 270 });
    expect(popScreen({ x: 400, y: 200 }, null, 960, 540)).toBeNull();
  });

  it('연속 처치는 2부터', () => {
    expect(comboText(1, 2)).toBeNull();
    expect(comboText(4, 2)).toBe('×4');
  });
});
