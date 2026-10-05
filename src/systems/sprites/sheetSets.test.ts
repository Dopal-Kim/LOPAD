import { describe, expect, it } from 'vitest';
import { WEAPONS } from '../../data';
import { bossLazyRequests } from '../boss/bossSheets';
import { bossIdsInScope } from '../../data/scope';
import {
  allSheetRequests,
  bootSheetRequests,
  bossSheetRequests,
  floorGatedFxIds,
  requestKey,
  runAllowsTier2,
  weaponSheetRequests,
} from './sheetSets';

describe('57라운드 A2 로드 묶음 (부팅 + 고른 무기)', () => {
  const ids = Object.keys(WEAPONS);

  it('부팅 묶음 + 모든 무기 묶음 = 예전 부팅 목록 (빠지거나 늘어난 시트 없음)', () => {
    const before = new Set(allSheetRequests().map(requestKey));
    const after = new Set(
      [
        ...bootSheetRequests(),
        ...bossSheetRequests(),
        ...bossLazyRequests(bossIdsInScope()),
        ...ids.flatMap((id) => weaponSheetRequests(id)),
      ].map(requestKey),
    );
    expect([...after].sort()).toEqual([...before].sort());
  });

  it('부팅 묶음에는 무기 이름이 붙은 몸·무기·이펙트 시트가 없다 (공용 보조 연출 고정 목록 제외)', () => {
    const boot = bootSheetRequests();
    expect(boot.some((r) => r.category === 'weapons')).toBe(false);
    for (const id of ids) {
      const own = weaponSheetRequests(id).map(requestKey);
      for (const k of own) expect(boot.map(requestKey)).not.toContain(k);
    }
    // 기본 몸 동작은 부팅에
    expect(boot.map(requestKey)).toContain('player/player_idle');
  });

  it('무기 묶음은 그 무기 것만 (다른 무기 이름의 시트가 섞이지 않는다)', () => {
    for (const id of ids) {
      const others = ids.filter((o) => o !== id);
      for (const r of weaponSheetRequests(id)) {
        const label = `${r.name}_${r.action}`;
        for (const o of others) expect(label.startsWith(`${o}_`) || label.includes(`player_${o}_`)).toBe(false);
      }
      expect(weaponSheetRequests(id).some((r) => r.category === 'weapons' && r.name === id)).toBe(true);
    }
  });

  it('57라운드 Q38: 단검 전용 낙인·가속 폭발 fx 3종은 단검 묶음 (부팅·다른 무기에는 없다 — 61라운드 식음 fx 삭제)', () => {
    const own = ['dagger_brand_mark', 'dagger_brand_burst', 'dagger_overheat_burst'];
    expect(weaponSheetRequests('dagger').some((r) => r.name === 'dagger_overheat_cool')).toBe(false);
    const names = (list: ReturnType<typeof bootSheetRequests>) =>
      list.filter((r) => r.category === 'fx').map((r) => r.name);
    for (const n of own) {
      expect(names(weaponSheetRequests('dagger'))).toContain(n);
      expect(names(bootSheetRequests())).not.toContain(n);
      for (const o of ids.filter((x) => x !== 'dagger')) expect(names(weaponSheetRequests(o))).not.toContain(n);
    }
  });

  it('61라운드 단계 2: 보스 몸·보스방 시트는 부팅 묶음이 아니라 보스 묶음 (보스 노드 preload)', () => {
    const boot = bootSheetRequests();
    expect(boot.some((r) => r.category === 'bosses')).toBe(false);
    const boss = bossSheetRequests();
    expect(boss.some((r) => r.category === 'bosses')).toBe(true);
    const bootKeys = new Set(boot.map(requestKey));
    expect(boss.every((r) => !bootKeys.has(requestKey(r)))).toBe(true);
  });

  it('모르는 무기는 빈 목록', () => {
    expect(weaponSheetRequests('nope')).toEqual([]);
  });

  it('61 E VRAM: 1층판에서 꺼진 세트 단계 fx(간파 6 정적 파동)는 어느 묶음에도 없다', () => {
    expect(floorGatedFxIds().has('set_stasis_wave')).toBe(true);
    const all = [...bootSheetRequests(), ...ids.flatMap((id) => weaponSheetRequests(id))];
    expect(all.some((r) => r.name === 'set_stasis_wave')).toBe(false);
  });

  it('61 E VRAM: 1층 런은 2단 갈래 그림을 올리지 않는다 (시험장은 전부)', () => {
    expect(runAllowsTier2()).toBe(false);
    const run = new Set(weaponSheetRequests('greatsword', false).map(requestKey));
    const lab = weaponSheetRequests('greatsword', true).map(requestKey);
    expect(run.has('fx/greatsword_giant_ring_fx')).toBe(false);
    expect(lab).toContain('fx/greatsword_giant_ring_fx');
    expect(run.has('fx/greatsword_quake_ring_fx')).toBe(true);
  });

  it('61 E 보스 묶음: 파훼 표시 작은 시트는 보스 묶음, 등장 동작도 보스 묶음, 국면 전환 들이켜기·림·결정타는 지연 묶음', () => {
    const boss = bossSheetRequests().map(requestKey);
    for (const k of ['fx/boss1_cup_glint_fx', 'fx/boss1_break_daze_fx', 'structures/boss1_rolling_barrel_rim_st'])
      expect(boss).toContain(k);
    expect(boss).toContain('bosses/stage1_intro');
    for (const k of ['bosses/stage1_phase_drink', 'bosses/stage1_idle_rim', 'fx/boss1_finisher_slash_fx'])
      expect(boss).not.toContain(k);
  });
});
