import { describe, expect, it } from 'vitest';
import { FEEL } from '../core/Constants';
import { WEAPONS } from '../data';
import {
  hitShake,
  isBackswing,
  isHeavyStrike,
  shakesOnHit,
  sparkOrientation,
  weaponHitSheet,
  weaponHitstopMs,
} from './hitFeel';

describe('hitFeel: 55라운드 Q6 히트스톱 · Q10 막타', () => {
  it('무기별 히트스톱 (단검 30·칼 45·대검 80·활 25), 막타·치명타 ×1.8', () => {
    expect(weaponHitstopMs(WEAPONS.dagger.feel, false)).toBe(30);
    expect(weaponHitstopMs(WEAPONS.katana.feel, false)).toBe(45);
    expect(weaponHitstopMs(WEAPONS.greatsword.feel, false)).toBe(80);
    expect(weaponHitstopMs(WEAPONS.bow.feel, false)).toBe(25);
    expect(weaponHitstopMs(WEAPONS.greatsword.feel, true)).toBe(144);
    expect(weaponHitstopMs(WEAPONS.katana.feel, true)).toBe(81);
    expect(weaponHitstopMs(undefined, false)).toBe(FEEL.HITSTOP.WEAPON_FALLBACK_MS);
  });

  it('막타 = 연격 마지막 타 · 대쉬 공격', () => {
    expect(isHeavyStrike({ kind: 'attack', comboIndex: 2, comboCount: 3 })).toBe(true);
    expect(isHeavyStrike({ kind: 'attack', comboIndex: 1, comboCount: 3 })).toBe(false);
    expect(isHeavyStrike({ kind: 'dashAttack', comboIndex: 0, comboCount: 3 })).toBe(true);
    expect(isHeavyStrike({ kind: 'attack' })).toBe(false);
  });

  it('스파크 시트: 막타면 _heavy → 일반, 없으면 null', () => {
    const has = (ids: string[]) => (id: string) => ids.includes(id);
    expect(weaponHitSheet('katana', true, has(['hit_katana', 'hit_katana_heavy']))).toBe('hit_katana_heavy');
    expect(weaponHitSheet('katana', false, has(['hit_katana', 'hit_katana_heavy']))).toBe('hit_katana');
    expect(weaponHitSheet('katana', true, has(['hit_katana']))).toBe('hit_katana');
    expect(weaponHitSheet('katana', true, has([]))).toBeNull();
  });

  it('흔들림: 막타·치명타, 대검은 모든 적중. 값은 shakeHint → 기본', () => {
    expect(shakesOnHit(WEAPONS.katana.feel, false)).toBe(false);
    expect(shakesOnHit(WEAPONS.katana.feel, true)).toBe(true);
    expect(shakesOnHit(WEAPONS.greatsword.feel, false)).toBe(true);
    expect(hitShake({ shakeHint: { px: 4, ms: 90, note: '' } })).toEqual({ px: 4, ms: 90 });
    expect(hitShake(null)).toEqual({ px: FEEL.SHAKE.HEAVY_HIT.PX, ms: FEEL.SHAKE.HEAVY_HIT.MS });
  });

  it('스파크 회전: 진행 방향 각도, 왼쪽이면 위아래 뒤집기, 되돌아 휘두름은 한 번 더', () => {
    expect(sparkOrientation(1, 0, { flipAllowed: true })).toEqual({ angle: 0, flipY: false });
    const left = sparkOrientation(-1, 0, { flipAllowed: true });
    expect(left.angle).toBeCloseTo(Math.PI);
    expect(left.flipY).toBe(true);
    expect(sparkOrientation(1, 0, { flipAllowed: true, backswing: true }).flipY).toBe(true);
    expect(sparkOrientation(-1, 0, { flipAllowed: false }).flipY).toBe(false);
    expect(sparkOrientation(0, 1, { drawnFacing: 'down' }).angle).toBeCloseTo(0);
  });

  it('Q28 왼쪽 회전 연격: 왼쪽이어도 바로 세우지 않고 되돌아 휘두름만 뒤집는다', () => {
    expect(sparkOrientation(-1, 0, { flipAllowed: true, rotateLeft: true }).flipY).toBe(false);
    expect(sparkOrientation(-1, 0, { flipAllowed: true, rotateLeft: true, backswing: true }).flipY).toBe(true);
    expect(sparkOrientation(1, 0, { flipAllowed: true, rotateLeft: true, backswing: true }).flipY).toBe(true);
  });

  it('칼 K-A 되돌아 휘두름은 데이터에서: 1타(+70→−40)만, 2타·3타(−75→+75, Q26)·잔상은 아님', () => {
    const k = WEAPONS.katana.combo!;
    const back = k.hits.map((h) => {
      const s = h.hitShape!;
      return s.kind === 'arc' ? isBackswing({ kind: 'arc', fromDeg: s.fromDeg, toDeg: s.toDeg }) : false;
    });
    expect(back).toEqual([true, false, false]);
    // 잔상 베기는 같은 호(followUps.hitShape 없음 → 3타 모양)
    expect(k.hits[2].followUps?.[0].hitShape).toBeUndefined();
  });
});

describe('hitFeel: 되돌아 휘두름은 판정 모양에서 읽는다', () => {
  it('호가 반대로 훑으면 true, 찌르기·원형·없음은 false', () => {
    expect(isBackswing({ kind: 'arc', fromDeg: 70, toDeg: -70, arcDeg: 140 })).toBe(true);
    expect(isBackswing({ kind: 'arc', fromDeg: -70, toDeg: 70, arcDeg: 140 })).toBe(false);
    expect(isBackswing({ kind: 'arc', fromDeg: 180, toDeg: -180, arcDeg: 360 })).toBe(false);
    expect(isBackswing({ kind: 'thrust' })).toBe(false);
    expect(isBackswing(null)).toBe(false);
  });
});
