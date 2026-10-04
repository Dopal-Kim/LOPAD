/**
 * 56라운드 Q2 칼 3타 일섬 기하 (Phaser 의존 없음): 조준 4방향 돌진 · 벽에 막힌 실제 거리 예측 · 선 시트 t1~t4 · 판정 직사각형.
 * 선·분신 시트(art combo56_fx)는 4방향 행으로 축을 따라 그려져 있으므로 돌진도 4방향 축으로 한다.
 */
import type { Facing } from '../sprites/spriteDefs';
import type { HitTarget, Pt } from './hitShapes';
import { thrustHit } from './hitShapes';

/** 4방향 → 단위벡터 */
export function facingVector(f: Facing): Pt {
  return f === 'right'
    ? { x: 1, y: 0 }
    : f === 'left'
      ? { x: -1, y: 0 }
      : f === 'down'
        ? { x: 0, y: 1 }
        : { x: 0, y: -1 };
}

/**
 * 출발점에서 dir 로 distancePx 까지 걸을 수 있는 거리 (stepPx 간격으로 walkable 확인 — 막힌 첫 칸 직전까지).
 * 몸 반폭 halfPx 만큼 앞을 본다
 */
export function predictTravel(
  x: number,
  y: number,
  dir: Pt,
  distancePx: number,
  walkable: (x: number, y: number) => boolean,
  stepPx = 2,
  halfPx = 0,
): number {
  let d = 0;
  while (d + stepPx <= distancePx + 1e-6) {
    const n = d + stepPx;
    if (!walkable(x + dir.x * (n + halfPx), y + dir.y * (n + halfPx))) break;
    d = n;
  }
  return Math.min(distancePx, d);
}

/** 실제 이동 칸 수(내림)로 t1~t4 고르기 — 1칸 미만 = t1 (아트 pickRule). 반환 = 0..count-1 */
export function lineTier(travelPx: number, tilePx: number, count: number): number {
  const tiles = Math.floor(travelPx / Math.max(1, tilePx) + 1e-6);
  return Math.max(0, Math.min(count - 1, tiles - 1));
}

/** 일섬 판정: 출발 원점 뒤 backPx 부터 이동 거리 + extraPx 까지, 폭 widthPx 의 직사각형 */
export function issenHit(
  origin: Pt,
  dir: Pt,
  travelPx: number,
  geom: { backPx: number; extraPx: number; widthPx: number },
  t: HitTarget,
): boolean {
  const sx = origin.x - dir.x * geom.backPx;
  const sy = origin.y - dir.y * geom.backPx;
  return thrustHit(sx, sy, dir.x, dir.y, geom.backPx + travelPx + geom.extraPx, geom.widthPx, t);
}

/** 그림자 분신 위치: 출발 → 도착을 travelMs 동안 선형 (그 뒤 도착점) */
export function shadowAt(from: Pt, to: Pt, elapsedMs: number, travelMs: number): Pt {
  const k = Math.max(0, Math.min(1, elapsedMs / Math.max(1, travelMs)));
  return { x: from.x + (to.x - from.x) * k, y: from.y + (to.y - from.y) * k };
}
