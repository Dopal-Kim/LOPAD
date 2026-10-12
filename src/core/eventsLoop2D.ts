/**
 * 62 루프 2 시스템 D 시스템 내부 이벤트 (EventBus `Events` 에 펼쳐 넣는다 — 공유 파일 EventBus.ts 를 덜 건드리려 따로 둔다).
 * 음향은 이 이름으로 효과음을 붙일 수 있다(sound 요청 — CHANGELOG 62 루프 2 시스템 D 절).
 */
export const LOOP2D_EVENTS = {
  /** P2-5: 나가기 자동 저장 (`RunSuspendedPayload`) */
  RUN_SUSPENDED: 'run:suspended',
  /** P2-5: 런 포기 (`RunAbandonedPayload`) — 바로 뒤 PLAYER_DIED */
  RUN_ABANDONED: 'run:abandoned',
  /** P1-12: 이벤트 NPC 에게 말 걸었다 (`EventTalkPayload`) */
  EVENT_TALK: 'event:talk',
  /** P1-12: 이벤트 선택 결과 (`EventResolvedPayload`) */
  EVENT_RESOLVED: 'event:resolved',
  /** P1-13: 노점 칸 카드가 떴다/사라졌다 (`StallFocusPayload`) */
  STALL_FOCUS: 'shop:stall-focus',
  /** P1-13: 상인에게 말 걸었다 */
  SHOP_TALK: 'shop:talk',
  /** P2-3: 노드 시련(완 조건)이 깨졌다 (`NodeTrialBrokenPayload`) — 음향 trial_fail 후보. 성공은 NODE_GRADED perfect */
  NODE_TRIAL_BROKEN: 'node:trial-broken',
  /** P2-6: 다음 노드 미리 읽기 시작·끝 (`PrefetchPayload`) */
  NODE_PREFETCH: 'node:prefetch',
  /** 음향 sound §13: 방 마지막 처치 슬로모를 실제로 걸었다 (`FeelSlowmoPayload`) → last_kill_slow */
  FEEL_SLOWMO: 'feel:slowmo',
  /** 음향 sound §13: 설정 켜기/끄기 칸이 바뀌었다 (`UiSettingToggledPayload`) → ui_toggle */
  UI_SETTING_TOGGLED: 'settings:toggled',
} as const;

export type RunSuspendedPayload = { nodeId: string | null; cleared: boolean };
export type RunAbandonedPayload = { nodeId: string | null };
export type EventTalkPayload = { id: string; npc: boolean };
export type EventResolvedPayload = { id: string; option: string };
export type StallFocusPayload = { stallId: string | null };
export type NodeTrialBrokenPayload = { nodeId: string; reason: 'hit' | 'time' };
export type PrefetchPayload = { phase: 'start' | 'done'; nodes: string[]; files: number };
export type WaveSidePayload = 'north' | 'south' | 'east' | 'west' | 'flank' | 'around';
export type FeelSlowmoPayload = { kind: 'lastKill' };
export type UiSettingToggledPayload = { key: string; on: boolean };
