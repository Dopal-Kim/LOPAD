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
    return { pos, ease: o.ease, rowStep: 0, yAt: () => bottom, scaleAt: () => 1 };
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
  return { pos, ease, rowStep, yAt, scaleAt };
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
