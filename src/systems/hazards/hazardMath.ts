/**
 * 61라운드 단계 2 신규 적 투사체 계산 (Phaser 없음 · 단위 테스트): 독주 행상 화염 술병 포물선 · 술통 짐꾼 술통 굴림·되치기.
 */

export interface Pt {
  x: number;
  y: number;
}

/**
 * 포물선 한 점 (t = 0..1): 땅 위 자리는 from → to 직선, 높이는 sin 곡선(꼭대기 apexPx) + 손 높이(handPx → 0 으로 줄어듦).
 * 반환 y = 그림 자리(땅 y − 높이) · groundY = 그림자 자리
 */
export function bottleArcAt(t: number, from: Pt, to: Pt, apexPx: number, handPx: number): Pt & { groundY: number } {
  const k = Math.max(0, Math.min(1, t));
  const gx = from.x + (to.x - from.x) * k;
  const gy = from.y + (to.y - from.y) * k;
  const h = Math.sin(k * Math.PI) * apexPx + handPx * (1 - k);
  return { x: gx, y: gy - h, groundY: gy };
}

/** 던질 자리: 대상까지 거리를 [minPx, maxPx] 로 자른다 (대상이 겹쳐 있으면 maxPx 오른쪽) */
export function clampThrowTarget(from: Pt, target: Pt, minPx: number, maxPx: number): Pt {
  const dx = target.x - from.x;
  const dy = target.y - from.y;
  const d = Math.hypot(dx, dy);
  if (d === 0) return { x: from.x + maxPx, y: from.y };
  const k = Math.max(minPx, Math.min(maxPx, d)) / d;
  return { x: from.x + dx * k, y: from.y + dy * k };
}

/**
 * 독주 행상 이동 의도: 너무 가까우면 도망(flee) · 유지 거리보다 가까우면 물러남(back) · 멀면 다가감(close) · 그 사이면 멈춤(hold)
 */
export function peddlerIntent(
  distTiles: number,
  p: { fleeTiles: number; keepMinTiles: number; keepMaxTiles: number },
): 'flee' | 'back' | 'close' | 'hold' {
  if (distTiles < p.fleeTiles) return 'flee';
  if (distTiles < p.keepMinTiles) return 'back';
  if (distTiles > p.keepMaxTiles) return 'close';
  return 'hold';
}

/** 단위 벡터 (0 이면 fallback) */
export function unit(dx: number, dy: number, fallback: Pt = { x: 1, y: 0 }): Pt {
  const len = Math.hypot(dx, dy);
  return len > 0 ? { x: dx / len, y: dy / len } : { ...fallback };
}

/**
 * 되치기 방향: 주인공 공격 방향(근접 판정 방향·화살 속도)으로. 공격 방향이 없으면 굴러오던 반대 방향
 */
export function deflectDir(rollDir: Pt, attackDir: Pt): Pt {
  const a = unit(attackDir.x, attackDir.y, { x: 0, y: 0 });
  if (a.x === 0 && a.y === 0) return unit(-rollDir.x, -rollDir.y);
  return a;
}

/**
 * 술통 한 번 전진: 한 걸음(stepPx 이하)씩 나아가며 앞쪽 가장자리(반경 r)가 막힌 칸에 닿으면 멈춘다.
 * 반환 = 새 위치 · 실제로 간 거리 · 막혔는지
 */
export function advanceBarrel(
  pos: Pt,
  dir: Pt,
  distPx: number,
  radiusPx: number,
  blocked: (x: number, y: number) => boolean,
  stepPx = 3,
): { x: number; y: number; moved: number; hit: boolean } {
  let { x, y } = pos;
  let moved = 0;
  let left = distPx;
  while (left > 0) {
    const s = Math.min(stepPx, left);
    const nx = x + dir.x * s;
    const ny = y + dir.y * s;
    if (blocked(nx + dir.x * radiusPx, ny + dir.y * radiusPx)) return { x, y, moved, hit: true };
    x = nx;
    y = ny;
    moved += s;
    left -= s;
  }
  return { x, y, moved, hit: false };
}

/** 원(중심·반경)과 사각형(x, y, w, h)이 겹치는가 */
export function circleHitsRect(c: Pt, r: number, rect: { x: number; y: number; w: number; h: number }): boolean {
  const cx = Math.max(rect.x, Math.min(c.x, rect.x + rect.w));
  const cy = Math.max(rect.y, Math.min(c.y, rect.y + rect.h));
  return (c.x - cx) ** 2 + (c.y - cy) ** 2 <= r * r;
}

/** 굴림 회전 프레임 (굴러간 거리 / 둘레 × 프레임 수) */
export function rollFrame(rolledPx: number, circumferencePx: number, frames: number): number {
  if (frames <= 0) return 0;
  return Math.floor((Math.max(0, rolledPx) / Math.max(1, circumferencePx)) * frames) % frames;
}
