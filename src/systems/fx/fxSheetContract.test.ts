/**
 * 55라운드 계약 §10·§16 점검: 아트 v3 JSON 을 그대로 읽어 시스템이 기대하는 키·값을 확인한다 (파일이 없으면 건너뜀).
 * 승인 대장 #8(시스템 → assets 시트 JSON 계약 범위 읽기).
 */
import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { WEAPONS } from '../../data';
import { parseAshKinds, parseAshRecipes } from './ashParticleMath';
import { weaponHitFxIds } from './fxIds';
import { animDurationMs, artScale, frameDurations, fxHoldFrame, type SheetJson } from '../sprites/spriteDefs';
import { readSheetJson } from '../sprites/sheetAtlas';

const DIR = resolve(__dirname, '../../../assets/sprites/fx/v3');
const read = (id: string): SheetJson | null => {
  const f = `${DIR}/${id}.json`;
  // 57라운드 아틀라스(`framesPerDirection`·`frames{}`)도 로더와 같은 정규화로 (frames = 방향당 프레임 수)
  return existsSync(f) ? (readSheetJson(JSON.parse(readFileSync(f, 'utf8')))?.json ?? null) : null;
};
const present = existsSync(DIR);

describe.skipIf(!present)('계약 §16 (55라운드) — 아트 v3 JSON', () => {
  it('움직임 fx: frameDurationsMs 가 프레임 수와 맞아 그대로 읽힌다 (Q12 길이 증가)', () => {
    for (const id of ['dash_trail', 'dash_dust', 'parry_flash', 'guard_wave', 'ironwall', 'shadowstep_ghost']) {
      const def = read(id);
      if (!def) continue;
      expect(def.frameDurationsMs?.length, id).toBe(def.frames);
      expect(frameDurations(def), id).toEqual(def.frameDurationsMs);
    }
    expect(read('parry_flash') ? animDurationMs(read('parry_flash')!) : 360).toBe(360);
  });

  it('무기 적중 스파크: 회전·holdFrame·백열 프레임', () => {
    for (const w of Object.keys(WEAPONS))
      for (const id of weaponHitFxIds(w)) {
        const def = read(id);
        if (!def) continue;
        expect(def.rotate, id).toBe(true);
        expect(fxHoldFrame(def), id).toBe(def.holdFrame ?? 0);
        expect(def.glowFrames, id).toContain(fxHoldFrame(def));
      }
  });

  it('재 파편: 모든 recipes 의 kind 가 kinds 에 있다', () => {
    const def = read('particles_ash');
    if (!def) return;
    const kinds = parseAshKinds(def.kinds, artScale(def));
    for (const [sheet, r] of Object.entries(parseAshRecipes(def.recipes))) {
      for (const k of Object.keys(r.kinds)) expect(kinds[k], `${sheet}.${k}`).toBeDefined();
      expect(r.coneDeg).toBeGreaterThan(0);
    }
  });

  it('리본: 4단계 나이 프레임, 2~3도트 폭', () => {
    for (const id of ['ribbon_ash', 'ribbon_ash_thin']) {
      const def = read(id);
      if (!def) continue;
      expect(def.frames, id).toBe(4);
      expect(def.frameHeight, id).toBeGreaterThanOrEqual(2);
      expect(def.frameHeight, id).toBeLessThanOrEqual(3);
    }
  });
});
