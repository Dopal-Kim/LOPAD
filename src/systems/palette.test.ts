import { describe, expect, it } from 'vitest';
import { PALETTE } from '../data';
import { buildSwapTable, hexToRgb, rampFor, recolorPixels, resolveFxColor, variantSuffix } from './palette';

describe('palette swap', () => {
  it('층 램프는 12칸이고 1층은 접미가 없다', () => {
    expect(rampFor(PALETTE, 1)?.length).toBe(12);
    expect(rampFor(PALETTE, 99)).toBeNull();
    expect(variantSuffix(1)).toBe('');
    expect(variantSuffix(2)).toBe('@f2');
  });

  it('1층 램프 색만 2층 램프로 치환하고 무채색·알파는 그대로', () => {
    const from = rampFor(PALETTE, 1)!;
    const to = rampFor(PALETTE, 2)!;
    const table = buildSwapTable(from, to);
    const [r, g, b] = hexToRgb(from[5]);
    const [gr, gg, gb] = hexToRgb(PALETTE.gray[3]);
    const data = new Uint8ClampedArray([r, g, b, 255, gr, gg, gb, 255, r, g, b, 0]);
    const changed = recolorPixels(data, table);
    expect(changed).toBe(1);
    expect([data[0], data[1], data[2]]).toEqual(hexToRgb(to[5]));
    expect([data[4], data[5], data[6]]).toEqual([gr, gg, gb]);
    expect([data[8], data[9], data[10], data[11]]).toEqual([r, g, b, 0]);
  });

  it('이펙트 JSON 색: #hex(A 묶음) 와 팔레트 경로(B 묶음) 둘 다 해석, 모르는 형식은 null', () => {
    expect(resolveFxColor(PALETTE, '#6f7e97')).toBe(0x6f7e97);
    const dagger = PALETTE.fx!.weapons.dagger.ramp[1];
    expect(resolveFxColor(PALETTE, 'fx.weapons.dagger.ramp[1]')).toBe(parseInt(dagger.slice(1), 16));
    expect(resolveFxColor(PALETTE, 'fx.core[1]')).toBe(parseInt(PALETTE.fx!.core[1].slice(1), 16));
    expect(resolveFxColor(PALETTE, 'fx.weapons.greatsword.ramp[2]')).toBe(0xd8441c);
    expect(resolveFxColor(PALETTE, 'fx.weapons.nope.ramp[1]')).toBeNull();
    expect(resolveFxColor(PALETTE, 'fx.weapons.dagger.ramp[9]')).toBeNull();
    expect(resolveFxColor(PALETTE, 'red')).toBeNull();
    expect(resolveFxColor(PALETTE, undefined)).toBeNull();
  });
});
