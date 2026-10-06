/**
 * 61 단계 6 (계약 §19) 그림 속 입구 전환 — UI 씬끼리 나누는 작은 상태 (Phaser 없음).
 * - 전환 중인가 · 덮였는가: HUD 는 배너·지역 카드를 전환이 끝날 때까지 미루고, 노드 지도·수련장 지도는 덮일 때까지 남는다
 *   (전환이 지도를 캡처해 그 위 노드 자리로 파고들어야 하므로).
 * - 파고들 자리: 노드 지도·수련장 지도는 UI 가 그리므로 고른 노드(방 자리)의 화면 좌표는 UI 가 가장 정확히 안다.
 *   지도가 고를 때 적어 두고, 전환 씬이 'enterNode'·'training' 시작 때 꺼내 쓴다(시스템 `from` 보다 먼저, 잠깐만 유효).
 * 시각은 `performance.now()` (씬마다 시계가 달라서).
 */

let busy = false;
let covered = false;
let origin: { kind: OriginKind; id: string; x: number; y: number; at: number } | null = null;

export type OriginKind = 'route' | 'training';

/** 적어 둔 자리가 유효한 시간 (ms) — 고른 뒤 시스템이 전환을 시작하기까지 */
export const ORIGIN_TTL_MS = 4000;

export function transitionBusy(): boolean {
  return busy;
}

/** 시작했지만 아직 덮이지 않았다 (지도가 남아 있어야 하는 동안) */
export function transitionOpening(): boolean {
  return busy && !covered;
}

export function setTransitionBusy(on: boolean): void {
  busy = on;
  covered = false;
}

export function setTransitionCovered(): void {
  covered = true;
}

/** 지도에서 고른 노드·방 자리 (논리 960×540 화면 좌표) */
export function noteTransitionOrigin(kind: OriginKind, id: string, x: number, y: number, now: number): void {
  origin = { kind, id, x, y, at: now };
}

/**
 * 적어 둔 자리를 꺼낸다 (한 번 쓰면 지움). 종류가 다르거나, id 가 주어졌는데 다르거나, 오래됐으면 null
 */
export function takeTransitionOrigin(
  kind: OriginKind,
  id: string | null | undefined,
  now: number,
): { x: number; y: number } | null {
  const o = origin;
  origin = null;
  if (!o || o.kind !== kind || now - o.at > ORIGIN_TTL_MS) return null;
  if (id && o.id && id !== o.id) return null;
  return { x: o.x, y: o.y };
}
