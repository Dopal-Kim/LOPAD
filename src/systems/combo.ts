/**
 * 48라운드 Q2: 근접 3연격 상태 머신과 판정 모양. Phaser 의존 없음.
 *
 * 흐름: 좌클릭 → `press(now)` 로 입력 버퍼에 넣는다 → 매 프레임 `poll(now, canAct)` 가 다음 타를 시작할 수 있으면
 * 타 번호(0부터)를 돌려준다. 다음 타는 직전 타 시작 + `cancelFromMs` 부터 허용(마지막 타는 + durationMs + finisherRecoverMs).
 * 직전 타가 끝나고(durationMs) `resetMs` 가 지나도록 다음 타가 없으면 1타로 돌아간다. 버퍼는 `bufferMs` 동안만 유효.
 */
import type { ComboDef, ComboHitDef } from '../data/types';

export class ComboTracker {
  /** 마지막으로 시작한 타 번호 (-1 = 아직 없음) */
  private index = -1;
  private startedAt = -Infinity;
  private bufferedAt = -Infinity;
  /** 이번 타의 다음 타 허용 시각 덮어쓰기 (아트 JSON cancelFromFrame, 이 타 시작부터 ms) */
  private cancelOverride: number | null = null;

  constructor(private readonly def: ComboDef) {}

  get hits(): readonly ComboHitDef[] {
    return this.def.hits;
  }

  /** 마지막으로 시작한 타 (디버그) */
  get lastIndex(): number {
    return this.index;
  }

  get lastStartedAt(): number {
    return this.startedAt;
  }

  /** 버퍼에 입력이 남아 있는지 */
  buffered(now: number): boolean {
    return now - this.bufferedAt <= this.def.bufferMs;
  }

  press(now: number): void {
    this.bufferedAt = now;
  }

  /** 다음 타를 시작할 수 있는 시각 */
  readyAt(): number {
    if (this.index < 0) return -Infinity;
    const h = this.def.hits[this.index];
    if (this.index >= this.def.hits.length - 1) return this.startedAt + h.durationMs + this.def.finisherRecoverMs;
    return this.startedAt + (this.cancelOverride ?? h.cancelFromMs);
  }

  /** 지금 시작하면 몇 번째 타인가 (리셋 시간이 지났거나 마지막 타 뒤면 0) */
  nextIndex(now: number): number {
    if (this.index < 0 || this.index >= this.def.hits.length - 1) return 0;
    const h = this.def.hits[this.index];
    if (now > this.startedAt + h.durationMs + this.def.resetMs) return 0;
    return this.index + 1;
  }

  /** 버퍼에 입력이 있고 시작 가능하면 타 번호를 돌려주고 시작 처리. 아니면 null (버퍼는 유효 시간 동안 유지) */
  poll(now: number, canAct: boolean): number | null {
    if (!this.buffered(now) || !canAct) return null;
    if (now < this.readyAt()) return null;
    const next = this.nextIndex(now);
    this.index = next;
    this.startedAt = now;
    this.bufferedAt = -Infinity;
    this.cancelOverride = null;
    return next;
  }

  /** 방금 시작한 타의 다음 타 허용 시각을 바꾼다 (시트 cancelFromFrame 시작 ms, 이 타 길이 안으로 자름) */
  overrideCancel(ms: number): void {
    if (this.index < 0) return;
    this.cancelOverride = Math.max(0, Math.min(ms, this.def.hits[this.index].durationMs));
  }

  /** 대쉬·피격 사망 등으로 연격을 끊는다 (버퍼도 비운다) */
  reset(): void {
    this.cancelOverride = null;
    this.index = -1;
    this.startedAt = -Infinity;
    this.bufferedAt = -Infinity;
  }
}

/** 판정 대상 (바디 중심·반지름 근사) */
export interface HitTarget {
  x: number;
  y: number;
  r: number;
}

/**
 * 부채꼴 판정: 중심 (cx, cy), 방향 (dirX, dirY) 기준 ±arcDeg/2, 반경 radius. 대상 원(반지름 r)이 걸치면 true.
 * 각도 여유 = asin(r / d) (원의 가장자리가 호 안에 들어오면 맞음). 대상이 중심과 겹치면 맞음
 */
export function arcHit(
  cx: number,
  cy: number,
  dirX: number,
  dirY: number,
  radius: number,
  arcDeg: number,
  t: HitTarget,
): boolean {
  const dx = t.x - cx;
  const dy = t.y - cy;
  const d = Math.hypot(dx, dy);
  if (d <= t.r) return true;
  if (d - t.r > radius) return false;
  const len = Math.hypot(dirX, dirY) || 1;
  const cos = (dx * dirX + dy * dirY) / (d * len);
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
  const len = Math.hypot(dirX, dirY) || 1;
  const ux = dirX / len;
  const uy = dirY / len;
  const dx = t.x - cx;
  const dy = t.y - cy;
  const along = dx * ux + dy * uy;
  const perp = Math.abs(-dx * uy + dy * ux);
  return along >= -t.r && along <= length + t.r && perp <= width / 2 + t.r;
}

/** 판정 모양의 축 정렬 외접 사각형 (구조물 타격·잔월 궤적처럼 사각형을 쓰는 곳) */
export function shapeBounds(
  cx: number,
  cy: number,
  dirX: number,
  dirY: number,
  shape: { kind: 'arc'; radius: number; arcDeg: number } | { kind: 'thrust'; length: number; width: number },
): { x: number; y: number; w: number; h: number } {
  const len = Math.hypot(dirX, dirY) || 1;
  const ux = dirX / len;
  const uy = dirY / len;
  const pts: [number, number][] = [[cx, cy]];
  if (shape.kind === 'thrust') {
    const px = -uy * (shape.width / 2);
    const py = ux * (shape.width / 2);
    const ex = cx + ux * shape.length;
    const ey = cy + uy * shape.length;
    pts.push([cx + px, cy + py], [cx - px, cy - py], [ex + px, ey + py], [ex - px, ey - py]);
  } else {
    const half = (shape.arcDeg * Math.PI) / 360;
    const base = Math.atan2(uy, ux);
    const steps = 8;
    for (let i = 0; i <= steps; i++) {
      const a = base - half + (2 * half * i) / steps;
      pts.push([cx + Math.cos(a) * shape.radius, cy + Math.sin(a) * shape.radius]);
    }
  }
  const xs = pts.map((p) => p[0]);
  const ys = pts.map((p) => p[1]);
  const x0 = Math.min(...xs);
  const y0 = Math.min(...ys);
  return { x: x0, y: y0, w: Math.max(...xs) - x0, h: Math.max(...ys) - y0 };
}

/** 한 타의 판정 모양 (px, 진화·강화·타 배율 적용 후) */
export type HitShape =
  /** centerDeg = 정면에서 부채꼴 가운데까지 (right 기준, + = 아래). fromDeg→toDeg = 휘두름 방향 */
  | { kind: 'arc'; radius: number; arcDeg: number; centerDeg: number; fromDeg: number; toDeg: number }
  | { kind: 'thrust'; length: number; width: number; angleDeg: number; fromPx: number };

/** 아트 JSON 메모 (계약 art §6.1): 있으면 데이터 기본값 대신 */
export interface ShapeMemo {
  hitRadiusPx?: number;
  arcDeg?: number;
  arcFromDeg?: number;
  arcToDeg?: number;
  thrust?: { lengthPx: number; widthPx: number; angleDeg?: number; fromPx?: number };
}

/**
 * 판정 모양: 아트 메모(hitRadiusPx·arcDeg·thrust)가 있으면 그것, 없으면 데이터(arc 반경 = reach + width/2, thrust 길이·폭).
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
  const radius =
    typeof memo?.hitRadiusPx === 'number' ? memo.hitRadiusPx : (def.radiusPx ?? base.reach + base.width / 2);
  const arcDeg = typeof memo?.arcDeg === 'number' ? memo.arcDeg : (def.arcDeg ?? 120);
  const from = typeof memo?.arcFromDeg === 'number' ? memo.arcFromDeg : -arcDeg / 2;
  const to = typeof memo?.arcToDeg === 'number' ? memo.arcToDeg : arcDeg / 2;
  return { kind: 'arc', radius: radius * scale, arcDeg, centerDeg: (from + to) / 2, fromDeg: from, toDeg: to };
}

/**
 * 아트 각도 규약(right 기준 화면각, + = 아래)을 실제 공격 방향에 맞춘다: down·up 은 회전이라 그대로, left 는 좌우 반전(부호 반대)
 */
export function facingAngle(deg: number, facing: 'down' | 'up' | 'left' | 'right'): number {
  return facing === 'left' ? -deg : deg;
}

/** 방향 (dirX, dirY) 를 deg 만큼 돌린 단위벡터 */
export function rotateDir(dirX: number, dirY: number, deg: number): { x: number; y: number } {
  const a = Math.atan2(dirY, dirX) + (deg * Math.PI) / 180;
  return { x: Math.cos(a), y: Math.sin(a) };
}

/** 모양 판정 (thrust 는 angleDeg 만큼 돌리고 fromPx 만큼 떨어진 곳부터) */
export function shapeHit(
  cx: number,
  cy: number,
  dirX: number,
  dirY: number,
  shape: HitShape,
  t: HitTarget,
  facing: 'down' | 'up' | 'left' | 'right' = 'right',
): boolean {
  if (shape.kind === 'arc') {
    const c = rotateDir(dirX, dirY, facingAngle(shape.centerDeg, facing));
    return arcHit(cx, cy, c.x, c.y, shape.radius, shape.arcDeg, t);
  }
  const d = rotateDir(dirX, dirY, facingAngle(shape.angleDeg, facing));
  return thrustHit(cx + d.x * shape.fromPx, cy + d.y * shape.fromPx, d.x, d.y, shape.length, shape.width, t);
}

/** 모양의 외접 사각형 (thrust 는 돌린 방향·시작 거리 반영) */
export function hitShapeBounds(
  cx: number,
  cy: number,
  dirX: number,
  dirY: number,
  shape: HitShape,
  facing: 'down' | 'up' | 'left' | 'right' = 'right',
): { x: number; y: number; w: number; h: number } {
  if (shape.kind === 'arc') {
    const c = rotateDir(dirX, dirY, facingAngle(shape.centerDeg, facing));
    return shapeBounds(cx, cy, c.x, c.y, { kind: 'arc', radius: shape.radius, arcDeg: shape.arcDeg });
  }
  const d = rotateDir(dirX, dirY, facingAngle(shape.angleDeg, facing));
  return shapeBounds(cx + d.x * shape.fromPx, cy + d.y * shape.fromPx, d.x, d.y, {
    kind: 'thrust',
    length: shape.length,
    width: shape.width,
  });
}
