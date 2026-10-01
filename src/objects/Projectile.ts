import Phaser from 'phaser';
import { COLORS, DEPTH } from '../core/Constants';
import type { ProjectileSpec } from './Mob';

type Body = Phaser.Physics.Arcade.Body;
export type ProjectileOwner = 'enemy' | 'player';

/** 투사체. 벽에 닿거나 수명이 끝나면 비활성화되어 풀로 돌아간다. */
export class Projectile extends Phaser.GameObjects.Rectangle {
  declare body: Body;
  attack = 0;
  owner: ProjectileOwner = 'enemy';
  /** 패링으로 반사됨: 플레이어 대신 적을 맞힌다 */
  reflected = false;
  /** 남은 관통 횟수 (플레이어 투사체). Infinity = 무한 관통 */
  pierceLeft = 0;
  /** 유도 선회 속도 (rad/s). 0 이면 유도 없음 */
  homingTurn = 0;
  /** 적중 시 적 경직 ms (조준 사격 중시) */
  hitStunMs = 0;
  /** 같은 적을 두 번 맞히지 않기 위한 기록 */
  private hitSet = new Set<unknown>();
  private expireAt = 0;

  constructor(scene: Phaser.Scene) {
    super(scene, 0, 0, 4, 4, COLORS.PROJECTILE);
    scene.add.existing(this);
    scene.physics.add.existing(this);
    this.setDepth(DEPTH.PROJECTILE);
    this.deactivate();
  }

  launch(
    x: number,
    y: number,
    dirX: number,
    dirY: number,
    spec: ProjectileSpec,
    time: number,
    owner: ProjectileOwner = 'enemy',
    pierce = 0,
  ): void {
    this.attack = spec.attack;
    this.owner = owner;
    this.reflected = false;
    this.pierceLeft = pierce;
    this.homingTurn = 0;
    this.hitStunMs = 0;
    this.hitSet.clear();
    this.setFillStyle(owner === 'player' ? COLORS.PLAYER_SHOT : COLORS.PROJECTILE);
    this.expireAt = time + spec.lifeMs;
    this.setSize(spec.size, spec.size);
    this.body.setSize(spec.size, spec.size);
    this.setPosition(x, y);
    this.setActive(true).setVisible(true);
    this.body.enable = true;
    this.body.reset(x, y);
    this.body.setVelocity(dirX * spec.speedPx, dirY * spec.speedPx);
  }

  /** 적에게 맞았을 때 호출. 이미 맞힌 적이면 false. 관통이 남으면 계속 날아간다 */
  registerHit(target: unknown): boolean {
    if (this.hitSet.has(target)) return false;
    this.hitSet.add(target);
    if (this.pierceLeft > 0) this.pierceLeft -= 1;
    else this.deactivate();
    return true;
  }

  /** 유도: 목표 방향으로 속도 벡터를 최대 homingTurn × dt 만큼 돌린다 */
  steerToward(x: number, y: number, deltaMs: number): void {
    if (this.homingTurn <= 0) return;
    const v = this.body.velocity;
    const speed = v.length();
    if (speed <= 0) return;
    const want = Math.atan2(y - this.y, x - this.x);
    const cur = Math.atan2(v.y, v.x);
    const next = Phaser.Math.Angle.RotateTo(cur, want, this.homingTurn * (deltaMs / 1000));
    this.body.setVelocity(Math.cos(next) * speed, Math.sin(next) * speed);
  }

  reflect(mult: number): void {
    this.reflected = true;
    this.attack = Math.round(this.attack * mult);
    this.body.setVelocity(-this.body.velocity.x, -this.body.velocity.y);
    this.setFillStyle(COLORS.PROJECTILE_REFLECTED);
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
