import { describe, expect, it } from 'vitest';
import { LIGHTING, validateLighting } from '../../data';
import type { LightingData } from '../../data/types';
import { flickerFactor, hash01, hexColor, lightFalloff, pickLights } from './lightMath';
import { LightRegistry, lightFor } from './lightRegistry';

describe('조명 규칙 (50라운드)', () => {
  it('색: #rrggbb → 정수, 형식이 아니면 기본값', () => {
    expect(hexColor('#ff8000', 0)).toBe(0xff8000);
    expect(hexColor('nope', 0x123456)).toBe(0x123456);
    expect(hexColor(undefined, 7)).toBe(7);
  });

  it('깜빡임: 세기 0 이면 1, 아니면 [1 - 세기, 1] 안에서 시간에 따라 바뀐다', () => {
    expect(flickerFactor(1234, 3, 0, [4, 9])).toBe(1);
    const vals = Array.from({ length: 60 }, (_, i) => flickerFactor(i * 16, 5, 0.3, [4, 9]));
    for (const v of vals) {
      expect(v).toBeGreaterThanOrEqual(0.7 - 1e-9);
      expect(v).toBeLessThanOrEqual(1 + 1e-9);
    }
    expect(new Set(vals.map((v) => v.toFixed(3))).size).toBeGreaterThan(5);
    // 광원마다 위상이 다르다
    expect(hash01(1)).not.toBeCloseTo(hash01(2), 5);
  });

  it('감쇠 = (1 - d²)² (아트 목업과 같은 식)', () => {
    expect(lightFalloff(0)).toBe(1);
    expect(lightFalloff(0.5)).toBeCloseTo(0.5625, 6);
    expect(lightFalloff(1)).toBe(0);
    expect(lightFalloff(2)).toBe(0);
  });

  it('광원 고르기: 고정 먼저, 화면에 걸치는 것만, 가까운 순, 상한', () => {
    const lights = [
      { x: 1000, y: 1000, radius: 10 }, // 화면 밖
      { x: 60, y: 0, radius: 10 },
      { x: 10, y: 0, radius: 10 },
      { x: 500, y: 0, radius: 10, pinned: true }, // 화면 밖이어도 고정
      { x: 130, y: 0, radius: 40 }, // 반경이 화면에 걸침
    ];
    expect(pickLights(lights, 0, 0, 100, 60, 10)).toEqual([3, 2, 1, 4]);
    expect(pickLights(lights, 0, 0, 100, 60, 2)).toEqual([3, 2]);
  });

  it('광원 목록: 대상을 따라가고(offsetY 위로), 대상이 비활성·만료면 지운다, 꺼둔 광원은 그리지 않는다', () => {
    const reg = new LightRegistry();
    const anchor = { x: 10, y: 20, active: true };
    const a = reg.add({ radius: 30, offsetY: 5, color: '#ffffff' }, { x: 0, y: 0, anchor });
    reg.add({ radius: 30 }, { x: 1, y: 1, until: 100 });
    const off = reg.add({ radius: 30 }, { x: 2, y: 2 });
    off.enabled = false;
    let live = reg.live(50);
    expect(live.length).toBe(2);
    expect(live.find((l) => l.id === a.id)).toMatchObject({ x: 10, y: 15 });
    live = reg.live(150);
    expect(live.length).toBe(1);
    anchor.active = false;
    expect(reg.live(160).length).toBe(0);
    expect(reg.size).toBe(1); // 꺼둔 것만 남음
  });

  it('시트 광원: JSON light → fallback(시트 id) → 무기 이펙트 → 없음', () => {
    expect(lightFor('anything', { light: { radius: 12 } })).toEqual({ radius: 12 });
    expect(lightFor('bonfire', {})).toBe(LIGHTING.fallback.bonfire);
    // 61 단계 6 (art §28): 시트 light 가 없는 무기 이펙트 = weaponFx 세기·반경 + 무기 색 (모르는 무기면 weaponFx 그대로)
    expect(lightFor('katana_combo1', { weapon: 'katana' })).toEqual({ ...LIGHTING.weaponFx, color: '#8fe3ff' });
    expect(lightFor('x_combo1', { weapon: 'unknown' })).toBe(LIGHTING.weaponFx);
    expect(lightFor('crate_f1', {})).toBeNull();
  });

  it('데이터: 외곽 거리만 지역 조명 (시범), 형식 검증', () => {
    expect(Object.keys(LIGHTING.regions)).toContain('outer');
    expect(LIGHTING.maxLights).toBeGreaterThan(0);
    const bad = { ...LIGHTING, regions: { outer: { ambient: 'dark' } } } as unknown as LightingData;
    expect(() => validateLighting(bad)).toThrow();
    const bad2 = { ...LIGHTING, player: { radius: 0 } } as unknown as LightingData;
    expect(() => validateLighting(bad2)).toThrow();
  });
});
