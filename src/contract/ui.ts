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
  /** 45라운드: 워프 도착 (`UiWarpDone`) */
  WARP_DONE: 'ui:warp-done',
  /** 45라운드: `warpTo` 거부 (`UiWarpDenied`) */
  WARP_DENIED: 'ui:warp-denied',
  /** 47라운드: E형 구조물 사용 완료 (`UiStructureUsed`) */
  STRUCTURE_USED: 'ui:structure-used',
  /** 47라운드: 타격형 구조물 부서짐 (`UiStructureBroken`) */
  STRUCTURE_BROKEN: 'ui:structure-broken',
  /** 47라운드: 구조물 결과 알림 — 획득·손실·경고 문구 (`UiStructureResult`) */
  STRUCTURE_RESULT: 'ui:structure-result',
  /** 47라운드: 구조물 도전 전투 시작 — 투견 링·흉패 (`UiChallengeStarted`) */
  CHALLENGE_STARTED: 'ui:challenge-started',
  /** 47라운드: 구조물 도전 전투 종료 (`UiChallengeCleared`) */
  CHALLENGE_CLEARED: 'ui:challenge-cleared',
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
  /** 45라운드: 워프 목적지 가능 (= `UiSnapshot.warp.targets` 에 있음) */
  warpable: boolean;
  /** 47라운드: 사용 가능한 E형 구조물이 남은 방 (미니맵 점 1개, 계약 §9.5) */
  structureDot: boolean;
}

/** 45라운드: 워프 거부 사유 — 전투 중 / 메뉴·연출 중(게임 씬 없음 포함) / 없는 방 / 미방문·미클리어 / 이미 그 방 */
export type UiWarpDenyReason = 'combat' | 'busy' | 'unknown-room' | 'not-cleared' | 'current-room';

/** 45라운드: 워프 상태 (계약 §8.1) */
export interface UiWarpState {
  /** 지금 `warpTo` 를 받을 수 있는지 (blocked === null) */
  ready: boolean;
  /** ready=false 의 이유 */
  blocked: 'combat' | 'busy' | null;
  /** 워프 가능한 방 id (map.rooms[].id). ready 와 무관하게 방 조건(방문·클리어·현재 방 아님)만으로 채운다 */
  targets: string[];
  /** 워프 연출 중 (입력 잠금) */
  warping: boolean;
}

export interface UiWarpDone {
  fromRoomId: string;
  roomId: string;
  type: RoomType;
}

export interface UiWarpDenied {
  roomId: string;
  reason: UiWarpDenyReason;
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

/**
 * 47라운드: 구조물 메뉴 id (계약 §9.4).
 * cards = 2-1 패 탁자 3장 중 1장 · exchange = 2-2 목숨 칩 환전대 · pawn = 2-6 전당포 창구 ·
 * grave = C3 무명 전사의 묘(영혼↔개성) · ledger = 1-3 외상 장부대(빌리기·갚기) · counter = 1-5 선술집 카운터(잔 고르기)
 */
export type UiStructureMenuId = 'cards' | 'exchange' | 'pawn' | 'grave' | 'ledger' | 'counter';

/** 'evolve' 는 27라운드 개성 3지선다, 'ending' 은 23라운드 엔딩 2지선다 (계약 추가분, 승인 대기) */
export type UiMenuId = 'reward' | 'passive' | 'shop' | 'meta' | 'evolve' | 'ending' | UiStructureMenuId;

export interface UiMenu {
  id: UiMenuId;
  title: string;
  footer?: string;
  lines: UiMenuLine[];
  /** 47라운드: 그만두기 줄의 key (구조물 메뉴는 항상 '0'). 있으면 UI 는 ESC·닫기 버튼을 `select(id, cancelKey)` 로 보낸다 */
  cancelKey?: string;
  /** 47라운드: 이 메뉴를 연 구조물 인스턴스 id (= `UiInteractable.id`). 구조물 메뉴만 */
  structureId?: string;
}

/**
 * 47라운드: 구조물 종류 (계약 §9.1). 초안 `structures-draft.md` id 대응:
 * crate C1 · chest C2 · grave C3 · campfire C5 · cask 1-1 · still 1-2 · ledger 1-3 · agingBarrel 1-4 ·
 * counter 1-5 · hiddenWall 1-6 · cardTable 2-1 · exchange 2-2 · dogRing 2-3 · stakeBell 2-4 · roulette 2-5 · pawn 2-6
 */
export type UiStructureKind =
  | 'crate'
  | 'chest'
  | 'grave'
  | 'campfire'
  | 'cask'
  | 'still'
  | 'ledger'
  | 'agingBarrel'
  | 'counter'
  | 'hiddenWall'
  | 'cardTable'
  | 'exchange'
  | 'dogRing'
  | 'stakeBell'
  | 'roulette'
  | 'pawn';

/** 47라운드: 상호작용 비용 표시 (계약 §9.1) */
export interface UiCost {
  /** 무엇을 내는가. none 이면 비용 없음 */
  kind: 'gold' | 'hp' | 'maxHp' | 'potion' | 'passive' | 'none';
  /** 수치 (gold=G, hp·maxHp=HP, potion=개, passive=개). 표시가 필요 없으면 0 */
  amount: number;
  /** 그대로 그릴 문자열 (자리표시, 예 '35전표', 'HP 25%'). none 이면 '' */
  label: string;
  /** 지금 낼 수 있는가 */
  affordable: boolean;
}

/**
 * 47라운드: 상호작용 불가 사유 (계약 §9.1).
 * combat 전투 중 · busy 메뉴·연출·워프 중 · gold 골드 부족 · hp HP 부족 · potion 물약 없음 ·
 * notReady 아직 때가 아님(숙성 중 등) · full 더 받을 수 없음(소지 상한·패시브 만렙 등) · limit 사용 횟수 소진
 */
export type UiInteractBlockReason = 'combat' | 'busy' | 'gold' | 'hp' | 'potion' | 'notReady' | 'full' | 'limit';

/** 47라운드: 가장 가까운 E형 구조물 안내 (계약 §9.1) */
export interface UiInteractable {
  /** 구조물 인스턴스 id (층 안에서 유일) */
  id: string;
  kind: UiStructureKind;
  /** 표시 이름 (자리표시 — 스토리 확정 전) */
  name: string;
  /** 구조물이 있는 방 id (map.rooms[].id) */
  roomId: string;
  /** 누를 키 이름 (시스템이 읽는 키, 현재 'E') */
  key: string;
  /** 행동 문구 키 (예 'chest.open'). 스토리 텍스트 확정 후 UI 가 문구를 바꿔 끼울 때 쓴다 */
  actionKey: string;
  /** 행동 문구 값 (자리표시, 예 '연다') */
  action: string;
  /** 비용. 없으면 null */
  cost: UiCost | null;
  /** 길게 누르기 (C3 묘 2000ms). 누르기 아니면 null. progress 0..1, 이동하면 0 으로 돌아간다 */
  hold: { durationMs: number; progress: number } | null;
  /** 지금 E 가 먹히는가 (reason === null) */
  usable: boolean;
  reason: UiInteractBlockReason | null;
  /** 불가 사유 문구 (자리표시). usable 이면 '' */
  reasonText: string;
  /** 구조물 윗변 중앙의 화면 좌표 (게임 캔버스 픽셀, 카메라 반영). 안내를 구조물 위에 띄우고 싶을 때 */
  screen: { x: number; y: number };
}

/**
 * 47라운드: HUD 상태 id (계약 §9.2).
 * debt 1-3 빚 · drunk 1-5 취기 · stakes 2-4 층 배율 · embers C5 불씨 · fireWeapon 1-2 불붙은 무기 ·
 * ring 2-3 투견 링 · roulette 2-5 판 규칙 · aging 1-4 숙성 · pawn 2-6 맡긴 물건
 */
export type UiStatusId = 'debt' | 'drunk' | 'stakes' | 'embers' | 'fireWeapon' | 'ring' | 'roulette' | 'aging' | 'pawn';

/** 47라운드: HUD 상태 한 칸 (계약 §9.2). UI 는 label·value 를 그대로 그린다 */
export interface UiStatus {
  id: UiStatusId;
  /** 표시 분류 — buff 이로움 · debuff 해로움 · resource 쌓인 자원 · timer 제한 시간 · rule 규칙 · progress 진행 */
  kind: 'buff' | 'debuff' | 'resource' | 'timer' | 'rule' | 'progress';
  /** 이름 (자리표시, 예 '빚') */
  label: string;
  /** 그대로 그릴 값 (예 '90G', '2단', '×1.6', '1/2') */
  value: string;
  /** 게이지용 수치·최대치 (선택) */
  amount?: number;
  max?: number;
  /** 남은 시간 ms (타이머가 있는 상태만) */
  remainMs?: number;
  /** 전체 시간 ms (remainMs 와 함께) */
  durationMs?: number;
  /** 효과 설명 한 줄 (자리표시, 툴팁·아래 줄용) */
  detail?: string;
}

/** 47라운드 이벤트 페이로드 (계약 §9.6) */
export interface UiStructureUsed {
  id: string;
  kind: UiStructureKind;
  roomId: string;
  /** 수행한 행동 문구 키 (`UiInteractable.actionKey` 또는 메뉴 선택 결과 키) */
  actionKey: string;
}

export interface UiStructureBroken {
  id: string;
  kind: UiStructureKind;
  roomId: string;
}

/** 결과 알림. text 는 그대로 그릴 한 줄(자리표시). deltas 는 바뀐 양(있는 것만) */
export interface UiStructureResult {
  id: string;
  kind: UiStructureKind;
  /** gain 획득 · loss 손실 · mixed 둘 다 · warn 경고(판돈 종 첫 타격 등) · info 안내 */
  tone: 'gain' | 'loss' | 'mixed' | 'warn' | 'info';
  text: string;
  deltas: {
    gold?: number;
    hp?: number;
    maxHp?: number;
    potions?: number;
    souls?: number;
    personality?: number;
    points?: number;
  };
}

export interface UiChallengeStarted {
  /** 구조물 인스턴스 id */
  id: string;
  /** dogRing 투견 링 · cardTable 흉패 소환 */
  kind: 'dogRing' | 'cardTable';
  roomId: string;
  /** 도전 이름 (자리표시) */
  label: string;
  /** 목표 문구 (자리표시, 예 '20초 안에 개 3마리') */
  goal: string;
  /** 제한 시간 ms. 없으면 null (흉패) */
  timeLimitMs: number | null;
}

export interface UiChallengeCleared {
  id: string;
  kind: 'dogRing' | 'cardTable';
  roomId: string;
  /** clear 달성 · flawless 무피격 달성 · timeout 시간 초과(판돈 몰수, 사망 아님) */
  outcome: 'clear' | 'flawless' | 'timeout';
  /** 결과 문구 (자리표시) */
  text: string;
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
  /** 45라운드: 활성 전투 방(시련·보스 진행 중)이 있으면 true */
  inCombat: boolean;
  /** 45라운드: 달리는 중 (비전투 + Shift + 이동) */
  sprinting: boolean;
  /** 45라운드: 워프 상태 */
  warp: UiWarpState;
  /** 47라운드: 가장 가까운 E형 구조물 안내. 없으면 null (계약 §9.1) */
  interactable: UiInteractable | null;
  /** 47라운드: HUD 상태 목록 (시스템이 그릴 순서로 정렬). 없으면 [] (계약 §9.2) */
  statuses: UiStatus[];
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
  /** 사망·클리어 문장 (클리어 시 고른 엔딩 문장) */
  line: string;
  /** 클리어 시 고른 엔딩 (23라운드). 사망이면 없음 */
  ending?: 'destroy' | 'understand';
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
  warpTo: (roomId: string) => boolean;
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
  inCombat: false,
  sprinting: false,
  warp: { ready: false, blocked: 'busy', targets: [], warping: false },
  interactable: null,
  statuses: [],
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
  /**
   * 45라운드: 클리어한 방으로 워프 (계약 §8.2). 시작하면 true, 거부면 false + `WARP_DENIED`.
   * 게임이 pause() 로 멈춰 있으면 허용될 때 시스템이 재개한 뒤 워프한다
   */
  warpTo(roomId: string): boolean {
    if (!impl) {
      uiBus.emit(UI_EVENTS.WARP_DENIED, { roomId, reason: 'busy' } satisfies UiWarpDenied);
      return false;
    }
    return impl.warpTo(roomId);
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
