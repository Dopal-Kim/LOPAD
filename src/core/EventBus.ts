import Phaser from 'phaser';
import type { BossPatternName } from '../data/bossPatterns';
import type { ComboFollowUpDef, HitShapeSpec } from '../data/comboTypes';

/** 씬·시스템 간 유일한 통신 경로. 직접 참조 금지. */
export const EventBus = new Phaser.Events.EventEmitter();

export const Events = {
  PLAYER_DAMAGED: 'player:damaged',
  PLAYER_HEALED: 'player:healed',
  PLAYER_DIED: 'player:died',
  PLAYER_ATTACKED: 'player:attacked',
  PLAYER_DASHED: 'player:dashed',
  PLAYER_PARRIED: 'player:parried',
  PLAYER_PARRY_FAILED: 'player:parry-failed',
  /** 가드 해제 → 주변 밀쳐내기 (대검) */
  PLAYER_GUARD_RELEASED: 'player:guard-released',
  /** 그림자 걸음 요청 (단검). Game 이 목표를 찾아 이동시킨다 */
  PLAYER_SHADOW_STEP: 'player:shadow-step',
  /** 보조 동작 국면 (음향 트리거): guard start / aimedshot start·cancel */
  PLAYER_SECONDARY: 'player:secondary',
  /**
   * 55라운드 Q22 대검 홀드 차지 국면 (`PlayerChargePayload`): start · stage(1..3, 단계마다 호박 번쩍임) · release · cancel.
   * 시스템 내부(월드 번쩍임·디버그·음향 audioMap). UI 계약 밖 — HUD 표시가 필요하면 계약 변경 인터뷰.
   * 차지가 시작된 뒤 1단 전에 떼서 일반 연격이 나가면 cancel(reason 'tap') — start 뒤엔 반드시 release 또는 cancel 이 온다
   */
  PLAYER_CHARGE: 'player:charge',
  /**
   * 55라운드 §17 후속 판정 시각 (`PlayerFollowUpPayload`): 칼 잔상 베기 · 대검 차지 3단 충격파 링. 씬 시계(히트스톱 동안 멈춤).
   * 시스템 내부(음향 audioMap — katana_echo). UI 계약 밖
   */
  PLAYER_FOLLOW_UP: 'player:follow-up',
  /**
   * 56라운드 Q7·Q8 퍼펙트 가드 (`PerfectGuardPayload`): 가드 직후 창 안 피격 — 피해 0, 튕겨내지 않음. 월드 문구 'PERFECT GUARD'·음향.
   * 시스템 내부(UI 계약 밖)
   */
  PLAYER_PERFECT_GUARD: 'player:perfect-guard',
  /**
   * 56라운드 무기 고유 자원 변화 (`WeaponGaugePayload`): 칼 검기 단 · 대검 울분 가득·소모 · 단검 낙인 · 활 숨·집중.
   * 시스템 내부(월드 연출·음향·디버그). HUD 표시는 UI 계약 변경 인터뷰가 필요하다
   */
  WEAPON_GAUGE: 'weapon:gauge',
  /** 56라운드 무기 전용 동작 국면 (`PlayerSkillPayload`): 일섬 돌진·분신·터짐 · 대검 끌림 · 낙인 폭발 — 음향 훅 */
  PLAYER_SKILL: 'player:skill',
  /** 56라운드 2단계 활 화살비 (`ArrowRainPayload`): 좌클릭 순간 — 예고 원·3발 발사·낙하점 판정은 씬(ArrowRain) */
  PLAYER_ARROW_RAIN: 'player:arrow-rain',
  /**
   * 57라운드 갈래 1단 수단 (`PlayerBranchMovePayload`): 칼 회전 베기·가드 불가 내려베기(좌클릭 홀드 0.4/0.6초 후 떼기) ·
   * 단검 부채꼴 투척(대쉬 직후 좌클릭) — 입력은 Player(BranchMoves), 판정·연출은 씬(build/BranchStrikes). 음향 훅 후보
   */
  PLAYER_BRANCH_MOVE: 'player:branch-move',
  /** 61라운드 P1: 4동사 '좌 홀드' 기술이 나갔다 (`PlayerHoldVerbPayload` — 튜토리얼 홀드 단계·런 로그) */
  PLAYER_HOLD_VERB: 'player:hold-verb',
  /** 49라운드 무기 휴대: 칼집·등에서 뽑음 / 넣음(납도) — 음향 훅 후보 (`WeaponCarryPayload`) */
  PLAYER_WEAPON_DRAWN: 'player:weapon-drawn',
  PLAYER_WEAPON_SHEATHED: 'player:weapon-sheathed',
  /** 49라운드 무기 자원 (`WeaponResourcePayload`): 기력 바닥·회복 / 장전 시작·끝 / 과열·냉각 끝 / 가열 단계 변화 */
  WEAPON_RESOURCE: 'weapon:resource',
  /** 물약 사용 (회복 일반 PLAYER_HEALED 와 구분) */
  POTION_USED: 'potion:used',
  /** 바닥 드랍 획득 (물약 등 골드 이외) */
  ITEM_PICKED: 'item:picked',
  SENSE_GAINED: 'sense:gained',
  PERSONALITY_GAINED: 'weapon:personality',
  WEAPON_EVOLVED: 'weapon:evolved',
  /** 임계 도달 → 3지선다 대기 */
  WEAPON_CHOICE_PENDING: 'weapon:choice-pending',
  /** 강화 선택 */
  WEAPON_REINFORCED: 'weapon:reinforced',
  ENEMY_DAMAGED: 'enemy:damaged',
  ENEMY_DIED: 'enemy:died',
  /** 적 공격 예고 (dash = 결사병 돌진, shot = 사수 조준 — 35라운드 2단계) */
  ENEMY_TELEGRAPH: 'enemy:telegraph',
  /** 적 공격 실행 (contact / dash / shot) */
  ENEMY_ATTACK: 'enemy:attack',
  /** 적 보조 행동 (35라운드 2단계): 사수 재장전 시작 / 결사병 방패 막기 / 징집병 집단 돌격 시작 */
  ENEMY_BEHAVIOR: 'enemy:behavior',
  ROOM_ENTERED: 'room:entered',
  TRIAL_STARTED: 'trial:started',
  TRIAL_WAVE: 'trial:wave',
  /** 53라운드 Q49: 적 소환 예고 (`EnemyIncomingPayload`) — 소환 delayMs 전에. UiRelay 가 UI_EVENTS.ENEMY_INCOMING 으로 중계 */
  ENEMY_INCOMING: 'enemy:incoming',
  TRIAL_CLEARED: 'trial:cleared',
  BOSS_UNLOCKED: 'boss:unlocked',
  BOSS_STARTED: 'boss:started',
  BOSS_PHASE: 'boss:phase',
  BOSS_DIED: 'boss:died',
  /** 보스 공격 예고 (패턴 이름 — data/bossPatterns.ts BOSS_PATTERN_NAMES) */
  BOSS_TELEGRAPH: 'boss:telegraph',
  /** 보스 공격 실행 (패턴 이름) */
  BOSS_ATTACK: 'boss:attack',
  /** 54라운드: 보스 패턴 안의 국면 (마시기·잔 깨짐·비틀 돌진 n타·넘어짐·술통·횃불·점화·촛대 — 음향 훅, `BossActionPayload`) */
  BOSS_ACTION: 'boss:action',
  /** 54라운드: 보스 패턴 루프음 켜기·끄기 (마시는 중·술통 구름·불 웅덩이 — 여러 개여도 하나, `BossLoopPayload`) */
  BOSS_LOOP: 'boss:loop',
  /** 54라운드: 화면 패턴 시작·끝 (세상이 돈다 tilt · 등불 끄기 dark, `BossScreenPayload`) */
  BOSS_SCREEN: 'boss:screen',
  /** 보스 돌진이 벽에 부딪혀 경직 (화면 흔들림·음향 훅, 35라운드) */
  BOSS_WALL_HIT: 'boss:wall-hit',
  GOLD_CHANGED: 'gold:changed',
  POTION_CHANGED: 'potion:changed',
  STAT_REWARD: 'stat:reward',
  PASSIVE_GAINED: 'passive:gained',
  SHOP_OPENED: 'shop:opened',
  SHOP_CLOSED: 'shop:closed',
  SHOP_BOUGHT: 'shop:bought',
  STAGE_STARTED: 'stage:started',
  STAGE_CLEARED: 'stage:cleared',
  STAGE_SAVED: 'stage:saved',
  /** 보스 보상 체인 끝: 출구(·상점) 타일이 열림 */
  EXIT_OPENED: 'stage:exit-opened',
  RUN_CLEARED: 'run:cleared',
  /** 결과 화면으로 넘어감 (사망·클리어 공통) */
  RUN_ENDED: 'run:ended',
  /** 엔딩 2지선다 선택 */
  ENDING_CHOSEN: 'run:ending-chosen',
  /** 개성 선택 끝: 운명(무기) 결정 */
  FATE_DECIDED: 'setup:fate-decided',
  /** 메뉴 브로커 (TextMenu): 열림·선택·닫힘 */
  MENU_OPENED: 'menu:opened',
  MENU_SELECTED: 'menu:selected',
  MENU_CLOSED: 'menu:closed',
  GAME_RESTART: 'game:restart',
  /** 47라운드 구조물 (음향 훅): 맞음 · 부서짐 · 사용 완료 · 불붙음 · 판돈 종 · 룰렛 · 도전 시작/끝 */
  STRUCTURE_HIT: 'structure:hit',
  STRUCTURE_BROKEN: 'structure:broken',
  STRUCTURE_USED: 'structure:used',
  STRUCTURE_FIRE: 'structure:fire',
  STRUCTURE_BELL: 'structure:bell',
  STRUCTURE_ROULETTE: 'structure:roulette',
  CHALLENGE_STARTED: 'challenge:started',
  CHALLENGE_CLEARED: 'challenge:cleared',
  // --- 60라운드 빌드 축 (음향 sound §6 요청 — 이름이 UI 계약 §14.11 과 겹치는 것은 그 이름. UI 는 uiBus 쪽을 듣는다) ---
  /** 세트 단계 변화 (`TagSetChangedPayload`) — UI_EVENTS.TAG_SET_CHANGED 와 같은 시점 */
  TAG_SET_CHANGED: 'build:tag-set-changed',
  /** 이중 개성 획득 (`{ id }`) */
  DUAL_TRAIT_GAINED: 'build:dual-trait-gained',
  /** 저주 받음 (`CurseGainedPayload` — source bloodPact = 개성 '피의 계약' 칸) */
  CURSE_GAINED: 'build:curse-gained',
  /** 저주 기간 끝 (`{ id }`) */
  CURSE_ENDED: 'build:curse-ended',
  /** 완벽 성공 (`PerfectSuccessPayload`) — 패링·퍼펙트 가드·완벽 놓기·완벽 회피 */
  PERFECT_SUCCESS: 'build:perfect-success',
  /** 공용 표식 변화 (`MarkChangedPayload` — 표식 태그 status_mark) */
  MARK_CHANGED: 'build:mark-changed',
  /** 상태 즉시 폭발 (`StatusBurstPayload` — 끓음 boil) */
  STATUS_BURST: 'build:status-burst',
  /** 세트 효과 발동 (`SetEffectPayload` — 간파 6 정적 stillness) */
  SET_EFFECT: 'build:set-effect',
  /** 술 웅덩이 점화 (`PoolIgnitedPayload` — 취기 술불) */
  POOL_IGNITED: 'build:pool-ignited',
  /** 취기 휘청 (취기 4 취보 — 피격 1회를 흘림) */
  DRUNK_SWAY: 'build:drunk-sway',
  /** 버팀 발동 (`EndureTriggeredPayload` — 버팀 4 위기·6 HP 0 버팀·패시브 마지막 잔) */
  ENDURE_TRIGGERED: 'build:endure-triggered',
  /** 갈래 효과 순간 (`BranchEffectPayload` — 음향 BRANCH_EFFECT{branch,effect,stack?}) */
  BRANCH_EFFECT: 'build:branch-effect',
  /** 패시브 발동 (`PassiveProcPayload` — 음향 PASSIVE_PROC{passive,fire?}, passive = 패시브 id) */
  PASSIVE_PROC: 'build:passive-proc',
  /** 상태 켜짐·꺼짐 (`StatusChangedPayload` — 불붙은 무기 fireWeapon) */
  STATUS_CHANGED: 'status:changed',
  // --- 60라운드 2차 묶음 ---
  /** 엘리트 등장 (`EliteSpawnedPayload` — scenes/game/bundle/EliteSystem) */
  ELITE_SPAWNED: 'elite:spawned',
  /** 엘리트 접두어 사건 (`ElitePrefixPayload` — 통 갑옷 break · 성난 trigger · 들이켜는 drink · 두목 death) */
  ELITE_PREFIX: 'elite:prefix',
  /** 소모품 사용 (`{ id }`) — UI_EVENTS.CONSUMABLE_USED 와 같은 시점 */
  CONSUMABLE_USED: 'consumable:used',
  /** 던진 소모품 착탄 (`{ id }`) */
  CONSUMABLE_IMPACT: 'consumable:impact',
  /** 보스 약점 파훼 성공 (`BossBreakPayload`) */
  BOSS_BREAK: 'boss:break',
  /** 노드 성과 등급 (`{ grade }`) — UI_EVENTS.NODE_GRADED 와 같은 시점 */
  NODE_GRADED: 'node:graded',
  /** 숨은 길 열림 (`{ nodeId }`) */
  HIDDEN_NODE_FOUND: 'node:hidden-found',
  /** 이벤트 노드 진입 (`{ id }` — 이벤트 내용 id) */
  EVENT_NODE_ENTERED: 'node:event-entered',
  /**
   * 61라운드 계약 sound §9: 연격 마지막 타가 적에 맞은 순간 (`ComboFinishPayload`, 활 제외 — 한 휘두름에 1회) → 음향 combo_finish.
   * 내는 곳 = 무기 연격 적중 처리(무기 쪽 에이전트 담당)
   */
  PLAYER_COMBO_FINISH: 'player:combo-finish',
  /** 61라운드 P9 런 로그: 런 시작 (`RunStartedPayload` — 새 런 · 세이브 이어하기). 시험장은 내지 않는다 */
  RUN_STARTED: 'run:started',
  /** 61라운드 P9 런 로그: 노드 지도 노드 진입 (`NodeEnteredPayload`) — UI_EVENTS.ROUTE_NODE_ENTERED 와 같은 시점 */
  NODE_ENTERED: 'node:entered',
} as const;

export type PlayerAttackPayload = {
  x: number;
  y: number;
  dirX: number;
  dirY: number;
  damageMult: number;
  sizeMult: number;
  kind: 'attack' | 'dashAttack' | 'aimed';
  /** 확정 치명타 (그림자 걸음 직후, 대쉬 공격 확정 치명) */
  forceCrit: boolean;
  /** 그림자 걸음 직후의 공격 (암살 이펙트 분기, 35라운드 3단계) */
  primed: boolean;
  /** 공격 애니 2프레임(휘두름) 시작까지 ms — 베기 이펙트 재생 시점 (시트가 없으면 0) */
  swingDelayMs: number;
  /** 공격 애니 3프레임 시작까지 ms — 활 화살 생성 시점 (시트가 없으면 0) */
  releaseDelayMs: number;
  /** 48라운드 3연격: 몇 번째 타(0부터) · 연격 타 수 · 판정 유지 ms · 애니 길이 ms (연격이 없는 무기면 없음) */
  comboIndex?: number;
  comboCount?: number;
  activeMs?: number;
  durationMs?: number;
  /** 재생한 주인공 몸 동작 (attack 또는 <무기>_combo<n>) */
  bodyAction?: string;
  /** 55라운드 Q14: 몸 동작의 실제 프레임 시작 ms (구간별 맞춤·배속 반영) — 칼끝 리본·이펙트 시각 정렬 */
  bodyFrameStartsMs?: number[];
  /** 49라운드: 대검 내리찍기 (착지 순간 = swingDelayMs, 원형 판정 반경 px, 착지점 = 그때 발 피벗 + offset) */
  slam?: { radiusPx: number; offsetX: number; offsetY: number };
  /** 49라운드: 대검 대쉬 공격 (달려들며 크게 한 번, 판정 부채꼴 각도) */
  dashSlash?: { arcDeg: number };
  /** 49라운드: 단검 가열 단계 0..3 (이펙트 강화) */
  heatStage?: number;
  /** 60라운드: 칼 검기 단 — 61라운드: 이 공격이 소모한 검기 단 (좌 홀드 발도만, 없으면 0) */
  kenkiStage?: number;
  /** 적중 넉백 배율 (61라운드: 넣은 채 첫 타 보너스 이름 firstStrike 삭제) */
  knockbackMult?: number;
  /** 55라운드 §17: 이 타의 판정 모양 (데이터 — 진화·강화·크기 배율은 받는 쪽이 R 로) · 끝점 충격원 배율(관성 최대) */
  hitShape?: HitShapeSpec;
  shapeScale?: { lengthMult?: number; impactMult?: number };
  /** 55라운드: 막타 (heavy 적중 스파크·히트스톱 ×HEAVY_MULT·흔들림·충격파 갈래). 없으면 연격 마지막 타 규칙 */
  heavy?: boolean;
  /** 55라운드 §17: 뒤따르는 판정 (칼 잔상 베기 · 차지 충격파 링) */
  followUps?: ComboFollowUpDef[];
  /** 55라운드 §17: 연격 그림 키 (`combo.art`) — 휘두름·바닥 충격 이펙트 고르기 */
  art?: string;
  /** 55라운드 Q22: 대검 차지 내려찍기 단계 (1..3) */
  charge?: number;
  /** 55라운드 Q23: 이 타에 더해진 관성 공속 비율 (0 ~ 0.2) */
  momentum?: number;
  /** 56라운드 Q5: 판정 순간 땅 균열 행 (greatsword_ground_crack s·m·l — 끝점 충격원 중심) */
  crack?: string;
  /** 56라운드 Q2 칼 일섬: 4방향 돌진 · 검기 소모 단 · 분신 (판정·선·분신은 IssenStrikes) */
  /** 칼 대쉬 일섬 (61라운드: 검기·그림자 분신 없음 — 분신 없는 선) */
  issen?: { facing: 'down' | 'up' | 'left' | 'right'; dirX: number; dirY: number };
  /**
   * 58라운드 Q3 대검 차지 균열 (CrackLineStrikes): 판정 순간 찍은 자리에서 조준 방향으로 커서까지(최대 maxTiles 칸·벽까지),
   * 앞머리가 지나간 칸만 판정. 찍은 자리 = 발 피벗 + startOffset(몸 시트 slamAnchors) — 없으면 쐐기 끝점 충격원 중심
   */
  crackLine?: {
    stage: number;
    maxTiles: number;
    cursorX: number;
    cursorY: number;
    halfWidthPx: number;
    damageMult: number;
    startOffset?: { x: number; y: number };
  };
  /** 56라운드 Q9 활 놓기 세기 (weak · perfect · full · strained) */
  bowPower?: 'weak' | 'perfect' | 'full' | 'strained';
  /** 56라운드: 화살 관통 (가득 이상). 없으면 조준 사격 = 무한 관통(기존) */
  pierce?: boolean;
  /**
   * 56라운드 2단계 새 기본기 (공격 수단 표 id — counter·iai_draw·tackle·brace_upswing·leap_slam·backstab·flurry).
   * 휘두름 소리는 PLAYER_SKILL 이 대신한다
   */
  move?: string;
  /** 단검 등 뒤 찌르기 (Q55): 공용 적중·치명 fx 를 띄우지 않는다 — 전용 섬광(휘두름 fx)만 */
  noImpactFx?: boolean;
  /**
   * 태클 (Q55): 판정이 몸과 함께 이동(공격 시작부터 fromMs~toMs, 적마다 1회) · 맞은 적을 밀고 감(carryPx) ·
   * 첫 접촉 fx(몸을 따라감) · (groundFx = 옛 '막다가 떼면 돌진' 바닥 fx — 61라운드 삭제, 남은 필드)
   */
  rush?: {
    /** 돌진 구간 (공격 시작부터) · 거리 — 밀고 가는 거리 = 남은 돌진 + carryExtraPx */
    dashFromMs: number;
    dashToMs: number;
    dashPx: number;
    carryExtraPx: number;
    contactFx?: string;
    groundFx?: string;
  };
  /** 도약 찍기 (Q55): 차지 단계 · 착지 발밑 링(반지름·피해 배율) · 나선 fx(도약 출발 고정, 벽에 막히면 null) */
  leap?: {
    stage: number;
    ringRadiusPx: number;
    ringDamageMult: number;
    spiralFx: string | null;
    startX: number;
    startY: number;
  };
};
/** 56라운드 Q7 퍼펙트 가드 */
export type PerfectGuardPayload = { x: number; y: number; attack: number; dirX?: number; dirY?: number };
/** 패링 성공 (56라운드: 주인공 → 공격자 방향 — 패링 fx 회전) */
export type PlayerParriedPayload = { attack: number; dirX?: number; dirY?: number };
/** 56라운드 무기 고유 자원 */
export type WeaponGaugePayload = {
  weapon: string;
  gauge: 'kenki' | 'grudge' | 'brand' | 'breath';
  /** stage = 검기 단 변화 · full = 울분·숨 가득 · consume = 소모 · apply = 낙인 표식 · focusStart/focusEnd = 숨 집중 */
  event: 'stage' | 'full' | 'consume' | 'apply' | 'focusStart' | 'focusEnd';
  stage?: number;
  /** 증가량(낙인 표식 수 증가 등) */
  delta?: number;
  /** 낙인: 대상의 표식 수 · 등 뒤 */
  marks?: number;
  back?: boolean;
};
/** 61라운드 P1: 좌 홀드 기술 (move = 공격 수단 표 id — iai_draw·spin·unblockable·charge_swing·flurry·arrow_rain·rapid_volley) */
export type PlayerHoldVerbPayload = { weapon: string; move: string };
/** 56라운드 무기 전용 동작 국면 (음향 매니페스트 PLAYER_SKILL move·phase) */
export type PlayerSkillPayload = {
  weapon: string;
  move:
    | 'issen'
    | 'drag'
    | 'brand'
    | 'overheat'
    // 56라운드 2단계 새 기본기 (음향 매니페스트 trigger.when 의 move 값)
    | 'counter'
    | 'iai'
    | 'tackle'
    | 'brace_upswing'
    | 'leap'
    | 'backstab'
    | 'flurry'
    | 'arrow_rain'
    // 60라운드 갈래 1단 수단 판정 순간 (음향 sound §6 — 씬 build/branch 가 낸다)
    | 'spin'
    | 'guardbreak'
    | 'crack'
    | 'fan_throw'
    | 'cross_clone'
    | 'pierce'
    | 'whirl';
  phase:
    | 'dash'
    | 'clone'
    | 'burst'
    | 'recover'
    | 'crack'
    | 'start'
    | 'hold'
    | 'release'
    | 'cancel'
    | 'takeoff'
    | 'land'
    | 'launch'
    | 'impact'
    | 'stab'
    | 'ready'
    | 'end'
    | 'strike'
    | 'snuff'
    | 'pass'
    | 'reflect'
    | 'cleave';
  /** 60라운드: 같은 동작의 몇 번째 재생 (회전 베기 2회전 = 2 — 음향 rate) */
  variant?: number;
  /** 60라운드: 판정 프레임까지 ms (가드 불가 내려베기 — 음향은 판정 100ms 앞) */
  impactDelayMs?: number;
  /** 울분 소모 강화판 (버티기 올려베기) */
  rage?: boolean;
  /** 도약 찍기 착지: 유지한 차지 단계 (1 이상이면 차지 내려찍기 소리 겹침) */
  stage?: number;
  /** 대치 일격 준비 반짝임 자리 (칼집 입구 — 월드) */
  at?: { x: number; y: number };
};
/** 56라운드 2단계 활 화살비: 원 중심·반지름·시트 행 · 발사 시각(좌클릭부터) · 낙하 · 피해 배율 */
export type ArrowRainPayload = {
  x: number;
  y: number;
  radiusPx: number;
  markRow: string;
  facing: 'down' | 'up' | 'left' | 'right';
  releasesAtMs: number[];
  /** 몸 시트 releaseFrames (무기 arrowSpawnAnchors 열 — 없으면 []) */
  releaseFrames: number[];
  drops: number;
  dropIntervalMs: number;
  firstDropAtMs: number;
  dropRadiusPx: number;
  damageMult: number;
  riseFx: string;
  markFx: string;
  fallFx: string;
};
/** 55라운드 Q22 대검 홀드 차지 국면 */
export type PlayerChargePayload = {
  phase: 'start' | 'stage' | 'release' | 'cancel';
  stage: number;
  /** release: 차지 내려찍기 판정(impact) 프레임까지 ms — 타격음은 이 시각에 */
  impactDelayMs?: number;
  /** cancel: 피격(hurt) · 1단 전에 떼서 일반 연격(tap) · 그 밖(대쉬·가드·F·워프·무기 교체 — 없음) */
  reason?: 'hurt' | 'tap';
};
/** 55라운드 §17 후속 판정 (데이터 `followUps[].id` — 칼 echo · 대검 ring) */
export type PlayerFollowUpPayload = { weapon: string; id: string; art?: string };
/** 49라운드: 무기 휴대 뽑기·넣기 */
export type WeaponCarryPayload = { weapon: string; mode: 'sheath' | 'back' | 'hand' };
/** 49라운드: 무기 자원 변화 */
export type WeaponResourcePayload = {
  weapon: string;
  kind: 'stamina' | 'ammo' | 'heat';
  /** 56라운드: groggy = 기력 0 그로기 시작(칼·대검, 끝은 recovered) */
  event: 'exhausted' | 'recovered' | 'reloadStart' | 'reloadDone' | 'overheat' | 'cooled' | 'heatStage' | 'groggy';
  /** heatStage 일 때 새 단계 */
  stage?: number;
};
export type PlayerSecondaryPayload = {
  kind: 'parry' | 'guard' | 'shadowstep' | 'aimedshot';
  /**
   * ready = 조준 사격 차지 완료(유지 중, 떼면 발사 — 31라운드 2). block = 가드로 피격을 받아냄(47라운드 룰렛 규칙).
   * 56라운드 Q9: release = 활 놓기(power = 약한·완벽·가득·흔들림) — 일찍 떼도 약한 1발이 나간다(취소 없음).
   * strain = 너무 오래 쥐어 흔들리기 시작(Q20 — 음향 bow_strain 루프)
   */
  phase: 'start' | 'ready' | 'cancel' | 'block' | 'release' | 'strain';
  power?: 'weak' | 'perfect' | 'full' | 'strained';
};
/** 60라운드: elite = 엘리트였음 (음향 elite_die) */
export type EnemyDiedPayload = { id: string; elite?: boolean };
export type EnemyDamagedPayload = { id: string; amount: number; crit: boolean; died: boolean; tick: boolean };
export type EnemyAttackPayload = { id: string; kind: 'contact' | 'dash' | 'shot' };
export type EnemyTelegraphPayload = { id: string; kind: 'dash' | 'shot' };
/** 35라운드 2단계: reload = 사수 재장전 시작, block = 결사병 방패로 막음, pack = 징집병 집단 돌격 시작 */
export type EnemyBehaviorPayload = { id: string; kind: 'reload' | 'block' | 'pack' };
/** 보스 패턴 이름 (54라운드: 단일 출처 data/bossPatterns.ts) */
export type BossPattern = BossPatternName;
export type BossAttackPayload = { id: string; attack: BossPattern };
export type BossTelegraphPayload = { id: string; attack: BossPattern };
/** 54라운드 보스 패턴 국면 (음향 매니페스트 트리거 대응표는 parts/system/CHANGELOG.md 54라운드 절) */
export type BossActionKind =
  | 'drinkLift'
  | 'drinkFinish'
  | 'cupBreak'
  | 'reelTelegraph'
  | 'reelDash'
  | 'fall'
  | 'rise'
  | 'kick'
  | 'caskBounce'
  | 'caskBreak'
  | 'caskRedirect'
  | 'spill'
  | 'torchThrow'
  | 'ignite'
  | 'bossIgnite'
  | 'candleTopple'
  | 'candleRelight'
  | 'phaseDrink';
/** index = 3연 취권 몇 번째 타(0부터) */
export type BossActionPayload = { id: string; action: BossActionKind; index?: number };
export type BossLoopKind = 'gulp' | 'roll' | 'fire';
export type BossLoopPayload = { loop: BossLoopKind; on: boolean };
export type BossScreenPayload = { effect: 'tilt' | 'dark'; on: boolean };
export type BossWallHitPayload = { id: string; x: number; y: number };
export type MenuEventPayload = { id: string; reopen?: boolean; key?: string; selected?: boolean };
export type RunEndedPayload = { cleared: boolean };
export type ComboFinishPayload = { weapon: string };
/** 61라운드 P9: continued = 세이브 이어하기 (그 전 노드 기록은 없음) */
export type RunStartedPayload = { seed: string; weapon: string; stageIndex: number; continued: boolean };
/** 61라운드 P9: kind = 노드 종류(birth·road·post·battle·shop·rest·event·boss …), type = 계약 UiNodeType */
export type NodeEnteredPayload = { id: string; kind: string; type: string; name: string; stageIndex: number };
/** 56라운드 2단계: quiet = 밀쳐내기 없이 끝 (퍼펙트 가드 직후 돌진 · 가드 중 반격·올려베기 — 밀쳐내기·그 소리 없음) */
export type GuardReleasedPayload = { x: number; y: number; quiet?: boolean };
export type ShadowStepPayload = { x: number; y: number; facingX: number; facingY: number };
/** 35라운드: `source` = 가해자 → 플레이어 방향 단위벡터(넉백·연출용, 계약 UI 페이로드에는 없음) */
export type PlayerDamagedPayload = {
  hp: number;
  maxHp: number;
  amount: number;
  source?: { dirX: number; dirY: number };
  /** 56라운드 2단계: 슈퍼아머(버티기 올려베기)로 받음 — 동작이 끊기지 않음, 흡수 fx */
  armored?: boolean;
  /** 61라운드 계약 sound §9: 가드로 막고 남은 피해 — 음향 guard_block (hit_player 대신). 내는 곳 = PlayerDefense(무기 쪽) */
  guarded?: boolean;
};
export type RoomEnteredPayload = { roomId: string; type: string };
export type TrialClearedPayload = { roomId: string; cleared: number; total: number };
export type BossPhasePayload = { phase: number; hp: number; maxHp: number };
/** 60라운드: kind = 갈래(branch, 기본) / 최종 각성(awaken — 음향 awaken_<무기>) */
export type WeaponEvolvedPayload = { weapon: string; stage: number; name: string; kind?: 'branch' | 'awaken' };
export type WeaponReinforcedPayload = { weapon: string; reinforce: number; name: string };
/** 47라운드 구조물 이벤트 (내부, 음향 훅). kind = 계약 UiStructureKind */
export type StructureEventPayload = { id: string; kind: string; roomId: string; actionKey?: string };
export type StructureFirePayload = { target: 'weapon' | 'arrow' | 'pool' | 'burn' };
export type StructureBellPayload = { id: string; confirmed: boolean; rings: number };
export type ChallengeEventPayload = {
  id: string;
  /** 60라운드: warFlag = 도전 성소 깃발 */
  kind: 'dogRing' | 'cardTable' | 'warFlag';
  outcome?: 'clear' | 'flawless' | 'timeout' | 'fail';
};

/** 53라운드 Q49: 적 소환 예고 (방 · 소환까지 ms · 마리 수) */
export interface EnemyIncomingPayload {
  roomId: string;
  delayMs: number;
  count?: number;
}

/**
 * 57라운드 갈래 1단 수단 국면: hold = 홀드 자세 시작(60라운드 — 음향 홀드 루프) · ready = 홀드 완료(번쩍임) · release = 뗌·발동 ·
 * sustain = 회오리 지속 회전 틱 · end = 끝 · cancel = 홀드가 발동 없이 끝남(짧게 뗌·대쉬·가드 — 60라운드)
 */
export type PlayerBranchMovePayload = {
  weapon: string;
  move: 'spin' | 'unblockable' | 'fanThrow';
  phase: 'hold' | 'ready' | 'release' | 'sustain' | 'end' | 'cancel';
  x: number;
  y: number;
  dirX: number;
  dirY: number;
};

// --- 60라운드 빌드 축 이벤트 페이로드 (음향 트리거 조건 키 — sound §6) ---
export type TagSetChangedPayload = { tag: string; stage: number; prev: number; delta: number };
export type CurseGainedPayload = {
  id: string;
  /** bloodPact = 개성 '피의 계약' 칸 · riskNode = 위험 노드 저주 길 · event · structure · 그 밖 */
  source: 'bloodPact' | 'riskNode' | 'event' | 'structure' | 'other';
};
export type PerfectSuccessPayload = { kind: 'parry' | 'perfectGuard' | 'perfectRelease' | 'perfectEvade' };
export type MarkChangedPayload = { marks: number; delta: number };
export type StatusBurstPayload = { kind: 'boil'; x: number; y: number };
export type SetEffectPayload = { tag: string; effect: 'stillness' };
export type PoolIgnitedPayload = { x: number; y: number };
export type EndureTriggeredPayload = { source: 'crisis' | 'lastStand' | 'lastCup' };
export type BranchEffectPayload = { branch: string; effect: string; stack?: number };
export type PassiveProcPayload = { passive: string; fire?: boolean };
export type StatusChangedPayload = { id: 'fireWeapon'; phase: 'start' | 'end' };
/** 회복 (60라운드: source — 독주 'potion' 만 음향 potion_use) */
export type PlayerHealedPayload = {
  hp: number;
  maxHp: number;
  amount: number;
  source?: 'potion' | 'rest' | 'shop' | 'event';
};
export type BossBreakPayload = { kind: string; distinct: boolean; count: number };
/** 60라운드 엘리트 (scenes/game/bundle/EliteSystem): prefix = 접두어 id (data/bundle2.json elite.prefixes) */
export type EliteSpawnedPayload = { id: string; prefix: string };
export type ElitePrefixPayload = { prefix: string; phase: 'break' | 'trigger' | 'drink' | 'death'; count?: number };
export type ConsumablePayload = { id: string };
export type NodeGradedPayload = { grade: 'perfect' | 'good' | null };
