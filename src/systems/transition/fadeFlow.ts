/**
 * 62 시스템 H (도영 님 추가 지시) 지도에서 고른 뒤의 짧은 암전 'fade' — 전환 시작 정보 (순수).
 * 노드 지도: 고른 노드의 지역(보스 = 'boss')·종류·id. 수련장: 방으로(nodeKind training|boss · nodeId 방 id) / 방 → 지도 마당(nodeId 없음).
 * 입구 그림(doorKey)·줌 중심(from)은 싣지 않는다 — 덮기는 UI 의 먹 번짐 암전 (렌더러가 없으면 카메라 암전).
 */
import type { UiTransitionBegin } from '../../contract/ui';
import { nodeRegionId, type RouteNode } from '../route';

export type FadeInfo = Omit<UiTransitionBegin, 'id' | 'skippable'> & { mode: 'fade'; durationMs: number };

/** 노드 지도에서 노드를 고른 뒤 */
export function nodeFadeInfo(
  stageId: string,
  node: Pick<RouteNode, 'id' | 'kind' | 'col'>,
  durationMs: number,
): FadeInfo {
  return { mode: 'fade', region: nodeRegionId(stageId, node), nodeKind: node.kind, nodeId: node.id, durationMs };
}

/** 수련장: room = 고른 방(지도 → 방) · 없으면 방 → 지도 마당 */
export function trainingFadeInfo(room: { id: string; boss: boolean } | null, durationMs: number): FadeInfo {
  return {
    mode: 'fade',
    region: 'training',
    nodeKind: room?.boss ? 'boss' : 'training',
    ...(room ? { nodeId: room.id } : {}),
    durationMs,
  };
}
