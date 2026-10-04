/**
 * 회피 시험 경기장 (Phaser 의존 없음): 무작위 모양(원·타원·불규칙 다각형·여러 섬) → 4px 칸 격자 바닥,
 * 가장자리부터의 갉아먹힘 순서(과제별 ErosionSpec, 없으면 무너지지 않음), 기둥 배치(③ 유도탄 과제).
 * 49라운드 2절 "서있는 공간도 매번 새롭고 공간 자체가 점점 갉아먹혀서" → 51라운드: 모양은 과제마다 새로, 갉아먹힘은 ②·⑤ 에서만.
 * 좌표는 경기장 중심 기준 월드 px.
 */
import { DODGE_TRIAL, type ArenaShape, type ErosionSpec, type TrialConfig } from './dodgeTrial';
import { clamp01 } from '../mathUtil';

/** 기둥 (중심 기준 px, 반지름 px) */
export interface Pillar {
  x: number;
  y: number;
  r: number;
}

/** 경기장 바닥 격자 */
export interface ArenaMask {
  shape: ArenaShape;
  cell: number;
  cols: number;
  rows: number;
  /** 격자 왼쪽 위 모서리 (중심 기준 px) */
  x0: number;
  y0: number;
  /** 1 = 처음 바닥 */
  floor: Uint8Array;
  /** 가장자리(빈 곳)까지의 칸 거리 (바닥만, 가장자리 칸 = 1) */
  depth: Uint16Array;
  /** 무너지는 시각 (과제 시작 기준 ms). Infinity = 끝까지 남음 */
  erodeAt: Float64Array;
  /** 바닥 칸 index 를 erodeAt 오름차순으로 */
  order: Int32Array;
  /** 처음 바닥 칸 수 */
  cells: number;
  /** 바닥 외곽 (중심 기준 px) */
  bounds: { minX: number; maxX: number; minY: number; maxY: number };
  erosion: ErosionSpec | null;
  pillars: Pillar[];
}

/** 목록에서 하나 (r ∈ [0,1)) */
export function pickShape(r: number, shapes: ArenaShape[]): ArenaShape {
  return shapes[Math.min(shapes.length - 1, Math.floor(r * shapes.length))] ?? 'circle';
}

/** 모양별 '바닥인가' 판정 함수 (중심 기준 px). rnd 로 모양 변수를 뽑는다 */
export function shapeTest(
  shape: ArenaShape,
  rnd: () => number,
  C: TrialConfig = DODGE_TRIAL,
): (x: number, y: number) => boolean {
  const A = C.ARENA;
  const R = A.RADIUS_TILES * 16;
  const range = ([a, b]: [number, number]) => a + (b - a) * rnd();
  const wobble = () => {
    const ph = [rnd(), rnd(), rnd()].map((v) => v * Math.PI * 2);
    const amp = [rnd(), rnd(), rnd()].map((v) => A.WOBBLE * (0.4 + 0.6 * v));
    return (th: number) =>
      1 + amp[0] * Math.sin(3 * th + ph[0]) + amp[1] * Math.sin(5 * th + ph[1]) + amp[2] * Math.sin(7 * th + ph[2]);
  };
  switch (shape) {
    case 'circle': {
      const w = wobble();
      return (x, y) => Math.hypot(x, y) <= R * w(Math.atan2(y, x));
    }
    case 'ellipse': {
      const ratio = range(A.ELLIPSE.RATIO);
      const rx = R * Math.sqrt(ratio);
      const ry = R / Math.sqrt(ratio);
      const tilt = (rnd() * 2 - 1) * A.ELLIPSE.TILT;
      const c = Math.cos(tilt);
      const s = Math.sin(tilt);
      const w = wobble();
      return (x, y) => {
        const u = x * c + y * s;
        const v = -x * s + y * c;
        return Math.hypot(u / rx, v / ry) <= w(Math.atan2(v, u));
      };
    }
    case 'polygon': {
      const P = A.POLYGON;
      const n = Math.round(range(P.VERTS));
      const step = (Math.PI * 2) / n;
      const start = rnd() * step;
      const verts = Array.from({ length: n }, (_, i) => {
        const a = start + i * step + (rnd() * 2 - 1) * P.ANGLE_JITTER * step;
        const r = R * range(P.RADIUS);
        return [Math.cos(a) * r * P.STRETCH_X, Math.sin(a) * r] as [number, number];
      });
      return (x, y) => pointInPolygon(x, y, verts);
    }
    case 'islands': {
      const I = A.ISLANDS;
      const isles: { x: number; y: number; r: number }[] = [{ x: 0, y: 0, r: R * I.CENTER_R }];
      const k = Math.round(range(I.COUNT));
      const step = (Math.PI * 2) / k;
      const start = rnd() * step;
      for (let i = 0; i < k; i++) {
        const a = start + i * step + (rnd() * 2 - 1) * 0.3 * step;
        const d = R * range(I.DIST);
        isles.push({ x: Math.cos(a) * d * I.STRETCH_X, y: Math.sin(a) * d * I.STRETCH_Y, r: R * range(I.R) });
      }
      const half = I.BRIDGE_PX / 2;
      return (x, y) => {
        for (const s of isles) if (Math.hypot(x - s.x, y - s.y) <= s.r) return true;
        for (let i = 1; i < isles.length; i++) if (segDist(x, y, 0, 0, isles[i].x, isles[i].y) <= half) return true;
        return false;
      };
    }
  }
}

/** 4방향 BFS: 빈 칸(격자 밖 포함)까지의 칸 거리. 가장자리 바닥 칸 = 1 */
export function floorDepth(floor: Uint8Array, cols: number, rows: number): Uint16Array {
  const depth = new Uint16Array(cols * rows);
  const queue: number[] = [];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const i = r * cols + c;
      if (!floor[i]) continue;
      const edge =
        c === 0 ||
        r === 0 ||
        c === cols - 1 ||
        r === rows - 1 ||
        !floor[i - 1] ||
        !floor[i + 1] ||
        !floor[i - cols] ||
        !floor[i + cols];
      if (edge) {
        depth[i] = 1;
        queue.push(i);
      }
    }
  }
  for (let q = 0; q < queue.length; q++) {
    const i = queue[q];
    const c = i % cols;
    const nb = [c > 0 ? i - 1 : -1, c < cols - 1 ? i + 1 : -1, i - cols, i + cols];
    for (const j of nb) {
      if (j < 0 || j >= floor.length || !floor[j] || depth[j]) continue;
      depth[j] = depth[i] + 1;
      queue.push(j);
    }
  }
  return depth;
}

/** 순위 비율 q (0~1) 의 칸이 무너지는 시각. 끝까지 남는 칸이면 Infinity */
export function erodeTimeForRank(q: number, E: ErosionSpec, C: TrialConfig = DODGE_TRIAL): number {
  const eat = 1 - E.endFloorFrac;
  if (q > eat) return Infinity;
  return E.startMs + (E.endMs - E.startMs) * Math.pow(Math.max(0, q) / eat, 1 / C.EROSION.POW);
}

/** 경과 ms 까지 무너진 바닥 비율 (0 ~ 1 − endFloorFrac) */
export function erodedFraction(elapsedMs: number, E: ErosionSpec | null, C: TrialConfig = DODGE_TRIAL): number {
  if (!E) return 0;
  const p = clamp01((elapsedMs - E.startMs) / Math.max(1, E.endMs - E.startMs));
  return (1 - E.endFloorFrac) * Math.pow(p, C.EROSION.POW);
}

/** 모양을 격자로 굽고 갉아먹힘 순서를 정한다. 중심 칸(시작 자리)은 항상 바닥이고 끝까지 남는다 */
export function buildArena(
  shape: ArenaShape,
  rnd: () => number,
  erosion: ErosionSpec | null = null,
  C: TrialConfig = DODGE_TRIAL,
): ArenaMask {
  const A = C.ARENA;
  const cell = A.CELL_PX;
  const cols = 2 * Math.ceil(A.HALF_W_PX / cell);
  const rows = 2 * Math.ceil(A.HALF_H_PX / cell);
  const x0 = (-cols / 2) * cell;
  const y0 = (-rows / 2) * cell;
  const test = shapeTest(shape, rnd, C);
  const floor = new Uint8Array(cols * rows);
  const bounds = { minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity };
  let cells = 0;
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const x = x0 + (c + 0.5) * cell;
      const y = y0 + (r + 0.5) * cell;
      if (!test(x, y)) continue;
      floor[r * cols + c] = 1;
      cells += 1;
      bounds.minX = Math.min(bounds.minX, x0 + c * cell);
      bounds.maxX = Math.max(bounds.maxX, x0 + (c + 1) * cell);
      bounds.minY = Math.min(bounds.minY, y0 + r * cell);
      bounds.maxY = Math.max(bounds.maxY, y0 + (r + 1) * cell);
    }
  }
  const depth = floorDepth(floor, cols, rows);
  const idx: number[] = [];
  const key = new Float64Array(cols * rows);
  for (let i = 0; i < floor.length; i++) {
    if (!floor[i]) continue;
    key[i] = depth[i] + rnd() * C.EROSION.NOISE_CELLS;
    idx.push(i);
  }
  idx.sort((a, b) => key[a] - key[b]);
  const erodeAt = new Float64Array(cols * rows).fill(Infinity);
  if (erosion)
    idx.forEach((i, rank) => {
      erodeAt[i] = erodeTimeForRank((rank + 1) / idx.length, erosion, C);
    });
  return {
    shape,
    cell,
    cols,
    rows,
    x0,
    y0,
    floor,
    depth,
    erodeAt,
    order: Int32Array.from(idx),
    cells,
    bounds,
    erosion,
    pillars: [],
  };
}

/** 중심 기준 px → 칸 index (격자 밖이면 -1) */
export function cellIndexAt(m: ArenaMask, x: number, y: number): number {
  const c = Math.floor((x - m.x0) / m.cell);
  const r = Math.floor((y - m.y0) / m.cell);
  if (c < 0 || r < 0 || c >= m.cols || r >= m.rows) return -1;
  return r * m.cols + c;
}

/** 경과 elapsedMs 에 그 자리가 아직 바닥인가 */
export function isFloorAt(m: ArenaMask, x: number, y: number, elapsedMs: number): boolean {
  const i = cellIndexAt(m, x, y);
  return i >= 0 && m.floor[i] === 1 && m.erodeAt[i] > elapsedMs;
}

/**
 * 기둥 n 개: 바닥 위(둘레 8점 + 여유가 전부 바닥), 시작 자리에서 CLEAR_CENTER 밖, 서로 MIN_GAP 이상.
 * 자리를 못 찾으면 덜 놓는다. 끝까지 무너지지 않는 칸에만 (갉아먹힘이 있으면 erodeAt = Infinity 인 칸).
 */
export function placePillars(m: ArenaMask, n: number, rnd: () => number, C: TrialConfig = DODGE_TRIAL): Pillar[] {
  const P = C.ARENA.PILLAR;
  const R = C.ARENA.RADIUS_TILES * 16;
  const out: Pillar[] = [];
  const range = ([a, b]: [number, number]) => a + (b - a) * rnd();
  const solid = (x: number, y: number) => isFloorAt(m, x, y, Number.MAX_VALUE);
  for (let tries = 0; out.length < n && tries < P.TRIES * Math.max(1, n); tries++) {
    const a = rnd() * Math.PI * 2;
    const d = R * range(P.DIST);
    const x = Math.cos(a) * d * 1.2;
    const y = Math.sin(a) * d * 0.8;
    const r = range(P.R_PX);
    if (Math.hypot(x, y) < P.CLEAR_CENTER_PX + r) continue;
    let ok = solid(x, y);
    for (let k = 0; ok && k < 8; k++) {
      const t = (k / 8) * Math.PI * 2;
      ok = solid(x + Math.cos(t) * (r + 6), y + Math.sin(t) * (r + 6));
    }
    if (!ok) continue;
    if (out.some((p) => Math.hypot(p.x - x, p.y - y) < p.r + r + P.MIN_GAP_PX)) continue;
    out.push({ x, y, r });
  }
  m.pillars = out;
  return out;
}

/** 점이 기둥 안인가 (여유 pad px) — 있으면 그 기둥 */
export function pillarAt(m: ArenaMask, x: number, y: number, pad = 0): Pillar | null {
  for (const p of m.pillars) if (Math.hypot(x - p.x, y - p.y) < p.r + pad) return p;
  return null;
}

function pointInPolygon(x: number, y: number, v: [number, number][]): boolean {
  let inside = false;
  for (let i = 0, j = v.length - 1; i < v.length; j = i++) {
    const [xi, yi] = v[i];
    const [xj, yj] = v[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

function segDist(px: number, py: number, ax: number, ay: number, bx: number, by: number): number {
  const dx = bx - ax;
  const dy = by - ay;
  const l2 = dx * dx + dy * dy;
  const t = l2 > 0 ? clamp01(((px - ax) * dx + (py - ay) * dy) / l2) : 0;
  return Math.hypot(px - (ax + dx * t), py - (ay + dy * t));
}
