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
  SENSE_GAINED: 'sense:gained',
  PERSONALITY_GAINED: 'weapon:personality',
  WEAPON_EVOLVED: 'weapon:evolved',
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
  kind: 'attack' | 'dashAttack';
};
export type PlayerDamagedPayload = { hp: number; maxHp: number; amount: number };
export type EnemyDiedPayload = { id: string; remaining: number };
export type RoomEnteredPayload = { roomId: string; type: string };
export type TrialClearedPayload = { roomId: string; cleared: number; total: number };
export type BossPhasePayload = { phase: number; hp: number; maxHp: number };
export type WeaponEvolvedPayload = { weapon: string; stage: number; name: string };
