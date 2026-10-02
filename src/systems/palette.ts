/** 런타임 팔레트 스왑 (계약 art-assets.md §2). Phaser 의존 없음 — 픽셀 배열만 다룬다. */
import type { PaletteData } from '../data/types';

/** 캐릭터 시트가 그려진 기준 층 (강조 램프 원본) */
export const BASE_FLOOR = 1;

export function rampFor(palette: PaletteData, floor: number): string[] | null {
  return palette.floors.find((f) => f.floor === floor)?.ramp ?? null;
}

/** 이펙트 보조 램프 색 (42라운드 Q2 fx 블록). 블록·무기·칸이 없으면 null */
export function fxWeaponColor(palette: PaletteData, weaponId: string, index: number): string | null {
  return palette.fx?.weapons?.[weaponId]?.ramp?.[index] ?? null;
}

/** 이펙트 코어 색 (fx.core[0] = 백열 G15). 없으면 null */
export function fxCoreColor(palette: PaletteData, index = 0): string | null {
  return palette.fx?.core?.[index] ?? null;
}

/**
 * 이펙트 JSON 색 값 해석 (43라운드 B 묶음): '#rrggbb' · 'fx.weapons.<무기>.ramp[i]' · 'fx.core[i]'.
 * 형식이 다르거나 팔레트에 없으면 null (호출 쪽 기본색)
 */
export function resolveFxColor(palette: PaletteData, ref: string | undefined | null): number | null {
  if (!ref) return null;
  if (/^#[0-9a-fA-F]{6}$/.test(ref)) return hexToInt(ref);
  const w = /^fx\.weapons\.([a-z_]+)\.ramp\[(\d+)\]$/.exec(ref);
  if (w) {
    const hex = fxWeaponColor(palette, w[1], Number(w[2]));
    return hex ? hexToInt(hex) : null;
  }
  const c = /^fx\.core\[(\d+)\]$/.exec(ref);
  if (c) {
    const hex = fxCoreColor(palette, Number(c[1]));
    return hex ? hexToInt(hex) : null;
  }
  return null;
}

/** '#rrggbb' → 0xrrggbb */
export function hexToInt(hex: string): number {
  return parseInt(hex.slice(1), 16);
}

export function hexToRgb(hex: string): [number, number, number] {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 0xff, (n >> 8) & 0xff, n & 0xff];
}

function pack(r: number, g: number, b: number): number {
  return (r << 16) | (g << 8) | b;
}

/** from[i] 색을 to[i] 색으로 치환하는 표. 길이가 다르면 짧은 쪽까지만 */
export function buildSwapTable(from: string[], to: string[]): Map<number, [number, number, number]> {
  const table = new Map<number, [number, number, number]>();
  const n = Math.min(from.length, to.length);
  for (let i = 0; i < n; i++) table.set(pack(...hexToRgb(from[i])), hexToRgb(to[i]));
  return table;
}

/**
 * RGBA 픽셀 배열을 제자리에서 재채색한다. 알파는 유지. 표에 없는 색(무채색)은 그대로.
 * 반환값: 바뀐 픽셀 수
 */
export function recolorPixels(data: Uint8ClampedArray, table: Map<number, [number, number, number]>): number {
  let changed = 0;
  for (let i = 0; i < data.length; i += 4) {
    if (data[i + 3] === 0) continue;
    const hit = table.get(pack(data[i], data[i + 1], data[i + 2]));
    if (!hit) continue;
    data[i] = hit[0];
    data[i + 1] = hit[1];
    data[i + 2] = hit[2];
    changed++;
  }
  return changed;
}

/** 층 번호 → 텍스처·애니 키 접미. 기준 층은 접미 없음 (치환 없음) */
export function variantSuffix(floor: number): string {
  return floor === BASE_FLOOR ? '' : `@f${floor}`;
}
