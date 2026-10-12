/**
 * 62 루프 2 (계약 sound §13, P16) 효과음 연결 — audioMap 에 펼친다. 매니페스트에 아직 없는 id(문 걸음 등)는 무음으로 통과한다.
 * 대체 관계(둘 다 울리지 않음 — 후보 목록의 로드된 첫 것 하나): `ui_*`↔`menu_*` · `death_slow`↔`player_death` ·
 * `trial_win`↔`grade_perfect` · `door_open`↔`exit_open`(같은 순간 문이 열리면 EXIT_OPENED 쪽은 쉰다).
 * - 메뉴 이동·선택·뒤로: UI 렌더러가 있으면 UI `uiSound.ts` 가 직접 낸다 → 시스템은 **임시 텍스트 메뉴일 때만**(같은 순간 두 번 금지).
 *   사연 고르기(event_choice)는 UI 소리가 아니라 그대로 낸다.
 * - UI 이벤트 트리거(`bus: 'ui'`): `ui:floor-end` → floor_end_sting · `ui:relic-gained` → relic_take (sound §6 `ui:boss-break` 와 같은 예외).
 * - 장터 사기: 코드 이벤트는 `SHOP_BOUGHT`(shop:bought) — 매니페스트 문구는 `SHOP_PURCHASE`(옛 이름, audioMap 이 처리).
 * - 방+복도 층(외벽 문 없음)만 옛 '시련 클리어 → door_open'(audioMap TRIAL_CLEARED — 매니페스트 옛 ROOM_CLEARED)이 남는다.
 */
import {
  Events,
  type DoorOpenedPayload,
  type DoorWalkPayload,
  type EnemyIncomingPayload,
  type FeelSlowmoPayload,
  type MenuEventPayload,
  type NodeGradedPayload,
  type UiSettingToggledPayload,
} from '../../core/EventBus';
import { FEEL } from '../../core/Constants';
import { gameState } from '../../core/GameState';
import { UI_EVENTS, __system, type UiRelic } from '../../contract/ui';
import { t, type AudioTrigger } from './audioTrigger';
import { BUILD_SFX } from './audioBuild';

const s = (id: string) => `sfx/${id}`;

export const LOOP2_SFX = {
  uiMove: s('ui_move'),
  uiSelect: s('ui_select'),
  uiBack: s('ui_back'),
  uiToggle: s('ui_toggle'),
  enemyIncoming: s('enemy_incoming'),
  lastKillSlow: s('last_kill_slow'),
  deathSlow: s('death_slow'),
  trialWin: s('trial_win'),
  trialFail: s('trial_fail'),
  floorEndSting: s('floor_end_sting'),
  relicTake: s('relic_take'),
  memoryUnlock: s('memory_unlock'),
  npcTalk: s('npc_talk'),
  doorOpen: s('door_open'),
  doorWalkOut: s('door_walk_out'),
  doorWalkIn: s('door_walk_in'),
  /** 지도 고르기 취소로 문턱 안쪽으로 걸어 나옴 (없으면 door_walk_in) */
  doorWalkBack: s('door_walk_back'),
} as const;

/** 옛 소리 (대체 관계의 폴백 — 새 소리가 없을 때만) */
const OLD = {
  menuMove: s('menu_move'),
  menuSelect: s('menu_select'),
  menuCancel: s('menu_cancel'),
  playerDeath: s('player_death'),
  exitOpen: s('exit_open'),
} as const;

/** enemy_incoming 정점(파일 1.00초 = 적이 일어서는 순간) — 시작 = max(0, delayMs − 정점) (manifest mixing.cues) */
export const ENEMY_INCOMING_PEAK_MS = 1000;
/** ui_toggle 끔 = 재생 속도 0.9 (sound §13) */
export const TOGGLE_OFF_RATE = 0.9;
/** 문 열림과 EXIT_OPENED 를 같은 순간으로 보는 창 (ms — 같은 프레임에 연달아 온다) */
const SAME_MOMENT_MS = 50;

const clock = (): number => (typeof performance !== 'undefined' ? performance.now() : Date.now());

/**
 * 같은 순간 판단용 시각 (트리거 `when` 이 적는다 — 이벤트 순서: DOOR_OPENED → EXIT_OPENED, FEEL_SLOWMO → NODE_GRADED).
 * 테스트·디버그용으로 내보낸다.
 */
export const loop2Moments = { doorOpenedAt: -Infinity, slowmoAt: -Infinity };

/** 시스템 임시 텍스트 메뉴일 때만 메뉴 소리 (UI 렌더러가 있으면 uiSound.ts 몫) */
const systemMenu = (): boolean => !__system.rendererRegistered();

/** trial_win: 마지막 처치 슬로모와 겹치면 슬로모가 풀린 뒤 (manifest mixing.cues trial_win) */
export function trialWinDelayMs(now = clock(), slowmoAt = loop2Moments.slowmoAt): number {
  const left = FEEL.KILL.SLOW.MS - (now - slowmoAt);
  return left > 0 ? Math.round(left) : 0;
}

/** 문 걸음 재생 속도: 파일 길이 기준(out 700·in/back 650ms) ÷ 실제 걸음 ms, 0.85~1.15 (음향 요청) */
export const DOOR_WALK_RATE = { outMs: 700, inMs: 650, min: 0.85, max: 1.15 } as const;

export function doorWalkRate(p: Pick<DoorWalkPayload, 'phase' | 'ms'> | undefined): number {
  if (!p || !(p.ms > 0)) return 1;
  const base = p.phase === 'out' ? DOOR_WALK_RATE.outMs : DOOR_WALK_RATE.inMs;
  return Math.min(DOOR_WALK_RATE.max, Math.max(DOOR_WALK_RATE.min, base / p.ms));
}

/** 문 걸음 → 효과음 후보 (back = 지도 취소로 물러남 — 없으면 door_walk_in). 매니페스트에 없으면 무음 */
export function doorWalkSfx(phase: DoorWalkPayload['phase'] | undefined): readonly string[] | null {
  if (phase === 'out') return [LOOP2_SFX.doorWalkOut];
  if (phase === 'in') return [LOOP2_SFX.doorWalkIn];
  if (phase === 'back') return [LOOP2_SFX.doorWalkBack, LOOP2_SFX.doorWalkIn];
  return null;
}

export const LOOP2_AUDIO_TRIGGERS: readonly AudioTrigger[] = [
  // --- 메뉴 (임시 텍스트 메뉴만 — UI 렌더러 메뉴는 uiSound.ts) ---
  t<MenuEventPayload>({
    event: Events.MENU_OPENED,
    note: '62 루프 2: 메뉴 열림 → ui_move(없으면 menu_move) — 임시 텍스트 메뉴만, 같은 메뉴 다시 그리기 제외',
    when: (p) => !p.reopen && systemMenu(),
    sfx: () => [LOOP2_SFX.uiMove, OLD.menuMove],
  }),
  t<MenuEventPayload>({
    event: Events.MENU_SELECTED,
    note: '62 루프 2: 메뉴 선택 → ui_select(없으면 menu_select) — 임시 텍스트 메뉴만. 사연 고르기 event_choice 는 늘',
    sfx: (p) => {
      const ui = systemMenu() ? [LOOP2_SFX.uiSelect, OLD.menuSelect] : [];
      return p?.id === 'event' ? [BUILD_SFX.eventChoice, ...ui] : ui.length ? ui : null;
    },
  }),
  t<MenuEventPayload>({
    event: Events.MENU_CLOSED,
    note: '62 루프 2: 선택 없이 닫힘(상점 이탈 등) → ui_back(없으면 menu_cancel) — 임시 텍스트 메뉴만',
    when: (p) => !p.selected && systemMenu(),
    sfx: () => [LOOP2_SFX.uiBack, OLD.menuCancel],
  }),
  t<UiSettingToggledPayload>({
    event: Events.UI_SETTING_TOGGLED,
    note: '62 루프 2: 설정 켜기/끄기 → ui_toggle (끔 = 재생 속도 0.9)',
    sfx: () => [LOOP2_SFX.uiToggle],
    rate: (p) => (p?.on === false ? TOGGLE_OFF_RATE : 1),
  }),

  // --- 전투 ---
  t<EnemyIncomingPayload>({
    event: Events.ENEMY_INCOMING,
    note: '62 루프 2: 적 등장 예고 → enemy_incoming (정점 1000ms 를 등장 순간에 — 시작 = max(0, delayMs − 1000))',
    sfx: () => [LOOP2_SFX.enemyIncoming],
    delayMs: (p) => Math.max(0, (p?.delayMs ?? 0) - ENEMY_INCOMING_PEAK_MS),
  }),
  t<FeelSlowmoPayload>({
    event: Events.FEEL_SLOWMO,
    note: '62 루프 2: 마지막 처치 슬로모를 실제로 걸었을 때 → last_kill_slow',
    when: (p) => {
      if (p?.kind !== 'lastKill') return false;
      loop2Moments.slowmoAt = clock();
      return true;
    },
    sfx: () => [LOOP2_SFX.lastKillSlow],
  }),
  t({
    event: Events.PLAYER_DIED,
    note: '62 루프 2: 사망 연출 시작(슬로모·먹 번짐과 같은 프레임) → death_slow (없으면 옛 player_death — 둘 다 울리지 않음)',
    sfx: () => [LOOP2_SFX.deathSlow, OLD.playerDeath],
  }),

  // --- 노드 시련 · 층 끝 · 유품 · 기억 ---
  t<NodeGradedPayload>({
    event: Events.NODE_GRADED,
    note: '노드 성과 등급: 완 → trial_win(없으면 grade_perfect, 막타 슬로모와 겹치면 풀린 뒤) · 양 → grade_good',
    sfx: (p) =>
      p?.grade === 'perfect'
        ? [LOOP2_SFX.trialWin, BUILD_SFX.gradePerfect]
        : p?.grade === 'good'
          ? BUILD_SFX.gradeGood
          : null,
    delayMs: (p) => (p?.grade === 'perfect' ? trialWinDelayMs() : 0),
  }),
  t({
    event: Events.NODE_TRIAL_BROKEN,
    note: '62 루프 2: 노드 시련(완 조건)이 깨짐 → trial_fail',
    sfx: () => [LOOP2_SFX.trialFail],
  }),
  t({
    event: UI_EVENTS.FLOOR_END,
    bus: 'ui',
    note: '62 루프 2: 1층 끝 결산 일기장 열림(UI 이벤트) → floor_end_sting',
    sfx: () => [LOOP2_SFX.floorEndSting],
  }),
  t<UiRelic>({
    event: UI_EVENTS.RELIC_GAINED,
    bus: 'ui',
    note: '62 루프 2: 유품을 지님(UI 이벤트) → relic_take — 장터에서 산 것은 shop_buy 가 대신',
    when: (p) => p?.source !== 'shop',
    sfx: () => [LOOP2_SFX.relicTake],
  }),
  t({
    event: Events.MEMORY_UNLOCKED,
    note: '62 루프 2: 기억을 떠올림 → memory_unlock',
    sfx: () => [LOOP2_SFX.memoryUnlock],
  }),
  t({ event: Events.EVENT_TALK, note: '62 루프 2: 사연 NPC 에게 말 걺 → npc_talk', sfx: () => [LOOP2_SFX.npcTalk] }),
  t({ event: Events.SHOP_TALK, note: '62 루프 2: 종군 상인에게 말 걺 → npc_talk', sfx: () => [LOOP2_SFX.npcTalk] }),

  // --- 외벽 문 (시스템 E) ---
  t<DoorOpenedPayload>({
    event: Events.DOOR_OPENED,
    note: '62 루프 2: 외벽 문 열림 → door_open (없으면 exit_open). 수련장 방 문은 처음부터 열려 있어 소리 없음',
    when: (p) => {
      loop2Moments.doorOpenedAt = clock();
      return p?.kind !== 'training';
    },
    sfx: () => [LOOP2_SFX.doorOpen, OLD.exitOpen],
  }),
  t({
    event: Events.EXIT_OPENED,
    note: '오르는 길(출구) 열림 → exit_open — 같은 순간 외벽 문이 열렸으면 door_open 이 대신 (방+복도 층 발판만)',
    when: () => clock() - loop2Moments.doorOpenedAt > SAME_MOMENT_MS,
    sfx: () => [OLD.exitOpen],
  }),
  t<DoorWalkPayload>({
    event: Events.DOOR_WALK,
    note: '62 루프 2: 문 자동 걸음 out → door_walk_out · in → door_walk_in · back(지도 취소) → door_walk_back(없으면 in) — 속도 = 걸음 길이에 맞춤',
    sfx: (p) => doorWalkSfx(p?.phase),
    rate: (p) => doorWalkRate(p),
  }),
];

/** 이 표가 고를 수 있는 새 효과음 id 전부 (매니페스트 대조 테스트용 — 아직 없는 문 걸음 포함) */
export function loop2SfxIds(): string[] {
  return Object.values(LOOP2_SFX);
}

/** 표가 대체 관계로만 쓰는 옛 id (테스트 — 매니페스트 used 목록) */
export const LOOP2_FALLBACK_SFX: readonly string[] = Object.values(OLD);

/** 노드 지도 층인가 — 노드 출구는 외벽 문(DOOR_OPENED)이 열림 소리를 낸다 (audioMap 의 옛 '시련 클리어: 문 열림' 은 방+복도 층만) */
export const routeFloorActive = (): boolean => gameState.route !== null;
