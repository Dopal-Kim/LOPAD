import Phaser from 'phaser';
import { COLORS, FEEDBACK, PROTOTYPE } from '../core/Constants';
import { EventBus, Events, type EnemyAttackPayload, type EnemyDamagedPayload } from '../core/EventBus';
import { facingOf, type Facing } from '../systems/sprites/spriteDefs';
import { knockFactor, knockSpeed } from '../systems/feel';
import type { PackCharge } from '../systems/packCharge';
import type { TelegraphFx } from '../systems/telegraph';
import type { BossArenaApi } from './boss/types';
import type { EnemyHazardApi } from '../systems/hazards/enemyHazardTypes';
import { EntityVisual, placeholderTexture } from './EntityVisual';
import { LIGHTING } from '../data';
import { lightRegistryOf } from '../systems/lighting/lightRegistry';

type Body = Phaser.Physics.Arcade.Body;

/** 적·보스가 update 때 받는 컨텍스트. 씬 참조 대신 필요한 것만 넘긴다. */
export interface MobContext {
  time: number;
  delta: number;
  player: { x: number; y: number };
  /** 투사체 발사 (월드 좌표, 방향 단위벡터) */
  fire: (x: number, y: number, dirX: number, dirY: number, spec: ProjectileSpec) => void;
  /** 공격 예고 마커 (35라운드 2단계) */
  telegraph: TelegraphFx;
  /** 시트 이펙트 1회 재생 (총구 화염 등). 시트가 없으면 무시 */
  playFx: (id: string, x: number, y: number, opts: { dir?: Facing; depth?: number; angle?: number }) => void;
  /** 같은 id 의 살아 있는 적 수 (집단 돌격 머릿수·소환 상한) */
  countMobs: (id: string) => number;
  /** 범위 피해 + 충격파 연출 (보스 내리찍기): 중심·반경 안의 플레이어에게 attack */
  areaHit: (x: number, y: number, radiusPx: number, attack: number) => void;
  /** 소환: 현재 방에 적을 추가한다 (방 상태 머신이 처치 대기 목록에 넣는다). 못 놓으면 false */
  summon: (enemyId: string, x: number, y: number) => boolean;
  /** 집단 돌격 공유 상태 */
  pack: PackCharge;
  /** 54라운드: 보스방 환경 (기둥·촛대·술통·술 웅덩이·화면 효과). 보스방이 아니면 없음 */
  arena?: BossArenaApi | null;
  /** 61라운드 단계 2: 일반 적 위험물 (독주 행상 화염 술병 · 술통 짐꾼 술통 · 술 웅덩이). 없으면 그 행동을 하지 않는다 */
  hazards?: EnemyHazardApi | null;
}

export interface ProjectileSpec {
  speedPx: number;
  attack: number;
  size: number;
  lifeMs: number;
  /** 탄 시트 이름 (`fx/<이름>.json`, anchor projectile). 없으면 플레이스홀더 사각형 */
  sprite?: string;
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
  /** 60라운드: 엘리트 HP ×2.5 로 늘릴 수 있다 (`scaleMaxHp`) */
  maxHp: number;
  readonly visual: EntityVisual;
  /** 적·보스 id (= 시트 이름). 이벤트 페이로드에 쓴다 */
  readonly spriteId: string;
  /** 47라운드: 이동 속도 배율 (독주 웅덩이 등 환경). 일반 적만, AI 가 정한 속도에 곱한다 */
  speedMult = 1;
  /** 60라운드 2차 묶음 엘리트 접두어 (없으면 null — 엘리트 아님). 규칙은 씬 EliteSystem */
  elite: { prefix: string; name: string } | null = null;
  /** 60라운드 엘리트 접두어 효과: 받는 피해 배율(통 갑옷) · 경직 면역 · 피격 경직 배율(고주망태) · 이동·공격 속도 배율(성난·두목) */
  damageTakenMult = 1;
  stunImmune = false;
  hitStunMult = 1;
  eliteSpeedMult = 1;
  attackRateMult = 1;
  /** 60라운드 정적(간파 6) 감속: 이 시각까지 이동 속도 × statusSlowMult (웅덩이 speedMult 와 따로 — 둘 다 곱한다) */
  statusSlowUntil = -Infinity;
  statusSlowMult = 1;
  /** 마지막으로 본 플레이어 위치 (대기 방향용) */
  private targetX = 0;
  private targetY = 0;
  protected nextContactAt = 0;
  protected stunnedUntil = 0;
  /** 경직의 출처: 패링 경직 처치만 '패링 처치'로 센다 */
  private stunSource: 'parry' | 'hit' = 'parry';
  /** 밀쳐내기 중 (AI 가 속도를 덮어쓰지 않는다) */
  private knockedUntil = 0;
  /**
   * 피격 넉백(35라운드): 선형 감쇠 속도. 경과는 update 의 delta 로 누적하므로 히트스톱 동안은 멈춘다.
   * 일반 적은 AI 를 멈추고(짧은 비틀거림), 보스는 AI 속도에 더한다(패턴을 끊지 않음)
   */
  private shoveState: {
    vx: number;
    vy: number;
    elapsed: number;
    ms: number;
    additive: boolean;
    onEnd?: (mob: Mob, dirX: number, dirY: number) => void;
  } | null = null;

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
    // 53라운드 Q22~25 적 판독성: 몸 중심의 약한 빛 (조명이 꺼진 씬에서는 무해, 개체가 사라지면 자동 해제)
    if (LIGHTING.mob) lightRegistryOf(scene).add(LIGHTING.mob, { x, y, anchor: this });
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
    const sh = this.shoveState;
    if (sh && !sh.additive) {
      // 비틀거림: AI 대신 감쇠 속도
      const f = this.stepShove(ctx.delta);
      if (f > 0) this.body.setVelocity(sh.vx * f, sh.vy * f);
    } else {
      this.think(ctx);
      if (this.speedMult !== 1 && !this.isBoss) this.body.velocity.scale(this.speedMult);
      if (ctx.time < this.statusSlowUntil) this.body.velocity.scale(this.statusSlowMult);
      if (this.eliteSpeedMult !== 1) this.body.velocity.scale(this.eliteSpeedMult);
      if (sh) {
        const f = this.stepShove(ctx.delta);
        if (f > 0) this.body.setVelocity(this.body.velocity.x + sh.vx * f, this.body.velocity.y + sh.vy * f);
      }
    }
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

  /** 보스인지 (히트스톱·넉백 배율 분기) */
  abstract get isBoss(): boolean;

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

  /** 54라운드: 피해를 받지 않는 중 (보스 페이즈 전환 들이켜기). 피격 경로(GameCombat.hitMob)가 숫자·넉백 대신 불꽃만 */
  isImmune(_time: number): boolean {
    return false;
  }

  /** 패링 경직으로 멈춰 있는지 (감각 '패링 처치' 분류용) */
  isParryStunned(time: number): boolean {
    return this.isStunned(time) && this.stunSource === 'parry';
  }

  isKnockedBack(time: number): boolean {
    return time < this.knockedUntil || (this.shoveState !== null && !this.shoveState.additive);
  }

  /** 피격 넉백 중인지 (디버그) */
  get isShoved(): boolean {
    return this.shoveState !== null;
  }

  /** 바라보는 쪽(마지막으로 본 플레이어) 방향 단위벡터. 0 벡터면 (1, 0) */
  protected facingVector(): { x: number; y: number } {
    const dx = this.targetX - this.x;
    const dy = this.targetY - this.y;
    const len = Math.hypot(dx, dy);
    return len > 0 ? { x: dx / len, y: dy / len } : { x: 1, y: 0 };
  }

  /**
   * 방패 막기(35라운드 2단계): `dirX, dirY` 방향으로 들어오는 공격의 피해 감소 비율(0 = 안 막음).
   * 기본은 안 막음. 결사병이 정면 범위를 판정한다
   */
  guardReduction(_dirX: number, _dirY: number, _time: number): number {
    return 0;
  }

  /**
   * 피격 넉백: `distPx` 를 `ms` 동안 선형 감쇠로 이동 (벽은 Arcade 충돌이 막는다). 새 타격이 오면 덮어쓴다.
   * `additive` 면 AI 속도에 더하기만 한다(보스). 끝나면 `onEnd`(먼지 이펙트)
   */
  shove(
    dirX: number,
    dirY: number,
    distPx: number,
    ms: number,
    additive = false,
    onEnd?: (mob: Mob, dirX: number, dirY: number) => void,
  ): void {
    const speed = knockSpeed(distPx, ms);
    if (speed <= 0) return;
    const len = Math.hypot(dirX, dirY) || 1;
    this.shoveState = { vx: (dirX / len) * speed, vy: (dirY / len) * speed, elapsed: 0, ms, additive, onEnd };
    if (!additive) this.body.setVelocity(this.shoveState.vx, this.shoveState.vy);
  }

  /**
   * 넉백 한 프레임: 이번 프레임 구간의 중점 감쇠 비율을 돌려주고 경과를 더한다 (중점 적분 → 프레임 속도와 무관하게 거리 ≈ distPx).
   * 끝났으면 0 을 돌려주고 정리한다
   */
  private stepShove(delta: number): number {
    const sh = this.shoveState;
    if (!sh) return 0;
    if (sh.elapsed >= sh.ms) {
      this.endShove();
      return 0;
    }
    const f = knockFactor(sh.elapsed + delta / 2, sh.ms);
    sh.elapsed += delta;
    if (f <= 0) {
      this.endShove();
      return 0;
    }
    return f;
  }

  private endShove(): void {
    const sh = this.shoveState;
    this.shoveState = null;
    if (!sh) return;
    if (!sh.additive) this.body.setVelocity(0, 0);
    const len = Math.hypot(sh.vx, sh.vy) || 1;
    sh.onEnd?.(this, sh.vx / len, sh.vy / len);
  }

  /** 히트스톱: 애니 정지·재개 */
  setAnimPaused(on: boolean): void {
    if (on) this.anims.pause();
    else this.anims.resume();
  }

  /** 밀쳐내기: ms 동안 속도를 유지하고 AI 를 멈춘다 (가드 해제) */
  knockback(time: number, dirX: number, dirY: number, speedPx: number, ms: number): void {
    this.knockedUntil = Math.max(this.knockedUntil, time + ms);
    this.body.setVelocity(dirX * speedPx, dirY * speedPx);
  }

  /** 패링·중압 등으로 경직. 경직 중엔 움직이지도 공격하지도 않는다 */
  stun(time: number, ms0: number, source: 'parry' | 'hit' = 'parry'): void {
    // 60라운드 엘리트: 통 갑옷 경직 면역 · 고주망태 피격 경직 절반 (패링 경직은 그대로)
    if (this.stunImmune && source === 'hit') return;
    const ms = source === 'hit' ? ms0 * this.hitStunMult : ms0;
    if (!this.isStunned(time) || source === 'parry') this.stunSource = source;
    this.stunnedUntil = Math.max(this.stunnedUntil, time + ms);
    this.shoveState = null;
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
    this.nextContactAt = time + this.contactIntervalMs() / Math.max(0.1, this.attackRateMult);
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
    // 56라운드 Q36: 호박 반투명 80ms (히트스톱에 늘어나지 않음)
    this.visual.flashOverlay(COLORS.MOB_HURT, FEEDBACK.MOB_HURT.ALPHA, FEEDBACK.MOB_HURT.MS);
    // 보스가 국면 프레임을 유지 중이면 피격 애니 대신 번쩍임만
    if (!this.visual.held) this.visual.oneShot('hurt', this.visual.facing, this.scene.time.now);
    return false;
  }

  protected onDeath(): void {}

  /** 지금 받는 피해 배율 (엘리트 접두어 damageTakenMult · 61라운드 보스는 파훼 경직 동안 더 곱한다 — Boss) */
  damageTakenMultAt(_now: number): number {
    return this.damageTakenMult;
  }

  /** 60라운드 엘리트: 최대 HP 를 배율로 늘리고 가득 채운다 */
  scaleMaxHp(mult: number): void {
    this.maxHp = Math.max(1, Math.round(this.maxHp * mult));
    this.hp = this.maxHp;
  }

  /** 60라운드 들이켜는: 최대 HP 비율만큼 회복 */
  healRatio(ratio: number): void {
    this.hp = Math.min(this.maxHp, this.hp + Math.round(this.maxHp * ratio));
  }

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
