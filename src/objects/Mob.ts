import Phaser from 'phaser';
import { COLORS, PROTOTYPE } from '../core/Constants';
import { EventBus, Events, type EnemyAttackPayload, type EnemyDamagedPayload } from '../core/EventBus';
import { facingOf } from '../systems/spriteDefs';
import { EntityVisual, placeholderTexture } from './EntityVisual';

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

/** 피해의 성격: 치명 여부, 지속 피해 틱(출혈·잔월)인지 — 효과음 분기용 */
export interface DamageInfo {
  crit?: boolean;
  tick?: boolean;
}

/** 전투 개체 공통부. 시트(`<id>_*`)가 있으면 애니메이션 스프라이트, 없으면 단색 사각형. */
export abstract class Mob extends Phaser.GameObjects.Sprite {
  declare body: Body;
  hp: number;
  readonly maxHp: number;
  readonly visual: EntityVisual;
  /** 적·보스 id (= 시트 이름). 이벤트 페이로드에 쓴다 */
  readonly spriteId: string;
  /** 마지막으로 본 플레이어 위치 (대기 방향용) */
  private targetX = 0;
  private targetY = 0;
  protected nextContactAt = 0;
  protected stunnedUntil = 0;
  /** 경직의 출처: 패링 경직 처치만 '패링 처치'로 센다 */
  private stunSource: 'parry' | 'hit' = 'parry';
  /** 밀쳐내기 중 (AI 가 속도를 덮어쓰지 않는다) */
  private knockedUntil = 0;

  constructor(
    scene: Phaser.Scene,
    x: number,
    y: number,
    /** 시트 이름 = 적·보스 id (계약 §1) */
    spriteName: string,
    size: [number, number],
    color: string,
    hp: number,
  ) {
    super(scene, x, y, placeholderTexture(scene, size[0], size[1]));
    this.spriteId = spriteName;
    this.hp = hp;
    this.maxHp = hp;
    scene.add.existing(this);
    scene.physics.add.existing(this);
    this.visual = new EntityVisual(
      this,
      spriteName,
      size[0],
      size[1],
      Phaser.Display.Color.HexStringToColor(color).color,
    );
    this.targetX = x;
    this.targetY = y;
  }

  protected preUpdate(time: number, delta: number): void {
    super.preUpdate(time, delta);
    this.visual.sync();
  }

  /** 행동(think) 뒤 속도·플레이어 위치로 idle/walk 와 방향을 정한다 */
  update(ctx: MobContext): void {
    if (!this.active) return;
    this.targetX = ctx.player.x;
    this.targetY = ctx.player.y;
    this.think(ctx);
    const v = this.body.velocity;
    const moving = v.lengthSq() > 1;
    const dir = moving
      ? facingOf(v.x, v.y, this.visual.facing)
      : facingOf(this.targetX - this.x, this.targetY - this.y, this.visual.facing);
    this.visual.loop(moving ? 'walk' : 'idle', dir, ctx.time);
  }

  /** 행동 결정 (하위 클래스) */
  protected abstract think(ctx: MobContext): void;

  /** 공격 동작 애니 (시트가 없으면 무시). fitMs 가 있으면 그 시간에 맞춘다 */
  protected playAttack(time: number, fitMs?: number): void {
    const dir = facingOf(this.targetX - this.x, this.targetY - this.y, this.visual.facing);
    this.visual.oneShot('attack', dir, time, fitMs);
  }

  /** 처치 시 플레이어 무기에 쌓이는 개성 수치 */
  abstract get personalityValue(): number;

  /** 처치 시 떨어지는 골드 기준값 */
  abstract get goldValue(): number;

  /** 지금 플레이어와 접촉 중일 때의 공격력 (상태에 따라 다름) */
  protected abstract currentContactAttack(): number;

  protected abstract contactIntervalMs(): number;

  isStunned(time: number): boolean {
    return time < this.stunnedUntil;
  }

  /** 패링 경직으로 멈춰 있는지 (감각 '패링 처치' 분류용) */
  isParryStunned(time: number): boolean {
    return this.isStunned(time) && this.stunSource === 'parry';
  }

  isKnockedBack(time: number): boolean {
    return time < this.knockedUntil;
  }

  /** 밀쳐내기: ms 동안 속도를 유지하고 AI 를 멈춘다 (가드 해제) */
  knockback(time: number, dirX: number, dirY: number, speedPx: number, ms: number): void {
    this.knockedUntil = Math.max(this.knockedUntil, time + ms);
    this.body.setVelocity(dirX * speedPx, dirY * speedPx);
  }

  /** 패링·중압 등으로 경직. 경직 중엔 움직이지도 공격하지도 않는다 */
  stun(time: number, ms: number, source: 'parry' | 'hit' = 'parry'): void {
    if (!this.isStunned(time) || source === 'parry') this.stunSource = source;
    this.stunnedUntil = Math.max(this.stunnedUntil, time + ms);
    this.body.setVelocity(0, 0);
    this.visual.paint(COLORS.STUN);
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
    // 프레임 유지 중(보스 돌진·예고)에는 접촉 공격 애니로 덮지 않는다
    if (!this.visual.held) this.playAttack(time);
    EventBus.emit(Events.ENEMY_ATTACK, { id: this.spriteId, kind: 'contact' } satisfies EnemyAttackPayload);
    return this.currentContactAttack();
  }

  /** 데미지를 받는다. 사망하면 true. `info` 는 효과음 분기(치명·틱) */
  takeDamage(amount: number, info: DamageInfo = {}): boolean {
    if (!this.active) return false;
    this.hp -= amount;
    const died = this.hp <= 0;
    const payload: EnemyDamagedPayload = {
      id: this.spriteId,
      amount,
      crit: Boolean(info.crit),
      died,
      tick: Boolean(info.tick),
    };
    EventBus.emit(Events.ENEMY_DAMAGED, payload);
    if (died) {
      this.onDeath();
      this.visual.spawnCorpse();
      this.destroy();
      return true;
    }
    this.flash(COLORS.MOB_HURT);
    // 보스가 국면 프레임을 유지 중이면 피격 애니 대신 번쩍임만
    if (!this.visual.held) this.visual.oneShot('hurt', this.visual.facing, this.scene.time.now);
    return false;
  }

  protected onDeath(): void {}

  /** 외부 효과(출혈 등)의 짧은 색 표시 */
  flashColor(color: number): void {
    this.flash(color);
  }

  protected flash(color: number, ms = PROTOTYPE.HURT_FLASH_MS): void {
    this.visual.flash(color);
    this.scene.time.delayedCall(ms, () => {
      if (this.active) this.restoreColor();
    });
  }

  /** 상태 색 (예고 등). 플레이스홀더는 채움색, 시트는 곱 틴트 */
  protected paint(color: number): void {
    this.visual.paint(color);
  }

  protected restoreColor(): void {
    if (this.isStunned(this.scene.time.now)) this.visual.paint(COLORS.STUN);
    else this.visual.restore();
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
