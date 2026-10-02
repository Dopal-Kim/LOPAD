import Phaser from 'phaser';

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
  /** 결사병 돌진 예고 */
  ENEMY_TELEGRAPH: 'enemy:telegraph',
  /** 적 공격 실행 (contact / dash / shot) */
  ENEMY_ATTACK: 'enemy:attack',
  ROOM_ENTERED: 'room:entered',
  TRIAL_STARTED: 'trial:started',
  TRIAL_WAVE: 'trial:wave',
  TRIAL_CLEARED: 'trial:cleared',
  BOSS_UNLOCKED: 'boss:unlocked',
  BOSS_STARTED: 'boss:started',
  BOSS_PHASE: 'boss:phase',
  BOSS_DIED: 'boss:died',
  /** 보스 돌진 예고 */
  BOSS_TELEGRAPH: 'boss:telegraph',
  /** 보스 공격 실행 (dash / fan) */
  BOSS_ATTACK: 'boss:attack',
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
  /** 공격 애니 2프레임(휘두름) 시작까지 ms — 베기 이펙트 재생 시점 (시트가 없으면 0) */
  swingDelayMs: number;
  /** 공격 애니 3프레임 시작까지 ms — 활 화살 생성 시점 (시트가 없으면 0) */
  releaseDelayMs: number;
};
export type PlayerSecondaryPayload = {
  kind: 'parry' | 'guard' | 'shadowstep' | 'aimedshot';
  /** ready = 조준 사격 차지 완료(유지 중, 떼면 발사 — 31라운드 2) */
  phase: 'start' | 'ready' | 'cancel';
};
export type EnemyDamagedPayload = { id: string; amount: number; crit: boolean; died: boolean; tick: boolean };
export type EnemyAttackPayload = { id: string; kind: 'contact' | 'dash' | 'shot' };
export type EnemyTelegraphPayload = { id: string; kind: 'dash' };
export type BossAttackPayload = { id: string; attack: 'dash' | 'fan' };
export type BossTelegraphPayload = { id: string; attack: 'dash' };
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
