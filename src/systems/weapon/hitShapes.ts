/**
 * 근접 판정 모양 기하 (48라운드 부채꼴·찌르기 → 55라운드 §17 arc(내반경·비대칭)·wedge(+끝점 충격원)·rect·ring). Phaser 의존 없음.
 * combo.ts 에서 분리(55라운드 6-1). 각도 규약: 조준 방향 = 0°, 화면 기준 시계 방향 + (right 기준, + = 아래),
 * 왼쪽 조준은 좌우 반전(`facingAngle` — 그림과 같은 규칙), 위·아래는 회전 그대로.
 */
import type { ComboDef, HitShapeSpec } from '../data/types';

export type ShapeFacing = 'down' | 'up' | 'left' | 'right';

/** 판정 대상 (바디 중심·반지름 근사) */
export interface HitTarget {
  x: number;
  y: number;
  r: number;
}

export interface Pt {
  x: number;
  y: number;
}

/** 한 타의 판정 모양 (px, 진화·강화·타 배율 적용 후). `thrust` = 데이터 `rect`(찌르기) */
export type HitShape =
  /** centerDeg = 정면에서 호 가운데까지, fromDeg→toDeg = 휘두름 방향, inner = 내반경(초승달, 없으면 0) */
  | { kind: 'arc'; radius: number; arcDeg: number; centerDeg: number; fromDeg: number; toDeg: number; inner?: number }
  | { kind: 'thrust'; length: number; width: number; angleDeg: number; fromPx: number }
  /** 좁은 쐐기(반경 length, 폭 arcDeg) + 끝점 충격원 (중심 = 쐐기 가운데 방향 dist) */
  | {
      kind: 'wedge';
      length: number;
      arcDeg: number;
      centerDeg: number;
      impact: { radius: number; dist: number } | null;
    }
  /** 충격파 고리 (중심 = 조준 방향 dist) */
  | { kind: 'ring'; radius: number; inner: number; dist: number };

/**
 * 아트 각도 규약(right 기준 화면각, + = 아래)을 실제 공격 방향에 맞춘다: down·up 은 회전이라 그대로, left 는 좌우 반전(부호 반대)
 */
export function facingAngle(deg: number, facing: ShapeFacing): number {
  return facing === 'left' ? -deg : deg;
}

/** 방향 (dirX, dirY) 를 deg 만큼 돌린 단위벡터 */
export function rotateDir(dirX: number, dirY: number, deg: number): Pt {
  const a = Math.atan2(dirY, dirX) + (deg * Math.PI) / 180;
  return { x: Math.cos(a), y: Math.sin(a) };
}

function unit(dirX: number, dirY: number): Pt {
  const len = Math.hypot(dirX, dirY) || 1;
  return { x: dirX / len, y: dirY / len };
}

/**
 * 부채꼴(내반경 선택) 판정: 중심 (cx, cy), 방향 (dirX, dirY) 기준 ±arcDeg/2, 반경 radius, 내반경 inner.
 * 대상 원(반지름 r)이 걸치면 true. 각도 여유 = asin(r / d). 내반경이 없으면 중심과 겹친 대상도 맞음
 */
export function arcHit(
  cx: number,
  cy: number,
  dirX: number,
  dirY: number,
  radius: number,
  arcDeg: number,
  t: HitTarget,
  inner = 0,
): boolean {
  const dx = t.x - cx;
  const dy = t.y - cy;
  const d = Math.hypot(dx, dy);
  // 내반경 안에 통째로 들어간 대상은 빗나감 (초승달). 원점과 겹친 대상은 맞음(가까이 붙은 적 — 내반경이 있으면 그 밖까지 걸칠 때만)
  if (inner > 0 && d + t.r < inner) return false;
  if (d <= t.r) return true;
  if (d - t.r > radius) return false;
  const u = unit(dirX, dirY);
  const cos = (dx * u.x + dy * u.y) / d;
  const ang = Math.acos(Math.max(-1, Math.min(1, cos)));
  const slack = Math.asin(Math.min(1, t.r / d));
  return ang <= (arcDeg * Math.PI) / 360 + slack;
}

/** 찌르기 판정: 중심에서 방향으로 길이 length, 폭 width 의 직사각형. 대상 원이 걸치면 true */
export function thrustHit(
  cx: number,
  cy: number,
  dirX: number,
  dirY: number,
  length: number,
  width: number,
  t: HitTarget,
): boolean {
  const u = unit(dirX, dirY);
  const dx = t.x - cx;
  const dy = t.y - cy;
  const along = dx * u.x + dy * u.y;
  const perp = Math.abs(-dx * u.y + dy * u.x);
  return along >= -t.r && along <= length + t.r && perp <= width / 2 + t.r;
}

/** 원 판정 (끝점 충격원) */
export function circleHit(cx: number, cy: number, radius: number, t: HitTarget): boolean {
  return Math.hypot(t.x - cx, t.y - cy) <= radius + t.r;
}

/** 고리 판정 (충격파): 바깥 반지름 안 · 안 반지름 밖에 걸치면 true */
export function ringHit(cx: number, cy: number, radius: number, inner: number, t: HitTarget): boolean {
  const d = Math.hypot(t.x - cx, t.y - cy);
  return d - t.r <= radius && d + t.r >= inner;
}

/** 쐐기 끝점 충격원·고리 중심 (월드). 해당 없으면 null */
export function shapeCenterPoint(
  cx: number,
  cy: number,
  dirX: number,
  dirY: number,
  shape: HitShape,
  facing: ShapeFacing = 'right',
): Pt | null {
  if (shape.kind === 'wedge' && shape.impact) {
    const c = rotateDir(dirX, dirY, facingAngle(shape.centerDeg, facing));
    return { x: cx + c.x * shape.impact.dist, y: cy + c.y * shape.impact.dist };
  }
  if (shape.kind === 'ring') {
    const u = unit(dirX, dirY);
    return { x: cx + u.x * shape.dist, y: cy + u.y * shape.dist };
  }
  return null;
}

/** 모양 판정 (thrust 는 angleDeg 만큼 돌리고 fromPx 만큼 떨어진 곳부터) */
export function shapeHit(
  cx: number,
  cy: number,
  dirX: number,
  dirY: number,
  shape: HitShape,
  t: HitTarget,
  facing: ShapeFacing = 'right',
): boolean {
  switch (shape.kind) {
    case 'arc': {
      const c = rotateDir(dirX, dirY, facingAngle(shape.centerDeg, facing));
      return arcHit(cx, cy, c.x, c.y, shape.radius, shape.arcDeg, t, shape.inner ?? 0);
    }
    case 'thrust': {
      const d = rotateDir(dirX, dirY, facingAngle(shape.angleDeg, facing));
      return thrustHit(cx + d.x * shape.fromPx, cy + d.y * shape.fromPx, d.x, d.y, shape.length, shape.width, t);
    }
    case 'wedge': {
      const c = rotateDir(dirX, dirY, facingAngle(shape.centerDeg, facing));
      if (arcHit(cx, cy, c.x, c.y, shape.length, shape.arcDeg, t)) return true;
      const p = shapeCenterPoint(cx, cy, dirX, dirY, shape, facing);
      return p !== null && shape.impact !== null && circleHit(p.x, p.y, shape.impact.radius, t);
    }
    case 'ring': {
      const p = shapeCenterPoint(cx, cy, dirX, dirY, shape, facing)!;
      return ringHit(p.x, p.y, shape.radius, shape.inner, t);
    }
  }
}

const ARC_STEPS_PER_DEG = 1 / 10;

function circlePts(cx: number, cy: number, r: number): Pt[] {
  const n = 32;
  const out: Pt[] = [];
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2;
    out.push({ x: cx + Math.cos(a) * r, y: cy + Math.sin(a) * r });
  }
  return out;
}

/** 중심각 a(라디안) ± half 의 호 점들 (반경 r) */
function arcPts(cx: number, cy: number, r: number, a: number, half: number): Pt[] {
  const n = Math.max(4, Math.ceil(((half * 2 * 180) / Math.PI) * ARC_STEPS_PER_DEG));
  const out: Pt[] = [];
  for (let i = 0; i <= n; i++) {
    const b = a - half + (2 * half * i) / n;
    out.push({ x: cx + Math.cos(b) * r, y: cy + Math.sin(b) * r });
  }
  return out;
}

/** 부채꼴·초승달 다각형 (360° 이상이면 원) */
function sectorPoly(cx: number, cy: number, dir: Pt, radius: number, inner: number, arcDeg: number): Pt[][] {
  if (arcDeg >= 360)
    return inner > 0 ? [circlePts(cx, cy, radius), circlePts(cx, cy, inner)] : [circlePts(cx, cy, radius)];
  const a = Math.atan2(dir.y, dir.x);
  const half = (arcDeg * Math.PI) / 360;
  const outer = arcPts(cx, cy, radius, a, half);
  if (inner <= 0) return [[{ x: cx, y: cy }, ...outer]];
  return [[...outer, ...arcPts(cx, cy, inner, a, half).reverse()]];
}

/**
 * 모양 윤곽 다각형들 (월드). 디버그 오버레이·외접 사각형이 쓴다.
 * arc = 부채꼴/초승달 1개 · thrust = 사각형 · wedge = 쐐기 + 충격원 · ring = 바깥 원 + 안 원
 */
export function shapeOutline(
  cx: number,
  cy: number,
  dirX: number,
  dirY: number,
  shape: HitShape,
  facing: ShapeFacing = 'right',
): Pt[][] {
  switch (shape.kind) {
    case 'arc': {
      const c = rotateDir(dirX, dirY, facingAngle(shape.centerDeg, facing));
      return sectorPoly(cx, cy, c, shape.radius, shape.inner ?? 0, shape.arcDeg);
    }
    case 'thrust': {
      const d = rotateDir(dirX, dirY, facingAngle(shape.angleDeg, facing));
      const px = -d.y * (shape.width / 2);
      const py = d.x * (shape.width / 2);
      const sx = cx + d.x * shape.fromPx;
      const sy = cy + d.y * shape.fromPx;
      const ex = sx + d.x * shape.length;
      const ey = sy + d.y * shape.length;
      return [
        [
          { x: sx + px, y: sy + py },
          { x: ex + px, y: ey + py },
          { x: ex - px, y: ey - py },
          { x: sx - px, y: sy - py },
        ],
      ];
    }
    case 'wedge': {
      const c = rotateDir(dirX, dirY, facingAngle(shape.centerDeg, facing));
      const polys = sectorPoly(cx, cy, c, shape.length, 0, shape.arcDeg);
      const p = shapeCenterPoint(cx, cy, dirX, dirY, shape, facing);
      if (p && shape.impact) polys.push(circlePts(p.x, p.y, shape.impact.radius));
      return polys;
    }
    case 'ring': {
      const p = shapeCenterPoint(cx, cy, dirX, dirY, shape, facing)!;
      const polys = [circlePts(p.x, p.y, shape.radius)];
      if (shape.inner > 0) polys.push(circlePts(p.x, p.y, shape.inner));
      return polys;
    }
  }
}

/** 모양의 축 정렬 외접 사각형 (물리 겹침 영역·구조물 타격·잔월 궤적) */
export function hitShapeBounds(
  cx: number,
  cy: number,
  dirX: number,
  dirY: number,
  shape: HitShape,
  facing: ShapeFacing = 'right',
): { x: number; y: number; w: number; h: number } {
  let x0 = Infinity;
  let y0 = Infinity;
  let x1 = -Infinity;
  let y1 = -Infinity;
  for (const poly of shapeOutline(cx, cy, dirX, dirY, shape, facing))
    for (const p of poly) {
      x0 = Math.min(x0, p.x);
      y0 = Math.min(y0, p.y);
      x1 = Math.max(x1, p.x);
      y1 = Math.max(y1, p.y);
    }
  if (!Number.isFinite(x0)) return { x: cx, y: cy, w: 0, h: 0 };
  return { x: x0, y: y0, w: x1 - x0, h: y1 - y0 };
}

/** 데이터 모양 배율 (차지 단계 쐐기 길이 · 관성 최대 충격원) */
export interface ShapeScale {
  /** 쐐기 길이 배율 (lengthMult 를 대신) */
  lengthMult?: number;
  /** 끝점 충격원 반지름 배율 */
  impactMult?: number;
}

/** 55라운드 §17: 데이터 모양 → px 모양. R = 현재 판정 반경 */
export function resolveHitShape(spec: HitShapeSpec, R: number, scale: ShapeScale = {}): HitShape {
  switch (spec.kind) {
    case 'arc': {
      const radius = R * (spec.radiusMult ?? 1);
      return {
        kind: 'arc',
        radius,
        inner: radius * (spec.innerRatio ?? 0),
        arcDeg: Math.abs(spec.toDeg - spec.fromDeg),
        centerDeg: (spec.fromDeg + spec.toDeg) / 2,
        fromDeg: spec.fromDeg,
        toDeg: spec.toDeg,
      };
    }
    case 'wedge': {
      const length = R * (scale.lengthMult ?? spec.lengthMult);
      const ic = spec.impactCircle;
      return {
        kind: 'wedge',
        length,
        arcDeg: spec.widthDeg,
        centerDeg: spec.angleDeg ?? 0,
        impact: ic
          ? {
              radius: R * ic.radiusRatio * (scale.impactMult ?? 1),
              dist: ic.atMult !== undefined ? R * ic.atMult : length,
            }
          : null,
      };
    }
    case 'rect':
      return {
        kind: 'thrust',
        length: R * spec.lengthMult,
        width: R * spec.widthMult,
        angleDeg: spec.angleDeg ?? 0,
        fromPx: R * (spec.fromMult ?? 0),
      };
    case 'ring': {
      const radius = R * spec.radiusMult;
      return { kind: 'ring', radius, inner: radius * (spec.innerRatio ?? 0), dist: R * (spec.atMult ?? 0) };
    }
  }
}

/** 아트 JSON 메모 (계약 art §6.1): 있으면 데이터 기본값 대신 — 타별 `hitShape` 가 없는 기존 연격(단검 찌르기 등)만 */
export interface ShapeMemo {
  hitRadiusPx?: number;
  arcDeg?: number;
  arcFromDeg?: number;
  arcToDeg?: number;
  thrust?: { lengthPx: number; widthPx: number; angleDeg?: number; fromPx?: number };
}

/** 연격 공통 판정 반경 px (R, 배율 전) — `radiusPx` 없으면 reach + width/2 */
export function comboRadius(def: Pick<ComboDef, 'radiusPx'>, base: { reach: number; width: number }): number {
  return def.radiusPx ?? base.reach + base.width / 2;
}

/**
 * 48라운드 연격 공통 판정 모양: 아트 메모(hitRadiusPx·arcDeg·thrust)가 있으면 그것, 없으면 데이터(arc 반경 = reach + width/2, thrust 길이·폭).
 * scale = 진화·강화 배율(현재 reach / 기본 reach) × 타·대쉬 크기 배율
 */
export function comboShape(
  def: ComboDef,
  base: { reach: number; width: number },
  scale: number,
  memo?: ShapeMemo | null,
): HitShape {
  if (def.shape === 'thrust') {
    const t = memo?.thrust ?? def.thrust ?? { lengthPx: base.reach + base.width / 2, widthPx: base.width / 2 };
    return {
      kind: 'thrust',
      length: t.lengthPx * scale,
      width: t.widthPx * scale,
      angleDeg: memo?.thrust?.angleDeg ?? 0,
      fromPx: (memo?.thrust?.fromPx ?? 0) * scale,
    };
  }
  const radius = typeof memo?.hitRadiusPx === 'number' ? memo.hitRadiusPx : comboRadius(def, base);
  const arcDeg = typeof memo?.arcDeg === 'number' ? memo.arcDeg : (def.arcDeg ?? 120);
  const from = typeof memo?.arcFromDeg === 'number' ? memo.arcFromDeg : -arcDeg / 2;
  const to = typeof memo?.arcToDeg === 'number' ? memo.arcToDeg : arcDeg / 2;
  return { kind: 'arc', radius: radius * scale, arcDeg, centerDeg: (from + to) / 2, fromDeg: from, toDeg: to };
}
