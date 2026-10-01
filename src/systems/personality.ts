import type { Affinity, PersonalityData, WeaponTable } from '../data/types';

/** 3획 입력: 각 획의 점 목록 (px, ms) */
export interface StrokePoint {
  x: number;
  y: number;
  t: number;
}
export type Stroke = StrokePoint[];

/** 키 입력 리듬 집계 */
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

/** 성향 벡터와 가장 가까운 무기 id (가중 유클리드 거리) */
export function chooseWeapon(
  features: Affinity,
  weapons: WeaponTable,
  P: PersonalityData,
): { id: string; distances: Record<string, number> } {
  const keys = Object.keys(P.weights) as (keyof Affinity)[];
  const distances: Record<string, number> = {};
  let best = '';
  let bestD = Infinity;
  for (const [id, w] of Object.entries(weapons)) {
    let d = 0;
    for (const k of keys) d += P.weights[k] * (features[k] - w.affinity[k]) ** 2;
    d = Math.sqrt(d);
    distances[id] = d;
    if (d < bestD) {
      bestD = d;
      best = id;
    }
  }
  return { id: best, distances };
}

function clamp01(v: number): number {
  return Math.max(0, Math.min(1, v));
}
