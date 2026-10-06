/**
 * 61 단계 6 (P14 §1 '막고 받아치기') 훈련 예고 — 원·선·부채를 주인공 자리에 그리고, 끝나는 순간 안에 있으면 맞는다.
 * 순수 기하 (Phaser 의존 없음, 단위 테스트). 씬(TrainingDrills)이 예고 그림·피해를 맡는다.
 */
export type DrillShape = 'circle' | 'line' | 'cone';

export interface DrillGeom {
  shape: DrillShape;
  /** 원 중심 · 선 시작점 · 부채 꼭짓점 */
  x: number;
  y: number;
  /** 선·부채 방향 (라디안) */
  angle: number;
  /** 원·부채 반지름 · 선 길이 */
  reachPx: number;
  /** 선 반폭 */
  halfWidthPx: number;
  /** 부채 반각 (라디안) */
  halfAngle: number;
}

export interface DrillSizes {
  radiusPx: number;
  lineLengthPx: number;
  lineHalfPx: number;
  coneRadiusPx: number;
  coneHalfAngle: number;
}

/**
 * 주인공 (px, py) 을 겨누는 예고 하나. side = 0..1 무작위 (선·부채가 오는 쪽).
 * 원 = 주인공 발밑 · 선 = 주인공을 지나도록 반대쪽에서 시작 · 부채 = 반지름 0.45 앞 꼭짓점에서 주인공 쪽으로
 */
export function aimDrill(shape: DrillShape, px: number, py: number, side: number, s: DrillSizes): DrillGeom {
  const a = side * Math.PI * 2;
  if (shape === 'circle') return { shape, x: px, y: py, angle: 0, reachPx: s.radiusPx, halfWidthPx: 0, halfAngle: 0 };
  if (shape === 'line') {
    const back = s.lineLengthPx / 2;
    return {
      shape,
      x: px - Math.cos(a) * back,
      y: py - Math.sin(a) * back,
      angle: a,
      reachPx: s.lineLengthPx,
      halfWidthPx: s.lineHalfPx,
      halfAngle: 0,
    };
  }
  const back = s.coneRadiusPx * 0.45;
  return {
    shape,
    x: px - Math.cos(a) * back,
    y: py - Math.sin(a) * back,
    angle: a,
    reachPx: s.coneRadiusPx,
    halfWidthPx: 0,
    halfAngle: s.coneHalfAngle,
  };
}

/** (px, py) 가 예고 안인가 */
export function insideDrill(d: DrillGeom, px: number, py: number): boolean {
  const dx = px - d.x;
  const dy = py - d.y;
  if (d.shape === 'circle') return Math.hypot(dx, dy) <= d.reachPx;
  const ux = Math.cos(d.angle);
  const uy = Math.sin(d.angle);
  const along = dx * ux + dy * uy;
  if (d.shape === 'line') {
    if (along < 0 || along > d.reachPx) return false;
    return Math.abs(-dx * uy + dy * ux) <= d.halfWidthPx;
  }
  const dist = Math.hypot(dx, dy);
  if (dist > d.reachPx) return false;
  if (dist === 0) return true;
  const cos = along / dist;
  return cos >= Math.cos(d.halfAngle);
}

/** 다음 예고 모양: 아직 피하지 못한 모양을 차례로 (모두 마쳤으면 순환) */
export function nextDrillShape(order: readonly DrillShape[], done: ReadonlySet<DrillShape>, last: number): number {
  if (order.length === 0) return -1;
  for (let k = 1; k <= order.length; k++) {
    const i = (last + k) % order.length;
    if (!done.has(order[i])) return i;
  }
  return (last + 1) % order.length;
}
