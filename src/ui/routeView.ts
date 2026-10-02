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
