import type { Affinity, PersonalityData, WeaponTable } from '../data/types';

/** 3획 입력: 각 획의 점 목록 (px, ms) */
export interface StrokePoint {
  x: number;
  y: number;
  t: number;
}
export type Stroke = StrokePoint[];

/** 키 입력 리듬 집계 (14라운드 5초 리듬. 48라운드부터 Setup 은 회피 시험 `dodgeTrial.evaluateDodge` 를 쓴다 — 호환용으로 유지) */
export interface RhythmSample {
  frames: number;
  movingFrames: number;
  attacks: number;
  dashes: number;
}

export function strokeFeatures(
  strokes: Stroke[],
  P: PersonalityData,
): Pick<Affinity, 'strokeLength' | 'strokeSpeed' | 'straightness'> {
  const valid = strokes.filter((s) => s.length >= P.strokes.minPoints);
  if (valid.length === 0) return { strokeLength: 0, strokeSpeed: 0, straightness: 0 };
  let len = 0;
  let speed = 0;
  let straight = 0;
  for (const s of valid) {
    let path = 0;
    for (let i = 1; i < s.length; i++) path += Math.hypot(s[i].x - s[i - 1].x, s[i].y - s[i - 1].y);
    const chord = Math.hypot(s[s.length - 1].x - s[0].x, s[s.length - 1].y - s[0].y);
    const dur = Math.max(1, s[s.length - 1].t - s[0].t) / 1000;
    len += path;
    speed += path / dur;
    straight += path > 0 ? chord / path : 0;
  }
  const n = valid.length;
  return {
    strokeLength: clamp01(len / n / P.strokes.lengthMaxPx),
    strokeSpeed: clamp01(speed / n / P.strokes.speedMaxPxPerSec),
    straightness: clamp01(straight / n),
  };
}

export function rhythmFeatures(
  r: RhythmSample,
  P: PersonalityData,
): Pick<Affinity, 'keyMove' | 'keyAttack' | 'keyDash'> {
  return {
    keyMove: r.frames > 0 ? clamp01(r.movingFrames / r.frames) : 0,
    keyAttack: clamp01(r.attacks / P.rhythm.attackSaturation),
    keyDash: clamp01(r.dashes / P.rhythm.dashSaturation),
  };
}

/**
 * 운명 무기 결정. 기본은 성향 벡터와 무기 affinity 의 가중 유클리드 거리가 가장 가까운 무기.
 * 48라운드 Q7: 회피 시험 가산 `bias`(무기 id → 0 이상)가 있으면 점수 = 거리 − 가산 이 가장 작은 무기.
 * `distances` 는 순수 거리, `scores` 는 가산을 뺀 값 (bias 가 없으면 같다).
 */
export function chooseWeapon(
  features: Affinity,
  weapons: WeaponTable,
  P: PersonalityData,
  bias: Record<string, number> = {},
): { id: string; distances: Record<string, number>; scores: Record<string, number> } {
  const keys = Object.keys(P.weights) as (keyof Affinity)[];
  const distances: Record<string, number> = {};
  const scores: Record<string, number> = {};
  let best = '';
  let bestS = Infinity;
  for (const [id, w] of Object.entries(weapons)) {
    let d = 0;
    for (const k of keys) d += P.weights[k] * (features[k] - w.affinity[k]) ** 2;
    d = Math.sqrt(d);
    distances[id] = d;
    const s = d - (bias[id] ?? 0);
    scores[id] = s;
    if (s < bestS) {
      bestS = s;
      best = id;
    }
  }
  return { id: best, distances, scores };
}

function clamp01(v: number): number {
  return Math.max(0, Math.min(1, v));
}
