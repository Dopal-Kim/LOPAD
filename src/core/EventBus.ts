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
  /** 51라운드 Q4: 넣은 채 첫 타 보너스 이름 (발도·끌어내기) · 적중 넉백 배율 */
  firstStrike?: string;
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
  event: 'exhausted' | 'recovered' | 'reloadStart' | 'reloadDone' | 'overheat' | 'cooled' | 'heatStage';
  /** heatStage 일 때 새 단계 */
  stage?: number;
};
export type PlayerSecondaryPayload = {
  kind: 'parry' | 'guard' | 'shadowstep' | 'aimedshot';
  /** ready = 조준 사격 차지 완료(유지 중, 떼면 발사 — 31라운드 2). block = 가드로 피격을 받아냄(47라운드 룰렛 규칙) */
  phase: 'start' | 'ready' | 'cancel' | 'block';
};
export type EnemyDamagedPayload = { id: string; amount: number; crit: boolean; died: boolean; tick: boolean };
export type EnemyAttackPayload = { id: string; kind: 'contact' | 'dash' | 'shot' };
export type EnemyTelegraphPayload = { id: string; kind: 'dash' | 'shot' };
/** 35라운드 2단계: reload = 사수 재장전 시작, block = 결사병 방패로 막음, pack = 징집병 집단 돌격 시작 */
export type EnemyBehaviorPayload = { id: string; kind: 'reload' | 'block' | 'pack' };
/** 보스 패턴 이름 (54라운드: 단일 출처 data/bossPatterns.ts) */
export type BossPattern = BossPatternName;
export type BossAttackPayload = { id: string; attack: BossPattern };
export type BossTelegraphPayload = { id: string; attack: BossPattern };
/** 54라운드 보스 패턴 국면 (음향 매니페스트 트리거 대응표는 parts/system/README.md 54라운드 절) */
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
export type GuardReleasedPayload = { x: number; y: number };
export type ShadowStepPayload = { x: number; y: number; facingX: number; facingY: number };
/** 35라운드: `source` = 가해자 → 플레이어 방향 단위벡터(넉백·연출용, 계약 UI 페이로드에는 없음) */
export type PlayerDamagedPayload = {
  hp: number;
  maxHp: number;
  amount: number;
  source?: { dirX: number; dirY: number };
};
export type EnemyDiedPayload = { id: string; remaining: number };
export type RoomEnteredPayload = { roomId: string; type: string };
export type TrialClearedPayload = { roomId: string; cleared: number; total: number };
export type BossPhasePayload = { phase: number; hp: number; maxHp: number };
export type WeaponEvolvedPayload = { weapon: string; stage: number; name: string };
export type WeaponReinforcedPayload = { weapon: string; reinforce: number; name: string };
/** 47라운드 구조물 이벤트 (내부, 음향 훅). kind = 계약 UiStructureKind */
export type StructureEventPayload = { id: string; kind: string; roomId: string; actionKey?: string };
export type StructureFirePayload = { target: 'weapon' | 'arrow' | 'pool' | 'burn' };
export type StructureBellPayload = { id: string; confirmed: boolean; rings: number };
export type ChallengeEventPayload = {
  id: string;
  kind: 'dogRing' | 'cardTable';
  outcome?: 'clear' | 'flawless' | 'timeout';
};

/** 53라운드 Q49: 적 소환 예고 (방 · 소환까지 ms · 마리 수) */
export interface EnemyIncomingPayload {
  roomId: string;
  delayMs: number;
  count?: number;
}
