import { describe, expect, it } from 'vitest';
import { artScale, sheetJsonPath, sheetToWorldUnits, type SheetJson } from './spriteDefs';
import { sheetJsonCandidates, sheetJsonPathTier } from './spriteMeta';

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
    expect(sheetJsonPathTier(r, 'v2')).toBe('sprites/player/v2/player_idle.json');
    expect(sheetJsonPathTier({ category: 'fx', name: 'slash', action: 'fx' }, 'v2')).toBe('sprites/fx/v2/slash.json');
  });

  it('52라운드 v3: 후보 경로 v3 → v2 → 기존, v3 도트(0.5) = 월드 0.25 (도트 1 = 실제 1px)', () => {
    const r = { category: 'weapons' as const, name: 'greatsword', action: 'carry_run' };
    expect(sheetJsonCandidates(r)).toEqual([
      'sprites/weapons/v3/greatsword_carry_run.json',
      'sprites/weapons/v2/greatsword_carry_run.json',
      'sprites/weapons/greatsword_carry_run.json',
    ]);
    // 53라운드 4번: 주인공·칼 오버레이는 v3 만 (구 시트·v2 를 로드하지 않는다)
    expect(sheetJsonCandidates({ category: 'weapons', name: 'katana', action: 'carry_run' })).toEqual([
      'sprites/weapons/v3/katana_carry_run.json',
    ]);
    expect(sheetJsonCandidates({ category: 'player', name: 'player', action: 'idle' })).toEqual([
      'sprites/player/v3/player_idle.json',
    ]);
    // 이펙트는 v3 → v2 → 기존 (없으면 기존 동작 유지). 53라운드 후속: v3 가 갖춰진 적 3종은 v3 만
    expect(sheetJsonCandidates({ category: 'fx', name: 'hit_spark', action: 'fx' })).toEqual([
      'sprites/fx/v3/hit_spark.json',
      'sprites/fx/v2/hit_spark.json',
      'sprites/fx/hit_spark.json',
    ]);
    expect(sheetJsonCandidates({ category: 'enemies', name: 'charger', action: 'walk' })).toEqual([
      'sprites/enemies/v3/charger_walk.json',
    ]);
    expect(artScale({ pixelScale: 0.5 })).toBe(0.25);
    // v3 판정 반경 132 도트 = v2 66 = 월드 33 (논리 크기 같음)
    expect(sheetToWorldUnits({ ...base, pixelScale: 0.5, hitRadiusPx: 132 }).hitRadiusPx).toBe(33);
  });
});
