import { describe, expect, it } from 'vitest';
import { REACTION } from '../core/Constants';
import { WEAPONS } from '../data';
import {
  StreakCounter,
  bowlDamage,
  defaultReaction,
  effectivePoise,
  extendAir,
  fallOutcome,
  knockDistancePx,
  overcomesPoise,
  strikeReaction,
  wallSlamDamage,
} from './reactions';

const R = (id: string) => WEAPONS[id].feel?.reaction;

describe('P19 넉백 단계 함수 (무기 반응 모양)', () => {
  it('칼: 1타 올려베기 띄움(버팀 0만) · 2타 1단계 · 3타 찌르기 2단계 · 홀드 발도 3단계', () => {
    expect(strikeReaction(R('katana'), { kind: 'attack', comboIndex: 0 })).toMatchObject({ tier: 1, launch: true });
    expect(strikeReaction(R('katana'), { kind: 'attack', comboIndex: 1 })).toMatchObject({ tier: 1, launch: false });
    expect(strikeReaction(R('katana'), { kind: 'attack', comboIndex: 2, heavy: true }).tier).toBe(2);
    expect(strikeReaction(R('katana'), { kind: 'attack', move: 'iai_draw' }).tier).toBe(3);
    expect(strikeReaction(R('katana'), { kind: 'attack', comboIndex: 0 }).launchMaxPoise).toBe(0);
  });

  it('대검: 가로 1 · 세로 2 · 태클·차지 3 (날림 — 벽꽝·볼링의 주력) · 버티기 올려베기 띄움', () => {
    expect(strikeReaction(R('greatsword'), { kind: 'attack', comboIndex: 0 }).tier).toBe(1);
    expect(strikeReaction(R('greatsword'), { kind: 'attack', comboIndex: 1 }).tier).toBe(2);
    expect(strikeReaction(R('greatsword'), { kind: 'dashAttack', move: 'tackle', heavy: true }).tier).toBe(3);
    expect(strikeReaction(R('greatsword'), { kind: 'attack', charge: 2, heavy: true }).tier).toBe(3);
    expect(strikeReaction(R('greatsword'), { kind: 'attack', move: 'brace_upswing' }).launch).toBe(true);
    expect(strikeReaction(R('greatsword'), { kind: 'dashAttack', heavy: true }).tier).toBeGreaterThanOrEqual(
      REACTION.BOWL.MIN_TIER,
    );
  });

  it('단검: 매 타 버팀 무시 1 (힘 = 단계 + 1) · 등 뒤 찌르기 띄움', () => {
    const r = strikeReaction(R('dagger'), { kind: 'attack', comboIndex: 1 });
    expect(r.power).toBe(r.tier + 1);
    expect(strikeReaction(R('dagger'), { kind: 'attack', move: 'backstab', heavy: true }).launch).toBe(true);
  });

  it('활: 완벽 놓기 2단계 (벽에 닿으면 벽꽝 = 꿰어 박기 기본기)', () => {
    expect(strikeReaction(R('bow'), { kind: 'attack', bowPower: 'perfect' }).tier).toBe(2);
    expect(strikeReaction(R('bow'), { kind: 'attack' }).tier).toBe(1);
  });

  it('데이터 없는 타격: 막타 2 · 그 밖 1', () => {
    expect(defaultReaction(true).tier).toBe(2);
    expect(defaultReaction(false)).toMatchObject({ tier: 1, launch: false, power: 1 });
  });

  it('넉백 거리: 0.6·1.5·3·6칸, 보스 ¼ · 정예 ½ · 무기 무게는 1단계에만', () => {
    expect(knockDistancePx(1, 16)).toBeCloseTo(9.6);
    expect(knockDistancePx(2, 16)).toBeCloseTo(24);
    expect(knockDistancePx(3, 16)).toBeCloseTo(48);
    expect(knockDistancePx(4, 16)).toBeCloseTo(96);
    expect(knockDistancePx(3, 16, { boss: true })).toBeCloseTo(12);
    expect(knockDistancePx(3, 16, { elite: true })).toBeCloseTo(24);
    expect(knockDistancePx(1, 16, { weaponMult: 2 })).toBeCloseTo(19.2);
    expect(knockDistancePx(2, 16, { weaponMult: 2 })).toBeCloseTo(24);
  });
});

describe('P19 버팀·벽꽝·볼링·낙하·띄움·연속 처치', () => {
  it('버팀: 힘 > 버팀이면 움찔 · 정예 ×3', () => {
    expect(overcomesPoise(1, 0)).toBe(true);
    expect(overcomesPoise(1, 1)).toBe(false);
    expect(overcomesPoise(2, 1)).toBe(true);
    expect(effectivePoise(1, true)).toBe(3);
    expect(effectivePoise(0, true)).toBe(0);
  });

  it('벽꽝 피해 = 타 피해 × 0.6 × 속도비 (하한 0.5) · 볼링 = × 0.4 · 최소 1', () => {
    expect(wallSlamDamage(10, 1)).toBe(6);
    expect(wallSlamDamage(10, 0.1)).toBe(3);
    expect(wallSlamDamage(1, 0.5)).toBe(1);
    expect(bowlDamage(10)).toBe(4);
    expect(bowlDamage(1)).toBe(1);
  });

  it('밀어 떨어뜨리기: 일반 즉사 · 정예 30% · 보스 없음', () => {
    expect(fallOutcome({ isBoss: false, elite: false })).toBe('die');
    expect(fallOutcome({ isBoss: false, elite: true })).toBe('elite');
    expect(fallOutcome({ isBoss: true, elite: false })).toBe('none');
  });

  it('띄움 체공 연장 +200ms 최대 2회', () => {
    let a = { until: 500, extends: 0 };
    a = extendAir(a);
    a = extendAir(a);
    expect(a).toEqual({ until: 900, extends: 2 });
    expect(extendAir(a)).toEqual(a);
  });

  it('연속 처치: 1.5초 안이면 이어지고 넘으면 1부터', () => {
    const s = new StreakCounter();
    expect(s.onKill(0)).toBe(1);
    expect(s.onKill(1000)).toBe(2);
    expect(s.onKill(2400)).toBe(3);
    expect(s.onKill(4000)).toBe(1);
  });
});
