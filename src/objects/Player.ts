import Phaser from 'phaser';
import { COLORS, DEPTH, PROTOTYPE, TILE } from '../core/Constants';
import { EventBus, Events, type PlayerAttackPayload, type PlayerDamagedPayload } from '../core/EventBus';
import { gameState } from '../core/GameState';
import { PLAYER_DATA } from '../data';
import { applyDefense } from '../systems/Combat';
import type { InputState } from '../systems/InputSystem';

type Body = Phaser.Physics.Arcade.Body;

export type PlayerAction = 'normal' | 'dash' | 'parry' | 'recover';
export type HitResult = 'hit' | 'dead' | 'parried' | 'ignored';

/** 사각형 플레이스홀더 플레이어. 스프라이트는 아트 파트 산출물이 계약으로 들어올 때 교체. */
export class Player extends Phaser.GameObjects.Rectangle {
  declare body: Body;
  action: PlayerAction = 'normal';
  private actionUntil = 0;
  private invulnerableUntil = 0;
  private attackReadyAt = 0;
  private dashReadyAt = 0;
  private dashEndedAt = -Infinity;
  private facing = new Phaser.Math.Vector2(1, 0);
  private dashVel = new Phaser.Math.Vector2();

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

  get isParrying(): boolean {
    return this.action === 'parry';
  }

  update(input: InputState, time: number): void {
    const D = PLAYER_DATA.dash;
    const P = PLAYER_DATA.parry;

    // 진행 중인 동작 종료 처리
    if (this.action !== 'normal' && time >= this.actionUntil) {
      if (this.action === 'dash') {
        this.dashEndedAt = time;
        this.body.setVelocity(0, 0);
        this.setAction('normal', 0);
      } else if (this.action === 'parry') {
        // 창이 닫혔는데 아무것도 못 막음 → 후딜
        EventBus.emit(Events.PLAYER_PARRY_FAILED);
        this.setAction('recover', time + P.failRecoveryMs);
      } else {
        this.setAction('normal', 0);
      }
    }

    // 이동 (대쉬 중엔 대쉬 속도 유지)
    const dir = new Phaser.Math.Vector2(input.moveX, input.moveY);
    if (dir.lengthSq() > 0) {
      dir.normalize();
      this.facing.copy(dir);
    }
    if (this.action === 'dash') {
      this.body.setVelocity(this.dashVel.x, this.dashVel.y);
    } else {
      this.body.setVelocity(dir.x * this.speedPx, dir.y * this.speedPx);
    }

    const canAct = this.action === 'normal';

    // 대쉬
    if (input.dashPressed && canAct && time >= this.dashReadyAt) {
      const d = dir.lengthSq() > 0 ? dir : this.facing;
      const speed = (D.distanceTiles * TILE) / (D.durationMs / 1000);
      this.dashVel.set(d.x * speed, d.y * speed);
      this.dashReadyAt = time + D.cooldownMs;
      if (D.invulnerable) this.invulnerableUntil = Math.max(this.invulnerableUntil, time + D.durationMs);
      this.setAction('dash', time + D.durationMs);
      EventBus.emit(Events.PLAYER_DASHED, { dirX: d.x, dirY: d.y });
      return;
    }

    // 패링
    if (input.parryPressed && canAct) {
      this.setAction('parry', time + P.windowMs);
      return;
    }

    // 공격 (대쉬 직후면 대쉬 공격)
    if (input.attackPressed && canAct && time >= this.attackReadyAt) {
      this.attackReadyAt = time + gameState.weapon.hitbox.cooldownMs;
      const aim = new Phaser.Math.Vector2(input.aimX - this.x, input.aimY - this.y);
      if (aim.lengthSq() > 0) aim.normalize();
      else aim.copy(this.facing);
      const isDashAttack = time - this.dashEndedAt <= D.attackWindowMs;
      const payload: PlayerAttackPayload = {
        x: this.x,
        y: this.y,
        dirX: aim.x,
        dirY: aim.y,
        damageMult: isDashAttack ? D.attackDamageMult : 1,
        sizeMult: isDashAttack ? D.attackSizeMult : 1,
        kind: isDashAttack ? 'dashAttack' : 'attack',
      };
      if (isDashAttack) this.dashEndedAt = -Infinity; // 대쉬 공격은 1회
      EventBus.emit(Events.PLAYER_ATTACKED, payload);
    }
  }

  heal(amount: number): void {
    const before = gameState.hp;
    gameState.hp = Math.min(gameState.maxHp, gameState.hp + amount);
    EventBus.emit(Events.PLAYER_HEALED, { hp: gameState.hp, maxHp: gameState.maxHp, amount: gameState.hp - before });
  }

  /**
   * 적의 공격을 받는다. 패링 창이면 'parried'(피해 0), 무적이면 'ignored'.
   * 사망하면 'dead'.
   */
  takeHit(attack: number, time: number): HitResult {
    if (gameState.gameOver) return 'ignored';
    if (this.action === 'parry') {
      // 성공: 창을 닫고 즉시 행동 가능
      this.setAction('normal', 0);
      this.flash(COLORS.PLAYER_PARRY);
      EventBus.emit(Events.PLAYER_PARRIED, { attack });
      return 'parried';
    }
    if (time < this.invulnerableUntil) return 'ignored';
    this.invulnerableUntil = time + PLAYER_DATA.invulnerableMs;
    const amount = applyDefense(attack, PLAYER_DATA.stats.defense);
    gameState.hp = Math.max(0, gameState.hp - amount);
    this.flash(COLORS.PLAYER_HURT);
    const payload: PlayerDamagedPayload = { hp: gameState.hp, maxHp: gameState.maxHp, amount };
    EventBus.emit(Events.PLAYER_DAMAGED, payload);
    if (gameState.hp <= 0) {
      gameState.gameOver = true;
      EventBus.emit(Events.PLAYER_DIED);
      return 'dead';
    }
    return 'hit';
  }

  private setAction(a: PlayerAction, until: number): void {
    this.action = a;
    this.actionUntil = until;
    switch (a) {
      case 'dash':
        this.setFillStyle(COLORS.PLAYER_DASH);
        this.setStrokeStyle(0);
        break;
      case 'parry':
        this.setFillStyle(COLORS.PLAYER);
        this.setStrokeStyle(2, COLORS.PLAYER_PARRY);
        break;
      case 'recover':
        this.setFillStyle(COLORS.PLAYER_RECOVER);
        this.setStrokeStyle(0);
        break;
      default:
        this.setFillStyle(COLORS.PLAYER);
        this.setStrokeStyle(0);
    }
  }

  private flash(color: number): void {
    this.setFillStyle(color);
    this.scene.time.delayedCall(PROTOTYPE.HURT_FLASH_MS, () => {
      if (this.active && this.action === 'normal') this.setFillStyle(COLORS.PLAYER);
    });
  }
}
