import { describe, expect, it } from 'vitest';
import { WEAPONS } from '../../data';
import { allSheetRequests, bootSheetRequests, requestKey, weaponSheetRequests } from './sheetSets';

describe('57라운드 A2 로드 묶음 (부팅 + 고른 무기)', () => {
  const ids = Object.keys(WEAPONS);

  it('부팅 묶음 + 모든 무기 묶음 = 예전 부팅 목록 (빠지거나 늘어난 시트 없음)', () => {
    const before = new Set(allSheetRequests().map(requestKey));
    const after = new Set([...bootSheetRequests(), ...ids.flatMap(weaponSheetRequests)].map(requestKey));
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

  it('모르는 무기는 빈 목록', () => {
    expect(weaponSheetRequests('nope')).toEqual([]);
  });
});
