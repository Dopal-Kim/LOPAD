import { describe, expect, it } from 'vitest';
import { PERSONALITY, WEAPONS } from '../data';
import { STROKE_KEYS, chooseWeapon, strokeFeatures, type Stroke } from './personality';

const line = (len: number, ms: number): Stroke => [
  { x: 0, y: 0, t: 0 },
  { x: len / 2, y: 0, t: ms / 2 },
  { x: len, y: 0, t: ms },
];
const zigzag = (len: number, ms: number): Stroke => [
  { x: 0, y: 0, t: 0 },
  { x: len / 4, y: 40, t: ms / 4 },
  { x: len / 2, y: 0, t: ms / 2 },
  { x: (3 * len) / 4, y: 40, t: (3 * ms) / 4 },
  { x: len, y: 0, t: ms },
];

describe('personality', () => {
  it('직선 획은 직선성 1, 긴 획은 길이 1에 가깝다', () => {
    const f = strokeFeatures([line(300, 200), line(300, 200), line(300, 200)], PERSONALITY);
    expect(f.straightness).toBeCloseTo(1);
    expect(f.strokeLength).toBeCloseTo(1);
    expect(f.strokeSpeed).toBeCloseTo(1);
  });
  it('지그재그는 직선성이 낮다', () => {
    const f = strokeFeatures([zigzag(200, 500)], PERSONALITY);
    expect(f.straightness).toBeLessThan(0.8);
  });
  it('점이 모자란 획은 무시', () => {
    expect(strokeFeatures([[{ x: 0, y: 0, t: 0 }]], PERSONALITY).strokeLength).toBe(0);
  });
  it('각 무기의 성향 벡터 자체를 넣으면 그 무기가 선택된다', () => {
    for (const [id, w] of Object.entries(WEAPONS)) {
      expect(chooseWeapon(w.affinity, WEAPONS, PERSONALITY).id).toBe(id);
    }
  });
  it('크고 느린 직선 획 → 대검 (획만으로)', () => {
    const f = strokeFeatures([line(300, 1500), line(280, 1400), line(290, 1600)], PERSONALITY);
    expect(chooseWeapon(f, WEAPONS, PERSONALITY).id).toBe('greatsword');
  });
  it('빠르고 꺾인 획 → 단검 (획만으로)', () => {
    const f = strokeFeatures([zigzag(100, 80), zigzag(100, 90), zigzag(100, 70)], PERSONALITY);
    expect(chooseWeapon(f, WEAPONS, PERSONALITY).id).toBe('dagger');
  });
});

/** 49라운드 2절: 무기는 3획만으로 결정 — 회피 시험(움직임) 축은 무기 결정에서 완전히 빠졌다 */
describe('personality: 3획만으로 무기 결정', () => {
  it('거리는 획 3축만 본다 (자기 affinity 와의 거리 0)', () => {
    for (const [id, w] of Object.entries(WEAPONS)) {
      expect(chooseWeapon(w.affinity, WEAPONS, PERSONALITY).distances[id]).toBe(0);
    }
  });
  it('STROKE_KEYS = 획 3축', () => {
    expect([...STROKE_KEYS]).toEqual(['strokeLength', 'strokeSpeed', 'straightness']);
  });
});
