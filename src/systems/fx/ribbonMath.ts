/**
 * 55라운드 Q7 칼끝 잔상 리본 수식 (계약 §16 `ribbon_ash`). Phaser 의존 없음 — 그리기는 `ribbon.ts`.
 * 점 = 칼끝 위치 + 찍은 시각(플레이 시계). 수명이 지난 점은 버리고, 리본 전체의 나이 프레임은 가장 새 점의 나이로 정한다
 * (텍스처 자체가 꼬리 재 → 머리 호박 그라데이션이라 점마다 따로 식힐 필요가 없다).
 */

export interface RibbonSample {
  x: number;
  y: number;
  t: number;
}

/**
 * 나이 프레임: 나이/수명 비율을 프레임 수로 균등하게 나눈다 (0 = 갓 그림, 마지막 = 재만 남음).
 * 아트 `ageFrames`([0,33,66,100] %)는 각 프레임이 시작하는 나이 — 마지막 프레임도 수명 안에서 보이도록 프레임 수로 나눈다
 */
export function ribbonAgeFrame(ageMs: number, lifeMs: number, frames: number): number {
  if (frames <= 1 || lifeMs <= 0) return 0;
  const f = Math.max(0, ageMs) / lifeMs;
  return Math.max(0, Math.min(frames - 1, Math.floor(f * frames)));
}

/** (from, to] 사이에 step 간격으로 찍을 시각들 (마지막은 늘 to). from 이 없으면 [to] */
export function sampleTimes(from: number | null, to: number, step: number): number[] {
  if (from === null || !(to > from)) return from === null ? [to] : [];
  const out: number[] = [];
  const s = Math.max(1, step);
  for (let t = from + s; t < to; t += s) out.push(t);
  out.push(to);
  return out;
}

/**
 * 점 넣기: 도트 격자(`unit`)에 맞추고, 바로 앞 점과 같은 자리면 시각만 갱신 (Rope 수직 벡터가 0 이 되지 않게). 넣었으면 true
 */
export function pushRibbonSample(samples: RibbonSample[], x: number, y: number, t: number, unit: number): boolean {
  const snap = (v: number) => (unit > 0 ? Math.round(v / unit) * unit : v);
  const sx = snap(x);
  const sy = snap(y);
  const last = samples[samples.length - 1];
  if (last && last.x === sx && last.y === sy) {
    last.t = t;
    return false;
  }
  samples.push({ x: sx, y: sy, t });
  return true;
}

/** 수명이 지난 점 · 최대 개수를 넘는 오래된 점을 버린다 (제자리 수정) */
export function pruneRibbon(samples: RibbonSample[], now: number, lifeMs: number, maxPoints: number): void {
  let drop = 0;
  while (drop < samples.length && now - samples[drop].t >= lifeMs) drop++;
  drop = Math.max(drop, samples.length - maxPoints);
  if (drop > 0) samples.splice(0, drop);
}
