/**
 * 48라운드 노드 지도의 순수 계산 (Phaser 없이 테스트한다). 계약 `ui-system-interface.md` §10.
 * 좌표는 화면 px. 노드는 왼→오(col) 진행, 같은 단계 안에서는 row 로 세로 배치(단계마다 가운데 정렬).
 */
import type { UiNodeState, UiRoute, UiRouteNode } from '../contract/ui';

export interface Area {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface RouteLayout {
  /** 노드 id → 중심 (정수) */
  pos: Map<string, { x: number; y: number }>;
  /** 단계 사이 가로 간격·줄 사이 세로 간격 (정수) */
  colStep: number;
  rowStep: number;
}

/**
 * 노드 중심 좌표. 단계 수만큼 영역 폭을 나누되 `colMax` 를 넘지 않게, 줄 간격도 `rowMax` 이하로.
 * 각 단계는 그 단계의 줄 수(max row + 1)로 세로 가운데 정렬 — 갈림길이 갈라졌다 합쳐지는 모양.
 */
export function layoutRoute(nodes: UiRouteNode[], area: Area, colMax: number, rowMax: number): RouteLayout {
  const pos = new Map<string, { x: number; y: number }>();
  if (!nodes.length) return { pos, colStep: 0, rowStep: 0 };
  const minCol = Math.min(...nodes.map((n) => n.col));
  const maxCol = Math.max(...nodes.map((n) => n.col));
  const cols = maxCol - minCol + 1;
  const rowsIn = new Map<number, number>();
  for (const n of nodes) rowsIn.set(n.col, Math.max(rowsIn.get(n.col) ?? 0, n.row + 1));
  const maxRows = Math.max(...rowsIn.values());
  const colStep = cols > 1 ? Math.min(colMax, Math.floor(area.w / cols)) : 0;
  const rowStep = maxRows > 1 ? Math.min(rowMax, Math.floor(area.h / maxRows)) : 0;
  const x0 = area.x + Math.round((area.w - colStep * (cols - 1)) / 2);
  const cy = area.y + area.h / 2;
  for (const n of nodes) {
    const rows = rowsIn.get(n.col) ?? 1;
    pos.set(n.id, {
      x: x0 + (n.col - minCol) * colStep,
      y: Math.round(cy + (n.row - (rows - 1) / 2) * rowStep),
    });
  }
  return { pos, colStep, rowStep };
}

/** 그리기·고르기 순서: 단계 → 줄 */
export function sortNodes(nodes: UiRouteNode[]): UiRouteNode[] {
  return [...nodes].sort((a, b) => a.col - b.col || a.row - b.row);
}

/** 목록 안에서 한 칸 앞뒤로 (끝에서 돌아온다). 현재가 없으면 delta>0 이면 처음, 아니면 끝 */
export function cycle(ids: string[], cur: string | null, delta: 1 | -1): string | null {
  if (!ids.length) return null;
  const i = cur ? ids.indexOf(cur) : -1;
  if (i < 0) return delta > 0 ? ids[0] : ids[ids.length - 1];
  return ids[(i + delta + ids.length) % ids.length];
}

/** 남은 단계 수 (현재 노드 → 마지막 단계). 현재가 없으면 전체 단계 수 */
export function remainingSteps(route: UiRoute): number {
  if (!route.nodes.length) return 0;
  const maxCol = Math.max(...route.nodes.map((n) => n.col));
  const minCol = Math.min(...route.nodes.map((n) => n.col));
  const cur = route.nodes.find((n) => n.id === route.currentId);
  return cur ? maxCol - cur.col : maxCol - minCol + 1;
}

/** 연결선 종류: 지나온 길 / 지금 고를 수 있는 길 / 그 외(흐림) */
export type LinkKind = 'walked' | 'option' | 'faint';
const WALKED: ReadonlySet<UiNodeState> = new Set<UiNodeState>(['cleared', 'current']);
export function linkKind(a: UiNodeState, b: UiNodeState): LinkKind {
  if (WALKED.has(a) && WALKED.has(b)) return 'walked';
  if (a === 'current' && b === 'available') return 'option';
  return 'faint';
}

/**
 * 점선 점 위치: (x1,y1)→(x2,y2) 선분에서 양 끝을 `trimA`/`trimB` 만큼 비우고 `step` 간격으로 찍는다. 정수 좌표.
 * 남는 길이를 양쪽에 반씩 나눠 점이 가운데 정렬되게 한다.
 */
export function dottedPoints(
  x1: number,
  y1: number,
  x2: number,
  y2: number,
  trimA: number,
  trimB: number,
  step: number,
): { x: number; y: number }[] {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const len = Math.hypot(dx, dy);
  const usable = len - trimA - trimB;
  if (len <= 0 || usable <= 0 || step <= 0) return [];
  const ux = dx / len;
  const uy = dy / len;
  const n = Math.floor(usable / step) + 1;
  const start = trimA + (usable - (n - 1) * step) / 2;
  const pts: { x: number; y: number }[] = [];
  for (let i = 0; i < n; i++) {
    const d = start + i * step;
    pts.push({ x: Math.round(x1 + ux * d), y: Math.round(y1 + uy * d) });
  }
  return pts;
}

/** 노드 지도로 그릴 수 있는 경로인가 (null·빈 노드는 기존 방 미니맵 동작) */
export function hasRoute(route: UiRoute | null | undefined): route is UiRoute {
  return Boolean(route && route.nodes && route.nodes.length > 0);
}

// ---------------------------------------------------------------------------------------------
// 49라운드: 입체(원근) 지도 — 진행(col)은 아래(가까움) → 위(멂), 같은 단계의 줄(row)은 좌우로 벌린다.

export interface PerspectiveOptions {
  /** 가장 가까운 단계의 줄 간격 상한 (px) */
  rowMax: number;
  /** 가장 먼 단계의 크기 비 (0..1). 좌우 폭·그림자·높이가 이 비율로 줄어든다 */
  farScale: number;
  /** 멀어질수록 단계 간격이 좁아지는 정도 (0 = 고르게) */
  ease: number;
  /** 단계 사이 최소 세로 간격. 원근으로 이보다 좁아지면 원근을 풀어 고르게 둔다 */
  minGap: number;
  /** 영역 위·아래 안쪽 여백 (노드 높이·이름표 자리) */
  padTop: number;
  padBottom: number;
}

export interface PerspectivePoint {
  /** 땅에 닿은 점 (노드 그림자 중심, 정수) */
  x: number;
  y: number;
  /** 깊이 0(가까움)..1(멂) */
  depth: number;
  /** 크기 비 1(가까움)..farScale(멂) */
  scale: number;
}

export interface PerspectiveLayout {
  pos: Map<string, PerspectivePoint>;
  /** 실제로 쓴 ease (최소 간격 때문에 0 으로 풀렸을 수 있다) */
  ease: number;
  /** 가장 가까운 단계의 줄 간격 */
  rowStep: number;
  /** 깊이 → 화면 y (지도 격자선용) */
  yAt: (depth: number) => number;
  /** 깊이 → 크기 비 */
  scaleAt: (depth: number) => number;
  /** 가장 먼 곳의 크기 비 (들림·그림자 보간 기준) */
  farScale: number;
}

/** 0..1 깊이를 원근 곡선으로 (멀수록 촘촘). ease 0 이면 직선 */
export function perspectiveCurve(t: number, ease: number): number {
  const c = Math.max(0, Math.min(1, t));
  if (ease <= 0) return c;
  return (1 - 1 / (1 + ease * c)) / (1 - 1 / (1 + ease));
}

/**
 * 원근 배치. 첫 단계가 영역 아래(가까움), 마지막 단계가 위(멂). 단계 간격은 멀수록 좁고, 좌우 폭은 farScale 까지 줄어든다.
 * 단계 수가 많아 가장 먼 간격이 minGap 보다 좁아지면 ease 를 0 으로 (고른 간격) 되돌린다.
 */
export function layoutPerspective(nodes: UiRouteNode[], area: Area, o: PerspectiveOptions): PerspectiveLayout {
  const pos = new Map<string, PerspectivePoint>();
  const top = area.y + o.padTop;
  const bottom = area.y + area.h - o.padBottom;
  const usable = Math.max(0, bottom - top);
  const cx = area.x + area.w / 2;
  if (!nodes.length) {
    return { pos, ease: o.ease, rowStep: 0, yAt: () => bottom, scaleAt: () => 1, farScale: o.farScale };
  }
  const minCol = Math.min(...nodes.map((n) => n.col));
  const maxCol = Math.max(...nodes.map((n) => n.col));
  const cols = maxCol - minCol + 1;
  const rowsIn = new Map<number, number>();
  for (const n of nodes) rowsIn.set(n.col, Math.max(rowsIn.get(n.col) ?? 0, n.row + 1));
  const maxRows = Math.max(...rowsIn.values());
  let ease = o.ease;
  if (cols > 1 && ease > 0) {
    const lastGap = usable * (1 - perspectiveCurve((cols - 2) / (cols - 1), ease));
    if (lastGap < o.minGap) ease = 0;
  }
  const yAt = (depth: number): number => Math.round(bottom - usable * perspectiveCurve(depth, ease));
  const scaleAt = (depth: number): number => 1 - (1 - o.farScale) * perspectiveCurve(depth, ease);
  const rowStep = maxRows > 1 ? Math.min(o.rowMax, Math.floor((area.w * 0.9) / maxRows)) : 0;
  for (const n of nodes) {
    const depth = cols > 1 ? (n.col - minCol) / (cols - 1) : 0;
    const scale = scaleAt(depth);
    const rows = rowsIn.get(n.col) ?? 1;
    pos.set(n.id, {
      x: Math.round(cx + (n.row - (rows - 1) / 2) * rowStep * scale),
      y: yAt(depth),
      depth,
      scale,
    });
  }
  return { pos, ease, rowStep, yAt, scaleAt, farScale: o.farScale };
}

/**
 * 계단식 사다리꼴 (펼친 양피지). 아래 폭 wBottom, 위 폭 wTop, 가운데 cx. 줄마다 [x, y, w] (정수).
 */
export function trapezoidRows(cx: number, yTop: number, yBottom: number, wTop: number, wBottom: number) {
  const rows: { x: number; y: number; w: number }[] = [];
  const h = Math.max(1, yBottom - yTop);
  for (let y = yTop; y <= yBottom; y++) {
    const t = (y - yTop) / h;
    const w = Math.round(wTop + (wBottom - wTop) * t);
    rows.push({ x: Math.round(cx - w / 2), y, w });
  }
  return rows;
}

/** 픽셀 타원 줄 (그림자). 중심 cx·cy, 반지름 rx·ry. 줄마다 [x, y, w] (정수) */
export function ellipseRows(cx: number, cy: number, rx: number, ry: number) {
  const rows: { x: number; y: number; w: number }[] = [];
  const R = Math.max(1, Math.round(ry));
  for (let dy = -R; dy <= R; dy++) {
    const k = 1 - (dy * dy) / ((R + 0.5) * (R + 0.5));
    const half = Math.round(rx * Math.sqrt(Math.max(0, k)));
    if (half <= 0) continue;
    rows.push({ x: Math.round(cx - half), y: Math.round(cy + dy), w: half * 2 });
  }
  return rows;
}

// ---------------------------------------------------------------------------------------------
// 50라운드: 지도 배경 일러스트 위 배치 — 그림 속 길(점 목록)을 따라 col 비율로 놓고, row 는 길에 수직으로 벌린다.

/** 층별 지도 그림 위 길 (그림 원본 px 좌표) */
export interface MapPathSpec {
  /** 그림 원본 크기 */
  srcW: number;
  srcH: number;
  /** 길 점 목록: 첫 단계(col 최소) → 마지막 단계(보스). 길이 비율로 보간한다 */
  points: readonly (readonly [number, number])[];
  /** 같은 단계 줄 간격 (원본 px, 길에 수직) */
  rowSpread: number;
  /** 그림 가장자리에서 띄우는 여백 (원본 px) */
  margin: number;
  /** 그림 위쪽(먼 곳)의 크기 비 — 일러스트가 거의 평면이라 원근보다 약하게 */
  farScale: number;
  /** 접선을 구할 때 앞뒤로 보는 거리 (원본 px) — 꺾인 점에서 줄이 튀지 않게 */
  tangentSpan: number;
}

/** 점 목록을 길이로 매개화한 길. at(s) = 시작에서 길이 s 인 점 */
export function pathSampler(points: readonly (readonly [number, number])[]) {
  const pts = points.length ? points : [[0, 0] as const];
  const acc: number[] = [0];
  for (let i = 1; i < pts.length; i++)
    acc.push(acc[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  const length = acc[acc.length - 1];
  const at = (s: number): { x: number; y: number } => {
    if (pts.length === 1 || length <= 0) return { x: pts[0][0], y: pts[0][1] };
    const c = Math.max(0, Math.min(length, s));
    let i = 1;
    while (i < acc.length - 1 && acc[i] < c) i++;
    const seg = acc[i] - acc[i - 1];
    const t = seg > 0 ? (c - acc[i - 1]) / seg : 0;
    return {
      x: pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * t,
      y: pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * t,
    };
  };
  /** 길이 s 에서의 단위 접선 (앞뒤 span 거리의 두 점으로) */
  const tangent = (s: number, span: number): { x: number; y: number } => {
    const a = at(s - span);
    const b = at(s + span);
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const len = Math.hypot(dx, dy);
    return len > 0 ? { x: dx / len, y: dy / len } : { x: 1, y: 0 };
  };
  return { length, at, tangent };
}

/** 그림(srcW×srcH)을 영역 안에 비율 유지로 맞춘 사각형 (가운데, 정수) */
export function fitContain(area: Area, srcW: number, srcH: number): Area {
  const s = Math.min(area.w / srcW, area.h / srcH);
  const w = Math.floor(srcW * s);
  const h = Math.floor(srcH * s);
  return { x: Math.round(area.x + (area.w - w) / 2), y: Math.round(area.y + (area.h - h) / 2), w, h };
}

/** w×h 를 빈틈없이 덮도록 원본(srcW×srcH)에서 잘라 올 영역 (가운데 기준, 정수) */
export function coverCrop(srcW: number, srcH: number, w: number, h: number) {
  const s = Math.max(w / srcW, h / srcH);
  const sw = Math.min(srcW, Math.round(w / s));
  const sh = Math.min(srcH, Math.round(h / s));
  return { sx: Math.floor((srcW - sw) / 2), sy: Math.floor((srcH - sh) / 2), sw, sh };
}

/**
 * 일러스트 좌표계 배치. 단계(col)는 길 전체 길이를 (단계 수 - 1) 로 나눈 비율 자리, 같은 단계의 줄(row)은 그 자리의
 * 접선에 수직으로 rowSpread 간격(가운데 정렬, row 0 = 길 진행 방향의 왼쪽 = 화면에서 대개 위). 그림 밖으로 나가지 않게 margin 안으로.
 * 깊이 = 그림 위쪽일수록 멂(0 가까움..1 멂), 크기 비 = 1..farScale. `rect` 는 그림이 화면에 놓인 사각형.
 */
export function layoutOnPath(nodes: UiRouteNode[], rect: Area, spec: MapPathSpec): PerspectiveLayout {
  const pos = new Map<string, PerspectivePoint>();
  const kx = rect.w / spec.srcW;
  const ky = rect.h / spec.srcH;
  const scaleAt = (depth: number): number => 1 - (1 - spec.farScale) * Math.max(0, Math.min(1, depth));
  const yAt = (depth: number): number => Math.round(rect.y + rect.h * (1 - depth));
  const base = { ease: 0, yAt, scaleAt, farScale: spec.farScale };
  if (!nodes.length) return { pos, rowStep: 0, ...base };
  const path = pathSampler(spec.points);
  const minCol = Math.min(...nodes.map((n) => n.col));
  const maxCol = Math.max(...nodes.map((n) => n.col));
  const cols = maxCol - minCol + 1;
  const rowsIn = new Map<number, number>();
  for (const n of nodes) rowsIn.set(n.col, Math.max(rowsIn.get(n.col) ?? 0, n.row + 1));
  for (const n of nodes) {
    const t = cols > 1 ? (n.col - minCol) / (cols - 1) : 0;
    const s = t * path.length;
    const p = path.at(s);
    const tg = path.tangent(s, spec.tangentSpan);
    const rows = rowsIn.get(n.col) ?? 1;
    const off = (n.row - (rows - 1) / 2) * spec.rowSpread;
    // 법선 = 접선을 시계 반대로 90° (화면 좌표: y 아래) → 오른쪽으로 가는 길이면 아래. row 0(음수 쪽)이 위로
    const qx = Math.max(spec.margin, Math.min(spec.srcW - spec.margin, p.x - tg.y * off));
    const qy = Math.max(spec.margin, Math.min(spec.srcH - spec.margin, p.y + tg.x * off));
    const depth = Math.max(0, Math.min(1, 1 - qy / spec.srcH));
    pos.set(n.id, {
      x: Math.round(rect.x + qx * kx),
      y: Math.round(rect.y + qy * ky),
      depth,
      scale: scaleAt(depth),
    });
  }
  return { pos, rowStep: Math.round(spec.rowSpread * kx), ...base };
}
