import { describe, expect, it } from 'vitest';
import { PERSONALITY, WEAPONS } from '../data';
import { chooseWeapon, rhythmFeatures, strokeFeatures, type Stroke } from './personality';
import { DODGE_TRIAL, emptySample, evaluateDodge, type DodgeSample } from './dodgeTrial';

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

  it('가산이 없으면 scores = distances', () => {
    const r = chooseWeapon(WEAPONS.katana.affinity, WEAPONS, PERSONALITY);
    for (const id of Object.keys(WEAPONS)) expect(r.scores[id]).toBe(r.distances[id]);
  });
  it('가산이 거리 차보다 크면 결정이 바뀐다', () => {
    const f = WEAPONS.katana.affinity;
    expect(chooseWeapon(f, WEAPONS, PERSONALITY, { bow: 0.05 }).id).toBe('katana');
    expect(chooseWeapon(f, WEAPONS, PERSONALITY, { bow: 1 }).id).toBe('bow');
  });
});

/** 48라운드 Q7: 같은 (중립) 획에 회피 시험 결과를 합산 */
describe('personality + 회피 시험', () => {
  const neutralStrokes = { strokeLength: 0.6, strokeSpeed: 0.6, straightness: 0.7 };
  const decide = (over: Partial<DodgeSample>) => {
    const s: DodgeSample = { ...emptySample(), survivedMs: DODGE_TRIAL.DURATION_MS, frames: 900, ...over };
    const e = evaluateDodge(s, PERSONALITY.rhythm.dashSaturation);
    return { ...chooseWeapon({ ...neutralStrokes, ...e.keys }, WEAPONS, PERSONALITY, e.bias), rare: e.rare };
  };
  it('멀찍이 피하고 거의 안 맞음 → 활', () => {
    expect(decide({ movingFrames: 540, dashes: 2, hits: 1, passes: { close: 1, mid: 3, far: 10 } }).id).toBe('bow');
  });
  it('직전 회피 + 대쉬 직전 회피 → 단검', () => {
    expect(
      decide({ movingFrames: 750, dashes: 8, dashDodges: 4, hits: 2, passes: { close: 9, mid: 3, far: 0 } }).id,
    ).toBe('dagger');
  });
  it('직전 회피 (대쉬 적음) → 칼', () => {
    expect(
      decide({ movingFrames: 450, dashes: 3, dashDodges: 1, hits: 1, passes: { close: 8, mid: 4, far: 1 } }).id,
    ).toBe('katana');
  });
  it('많이 맞고 버팀 / 떨어짐 → 대검', () => {
    expect(decide({ movingFrames: 300, dashes: 1, hits: 7, passes: { close: 4, mid: 4, far: 2 } }).id).toBe(
      'greatsword',
    );
    expect(decide({ movingFrames: 300, dashes: 1, hits: 3, falls: 1, survivedMs: 7000 }).id).toBe('greatsword');
  });
  it('무피격 생존은 희귀 기록만 남기고 무기는 4종 중 하나', () => {
    const r = decide({ movingFrames: 700, dashes: 3, passes: { close: 0, mid: 2, far: 12 } });
    expect(r.rare.flag).toBe(true);
    expect(Object.keys(WEAPONS)).toContain(r.id);
  });
});
