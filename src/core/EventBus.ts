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
  SENSE_GAINED: 'sense:gained',
  PERSONALITY_GAINED: 'weapon:personality',
  WEAPON_EVOLVED: 'weapon:evolved',
  /** 임계 도달 → 3지선다 대기 */
  WEAPON_CHOICE_PENDING: 'weapon:choice-pending',
  /** 강화 선택 */
  WEAPON_REINFORCED: 'weapon:reinforced',
  ENEMY_DAMAGED: 'enemy:damaged',
  ENEMY_DIED: 'enemy:died',
  ROOM_ENTERED: 'room:entered',
  TRIAL_STARTED: 'trial:started',
  TRIAL_WAVE: 'trial:wave',
  TRIAL_CLEARED: 'trial:cleared',
  BOSS_UNLOCKED: 'boss:unlocked',
  BOSS_STARTED: 'boss:started',
  BOSS_PHASE: 'boss:phase',
  BOSS_DIED: 'boss:died',
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
  RUN_CLEARED: 'run:cleared',
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
};
export type GuardReleasedPayload = { x: number; y: number };
export type ShadowStepPayload = { x: number; y: number; facingX: number; facingY: number };
export type PlayerDamagedPayload = { hp: number; maxHp: number; amount: number };
export type EnemyDiedPayload = { id: string; remaining: number };
export type RoomEnteredPayload = { roomId: string; type: string };
export type TrialClearedPayload = { roomId: string; cleared: number; total: number };
export type BossPhasePayload = { phase: number; hp: number; maxHp: number };
export type WeaponEvolvedPayload = { weapon: string; stage: number; name: string };
export type WeaponReinforcedPayload = { weapon: string; reinforce: number; name: string };
