/**
 * UI ↔ 게임 시스템 계약 (parts/producer/contracts/ui-system-interface.md, 16라운드 승인).
 * UI 파트 코드는 이 파일과 phaser 만 import 한다. 시스템 파트는 `__system` 으로 구현을 등록한다.
 */
import Phaser from 'phaser';
// 62 루프 2 F: C·D·E 의 독립 형식·상수는 uiLoop2.ts (그대로 재수출 — UI import 경로 그대로)
export * from './uiLoop2';
import type {
  UiEventIcon,
  UiEventScene,
  UiShopOffer,
  UiLoop2DStructureKind,
  UiLoop2DMenuId,
  UiKeyBindings,
  UiTextScale,
  UiWorldSign,
  UiWaveSide,
  UiRelic,
  UiEndChoice,
  UiFloorEnd,
  UiRunSummary,
  UiMemoryEntry,
  UiMemoryBook,
  UiLoop2CMenuId,
  UiDoorSide,
  UiDoor,
  UiHeroScreen,
} from './uiLoop2';

/**
 * 53라운드 계약 추가: 화면 기준. 실제 캔버스 1920×1080 = 논리 960×540 × RESOLUTION. UI 씬은 논리 좌표로 그린다
 * (main 카메라 zoom·origin 은 시스템이 READY 때 맞춘다 — UI 는 바꾸지 않는다)
 */
export const UI_SCREEN = { WIDTH: 960, HEIGHT: 540, RESOLUTION: 2 } as const;

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
  /**
   * 48라운드: 다음 노드를 고를 차례 (`UiRoute`, 계약 §10.2). 62 H: 외벽 문 안에 들어선 순간 곧바로 (전환 없이 · 외길이어도) —
   * 고르면 `TRANSITION_BEGIN{mode:'fade'}`
   */
  ROUTE_CHOOSE_OPEN: 'ui:route-choose-open',
  /** 48라운드: 노드 진입 (`UiRouteEntered`) */
  ROUTE_NODE_ENTERED: 'ui:route-node-entered',
  /** 48라운드: 탄생 연출 시작·끝 (계약 §10.3) — 62 P1-10: 페이로드 `UiBirthInfo` */
  BIRTH_STARTED: 'ui:birth-started',
  BIRTH_DONE: 'ui:birth-done',
  /** 53라운드 Q49: 적 소환 예고 (`UiEnemyIncoming`) — 소환 delayMs 전에 모든 전투에서. UI 경고는 튜토리얼만 */
  ENEMY_INCOMING: 'ui:enemy-incoming',
  /** 61라운드 단계 2 (계약 §17): 이번 런에 처음 나온 적 종류 소개 (`UiEnemyIntro`) — 그 적이 처음 나온 웨이브에 한 번 */
  ENEMY_INTRO: 'ui:enemy-intro',
  /** 53라운드: 튜토리얼 단계 안내 (`UiTutorialStep`) — 안내 문구가 뜰 때 */
  TUTORIAL_STEP: 'ui:tutorial-step',
  /** 57라운드 §14.11: 세트 단계가 오르거나 내림 (`UiTagSetChanged`) */
  TAG_SET_CHANGED: 'ui:tag-set-changed',
  /** 57라운드 §14.11: 이중 개성 획득 (`UiDualTrait`) — 61 G(§18): 이중 개성 폐지, 더 오지 않는다 (`TRAIT_GAINED`) */
  DUAL_TRAIT_GAINED: 'ui:dual-trait-gained',
  /** 57라운드 §14.11: 저주 받음 (`UiCurse`) */
  CURSE_GAINED: 'ui:curse-gained',
  /** 57라운드 §14.11: 저주 기간 끝 (`UiCurseEnded`) */
  CURSE_ENDED: 'ui:curse-ended',
  /** 57라운드 §14.11: 완벽 성공 사건 (`UiPerfectSuccess`) — 완벽 회피 = 적 공격 판정 직전 0.15초 안 대쉬·그림자 걸음 */
  PERFECT_SUCCESS: 'ui:perfect-success',
  /** 60라운드 §14.11: 성과 등급 노드 종료 (`UiNodeGraded`) */
  NODE_GRADED: 'ui:node-graded',
  /** §14.11: 단서 조사로 숨은 길 열림 (`UiHiddenNodeFound`) */
  HIDDEN_NODE_FOUND: 'ui:hidden-node-found',
  /** §14.11: 소모품 사용 (`UiConsumableUsed`) */
  CONSUMABLE_USED: 'ui:consumable-used',
  /** 61라운드 단계 3 (계약 §17): 보스 파훼·결정타 (`UiBossBreak`) */
  BOSS_BREAK: 'ui:boss-break',
  /** 61라운드 단계 4 (계약 §17.1): 보스 등장 포효 순간 (`UiBossRoar`) — 이름 카드 자리. 등장 연출이 없으면(introMs 0) BOSS_STARTED 직후 */
  BOSS_ROAR: 'ui:boss-roar',
  /** 61라운드 단계 4 (계약 §18): 각성 게이지가 올랐다 (`UiGrowthGain`) — HUD 반짝 */
  GROWTH_GAIN: 'ui:growth-gain',
  /** §18: 1차·2차 각성 연출 시작 (`UiAwaken`) — 시스템이 게임을 0.8/1.0초 멈춘다. UI 는 이름·한 줄 배너 */
  AWAKEN: 'ui:awaken',
  /** §18: 개성 하나를 얻었다 (`UiGrowthTrait`) — 옛 이중 개성 notice 대체 */
  TRAIT_GAINED: 'ui:trait-gained',
  /** §18.1 (61 단계 5, P13): 같은 태그 개성 2장으로 공명이 켜졌다 (`UiResonance`) — `ui:trait-gained` 와 같은 알림 형식 */
  RESONANCE: 'ui:resonance',
  /**
   * 61 단계 6 (계약 §19, P14): 그림 속 입구 전환 시작 (`UiTransitionBegin`, 시스템 → UI). UI 가 화면을 다 덮으면 `TRANSITION_COVERED`
   * 를 uiBus 로 보낸다. 시스템은 3초 안에 COVERED 가 없으면 스스로 진행한다(안전장치)
   */
  TRANSITION_BEGIN: 'ui:transition-begin',
  /** §19: UI → 시스템 `{ id }` — 화면이 다 덮였다 (이때 시스템이 방·지도를 바꾼다) */
  TRANSITION_COVERED: 'ui:transition-covered',
  /** §19: 시스템 → UI `{ id }` — 새 장면 준비됨 (걷어내기 시작) */
  TRANSITION_READY: 'ui:transition-ready',
  /** §19: UI → 시스템 `{ id }` — 전환 끝 (입력 재개). 시스템은 READY 뒤 3초 안에 없으면 스스로 재개한다 */
  TRANSITION_END: 'ui:transition-end',
  /** §19: 수련장 과제 하나 완료 (`UiTrainingTask`) */
  TRAINING_TASK: 'ui:training-task',
  /** §19 (61 단계 6 시스템 추가): 수련장 방 도장 — 그 방 과제를 모두 마침 (`UiTrainingStamp`) */
  TRAINING_STAMP: 'ui:training-stamp',
  /**
   * 62 루프 1 (계약 §20, P15 — 시스템 추가): 첫 생 의식 상태가 바뀌었다 (`UiRitual`). 단계·과제·운명이 바뀔 때마다 (매 프레임 아님).
   * 같은 값은 `getUiSnapshot().ritual` 로도 읽는다
   */
  RITUAL: 'ui:ritual',
  /** §20: 획 하나 판정 (`UiRitualStrokeJudged`) — UI 연출용 (판정 수치는 보내지 않는다) */
  RITUAL_STROKE_JUDGED: 'ui:ritual-stroke',
  /** 62 루프 2 시스템 D 이벤트 (아래 '62 루프 2 시스템 D' 절) */
  ...loop2DEvents(),
  /** 62 루프 2 시스템 C 이벤트 (아래 '62 루프 2 시스템 C' 절) */
  ...loop2CEvents(),
  /** P19 S1 자유 전투 반응 이벤트 (아래 'P19 S1' 절) */
  ...p19S1Events(),
  /** P21 어두운 톤·잔혹 전투·상흔 이벤트 (아래 'P21' 절 — 계약 dark-brutal.md §2) */
  ...p21Events(),
} as const;

/**
 * §19 그림 속 입구 전환 종류 — enterNode 노드 입구로 · exitRoom 방 → 지도 · floor 층(큰 그림) · training 수련장 방 입구로 ·
 * (62 시스템 H) fade 짧은 먹 번짐 암전 — 노드 지도·수련장 지도에서 고른 뒤 / 수련장 방 → 지도 마당. 62 H 부터 시스템은 노드 이동·
 * 수련장에서 enterNode·exitRoom·training 을 보내지 않는다 (floor 는 그대로)
 */
export type UiTransitionMode = 'enterNode' | 'exitRoom' | 'floor' | 'training' | 'fade';
/** §19 `TRANSITION_BEGIN` 페이로드 */
export interface UiTransitionBegin {
  /** 이번 전환 번호 (COVERED·READY·END 가 같은 id) */
  id: number;
  mode: UiTransitionMode;
  /** waste|outer|gate|hall|brewery|boss|training */
  region: string;
  /** battle|elite|shop|rest|event|boss|training… (route kind — birth·road·post 등도 그대로) */
  nodeKind?: string;
  /**
   * 입구 그림 텍스처 키 `paint/door_<…>` (시스템이 로드한 것만 — 같은 키로 cache.json 에 메타 doorRect·doorCenter·light).
   * art §28 찾는 순서: 정확 → 별칭 → `<region>_battle` → 없음(생략 — UI 가 키아트·단색). 수련장 방 = door_training_training,
   * 만취 그림자 방 = door_training_boss (nodeKind 'boss')
   */
  doorKey?: string;
  /** 줌 중심 화면 좌표 (논리 960×540) — 방 출구 · 수련장 지도의 방 자리. enterNode 는 UI 가 nodeId 로 자기 지도 자리를 쓴다 */
  from?: { x: number; y: number };
  /** (시스템 추가) enterNode·fade: 고른 노드 id (UiRouteNode.id) · training·fade(수련장): 고른 방 id */
  nodeId?: string;
  /** (62 시스템 H) fade: 덮기 시간 힌트 ms (약 400 — UI 는 이 안에 다 덮고 COVERED). 다른 mode 는 생략 */
  durationMs?: number;
  skippable: boolean;
}
/** §19 COVERED·READY·END 페이로드 */
export interface UiTransitionStep {
  id: number;
}

/** §19 수련장 과제 한 줄 (label 은 키캡 없는 짧은 명령형 — 키캡은 verb 로 UI 가 붙인다) */
export interface UiTrainingTaskLine {
  id: string;
  label: string;
  done: boolean;
  verb?: UiVerbSlot;
}
/** §19 수련장 방 (지도 두루마리 한 칸) */
export interface UiTrainingRoom {
  id: string;
  name: string;
  stamped: boolean;
}
/**
 * §19 `UiSnapshot.training` — 수련장 안에서만 (런·시험장은 null). room = 지금 방 id (지도 마당이면 'hall', tasks 는 [])
 */
export interface UiTraining {
  room: string;
  roomName: string;
  tasks: UiTrainingTaskLine[];
  stamped: boolean;
  rooms: UiTrainingRoom[];
  /** (시스템 추가) 지금 방의 짧은 안내 (들어갈 때 notice 와 같은 문장) */
  line?: string;
  /**
   * (시스템 추가) 수련장 지도 그림 텍스처 키 `paint/map_training` (로드됐을 때만 — cache.json 같은 키에 메타 rooms[]).
   * 메타 rooms 는 index 순서로 `rooms` 와 대응 (메타 id 는 아트 제안 — 1번 'breath' = step)
   */
  mapKey?: string;
}
/** §19 `TRAINING_TASK` 페이로드 */
export interface UiTrainingTask {
  room: string;
  id: string;
  label: string;
}
/** §19 `TRAINING_STAMP` 페이로드 */
export interface UiTrainingStamp {
  room: string;
  name: string;
  /** 여덟 방 모두 도장 */
  all: boolean;
}

/**
 * §20 첫 생 의식 단계 (62 루프 1, P15). null = 의식 밖(Setup 이 아님).
 * name 첫 생 이름 → strokes 3획 → trial 회피 시험(탄생 전장, 첫 생만) → fate 운명 공개 /
 * 두 번째 생부터 rewrite 이름 덧쓰기 한 화면 → fate (3획은 `ritual.redraw` 를 고를 때만, 회피 시험 없음)
 */
export type UiRitualPhase = 'name' | 'strokes' | 'trial' | 'fate' | 'rewrite' | null;
/** §20 획 입력 점: 논리 화면 좌표(960×540) · t = ms (아무 시계 — 점 사이 차이만 쓴다) */
export interface UiRitualPoint {
  x: number;
  y: number;
  t: number;
}
/** §20 (시스템 추가) 획 ↔ 무기 규칙 한 줄 — 무기 선택 규칙이 보이게 (수치 없음, 예 '곧고 빠르게 → 칼') */
export interface UiRitualLegend {
  weapon: string;
  weaponName: string;
  line: string;
}
/** §20 회피 시험 과제 한 줄 (label = 짧은 명령형, 키캡은 verb 로 UI 가 붙인다) */
export interface UiRitualTask {
  id: string;
  label: string;
  done: boolean;
  /** (시스템 추가) 이 과제에 쓰는 키 칸 (대쉬 과제 = 'dash') */
  verb?: UiVerbSlot;
  /** (시스템 추가) 끝난 과제를 한 대도 안 맞고 마쳤다 (done 일 때만) */
  clean?: boolean;
}
/** §20 의식 상태 — `UiSnapshot.ritual` · `RITUAL` 이벤트 */
export interface UiRitual {
  phase: UiRitualPhase;
  /** 지난 생 수 (0 = 첫 생) */
  lives: number;
  /** (시스템 추가) 일기장에 적힌 문장 — 첫 장 안내·번진 이름·덧쓰기 결과 (UI 가 종이 위에 쓴다, 위 → 아래) */
  lines?: string[];
  /** name·rewrite: value = 입력칸에 미리 채울 값(두 번째 생 = 지난 이름) · lastName = 번진 이름 */
  name?: { value: string; lastName?: string; maxLen: number };
  /** strokes: 진행 (판정은 시스템) · lastWeapon = 3획째가 정한 무기 id · legend = 획 ↔ 무기 규칙 (시스템 추가) */
  strokes?: { done: number; total: 3; lastWeapon?: string; legend?: UiRitualLegend[] };
  /**
   * trial: 과제 목록 · skippable = `ritual.skip()` 으로 건너뛸 수 있다.
   * (시스템 추가) current = 지금 과제 id · state = card(과제 이름 보여 줌) | run(사격 중) | clear(과제 끝) | done(전부 끝)
   */
  trial?: {
    tasks: UiRitualTask[];
    skippable: boolean;
    current?: string;
    state?: 'card' | 'run' | 'clear' | 'done';
  };
  /**
   * fate: line = 무기의 첫 한마디(원한의 목소리) · why = 왜 이 무기인지 한 줄(수치 금지) · lookKey = 무기 미리보기 텍스처(로드됐을 때만).
   * (시스템 추가) gift = 회피 시험 결과 한 줄(수치 없음, 없으면 생략) · remembered = 두 번째 생 '손이 기억한 무기'
   */
  fate?: {
    weapon: string;
    weaponName: string;
    line: string;
    lookKey?: string;
    why: string;
    gift?: string;
    remembered?: boolean;
  };
  /** (시스템 추가) rewrite: 획을 다시 그어 새 무기를 부를 수 있다 — `ritual.redraw(name)` (key = 안내 키캡) */
  redraw?: { key: string; label: string };
  /** (시스템 추가) rewrite: 영혼 강화 귀퉁이 — canBuy = 지금 살 수 있는 강화가 있다 · `ritual.openMeta()` (key = 안내 키캡) */
  meta?: { souls: number; canBuy: boolean; label: string; key: string };
  /** 아래 안내 한 줄 (키캡 포함 가능 — '[Enter] 적는다' 형식) */
  hint?: string;
}
/**
 * 62 P1-10 (시스템 추가): BIRTH_STARTED·BIRTH_DONE 페이로드. firstLife = 첫 생 — false 면 '싸우는 법' 조작 패널을 띄우지 않는다
 * (조작 전체 표는 일시정지 메뉴에만 · 첫 생 첫 노드들은 `UiSnapshot.keyBar` 작은 키 막대)
 */
export interface UiBirthInfo {
  firstLife: boolean;
}
/** §20 `RITUAL_STROKE_JUDGED` — index = 방금 판정한 획 (0부터) · weaponHint = 지금까지의 획이 기우는 무기 id */
export interface UiRitualStrokeJudged {
  index: number;
  weaponHint?: string;
}
/** §20 명령 종류 (uiCommands.ritual.* 이 시스템에 넘기는 형식 — UI 는 uiCommands.ritual 을 쓴다) */
export type UiRitualCommand =
  | { kind: 'submitName'; name: string }
  | { kind: 'redraw'; name: string }
  | { kind: 'stroke'; points: UiRitualPoint[] }
  | { kind: 'next' }
  | { kind: 'skip' }
  | { kind: 'back' }
  | { kind: 'openMeta' };

/**
 * 57라운드 계약 §14.1 (승인 #21): 10태그. 이름(name)은 자리표시. 2층부터 층 테마 태그가 이 유니온에 추가된다
 * insight 간파 · breach 돌파 · vital 급소 · scar 상흔 · chain 연쇄 · ranged 원격 · weight 중량 · mark 표식 · endure 버팀 · drunk 취기
 */
export type UiTagId =
  'insight' | 'breach' | 'vital' | 'scar' | 'chain' | 'ranged' | 'weight' | 'mark' | 'endure' | 'drunk';

/** §14.1 태그 하나의 상태 */
export interface UiTagState {
  id: UiTagId;
  /** '간파' 등 (자리표시) */
  name: string;
  /** 태그 점수 = 패시브 종류당 1 + Lv3 +1 + 갈래 노드 1(강화 시 최대 3) + 저주 이득 */
  score: number;
  /** 지금 켜진 세트 단계 (임계 2/4/6) */
  stage: 0 | 2 | 4 | 6;
  /** 다음 임계 (6 달성이면 null) */
  next: number | null;
  /** 세트 효과 3칸 */
  effects: {
    threshold: 2 | 4 | 6;
    name: string;
    /** 상세 수치 (Tab 보기) */
    description: string;
    /** 62 I (P1-N2): 카드 문장 — 숫자·×·% 없음 (세트 칩) */
    line?: string;
    active: boolean;
  }[];
}

/** §14.2 이중 개성 */
export interface UiDualTrait {
  id: string;
  name: string;
  description: string;
  /** 짝 갈래 이름 (예 '선풍') */
  branchName: string;
  /** 짝 태그 (취기 짝 4종은 'drunk') */
  tag: UiTagId;
  /** 1단 짝(태그 2점) / 2단 짝(태그 4점) */
  tier: 1 | 2;
}

/** §14.3 저주 (동시 1개, 정화 없음) */
export interface UiCurse {
  id: string;
  /** 1층 7종 (만취 서약·외상·깨진 잔·불붙은 혀·맨손 맹세·저주 궤짝·피멍), 자리표시 */
  name: string;
  /** 이득 한 줄 */
  benefit: string;
  /** 저주 한 줄 */
  penalty: string;
  /** 남은 노드 수 (층을 넘어도 유지). 처치 수 기준 저주면 null */
  nodesLeft: number | null;
  /** 처치 수 기준 저주(저주 궤짝 '다음 12처치')만, 그 외 null */
  killsLeft: number | null;
}

/** §14.1 `UiSnapshot.build` */
export interface UiBuildState {
  /** score > 0 인 태그만, 점수 높은 순 (시스템 정렬) */
  tags: UiTagState[];
  /** 얻은 이중 개성 — 61 G(§18): 이중 개성 폐지, 늘 [] (개성은 `UiSnapshot.growth.traits`) */
  dualTraits: UiDualTrait[];
  /** 지금 걸린 저주 (동시 1개) */
  curse: UiCurse | null;
}

/** §14.11 `TAG_SET_CHANGED` 페이로드 */
export interface UiTagSetChanged {
  tag: UiTagId;
  name: string;
  stage: 0 | 2 | 4 | 6;
  /** 새로 켜진(또는 꺼진 뒤 남은) 단계 효과 이름. 0 단계면 '' */
  effectName: string;
  /**
   * 62 I (P1-N2): 토스트 한 줄 '{태그} 세트 — {단계 문장}'(숫자·×·% 없음, 예 '중량 세트 — 강공이 더 무겁다'). 0 단계면 ''.
   * ('공명'은 개성 공명(§18.1)과 겹쳐 쓰지 않는다.) 문장만은 `UiTagState.effects[].line`.
   * 시스템은 세트 단계 STORY notice 를 더 보내지 않는다(렌더러가 있을 때) — 이 칩 하나가 알림.
   */
  line?: string;
}

/** §14.11 `CURSE_ENDED` 페이로드 */
export interface UiCurseEnded {
  id: string;
  name: string;
}

/** §14.11 `PERFECT_SUCCESS` 페이로드 */
export interface UiPerfectSuccess {
  kind: 'parry' | 'perfectGuard' | 'perfectRelease' | 'perfectEvade';
}

/**
 * §14.4 메뉴 줄 종류 — 보상 칸. passive 일반 패시브 · curse 저주 선택.
 * 61 G (§18 무기 성장 — `evolve` 메뉴): trait 개성 3장 · awaken1 1차 갈래 · awaken2 2차 길 · temper 단련.
 * 옛 branchA/branchB/reinforce/bloodPact/awaken/dual 은 UI 코드 호환으로만 남는다 — 시스템은 더 내보내지 않는다
 */
export type UiChoiceKind =
  | 'trait'
  | 'awaken1'
  | 'awaken2'
  | 'temper'
  | 'passive'
  | 'curse'
  /** @deprecated 61 G — 더 오지 않는다 */
  | 'branchA'
  /** @deprecated 61 G */
  | 'branchB'
  /** @deprecated 61 G */
  | 'reinforce'
  /** @deprecated 61 G */
  | 'bloodPact'
  /** @deprecated 61 G */
  | 'awaken'
  /** @deprecated 61 G */
  | 'dual';

/** §18 각성 게이지 눈금 종류: ◇ 개성 발현 · ◆ 1차 각성 · ◆ 2차 각성 · 단련(단련 또는 개성) */
export type UiGrowthMarkKind = 'trait' | 'awaken1' | 'awaken2' | 'temper';
/** §18 눈금 하나 (지난 것 done) */
export interface UiGrowthMark {
  at: number;
  kind: UiGrowthMarkKind;
  done: boolean;
}
/** §18 개성 카드 (verb = 바뀌는 키 칸, tag = 1층 태그) */
export interface UiGrowthTrait {
  id: string;
  name: string;
  /** 조건 → 행동 변화 한 문장 */
  line: string;
  verb: UiVerbSlot;
  tag?: UiTagId;
  /** §18.1 (P13): 개성 카드 그림 텍스처 키 (`ui_traits/<무기>_<개성 id>` — 시스템이 로드한 것만, 없으면 생략 → 키캡) */
  iconKey?: string;
  /** 62 루프 4 (스토리 64 팩 — 기억 '떠올릴 개성'): 상세 보기 줄 (수치 채움) · 흐린 한 줄. 있는 카드만 */
  detail?: string;
  flavor?: string;
}
/** §18.1 (P13) 공명: 같은 무기·같은 태그 개성 2장으로 켜지는 엮임 효과 */
export interface UiResonance {
  tag: UiTagId;
  name: string;
  /** 조건 → 행동 한 문장 */
  line: string;
  /** §18.1 (61 단계 5): 공명 카드 그림 텍스처 키 (`ui_traits/<공명 id>` — 시스템이 로드한 것만) */
  iconKey?: string;
}
/** §18.1 `UiGrowth.resonance` 한 줄 (이 무기의 공명 전부 — active = 켜짐) */
export interface UiResonanceState extends UiResonance {
  active: boolean;
}
/** §18 2차 길 */
export interface UiGrowthPath {
  id: string;
  name: string;
  line: string;
  /** 2차 모양 미리보기 텍스처 키 (시스템이 로드해 둔 것만 — 없으면 생략) */
  lookKey?: string;
  /** 61 G 시스템 추가: 길이 바꾸는 칸 */
  verb?: UiVerbSlot;
}
/** §18 1차 갈래 */
export interface UiGrowthBranch {
  id: string;
  name: string;
  /** 한 줄 양상 ('무리 한가운데로 파고드는 칼') */
  line: string;
  /** 1차 각성 때 바뀌는 칸 */
  verb: UiVerbSlot;
  /** 1차 모양 미리보기 텍스처 키 (로드돼 있을 때만) */
  lookKey?: string;
  paths: [UiGrowthPath, UiGrowthPath];
}
/** §18 `UiSnapshot.growth` */
export interface UiGrowth {
  /** 누적, 줄지 않음 */
  gauge: number;
  /** 이번 층 눈금 (지난 것 done) — 기본 눈금 + 다음 단련 눈금 하나 */
  marks: UiGrowthMark[];
  /** 다음 눈금 (null = 더 없음) */
  next: UiGrowthMark | null;
  /** 각성 단계 */
  stage: 0 | 1 | 2;
  weaponName: string;
  baseLookKey?: string;
  /** 이 무기의 갈래 3 (성장도 나무용, 항상 전체) */
  branches: UiGrowthBranch[];
  /** 고른 1차 갈래 id */
  branch: string | null;
  /** 고른 2차 길 id */
  path: string | null;
  /** 얻은 개성 */
  traits: UiGrowthTrait[];
  /** §18.1 (P13): 이 무기의 공명 2~3개 (켜짐 표시 — 성장도·Tab) */
  resonance?: UiResonanceState[];
  temper: { n: number; max: number };
  /** true = 메타 기준 처음 (안내 카드) — 메뉴가 닫히면 시스템이 메타 `diary.guides` 에 기록 */
  firstTime: { trait: boolean; awaken1: boolean; awaken2: boolean };
}
/** §18 `GROWTH_GAIN` 페이로드 */
export interface UiGrowthGain {
  amount: number;
  gauge: number;
}
/** §18 `AWAKEN` 페이로드 */
export interface UiAwaken {
  stage: 1 | 2;
  weapon: string;
  branch: string;
  path?: string;
  name: string;
  line: string;
  lookKey?: string;
}

/** §14.4 패시브 희귀도 (일반·희귀·영웅·전설) */
export type UiRarity = 'common' | 'rare' | 'epic' | 'legendary';

/** 53라운드 Q49: 적 소환 예고. delayMs = 소환까지 남은 ms (0 = 바로) · count = 마리 수 */
/** 61라운드 단계 2 (계약 §17): 새 적 소개 자막 — id = 적 id, name = 표시 이름, desc = 한 줄 요령 */
export interface UiEnemyIntro {
  id?: string;
  name: string;
  desc?: string;
}

export interface UiEnemyIncoming {
  roomId: string;
  delayMs: number;
  count?: number;
}

/** 53라운드: 튜토리얼 단계 (index 0부터 · total 단계 수 · text 안내 문구 · keys 키 표시 — 예 ['W','A','S','D'], ['좌클릭']) */
export interface UiTutorialStep {
  index: number;
  total: number;
  text: string;
  keys: string[];
}

/** 48라운드: 노드 지도 (계약 §10.1) */
export type UiNodeType = 'journey' | 'battle' | 'shop' | 'rest' | 'event' | 'boss';
export type UiNodeState = 'locked' | 'available' | 'current' | 'cleared' | 'passed';
export interface UiRouteNode {
  id: string;
  type: UiNodeType;
  /** 자리표시 이름 (스토리 확정 전) */
  name: string;
  /** 왼→오 진행 단계 (0부터) */
  col: number;
  /** 같은 단계 안 위치 (0부터), 그리기용 */
  row: number;
  /** 다음 단계로 이어지는 노드 id */
  links: string[];
  state: UiNodeState;
  /** 49라운드: 지역 이름 (예: '성문', '외곽 거리') — M 지도 위치 정보 (계약 §11.2) */
  region?: string;
  /** 49라운드: 장소 설명 한두 줄 (자리표시) */
  desc?: string;
  /** 60라운드 §14.5 (아래 7개 필수): 공개된 보상 (null = 아직 비공개·상점·휴식, 'unknown' = '?' 이벤트·숨김) */
  reward: UiNodeRewardKind | null;
  /** §14.5: 위험 노드 (엘리트 길 / 저주 길, 1층 1개) */
  risk: 'elite' | 'curse' | null;
  /** §14.5: 진입 확인에 붙일 위험 한 줄 (위험 노드 아니면 '') */
  riskText: string;
  /** §14.5: 엘리트 접두어 이름 (지도 정보로 공개된 경우만) */
  prefixes: string[] | null;
  /** §14.5: 이벤트 내용 이름 (지도 정보로 공개된 경우만) */
  eventName: string | null;
  /** §14.5: 숨은 노드 — 얼룩만 / 위치 표시(지도 정보) / 조사로 길 열림. 일반 노드는 null */
  hidden: 'smudge' | 'located' | 'found' | null;
  /** §14.5: 지나온 노드의 성과 도장 */
  grade: UiNodeGrade | null;
}
/** 60라운드 §14.5: 보상 미리보기 아이콘 7종 (설계안 a.1) */
export type UiNodeRewardKind = 'gold' | 'passive' | 'personality' | 'consumable' | 'statPoint' | 'curse' | 'unknown';
/** §14.5: 완(完) · 양(良) */
export type UiNodeGrade = 'perfect' | 'good';
export interface UiRoute {
  floor: number;
  nodes: UiRouteNode[];
  currentId: string | null;
  /** true = 다음 노드를 골라야 함 (시스템이 게임 입력 잠금) */
  choosing: boolean;
  /** 60라운드 §14.5: 산 지도 정보 3품목 */
  intel: { nextTier: boolean; fullFloor: boolean; hiddenLocated: boolean };
}
export interface UiRouteEntered {
  id: string;
  type: UiNodeType;
  name: string;
}

/**
 * 61라운드 P8 계약 추가 (프로듀서 계약 문서 갱신 대상): voice 원한(무기)의 목소리 · speech 군주의 말(speaker) ·
 * clue 단서 조사(lines 여러 줄을 차례로) · event 이벤트 결과 문장(이벤트 메뉴를 닫은 뒤)
 */
export type StoryKind =
  'floor' | 'boss' | 'rest' | 'notice' | 'evolution' | 'death' | 'voice' | 'speech' | 'clue' | 'event';
export interface UiStoryLine {
  kind: StoryKind;
  /** 한 줄 (clue 는 lines 를 '\n' 으로 이은 것) */
  text: string;
  /** 61 speech: 화자 이름 (예 '만취') — UI 가 '만취: …' 로 */
  speaker?: string;
  /** 61 voice: 말하는 무기 id (katana · greatsword · dagger · bow — 무기 빛 색·아이콘). 화자 이름은 붙이지 않는다 */
  weapon?: string;
  /** 61 clue: 조사 문장 줄들 (순서대로 이어서 띄운다) */
  lines?: string[];
  /** 61: 표시 시간 힌트 ms (voice crisis = 전투 중이라 짧게 1500). 없으면 UI 기본 */
  holdMs?: number;
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
  /** 57라운드 §14.4: 칸 종류 (개성 3지선다·보상 3지선다·저주 2택). 없으면 일반 줄 */
  kind?: UiChoiceKind;
  /** §14.4: 이 선택이 주는 태그 (패시브·갈래 노드) */
  tags?: UiTagId[];
  /** §14.4: 패시브 희귀도 */
  rarity?: UiRarity;
  /** §14.4: 잠긴 칸 — 각성 조건 안내. locked 면 enabled = false */
  locked?: { condition: string } | null;
  /** 61 G §18: `awaken1` 줄의 갈래 */
  branch?: UiGrowthBranch;
  /** §18: `awaken2` 줄의 길 */
  path?: UiGrowthPath;
  /** §18: `trait` 줄이 바꾸는 키 칸 */
  verb?: UiVerbSlot;
  /** §18.1 (61 단계 5 시스템 추가): `trait` 줄의 개성 (카드 그림 iconKey 포함) */
  trait?: UiGrowthTrait;
  /** §18.1 (시스템 추가): 이 개성을 고르면 켜지는 공명 (없으면 생략) */
  resonance?: UiResonance;
  /** 60라운드 §14.6: 상점 줄 묶음 — 고정 4칸 / 진열 3칸 / 리롤 / 궤짝 덤 / 지도 정보 */
  group?: 'fixed' | 'display' | 'reroll' | 'chest' | 'mapInfo';
  /** §14.6: 가격 (리롤은 15 → 25 → 35) */
  price?: UiCost;
  /** §14.6: 팔림 (enabled = false) */
  soldOut?: boolean;
  /** 61 단계 6 §19: 수련장 지도(`training` 메뉴) 줄의 방 id · 도장 */
  room?: string;
  stamped?: boolean;
  /** 62 P1-20 (시스템 추가): `trainingChoice` 카드 그림 — 입구 그림 텍스처 `paint/door_*` (로드됐을 때만) */
  doorKey?: string;
}

/**
 * 47라운드: 구조물 메뉴 id (계약 §9.4).
 * cards = 2-1 패 탁자 3장 중 1장 · exchange = 2-2 목숨 칩 환전대 · pawn = 2-6 전당포 창구 ·
 * grave = C3 무명 전사의 묘(영혼↔개성) · ledger = 1-3 외상 장부대 (62 루프 4: 시스템이 더 보내지 않음 — 구조물 제거) · counter = 1-5 선술집 카운터(잔 고르기)
 */
export type UiStructureMenuId = 'cards' | 'exchange' | 'pawn' | 'grave' | 'ledger' | 'counter';

/** 'evolve' 는 27라운드 개성 3지선다, 'ending' 은 23라운드 엔딩 2지선다 (계약 추가분, 승인 대기) */
/** 49라운드: 무기 시험장 메뉴 (계약 §11.4) */
export type UiLabMenuId = 'lab' | 'labBranch';
/**
 * 57라운드 §14.7: 저주 2택 (필수 — cancelKey 없음). 60라운드 2차 묶음: event 이벤트 노드('0' 지나간다) · mapInfo 지도 장수 ·
 * consumableSwap 소모품 바꾸기(필수)
 */
export type UiBuildMenuId = 'curse' | 'event' | 'mapInfo' | 'consumableSwap';
/**
 * 61 단계 6 (§19): training = 수련장 지도(방 고르기 — 줄 `room` = 방 id, cancelKey '0' = 수련장 나가기) ·
 * trainingChoice = 첫 생 '수련장부터 / 바로 벽 밖으로' (key '1' 수련장 · '2' 바로 런)
 */
export type UiTrainingMenuId = 'training' | 'trainingChoice';
export type UiMenuId =
  | 'reward'
  | 'passive'
  | 'shop'
  | 'meta'
  | 'evolve'
  | 'ending'
  | UiStructureMenuId
  | UiLabMenuId
  | UiBuildMenuId
  | UiTrainingMenuId
  | UiLoop2DMenuId
  | UiLoop2CMenuId;

/**
 * 53라운드 계약 추가 (51라운드 Q4 넣기/뽑기): 칼·대검처럼 넣고 뽑는 무기만 (단검·활은 스냅샷 carry = null).
 * firstStrike = 넣은 상태에서 준비된 첫 타 보너스 이름(예: '발도', '끌어내기'), 뽑았거나 없으면 null
 */
export interface UiCarry {
  drawn: boolean;
  firstStrike: string | null;
  key: 'F';
}

/** 49라운드: 무기 자원 게이지 (계약 §11.1) — 칼·대검 기력, 활 탄창, 단검 과열 */
export type UiResourceKind = 'stamina' | 'ammo' | 'heat';
export interface UiWeaponResource {
  kind: UiResourceKind;
  /** 표시 이름 (자리표시: 기력 / 화살 / 열기) */
  label: string;
  value: number;
  max: number;
  /** ok · low(부족) · exhausted(기력 바닥) · reloading(장전 중) · overheat(과열) */
  state: 'ok' | 'low' | 'exhausted' | 'reloading' | 'overheat';
  /** 장전·과열 냉각 진행도 0..1 (해당 없으면 생략) */
  progress?: number;
  /** 단검 과열 단계 등 보조 숫자 (예: 연격 가열 단계 0..3) */
  stage?: number;
}

/**
 * 56라운드 계약 §13 (승인 #20): 무기 고유 자원.
 * 칼 kenki(검기 3단) · 대검 grudge(울분) · 단검 brand(낙인 — 가장 많이 쌓인 적의 스택 0~5, 과열은 resource) · 활 breath(숨 0~3)
 */
export type UiWeaponGaugeKind = 'kenki' | 'grudge' | 'brand' | 'breath';
export interface UiWeaponGauge {
  kind: UiWeaponGaugeKind;
  label: string;
  value: number;
  max: number;
  /** 단계형 — 검기 0~3, 울분 0~3 (구간 1~33 / 34~66 / 67~100%) */
  stage?: number;
  /** 숨 감속 정밀 조준 중 */
  focusing?: boolean;
}

/**
 * 61라운드 P1 계약 추가 (프로듀서 계약 문서 갱신 대상): 무기 4동사 — 좌 = 연격 · 우 = 시그니처 · 스페이스 = 대쉬(+대쉬 공격) ·
 * 좌 홀드 = 고유 자원 기술. 칸 순서는 attack · signature · dash · hold 고정. 1단 갈래가 바꾼 칸은 그 동작 이름·hint 와 branch(갈래 이름).
 * key = 키캡 표시 문자열 (예 '좌클릭' · '우클릭' · 'Space' · '좌클릭 길게'). UI 는 이것으로 키캡 안내를 그린다
 */
export type UiVerbSlot = 'attack' | 'signature' | 'dash' | 'hold';
export interface UiWeaponVerb {
  slot: UiVerbSlot;
  key: string;
  /** 동작 이름 (예 '3연격', '가드 · 패링', '대쉬 · 일섬', '발도') */
  name: string;
  /** 한 줄 설명 */
  hint: string;
  /** 이 칸을 바꾼 1단 갈래 이름 (기본 동사면 null) */
  branch: string | null;
}
export interface UiWeaponVerbs {
  weapon: string;
  verbs: UiWeaponVerb[];
}

/** 56라운드 계약 §13: 그로기(기력 0 → 1.5초, 시간으로만 회복). 칼·대검만, 그 밖은 null */
export interface UiGroggy {
  active: boolean;
  leftMs: number;
}

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
 * crate C1 · chest C2 · grave C3 · campfire C5 · cask 1-1 · still 1-2 · ledger 1-3(62 루프 4 제거 — 배치·정의 없음) · agingBarrel 1-4 ·
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
  | 'pawn'
  /** 60라운드 §14.10: 도전 성소 C4 전장 깃발 (E, 첫 웨이브 전 비전투에만) */
  | 'warFlag'
  /** 60라운드 Q32 §14.10: 숨은 노드 단서 (E 로 살펴보기 → 지도에 길 공개) */
  | 'clue'
  /** 60라운드 Q32 §14.10: 이벤트 노드 소품 (E 로 이벤트 메뉴) */
  | 'eventProp'
  /** 60라운드 Q32 §14.10: 국경 초소 지도 장수 (E 로 mapInfo 메뉴) */
  | 'mapSeller'
  /** 62 루프 2 시스템 D: 이벤트 NPC · 상점 노점 칸 */
  | UiLoop2DStructureKind;

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
 * debt 1-3 빚(62 루프 4: 장부대 제거로 더 보내지 않음) · drunk 1-5 취기 · stakes 2-4 층 배율 · embers C5 불씨 · fireWeapon 1-2 불붙은 무기 ·
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
  /** dogRing 투견 링 · cardTable 흉패 소환 · 60라운드 warFlag 도전 성소 */
  kind: 'dogRing' | 'cardTable' | 'warFlag';
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
  kind: 'dogRing' | 'cardTable' | 'warFlag';
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
  /**
   * personality·threshold = 61 G: 각성 게이지(누적)·다음 눈금 값 (옛 '개성 n/max' 대체 — 정식 표시는 `growth`).
   * @deprecated personality·threshold — `growth.gauge`·`growth.next` 를 쓴다
   */
  weapon: { name: string; evolutionName: string | null; personality: number; threshold: number; secondaryName: string };
  /** 61라운드 단계 4 §18: 무기 성장 (무기 없을 때 null) */
  growth: UiGrowth | null;
  boss: UiBossSnapshot | null;
  stats: { attack: number; defense: number; crit: number; sense: number };
  /** 57라운드 §14.1: 태그(1~2개)·최대 레벨 추가 */
  passives: { name: string; level: number; description: string; tags: UiTagId[]; maxLevel: number }[];
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
  /** 48라운드: 노드 지도. 노드 지도를 쓰지 않는 층이면 null (계약 §10.1) */
  route: UiRoute | null;
  /** 49라운드: 무기 자원 게이지. 없으면 null (계약 §11.1). 61라운드: 단검 '가속'은 보이지 않는 자원이라 null */
  resource: UiWeaponResource | null;
  /** 49라운드: 음소거 상태 (계약 §11.3) */
  muted: boolean;
  /** 49라운드: 무기 시험장 안이면 true (계약 §11.4) */
  lab: boolean;
  /** 53라운드: 넣기/뽑기 상태 (F). 61라운드: F 넣기/뽑기를 지워 늘 null (칼 발도는 좌 홀드 — weaponVerbs) */
  carry: UiCarry | null;
  /** 56라운드: 무기 고유 자원. 없으면 null (계약 §13). 61라운드: 활 숨은 저격 갈래일 때만 */
  gauge: UiWeaponGauge | null;
  /** 61라운드 P1: 무기 4동사 (키캡 안내). 게임 씬 밖이면 null */
  weaponVerbs: UiWeaponVerbs | null;
  /** 56라운드: 그로기 상태. 칼·대검만, 그 밖은 null (계약 §13) */
  groggy: UiGroggy | null;
  /** 57라운드: 태그·세트 · 이중 개성 · 저주 (계약 §14.1) */
  build: UiBuildState;
  /** 60라운드 §14.8: 소모품 칸 (소모품 칸이 없는 모드면 null) */
  consumable: UiConsumableSlot | null;
  /** 60라운드 §14.9: 화면 안의 살아 있는 엘리트 */
  elites: UiElite[];
  /** 60라운드 §14.10: 잔 구간 전투·위험 노드 진행 중에만 */
  nodeTrial: UiNodeTrial | null;
  /** 61라운드 §15: 설정 (시스템 세이브 메타 영역에 저장된 값 — 타이틀에서도 들어 있다) */
  settings: UiSettings;
  /** 61 단계 6 §19: 수련장 (수련장 밖이면 null/생략). 수련장 안에서는 lab = false */
  training?: UiTraining | null;
  /** 62 §20: 첫 생 의식 (Setup 씬 안에서만 — 그 밖은 null/생략) */
  ritual?: UiRitual | null;
  /**
   * 62 P1-10 (시스템 추가): 첫 생 첫 노드들 동안 화면 아래 작은 4동사 키 막대를 보여 준다 (막는 패널 금지 — weaponVerbs 로 그린다).
   * 두 번째 생부터·시험장·수련장은 false/생략
   */
  keyBar?: boolean;
  /**
   * 62 (시스템 추가, 타이틀 UI 요청): 메타 요약 — 타이틀·일기장 귀퉁이 표시용. 게임 씬이 없을 때(타이틀·의식)도 메타 세이브에서 채운다.
   * lives = 끝난 생 수(첫 생이면 0) · souls = 보유 영혼 · bestFloor = 가장 깊이 간 층(없으면 0)
   */
  meta?: UiMetaSummary;
}

/** 62 `UiSnapshot.meta` */
export interface UiMetaSummary {
  lives: number;
  souls: number;
  bestFloor: number;
}

/**
 * 61라운드 §15 설정. UI 가 설정 화면에서 바꾸고 `uiCommands.setSettings` 로 넘긴다. 시스템이 즉시 적용하고 메타 세이브에 저장한다.
 * 범위 밖 값은 시스템이 잘라 쓴다(0~1). 기본값 = `UI_DEFAULT_SETTINGS`
 */
export interface UiSettings {
  /** 화면 흔들림 배율 0~1 (기본 1) */
  shake: number;
  /** 섬광(피격·결정타 화면 번쩍임) 켜기 (기본 true) */
  flash: boolean;
  /** 보스 '세상이 돈다' 화면 기울기 켜기 (기본 true) */
  tilt: boolean;
  /** 피해 숫자 표시 (기본 true) */
  damageNumbers: boolean;
  /** 전체 음량 0~1 (기본 1) */
  master: number;
  /** 배경음 0~1 (기본 1) */
  bgm: number;
  /** 효과음 0~1 (기본 1) */
  sfx: number;
}

/** 61라운드 §15 설정 기본값 */
export const UI_DEFAULT_SETTINGS: Readonly<UiSettings> = Object.freeze({
  shake: 1,
  flash: true,
  tilt: true,
  damageNumbers: true,
  master: 1,
  bgm: 1,
  sfx: 1,
  // 62 루프 2 시스템 D (P1-16 — 아래 D 절): 키 재설정 · 히트스톱 · 글자 크기
  keys: { up: 'W', down: 'S', left: 'A', right: 'D', dash: 'SPACE', interact: 'E', potion: 'Q' },
  hitstop: true,
  textScale: 1,
  // P21 (계약 dark-brutal §1): 고어 2 전체 · 1 줄임 · 0 끔
  gore: 2,
});

/** 60라운드 §14.8 소모품 칸 */
export interface UiConsumableSlot {
  /** 사용 키 이름 (시스템이 읽음 — 독주 Q 와 별개) */
  key: string;
  /** 같은 종류 최대 max. 빈 칸이면 null */
  item: { id: string; name: string; description: string; kind: 'throw' | 'drink'; count: number; max: number } | null;
}

/** 60라운드 §14.9 엘리트 이름표 */
export interface UiElite {
  id: string;
  /** 이름표 문구 (예 '불붙은 결사병', 자리표시) */
  name: string;
  prefixes: string[];
  hp: number;
  maxHp: number;
  /** 머리 위 화면 좌표 (논리 960×540 px, 카메라 반영 — §9.1 screen 과 같은 규칙) */
  screen: { x: number; y: number };
}

/** 60라운드 §14.10 노드 성과 진행 */
export interface UiNodeTrial {
  timeLimitMs: number;
  elapsedMs: number;
  hitTaken: boolean;
}

/** 60라운드 §14.10 노드 성과 등급 결과 (NODE_GRADED) */
export interface UiNodeGraded {
  nodeId: string;
  grade: UiNodeGrade | null;
  noHit: boolean;
  inTime: boolean;
  deltas: { gold?: number; personality?: number };
  text: string;
}

/** 60라운드 §14.11 숨은 길 열림 · 소모품 사용 */
export interface UiHiddenNodeFound {
  nodeId: string;
}
export interface UiConsumableUsed {
  id: string;
  name: string;
  left: number;
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
  /** 61라운드 P7: 사망 문장 뒤 이름 번짐 한 줄 ('이름이 번진다.' — 이름 글자 번짐 연출과 함께). 클리어면 없음 */
  smudgeLine?: string;
}

export interface UiBossInfo {
  name: string;
  hp: number;
  maxHp: number;
  phase: number;
  /** 61라운드 (계약 §17): BOSS_STARTED — 등장 연출 길이 ms (전투 시작까지, 0 = 연출 없음) */
  introMs?: number;
  /** 61라운드: BOSS_DIED — 파훼 경직 중 결정타로 끝냈는지 */
  finisher?: boolean;
}

/** 61라운드 단계 4 (계약 §17.1): BOSS_ROAR — 등장 포효 프레임에 한 번 */
export interface UiBossRoar {
  name: string;
}

/** 61라운드 (계약 §17): 보스 파훼(잔·기둥·술통·취권 넘어짐)·결정타. label = 짧은 이름, text = 알림 문구 */
export interface UiBossBreak {
  kind: 'cup' | 'pillar' | 'cask' | 'stumble' | 'finisher';
  label?: string;
  text?: string;
}

/** 스냅샷 보스 (61라운드 계약 §17 선택 필드: 국면 이름·눈금 · 파훼 경직 창 · 촛대(논리 960×540 화면 좌표) · 어둠) */
export interface UiBossSnapshot {
  name: string;
  hp: number;
  maxHp: number;
  phase: number;
  phaseName?: string;
  phaseNames?: string[];
  /** 체력 비율 눈금 (국면이 바뀌는 비율, 예 [0.65, 0.3]) */
  phaseMarks?: number[];
  /** 파훼로 무너진 동안 (받는 피해 증가 창) — 아니면 null/생략 */
  broken?: { leftMs: number; totalMs: number } | null;
  candles?: { x: number; y: number; lit: boolean }[];
  dark?: boolean;
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
  chooseNode: (id: string) => boolean;
  cancelChoose: () => boolean;
  setMuted: (muted: boolean) => void;
  startWeaponLab: () => void;
  /** 61라운드 §15 */
  getSettings: () => UiSettings;
  setSettings: (s: UiSettings) => void;
  /** 61 단계 6 §19 */
  startTraining: (room?: string) => UiTrainingStart;
  leaveTraining: () => void;
  /** 62 §20: 의식 명령 (의식 밖이면 false) · 지금 의식 상태 (의식 밖이면 null) */
  ritual: (cmd: UiRitualCommand) => boolean;
  getRitual: () => UiRitual | null;
  /** 62: 메타 요약 (메타 세이브) */
  getMeta: () => UiMetaSummary;
}

/**
 * §19 `startTraining` 결과: ok · combat(싸우는 중 — 끝난 뒤) · busy(메뉴·연출·전환 중) · boss(보스 노드 — 수련장은 보스 앞에서 열 수 없다)
 */
export type UiTrainingStart = 'ok' | 'combat' | 'busy' | 'boss';

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
  growth: null,
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
  route: null,
  resource: null,
  muted: false,
  lab: false,
  carry: null,
  gauge: null,
  weaponVerbs: null,
  groggy: null,
  build: { tags: [], dualTraits: [], curse: null },
  consumable: null,
  elites: [],
  nodeTrial: null,
  settings: { ...UI_DEFAULT_SETTINGS },
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
    const snap = impl?.getSnapshot();
    if (snap) return snap;
    // 61라운드 §15: 게임 씬이 없을 때(타이틀)도 저장된 설정을 알려 준다 · 62 §20: 의식 중이면 의식 상태
    return impl
      ? { ...EMPTY_SNAPSHOT, settings: impl.getSettings(), ritual: impl.getRitual(), meta: impl.getMeta() }
      : EMPTY_SNAPSHOT;
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
  /** 48라운드: 다음 노드 선택 (계약 §10.2). available 노드만 true. 62 H: 뒤이어 짧은 암전('fade') → 새 노드 */
  chooseNode(id: string): boolean {
    return impl?.chooseNode(id) ?? false;
  },
  /**
   * 53라운드 Q47: 노드 고르기 취소 (지도에서 Esc) — 지도를 닫고 주인공이 출구에서 한 걸음 물러난다.
   * 고르는 중이 아니면 false. 다시 출구에 들어서면 ROUTE_CHOOSE_OPEN 이 다시 온다
   */
  cancelChoose(): boolean {
    return impl?.cancelChoose() ?? false;
  },
  /** 49라운드: 음소거 (Esc 메뉴 설정에서, 계약 §11.3). M 키는 더 이상 음소거가 아니다 */
  setMuted(muted: boolean): void {
    impl?.setMuted(muted);
  },
  /** 49라운드: 무기 시험장 진입 (타이틀에서, 계약 §11.4) */
  startWeaponLab(): void {
    impl?.startWeaponLab();
  },
  /**
   * 61라운드 §15: 설정 적용·저장. 시스템이 즉시 반영(흔들림 배율·섬광·기울기·피해 숫자·음량 버스)하고 메타 세이브에 쓴다.
   * 다음 스냅샷의 `settings` 가 잘라 쓴 실제 값이다. `setMuted` 와 별개(빠른 음소거는 그대로)
   */
  setSettings(s: UiSettings): void {
    impl?.setSettings(s);
  },
  /**
   * 61 단계 6 §19: 수련장 열기 (타이틀 메뉴 '수련장' · 일기장 '수련장'). 런 중이면 런을 그대로 맡겨 두고(세이브·게이지·전표 무관)
   * 수련장에서 나가면 그 노드로 돌아온다 — 싸우는 중·보스 노드·메뉴/연출 중이면 거부(결과 문자열). room 을 주면 그 방으로 바로
   */
  startTraining(room?: string): UiTrainingStart {
    return impl?.startTraining(room) ?? 'busy';
  },
  /** §19: 수련장 나가기 (런에서 왔으면 그 노드로, 첫 생 선택에서 왔으면 시작 의식으로, 아니면 타이틀로) */
  leaveTraining(): void {
    impl?.leaveTraining();
  },
  /**
   * 62 §20 첫 생 의식 명령 (UI 가 그리고 시스템이 흐름·판정). 받아들였으면 true — 단계가 맞지 않으면 false (아무 일도 없다).
   * 새 상태는 `RITUAL` 이벤트·`getUiSnapshot().ritual` 로 온다
   */
  ritual: {
    /** name: 이름을 적었다 → 3획 · rewrite: 덧썼다 → 손이 기억한 무기로 운명 공개 (빈 이름은 '―' 로 적힌다) */
    submitName(name: string): boolean {
      return impl?.ritual({ kind: 'submitName', name }) ?? false;
    },
    /** (시스템 추가) rewrite: 이름을 적고 3획을 다시 그어 새 무기를 부른다 (회피 시험 없음) */
    redraw(name: string): boolean {
      return impl?.ritual({ kind: 'redraw', name }) ?? false;
    },
    /** strokes: 한 획 (UI 가 누름 → 뗌까지 모은 점). 점이 너무 적으면 false(획으로 치지 않음) · 판정 결과는 RITUAL_STROKE_JUDGED */
    stroke(points: UiRitualPoint[]): boolean {
      return impl?.ritual({ kind: 'stroke', points: points.map((p) => ({ x: p.x, y: p.y, t: p.t })) }) ?? false;
    },
    /** trial: 과제 이름 카드를 넘긴다 · fate: 기다리지 않고 바로 벽 밖으로 */
    next(): boolean {
      return impl?.ritual({ kind: 'next' }) ?? false;
    },
    /** trial: 회피 시험을 건너뛴다 (skippable 일 때 — 시험 보상 없음) */
    skip(): boolean {
      return impl?.ritual({ kind: 'skip' }) ?? false;
    },
    /** (시스템 추가) Esc — 한 단계 앞으로: strokes → name(그은 획 버림) · trial → strokes 처음부터 */
    back(): boolean {
      return impl?.ritual({ kind: 'back' }) ?? false;
    },
    /** (시스템 추가) rewrite: 영혼 강화 메뉴 (`MENU_OPEN` id 'meta', 닫기 cancelKey '0' → 다시 rewrite) */
    openMeta(): boolean {
      return impl?.ritual({ kind: 'openMeta' }) ?? false;
    },
  },
  /** 62 루프 2 시스템 D 명령 (아래 '62 루프 2 시스템 D' 절) */
  ...loop2DCommands(),
  /** 62 루프 2 시스템 C 명령 (아래 '62 루프 2 시스템 C' 절) */
  ...loop2CCommands(),
  /** 62 루프 2 시스템 E 명령 (아래 '62 루프 2 시스템 E' 절) */
  ...loop2ECommands(),
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

// ═══════════════════════════════════════════════════════════════════════════════════════════════════════════
// 62 루프 2 시스템 D (P16 §5·§6·§7·§8 — 점검 P1-2·12·13·14·16·17, P2-3·5·6·10·14). 계약 문서 §22.
// 이 절은 같은 모듈 안의 인터페이스 합치기(declaration merging)로 위 형식에 필드를 더한다. 새 필드는 모두 선택(?)이며
// 시스템이 채우기 전까지 비어 있다. 이름·문장은 시스템이 내려주는 문자열을 그대로 그린다(§9.8 원칙).
// ═══════════════════════════════════════════════════════════════════════════════════════════════════════════

/** D 이벤트 키 (UI_EVENTS 에 펼쳐 넣는다 — 함수 선언이라 위에서 먼저 쓸 수 있다) */
function loop2DEvents() {
  return {
    /** P1-12: 이벤트 선택 결과 (`UiEventResult`) — 결과 컷 한 장(그림 키 + 한 줄). 고른 직후 한 번 */
    EVENT_RESULT: 'ui:event-result',
    /** P1-12: 숨은 보상 알림 (`UiHiddenReward`) — '다음 노드 정보' 식 한 줄 (예: 징집병이 다음 싸움 끝에 갚으러 온다) */
    HIDDEN_REWARD: 'ui:hidden-reward',
    /** P1-13: 노점에서 샀다 (`UiShopPurchased`) — 반짝임·소리 연출용 */
    SHOP_PURCHASED: 'ui:shop-purchased',
    /** P1-16: 전체화면이 바뀌었다 (`{ on: boolean }`) — F11·설정·브라우저 Esc 모두 */
    FULLSCREEN: 'ui:fullscreen',
    /** P2-3: 노드 시련(완 조건)이 깨졌다 (`UiNodeTrialBroken`) — 첫 피격 또는 제한 시간 넘김 순간. 성공은 기존 NODE_GRADED(grade 'perfect') */
    NODE_TRIAL_BROKEN: 'ui:node-trial-broken',
    /** P2-6: 로딩 진행률 (`UiLoading`) — 부팅·노드 진입·보스·수련장 로드 중 여러 번, 끝나면 done true 로 한 번 */
    LOADING: 'ui:loading',
  } as const;
}

// --- P1-16 설정 확장 (§15) ---

export interface UiSettings {
  /** P1-16 키 재설정 (기본 `UI_DEFAULT_KEYS`). 스냅샷에는 늘 들어 있다 */
  keys?: UiKeyBindings;
  /** P1-16 히트스톱(타격 순간 멈춤) 켜기 (기본 true) */
  hitstop?: boolean;
  /** P1-16 글자 크기 (기본 1) */
  textScale?: UiTextScale;
}

// --- 기존 형식에 더하는 필드 (같은 모듈 인터페이스 합치기) ---

export interface UiMenu {
  /** P1-12: 이벤트 장면 머리 (id 'event' 메뉴 — NPC·설명). 없으면 옛 꼴(title·footer) */
  event?: UiEventScene;
  /** P1-13: 말하는 이 (shopTalk 메뉴의 상인 이름 등) */
  speaker?: string;
}

export interface UiMenuLine {
  /** P1-12: 이 선택의 대가 아이콘 줄 */
  costs?: UiEventIcon[];
  /** P1-12: 이 선택의 보상 아이콘 줄 (숨은 보상은 hidden true — UI 는 '?') */
  rewards?: UiEventIcon[];
}

export interface UiBossSnapshot {
  /**
   * P1-14: 국면 이름 공개 여부 (phaseNames 와 같은 길이). false 인 국면은 아직 오지 않은 국면 — phaseNames 의 그 칸은 '' 이고
   * UI 는 '???' 로 그린다. 국면이 바뀌는 순간(BOSS_PHASE) 그 칸이 true 가 된다
   */
  phaseRevealed?: boolean[];
}

export interface UiNodeTrial {
  /** P2-3: 완(完) 조건을 지키면 받는 보상 아이콘 (예 전표 25 · 각성 20, 위험 노드 ×2 반영) */
  reward?: UiEventIcon[];
  /** P2-3: 이미 깨졌으면 그 이유 (아직 지키는 중이면 null) */
  broken?: 'hit' | 'time' | null;
}

export interface UiEnemyIncoming {
  /** P2-10: 이번 웨이브가 들어오는 쪽 (선택) */
  side?: UiWaveSide;
}

export interface UiSnapshot {
  /** P1-13: 가장 가까운 노점 카드 (없으면 null/생략) */
  shopOffer?: UiShopOffer | null;
  /** P1-16: 지금 전체화면인가 */
  fullscreen?: boolean;
  /** P1-17: 화면 안 월드 팻말 (수련장·시험장 허수아비) */
  signs?: UiWorldSign[];
  /** P2-5: 나갈 때 이어하기가 자동 저장된다 (횟수 제한 없음 — savesLeft 는 더 쓰지 않는다) */
  autoSave?: boolean;
}

/** D 명령 구현 (시스템이 `__system.patchImpl({ loop2D })` 로 등록) */
interface Loop2DImpl {
  setFullscreen: (on: boolean) => boolean;
  isFullscreen: () => boolean;
  abandonRun: () => boolean;
  saveAndQuit: () => boolean;
}

interface SystemImpl {
  loop2D?: Loop2DImpl;
}

/** D 명령 (uiCommands 에 펼쳐 넣는다) */
function loop2DCommands() {
  return {
    /**
     * P1-16: 전체화면 켜기·끄기 (설정 화면 버튼 — 클릭·키 처리 안에서 불러야 브라우저가 허락한다). 바뀌었으면 true.
     * F11 은 시스템이 읽는다(브라우저 F11 대신 게임 전체화면). 결과는 `FULLSCREEN` 이벤트·`getUiSnapshot().fullscreen`
     */
    setFullscreen(on: boolean): boolean {
      return impl?.loop2D?.setFullscreen(on) ?? false;
    },
    toggleFullscreen(): boolean {
      const l = impl?.loop2D;
      return l ? l.setFullscreen(!l.isFullscreen()) : false;
    },
    /**
     * P2-5: 런 포기 — 지금 런을 사망과 같은 결산으로 끝낸다(영혼은 받은 만큼, 이어하기 지움). RUN_ENDED 가 온다.
     * 런 중이 아니면 false. 확인창은 UI 가 띄운다
     */
    abandonRun(): boolean {
      return impl?.loop2D?.abandonRun() ?? false;
    },
    /**
     * P2-5: 저장하고 나가기 — 이어하기를 자동 저장(횟수 제한 없음)하고 타이틀로. 싸우는 중이면 그 노드에 들어설 때 상태로 저장된다
     * (이어하면 그 노드를 처음부터). 런 중이 아니면 그냥 타이틀. `toTitle()` 도 이제 같은 저장을 한다
     */
    saveAndQuit(): boolean {
      return impl?.loop2D?.saveAndQuit() ?? false;
    },
  };
}

// ═══════════════════════════════════════════════════════════════════════════════════════════════════════════
// 62 루프 2 시스템 C (P16 §1~§4 — 점검 P1-5·6·7·8: 빌드 언어 '유품' · 층 끝 결산 · 죽음 연출·결산 · 메타 해금 '기억').
// D 절과 같은 방식: 같은 모듈 인터페이스 합치기로 위 형식에 필드를 더한다. 새 필드는 모두 선택(?)이다.
// 이름·문장 = 스토리 63 팩(시스템 data 에 합침) — UI 는 내려온 문자열을 그대로 그린다. 화면 용어는 계약 story-glossary.
// 그림 키는 시스템이 로드한 것만 내려온다(없으면 대체 그림 키 · 그것도 없으면 생략 → UI 는 키캡·글자로).
// ═══════════════════════════════════════════════════════════════════════════════════════════════════════════

/** C 이벤트 키 (UI_EVENTS 에 펼쳐 넣는다) */
function loop2CEvents() {
  return {
    /** P1-5: 유품 하나를 얻었다 (`UiRelic`) — 알림 한 줄(개성 획득과 같은 꼴) */
    RELIC_GAINED: 'ui:relic-gained',
    /**
     * P1-6: 1층 끝 결산 (`UiFloorEnd`) — 군주의 유품·(있으면) 개성 발현 한 장이 끝나고 data runEnd.floorEnd.delayMs(1.2초) 뒤 한 번.
     * 곧바로 RUN_ENDED(`UiResult.cleared` true · `floorEnd` · `summary`)가 뒤따르고 결과 씬이 시작된다
     */
    FLOOR_END: 'ui:floor-end',
    /** P1-7: 사망 연출 시작 (`UiDeathFx`) — 슬로모·먹 번짐(시스템이 월드 위에 그린다) 동안 UI 는 HUD 를 걷는다. 끝나면 RUN_ENDED */
    DEATH_STARTED: 'ui:death-started',
    /** P1-8: 기억이 바뀌었다 (`UiMemoryBook`) — 해금 직후 · 소품을 고른 직후 */
    MEMORY_CHANGED: 'ui:memory-changed',
  } as const;
}

// --- P1-5 유품 카드 ---

/*
 * 유품 메뉴 = 메뉴 id 'passive' 그대로(카드 3장 레이아웃) · 줄 kind 'passive'(호환 — UiChoiceKind 를 넓히지 않는다) + `line.relic` 이
 * 있으면 유품 카드: label = 이름 · detail = 한 문장(수치 없음) · 수치는 `line.relic.detail`(상세 보기 D). 머리표는 '유품'으로 그린다.
 * 보스 '군주의 유품'은 title '군주의 유품' · `line.relic.source` 'boss'.
 */

// --- P1-6·P1-7 층 끝 · 죽음 결산 ---

/** 출구 방향 (`UiSnapshot.exitHint`) — 출구가 열렸고 화면 밖이면 UI 가 가장자리 화살표를 그린다 */
export interface UiExitHint {
  /** 출구 가운데 논리 화면 좌표 (화면 밖이면 화면 테두리 안으로 붙인 점) */
  x: number;
  y: number;
  /** 화살표 글 ('오르는 길' — 층 출구 · 노드 출구는 '') */
  label: string;
  /** 화면 가운데 → 출구 방향 (rad, 0 = 오른쪽, 아래가 +) */
  angle: number;
  /** 출구가 화면 안에 보이는가 (true 면 화살표를 숨겨도 된다) */
  onScreen: boolean;
  /** 주인공 → 출구 거리 (칸) */
  distTiles: number;
}

// --- 기존 형식에 더하는 필드 ---

export interface UiMenuLine {
  /** P1-5: 유품 카드 (줄 kind 'passive' + 이 필드) */
  relic?: UiRelic;
  /** P1-8: 기억 한 칸 (메뉴 'meta' · 'aspect' · 'keepsake') */
  memory?: UiMemoryEntry;
}

export interface UiSnapshot {
  /** P1-5: 가진 유품 (얻은 순서). `passives` 는 호환용으로 같은 유품을 옛 꼴(이름·한 문장)로 싣는다 */
  relics?: UiRelic[];
  /** P1-6: 출구 방향 (출구가 열렸고 노드를 고르는 중이 아닐 때만 — 아니면 null) */
  exitHint?: UiExitHint | null;
}

export interface UiResult {
  /** P1-6·P1-7: 결산 (사망·층 끝) */
  summary?: UiRunSummary;
  /** P1-6: 층 끝 결산 (cleared true 이고 층 끝일 때) */
  floorEnd?: UiFloorEnd;
}

export interface UiRitual {
  /**
   * P1-8: 운명 공개 뒤 고르기 — picking = 지금 여는 고르기 메뉴('aspect' · 'keepsake' · null) · aspect = 고른 양상 · keepsake = 지닐 소품.
   * 고르는 동안은 운명 공개 시계가 멈춘다(ritual.next 거부)
   */
  memory?: { picking: 'aspect' | 'keepsake' | null; aspect: UiMemoryEntry | null; keepsake: UiMemoryEntry | null };
  /** P1-5: 회피 시험 결과 한 줄 ('첫 개성 발현 때 카드 {n}장에서 고른다.' — fate, 첫 생·결과가 있을 때만) */
  giftNote?: string;
}

/** C 명령 구현 (시스템이 `__system.patchImpl({ loop2C })` 로 등록) */
interface Loop2CImpl {
  memoryBook: () => UiMemoryBook;
  unlockMemory: (id: string) => boolean;
  setKeepsake: (id: string | null) => boolean;
  endChoice: (c: UiEndChoice) => boolean;
}

interface SystemImpl {
  loop2C?: Loop2CImpl;
}

/** C 명령 (uiCommands 에 펼쳐 넣는다) */
function loop2CCommands() {
  return {
    /** P1-6·P1-7: 결과 화면 선택 — 'reborn' 다시 태어난다(= startNewRun) · 'closeDiary' 일기장 덮기(= toTitle) */
    endChoice(c: UiEndChoice): boolean {
      return impl?.loop2C?.endChoice(c) ?? false;
    },
    /** P1-8 일기장 '기억' 장 */
    memory: {
      /** 지금 기억 장 (메타 세이브 — 어느 화면에서나) */
      book(): UiMemoryBook | null {
        return impl?.loop2C?.memoryBook() ?? null;
      },
      /** 연다 (영혼 부족·이미 열림·모르는 id 면 false). 연 뒤 MEMORY_CHANGED */
      unlock(id: string): boolean {
        return impl?.loop2C?.unlockMemory(id) ?? false;
      },
      /** 다음 생에 지닐 소품을 미리 정한다 (null = 빈손 · 안 열린 소품이면 false) */
      setKeepsake(id: string | null): boolean {
        return impl?.loop2C?.setKeepsake(id) ?? false;
      },
    },
  };
}

// ═══════════════════════════════════════════════════════════════════════════════════════════════════════════
// 62 루프 2 시스템 E (도영 님 피드백: 발판 출구 → 문 나가기 · 메뉴 뜨기 전 렉 · 렉 중 원치 않는 선택). 계약 문서 §24.
// 같은 모듈 인터페이스 합치기로 필드를 더한다. 새 필드는 모두 선택(?).

export interface UiSnapshot {
  /** 출구 문 상태. UI 는 walkOut·inside·walkIn 동안 조작 안내·키 막대를 숨기고, 열림(open) 순간 '오르는 길' 문구를 띄울 수 있다 */
  door?: UiDoor | null;
}

export interface UiExitHint {
  /** 출구가 어느 벽의 문인가 (출구 = 외벽 문 — 바닥 발판 없음) */
  side?: UiDoorSide;
}

export interface UiMenu {
  /**
   * 시스템이 이 메뉴를 연 시각 (`performance.now()` ms — UI 와 같은 시계). 같은 id 를 다시 그리는 것(상점 갱신 등)은 처음 시각 유지.
   * 시스템은 `max(openedAt, menuShown 시각) + armMs` 전에 온 선택(`uiCommands.select`)을 무시한다 (렉·정지 사이 쌓인 클릭·숫자 키)
   */
  openedAt?: number;
  /** 열린 뒤 선택을 받지 않는 시간 (ms) */
  armMs?: number;
}

export interface UiRoute {
  /** choosing 이 켜진 시각 (`performance.now()`) — `chooseNode` 도 UiMenu 와 같은 규칙으로 armMs 동안 무시 */
  openedAt?: number;
  armMs?: number;
}

/** E 명령 구현 (시스템이 `__system.patchImpl({ loop2E })`) */
interface Loop2EImpl {
  menuShown: (id: UiMenuId | 'route') => void;
}

interface SystemImpl {
  loop2E?: Loop2EImpl;
}

/** E 명령 (uiCommands 에 펼쳐 넣는다) */
function loop2ECommands() {
  return {
    /**
     * 메뉴(또는 'route' 노드 고르기 지도)를 실제로 화면에 그렸다 — 기다림(성과 카드 등)·등장 애니가 끝난 순간 한 번.
     * 시스템은 그때부터 armMs 를 다시 센다 (늦은 쪽). 부르지 않아도 openedAt 기준 가드는 그대로
     */
    menuShown(id: UiMenuId | 'route'): void {
      impl?.loop2E?.menuShown(id);
    },
  };
}

// ═══════════════════════════════════════════════════════════════════════════════════════════════════════════
// 62 루프 2 시스템 G (UI E·F 요청 처리). 계약 문서 §24. 같은 모듈 인터페이스 합치기 — 새 필드는 모두 선택(?).
// - shopTalk 메뉴에 `UiMenu.event`(사연 메뉴와 같은 머리 — speaker 종군 상인 · portrait npc_merchant 0프레임 · greet 상인 한마디)
// - shopTalk '외상을 단다'(key 'credit') 줄 = `costs`[{kind 'curse', label '저주 외상'}] + detail 대체 글('장터' — 용어집)
// - `UiShopOffer.screen` = 보이는 물건 그림 윗변 가운데 (칸 위 투명 여백 제외) · `UiShopPurchased.stallId` = 노점에서 사면 그 칸 id
// - 사연 결과 컷(`EVENT_RESULT.cutKey`)이 있으면 같은 문장의 STORY 'event' 자막은 오지 않는다
// - 기억 장 그림(소품·모양·떠올릴 개성)은 부팅에서 받는다 — 타이틀·의식·결과 어디서 `memory.book()` 을 불러도 iconKey 가 채워진다
// ═══════════════════════════════════════════════════════════════════════════════════════════════════════════

export interface UiSnapshot {
  /** 주인공 화면 자리 (게임 씬 — 런·시험장·수련장. 주인공이 없으면 null/생략) */
  hero?: UiHeroScreen | null;
}

// ═══════════════════════════════════════════════════════════════════════════════════════════════════════════
// 62 시스템 H (도영 님 추가 지시: 키아트 넘어가는 과정 → 지도로 먼저 고르고 키아트는 작은 미리보기). 같은 모듈 인터페이스 합치기 —
// 새 필드는 모두 선택(?).
// - 노드 이동: 외벽 문 안(`UiDoor.phase` 'inside')에 들어서면 그림 속 입구 전환('exitRoom') 없이 곧바로 `ROUTE_CHOOSE_OPEN`.
//   갈 길이 하나여도 지도를 연다(옛 P2-1 '외길 자동 진행' 폐지). 고르면 `TRANSITION_BEGIN{mode:'fade', durationMs, nodeId}` → UI 가
//   짧게 덮고 COVERED → 씬 재시작 → READY → END (입구 그림 확대 'enterNode' 대신). 그다음 반대편 문으로 입장(§23). 취소(Esc)는 §23 그대로.
// - 수련장: 지도에서 방 고름 → 'fade' (nodeId = 방 id, nodeKind training|boss) · 방 출구 문 안 → 'fade' → 지도 마당(지도 메뉴).
// - 층 이동 'floor' · 타이틀 → 첫 생 · 탄생은 그대로.
// - 미리보기: `UiRouteNode.previewKey`·`previewRegion`, 수련장 지도 메뉴 줄 `UiMenuLine.previewKey`·`previewRegion`.
// ═══════════════════════════════════════════════════════════════════════════════════════════════════════════

export interface UiRouteNode {
  /**
   * 지도 미리보기 그림 텍스처 키 `paint/door_<지역>_<종류>` (art §28 입구 그림 — 정확 → 별칭 → `<지역>_battle`; 보스 = door_hall_boss).
   * 매니페스트에 그림이 있으면 늘 채운다 — **텍스처가 아직 없을 수 있다**(시스템이 노드 진입 뒤 고를 수 있는 노드 + 그다음 열을 미리
   * 받는다, 지도 열기를 막지 않음). UI 는 `textures.exists(previewKey)` 로 보고, 없으면 `previewRegion` 키아트로 대체
   * (받히는 순간 Phaser `addtexture-<key>`). 그림이 없는 층·지역이면 생략
   */
  previewKey?: string;
  /** 미리보기 대체 키아트 지역 id (waste·gate·outer·brewery·hall … — 보스 노드도 그 열의 지역 'hall'). 지역 없는 층이면 생략 */
  previewRegion?: string;
}

export interface UiMenuLine {
  /** (62 H) 수련장 지도(`training` 메뉴) 줄 미리보기 그림 — `paint/door_training_training` · 만취 그림자 방 `paint/door_training_boss` (매니페스트에 있으면 — 지도 마당이 지도와 함께 받는다. UiRouteNode.previewKey 와 같이 `textures.exists` 로 확인) */
  previewKey?: string;
  /** (62 H) 수련장 지도 줄 대체 지역 id = 'training' */
  previewRegion?: string;
}

// ═════════════════════════════════════════════════════════════════
// P19 S1 (자유 전투 — 계약 free-combat.md §1). 시스템 내부 반응 이벤트를 같은 이름의 `ui:` 접두로 중계한다.
// 같은 프레임 같은 적의 ENEMY_KNOCKED → ENEMY_WALL_SLAM 순서 보장. x·y 는 월드 px, `screen` 은 그 순간의 논리 화면 좌표
// (960×540 — 카메라 줌·스크롤 반영, §9.1 screen 과 같은 규칙). COMBO_STREAK 만 좌표 없음.
// ═════════════════════════════════════════════════════════════════

/** P19 S1 이벤트 키 (UI_EVENTS 에 펼쳐 넣는다) */
function p19S1Events() {
  return {
    /** 움찔·버팀 깨짐 (`UiEnemyStaggered`) */
    ENEMY_STAGGERED: 'ui:enemy-staggered',
    /** 넉백 단계 (`UiEnemyKnocked`) */
    ENEMY_KNOCKED: 'ui:enemy-knocked',
    /** 벽꽝 (`UiEnemyWallSlam`) — 반응 팝 */
    ENEMY_WALL_SLAM: 'ui:enemy-wall-slam',
    /** 볼링 — 날아간 적이 다른 적과 부딪침 (`UiEnemyBowled`) — 반응 팝 */
    ENEMY_BOWLED: 'ui:enemy-bowled',
    /** 띄움 · 착지 (`UiEnemyLaunched` · `UiEnemyLanded`) */
    ENEMY_LAUNCHED: 'ui:enemy-launched',
    ENEMY_LANDED: 'ui:enemy-landed',
    /** 낙하 구역으로 떨어짐 (`UiEnemyFell`) — 반응 팝 */
    ENEMY_FELL: 'ui:enemy-fell',
    /** 위험물 폭발 (`UiHazardExploded`) — 반응 팝 */
    HAZARD_EXPLODED: 'ui:hazard-exploded',
    /** 위험물 점화 (`UiHazardIgnited`) */
    HAZARD_IGNITED: 'ui:hazard-ignited',
    /** 연속 처치 (`UiComboStreak`) — 처치 사이 ≤ 1.5초, 2 이상일 때마다 */
    COMBO_STREAK: 'ui:combo-streak',
    /**
     * P19 2단계: 적의 지나가는 대사 (`UiEnemyBark` — 스토리 65 팩 barks, kind speech). 머리 위 말풍선은 UI 가 나중에 —
     * 시스템은 내보내기만 (같은 적 4초 · 전체 1.5초 간격)
     */
    ENEMY_BARK: 'ui:enemy-bark',
  } as const;
}

export interface UiEnemyBark {
  /** 논리 화면 좌표 (머리 위 — 그림 위끝, 960×540, 카메라 반영) */
  screen: { x: number; y: number };
  /** 적 종류 id (drummer · bomber) */
  id: string;
  x: number;
  y: number;
  /** 대사 갈래 (drummer: beat·flee / bomber: charge·fuse·launched) */
  kind: string;
  text: string;
}

export interface UiEnemyStaggered {
  /** 논리 화면 좌표 (960×540, 카메라 반영) */
  screen: { x: number; y: number };
  id: string;
  x: number;
  y: number;
  /** flinch = 움찔(버팀 0) · stagger = 버팀이 깨짐 */
  kind: 'flinch' | 'stagger';
  ms: number;
}

export interface UiEnemyKnocked {
  /** 논리 화면 좌표 (960×540, 카메라 반영) */
  screen: { x: number; y: number };
  id: string;
  x: number;
  y: number;
  /** 1 밀림 · 2 날림 · 3 크게 날림 · 4 화면 가로지름 */
  tier: 1 | 2 | 3 | 4;
  dirX: number;
  dirY: number;
  distTiles: number;
}

export interface UiEnemyWallSlam {
  /** 논리 화면 좌표 (960×540, 카메라 반영) */
  screen: { x: number; y: number };
  id: string;
  x: number;
  y: number;
  speed: number;
  bonusDamage: number;
  surface: 'wall' | 'prop' | 'pillar';
}

export interface UiEnemyBowled {
  /** 논리 화면 좌표 (960×540, 카메라 반영) */
  screen: { x: number; y: number };
  hitter: string;
  target: string;
  x: number;
  y: number;
  damage: number;
}

export interface UiEnemyLaunched {
  /** 논리 화면 좌표 (960×540, 카메라 반영) */
  screen: { x: number; y: number };
  id: string;
  x: number;
  y: number;
  airMs: number;
}

export interface UiEnemyLanded {
  /** 논리 화면 좌표 (960×540, 카메라 반영) */
  screen: { x: number; y: number };
  id: string;
  x: number;
  y: number;
  slam: boolean;
}

export interface UiEnemyFell {
  /** 논리 화면 좌표 (960×540, 카메라 반영) */
  screen: { x: number; y: number };
  id: string;
  x: number;
  y: number;
  zone: 'water' | 'drop' | 'fire';
}

export interface UiHazardExploded {
  /** 논리 화면 좌표 (960×540, 카메라 반영) */
  screen: { x: number; y: number };
  x: number;
  y: number;
  kind: 'cask' | 'still' | 'bottle';
  chain: number;
}

export interface UiHazardIgnited {
  /** 논리 화면 좌표 (960×540, 카메라 반영) */
  screen: { x: number; y: number };
  x: number;
  y: number;
  kind: 'pool' | 'cask' | 'still';
  radiusTiles: number;
}

export interface UiComboStreak {
  count: number;
  windowMs: number;
}

// ═════════════════════════════════════════════════════════════════
// P19 S2 카메라 신호 (계약 free-combat.md §4)
// ═════════════════════════════════════════════════════════════════

export interface UiCamera {
  /** 논리 배율 (탐색 1.75 · 전투 중 1.6 · 보스 1.5 — 바뀔 때 0.6초에 걸쳐 옮겨 가는 중간값) */
  zoom: number;
  /** 살아 있는 적 ≥ 1 */
  combat: boolean;
  /** 보이는 월드 사각형 (월드 px — Phaser worldView, 흔들림 포함). 월드 → 논리 화면 = (wx − x) × 960 / w */
  view: { x: number; y: number; w: number; h: number };
}

export interface UiSnapshot {
  /** P19 §4: 게임 월드 카메라 (게임 씬 밖이면 생략) */
  camera?: UiCamera;
}

// ═════════════════════════════════════════════════════════════════
// P19 S3 화면 밖 적 (계약 free-combat.md §4) — UI 가 화면 가장자리 표식
// ═════════════════════════════════════════════════════════════════

export interface UiOffscreenEnemy {
  /** 이 씬 안에서 같은 적이면 같은 번호 (표식 이어 그리기) */
  id: number;
  /** 화면(카메라 worldView) 가운데 → 적 방향 (rad — +x 오른쪽, +y 아래) */
  angle: number;
  /** 주인공과의 거리 (칸) */
  distTiles: number;
  /** 예고·공격 중이면 그 위협 색 단계 (계약 §2: warn 호박 · danger 적 · ranged 청백), 아니면 null */
  threat: 'warn' | 'danger' | 'ranged' | null;
}

export interface UiSnapshot {
  /** P19 S3: 카메라 화면(worldView) 밖에 있는 살아 있는 적. 없으면 [] (게임 씬 밖이면 생략) */
  offscreen?: UiOffscreenEnemy[];
}

// ═════════════════════════════════════════════════════════════════
// P21 어두운 톤 · 잔혹 전투 · 상흔 (계약 dark-brutal.md §1·§2). 시스템 내부 이벤트를 같은 이름의 `ui:` 접두로 중계한다
// (free-combat §1 과 같은 규칙 — x·y 가 있으면 논리 화면 좌표 `screen` 을 붙인다).
// ═════════════════════════════════════════════════════════════════

/** P21 §1 고어 설정: 2 전체(기본) · 1 줄임(절단·잘린 조각 없음, 피 1/3·더 어둡게) · 0 끔(먹·재 입자, 데칼·사망 변형 없음) */
export type UiGoreLevel = 0 | 1 | 2;

export interface UiSettings {
  /** P21 §1 고어 (기본 2). 스냅샷에는 늘 들어 있다 */
  gore?: UiGoreLevel;
}

/** P21 이벤트 키 (UI_EVENTS 에 펼쳐 넣는다) */
function p21Events() {
  return {
    /** 처형 대상(공격 키가 처형이 되는 적 하나) 켜기·끄기 (`UiEnemyExecutable`) — 바뀔 때만, on:false 는 즉시 숨김 (위치는 스냅샷 `executable`) */
    ENEMY_EXECUTABLE: 'ui:enemy-executable',
    /** 처형 시작 (`UiPlayerExecute`) — 끝나면 일반 처치 이벤트 */
    PLAYER_EXECUTE: 'ui:player-execute',
    /** 주인공 상처 단계가 바뀜 · 화살이 박힘 (`UiPlayerWounded`) */
    PLAYER_WOUNDED: 'ui:player-wounded',
    /** HP ≤ 25% 진입·이탈 (`UiLowHp`) */
    LOW_HP: 'ui:low-hp',
  } as const;
}

export interface UiEnemyExecutable {
  /** 논리 화면 좌표 (960×540, 카메라 반영 — 적 발밑). on false 면 마지막 자리 */
  screen: { x: number; y: number };
  /** 적 종류 id */
  id: string;
  /** 이 씬 안의 개체 번호 (`UiOffscreenEnemy.id` 와 같은 번호 — 켜기·끄기 짝 맞추기) */
  uid: number;
  x: number;
  y: number;
  on: boolean;
}

export interface UiPlayerExecute {
  /** 논리 화면 좌표 (대상 자리) */
  screen: { x: number; y: number };
  /** 대상 적 종류 id */
  target: string;
  x: number;
  y: number;
  weapon: 'katana' | 'greatsword' | 'dagger' | 'bow';
  /** 처형 동작 길이 */
  ms: number;
  /** 시작 → 결정타 ms (시스템 추가 — 결정타 순간 연출용) */
  impactMs?: number;
}

export interface UiPlayerWounded {
  /** 0 성함 · 1 (≤75%) 가는 균열 · 2 (≤50%) 균열 벌어짐 · 3 (≤25%) 크게 갈라짐 */
  stage: 0 | 1 | 2 | 3;
  /** 몸에 박힌 화살 수 (0~5, 노드가 바뀌면 0) */
  arrows: number;
}

export interface UiLowHp {
  on: boolean;
  /** HP 비율 0~1 */
  ratio: number;
}

export interface UiSnapshot {
  /** P21 §2: 주인공 상처 (게임 씬 밖이면 생략) */
  player?: { wound: UiPlayerWounded };
  /**
   * P21 §2 조정: 지금 처형 가능한 적들 — 개체 uid · 화면 좌표(발밑, 논리 960×540). 없으면 [] (게임 씬 밖이면 생략).
   * 공격 키가 처형으로 바뀌는 대상은 그중 `ui:enemy-executable{on:true}` 를 받은 것 하나 (가장 가까운 적)
   */
  executable?: { uid: number; screen: { x: number; y: number } }[];
}
