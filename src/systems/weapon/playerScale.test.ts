import { describe, expect, it } from 'vitest';
import { PLAYER_DATA, WEAPONS } from '../../data';
import { HIT_ORIGIN_BASE_PX, PLAYER_HIT_ORIGIN_UP_PX, PLAYER_HIT_SCALE, weaponRangeScale } from './playerScale';
import { WeaponState } from './weapons';

describe('58라운드 Q2 주인공·무기 그림 배율', () => {
  it('데이터 render·hit (약 1.25배) · 판정 원점은 그림 배율만큼 올라간다', () => {
    expect(PLAYER_DATA.drawScale).toMatchObject({ render: 1.25, hit: 1.25 });
    expect(PLAYER_HIT_ORIGIN_UP_PX).toBeCloseTo(HIT_ORIGIN_BASE_PX * 1.25);
  });

  it('근접 무기만 판정 배율을 곱한다 (활 화살 크기는 그대로) · 이동 충돌 크기는 그대로', () => {
    expect(weaponRangeScale(new WeaponState('katana', WEAPONS.katana))).toBeCloseTo(PLAYER_HIT_SCALE);
    expect(weaponRangeScale(new WeaponState('bow', WEAPONS.bow))).toBe(1);
    expect(PLAYER_DATA.size).toEqual([16, 16]);
  });
});
