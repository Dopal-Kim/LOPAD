import Phaser from 'phaser';
import { COLORS, FEEDBACK, KEYS, PROTOTYPE, TILE } from '../core/Constants';
import { EventBus, Events, type PlayerAttackPayload } from '../core/EventBus';
import { gameState } from '../core/GameState';
import { PLAYER_DATA } from '../data';
import type { SecondaryDef, WeaponCarryDef, WeaponFirstStrikeDef } from '../data/types';
import type { InputState } from '../systems/InputSystem';
import { GROGGY_ACTION, facingOf, motionAction, type Facing } from '../systems/spriteDefs';
import type { ComboTracker } from '../systems/combo';
import type { WeaponResource } from '../systems/weaponResource';
import { knockFactor } from '../systems/feel';
import { isPerfectGuard } from '../systems/defense';
import { sprintStep } from '../systems/traversal';
import { EntityVisual, placeholderTexture } from './EntityVisual';
import { WeaponOverlay } from './WeaponOverlay';
import { ScarOverlay } from './player/ScarOverlay';
import { PlayerGear } from './player/PlayerGear';
import { PlayerPoses } from './player/PlayerPoses';
import type { ComboStrike } from './player/heavyMoves';
import { emitPlayerAttack, type AttackExtra } from './player/attackEmit';
import { MeleeDriver } from './player/MeleeDriver';
import { PlayerDefense } from './player/PlayerDefense';
import { PlayerGauges } from './player/PlayerGauges';
import { SecondaryDriver } from './player/SecondaryDriver';

type Body = Phaser.Physics.Arcade.Body;

/**
 * guard = 대검 가드(유지), aim = 활 당김(유지).
 * 49라운드: draw = 대검을 등에서 끌어냄 · slam = 대검 내리찍기(도약 → 착지 → 회복) · dashslash = 대검 대쉬 공격(달려들며 휘두름 → 멈춤)
 * 56라운드: skill = 무기 전용 동작(칼 일섬·대검 꽂아내리기 — 입력 잠금, 이동은 내딛기만)
 */
export type PlayerAction =
  'normal' | 'dash' | 'parry' | 'recover' | 'guard' | 'aim' | 'draw' | 'slam' | 'dashslash' | 'skill';

/** 내딛기·도약 한 구간 (from ~ until 동안 이 속도) */
interface Lunge {
  vx: number;
  vy: number;
  from: number;
  until: number;
}

export type HitResult = 'hit' | 'dead' | 'parried' | 'ignored';

/**
 * 주인공. 시트(`player_*`)가 있으면 애니메이션 스프라이트, 없으면 단색 사각형 플레이스홀더.
 * 50라운드 분리: 무기 자원·휴대 = `player/PlayerGear`, 무기를 든 자세 = `player/PlayerPoses`,
 * 대검 내리찍기·대쉬 공격 = `player/heavyMoves`. 55라운드: 연격 입력(순환·관성·차지·내딛기·정지) = `player/MeleeDriver`.
 * 56라운드 6-1: 우클릭 보조 동작(패링·가드·그림자 걸음·활 당김) = `player/SecondaryDriver`, 피격(퍼펙트 가드) = `player/PlayerDefense`,
 * 무기 고유 자원(검기·울분·숨) = `player/PlayerGauges`. 이 파일은 상태 머신(이동·대쉬·그로기·동작 전환)
 */
export class Player extends Phaser.GameObjects.Sprite {
  declare body: Body;
  action: PlayerAction = 'normal';
  readonly visual: EntityVisual;
  /** 손에 든 무기 오버레이 (계약 §3.1). 공격 애니 중에만 보인다 */
  readonly overlay: WeaponOverlay;
  /** 53라운드 Q4: 등 상흔 (몸 위·무기 아래) */
  readonly scar: ScarOverlay;
  /** 사망 애니 길이 (시트가 없으면 0) — Game 이 결과 화면 전환을 이만큼 늦춘다 */
  deathAnimMs = 0;
  /** 이번 프레임 이동 입력이 있었는지 (질풍 루프 이펙트용) */
  moving = false;
  /** 45라운드: 달리기 허용 (비전투). Game 이 매 프레임 RoomDirector 기준으로 넣는다 */
  sprintAllowed = false;
  /** 47라운드: 환경 이동 배율 (독주 웅덩이 -20%). 구조물 시스템이 매 프레임 넣는다 */
  envSpeedMult = 1;
  /** 54라운드 Q3: 미끄러움 0..1 (보스 술 웅덩이). 0 이면 조작 속도 그대로, 클수록 속도가 목표로 천천히 붙는다 */
  envSlip = 0;
  /** 53라운드 Q10: 이번 프레임 감속 배율 (조준·가드·공격 뒤·넣기/뽑기·기력 바닥·환경, 달리기 제외) — 낮으면 걷기 그림 */
  moveSlowMult = 1;
  /** 현재 이동 속도 배율 (1 ~ sprint.speedMult, 가속·감속) */
  private sprintFactor = 1;
  /** 이번 프레임 달리기 입력이 유효했는지 (Shift + 허용 + 이동 + 일반 상태) */
  private sprintingNow = false;
  private actionUntil = 0;
  private invulnerableUntil = 0;
  private attackReadyAt = 0;
  private dashReadyAt = 0;
  private dashEndedAt = -Infinity;
  /** 공격 판정 중(둔중한 무기일수록 길다) 이동 감속 */
  private attackSlowUntil = 0;
  /** 그림자 걸음 직후: 이 시간까지의 다음 공격 1회가 확정 치명(+암살 배율) */
  private shadowPrimedUntil = -Infinity;
  private facing = new Phaser.Math.Vector2(1, 0);
  private dashVel = new Phaser.Math.Vector2();
  private lastAimAngle = 0;
  /** 피격 넉백(35라운드): 가해자 반대 방향으로 선형 감쇠. 경과는 update 의 시간 차로 누적(히트스톱 중엔 update 가 없다) */
  private shoveState: { vx: number; vy: number; elapsed: number; ms: number } | null = null;
  /** 49라운드 무기 자원·휴대 · 48라운드 무기를 든 자세 · 55라운드 근접 연격 입력 */
  readonly gear: PlayerGear;
  readonly poses: PlayerPoses;
  readonly melee: MeleeDriver;
  /** 56라운드: 우클릭 보조 동작 · 피격 · 무기 고유 자원 */
  readonly secondaryDriver: SecondaryDriver;
  readonly defense: PlayerDefense;
  readonly gauges = new PlayerGauges();
  /** 49라운드: 앞으로 내딛기·도약. 56라운드: 구간 여러 개를 이어 붙인다 (대검 내딛기 → 휘두른 뒤 끌림) */
  private lunges: Lunge[] = [];
  /** 그로기 틴트를 칠했는가 (풀리면 원래 색) */
  private groggyPainted = false;
  /**
   * 56라운드: 플레이어 자신의 시계 (update 의 delta 합 — 히트스톱·정지 동안 멈춤). 내딛기 구간은 이 시계로 잰다 —
   * 몸 애니도 히트스톱에 멈추므로 일섬 돌진(적중 히트스톱이 끼어도 4칸)·대검 끌림이 그림과 어긋나지 않는다
   */
  private ownClock = 0;

  constructor(scene: Phaser.Scene, x: number, y: number) {
    const [w, h] = PLAYER_DATA.size;
    super(scene, x, y, placeholderTexture(scene, w, h));
    scene.add.existing(this);
    scene.physics.add.existing(this);
    this.visual = new EntityVisual(this, 'player', w, h, COLORS.PLAYER);
    this.gear = new PlayerGear(this);
    this.poses = new PlayerPoses(this);
    this.melee = new MeleeDriver(this);
    this.secondaryDriver = new SecondaryDriver(this);
    this.defense = new PlayerDefense(this);
    this.overlay = new WeaponOverlay(
      this,
      () => this.visual.current,
      () => ({ mode: this.gear.carryMode, drawn: this.gear.drawn }),
    );
    this.scar = new ScarOverlay(this, () => this.visual.current);
    this.body.setCollideWorldBounds(true);
  }

  protected preUpdate(time: number, delta: number): void {
    super.preUpdate(time, delta);
    this.visual.sync();
    this.overlay.update();
    // 56라운드 Q14·Q15: 검기·울분 무기 오버레이 (시트가 없으면 칼날 곱 틴트)
    this.overlay.setGauge(this.gauges.overlay, this.gauges.bladeTint);
    this.scar.update(time);
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

  /** 달리는 중 (스냅샷 `sprinting`) */
  get sprinting(): boolean {
    return this.sprintingNow;
  }

  /** 현재 달리기 배율 (디버그) */
  get sprintMult(): number {
    return this.sprintFactor;
  }

  /** 패링 창 (구 패링 동작 · 56라운드 Q48 칼 가드 직후 창) — 접촉 공격 주기와 무관하게 막는다 */
  get isParrying(): boolean {
    if (this.action === 'parry') return true;
    const S = this.secondary;
    return (
      this.action === 'guard' &&
      S.kind === 'guard' &&
      S.perfect === 'parry' &&
      isPerfectGuard(this.defense.guardStartedAt, this.scene.time.now, PLAYER_DATA.perfectGuard?.windowMs ?? 0)
    );
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

  /** 활 당김 진행도 0..1 (당기는 중이 아니면 0). 1 이면 가득 유지 중 */
  aimProgress(time: number): number {
    return this.secondaryDriver.aimProgress(time);
  }

  /** 활을 가득 당겨 유지 중인지 */
  get isAimReady(): boolean {
    return this.secondaryDriver.aimReady;
  }

  /** 마지막 조준 각도(rad, 커서 방향). 조준 점선·차지 게이지용 */
  get aimAngle(): number {
    return this.lastAimAngle;
  }

  /** 56라운드 Q20: 오래 쥔 활의 조준 흔들림 각(rad) — 조준선·화살이 함께 흔들린다 */
  aimJitter(time: number): number {
    return this.secondaryDriver.aimJitter(time);
  }

  /** 56라운드 Q7: 그로기 중 (칼·대검 기력 0 — 공격·대쉬 불가, 가드만) */
  get groggy(): boolean {
    return Boolean(this.resource?.isGroggy);
  }

  /** 56라운드: 플레이어 시계 지금 (히트스톱 동안 멈춤 — 내딛기·일섬 무적 구간) */
  get ownNow(): number {
    return this.ownClock;
  }

  /** 이 시각에 무적인가 (피격 무적·대쉬 무적) */
  isInvulnerableAt(time: number): boolean {
    return time < this.invulnerableUntil;
  }

  /** 공격 판정 중 감속 구간인가 (거인 슈퍼아머) */
  inAttackSlow(time: number): boolean {
    return time < this.attackSlowUntil;
  }

  /** 그림자 걸음 직후 확정 치명 (이 시각까지) */
  primeShadow(until: number): void {
    this.shadowPrimedUntil = until;
  }

  /** 피격 넉백 (가해자 반대 방향 감쇠 속도) */
  shove(vx: number, vy: number, ms: number): void {
    this.shoveState = { vx, vy, elapsed: 0, ms };
  }

  /** 48라운드: 현재 무기의 연격 상태 (연격이 없는 무기면 null) */
  get combo(): ComboTracker | null {
    return this.melee.combo;
  }

  /** 49라운드: 현재 무기의 자원 상태 (자원이 없는 무기면 null) */
  get resource(): WeaponResource | null {
    return this.gear.resource;
  }

  /** 바라보는 방향 단위벡터 (마지막 이동 방향) */
  get facingVec(): Phaser.Math.Vector2 {
    return this.facing;
  }

  /** 대검 마지막 타 뒤 정지 중 */
  isStopped(time: number): boolean {
    return this.melee.isStopped(time);
  }

  /** 대쉬가 끝나고 대쉬 공격 창 안인가 */
  inDashWindow(time: number): boolean {
    return time - this.dashEndedAt <= PLAYER_DATA.dash.attackWindowMs;
  }

  /** 현재 대쉬 방향 단위벡터 (대쉬 중이 아니면 마지막 값) */
  get dashDir(): { x: number; y: number } {
    const len = this.dashVel.length() || 1;
    return { x: this.dashVel.x / len, y: this.dashVel.y / len };
  }

  /** `delta` 는 이번 프레임 ms (넉백 감쇠 누적 — 히트스톱 동안은 호출되지 않으므로 그만큼 멈춘다) */
  update(input: InputState, time: number, delta = 0): void {
    const D = PLAYER_DATA.dash;
    if (input.aimX !== this.x || input.aimY !== this.y)
      this.lastAimAngle = Math.atan2(input.aimY - this.y, input.aimX - this.x);
    const P = PLAYER_DATA.parry;
    const mods = gameState.weapon.mods;
    this.ownClock += Math.max(0, delta);
    // 49라운드 무기 자원: 회복·장전·냉각 진행 (상태 변화는 WEAPON_RESOURCE 로 알린다) · 56라운드 고유 자원(숨 집중 끝)
    const res = this.resource;
    if (res) this.gear.tick(res, time, delta);
    this.gauges.tick(time);
    this.paintGroggy();

    // 진행 중인 동작 종료 처리
    if (this.action !== 'normal' && this.actionUntil > 0 && time >= this.actionUntil) {
      if (this.action === 'dash') {
        this.dashEndedAt = time;
        this.body.setVelocity(0, 0);
        this.setAction('normal', 0);
      } else if (this.action === 'parry') {
        // 창이 닫혔는데 아무것도 못 막음 → 후딜
        EventBus.emit(Events.PLAYER_PARRY_FAILED);
        this.poses.playSpecial(time, 'parryFail', P.failRecoveryMs);
        this.setAction('recover', time + P.failRecoveryMs);
      } else {
        this.setAction('normal', 0);
      }
    }

    // 유지형 보조 동작: 가드(떼면 밀쳐내기) · 활 당김(떼면 발사 — 56라운드 Q9 일찍 떼면 약한 1발)
    this.secondaryDriver.hold(input, time);

    // 49라운드: 수동 장전 (R) — 탄창이 덜 찼고 장전 중이 아닐 때
    if (input.reloadPressed && res?.kind === 'ammo' && this.action === 'normal' && res.startReload(time))
      this.gear.onReloadStart(time);

    // 이동 (대쉬 중엔 대쉬 속도 유지)
    const dir = new Phaser.Math.Vector2(input.moveX, input.moveY);
    if (dir.lengthSq() > 0) {
      dir.normalize();
      this.facing.copy(dir);
    }
    // 달리기 (45라운드): 일반 상태 이동 중에만 목표 배율. 대쉬 동안은 배율을 유지해 끝나면 이어서 달린다
    const SP = PLAYER_DATA.sprint;
    this.sprintingNow = this.sprintAllowed && input.sprintHeld && dir.lengthSq() > 0 && this.action === 'normal';
    if (this.action !== 'dash')
      this.sprintFactor = sprintStep(this.sprintFactor, this.sprintingNow ? SP.speedMult : 1, delta, SP);
    const sh = this.shoveState;
    // 49라운드: 내딛기·도약 (대검 반 걸음 · 내리찍기 도약 · 대쉬 공격 돌진 · 56라운드 끌림·일섬 돌진)
    const own = this.ownClock;
    this.lunges = this.lunges.filter((l) => own < l.until);
    const lunge = this.lunges.find((l) => own >= l.from) ?? null;
    const stopped = this.isStopped(time);
    if (this.action === 'dash') {
      this.body.setVelocity(this.dashVel.x, this.dashVel.y);
    } else if (sh) {
      // 피격 넉백: 조작 대신 감쇠 속도 (아주 짧음). 프레임 구간 중점 비율로 적분
      const f = sh.elapsed >= sh.ms ? 0 : knockFactor(sh.elapsed + delta / 2, sh.ms);
      sh.elapsed += delta;
      if (f <= 0) this.shoveState = null;
      this.body.setVelocity(sh.vx * f, sh.vy * f);
    } else if (lunge) {
      this.body.setVelocity(lunge.vx, lunge.vy);
    } else if (this.action === 'slam' || this.action === 'dashslash' || this.action === 'skill' || stopped) {
      // 대검: 내리찍기 착지·대쉬 공격 뒤 멈춤 · 3타 뒤 정지 · 56라운드 전용 동작(일섬 자세·꽂아내리기)
      this.body.setVelocity(0, 0);
    } else {
      let slow = time < this.attackSlowUntil ? gameState.weapon.attackSlowMult : 1;
      const S = this.secondary;
      if (this.action === 'guard' && S.kind === 'guard') slow = Math.min(slow, S.moveMult);
      if (this.action === 'aim' && S.kind === 'aimedshot') slow = Math.min(slow, S.moveMult);
      // 55라운드 Q22: 대검 차지 중 감속
      slow = Math.min(slow, this.melee.moveMult);
      // 49라운드: 기력이 바닥나면 감속 (56라운드: 그로기 · 단검 과열 식는 동안)
      const tired = res?.moveMult ?? 1;
      this.moveSlowMult = slow * tired * Math.min(1, this.envSpeedMult);
      const speed = this.speedPx * slow * this.sprintFactor * this.envSpeedMult * tired;
      if (this.envSlip > 0) {
        // 미끄러움: 60fps 한 프레임에 (1 - slip) 만큼만 목표 속도로 붙는다 (프레임 시간 보정)
        const k = 1 - Math.pow(this.envSlip, delta / (1000 / 60));
        const v = this.body.velocity;
        this.body.setVelocity(v.x + (dir.x * speed - v.x) * k, v.y + (dir.y * speed - v.y) * k);
      } else this.body.setVelocity(dir.x * speed, dir.y * speed);
    }
    this.moving = this.poses.locomotion(input, dir, time);
    this.poses.holdSecondary(input, time);
    this.melee.holdPose(input, time);
    this.gear.updateCarry(time);

    const canAct = this.action === 'normal' && !(stopped && this.melee.stopBlocksAct);
    // 56라운드 Q7: 그로기 중엔 공격·대쉬·넣기 불가 (보조 동작 = 가드·패링만)
    const canStrike = canAct && !this.groggy;

    // 51라운드 Q4: F = 넣기/뽑기 (칼·대검). 동작 동안 다른 행동은 잠그고 느리게 걷는다
    if (input.carryPressed && canStrike) {
      const r = this.gear.toggle(time);
      if (r) {
        this.melee.reset();
        this.lunges = [];
        if (r.ms > 0) {
          this.setAction('draw', time + r.ms);
          this.slowUntil(time + r.ms);
        }
        return;
      }
    }

    // 대쉬
    if (input.dashPressed && canStrike && time >= this.dashReadyAt) {
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
      // 49라운드 기력: 대쉬 소모 (바닥나도 대쉬는 된다 — 회피 수단은 남긴다, 임시)
      if (res?.def.kind === 'stamina') res.spend(res.def.cost.dash, time);
      this.lunges = [];
      this.setAction('dash', time + D.durationMs);
      this.combo?.reset();
      this.melee.cancelCharge();
      this.visual.oneShot(this.poses.bodyAction('dash'), facingOf(d.x, d.y, this.visual.facing), time, D.durationMs);
      EventBus.emit(Events.PLAYER_DASHED, { dirX: d.x, dirY: d.y, x: this.x, y: this.y });
      return;
    }

    // 보조 동작 (우클릭): 무기별 — 56라운드 `SecondaryDriver`. 그로기 중에도 가드·패링은 된다
    if (input.secondaryPressed && canAct && this.secondaryDriver.press(input, time)) return;

    // 공격 (대쉬 직후면 대쉬 공격). 48라운드: 근접은 연격 상태 머신 — 55라운드 `MeleeDriver`(순환·관성·차지·내딛기)
    if (this.combo) {
      this.melee.update(input, time, canStrike, dir.lengthSq() > 0);
      return;
    }
    if (input.attackPressed && canStrike && time >= this.attackReadyAt) {
      // 49라운드 탄창: 비었으면 장전 (자동 장전이 이미 돌고 있으면 그대로)
      if (res && !res.canAttack()) {
        if (res.kind === 'ammo' && res.startReload(time)) this.gear.onReloadStart(time);
        return;
      }
      // 51라운드 Q2·Q3: 시위 당김(drawMs)이 보이게 · 다음 발 간격 (속사 배율 반영)
      const T = gameState.weapon.shotTiming;
      this.attackReadyAt = time + T.cooldownMs;
      this.attackSlowUntil = time + Math.max(gameState.weapon.hitbox.activeMs, PLAYER_DATA.attackSlowMinMs, T.drawMs);
      this.fireAttack(input, time, null, true);
      this.gear.markDrawn(time);
      if (res?.kind === 'ammo' && res.fire(time)) this.gear.onReloadStart(time);
    }
  }

  /** 대쉬 공격·그림자 걸음 배율 (대쉬 공격·확정 치명은 1회 소비). heavyMoves 도 쓴다 */
  strikeMods(
    time: number,
    allowDash: boolean,
  ): { mult: number; forceCrit: boolean; primed: boolean; isDashAttack: boolean } {
    const D = PLAYER_DATA.dash;
    const mods = gameState.weapon.mods;
    const isDashAttack = allowDash && time - this.dashEndedAt <= D.attackWindowMs;
    let mult = 1;
    let forceCrit = false;
    if (isDashAttack) {
      mult *= D.attackDamageMult * (1 + gameState.passives.total('dashAttackMult')) * (mods.dashAttackMult ?? 1);
      forceCrit = Boolean(mods.dashAttackForceCrit);
      this.dashEndedAt = -Infinity; // 대쉬 공격은 1회
    }
    let primed = false;
    if (this.isShadowPrimed(time)) {
      mult *= mods.shadowStepMult ?? 1;
      forceCrit = true;
      primed = true;
      this.shadowPrimedUntil = -Infinity; // 1회
    }
    return { mult, forceCrit, primed, isDashAttack };
  }

  /**
   * 공격 1회 (대쉬 공격·그림자 걸음 직후 확정 치명 판정 포함). combo 가 있으면 그 타의 배율·길이.
   * 49라운드: allowDash 가 false(기력 바닥)면 대쉬 직후라도 일반 공격. MeleeDriver 도 쓴다
   */
  fireAttack(
    input: InputState,
    time: number,
    combo: ComboStrike | null,
    allowDash = true,
    first: WeaponFirstStrikeDef | null = null,
    more?: AttackExtra,
  ): PlayerAttackPayload {
    const D = PLAYER_DATA.dash;
    const m = this.strikeMods(time, allowDash);
    const mult = (combo ? combo.hit.damageMult : 1) * m.mult * (first?.damageMult ?? 1);
    const size = (m.isDashAttack ? D.attackSizeMult : 1) * (combo ? combo.hit.sizeMult : 1);
    return this.emitAttack(
      input,
      time,
      m.isDashAttack ? 'dashAttack' : 'attack',
      mult,
      size,
      m.forceCrit || Boolean(first?.forceCrit),
      m.primed,
      combo,
      first || more
        ? { ...(first ? { firstStrike: first.label, knockbackMult: first.knockbackMult } : {}), ...more }
        : undefined,
    );
  }

  // --- 49라운드: 대검 무게감 (내딛기·감속·뽑기) — heavyMoves 도 쓴다 ---

  /** 대검: 등에서 두 손으로 끌어냄 (`player_greatsword_draw` + `weapons/greatsword_draw`, drawMs 에 맞춤) */
  startDraw(input: InputState, time: number, carry: WeaponCarryDef): void {
    this.setAction('draw', time + carry.drawMs);
    this.slowUntil(time + carry.drawMs);
    const act = motionAction(gameState.weapon.id, 'draw');
    const dir = facingOf(input.aimX - this.x, input.aimY - this.y, this.visual.facing);
    if (this.visual.hasAction(act)) this.visual.oneShot(act, dir, time, carry.drawMs);
    this.gear.beginDraw(time);
  }

  /** 공격 감속을 이 시각까지 늘린다 (이미 더 길면 그대로) */
  slowUntil(until: number): void {
    this.attackSlowUntil = Math.max(this.attackSlowUntil, until);
  }

  /**
   * dir 방향으로 distPx 를 ms 동안 내딛는다 (fromMs 는 지금부터 시작 지연). append 면 앞 구간 뒤에 이어 붙인다(대검 끌림).
   * 56라운드: 구간은 플레이어 시계(히트스톱 동안 멈춤)로 잰다 — `_time` 은 호출 호환용(같은 프레임의 지금)
   */
  startLunge(dirX: number, dirY: number, distPx: number, ms: number, _time: number, fromMs = 0, append = false): void {
    const len = Math.hypot(dirX, dirY) || 1;
    const v = distPx / (Math.max(1, ms) / 1000);
    const t0 = this.ownClock;
    const l: Lunge = { vx: (dirX / len) * v, vy: (dirY / len) * v, from: t0 + fromMs, until: t0 + fromMs + ms };
    if (append) {
      this.lunges.push(l);
      this.lunges.sort((a, b) => a.from - b.from);
    } else this.lunges = [l];
  }

  /** 53라운드 계약 `UiSnapshot.carry`: 넣고 뽑는 무기(칼·대검)만, 손에 드는 무기는 null */
  carryUi(): { drawn: boolean; firstStrike: string | null; key: 'F' } | null {
    if (this.gear.carryMode === 'hand') return null;
    return { drawn: this.gear.drawn, firstStrike: this.gear.firstStrike?.label ?? null, key: KEYS.CARRY };
  }

  /** 디버그 (49라운드): 자원·휴대·내딛기 상태 */
  debugWeapon(time: number): Record<string, unknown> {
    return {
      weapon: gameState.weapon.id,
      action: this.action,
      carry: {
        mode: this.gear.carryMode,
        drawn: this.gear.drawn,
        sheathed: this.gear.sheathed,
        firstStrike: this.gear.firstStrike?.label ?? null,
        regenMult: this.resource?.regenMult ?? 1,
        overlay: this.overlay.carry,
        lastAttackAt: this.gear.lastAttackAt,
      },
      // 52라운드 v3: 무기 시트·프레임 · 연격 중 휴대 숨김 · 손·칼 앵커(월드) · 걷기·달리기 배속
      overlay: {
        action: this.overlay.action,
        frame: this.overlay.frame,
        carryHidden: this.overlay.carryHidden,
        anchors: this.overlay.anchors(),
      },
      strideRate: this.poses.strideRate,
      resource: this.resource?.debug(time) ?? null,
      lunge: this.lunges[0] ? { ...this.lunges[0], clock: this.ownClock } : null,
      lunges: this.lunges.length,
      groggy: this.groggy,
      gauge: this.gauges.debug(time),
      secondary: { lastRelease: this.secondaryDriver.lastRelease, defense: this.defense.lastOutcome },
      melee: this.melee.debug(time),
      stopped: this.isStopped(time),
      sinceDashMs: Number.isFinite(this.dashEndedAt) ? time - this.dashEndedAt : null,
      lastEvent: this.gear.lastEvent,
      vx: this.body.velocity.x,
      vy: this.body.velocity.y,
    };
  }

  /** 공격 1회 알림 (애니·판정 시각·페이로드) — 51라운드 정리로 `player/attackEmit`. SecondaryDriver(활 놓기)도 쓴다 */
  emitAttack(
    input: InputState,
    time: number,
    kind: PlayerAttackPayload['kind'],
    damageMult: number,
    sizeMult: number,
    forceCrit: boolean,
    primed = false,
    combo: ComboStrike | null = null,
    extra?: AttackExtra,
  ): PlayerAttackPayload {
    return emitPlayerAttack(this, input, time, { kind, damageMult, sizeMult, forceCrit, primed }, combo, extra);
  }

  /** 워프(45라운드): 진행 중 동작·넉백·달리기를 끊고 멈춘다 */
  haltForWarp(): void {
    if (this.action === 'aim') this.secondaryDriver.cancelDraw(this.scene.time.now);
    if (this.action !== 'normal') this.setAction('normal', 0);
    this.lunges = [];
    this.defense.clearWindows();
    this.melee.reset();
    this.visual.release();
    this.shoveState = null;
    this.sprintFactor = 1;
    this.sprintingNow = false;
    this.body.setVelocity(0, 0);
  }

  /** 이 시각까지 무적 (기존 무적보다 길 때만) */
  grantInvulnerable(until: number): void {
    this.invulnerableUntil = Math.max(this.invulnerableUntil, until);
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

  /** 피격 넉백 중인지 (디버그) */
  get isShoved(): boolean {
    return this.shoveState !== null;
  }

  /** 히트스톱: 애니 정지·재개 */
  setAnimPaused(on: boolean): void {
    if (on) this.anims.pause();
    else this.anims.resume();
  }

  /** 적의 공격을 받는다 — 56라운드 `player/PlayerDefense` (패링·퍼펙트 가드·가드·슈퍼아머·넉백·사망) */
  takeHit(attack: number, time: number, source?: { dirX: number; dirY: number }): HitResult {
    return this.defense.takeHit(attack, time, source);
  }

  /** 동작 상태 전환 (heavyMoves 도 쓴다) */
  setAction(a: PlayerAction, until: number): void {
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
        // 그로기 몸 시트(player_groggy)가 없을 때만 임시 틴트
        if (this.groggy && !this.visual.hasAction(GROGGY_ACTION)) this.visual.paint(FEEDBACK.GROGGY_TINT);
        else this.visual.restore();
    }
  }

  /** 56라운드 Q7: 그로기 시작·끝에 몸 색 (아트 그로기 자세가 오기 전 임시 틴트). 그로기 시작이면 차지·당김을 끊는다 */
  private paintGroggy(): void {
    const g = this.groggy;
    if (g === this.groggyPainted) return;
    this.groggyPainted = g;
    if (g) this.melee.cancelCharge();
    this.applyStateColor();
  }

  /** 짧은 번쩍임 (55라운드 차지 단계 호박 번쩍임 — MeleeDriver) */
  flashColor(color: number): void {
    this.flash(color);
  }

  private flash(color: number): void {
    this.visual.flash(color);
    this.scene.time.delayedCall(PROTOTYPE.HURT_FLASH_MS, () => {
      if (this.active) this.applyStateColor();
    });
  }
}
