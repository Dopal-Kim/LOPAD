import { describe, expect, it } from 'vitest';
import { PERSONALITY, WEAPONS } from '../data';
import { chooseWeapon, rhythmFeatures, strokeFeatures, type Stroke } from './personality';

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
  it('리듬: 이동 비율·공격·대쉬 포화', () => {
    const f = rhythmFeatures({ frames: 100, movingFrames: 80, attacks: 30, dashes: 4 }, PERSONALITY);
    expect(f.keyMove).toBeCloseTo(0.8);
    expect(f.keyAttack).toBe(1);
    expect(f.keyDash).toBeCloseTo(0.5);
  });
  it('각 무기의 성향 벡터 자체를 넣으면 그 무기가 선택된다', () => {
    for (const [id, w] of Object.entries(WEAPONS)) {
      expect(chooseWeapon(w.affinity, WEAPONS, PERSONALITY).id).toBe(id);
    }
  });
  it('크고 느린 획 + 공격 위주 → 대검', () => {
    const f = {
      ...strokeFeatures([line(300, 1500), line(280, 1400), line(290, 1600)], PERSONALITY),
      ...rhythmFeatures({ frames: 300, movingFrames: 80, attacks: 14, dashes: 1 }, PERSONALITY),
    };
    expect(chooseWeapon(f, WEAPONS, PERSONALITY).id).toBe('greatsword');
  });
});
