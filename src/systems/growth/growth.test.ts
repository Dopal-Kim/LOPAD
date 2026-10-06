import { describe, expect, it } from 'vitest';
import { WEAPONS } from '../../data';
import { GROWTH, TRAITS, plainLine, validateGrowth } from '../../data/growth';
import type { GrowthData } from '../../data/growthTypes';
import { WeaponState } from '../weapon/weapons';
import {
  effectiveKind,
  growthLookOf,
  growthMarks,
  marksReached,
  nextMarkOf,
  pendingMarkOf,
  pickTraits,
  traitPool,
} from './growth';
import { growthMenu } from './growthMenu';
import { uiGrowth } from './uiGrowth';

const seq = (vals: number[]) => {
  let i = 0;
  return () => vals[i++ % vals.length];
};

describe('61 G P12 각성 게이지 눈금', () => {
  it('1층: 30 ◇ / 90 ◆ / 150 ◇ / 220 ◆ / 290 ◇ · 이후 70마다 단련', () => {
    const m = growthMarks(1, 8);
    expect(m.map((x) => `${x.at}${x.kind}`)).toEqual([
      '30trait',
      '90awaken1',
      '150trait',
      '220awaken2',
      '290trait',
      '360temper',
      '430temper',
      '500temper',
    ]);
    expect(growthMarks(null).length).toBe(5); // 시험장 = 1층 눈금
    expect(nextMarkOf(1, 0).at).toBe(30);
    expect(pendingMarkOf(1, 29, 0)).toBeNull();
    expect(pendingMarkOf(1, 95, 0)?.at).toBe(30);
    expect(pendingMarkOf(1, 95, 1)?.kind).toBe('awaken1');
    expect(pendingMarkOf(1, 95, 2)).toBeNull();
    expect(marksReached(1, 225)).toBe(4);
  });

  it('눈금 종류 보정: 각성 단계와 어긋나면 개성 · 2차 눈금인데 0단이면 1차 · 단련은 2차 뒤', () => {
    expect(effectiveKind('awaken1', 0)).toBe('awaken1');
    expect(effectiveKind('awaken1', 1)).toBe('trait');
    expect(effectiveKind('awaken2', 0)).toBe('awaken1');
    expect(effectiveKind('awaken2', 1)).toBe('awaken2');
    expect(effectiveKind('awaken2', 2)).toBe('trait');
    expect(effectiveKind('temper', 1)).toBe('trait');
    expect(effectiveKind('temper', 2)).toBe('temper');
  });

  it('검증: 1차가 2차보다 뒤면 거부 · 화면 문구에 숫자 금지', () => {
    const bad = JSON.parse(JSON.stringify(GROWTH)) as GrowthData;
    bad.marks['1'] = [
      { at: 30, kind: 'awaken2' },
      { at: 90, kind: 'awaken1' },
    ];
    expect(() => validateGrowth(bad, WEAPONS)).toThrow(/1차 각성이 2차/);
    expect(plainLine('검기 +1')).toBe(false);
    expect(plainLine('쓰러뜨리면 검기가 찬다')).toBe(true);
    for (const t of TRAITS) expect(plainLine(t.line), t.id).toBe(true);
  });
});

describe('개성 풀·제시', () => {
  it('풀 = 기본 8 + 고른 갈래 2 (가진 것 제외)', () => {
    expect(traitPool('katana', null, [])).toHaveLength(8);
    expect(traitPool('katana', 'mangetsu', [])).toHaveLength(10);
    expect(traitPool('katana', 'mangetsu', ['k_moonRelay', 'k_iaiWave'])).toHaveLength(8);
  });

  it('3장 제시: 갈래 개성 우선 1장 · 나머지는 같은 칸이 겹치지 않게', () => {
    for (let s = 0; s < 20; s++) {
      const pick = pickTraits(traitPool('dagger', 'hyakki', []), 3, seq([s / 20, 0.37, 0.71, 0.13]));
      expect(pick).toHaveLength(3);
      expect(pick[0].branch).toBe('hyakki');
      expect(new Set(pick.map((t) => t.id)).size).toBe(3);
      expect(new Set(pick.map((t) => t.verb)).size).toBe(3);
    }
    expect(pickTraits(traitPool('bow', null, []), 3, seq([0.5]))[0].branch).toBeUndefined();
  });
});

describe('성장 메뉴 (계약 UI §18)', () => {
  it('1차 각성 = 갈래 3장 (line.branch · verb) · 2차 = 내 갈래의 길 2장 · 개성 = 3장 · 단련 = [단련 / 개성 / 개성]', () => {
    const w = new WeaponState('greatsword', WEAPONS.greatsword);
    const a1 = growthMenu(w, 'awaken1', 1, seq([0.1]))!;
    expect(a1.lines.map((l) => l.kind)).toEqual(['awaken1', 'awaken1', 'awaken1']);
    expect(a1.lines.map((l) => l.branch?.id)).toEqual(['crush', 'weight', 'berserk']);
    expect(a1.lines[2].branch?.paths.map((p) => p.id)).toEqual(['bloodwind', 'ironpeak']);
    for (const l of a1.lines) expect(plainLine(l.label) && plainLine(l.detail ?? '')).toBe(true);
    w.choose('berserk');
    const a2 = growthMenu(w, 'awaken2', 1, seq([0.1]))!;
    expect(a2.lines.map((l) => l.path?.id)).toEqual(['bloodwind', 'ironpeak']);
    const tr = growthMenu(w, 'trait', 1, seq([0.3, 0.6, 0.9]))!;
    expect(tr.lines).toHaveLength(3);
    expect(tr.lines.every((l) => l.kind === 'trait' && l.verb && l.tags?.length === 1)).toBe(true);
    w.choose('ironpeak');
    const te = growthMenu(w, 'temper', 1, seq([0.3, 0.6]))!;
    expect(te.lines.map((l) => l.kind)).toEqual(['temper', 'trait', 'trait']);
    w.temper = 3;
    expect(growthMenu(w, 'temper', 1, seq([0.3]))!.lines.every((l) => l.kind === 'trait')).toBe(true);
  });

  it('고를 개성이 하나도 없으면 null (눈금만 지나간다)', () => {
    const w = new WeaponState('bow', WEAPONS.bow);
    w.traits = traitPool('bow', null, []).map((t) => t.id);
    expect(growthMenu(w, 'trait', 1, seq([0.5]))).toBeNull();
  });
});

describe('스냅샷 growth · 각성 외형', () => {
  it('게이지·눈금(done)·다음 눈금·갈래 3·처음 안내', () => {
    const w = new WeaponState('katana', WEAPONS.katana);
    w.gain(100);
    w.marksDone = 2;
    w.choose('mangetsu');
    w.addTrait('k_moonRelay');
    const g = uiGrowth(w, 1, { guides: ['trait'] });
    expect(g.gauge).toBe(100);
    expect(g.marks.filter((m) => m.done).map((m) => m.at)).toEqual([30, 90]);
    expect(g.next).toEqual({ at: 150, kind: 'trait', done: false });
    expect(g.stage).toBe(1);
    expect(g.branch).toBe('mangetsu');
    expect(g.branches.map((b) => b.id)).toEqual(['senpu', 'kabuto', 'mangetsu']);
    expect(g.traits.map((t) => t.id)).toEqual(['k_moonRelay']);
    expect(g.firstTime).toEqual({ trait: false, awaken1: true, awaken2: true });
    expect(g.temper).toEqual({ n: 0, max: 3 });
  });

  it('외형: 0단 없음 · 1차 = 갈래 (셋째 갈래 legacy) · 2차 = 길 강조색', () => {
    const w = new WeaponState('dagger', WEAPONS.dagger);
    expect(growthLookOf(w)).toBeNull();
    w.choose('hyakki');
    expect(growthLookOf(w)).toEqual({ branch: 'hyakki', stage: 1, path: null, tint: null, legacy: true });
    w.choose('onibi');
    const look = growthLookOf(w)!;
    expect(look.stage).toBe(2);
    expect(look.path).toBe('onibi');
    // 61 단계 6: 길 색은 아트 looks/dagger.json pathTint (단검 독 계열) 로 맞춤
    expect(look.tint).toBe((248 << 16) | (120 << 8) | 255);
    const k = new WeaponState('katana', WEAPONS.katana);
    k.choose('iai');
    expect(growthLookOf(k)?.legacy).toBe(false);
  });
});
