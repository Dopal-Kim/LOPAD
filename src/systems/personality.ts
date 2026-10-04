import type { Affinity, PersonalityData, WeaponTable } from '../data/types';
import { clamp01 } from './mathUtil';

/** 3획 입력: 각 획의 점 목록 (px, ms) */
export interface StrokePoint {
  x: number;
  y: number;
  t: number;
}
export type Stroke = StrokePoint[];

/** 무기 결정에 쓰는 획 3축 (49라운드 2절: 무기는 3획만으로 결정) */
export const STROKE_KEYS = ['strokeLength', 'strokeSpeed', 'straightness'] as const;
export type StrokeKey = (typeof STROKE_KEYS)[number];
export type StrokeFeatures = Pick<Affinity, StrokeKey>;

export function strokeFeatures(strokes: Stroke[], P: PersonalityData): StrokeFeatures {
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

/**
 * 운명 무기 결정 (49라운드 2절): **3획 특징만으로** — 획 3축(길이·속도·직선성)과 무기 affinity 의 같은 3축 사이
 * 가중 유클리드 거리(가중치 `personality.json weights` 의 획 3축)가 가장 가까운 무기.
 * 회피 시험(움직임)은 무기 결정에서 완전히 빠졌다 — 시험은 등급 → 시작 감각 가산만 준다 (`dodgeTrial.gradeTrial`).
 */
export function chooseWeapon(
  features: StrokeFeatures,
  weapons: WeaponTable,
  P: PersonalityData,
): { id: string; distances: Record<string, number> } {
  const distances: Record<string, number> = {};
  let best = '';
  let bestD = Infinity;
  for (const [id, w] of Object.entries(weapons)) {
    let d = 0;
    for (const k of STROKE_KEYS) d += P.weights[k] * (features[k] - w.affinity[k]) ** 2;
    d = Math.sqrt(d);
    distances[id] = d;
    if (d < bestD) {
      bestD = d;
      best = id;
    }
  }
  return { id: best, distances };
}
