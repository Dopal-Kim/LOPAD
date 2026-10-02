import { describe, expect, it } from 'vitest';
import { artScale, sheetJsonPath, sheetJsonPathV2, sheetToWorldUnits, type SheetJson } from './spriteDefs';

const base: SheetJson = {
  image: 'x.png',
  action: 'idle',
  frameWidth: 32,
  frameHeight: 48,
  frames: 2,
  directions: ['down'],
  fps: 8,
  loop: true,
  pivot: { x: 16, y: 46 },
};

describe('도트 배율 (50라운드 계약 art §9)', () => {
  it('pixelScale 1(새 2배 도트) = 월드 0.5, 없음/2(기존) = 1', () => {
    expect(artScale({ pixelScale: 1 })).toBe(0.5);
    expect(artScale({})).toBe(1);
    expect(artScale({ pixelScale: 2 })).toBe(1);
  });

  it('새 도트 메모 길이(판정 반경·찌르기·착지·광원·가림 높이)는 월드 단위로, 기존 도트는 그대로', () => {
    const v2 = sheetToWorldUnits({
      ...base,
      pixelScale: 1,
      hitRadiusPx: 66,
      thrust: { lengthPx: 48, widthPx: 16, fromPx: 8 },
      impactOffsetPx: { right: { x: 40, y: -4 } },
      impactDistancePx: 30,
      light: { radius: 120, offsetY: 20 },
      occludeAbove: 24,
    });
    expect(v2.hitRadiusPx).toBe(33);
    expect(v2.thrust).toEqual({ lengthPx: 24, widthPx: 8, fromPx: 4 });
    expect(v2.impactOffsetPx?.right).toEqual({ x: 20, y: -2 });
    expect(v2.impactDistancePx).toBe(15);
    expect(v2.light).toEqual({ radius: 60, offsetY: 10 });
    expect(v2.occludeAbove).toBe(12);
    expect(v2.pivot).toEqual({ x: 16, y: 46 }); // 텍스처 좌표는 그대로
    const old = { ...base, hitRadiusPx: 33 };
    expect(sheetToWorldUnits(old)).toBe(old);
  });

  it('v2 경로: sprites/<분류>/v2/<파일>', () => {
    const r = { category: 'player' as const, name: 'player', action: 'idle' };
    expect(sheetJsonPath(r)).toBe('sprites/player/player_idle.json');
    expect(sheetJsonPathV2(r)).toBe('sprites/player/v2/player_idle.json');
    expect(sheetJsonPathV2({ category: 'fx', name: 'slash', action: 'fx' })).toBe('sprites/fx/v2/slash.json');
  });
});
