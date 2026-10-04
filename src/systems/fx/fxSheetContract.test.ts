/**
 * 55라운드 계약 §10·§16 점검: 아트 v3 JSON 을 그대로 읽어 시스템이 기대하는 키·값을 확인한다 (파일이 없으면 건너뜀).
 * 승인 대장 #8(시스템 → assets 시트 JSON 계약 범위 읽기).
 */
import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { WEAPONS } from '../data';
import { parseAshKinds, parseAshRecipes } from './ashParticleMath';
import { weaponHitFxIds } from './fxIds';
import { secondarySheetId, tier2FxSheetIds } from './fxTier';
import { branchComboFxId } from './fxVariants';
import { animDurationMs, artScale, frameDurations, fxHoldFrame, type SheetJson } from './spriteDefs';

const DIR = resolve(__dirname, '../../assets/sprites/fx/v3');
const read = (id: string): SheetJson | null => {
  const f = `${DIR}/${id}.json`;
  return existsSync(f) ? (JSON.parse(readFileSync(f, 'utf8')) as SheetJson) : null;
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

  it('2단 전용 시트: 1단 JSON 이 가리키는 시트가 로드 목록에 있다 (Q16)', () => {
    const load = new Set(tier2FxSheetIds(WEAPONS));
    for (const [w, def] of Object.entries(WEAPONS)) {
      if (def.kind !== 'melee') continue;
      for (const b of def.personality.branches)
        for (let n = 1; n <= 3; n++) {
          const tier1 = branchComboFxId(w, n, b.id);
          const j = read(tier1);
          if (!j) continue;
          for (const s of b.next ?? []) {
            const id = secondarySheetId(tier1, j, s.id);
            expect(load.has(id), id).toBe(true);
            const t2 = read(id);
            if (t2) expect(t2.hitRadiusPx ?? null, id).toBe(j.hitRadiusPx ?? null); // 판정 필드는 1단과 같다
          }
        }
    }
  });
});
