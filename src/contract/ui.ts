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
  /** 스토리 자막 (계약 story-text.md §3) */
  STORY: 'ui:story',
} as const;

export type StoryKind = 'floor' | 'boss' | 'rest' | 'notice' | 'evolution' | 'death';
export interface UiStoryLine {
  kind: StoryKind;
  text: string;
}

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

/** 'evolve' 는 27라운드 개성 3지선다 (계약 추가분, 승인 대기) */
export type UiMenuId = 'reward' | 'passive' | 'shop' | 'meta' | 'evolve';

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
  /** 일기장에 적은 이름 */
  playerName: string;
  /** 층 제목 (예: "1층 · 술독 제국 '잔(盞)'") */
  floorTitle: string;
  /** 서사 이름 */
  names: { potion: string; gold: string; shop: string; souls: string };
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
  playerName: string;
  /** 사망·클리어 문장 */
  line: string;
}

export interface UiBossInfo {
  name: string;
  hp: number;
  maxHp: number;
  phase: number;
}

/** 세계관 문구 (스토리 파트 텍스트 팩 2차, 29라운드). 키가 없으면 UI 는 기본 문구를 쓴다 */
export interface UiText {
  title: Record<string, string>;
  evolveMenu: Record<string, string>;
  result: Record<string, string>;
  pause: Record<string, string>;
  hud: Record<string, string>;
  /** 조작법 한 줄 템플릿. {secondary} 치환 */
  controls: string;
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
  getText: () => UiText;
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
  playerName: '',
  floorTitle: '',
  names: { potion: '물약', gold: 'G', shop: '상점', souls: '영혼' },
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
  /** 세계관 문구. 시스템 미등록 시 빈 객체 */
  getUiText(): UiText {
    return impl?.getText() ?? { title: {}, evolveMenu: {}, result: {}, pause: {}, hud: {}, controls: '' };
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
