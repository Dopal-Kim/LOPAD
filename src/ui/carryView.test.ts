import { describe, expect, it } from 'vitest';
import { carryKey, carryView } from './carryView';

describe('carryView (53라운드 F 넣기/뽑기)', () => {
  it('값이 없으면 숨김', () => {
    expect(carryView(null)).toBeNull();
    expect(carryView(undefined)).toBeNull();
    expect(carryView({} as never)).toBeNull();
  });
  it('넣은 상태 + 첫 타 준비', () => {
    expect(carryView({ drawn: false, firstStrike: '발도', key: 'F' })).toEqual({
      sheathed: true,
      ready: '발도',
      key: 'F',
    });
  });
  it('뽑은 상태는 첫 타 이름이 와도 준비 아님', () => {
    expect(carryView({ drawn: true, firstStrike: '끌어내기', key: 'F' })).toEqual({
      sheathed: false,
      ready: null,
      key: 'F',
    });
  });
  it('넣었지만 보너스 없음', () => {
    expect(carryView({ drawn: false, firstStrike: null, key: 'F' })?.ready).toBeNull();
    expect(carryView({ drawn: false, firstStrike: '  ', key: 'F' })?.ready).toBeNull();
  });
  it('표시 키', () => {
    expect(carryKey(null)).toBe('');
    expect(carryKey(carryView({ drawn: false, firstStrike: '발도', key: 'F' }))).toBe('F|1|발도');
  });
});
