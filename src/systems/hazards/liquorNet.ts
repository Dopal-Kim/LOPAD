/**
 * 54라운드 Q3 술 웅덩이 연결망 (Phaser 의존 없음): 불이 '연결된' 웅덩이를 따라 칸마다 msPerCell 씩 늦게 번진다.
 * 두 웅덩이 사각형 사이 틈이 gapPx 이하이면 연결.
 */
export interface CellRect {
  x: number;
  y: number;
  w: number;
  h: number;
}

/** 두 사각형 사이 틈(축별 거리 중 큰 값, 겹치면 0) */
export function rectGap(a: CellRect, b: CellRect): number {
  const dx = Math.max(0, Math.max(a.x, b.x) - Math.min(a.x + a.w, b.x + b.w));
  const dy = Math.max(0, Math.max(a.y, b.y) - Math.min(a.y + a.h, b.y + b.h));
  return Math.max(dx, dy);
}

export function linked(a: CellRect, b: CellRect, gapPx: number): boolean {
  return rectGap(a, b) <= gapPx;
}

/** 이웃 목록 */
export function neighbors(cells: readonly CellRect[], i: number, gapPx: number): number[] {
  const out: number[] = [];
  for (let j = 0; j < cells.length; j++) if (j !== i && linked(cells[i], cells[j], gapPx)) out.push(j);
  return out;
}

/**
 * start 칸에서 번지는 순서: 칸 번호 → 불붙는 지연 ms (BFS 단계 × msPerCell). 연결되지 않은 칸은 없음.
 * `canBurn(j)` 가 false 인 칸(이미 탔거나 불붙을 수 없는 칸)은 지나가지 않는다
 */
export function spreadDelays(
  cells: readonly CellRect[],
  start: number,
  gapPx: number,
  msPerCell: number,
  canBurn: (j: number) => boolean = () => true,
): Map<number, number> {
  const out = new Map<number, number>([[start, 0]]);
  const queue = [start];
  while (queue.length > 0) {
    const i = queue.shift()!;
    const d = out.get(i)!;
    for (const j of neighbors(cells, i, gapPx)) {
      if (out.has(j) || !canBurn(j)) continue;
      out.set(j, d + msPerCell);
      queue.push(j);
    }
  }
  return out;
}

/** 꺾은선을 따라 간격 stepPx 마다 놓을 칸 중심 (같은 칸 격자 tile 에 둘이 들어가면 하나만) */
export function cellsAlong(
  points: readonly { x: number; y: number }[],
  stepPx: number,
  tile: number,
): { tx: number; ty: number }[] {
  const out: { tx: number; ty: number }[] = [];
  const seen = new Set<string>();
  const put = (x: number, y: number) => {
    const tx = Math.floor(x / tile);
    const ty = Math.floor(y / tile);
    const k = `${tx},${ty}`;
    if (seen.has(k)) return;
    seen.add(k);
    out.push({ tx, ty });
  };
  if (points.length === 0) return out;
  put(points[0].x, points[0].y);
  for (let i = 1; i < points.length; i++) {
    const a = points[i - 1];
    const b = points[i];
    const len = Math.hypot(b.x - a.x, b.y - a.y);
    const n = Math.max(1, Math.ceil(len / stepPx));
    for (let k = 1; k <= n; k++) put(a.x + ((b.x - a.x) * k) / n, a.y + ((b.y - a.y) * k) / n);
  }
  return out;
}
