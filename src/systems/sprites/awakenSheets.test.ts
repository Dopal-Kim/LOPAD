/**
 * 60라운드 계약 art §21 '60라운드 제작 결과' 점검: 실제 각성 JSON 을 읽어
 * - 각성 오버레이 틀이 커져도(칼 264·단검/활 256·대검 +80/+64) 주인공 피벗에 맞춰 원 무기 오버레이와 같은 자리(= 원 피벗 + pivotDelta)
 * - 각성 순간 fx `<무기>_awaken_in` · 각성 궤적 `<fx>_awaken` 19종(1:1 교체 — 틀·ms·피벗·행 동일, 화살 3종은 틀이 길어도 피벗 기준)
 * 을 확인한다 (파일이 없으면 건너뜀). 승인 대장 #8(시스템 → assets 시트 JSON 계약 범위 읽기).
 */
import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { readSheetJson } from './sheetAtlas';
import type { SheetJson } from './sheetJson';
import { overlayPivot } from './spriteMeta';
import { frameDurations } from './sheetFrames';
import { FX_ACTION } from './spriteActions';
import {
  awakenFxAliases,
  awakenInFxId,
  awakenSheetRequests,
  bootSheetRequests,
  fxSwapTable,
  requestKey,
} from './sheetSets';
import { WEAPONS as WEAPON_TABLE } from '../../data';

const ROOT = resolve(__dirname, '../../../assets/sprites');
const read = (rel: string): (SheetJson & Record<string, unknown>) | null => {
  const f = `${ROOT}/${rel}.json`;
  return existsSync(f)
    ? ((readSheetJson(JSON.parse(readFileSync(f, 'utf8')))?.json ?? null) as
        (SheetJson & Record<string, unknown>) | null)
    : null;
};
const WEAPONS = ['katana', 'greatsword', 'dagger', 'bow'] as const;
/** 계약 §21 각성 전용 궤적 19종 */
const TRAILS: Record<(typeof WEAPONS)[number], string[]> = {
  katana: [
    'katana_rise',
    'katana_fall',
    'katana_spin',
    'katana_thrust',
    'katana_issen_line_t1',
    'katana_issen_line_t2',
    'katana_issen_line_t3',
    'katana_issen_line_t4',
  ],
  greatsword: ['greatsword_sweep_cw', 'greatsword_sweep_ccw', 'greatsword_cleave', 'greatsword_charge_swing'],
  dagger: ['dagger_combo1', 'dagger_combo2', 'dagger_combo3', 'dagger_flurry'],
  bow: ['bow_arrow', 'bow_arrow_rapid', 'bow_arrow_snipe'],
};
const ARROWS = new Set(TRAILS.bow);
/** 60 Q33 갈래 × 각성 합친 그림 (계약 art §21 — awakenOf = 갈래 시트, swapPriority 갈래+각성 → 갈래 → 각성 → 기본) */
const MERGED: Record<string, { weapon: (typeof WEAPONS)[number]; from: string; branch: string }> = {
  katana_fall_wide_awaken: { weapon: 'katana', from: 'katana_fall', branch: 'katana_fall_wide' },
  dagger_combo3_double_awaken: { weapon: 'dagger', from: 'dagger_combo3', branch: 'dagger_combo3_double' },
};
const MERGED_FROM = new Set(Object.values(MERGED).map((m) => m.branch));

describe('60 Q33 갈래 + 각성 교체 표 (데이터만)', () => {
  const replaceOf = (w: string) =>
    Object.assign(
      {},
      ...WEAPON_TABLE[w].personality.branches.flatMap((a) => [a, ...(a.next ?? [])]).map((n) => n.art?.replaceFx ?? {}),
    ) as Record<string, string>;

  it('합친 그림은 각성 묶음에 요청되고, 갈래 + 각성이면 합친 그림 → 갈래 그림 → 각성 궤적 순 후보', () => {
    for (const [merged, m] of Object.entries(MERGED)) {
      expect(awakenSheetRequests(m.weapon).map(requestKey), merged).toContain(`fx/${merged}_${FX_ACTION}`);
      const replace = replaceOf(m.weapon);
      expect(replace[m.from], merged).toBe(m.branch);
      const table = fxSwapTable(awakenFxAliases(m.weapon), replace);
      expect(table[m.from], merged).toEqual([merged, m.branch, `${m.from}_awaken`]);
      // 갈래만(각성 아님): 갈래 그림 / 각성만(갈래 아님): 각성 궤적
      expect(fxSwapTable({}, replace)[m.from]).toEqual([m.branch]);
      expect(fxSwapTable(awakenFxAliases(m.weapon), {})[m.from]).toEqual([`${m.from}_awaken`]);
    }
  });

  it('후보 순서: 합친 그림 이름이 없으면 갈래 → 각성 궤적, 각성 아님이면 갈래 하나', () => {
    expect(fxSwapTable({ a: 'a_awaken' }, { a: 'b' })).toEqual({ a: ['b', 'a_awaken'] });
    expect(fxSwapTable({ a: 'a_awaken', b: 'b_awaken' }, { a: 'b' })).toEqual({
      a: ['b_awaken', 'b', 'a_awaken'],
      b: ['b_awaken'],
    });
    expect(fxSwapTable({}, { a: 'b' })).toEqual({ a: ['b'] });
  });
});

describe.skipIf(!existsSync(`${ROOT}/fx/v3/katana_fall_wide_awaken.json`))('60 Q33 합친 그림 (실제 JSON)', () => {
  it('JSON swapPriority = 교체 표 후보 + 원 fx · awakenOf = 갈래 시트 · 갈래 시트와 1:1 (틀·프레임·ms·피벗·행·판정)', () => {
    for (const [merged, m] of Object.entries(MERGED)) {
      const aw = read(`fx/v3/${merged}`);
      const base = read(`fx/v3/${m.branch}`);
      expect(aw && base, merged).toBeTruthy();
      const table = fxSwapTable(awakenFxAliases(m.weapon), { [m.from]: m.branch });
      expect(aw!.swapPriority, merged).toEqual([...table[m.from], m.from]);
      expect(aw!.awakenOf, merged).toBe(`fx/v3/${m.branch}`);
      expect([aw!.frameWidth, aw!.frameHeight], merged).toEqual([base!.frameWidth, base!.frameHeight]);
      expect(aw!.frames, merged).toBe(base!.frames);
      expect(aw!.frameDurationsMs, merged).toEqual(base!.frameDurationsMs);
      expect(aw!.pivot, merged).toEqual(base!.pivot);
      expect(aw!.directions, merged).toEqual(base!.directions);
      expect(aw!.anchor, merged).toBe(base!.anchor);
      expect(aw!.impactFrame ?? null, merged).toBe(base!.impactFrame ?? null);
      expect(existsSync(`${ROOT}/fx/v3/${merged}.png`), merged).toBe(true);
    }
  });
});
const present = existsSync(`${ROOT}/fx/v3/katana_awaken_in.json`);

describe.skipIf(!present)('60라운드 계약 §21 — 최종 각성 재디자인 (실제 JSON)', () => {
  const body = read('player/v3/player_idle');

  it('각성 오버레이: 원 무기 오버레이와 같은 자리 (overlayPivot = 원 + pivotDelta = JSON pivot), 프레임·ms 같음', () => {
    expect(body).not.toBeNull();
    let checked = 0;
    const frames = new Set<string>();
    for (const w of WEAPONS)
      for (const r of awakenSheetRequests(w).filter((q) => q.category === 'weapons')) {
        const aw = read(`weapons/v3/${r.name}_${r.action}`);
        const base = read(`weapons/v3/${r.name}_${r.action.replace(/_awaken$/, '')}`);
        if (!aw || !base) continue;
        const d = aw.pivotDelta as { x: number; y: number };
        const pa = overlayPivot(aw, body!);
        const pb = overlayPivot(base, body!);
        expect({ x: pa.x - pb.x, y: pa.y - pb.y }, r.action).toEqual(d);
        expect(pa, r.action).toEqual(aw.pivot);
        expect(aw.weaponSheetPivot, r.action).toEqual(base.pivot);
        expect(aw.frames, r.action).toBe(base.frames);
        expect(frameDurations(aw), r.action).toEqual(frameDurations(base));
        frames.add(`${w}:${aw.frameWidth}x${aw.frameHeight}`);
        checked += 1;
      }
    expect(checked).toBeGreaterThan(50);
    // 틀: 칼 264 · 단검/활 256 · 대검 가로 +80·세로 +64
    expect(frames).toContain('katana:264x264');
    expect(frames).toContain('dagger:256x256');
    expect(frames).toContain('bow:256x256');
    for (const f of [...frames].filter((x) => x.startsWith('greatsword:')))
      expect(['320x336', '320x360', '360x376', '328x352']).toContain(f.split(':')[1]);
  });

  it('각성 순간 fx: 무기마다 12프레임 · 주인공 피벗을 따라감 · 각성 묶음에 있고 부팅 묶음에는 없다', () => {
    const boot = new Set(bootSheetRequests().map(requestKey));
    for (const w of WEAPONS) {
      const id = awakenInFxId(w);
      const def = read(`fx/v3/${id}`);
      expect(def, id).not.toBeNull();
      expect(def!.frames).toBe(12);
      expect(def!.anchor).toBe('player_pivot');
      expect(def!.followPlayer).toBe(true);
      const reqs = awakenSheetRequests(w).map(requestKey);
      expect(reqs).toContain(`fx/${id}_${FX_ACTION}`);
      expect(boot.has(`fx/${id}_${FX_ACTION}`)).toBe(false);
    }
  });

  it('각성 궤적 19종: 교체 표(무기 fx → <fx>_awaken) 중 실제 파일이 있는 것(갈래 합친 그림 제외) = 계약 목록, JSON awakenOf 일치', () => {
    for (const w of WEAPONS) {
      const map = awakenFxAliases(w);
      const real = Object.entries(map)
        .filter(([from, to]) => !MERGED_FROM.has(from) && existsSync(`${ROOT}/fx/v3/${to}.json`))
        .map(([from]) => from)
        .sort();
      expect(real, w).toEqual([...TRAILS[w]].sort());
      for (const from of real) {
        expect(
          String(read(`fx/v3/${map[from]}`)!.awakenOf)
            .split('/')
            .pop(),
          from,
        ).toBe(from);
        expect(awakenSheetRequests(w).map(requestKey)).toContain(`fx/${map[from]}_${FX_ACTION}`);
      }
    }
  });

  it('각성 궤적은 1:1 교체: 프레임·ms·행·앵커 같음 — 근접은 틀·피벗도 같고, 화살 3종은 틀이 길어도 피벗~앞 끝 거리·회전 같음', () => {
    for (const id of Object.values(TRAILS).flat()) {
      const base = read(`fx/v3/${id}`);
      const aw = read(`fx/v3/${id}_awaken`);
      expect(base && aw, id).toBeTruthy();
      expect(aw!.frames, id).toBe(base!.frames);
      expect(aw!.frameDurationsMs, id).toEqual(base!.frameDurationsMs);
      expect(aw!.directions, id).toEqual(base!.directions);
      expect(aw!.anchor, id).toBe(base!.anchor);
      expect(aw!.impactFrame ?? null, id).toBe(base!.impactFrame ?? null);
      if (ARROWS.has(id)) {
        expect(aw!.rotate, id).toBe(base!.rotate);
        expect(aw!.drawnFacing, id).toBe(base!.drawnFacing);
        expect(aw!.frameWidth, id).toBeGreaterThan(base!.frameWidth);
        // 화살촉(앞 끝)은 피벗에서 같은 거리 — 꼬리만 뒤로 길다
        expect(aw!.frameWidth - aw!.pivot.x, id).toBe(base!.frameWidth - base!.pivot.x);
        expect(aw!.pivot.y / aw!.frameHeight, id).toBeCloseTo(0.5, 1);
      } else {
        expect([aw!.frameWidth, aw!.frameHeight], id).toEqual([base!.frameWidth, base!.frameHeight]);
        expect(aw!.pivot, id).toEqual(base!.pivot);
      }
    }
  });
});
