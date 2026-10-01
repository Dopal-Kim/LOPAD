import Phaser from 'phaser';
import { COLORS, DEPTH } from '../core/Constants';
import type { ProjectileSpec } from './Mob';

type Body = Phaser.Physics.Arcade.Body;

/** 적 투사체. 벽에 닿거나 수명이 끝나면 비활성화되어 풀로 돌아간다. */
export class Projectile extends Phaser.GameObjects.Rectangle {
  declare body: Body;
  attack = 0;
  private expireAt = 0;

  constructor(scene: Phaser.Scene) {
    super(scene, 0, 0, 4, 4, COLORS.PROJECTILE);
    scene.add.existing(this);
    scene.physics.add.existing(this);
    this.setDepth(DEPTH.PROJECTILE);
    this.deactivate();
  }

  launch(x: number, y: number, dirX: number, dirY: number, spec: ProjectileSpec, time: number): void {
    this.attack = spec.attack;
    this.expireAt = time + spec.lifeMs;
    this.setSize(spec.size, spec.size);
    this.body.setSize(spec.size, spec.size);
    this.setPosition(x, y);
    this.setActive(true).setVisible(true);
    this.body.enable = true;
    this.body.reset(x, y);
    this.body.setVelocity(dirX * spec.speedPx, dirY * spec.speedPx);
  }

  tick(time: number): void {
    if (!this.active) return;
    if (time >= this.expireAt || !this.body.blocked.none) this.deactivate();
  }

  deactivate(): void {
    this.setActive(false).setVisible(false);
    this.body.enable = false;
    this.body.setVelocity(0, 0);
  }
}
