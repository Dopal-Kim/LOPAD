/**
 * 54라운드 Q9 휘는 궤적 · Q3 튕기는 술통 경로 계산 (Phaser 의존 없음, 단위 테스트).
 */
export interface P2 {
  x: number;
  y: number;
}

/** 2차 베지어 */
export function quadBezier(a: P2, c: P2, b: P2, t: number): P2 {
  const u = 1 - t;
  return { x: u * u * a.x + 2 * u * t * c.x + t * t * b.x, y: u * u * a.y + 2 * u * t * c.y + t * t * b.y };
}

/**
 * 비틀 돌진 경로: start 에서 target 쪽으로 lengthPx 만큼(현 길이), 가운데가 옆으로 bendRatio × 길이 만큼 휘는 곡선.
 * sign = +1 이면 진행 방향 왼쪽(화면 반시계), -1 이면 오른쪽. samples+1 개 점
 */
export function curvedDashPath(
  start: P2,
  target: P2,
  lengthPx: number,
  bendRatio: number,
  sign: number,
  samples = 24,
): P2[] {
  let dx = target.x - start.x;
  let dy = target.y - start.y;
  const d = Math.hypot(dx, dy);
  if (d > 0) {
    dx /= d;
    dy /= d;
  } else {
    dx = 1;
    dy = 0;
  }
  const end = { x: start.x + dx * lengthPx, y: start.y + dy * lengthPx };
  // 수직 (왼쪽 = (dy, -dx) 화면 좌표에서 반시계)
  const off = bendRatio * lengthPx * sign;
  const ctrl = { x: (start.x + end.x) / 2 + dy * off, y: (start.y + end.y) / 2 - dx * off };
  const out: P2[] = [];
  for (let i = 0; i <= samples; i++) out.push(quadBezier(start, ctrl, end, i / samples));
  return out;
}

/** 꺾은선 누적 길이 (첫 값 0) */
export function cumulative(points: readonly P2[]): number[] {
  const acc = [0];
  for (let i = 1; i < points.length; i++)
    acc.push(acc[i - 1] + Math.hypot(points[i].x - points[i - 1].x, points[i].y - points[i - 1].y));
  return acc;
}

/** 꺾은선 위 거리 dist 의 점 (넘으면 끝점) */
export function pointAlong(points: readonly P2[], acc: readonly number[], dist: number): P2 {
  if (points.length === 0) return { x: 0, y: 0 };
  if (dist <= 0) return { ...points[0] };
  for (let i = 1; i < points.length; i++) {
    if (acc[i] >= dist) {
      const seg = acc[i] - acc[i - 1];
      const t = seg > 0 ? (dist - acc[i - 1]) / seg : 0;
      return {
        x: points[i - 1].x + (points[i].x - points[i - 1].x) * t,
        y: points[i - 1].y + (points[i].y - points[i - 1].y) * t,
      };
    }
  }
  return { ...points[points.length - 1] };
}

/** 술 뿌리기 경로: start → dir 방향 lengthPx, 옆으로 wobblePx 진폭의 한 번 반 물결. samples+1 개 점 */
export function wobblyLine(
  start: P2,
  dirX: number,
  dirY: number,
  lengthPx: number,
  wobblePx: number,
  samples: number,
): P2[] {
  const len = Math.hypot(dirX, dirY) || 1;
  const ux = dirX / len;
  const uy = dirY / len;
  const out: P2[] = [];
  for (let i = 0; i <= samples; i++) {
    const t = i / samples;
    const side = Math.sin(t * Math.PI * 3) * wobblePx * Math.min(1, t * 3);
    out.push({ x: start.x + ux * lengthPx * t + uy * side, y: start.y + uy * lengthPx * t - ux * side });
  }
  return out;
}

export interface BounceTrace {
  /** 시작점 · 튕긴 점들 · 끝점 */
  points: P2[];
  /** 실제로 튕긴 횟수 */
  bounces: number;
  /** 마지막에 벽에 부딪혀 멈췄는지 (튕김 횟수를 다 쓴 뒤 다음 벽) */
  hitWall: boolean;
}

/**
 * 튕김 경로: from 에서 (dirX, dirY) 로 stepPx 씩 나아가며, 반경 radiusPx 의 앞쪽 가장자리가 막힌 칸(blocked(월드 x, y))에 닿으면
 * 축별로 반사한다(가로로 막히면 x 반전, 세로로 막히면 y 반전, 둘 다면 둘 다). bounces 번 튕긴 뒤 다음 벽에서 멈춘다. maxPx 까지
 */
export function traceBounces(
  from: P2,
  dirX: number,
  dirY: number,
  bounces: number,
  maxPx: number,
  radiusPx: number,
  blocked: (x: number, y: number) => boolean,
  stepPx = 2,
): BounceTrace {
  const len = Math.hypot(dirX, dirY) || 1;
  let vx = dirX / len;
  let vy = dirY / len;
  let x = from.x;
  let y = from.y;
  const points: P2[] = [{ x, y }];
  let used = 0;
  let traveled = 0;
  while (traveled < maxPx) {
    const nx = x + vx * stepPx;
    const ny = y + vy * stepPx;
    const hitX = blocked(nx + Math.sign(vx) * radiusPx, y);
    const hitY = blocked(x, ny + Math.sign(vy) * radiusPx);
    const hitXY = !hitX && !hitY && blocked(nx + Math.sign(vx) * radiusPx, ny + Math.sign(vy) * radiusPx);
    if (hitX || hitY || hitXY) {
      if (used >= bounces) {
        points.push({ x, y });
        return { points, bounces: used, hitWall: true };
      }
      used++;
      if (hitX || hitXY) vx = -vx;
      if (hitY || hitXY) vy = -vy;
      points.push({ x, y });
      continue;
    }
    x = nx;
    y = ny;
    traveled += stepPx;
  }
  points.push({ x, y });
  return { points, bounces: used, hitWall: false };
}
