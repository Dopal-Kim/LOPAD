import Phaser from 'phaser';
import { COLORS, TILE } from '../core/Constants';
import { EventBus, Events } from '../core/EventBus';
import { ENEMIES } from '../data';
import type { EnemyDef, EnemyScale } from '../data/types';
import { Mob, type MobContext } from './Mob';

type ChargeState = 'approach' | 'telegraph' | 'dash' | 'cooldown';

/** 일반 적. 행동은 data/enemies.json 의 behavior 로 결정. */
export class Enemy extends Mob {
  readonly def: EnemyDef;
  readonly id: string;
  private nextShotAt = 0;
  private chargeState: ChargeState = 'approach';
  private chargeUntil = 0;
  private dashDir = new Phaser.Math.Vector2(1, 0);

  private readonly stageScale: EnemyScale;

  constructor(scene: Phaser.Scene, x: number, y: number, id: string, scale: EnemyScale = { hp: 1, attack: 1 }) {
    const def = ENEMIES[id];
    if (!def) throw new Error(`[enemy] 정의 없음: ${id}`);
    super(scene, x, y, def.size, def.color, Math.round(def.hp * scale.hp));
    this.def = def;
    this.id = id;
    this.stageScale = scale;
  }

  /** 스테이지 배율이 적용된 공격력 */
  private atk(base: number): number {
    return Math.round(base * this.stageScale.attack);
  }

  update(ctx: MobContext): void {
    if (!this.active) return;
    if (this.isKnockedBack(ctx.time)) return;
    if (this.isStunned(ctx.time)) {
      this.body.setVelocity(0, 0);
      return;
    }
    switch (this.def.behavior) {
      case 'chase':
        this.moveToward(ctx.player.x, ctx.player.y, this.def.speedTiles * TILE);
        break;
      case 'ranged':
        this.updateRanged(ctx);
        break;
      case 'charge':
        this.updateCharge(ctx);
        break;
    }
  }

  get personalityValue(): number {
    return this.def.personalityValue;
  }

  get goldValue(): number {
    return this.def.gold;
  }

  protected currentContactAttack(): number {
    if (this.def.behavior === 'charge' && this.def.charge) {
      return this.atk(this.chargeState === 'dash' ? this.def.charge.dashAttack : this.def.charge.idleAttack);
    }
    return this.atk(this.def.attack);
  }

  protected contactIntervalMs(): number {
    return this.def.attackIntervalMs;
  }

  protected onDeath(): void {
    EventBus.emit(Events.ENEMY_DIED, { id: this.id });
  }

  protected onStunned(): void {
    if (this.def.behavior === 'charge') this.chargeState = 'approach';
  }

  private updateRanged(ctx: MobContext): void {
    const R = this.def.ranged!;
    const dist = Phaser.Math.Distance.Between(this.x, this.y, ctx.player.x, ctx.player.y);
    const speed = this.def.speedTiles * TILE;
    if (dist < R.keepMinTiles * TILE) {
      // 멀어진다
      const away = new Phaser.Math.Vector2(this.x - ctx.player.x, this.y - ctx.player.y).normalize().scale(speed);
      this.body.setVelocity(away.x, away.y);
    } else if (dist > R.keepMaxTiles * TILE) {
      this.moveToward(ctx.player.x, ctx.player.y, speed);
    } else {
      this.body.setVelocity(0, 0);
    }
    if (ctx.time >= this.nextShotAt && dist <= R.keepMaxTiles * TILE * 1.5) {
      this.nextShotAt = ctx.time + this.def.attackIntervalMs;
      const dir = new Phaser.Math.Vector2(ctx.player.x - this.x, ctx.player.y - this.y).normalize();
      ctx.fire(this.x, this.y, dir.x, dir.y, {
        speedPx: R.projectileSpeedTiles * TILE,
        attack: this.atk(this.def.attack),
        size: R.projectileSize,
        lifeMs: R.projectileLifeMs,
      });
    }
  }

  private updateCharge(ctx: MobContext): void {
    const C = this.def.charge!;
    const dist = Phaser.Math.Distance.Between(this.x, this.y, ctx.player.x, ctx.player.y);
    switch (this.chargeState) {
      case 'approach':
        this.moveToward(ctx.player.x, ctx.player.y, this.def.speedTiles * TILE);
        if (dist <= C.triggerTiles * TILE) {
          this.chargeState = 'telegraph';
          this.chargeUntil = ctx.time + C.telegraphMs;
          this.body.setVelocity(0, 0);
          this.setFillStyle(COLORS.TELEGRAPH);
        }
        break;
      case 'telegraph':
        if (ctx.time >= this.chargeUntil) {
          this.dashDir.set(ctx.player.x - this.x, ctx.player.y - this.y).normalize();
          this.chargeState = 'dash';
          this.chargeUntil = ctx.time + C.dashMs;
          this.restoreColor();
        }
        break;
      case 'dash':
        this.body.setVelocity(this.dashDir.x * C.dashSpeedTiles * TILE, this.dashDir.y * C.dashSpeedTiles * TILE);
        if (ctx.time >= this.chargeUntil || this.body.blocked.none === false) {
          this.chargeState = 'cooldown';
          this.chargeUntil = ctx.time + C.cooldownMs;
          this.body.setVelocity(0, 0);
        }
        break;
      case 'cooldown':
        this.body.setVelocity(0, 0);
        if (ctx.time >= this.chargeUntil) this.chargeState = 'approach';
        break;
    }
  }
}
