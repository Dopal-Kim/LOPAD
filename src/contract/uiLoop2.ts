/**
 * 62 루프 2 (시스템 C·D·E) UI 계약 형식 중 **새로 생긴 독립 형식·상수** — `ui.ts` 가 2000줄을 넘어 나눴다(62 루프 2 F, 루트 CLAUDE.md 6-1).
 * UI 는 늘 `contract/ui` 에서 가져온다(`ui.ts` 가 이 파일을 그대로 재수출). 기존 형식에 필드를 더하는 인터페이스 합치기
 * (UiSnapshot·UiMenu·UiSettings 등)와 이벤트·명령은 같은 모듈이어야 해서 `ui.ts` 의 C·D·E 절에 남는다.
 */
import type { UiInteractBlockReason, UiMenuLine, UiRarity, UiRoute, UiTagId } from './ui';
// ═══ 62 루프 2 시스템 D (P16 §5~§8 · 계약 문서 §22) ═══

// --- P1-12 이벤트: NPC · 설명 → 선택지(대가·보상 아이콘) → 결과 컷 ---

/** 대가·보상 아이콘 종류 — UI 가 자기 아이콘(assets/ui)으로 그린다. unknown = '?' (숨은 보상) */
export type UiEventIconKind =
  | 'gold'
  | 'potion'
  | 'hp'
  | 'maxHp'
  | 'growth'
  | 'passive'
  | 'sense'
  | 'curse'
  | 'discount'
  | 'enemies'
  | 'diary'
  | 'unknown';

/** 아이콘 한 칸. amount 는 표시용 수치(없으면 생략) · label = 그대로 그릴 짧은 글 (예 '전표 30', '독주 1') · hidden = '?' 로 가린 보상 */
export interface UiEventIcon {
  kind: UiEventIconKind;
  amount?: number;
  label: string;
  hidden?: boolean;
}

/** 이벤트 장면 머리 — 메뉴 id 'event' 에 붙는다 (`UiMenu.event`). UI 는 설명(위) → 선택지(아래) 순서로 그린다 */
export interface UiEventScene {
  /** 이벤트 id (conscript · diary · tasting · offering · droppedLedger …) */
  id: string;
  name: string;
  /** 말하는 이 (NPC 이벤트만 — 예 '낙오한 징집병'). 소품 이벤트면 생략 */
  speaker?: string;
  /** 말하는 이 그림 텍스처 키·프레임 (시스템이 로드해 둔 NPC 시트 `structures/v3/npc_*` 0프레임 — 없으면 생략) */
  portrait?: { key: string; frame: string | number };
  /** 첫 마디 (speaker 가 있으면 그 사람의 말, 없으면 지문 한 줄) — 설명 위에 */
  greet?: string;
  /** 설명 문단 (위) — 스토리 팩 intro */
  intro: string[];
  /** 머리말 (63 팩 events.ui — costHead '내준다' · gainHead '얻는다' · unknown '?' · pick '하나를 고른다') */
  heads?: Record<string, string>;
}

/** EVENT_RESULT 페이로드 — 결과 컷 한 장 */
export interface UiEventResult {
  eventId: string;
  /** 고른 선택지 key ('0' = 지나간다) */
  optionKey: string;
  /** 결과 컷 그림 텍스처 키 (시스템이 로드해 둔 `events/cut_<이벤트>_<선택지>` — 없으면 생략, UI 는 이벤트 그림·단색으로 대체) */
  cutKey?: string;
  /** 결과 한 줄 (스토리 팩 result) */
  line: string;
  /** 얻고 잃은 것 (아이콘 줄) */
  gains: UiEventIcon[];
  losses: UiEventIcon[];
}

/** HIDDEN_REWARD 페이로드 — 숨은 보상이 생겼다/받았다 */
export interface UiHiddenReward {
  /** 'later' = 다음에 받는다(예약) · 'paid' = 지금 받았다 */
  state: 'later' | 'paid';
  /** 예약 종류 (laterGold 다음 전투 끝 전표 · extraWave 다음 전투 웨이브 +1 · shopDiscount 다음 상점 할인) */
  kind: 'laterGold' | 'extraWave' | 'shopDiscount';
  /** 그대로 그릴 한 줄 */
  text: string;
  /** 언제 (다음 전투 노드 끝 · 다음 상점) */
  when: 'nextBattle' | 'nextShop';
  icon: UiEventIcon;
}

// --- P1-13 상점: 노점 칸 위 물건 → 다가가면 카드 + E 사기 · 다시 진열·외상은 상인 대사 ---

/** 노점 카드 (`UiSnapshot.shopOffer`) — 주인공이 가장 가까운 노점 칸 반경 안에 있을 때 하나. 없으면 null/생략 */
export interface UiShopOffer {
  /** 노점 칸 id ('stall:1' …) */
  stallId: string;
  /**
   * 상점 메뉴 줄 그대로 (계약 §14.6 — key·label·detail·price·rarity·trait·tags·soldOut). 카드 내용은 이 줄로 그린다
   * (품목 목록은 시스템 C 가 정한다 — 줄 형식이 같으면 카드도 같다)
   */
  line: UiMenuLine;
  /** 물건 그림 텍스처 키·프레임 (월드 드랍 그림 items/v3 — 시스템이 로드해 둔 것, 없으면 생략) */
  icon?: { key: string; frame: string | number };
  /** 사기 키 (설정의 상호작용 키, 기본 'E') */
  buyKey: string;
  /** 지금 살 수 있나 (= reason null) · 못 사는 이유 */
  usable: boolean;
  reason: UiInteractBlockReason | null;
  reasonText: string;
  /** 카드를 띄울 자리 — 보이는 물건 그림 윗변 가운데 (칸 위 투명 여백 제외 — 62 G, 둥실 흔들림을 따라감. 논리 960×540 화면 좌표) */
  screen: { x: number; y: number };
}

/** SHOP_PURCHASED 페이로드 */
export interface UiShopPurchased {
  /** 산 줄의 노점 칸 id (노점 E · 외상 모두 — 62 G). 노점이 없는 글자 목록 상점·다시 진열이면 null */
  stallId: string | null;
  key: string;
  name: string;
  price: number;
}

/** D 구조물 종류 — eventNpc = 이벤트 NPC (E 로 말 걸기, actionKey 'eventNpc.talk') · shopStall = 노점 칸 물건 (E 로 사기, actionKey 'stall.buy') */
export type UiLoop2DStructureKind = 'eventNpc' | 'shopStall';

/**
 * D 메뉴 id — shopTalk = 종군 상인과 말하기 (줄: 'reroll' 다시 진열(price) · 'credit' 외상 · '0' 그만 본다).
 * 외상을 고르면 같은 id 로 노점 물건 줄(값 없음) + '0' 이 다시 온다. 말하는 이 = `UiMenu.speaker`, 상인 한마디 = `footer`.
 * 62 G: `UiMenu.event`(UiEventScene — id 'merchant' · speaker · portrait npc_merchant 0프레임 · greet = footer 와 같은 한마디 · intro [])
 * 가 붙어 사연 대화 꼴로 그릴 수 있다. 'credit' 줄 대가 = `costs`[{kind 'curse', label '저주 외상'}] · detail = 아이콘을 안 그릴 때의 대체 글
 */
export type UiLoop2DMenuId = 'shopTalk';

// --- P1-16 설정 확장 (§15) ---

/** 키 재설정 대상 동작 */
export type UiBindAction = 'up' | 'down' | 'left' | 'right' | 'dash' | 'interact' | 'potion';

/** 동작 → 키 이름 (Phaser 키 이름: 'W' · 'SPACE' · 'SHIFT' · 'E' · 'UP' …). 표시 이름은 `UI_KEY_LABELS` */
export type UiKeyBindings = Record<UiBindAction, string>;

/** 기본 키 */
export const UI_DEFAULT_KEYS: Readonly<UiKeyBindings> = Object.freeze({
  up: 'W',
  down: 'S',
  left: 'A',
  right: 'D',
  dash: 'SPACE',
  interact: 'E',
  potion: 'Q',
});

/**
 * 바꿀 수 있는 키 (이 밖의 키·겹치는 키는 시스템이 받아들이지 않고 앞 값을 둔다). 고정 키는 빠져 있다:
 * Esc(일시정지) · M·Tab(지도·빌드) · F11(전체화면) · F2 · Enter · L(시험장) · R(장전) · C(소모품) · Shift(달리기) · 마우스
 */
export const UI_BINDABLE_KEYS: readonly string[] = Object.freeze([
  ...'ABDEFGHIJKNOPQSTUVWXYZ'.split(''),
  'ONE',
  'TWO',
  'THREE',
  'FOUR',
  'FIVE',
  'SIX',
  'SEVEN',
  'EIGHT',
  'NINE',
  'ZERO',
  'COMMA',
  'PERIOD',
  'FORWARD_SLASH',
  'SEMICOLON',
  'QUOTES',
  'OPEN_BRACKET',
  'CLOSED_BRACKET',
  'MINUS',
  'PLUS',
  'BACK_SLASH',
  'SPACE',
  'CTRL',
  'ALT',
  'UP',
  'DOWN',
  'LEFT',
  'RIGHT',
]);

/** 키 이름 → 화면에 그릴 이름 (없으면 키 이름 그대로) */
export const UI_KEY_LABELS: Readonly<Record<string, string>> = Object.freeze({
  SPACE: 'Space',
  SHIFT: 'Shift',
  CTRL: 'Ctrl',
  ALT: 'Alt',
  UP: '↑',
  DOWN: '↓',
  LEFT: '←',
  RIGHT: '→',
  ONE: '1',
  TWO: '2',
  THREE: '3',
  FOUR: '4',
  FIVE: '5',
  SIX: '6',
  SEVEN: '7',
  EIGHT: '8',
  NINE: '9',
  ZERO: '0',
  COMMA: ',',
  PERIOD: '.',
  FORWARD_SLASH: '/',
  SEMICOLON: ';',
  QUOTES: "'",
  OPEN_BRACKET: '[',
  CLOSED_BRACKET: ']',
  MINUS: '-',
  PLUS: '=',
  BACK_SLASH: '\\',
});

/** 글자 크기 2단 (1 = 보통 · 1.5 = 크게 — Galmuri 도트가 흐려지지 않는 배율). UI 글자에 곱한다 — 시스템 월드 글자(피해 숫자·PERFECT 등)도 같이 */
export type UiTextScale = 1 | 1.5;

// --- P1-17 · P2-3 · P2-6 · P2-10 ---

/** P1-17 월드 팻말 (수련장·시험장 허수아비 — 옛 디버그 글자 대신 UI 가 나무 팻말로 그린다) */
export interface UiWorldSign {
  id: string;
  /** dummy = 맞는 허수아비 · turret = 쏘는 허수아비 */
  kind: 'dummy' | 'turret';
  /** 이름 (예 '허수아비') */
  title: string;
  /** 값 한 줄 (예 '누적 120 · 8타' / '7발') — 수련장에서는 숫자를 보여 줘도 된다 */
  value: string;
  /** 팻말을 세울 자리 — 머리 위 끝 (논리 960×540 화면 좌표) */
  screen: { x: number; y: number };
}

/** P2-3 NODE_TRIAL_BROKEN 페이로드 */
export interface UiNodeTrialBroken {
  nodeId: string;
  /** hit = 첫 피격 · time = 제한 시간 넘김 */
  reason: 'hit' | 'time';
}

/** P2-6 LOADING 페이로드 */
export interface UiLoading {
  /** boot 부팅 · node 노드 진입 · boss 보스 노드 · training 수련장 · prefetch 다음 노드 미리 읽기(배경 — 막는 화면 금지) */
  phase: 'boot' | 'node' | 'boss' | 'training' | 'prefetch';
  /** 0..1 */
  progress: number;
  done: boolean;
  /** 들어갈 노드의 지역 id (waste·gate·outer·brewery·hall — 그 키아트) · node·boss 만 */
  region?: string;
  /** 단서 팁 한 줄 (스토리 63 팩 loadingTips — kind tip 지난 생의 메모 · lore 세계 한 줄). 로딩 한 번에 같은 줄 (첫 이벤트부터) */
  tip?: { kind: 'tip' | 'lore'; text: string };
}

/** P2-10 웨이브 진입 방향 (`UiEnemyIncoming.side`) — 화면 가장자리 화살표 등에 쓸 수 있다(선택) */
export type UiWaveSide = 'north' | 'south' | 'east' | 'west' | 'flank' | 'around';

// ═══ 62 루프 2 시스템 C (P16 §1~§4 — 유품 · 층 끝 결산 · 죽음 · 기억) ═══

// --- P1-5 유품 카드 ---

/** 유품이 나온 곳 — boss = 군주의 유품(층 보스 처치 1회) */
export type UiRelicSource = 'boss' | 'chest' | 'curse' | 'node' | 'shop' | 'lab' | 'event';

/**
 * 유품 카드 — 개성 카드와 같은 문법: 그림 128×128 · 조건 → 행동 한 문장(line, 들고 있는 무기 문장만 · 수치 없음) ·
 * 수치는 detail(상세 보기 D 에서만) · 태그 1개
 */
export interface UiRelic {
  id: string;
  name: string;
  line: string;
  /** 수치 설명 — 카드 앞면에 그리지 않는다(상세 보기 D) */
  detail: string;
  tag?: UiTagId;
  rarity: UiRarity;
  /**
   * 단계 — 고르기 카드는 '고르면 될 단계'(처음 1 · 지닌 것을 또 고르면 +1), 지닌 목록은 지금 단계. levelText = '{n}단계'(용어집 — 'Lv' 금지).
   * owned = 이미 지닌 유품(고르면 한 단계 깊어진다 — 카드에 relics.ui.owned 한 줄)
   */
  level: number;
  maxLevel: number;
  levelText: string;
  owned?: boolean;
  /** 상세 보기 아래 흐린 한 줄 */
  flavor?: string;
  /** `ui_relics/<id>` (아트) → 없으면 같은 태그 개성 그림 `ui_traits/<무기>_<개성>` → 없으면 생략 */
  iconKey?: string;
  source?: UiRelicSource;
}

// --- P1-6·P1-7 층 끝 · 죽음 결산 ---

/** 시간·처치·받은 피해 (플레이 시간 — 일시정지 제외, 메뉴 포함) */
export interface UiRunStats {
  timeMs: number;
  kills: number;
  damageTaken: number;
}

/** 빌드 아이콘 한 칸 (결산 아이콘 줄) — trait 개성 · relic 유품 · keepsake 기억의 소품 · aspect 무기 양상 · branch 1차 갈래 · path 2차 길 */
export interface UiBuildIcon {
  kind: 'trait' | 'relic' | 'keepsake' | 'aspect' | 'branch' | 'path';
  id: string;
  name: string;
  /** 그림 키 (로드된 것만 — 없으면 UI 는 글자) */
  iconKey?: string;
  tag?: UiTagId;
}

/** '다시 태어난다' · '일기장 덮기' (결과 화면의 두 선택 — `uiCommands.endChoice`) */
export type UiEndChoice = 'reborn' | 'closeDiary';

/** FLOOR_END 페이로드 · `UiResult.floorEnd` — '1층 끝' 결산 일기장 */
export interface UiFloorEnd extends UiRunStats {
  /** 끝낸 층 (1부터) */
  floor: number;
  /** 머리 (예 '1층 끝') */
  title: string;
  /** 층 제목 (예 "1층 · 술독 제국 '잔(盞)'") */
  floorTitle: string;
  /** 빌드 아이콘 줄 (갈래·길 → 개성 → 유품 → 소품 순) */
  build: UiBuildIcon[];
  /** 모은 단서 (이번 생에 읽은 수 / 이 층 단서 수) */
  clues: { found: number; total: number };
  /** 일기장 문장 (위 → 아래 — 제국 · 여는 말 · 단서 한 줄 · (안 맞았으면) 깨끗한 일기장 · 맺음 '다음 장은 아직 그려지지 않았다') */
  lines: string[];
  /** 칸 이름 (time 걸린 시간 · kills · damageTaken · build 지닌 것 · clues · souls) */
  labels: Record<string, string>;
  /** 칸 값 (그대로 그릴 글 — time '{m}분 {s}초' · kills · damageTaken · clues '{n} / {max}' · souls '+{n}') */
  values: Record<string, string>;
  /** 아래 한 줄 ('이 생의 영혼은 기억 장에 모였다.') */
  footer: string;
  /** 두 선택 (key → `uiCommands.endChoice(key)`) */
  choices: { key: UiEndChoice; label: string }[];
}

/** 처치자 — enemy 일반 적 · elite 엘리트 · boss 층 보스 · unknown 알 수 없음(환경 피해 등) */
export interface UiKiller {
  kind: 'enemy' | 'elite' | 'boss' | 'unknown';
  /** 적·보스 id (unknown 이면 '') */
  id: string;
  name: string;
  /** 초상 — `ui_portraits/<적 id>` · 군주 `ui_portraits/boss1`(아트 §31-5, frame 0) → 없으면 그 적 대기 시트 아래쪽 첫 칸 (로드된 것만) */
  portrait?: { key: string; frame: string | number };
}

/** 지나온 노드 한 칸 (지난 순서) — died = 쓰러진 노드 */
export interface UiPathNode {
  id: string;
  type: string;
  name: string;
  col: number;
  row: number;
  died?: boolean;
}

/** 다음 해금 — 가장 싼 아직 못 연 기억 (다 열었으면 몸의 기억 강화). left 0 = 지금 열 수 있다 */
export interface UiNextUnlock {
  id: string;
  name: string;
  cost: number;
  left: number;
}

/** `UiResult.summary` — 결산 (사망·층 끝 공통) */
export interface UiRunSummary extends UiRunStats {
  cause: 'death' | 'floorEnd';
  /** 머리 ('이 생의 기록') */
  title: string;
  /** 사망만 (층 끝이면 null) */
  killer: UiKiller | null;
  /** 처치자 한 줄 ('{killer}에게 쓰러졌다.' 등 — 층 끝이면 '') */
  killerLine: string;
  /** 쓰러진 곳 ('{floor}층 · {곳 이름}' — 사망만, 층 끝이면 '') */
  where: string;
  /** 지나온 곳 (지난 순서 — 노드 지도가 없는 생이면 []) */
  path: UiPathNode[];
  /** 사망이고 탄생지를 못 벗어났으면 '탄생지를 벗어나지 못했다.' (아니면 '') */
  pathEmpty: string;
  /** 그 순간의 노드 지도 (미니맵 — 없으면 null) */
  route: UiRoute | null;
  build: UiBuildIcon[];
  souls: { gained: number; total: number; next: UiNextUnlock | null };
  /** '영혼 +{n}' */
  soulsText: string;
  /** 다음 기억 한 줄 ('다음 기억까지 영혼 {n}' · '떠올릴 수 있는 기억이 있다.' · 처음 · 다 떠올림) */
  soulsLine: string;
  /** 칸 이름 (killer · where · path · time · kills · damageTaken · build · souls) */
  labels: Record<string, string>;
  /** 걸린 시간 글 ('{m}분 {s}초') */
  time: string;
}

/** DEATH_STARTED 페이로드 (실시간 ms) */
export interface UiDeathFx {
  /** 슬로모 길이 · 배율 (0.25 = 4배 느림) */
  slowMs: number;
  slowScale: number;
  /** 먹 번짐 길이 (슬로모 뒤) */
  inkMs: number;
  /** RUN_ENDED 까지 */
  totalMs: number;
}

// --- P1-8 메타 해금 '기억' ---

/** 기억 장 종류 — keepsake 기억의 소품 · aspect 무기 양상 · pool 개성 풀 확장 · shop 상점 품목 · stat 몸의 기억(능력치 강화 3줄) */
export type UiMemoryKind = 'keepsake' | 'aspect' | 'pool' | 'shop' | 'stat';

/** 기억 한 칸 */
export interface UiMemoryEntry {
  /** 해금 id (`uiCommands.memory.unlock(id)`) — stat 은 'stat:<강화 id>' */
  id: string;
  kind: UiMemoryKind;
  name: string;
  /** 한 문장 (수치 없음) */
  line: string;
  /** 수치 설명 (상세) */
  detail: string;
  /** 지금 열 값 (stat 은 다음 레벨 값 · 다 열렸으면 0) */
  cost: number;
  /** 열림 (stat 은 최대 레벨) */
  unlocked: boolean;
  /** 지금 열 수 있다 (영혼 충분 · 아직 안 열림) */
  affordable: boolean;
  /** aspect·pool: 무기 */
  weapon?: string;
  weaponName?: string;
  /** stat: 단계 (UI 는 '{n}단계' — relics.ui.level 꼴) */
  level?: { n: number; max: number };
  /** 칸 상태 한 줄 ('떠올렸다' · '떠올린다 · 영혼 {n}' · '영혼이 모자란다 · 영혼 {n}') */
  state: string;
  /** 상세 보기 아래 흐린 한 줄 (소품) */
  flavor?: string;
  /** 소품 = `ui_relics/keepsake_<id>`(아트 §31-4) · 모양·풀 = 그 개성 그림 `ui_traits/<무기>_<개성>` · 장터 것 = 없음 (로드된 것만) */
  iconKey?: string;
}

/** 일기장 '기억' 장 (`uiCommands.memory.book()`) */
export interface UiMemoryBook {
  title: string;
  /** 머리 문장 (위 → 아래) */
  intro: string[];
  /** '지닌 영혼 {n}' 채운 글 */
  soulsText: string;
  souls: number;
  chapters: { kind: UiMemoryKind; name: string; entries: UiMemoryEntry[] }[];
  next: UiNextUnlock | null;
  /** 다음 생에 지닐 소품 id (null = 빈손 · 열린 소품이 없으면 null) */
  keepsake: string | null;
}

/**
 * C 메뉴 id — 'aspect' 운명 공개 뒤 '손이 기억한 모양'(key 'base' 처음 모양 · 'a:<기억 id>' + `line.memory`) ·
 * 'keepsake' 지니고 태어날 소품(key 'k:<기억 id>' + `line.memory` · 'none' 빈손). 둘 다 필수 선택(cancelKey 없음).
 * 일기장 기억 장(F2)은 기존 메뉴 id 'meta' — 줄마다 `line.memory` · key 'm:<기억 id>'(몸의 기억 'm:stat:<id>') · 닫기 '0'.
 * 줄 kind 는 넣지 않는다(UiChoiceKind 를 넓히지 않음) — `line.memory` 가 있으면 기억 칸
 */
export type UiLoop2CMenuId = 'aspect' | 'keepsake';

// ═══ 62 루프 2 시스템 E (문 나가기 · 메뉴 입력 가드 — 계약 문서 §24) ═══

/** 외벽 문 방향 */
export type UiDoorSide = 'north' | 'south' | 'east' | 'west';

/**
 * 출구 문 상태 — closed 아직 닫힘(싸우는 중) · open 열림(문턱에 들어서면 나간다) · walkOut 문으로 걸어 들어가는 중(입력 잠금) ·
 * inside 문 안(지도 고르기·전환 — 주인공은 보이지 않는다) · walkIn 반대편 문에서 걸어 들어오는 중 / 지도 취소로 물러나는 중(입력 잠금)
 */
export type UiDoorPhase = 'closed' | 'open' | 'walkOut' | 'inside' | 'walkIn';

/** 출구 문 (`UiSnapshot.door`) — 노드 전투장·수련장 방에만 (그 밖은 null) */
export interface UiDoor {
  side: UiDoorSide;
  phase: UiDoorPhase;
  /** node 다음 노드 · floor 층 출구 · training 수련장 방 → 지도 */
  kind: 'node' | 'floor' | 'training';
  /** 문 가운데 (논리 화면 좌표, 화면 밖일 수 있음) */
  screen: { x: number; y: number };
}

// ═══ 62 루프 2 시스템 G (UI E·F 요청 — 계약 문서 §24) ═══

/**
 * 주인공 화면 자리 (`UiSnapshot.hero`) — 논리 960×540 화면 좌표. 머리 위 말풍선·외침·자막 꼬리·포커스 원 등 UI 연출이 따라붙을 자리.
 * head = 머리 꼭대기 · body = 그림 가운데 (발과 머리의 가운데) · feet = 발 (피벗). 도약 찍기 공중 높이를 반영한다
 */
export interface UiHeroScreen {
  head: { x: number; y: number };
  body: { x: number; y: number };
  feet: { x: number; y: number };
  /** 그림이 보이는가 (문 안·탄생 연출·사망 뒤 등 숨었으면 false — UI 는 따라붙는 연출을 숨긴다) */
  visible: boolean;
}
