/**
 * 62 루프 2 시스템 E 시스템 내부 이벤트 (EventBus `Events` 에 펼쳐 넣는다 — 공유 파일 EventBus.ts 를 덜 건드리려 따로 둔다).
 * 음향은 이 이름으로 효과음을 붙일 수 있다 (sound 요청 — CHANGELOG 62 루프 2 시스템 E 절).
 */
export const LOOP2E_EVENTS = {
  /** 외벽 문이 열렸다 (`DoorOpenedPayload`) — 노드 출구·층 출구·수련장 방 출구. 막힘이 걷히고 빛이 켜지는 순간 (음향: 문 열림) */
  DOOR_OPENED: 'door:opened',
  /** 문 자동 걸음 (`DoorWalkPayload`) — out 문으로 걸어 들어감 · in 반대편 문에서 걸어 나옴 · back 지도 취소로 문턱 안으로 물러남 */
  DOOR_WALK: 'door:walk',
  /** 메뉴 입력 가드가 선택을 막았다 (`MenuEventPayload` id·key) — 런 로그·디버그용 (소리 없음) */
  MENU_GUARDED: 'menu:guarded',
} as const;

export type DoorSidePayload = 'north' | 'south' | 'east' | 'west';

export interface DoorOpenedPayload {
  side: DoorSidePayload;
  /** node 노드 출구(다음 노드) · floor 층 출구 · training 수련장 방 출구 */
  kind: 'node' | 'floor' | 'training';
}

export interface DoorWalkPayload {
  phase: 'out' | 'in' | 'back';
  side: DoorSidePayload;
  /** 걸음 길이 (ms, 예상) */
  ms: number;
}
