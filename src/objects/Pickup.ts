import Phaser from 'phaser';
import { COLORS, DEPTH } from '../core/Constants';

export type PickupKind = 'gold' | 'potion';

type Body = Phaser.Physics.Arcade.Body;

/** 바닥 드랍(골드·물약). 닿으면 획득, 수명이 끝나면 사라진다. 플레이스홀더 사각형. */
export class Pickup extends Phaser.GameObjects.Rectangle {
  declare body: Body;
  kind: PickupKind = 'gold';
  value = 0;
  private expireAt = 0;

  constructor(scene: Phaser.Scene) {
    super(scene, 0, 0, 6, 6, COLORS.GOLD);
    scene.add.existing(this);
    scene.physics.add.existing(this);
    this.setDepth(DEPTH.PICKUP);
    this.deactivate();
  }

  spawn(x: number, y: number, kind: PickupKind, value: number, lifeMs: number, time: number): void {
    this.kind = kind;
    this.value = value;
    this.expireAt = time + lifeMs;
    const size = kind === 'gold' ? 6 : 8;
    this.setSize(size, size);
    this.body.setSize(size, size);
    this.setFillStyle(kind === 'gold' ? COLORS.GOLD : COLORS.POTION);
    this.setPosition(x, y);
    this.setActive(true).setVisible(true).setAlpha(1);
    this.body.enable = true;
    this.body.reset(x, y);
  }

  tick(time: number): void {
    if (!this.active) return;
    const left = this.expireAt - time;
    if (left <= 0) this.deactivate();
    else if (left < 2000) this.setAlpha(Math.floor(time / 120) % 2 === 0 ? 1 : 0.3); // 사라지기 전 깜빡임
  }

  deactivate(): void {
    this.setActive(false).setVisible(false);
    this.body.enable = false;
  }
}
