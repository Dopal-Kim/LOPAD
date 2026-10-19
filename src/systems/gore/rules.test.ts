import { describe, expect, it } from 'vitest';
import {
  CappedList,
  cutOf,
  enemyWoundStage,
  execDistance,
  executeVariant,
  goreCount,
  goreVariant,
  heroWoundStage,
  pickDeathVariant,
  stampTarget,
  type DeathContext,
  type ExecCandidate,
} from './rules';

describe('P21 상처 단계 (dark-brutal §3)', () => {
  it('주인공: > 75% 0 · ≤ 75% 1 · ≤ 50% 2 · ≤ 25% 3, 회복하면 내려간다', () => {
    expect(heroWoundStage(100, 100)).toBe(0);
    expect(heroWoundStage(76, 100)).toBe(0);
    expect(heroWoundStage(75, 100)).toBe(1);
    expect(heroWoundStage(50, 100)).toBe(2);
    expect(heroWoundStage(25, 100)).toBe(3);
    expect(heroWoundStage(0, 100)).toBe(3);
    expect(heroWoundStage(60, 100)).toBe(1);
  });

  it('적: ≤ 66% 1 · ≤ 33% 2 · 스탬프 수 2~3 / 4~6', () => {
    expect(enemyWoundStage(67, 100)).toBe(0);
    expect(enemyWoundStage(66, 100)).toBe(1);
    expect(enemyWoundStage(33, 100)).toBe(2);
    expect(stampTarget(0, 0.9)).toBe(0);
    expect(stampTarget(1, 0)).toBe(2);
    expect(stampTarget(1, 0.999)).toBe(3);
    expect(stampTarget(2, 0)).toBe(4);
    expect(stampTarget(2, 0.999)).toBe(6);
  });

  it('적중 결: 칼 베기 · 대검 막타 부숨 · 단검 찌르기 · 활 꿰뚫기 · 환경 부숨', () => {
    expect(cutOf('katana', false)).toBe('slash');
    expect(cutOf('greatsword', true)).toBe('crush');
    expect(cutOf('greatsword', false)).toBe('slash');
    expect(cutOf('dagger', true)).toBe('stab');
    expect(cutOf('bow', false)).toBe('pierce');
    expect(cutOf(null, false)).toBe('crush');
  });
});

describe('P21 사망 변형 (§5)', () => {
  const base: DeathContext = {
    weapon: null,
    overkillRatio: 0,
    wallNear: false,
    fire: false,
    drown: false,
    boss: false,
  };
  it('대검·칼 막타 넘친 피해 ≥ 30% → bisect·behead, 그 아래면 collapse', () => {
    expect(pickDeathVariant({ ...base, weapon: 'greatsword', overkillRatio: 0.3 })).toBe('bisect');
    expect(pickDeathVariant({ ...base, weapon: 'katana', overkillRatio: 0.31 })).toBe('behead');
    expect(pickDeathVariant({ ...base, weapon: 'katana', overkillRatio: 0.29 })).toBe('collapse');
  });
  it('활 + 벽 가까이 → pinned · 불 → burn · 물 → drown · 처형 · 군주', () => {
    expect(pickDeathVariant({ ...base, weapon: 'bow', wallNear: true })).toBe('pinned');
    expect(pickDeathVariant({ ...base, weapon: 'bow' })).toBe('collapse');
    expect(pickDeathVariant({ ...base, fire: true })).toBe('burn');
    expect(pickDeathVariant({ ...base, drown: true, fire: true })).toBe('drown');
    expect(pickDeathVariant({ ...base, weapon: 'dagger', execute: 'collapse' })).toBe('collapse');
    expect(pickDeathVariant({ ...base, weapon: 'katana', execute: executeVariant('katana') })).toBe('behead');
    expect(pickDeathVariant({ ...base, boss: true, weapon: 'greatsword', overkillRatio: 2 })).toBe('collapse');
  });
  it('고어 1 은 절단 → collapse, 고어 0 은 모두 collapse', () => {
    expect(goreVariant('bisect', 2)).toBe('bisect');
    expect(goreVariant('bisect', 1)).toBe('collapse');
    expect(goreVariant('behead', 1)).toBe('collapse');
    expect(goreVariant('pinned', 1)).toBe('pinned');
    expect(goreVariant('burn', 0)).toBe('collapse');
  });
  it('처형 변형: 칼 behead · 대검 bisect · 단검 collapse · 활 pinned', () => {
    expect(['katana', 'greatsword', 'dagger', 'bow'].map((w) => executeVariant(w as never))).toEqual([
      'behead',
      'bisect',
      'collapse',
      'pinned',
    ]);
  });
});

describe('P21 처형 조건 (§4)', () => {
  const T = 16;
  const c: ExecCandidate = { boss: false, elite: false, hp: 10, maxHp: 100, broken: false, dx: 12, dy: 0, radius: 6 };
  it('HP ≤ 15% 또는 버팀 깨짐 · 앞 부채꼴 1.2칸 안', () => {
    expect(execDistance(c, 0, T)).toBe(12);
    expect(execDistance({ ...c, hp: 16 }, 0, T)).toBeNull();
    expect(execDistance({ ...c, hp: 80, broken: true }, 0, T)).toBe(12);
    // 등 뒤
    expect(execDistance(c, Math.PI, T)).toBeNull();
    // 1.2칸(19.2px) + 몸 반지름 6 을 넘음
    expect(execDistance({ ...c, dx: 26 }, 0, T)).toBeNull();
    expect(execDistance({ ...c, dx: 25 }, 0, T)).toBe(25);
  });
  it('군주 제외 · 엘리트는 HP ≤ 15% 일 때만', () => {
    expect(execDistance({ ...c, boss: true }, 0, T)).toBeNull();
    expect(execDistance({ ...c, elite: true, hp: 80, broken: true }, 0, T)).toBeNull();
    expect(execDistance({ ...c, elite: true, hp: 15 }, 0, T)).toBe(12);
  });
});

describe('P21 데칼·시체 상한 (§6)', () => {
  it('넘치면 오래된 것부터 돌려준다', () => {
    const l = new CappedList<number>(3);
    expect(l.push(1)).toEqual([]);
    l.push(2);
    l.push(3);
    expect(l.push(4)).toEqual([1]);
    expect(l.size).toBe(3);
    l.remove(3);
    expect(l.push(5)).toEqual([]);
    expect(l.clear()).toEqual([2, 4, 5]);
    expect(l.size).toBe(0);
  });
  it('160 장 상한', () => {
    const l = new CappedList<number>(160);
    let evicted = 0;
    for (let i = 0; i < 200; i++) evicted += l.push(i).length;
    expect(l.size).toBe(160);
    expect(evicted).toBe(40);
  });
  it('고어 피 양: 2 그대로 · 1 은 1/3 · 0 은 없음', () => {
    expect(goreCount(3, 2, 0.5)).toBe(3);
    expect(goreCount(3, 1, 0.5)).toBe(1);
    expect(goreCount(2, 1, 0.1)).toBe(1);
    expect(goreCount(2, 1, 0.9)).toBe(0);
    expect(goreCount(5, 0, 0)).toBe(0);
  });
});
