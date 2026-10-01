import Phaser from 'phaser';

/** 씬·시스템 간 유일한 통신 경로. 직접 참조 금지. */
export const EventBus = new Phaser.Events.EventEmitter();

export const Events = {
  PLAYER_DAMAGED: 'player:damaged',
  PLAYER_DIED: 'player:died',
  PLAYER_ATTACKED: 'player:attacked',
  ENEMY_DAMAGED: 'enemy:damaged',
  ENEMY_DIED: 'enemy:died',
  RUN_CLEARED: 'run:cleared',
  GAME_RESTART: 'game:restart',
} as const;

export type PlayerDamagedPayload = { hp: number; maxHp: number; amount: number };
export type EnemyDiedPayload = { id: string; remaining: number };
