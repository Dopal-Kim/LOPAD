import { describe, expect, it } from 'vitest';
import {
  GORE_NOTICE_KEY,
  crackPaths,
  executableOf,
  executableOffUid,
  executeMsOf,
  goreNoticeSeen,
  lowHpAlpha,
  lowHpOf,
  markGoreNoticeSeen,
  resetGoreNoticePage,
  snapshotWound,
  stepGoreIndex,
  streakKey,
  woundOf,
} from './p21View';
import { LOW_HP_VIG } from './themeP21';

const memStore = (): Pick<Storage, 'getItem' | 'setItem'> & { data: Map<string, string> } => {
  const data = new Map<string, string>();
  return { data, getItem: (k) => data.get(k) ?? null, setItem: (k, v) => void data.set(k, v) };
};

describe('P21 잔혹 묘사 안내 (한 번)', () => {
  it('저장소에 표시하면 다음부터 안 뜬다', () => {
    resetGoreNoticePage();
    const st = memStore();
    expect(goreNoticeSeen(st)).toBe(false);
    markGoreNoticeSeen(st);
    expect(st.data.get(GORE_NOTICE_KEY)).toBe('1');
    resetGoreNoticePage();
    expect(goreNoticeSeen(st)).toBe(true);
  });
  it('저장소가 막혀도 터지지 않고, 이번 페이지에서는 기억한다', () => {
    resetGoreNoticePage();
    const bad = {
      getItem: () => {
        throw new Error('blocked');
      },
      setItem: () => {
        throw new Error('blocked');
      },
    };
    expect(goreNoticeSeen(bad)).toBe(false);
    markGoreNoticeSeen(bad);
    expect(goreNoticeSeen(bad)).toBe(true);
    expect(goreNoticeSeen(null)).toBe(true);
    resetGoreNoticePage();
    expect(goreNoticeSeen(null)).toBe(false);
  });
  it('갈래 이동은 끝에서 멈춘다', () => {
    expect(stepGoreIndex(0, -1)).toBe(0);
    expect(stepGoreIndex(0, 1)).toBe(1);
    expect(stepGoreIndex(2, 1)).toBe(2);
  });
});

describe('P21 상흔', () => {
  it('페이로드·스냅샷 읽기 (자르고, 틀리면 null)', () => {
    expect(woundOf({ stage: 2, arrows: 3 })).toEqual({ stage: 2, arrows: 3 });
    expect(woundOf({ stage: 9, arrows: 40 })).toEqual({ stage: 3, arrows: 5 });
    expect(woundOf({ stage: 1 })).toEqual({ stage: 1, arrows: 0 });
    expect(woundOf({ arrows: 1 })).toBeNull();
    expect(woundOf(null)).toBeNull();
    expect(snapshotWound({ player: { wound: { stage: 1, arrows: 2 } } })).toEqual({ stage: 1, arrows: 2 });
    expect(snapshotWound({})).toBeNull();
  });
  it('균열은 늘 같은 모양이고 막대 안에 머문다, 단계가 오르면 앞 균열을 그대로 둔다', () => {
    const a = crackPaths(3, 120, 14);
    expect(crackPaths(3, 120, 14)).toEqual(a);
    expect(crackPaths(5, 120, 14).slice(0, 3)).toEqual(a);
    expect(crackPaths(0, 120, 14)).toEqual([]);
    for (const pts of crackPaths(5, 120, 14))
      for (const p of pts) {
        expect(p.x).toBeGreaterThanOrEqual(0);
        expect(p.x).toBeLessThan(120);
        expect(p.y).toBeGreaterThanOrEqual(0);
        expect(p.y).toBeLessThan(14);
      }
  });
});

describe('P21 저HP 비네트', () => {
  it('on 읽기', () => {
    expect(lowHpOf({ on: true, ratio: 0.2 })).toBe(true);
    expect(lowHpOf({ on: false })).toBe(false);
    expect(lowHpOf({})).toBeNull();
  });
  it('섬광 끄면 고정, 켜면 박동 사이 최소 ~ 박동 꼭대기 최대', () => {
    expect(lowHpAlpha(123, false, LOW_HP_VIG)).toBe(LOW_HP_VIG.alphaFixed);
    expect(lowHpAlpha(0, true, LOW_HP_VIG)).toBeCloseTo(LOW_HP_VIG.alphaMax, 2);
    const between = lowHpAlpha((0.6 / LOW_HP_VIG.hz) * 1000, true, LOW_HP_VIG);
    expect(between).toBeCloseTo(LOW_HP_VIG.alphaMin, 2);
    const second = lowHpAlpha((LOW_HP_VIG.beat2 / LOW_HP_VIG.hz) * 1000, true, LOW_HP_VIG);
    expect(second).toBeGreaterThan(between);
    expect(second).toBeLessThan(LOW_HP_VIG.alphaMax);
  });
});

describe('P21 연속 처치 낱말', () => {
  it('2 · 4 · 7 부터', () => {
    expect([2, 3, 4, 6, 7, 12].map(streakKey)).toEqual([
      'streak2',
      'streak2',
      'streak4',
      'streak4',
      'streak7',
      'streak7',
    ]);
  });
});

describe('P21 처형 표식', () => {
  it('스냅샷 자리 · 꺼짐 이벤트 · 처형 길이', () => {
    expect(executableOf({ executable: { uid: 4, screen: { x: 10, y: 20 } } })).toEqual({ uid: 4, x: 10, y: 20 });
    expect(executableOf({ executable: null })).toBeNull();
    expect(executableOf({})).toBeNull();
    expect(executableOffUid({ uid: 4, on: false })).toBe(4);
    expect(executableOffUid({ uid: 4, on: true })).toBeNull();
    expect(executeMsOf({ ms: 600 })).toBe(600);
    expect(executeMsOf({})).toBe(450);
  });
});
