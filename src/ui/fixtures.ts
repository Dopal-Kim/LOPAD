import type { UiRoute, UiRouteNode } from '../contract/ui';

/**
 * 테스트용 노드 지도 값 (60라운드). 계약 §14.5 의 노드·지도 필드(reward·risk·riskText·prefixes·eventName·hidden·grade·
 * intel)를 **모두 채운다** — 계약 코드(`src/contract/ui.ts`)가 이 필드를 임시로 선택(`?`)으로 둔 것을 시스템이 필수로
 * 되돌려도 UI 테스트가 깨지지 않게 (계약 §14.10 60라운드 메모).
 */
export function routeNode(p: Pick<UiRouteNode, 'id'> & Partial<UiRouteNode>): UiRouteNode {
  return {
    type: 'battle',
    name: p.id,
    col: 0,
    row: 0,
    links: [],
    state: 'locked',
    reward: null,
    risk: null,
    riskText: '',
    prefixes: null,
    eventName: null,
    hidden: null,
    grade: null,
    ...p,
  };
}

/** 지도 정보를 하나도 사지 않은 상태 */
export const NO_INTEL: NonNullable<UiRoute['intel']> = { nextTier: false, fullFloor: false, hiddenLocated: false };

export function routeOf(p: Pick<UiRoute, 'nodes'> & Partial<UiRoute>): UiRoute {
  return { floor: 1, currentId: null, choosing: false, intel: { ...NO_INTEL }, ...p };
}
