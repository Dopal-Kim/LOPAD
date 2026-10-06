import Phaser from 'phaser';
import { DEPTH, DROP_ART, TILE } from '../core/Constants';
import { EventBus, Events, type PickupPayload } from '../core/EventBus';
import { ECONOMY } from '../data';
import { magnetStep, voucherSize, type VoucherSize } from '../systems/drops/dropRules';
import { DropVisual } from './drop/DropVisual';

export type PickupKind = 'gold' | 'potion';

type Body = Phaser.Physics.Arcade.Body;

/** 자석 흡수 대상 (주인공) — ok(kind) 가 false 면 끌지 않는다 (물약 가득) */
export interface PickupMagnet {
  x: number;
  y: number;
  ok(kind: PickupKind): boolean;
}

/**
 * 바닥 드랍(골드·물약). 닿으면 획득, 수명이 끝나면 사라진다. 판정은 보이지 않는 작은 사각형(물리 바디),
 * 그림은 61 단계 5 (P13 §4) `DropVisual` — 전표 무더기·물약 그림(없으면 임시 동전·병), 그림자, 튀어나옴, 반짝임, 자석 흡수 늘어남, 획득 팝.
 */
export class Pickup extends Phaser.GameObjects.Rectangle {
  declare body: Body;
  kind: PickupKind = 'gold';
  value = 0;
  size: VoucherSize | null = null;
  private expireAt = 0;
  private landed = false;
  private pull = 0;
  readonly view: DropVisual;

  constructor(scene: Phaser.Scene) {
    super(scene, 0, 0, 6, 6, 0xffffff, 0);
    scene.add.existing(this);
    scene.physics.add.existing(this);
    this.setDepth(DEPTH.PICKUP);
    this.view = new DropVisual(scene);
    this.once(Phaser.GameObjects.Events.DESTROY, () => this.view.destroy());
    this.deactivate();
  }

  /** from = 떨군 자리 (튀어나오는 동안 그림이 거기서 (x, y) 로 흩뿌려진다 — 판정은 처음부터 (x, y)) */
  spawn(
    x: number,
    y: number,
    kind: PickupKind,
    value: number,
    lifeMs: number,
    time: number,
    from?: { x: number; y: number },
  ): void {
    this.kind = kind;
    this.value = value;
    this.expireAt = time + lifeMs;
    this.size = kind === 'gold' ? voucherSize(value, ECONOMY.pickup.voucherSize) : null;
    this.landed = false;
    this.pull = 0;
    const size = kind === 'gold' ? 6 : 8;
    this.setSize(size, size);
    this.body.setSize(size, size);
    this.setPosition(x, y);
    // 판정 사각형은 보이지 않는다 (그림은 view)
    this.setActive(true).setVisible(false);
    this.body.enable = true;
    this.body.reset(x, y);
    this.view.show(
      x,
      y,
      kind === 'gold' ? 'voucher' : 'potion',
      this.size,
      time,
      () => {
        this.landed = true;
        EventBus.emit(Events.PICKUP_LANDED, this.payload());
      },
      from,
    );
  }

  /** 디버그: 지금 자석 흡수 속도 (px/s, 0 = 안 끌림) */
  get pullSpeed(): number {
    return Math.round(this.pull);
  }

  payload(): PickupPayload {
    return {
      kind: this.kind === 'gold' ? 'voucher' : 'potion',
      value: this.value,
      ...(this.size ? { size: this.size } : {}),
    };
  }

  /** 매 프레임 (그림은 줍힌 뒤 팝이 끝날 때까지 돈다) · magnet = 주인공 (자석 흡수) */
  tick(time: number, delta = 0, magnet: PickupMagnet | null = null): void {
    if (!this.active) {
      this.view.update(time);
      return;
    }
    const left = this.expireAt - time;
    if (left <= 0) {
      this.deactivate();
      return;
    }
    const P = ECONOMY.pickup;
    const max = P.magnetMaxTiles * TILE;
    let vx = 0;
    let vy = 0;
    const near =
      magnet !== null &&
      this.landed &&
      magnet.ok(this.kind) &&
      Math.hypot(magnet.x - this.x, magnet.y - this.y) <= P.magnetTiles * TILE;
    if (near && magnet) {
      const M = DROP_ART.MAGNET;
      const r = magnetStep(this, magnet, this.pull > 0 ? this.pull : M.START_TILES_PER_S * TILE, delta, {
        accel: M.ACCEL_TILES_PER_S2 * TILE,
        max,
      });
      this.pull = r.speed;
      vx = r.vx;
      vy = r.vy;
    } else this.pull = 0;
    this.body.setVelocity(vx, vy);
    // 사라지기 전 깜빡임 (흡수 중이면 없음)
    const blink = left < DROP_ART.EXPIRE_BLINK_MS && vx === 0 && vy === 0;
    const alpha = blink && Math.floor(time / 120) % 2 === 1 ? 0.3 : 1;
    this.view.update(time, this.x, this.y, vx, vy, max, alpha);
  }

  /** 주웠다: 판정은 바로 끄고 그림은 팝 */
  collect(time: number): void {
    this.setActive(false);
    this.body.enable = false;
    this.body.setVelocity(0, 0);
    this.pull = 0;
    EventBus.emit(Events.PICKUP_COLLECTED, this.payload());
    this.view.pop(time);
  }

  deactivate(): void {
    this.setActive(false).setVisible(false);
    this.body.enable = false;
    this.body.setVelocity(0, 0);
    this.pull = 0;
    this.view.hide();
  }
}
