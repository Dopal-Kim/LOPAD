import Phaser from 'phaser';
import { COLORS, DEPTH, PROTOTYPE, TILE } from '../core/Constants';
import { EventBus, Events } from '../core/EventBus';
import { ENEMIES } from '../data';
import type { EnemyDef } from '../data/types';

type Body = Phaser.Physics.Arcade.Body;

/** 사각형 플레이스홀더 적. 행동은 data/enemies.json 의 behavior 로 결정. */
export class Enemy extends Phaser.GameObjects.Rectangle {
  declare body: Body;
  readonly def: EnemyDef;
  readonly id: string;
  private hp: number;
  private nextAttackAt = 0;
  private baseColor: number;

  constructor(scene: Phaser.Scene, x: number, y: number, id: string) {
    const def = ENEMIES[id];
    if (!def) throw new Error(`[enemy] 정의 없음: ${id}`);
    const [w, h] = def.size;
    const color = Phaser.Display.Color.HexStringToColor(def.color).color;
    super(scene, x, y, w, h, color);
    this.def = def;
    this.id = id;
    this.hp = def.hp;
    this.baseColor = color;
    scene.add.existing(this);
    scene.physics.add.existing(this);
    this.setDepth(DEPTH.ENEMY);
    this.body.setCollideWorldBounds(true);
  }

  update(target: Phaser.Math.Vector2): void {
    if (!this.active) return;
    if (this.def.behavior === 'chase') {
      const dir = new Phaser.Math.Vector2(target.x - this.x, target.y - this.y);
      if (dir.lengthSq() > 1) {
        dir.normalize().scale(this.def.speedTiles * TILE);
        this.body.setVelocity(dir.x, dir.y);
      } else {
        this.body.setVelocity(0, 0);
      }
    }
  }

  /** 플레이어와 접촉 중일 때 공격 가능하면 공격력을 반환, 아니면 0 */
  tryAttack(time: number): number {
    if (time < this.nextAttackAt) return 0;
    this.nextAttackAt = time + this.def.attackIntervalMs;
    return this.def.attack;
  }

  /** 데미지를 받는다. 사망하면 true */
  takeDamage(amount: number): boolean {
    if (!this.active) return false;
    this.hp -= amount;
    EventBus.emit(Events.ENEMY_DAMAGED, { id: this.id, hp: this.hp, amount });
    if (this.hp <= 0) {
      this.destroy();
      return true;
    }
    this.setFillStyle(COLORS.ENEMY_HURT);
    this.scene.time.delayedCall(PROTOTYPE.HURT_FLASH_MS, () => {
      if (this.active) this.setFillStyle(this.baseColor);
    });
    return false;
  }
}
