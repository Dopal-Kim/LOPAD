/**
 * 60라운드 계약 art §11 P1 점검 (실제 JSON): 1층 적 3종(dummy·archer·charger) attack 10프레임 [3,1,3,3]·hurt 4프레임 [70,30,30,30].
 * 시스템은 프레임 번호를 하드코딩하지 않고 phaseFrames·impactFrame/fireFrame·앵커 배열·frameDurationsMs 를 읽으므로,
 * 판정·발사 시각과 총 길이가 이전(JSON oldTiming · 60라운드 전 값)과 같은지 확인한다. 엘리트 외곽선 `*_elite` 도 같은 프레임.
 * 파일이 없으면 건너뜀. 승인 대장 #8(시스템 → assets 시트 JSON 계약 범위 읽기).
 */
import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { readSheetJson } from './sheetAtlas';
import type { SheetJson } from './sheetJson';
import { animDurationMs, fireDelayMs, frameStarts, startsOf } from './sheetFrames';

const DIR = resolve(__dirname, '../../../assets/sprites');
type Raw = SheetJson & {
  oldTiming?: { frameDurationsMs: number[]; framesMap: number[][] };
  phaseStartMs?: Record<string, number>;
  muzzleAnchors?: Record<string, unknown[]>;
  hammerFaceAnchors?: Record<string, unknown[]>;
  headTopByEnemy?: Record<string, number>;
  flashFrame?: number;
};
const read = (rel: string): Raw | null => {
  const f = `${DIR}/${rel}.json`;
  return existsSync(f) ? ((readSheetJson(JSON.parse(readFileSync(f, 'utf8')))?.json ?? null) as Raw | null) : null;
};
const ENEMIES = ['dummy', 'archer', 'charger'] as const;
/** 60라운드 전(7·8프레임 v3) 판정·발사 시각 ms — dummy impactFrame 3 · archer fireFrame 2 · charger impactFrame 4 */
const BEFORE = { dummy: 170, archer: 160, charger: 240 } as const;
const present = existsSync(`${DIR}/enemies/v3/dummy_attack.json`);

/** 새 프레임 f 의 시작 = 구 프레임(framesMap 에서 f 로 시작하는 칸)의 시작 */
function oldStartOf(def: Raw, f: number): number | null {
  const ot = def.oldTiming;
  if (!ot) return null;
  const k = ot.framesMap.findIndex((cols) => cols[0] === f);
  return k < 0 ? null : startsOf(ot.frameDurationsMs)[k];
}

describe.skipIf(!present)('60라운드 P1 — 1층 적 attack 10·hurt 4 프레임 (실제 JSON)', () => {
  for (const id of ENEMIES) {
    const atk = read(`enemies/v3/${id}_attack`);
    const hurt = read(`enemies/v3/${id}_hurt`);
    if (!atk || !hurt) continue;

    it(`${id}: attack 10 · hurt 4 프레임, 총 길이는 이전과 같다`, () => {
      expect(atk.frames).toBe(10);
      expect(hurt.frames).toBe(4);
      expect(hurt.frameDurationsMs).toEqual([70, 30, 30, 30]);
      expect(hurt.flashFrame).toBe(0);
      for (const d of [atk, hurt]) {
        const ot = d.oldTiming!;
        expect(animDurationMs(d)).toBe(ot.frameDurationsMs.reduce((a, b) => a + b, 0));
      }
    });

    it(`${id}: 국면(phaseFrames) 시작 = phaseStartMs = 구 프레임 시작`, () => {
      const st = frameStarts(atk);
      for (const [phase, cols = []] of Object.entries(atk.phaseFrames ?? {})) {
        expect(st[cols[0]], phase).toBeCloseTo(atk.phaseStartMs![phase], 6);
        expect(st[cols[0]], phase).toBeCloseTo(oldStartOf(atk, cols[0])!, 6);
      }
      const split = Object.values(atk.phaseFrames ?? {}).map((c) => c?.length ?? 0);
      expect(split).toEqual([3, 1, 3, 3]);
    });

    it(`${id}: 판정·발사 프레임 시각이 이전과 같다`, () => {
      const key = typeof atk.fireFrame === 'number' ? atk.fireFrame : atk.impactFrame!;
      expect(frameStarts(atk)[key]).toBeCloseTo(BEFORE[id], 6);
      expect(frameStarts(atk)[key]).toBeCloseTo(oldStartOf(atk, key)!, 6);
      // 사수 탄 생성 지연(EntityVisual.impactDelayMs → fireDelayMs)
      if (typeof atk.fireFrame === 'number') expect(fireDelayMs(atk)).toBeCloseTo(BEFORE[id], 6);
    });

    it(`${id}: 앵커 배열은 방향마다 프레임 수만큼 (판정 프레임으로 찾는다)`, () => {
      for (const anchors of [atk.muzzleAnchors, atk.hammerFaceAnchors])
        for (const [dir, list] of Object.entries(anchors ?? {})) expect(list.length, dir).toBe(atk.frames);
    });

    it(`${id}: 엘리트 외곽선 *_elite 는 같은 프레임 수·ms·틀·피벗`, () => {
      for (const [base, act] of [
        [atk, 'attack'],
        [hurt, 'hurt'],
      ] as const) {
        const el = read(`enemies/v3/${id}_${act}_elite`);
        if (!el) continue;
        expect(el.frames, act).toBe(base.frames);
        expect(el.frameDurationsMs, act).toEqual(base.frameDurationsMs);
        expect([el.frameWidth, el.frameHeight], act).toEqual([base.frameWidth, base.frameHeight]);
        expect(el.pivot, act).toEqual(base.pivot);
      }
    });
  }

  it('엘리트 문장·술 김·마시기 headTopByEnemy 새 값 (dummy 119 · archer 120 · charger 139)', () => {
    for (const id of ['elite_emblem', 'elite_drunk_vapor', 'elite_guzzle_drink']) {
      const def = read(`fx/v3/${id}`);
      if (!def) continue;
      expect(def.headTopByEnemy, id).toEqual({ dummy: 119, archer: 120, charger: 139 });
    }
  });
});
