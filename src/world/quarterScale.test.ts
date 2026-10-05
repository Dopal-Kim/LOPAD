/**
 * 60라운드 계약 art §11 P1 점검 (실제 JSON): 1층 5지역 타일셋 `tiles/v2/stage1_<지역>` 이 64도트 = 1칸·pixelScale 0.5 가 되고
 * 도트 단위 길이(tileLights·decals rect·props/bigProps 의 rect·pivot·occludeAbove·light radius·offset)가 2배가 됐을 때,
 * 시스템 환산(`quarterScale`)으로 화면상 크기가 그대로인지 — 한 칸 = TILE, 데칼·큰 소품 = 발자국 칸, 광원은 칸·그림 안.
 * 파일이 없으면 건너뜀. 승인 대장 #8(시스템 → assets 시트 JSON 계약 범위 읽기).
 */
import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { TILE } from '../core/Constants';
import { cellLight, cutLight, occludeCut, tileDotScale } from './quarterScale';
import { TileSkin, lightOffsetOf, type TilesetJson } from './tileskin';

const DIR = resolve(__dirname, '../../assets/tiles');
const REGIONS = ['outer', 'gate', 'hall', 'brewery', 'waste'] as const;
const read = (rel: string): TilesetJson | null =>
  existsSync(`${DIR}/${rel}.json`) ? (JSON.parse(readFileSync(`${DIR}/${rel}.json`, 'utf8')) as TilesetJson) : null;
const present = existsSync(`${DIR}/v2/stage1_outer.json`);

describe('quarterScale (합성 값)', () => {
  it('32칸(옛)과 64칸(새)의 같은 그림은 월드에서 같은 크기·자리', () => {
    expect(32 * tileDotScale(32)).toBe(TILE);
    expect(64 * tileDotScale(64)).toBe(TILE);
    const old = cellLight(
      { color: '#fff', radius: 70, intensity: 1, offset: { x: 16, y: 26 } },
      3,
      4,
      32,
      tileDotScale(32),
    );
    const neu = cellLight(
      { color: '#fff', radius: 140, intensity: 1, offset: { x: 32, y: 52 } },
      3,
      4,
      64,
      tileDotScale(64),
    );
    expect(neu.spec.radius).toBe(old.spec.radius);
    expect([neu.x, neu.y]).toEqual([old.x, old.y]);
    // offset 이 없으면 칸 가운데
    const mid = cellLight({ color: '#fff', radius: 8, intensity: 1 }, 0, 0, 64, tileDotScale(64));
    expect([mid.x, mid.y]).toEqual([TILE / 2, TILE / 2]);
    const a = cutLight({ color: '#fff', radius: 150, intensity: 1, offset: [24, 22] }, 100, 200, { x: 13, y: 62 }, 0.5);
    const b = cutLight(
      { color: '#fff', radius: 300, intensity: 1, offset: [48, 44] },
      100,
      200,
      { x: 26, y: 124 },
      0.25,
    );
    expect([b.x, b.y, b.spec.radius]).toEqual([a.x, a.y, a.spec.radius]);
    expect(occludeCut({ rect: { h: 128 }, pivot: { y: 124 }, occludeAbove: 32 })).toBe(92);
    expect(occludeCut({ rect: { h: 128 }, pivot: { y: 124 } })).toBe(128);
  });
});

describe.skipIf(!present)('60라운드 P1 — 1층 5지역 64도트 타일셋 (실제 JSON)', () => {
  for (const region of REGIONS) {
    const def = read(`v2/stage1_${region}`);
    if (!def) continue;
    const skin = new TileSkin(`tiles_${region}`, def, true);
    const k = tileDotScale(skin.tilePx);

    it(`${region}: 64도트 칸 · pixelScale 0.5 → 한 칸 = TILE (화면상 2배가 아님), 두 환산이 같다`, () => {
      expect(skin.tilePx).toBe(64);
      expect(def.pixelScale).toBe(0.5);
      expect(skin.tilePx * k).toBe(TILE);
      expect(skin.worldScale).toBe(k);
    });

    it(`${region}: tileLights offset 은 칸 안, 반경은 월드로 줄어든다`, () => {
      for (const [idx, l] of Object.entries(def.tileLights ?? {})) {
        const o = lightOffsetOf(l.offset);
        if (o) {
          expect(o.x, idx).toBeGreaterThanOrEqual(0);
          expect(o.x, idx).toBeLessThanOrEqual(skin.tilePx);
          expect(o.y, idx).toBeLessThanOrEqual(skin.tilePx);
        }
        const c = cellLight(l, 5, 7, skin.tilePx, k);
        expect(c.x - 5 * TILE, idx).toBeLessThanOrEqual(TILE);
        expect(c.y - 7 * TILE, idx).toBeLessThanOrEqual(TILE);
        expect(c.spec.radius, idx).toBe(l.radius / 4);
        // 64도트 칸 기준 광원 반경(월드)은 몇 칸 남짓 — 옛 32도트 값이 그대로 남아 반으로 줄지 않았다
        expect(c.spec.radius, idx).toBeGreaterThan(TILE);
      }
    });

    it(`${region}: 데칼 rect = 발자국 칸 (월드)`, () => {
      for (const d of def.decals ?? []) {
        expect(d.rect.w * k, d.name).toBe(d.footprint[0] * TILE);
        expect(d.rect.h * k, d.name).toBe(d.footprint[1] * TILE);
      }
    });

    it(`${region}: 큰 소품·소품 rect·pivot·occludeAbove·광원이 같은 도트 단위`, () => {
      for (const b of skin.bigProps) {
        const [fw] = b.footprint ?? [1, 1];
        expect(b.rect.w * k, b.name).toBe(fw * TILE);
        expect(b.pivot.x, b.name).toBeLessThanOrEqual(b.rect.w);
        expect(b.pivot.y, b.name).toBeLessThanOrEqual(b.rect.h);
        const cut = occludeCut(b);
        expect(cut, b.name).toBeGreaterThanOrEqual(0);
        expect(cut, b.name).toBeLessThanOrEqual(b.rect.h);
        for (const l of b.lights ?? (b.light ? [b.light] : [])) {
          const o = lightOffsetOf(l.offset);
          if (!o) continue;
          expect(o.x, b.name).toBeLessThanOrEqual(b.rect.w);
          expect(o.y, b.name).toBeLessThanOrEqual(b.rect.h);
          // 광원 = 그림 안 (월드)
          const c = cutLight(l, 0, 0, b.pivot, k);
          expect(Math.abs(c.x), b.name).toBeLessThanOrEqual(b.rect.w * k);
          expect(-c.y, b.name).toBeLessThanOrEqual(b.rect.h * k);
        }
      }
      for (const p of def.props ?? []) {
        if (!p.pivot) continue;
        expect(p.pivot.x, p.name).toBeLessThanOrEqual(p.rect?.w ?? skin.tilePx);
        expect(p.pivot.y, p.name).toBeLessThanOrEqual(p.rect?.h ?? skin.tilePx);
      }
    });
  }

  it('v3 소품 시트(지역 propsSheet)는 자기 pixelScale 로 (바닥 64도트 전환과 무관)', () => {
    for (const region of REGIONS) {
      const props = read(`v3/stage1_${region}_props`);
      if (!props) continue;
      const ps = props.pixelScale ?? 1;
      expect(new TileSkin(`p_${region}`, props, true).worldScale).toBe(ps / 2);
    }
  });
});
