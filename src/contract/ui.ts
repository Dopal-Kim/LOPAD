/**
 * UI ↔ 게임 시스템 계약 (parts/producer/contracts/ui-system-interface.md, 16라운드 승인).
 * UI 파트 코드는 이 파일과 phaser 만 import 한다. 시스템 파트는 `__system` 으로 구현을 등록한다.
 */
import Phaser from 'phaser';

export const UI_EVENTS = {
  STATE: 'ui:state',
  STAGE_STARTED: 'ui:stage-started',
  ROOM_ENTERED: 'ui:room-entered',
  PLAYER_DAMAGED: 'ui:player-damaged',
  PLAYER_HEALED: 'ui:player-healed',
  GOLD_CHANGED: 'ui:gold-changed',
  WEAPON_EVOLVED: 'ui:weapon-evolved',
  BOSS_STARTED: 'ui:boss-started',
  BOSS_PHASE: 'ui:boss-phase',
  BOSS_DIED: 'ui:boss-died',
  MENU_OPEN: 'ui:menu-open',
  MENU_CLOSE: 'ui:menu-close',
  RUN_ENDED: 'ui:run-ended',
  FATE_DECIDED: 'ui:fate-decided',
  PAUSED: 'ui:paused',
  RESUMED: 'ui:resumed',
} as const;

export type RoomType = 'start' | 'trial' | 'rest' | 'boss';

export interface UiCell {
  cx: number;
  cy: number;
}

export interface UiRoom {
  id: string;
  type: RoomType;
  cells: UiCell[];
  visited: boolean;
  cleared: boolean;
}

export interface UiMap {
  rooms: UiRoom[];
  connections: { a: UiCell; b: UiCell }[];
  currentRoomId: string;
  gridW: number;
  gridH: number;
}

export interface UiMenuLine {
  key: string;
  label: string;
  enabled: boolean;
  detail?: string;
}

export type UiMenuId = 'reward' | 'passive' | 'shop' | 'meta';

export interface UiMenu {
  id: UiMenuId;
  title: string;
  footer?: string;
  lines: UiMenuLine[];
}

export interface UiSnapshot {
  hp: number;
  maxHp: number;
  gold: number;
  potions: number;
  potionMax: number;
  stageIndex: number;
  stageName: string;
  trialsCleared: number;
  trialsTotal: number;
  bossUnlocked: boolean;
  exitOpen: boolean;
  weapon: { name: string; evolutionName: string | null; personality: number; threshold: number; secondaryName: string };
  boss: { name: string; hp: number; maxHp: number; phase: number } | null;
  stats: { attack: number; defense: number; crit: number; sense: number };
  passives: { name: string; level: number; description: string }[];
  savesLeft: number;
  seed: string;
  map: UiMap;
  paused: boolean;
  menu: UiMenu | null;
}

export interface UiResult {
  cleared: boolean;
  stageName: string;
  floorReached: number;
  kills: number;
  gold: number;
  sense: number;
  weaponName: string;
  soulsGained: number;
  soulsTotal: number;
  seed: string;
}

export interface UiBossInfo {
  name: string;
  hp: number;
  maxHp: number;
  phase: number;
}

/** UI 가 구독하는 버스 (시스템 내부 버스와 분리) */
export const uiBus = new Phaser.Events.EventEmitter();

/** 시스템이 등록하는 구현 (UI 파트는 사용 금지) */
interface SystemImpl {
  getSnapshot: () => UiSnapshot | null;
  select: (menuId: UiMenuId, key: string) => void;
  pause: () => void;
  resume: () => void;
  startNewRun: () => void;
  continueRun: () => void;
  hasSave: () => boolean;
  toTitle: () => void;
}

let impl: SystemImpl | null = null;
let rendererRegistered = false;

const EMPTY_SNAPSHOT: UiSnapshot = {
  hp: 0,
  maxHp: 1,
  gold: 0,
  potions: 0,
  potionMax: 0,
  stageIndex: 0,
  stageName: '',
  trialsCleared: 0,
  trialsTotal: 0,
  bossUnlocked: false,
  exitOpen: false,
  weapon: { name: '', evolutionName: null, personality: 0, threshold: 1, secondaryName: '' },
  boss: null,
  stats: { attack: 0, defense: 0, crit: 0, sense: 0 },
  passives: [],
  savesLeft: 0,
  seed: '',
  map: { rooms: [], connections: [], currentRoomId: '', gridW: 0, gridH: 0 },
  paused: false,
  menu: null,
};

export const uiCommands = {
  registerRenderer(): void {
    rendererRegistered = true;
  },
  select(menuId: UiMenuId, key: string): void {
    impl?.select(menuId, key);
  },
  pause(): void {
    impl?.pause();
  },
  resume(): void {
    impl?.resume();
  },
  startNewRun(): void {
    impl?.startNewRun();
  },
  continueRun(): void {
    impl?.continueRun();
  },
  hasSave(): boolean {
    return impl?.hasSave() ?? false;
  },
  toTitle(): void {
    impl?.toTitle();
  },
  getUiSnapshot(): UiSnapshot {
    return impl?.getSnapshot() ?? EMPTY_SNAPSHOT;
  },
};

/** @internal 시스템 파트 전용 */
export const __system = {
  setImpl(i: SystemImpl): void {
    impl = i;
  },
  patchImpl(p: Partial<SystemImpl>): void {
    if (!impl) throw new Error('[contract] impl 미등록');
    impl = { ...impl, ...p };
  },
  rendererRegistered(): boolean {
    return rendererRegistered;
  },
  emit(event: string, payload?: unknown): void {
    uiBus.emit(event, payload);
  },
};
