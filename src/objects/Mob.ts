import Phaser from 'phaser';
import { COLORS, DEPTH, PROTOTYPE } from '../core/Constants';

type Body = Phaser.Physics.Arcade.Body;

/** 적·보스가 update 때 받는 컨텍스트. 씬 참조 대신 필요한 것만 넘긴다. */
export interface MobContext {
  time: number;
  delta: number;
  player: { x: number; y: number };
  /** 투사체 발사 (월드 좌표, 방향 단위벡터) */
  fire: (x: number, y: number, dirX: number, dirY: number, spec: ProjectileSpec) => void;
}

export interface ProjectileSpec {
  speedPx: number;
  attack: number;
  size: number;
  lifeMs: number;
}

/** 사각형 플레이스홀더 전투 개체의 공통부. 스프라이트는 아트 파트 산출물이 계약으로 들어올 때 교체. */
export abstract class Mob extends Phaser.GameObjects.Rectangle {
  declare body: Body;
  hp: number;
  readonly maxHp: number;
  protected baseColor: number;
  protected nextContactAt = 0;
  protected stunnedUntil = 0;

  constructor(scene: Phaser.Scene, x: number, y: number, size: [number, number], color: string, hp: number) {
    const c = Phaser.Display.Color.HexStringToColor(color).color;
    super(scene, x, y, size[0], size[1], c);
    this.baseColor = c;
    this.hp = hp;
    this.maxHp = hp;
    scene.add.existing(this);
    scene.physics.add.existing(this);
    this.setDepth(DEPTH.ENEMY);
  }

  abstract update(ctx: MobContext): void;

  /** 지금 플레이어와 접촉 중일 때의 공격력 (상태에 따라 다름) */
  protected abstract currentContactAttack(): number;

  protected abstract contactIntervalMs(): number;

  isStunned(time: number): boolean {
    return time < this.stunnedUntil;
  }

  /** 패링 등으로 경직. 경직 중엔 움직이지도 공격하지도 않는다 */
  stun(time: number, ms: number): void {
    this.stunnedUntil = Math.max(this.stunnedUntil, time + ms);
    this.body.setVelocity(0, 0);
    this.setFillStyle(COLORS.STUN);
    this.onStunned();
    this.scene.time.delayedCall(ms, () => {
      if (this.active && !this.isStunned(this.scene.time.now)) this.restoreColor();
    });
  }

  protected onStunned(): void {}

  /** 플레이어와 접촉 중일 때 호출. 공격 가능하면 공격력, 아니면 0 */
  tryContactAttack(time: number): number {
    if (this.isStunned(time)) return 0;
    if (time < this.nextContactAt) return 0;
    this.nextContactAt = time + this.contactIntervalMs();
    return this.currentContactAttack();
  }

  /** 데미지를 받는다. 사망하면 true */
  takeDamage(amount: number): boolean {
    if (!this.active) return false;
    this.hp -= amount;
    if (this.hp <= 0) {
      this.onDeath();
      this.destroy();
      return true;
    }
    this.flash(COLORS.MOB_HURT);
    return false;
  }

  protected onDeath(): void {}

  protected flash(color: number, ms = PROTOTYPE.HURT_FLASH_MS): void {
    this.setFillStyle(color);
    this.scene.time.delayedCall(ms, () => {
      if (this.active) this.restoreColor();
    });
  }

  protected restoreColor(): void {
    this.setFillStyle(this.baseColor);
  }

  protected moveToward(x: number, y: number, speedPx: number): void {
    const dir = new Phaser.Math.Vector2(x - this.x, y - this.y);
    if (dir.lengthSq() > 1) {
      dir.normalize().scale(speedPx);
      this.body.setVelocity(dir.x, dir.y);
    } else {
      this.body.setVelocity(0, 0);
    }
  }
}
