import Phaser from 'phaser';
import { COLORS, DEPTH, PROTOTYPE, TILE } from '../core/Constants';
import { EventBus, Events, type PlayerDamagedPayload } from '../core/EventBus';
import { gameState } from '../core/GameState';
import { PLAYER_DATA } from '../data';
import { applyDefense } from '../systems/Combat';
import type { InputState } from '../systems/InputSystem';

type Body = Phaser.Physics.Arcade.Body;

/** 사각형 플레이스홀더 플레이어. 스프라이트는 아트 파트 산출물이 계약으로 들어올 때 교체. */
export class Player extends Phaser.GameObjects.Rectangle {
  declare body: Body;
  private invulnerableUntil = 0;
  private attackReadyAt = 0;
  private facing = new Phaser.Math.Vector2(1, 0);

  constructor(scene: Phaser.Scene, x: number, y: number) {
    const [w, h] = PLAYER_DATA.size;
    super(scene, x, y, w, h, COLORS.PLAYER);
    scene.add.existing(this);
    scene.physics.add.existing(this);
    this.setDepth(DEPTH.PLAYER);
    this.body.setCollideWorldBounds(true);
  }

  get speedPx(): number {
    return PLAYER_DATA.stats.speedTiles * TILE;
  }

  update(input: InputState, time: number): void {
    const dir = new Phaser.Math.Vector2(input.moveX, input.moveY);
    if (dir.lengthSq() > 0) {
      dir.normalize();
      this.facing.copy(dir);
    }
    this.body.setVelocity(dir.x * this.speedPx, dir.y * this.speedPx);

    if (input.attackPressed && time >= this.attackReadyAt) {
      this.attackReadyAt = time + PLAYER_DATA.attackHitbox.cooldownMs;
      const aim = new Phaser.Math.Vector2(input.aimX - this.x, input.aimY - this.y);
      if (aim.lengthSq() > 0) aim.normalize();
      else aim.copy(this.facing);
      EventBus.emit(Events.PLAYER_ATTACKED, { x: this.x, y: this.y, dirX: aim.x, dirY: aim.y });
    }
  }

  /** 적의 공격을 받는다. 무적 중이면 무시. 사망 시 true 반환 */
  takeHit(attack: number, time: number): boolean {
    if (time < this.invulnerableUntil || gameState.gameOver) return false;
    this.invulnerableUntil = time + PLAYER_DATA.invulnerableMs;
    const amount = applyDefense(attack, PLAYER_DATA.stats.defense);
    gameState.hp = Math.max(0, gameState.hp - amount);
    this.flash();
    const payload: PlayerDamagedPayload = { hp: gameState.hp, maxHp: gameState.maxHp, amount };
    EventBus.emit(Events.PLAYER_DAMAGED, payload);
    if (gameState.hp <= 0) {
      gameState.gameOver = true;
      EventBus.emit(Events.PLAYER_DIED);
      return true;
    }
    return false;
  }

  private flash(): void {
    this.setFillStyle(COLORS.PLAYER_HURT);
    this.scene.time.delayedCall(PROTOTYPE.HURT_FLASH_MS, () => {
      if (this.active) this.setFillStyle(COLORS.PLAYER);
    });
  }
}
