import Phaser from 'phaser';
import { COLORS, PROTOTYPE, TILE } from '../core/Constants';
import {
  EventBus,
  Events,
  type GuardReleasedPayload,
  type PlayerAttackPayload,
  type PlayerDamagedPayload,
  type PlayerSecondaryPayload,
  type ShadowStepPayload,
} from '../core/EventBus';
import { gameState } from '../core/GameState';
import { PLAYER_DATA } from '../data';
import type { SecondaryDef } from '../data/types';
import { applyDefense } from '../systems/Combat';
import type { InputState } from '../systems/InputSystem';
import { facingOf, type Facing } from '../systems/spriteDefs';
import { EntityVisual, placeholderTexture } from './EntityVisual';
import { WeaponOverlay } from './WeaponOverlay';

type Body = Phaser.Physics.Arcade.Body;

/** guard = 대검 가드(유지), aim = 활 조준 사격 차지(유지) */
export type PlayerAction = 'normal' | 'dash' | 'parry' | 'recover' | 'guard' | 'aim';
export type HitResult = 'hit' | 'dead' | 'parried' | 'ignored';

/** 주인공. 시트(`player_*`)가 있으면 애니메이션 스프라이트, 없으면 단색 사각형 플레이스홀더. */
export class Player extends Phaser.GameObjects.Sprite {
  declare body: Body;
  action: PlayerAction = 'normal';
  readonly visual: EntityVisual;
  /** 손에 든 무기 오버레이 (계약 §3.1). 공격 애니 중에만 보인다 */
  readonly overlay: WeaponOverlay;
  /** 사망 애니 길이 (시트가 없으면 0) — Game 이 결과 화면 전환을 이만큼 늦춘다 */
  deathAnimMs = 0;
  /** 이번 프레임 이동 입력이 있었는지 (질풍 루프 이펙트용) */
  moving = false;
  private actionUntil = 0;
  private invulnerableUntil = 0;
  private attackReadyAt = 0;
  private dashReadyAt = 0;
  private dashEndedAt = -Infinity;
  /** 공격 판정 중(둔중한 무기일수록 길다) 이동 감속 */
  private attackSlowUntil = 0;
  /** 보조 동작(그림자 걸음·조준 사격) 쿨 */
  private secondaryReadyAt = 0;
  /** 조준 사격 차지 시작 */
  private aimStartedAt = 0;
  /** 그림자 걸음 직후: 이 시간까지의 다음 공격 1회가 확정 치명(+암살 배율) */
  private shadowPrimedUntil = -Infinity;
  private facing = new Phaser.Math.Vector2(1, 0);
  private dashVel = new Phaser.Math.Vector2();

  constructor(scene: Phaser.Scene, x: number, y: number) {
    const [w, h] = PLAYER_DATA.size;
    super(scene, x, y, placeholderTexture(scene, w, h));
    scene.add.existing(this);
    scene.physics.add.existing(this);
    this.visual = new EntityVisual(this, 'player', w, h, COLORS.PLAYER);
    this.overlay = new WeaponOverlay(this);
    this.body.setCollideWorldBounds(true);
  }

  protected preUpdate(time: number, delta: number): void {
    super.preUpdate(time, delta);
    this.visual.sync();
    this.overlay.update();
  }

  /** 현재 애니 방향 (디버그) */
  get facingDir(): Facing {
    return this.visual.facing;
  }

  get animKey(): string | null {
    return this.visual.current;
  }

  get speedPx(): number {
    const weaponMult = gameState.weapon.mods.moveSpeedMult ?? 1;
    return PLAYER_DATA.stats.speedTiles * TILE * (1 + gameState.passives.total('moveSpeedMult')) * weaponMult;
  }

  get isParrying(): boolean {
    return this.action === 'parry';
  }

  get isGuarding(): boolean {
    return this.action === 'guard';
  }

  /** 그림자 걸음으로 다음 공격이 확정 치명인 상태 */
  isShadowPrimed(time: number): boolean {
    return time < this.shadowPrimedUntil;
  }

  get secondary(): SecondaryDef {
    return gameState.weapon.def.secondary;
  }

  /** 조준 차지 진행도 0..1 (조준 중이 아니면 0) */
  aimProgress(time: number): number {
    const S = this.secondary;
    if (this.action !== 'aim' || S.kind !== 'aimedshot') return 0;
    return Phaser.Math.Clamp((time - this.aimStartedAt) / S.chargeMs, 0, 1);
  }

  update(input: InputState, time: number): void {
    const D = PLAYER_DATA.dash;
    const P = PLAYER_DATA.parry;
    const S = this.secondary;
    const mods = gameState.weapon.mods;

    // 진행 중인 동작 종료 처리
    if (this.action !== 'normal' && this.actionUntil > 0 && time >= this.actionUntil) {
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

    // 유지형 보조 동작: 가드(떼면 밀쳐내기) · 조준(차지 완료 시 발사, 먼저 떼면 취소)
    if (this.action === 'guard' && !input.secondaryHeld) {
      this.setAction('normal', 0);
      const payload: GuardReleasedPayload = { x: this.x, y: this.y };
      EventBus.emit(Events.PLAYER_GUARD_RELEASED, payload);
    }
    if (this.action === 'aim') {
      if (!input.secondaryHeld) {
        this.setAction('normal', 0);
        EventBus.emit(Events.PLAYER_SECONDARY, { kind: 'aimedshot', phase: 'cancel' } satisfies PlayerSecondaryPayload);
      } else if (S.kind === 'aimedshot' && time - this.aimStartedAt >= S.chargeMs) {
        this.setAction('normal', 0);
        this.secondaryReadyAt = time + S.cooldownMs;
        this.emitAttack(input, time, 'aimed', S.damageMult * (mods.aimedShotMult ?? 1), 1, false);
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
      let slow = time < this.attackSlowUntil ? gameState.weapon.attackSlowMult : 1;
      if (this.action === 'guard' && S.kind === 'guard') slow = Math.min(slow, S.moveMult);
      if (this.action === 'aim' && S.kind === 'aimedshot') slow = Math.min(slow, S.moveMult);
      this.body.setVelocity(dir.x * this.speedPx * slow, dir.y * this.speedPx * slow);
    }
    this.animateLocomotion(input, dir, time);

    const canAct = this.action === 'normal';

    // 대쉬
    if (input.dashPressed && canAct && time >= this.dashReadyAt) {
      const d = dir.lengthSq() > 0 ? dir : this.facing;
      const speed = (D.distanceTiles * TILE) / (D.durationMs / 1000);
      this.dashVel.set(d.x * speed, d.y * speed);
      this.dashReadyAt =
        time +
        D.cooldownMs *
          gameState.meta.dashCooldownMult *
          (1 + gameState.passives.total('dashCooldownMult')) *
          (mods.dashCooldownMult ?? 1);
      if (D.invulnerable) {
        this.invulnerableUntil = Math.max(this.invulnerableUntil, time + D.durationMs + (mods.dashInvulnExtraMs ?? 0));
      }
      this.setAction('dash', time + D.durationMs);
      this.visual.oneShot('dash', facingOf(d.x, d.y, this.visual.facing), time, D.durationMs);
      EventBus.emit(Events.PLAYER_DASHED, { dirX: d.x, dirY: d.y, x: this.x, y: this.y });
      return;
    }

    // 보조 동작 (우클릭): 무기별
    if (input.secondaryPressed && canAct) {
      switch (S.kind) {
        case 'parry':
          this.setAction('parry', time + P.windowMs * (1 + gameState.passives.total('parryWindowMult')));
          return;
        case 'guard':
          this.setAction('guard', 0);
          EventBus.emit(Events.PLAYER_SECONDARY, { kind: 'guard', phase: 'start' } satisfies PlayerSecondaryPayload);
          return;
        case 'aimedshot':
          if (time >= this.secondaryReadyAt) {
            this.aimStartedAt = time;
            this.setAction('aim', 0);
            EventBus.emit(Events.PLAYER_SECONDARY, {
              kind: 'aimedshot',
              phase: 'start',
            } satisfies PlayerSecondaryPayload);
          }
          return;
        case 'shadowstep':
          if (time >= this.secondaryReadyAt) {
            this.secondaryReadyAt = time + S.cooldownMs;
            this.shadowPrimedUntil = time + S.primeMs;
            const payload: ShadowStepPayload = { x: this.x, y: this.y, facingX: this.facing.x, facingY: this.facing.y };
            EventBus.emit(Events.PLAYER_SHADOW_STEP, payload);
          }
          return;
      }
    }

    // 공격 (대쉬 직후면 대쉬 공격)
    if (input.attackPressed && canAct && time >= this.attackReadyAt) {
      this.attackReadyAt = time + gameState.weapon.hitbox.cooldownMs;
      this.attackSlowUntil = time + Math.max(gameState.weapon.hitbox.activeMs, PLAYER_DATA.attackSlowMinMs);
      const isDashAttack = time - this.dashEndedAt <= D.attackWindowMs;
      let mult = 1;
      let forceCrit = false;
      if (isDashAttack) {
        mult = D.attackDamageMult * (1 + gameState.passives.total('dashAttackMult')) * (mods.dashAttackMult ?? 1);
        forceCrit = Boolean(mods.dashAttackForceCrit);
        this.dashEndedAt = -Infinity; // 대쉬 공격은 1회
      }
      if (this.isShadowPrimed(time)) {
        mult *= mods.shadowStepMult ?? 1;
        forceCrit = true;
        this.shadowPrimedUntil = -Infinity; // 1회
      }
      this.emitAttack(
        input,
        time,
        isDashAttack ? 'dashAttack' : 'attack',
        mult,
        isDashAttack ? D.attackSizeMult : 1,
        forceCrit,
      );
    }
  }

  /** 이동 중엔 이동 방향, 멈춰 있으면 마우스 조준 방향으로 idle/walk */
  private animateLocomotion(input: InputState, dir: Phaser.Math.Vector2, time: number): void {
    const moving = dir.lengthSq() > 0 && this.action !== 'dash';
    this.moving = moving;
    const facing = moving
      ? facingOf(dir.x, dir.y, this.visual.facing)
      : facingOf(input.aimX - this.x, input.aimY - this.y, this.visual.facing);
    this.visual.loop(moving ? 'walk' : 'idle', facing, time);
  }

  private emitAttack(
    input: InputState,
    time: number,
    kind: PlayerAttackPayload['kind'],
    damageMult: number,
    sizeMult: number,
    forceCrit: boolean,
  ): void {
    const aim = new Phaser.Math.Vector2(input.aimX - this.x, input.aimY - this.y);
    if (aim.lengthSq() > 0) aim.normalize();
    else aim.copy(this.facing);
    // 공격 애니는 조준 방향으로, 다음 공격 가능 시점(쿨다운)에 맞춰 재생
    this.visual.oneShot('attack', facingOf(aim.x, aim.y, this.visual.facing), time, gameState.weapon.hitbox.cooldownMs);
    const payload: PlayerAttackPayload = {
      x: this.x,
      y: this.y,
      dirX: aim.x,
      dirY: aim.y,
      damageMult,
      sizeMult,
      kind,
      forceCrit,
      swingDelayMs: this.visual.lastImpactMs,
      releaseDelayMs: this.visual.frameStartMs(2),
    };
    EventBus.emit(Events.PLAYER_ATTACKED, payload);
  }

  /** 그림자 걸음 등으로 순간이동 (Game 이 목적지를 정한다) */
  teleportTo(x: number, y: number): void {
    this.body.reset(x, y);
    this.flash(COLORS.PLAYER_SHADOW);
  }

  heal(amount: number): void {
    const before = gameState.hp;
    gameState.hp = Math.min(gameState.maxHp, gameState.hp + amount);
    EventBus.emit(Events.PLAYER_HEALED, { hp: gameState.hp, maxHp: gameState.maxHp, amount: gameState.hp - before });
  }

  /**
   * 적의 공격을 받는다. 패링 창이면 'parried'(피해 0), 무적이면 'ignored'.
   * 가드 중이면 피해 감소, 공격 중 슈퍼아머(거인)면 추가 감소. 사망하면 'dead'.
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
    let amount = applyDefense(attack, gameState.defense);
    const S = this.secondary;
    const mods = gameState.weapon.mods;
    if (this.action === 'guard' && S.kind === 'guard') {
      amount = Math.round(amount * (1 - (mods.guardReduction ?? S.damageReduction)));
    }
    if (mods.superArmorReduction && time < this.attackSlowUntil) {
      amount = Math.round(amount * (1 - mods.superArmorReduction));
    }
    gameState.hp = Math.max(0, gameState.hp - amount);
    this.flash(COLORS.PLAYER_HURT);
    const payload: PlayerDamagedPayload = { hp: gameState.hp, maxHp: gameState.maxHp, amount };
    EventBus.emit(Events.PLAYER_DAMAGED, payload);
    if (gameState.hp <= 0) {
      gameState.gameOver = true;
      this.setAction('normal', 0);
      this.deathAnimMs = this.visual.oneShot('death', this.visual.facing, time);
      EventBus.emit(Events.PLAYER_DIED);
      return 'dead';
    }
    this.visual.oneShot('hurt', this.visual.facing, time);
    return 'hit';
  }

  private setAction(a: PlayerAction, until: number): void {
    this.action = a;
    this.actionUntil = until;
    this.applyStateColor();
  }

  /** 상태 표시: 플레이스홀더는 채움색, 시트는 틴트(대쉬는 애니가 있으므로 원색) */
  private applyStateColor(): void {
    switch (this.action) {
      case 'dash':
        if (this.visual.animated) this.visual.restore();
        else this.visual.paint(COLORS.PLAYER_DASH);
        break;
      case 'parry':
        this.visual.paint(COLORS.PLAYER_PARRY);
        break;
      case 'guard':
        this.visual.paint(COLORS.PLAYER_GUARD);
        break;
      case 'aim':
        this.visual.paint(COLORS.PLAYER_AIM);
        break;
      case 'recover':
        this.visual.paint(COLORS.PLAYER_RECOVER);
        break;
      default:
        this.visual.restore();
    }
  }

  private flash(color: number): void {
    this.visual.flash(color);
    this.scene.time.delayedCall(PROTOTYPE.HURT_FLASH_MS, () => {
      if (this.active) this.applyStateColor();
    });
  }
}
