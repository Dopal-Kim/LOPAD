import { describe, expect, it } from 'vitest';
import { WEAPONS } from '../../data';
import { allSheetRequests, bootSheetRequests, bossSheetRequests, requestKey, weaponSheetRequests } from './sheetSets';

describe('57라운드 A2 로드 묶음 (부팅 + 고른 무기)', () => {
  const ids = Object.keys(WEAPONS);

  it('부팅 묶음 + 모든 무기 묶음 = 예전 부팅 목록 (빠지거나 늘어난 시트 없음)', () => {
    const before = new Set(allSheetRequests().map(requestKey));
    const after = new Set(
      [...bootSheetRequests(), ...bossSheetRequests(), ...ids.flatMap(weaponSheetRequests)].map(requestKey),
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
});
