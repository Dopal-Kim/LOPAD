import Phaser from 'phaser';
import { COLORS, FEEL, PROTOTYPE, TILE } from '../core/Constants';
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
import type { SecondaryDef, WeaponCarryDef } from '../data/types';
import { applyDefense } from '../systems/Combat';
import type { InputState } from '../systems/InputSystem';
import { comboAction, facingOf, motionAction, type Facing } from '../systems/spriteDefs';
import { ComboTracker } from '../systems/combo';
import type { WeaponResource } from '../systems/weaponResource';
import { knockFactor, knockSpeed } from '../systems/feel';
import { sprintStep } from '../systems/traversal';
import { EntityVisual, placeholderTexture } from './EntityVisual';
import { WeaponOverlay } from './WeaponOverlay';
import { PlayerGear } from './player/PlayerGear';
import { PlayerPoses } from './player/PlayerPoses';
import { startDashSlash, startSlam, type ComboStrike } from './player/heavyMoves';

type Body = Phaser.Physics.Arcade.Body;

/**
 * guard = 대검 가드(유지), aim = 활 조준 사격 차지(유지).
 * 49라운드: draw = 대검을 등에서 끌어냄 · slam = 대검 내리찍기(도약 → 착지 → 회복) · dashslash = 대검 대쉬 공격(달려들며 휘두름 → 멈춤)
 */
export type PlayerAction = 'normal' | 'dash' | 'parry' | 'recover' | 'guard' | 'aim' | 'draw' | 'slam' | 'dashslash';

export type HitResult = 'hit' | 'dead' | 'parried' | 'ignored';

/**
 * 주인공. 시트(`player_*`)가 있으면 애니메이션 스프라이트, 없으면 단색 사각형 플레이스홀더.
 * 50라운드 분리: 무기 자원·휴대 = `player/PlayerGear`, 무기를 든 자세 = `player/PlayerPoses`,
 * 대검 내리찍기·대쉬 공격 = `player/heavyMoves`. 이 파일은 상태 머신(이동·대쉬·보조 동작·연격 입력·피격)
 */
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
  /** 45라운드: 달리기 허용 (비전투). Game 이 매 프레임 RoomDirector 기준으로 넣는다 */
  sprintAllowed = false;
  /** 47라운드: 환경 이동 배율 (독주 웅덩이 -20%). 구조물 시스템이 매 프레임 넣는다 */
  envSpeedMult = 1;
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
  /** 보조 동작(그림자 걸음·조준 사격) 쿨 */
  private secondaryReadyAt = 0;
  /** 조준 사격 차지 시작 */
  private aimStartedAt = 0;
  /** 조준 사격 차지 완료(유지 중). 떼면 발사 */
  private aimReady = false;
  /** 그림자 걸음 직후: 이 시간까지의 다음 공격 1회가 확정 치명(+암살 배율) */
  private shadowPrimedUntil = -Infinity;
  private facing = new Phaser.Math.Vector2(1, 0);
  private dashVel = new Phaser.Math.Vector2();
  private lastAimAngle = 0;
  /** 피격 넉백(35라운드): 가해자 반대 방향으로 선형 감쇠. 경과는 update 의 시간 차로 누적(히트스톱 중엔 update 가 없다) */
  private shoveState: { vx: number; vy: number; elapsed: number; ms: number } | null = null;
  /** 48라운드 Q2: 근접 3연격 상태 (무기 데이터에 combo 가 있을 때) */
  private comboTracker: ComboTracker | null = null;
  private comboWeapon = '';
  /** 49라운드 무기 자원·휴대 · 48라운드 무기를 든 자세 */
  readonly gear: PlayerGear;
  readonly poses: PlayerPoses;
  /** 49라운드: 앞으로 내딛기·도약 (from ~ until 동안 이 속도) */
  private lunge: { vx: number; vy: number; from: number; until: number } | null = null;
  /** 49라운드 대검: 마지막 타 뒤 완전 정지 구간 */
  private stopFrom = 0;
  private stopUntil = 0;
  /** 정지 구간에 공격·대쉬도 막는가 (마지막 타) — 1·2타 회복 구간은 이동만 막고 다음 타는 허용 */
  private stopBlocksAct = false;

  constructor(scene: Phaser.Scene, x: number, y: number) {
    const [w, h] = PLAYER_DATA.size;
    super(scene, x, y, placeholderTexture(scene, w, h));
    scene.add.existing(this);
    scene.physics.add.existing(this);
    this.visual = new EntityVisual(this, 'player', w, h, COLORS.PLAYER);
    this.gear = new PlayerGear(this);
    this.poses = new PlayerPoses(this);
    this.overlay = new WeaponOverlay(
      this,
      () => this.visual.current,
      () => ({ mode: this.gear.carryMode, drawn: this.gear.drawn }),
    );
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

  /** 달리는 중 (스냅샷 `sprinting`) */
  get sprinting(): boolean {
    return this.sprintingNow;
  }

  /** 현재 달리기 배율 (디버그) */
  get sprintMult(): number {
    return this.sprintFactor;
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

  /** 조준 차지 진행도 0..1 (조준 중이 아니면 0). 1 이면 차지 완료 상태로 유지 중 */
  aimProgress(time: number): number {
    const S = this.secondary;
    if (this.action !== 'aim' || S.kind !== 'aimedshot') return 0;
    return Phaser.Math.Clamp((time - this.aimStartedAt) / S.chargeMs, 0, 1);
  }

  /** 조준 사격 차지가 끝나 발사 대기 중인지 */
  get isAimReady(): boolean {
    return this.action === 'aim' && this.aimReady;
  }

  /** 마지막 조준 각도(rad, 커서 방향). 조준 점선·차지 게이지용 */
  get aimAngle(): number {
    return this.lastAimAngle;
  }

  /** 48라운드: 현재 무기의 연격 상태 (연격이 없는 무기면 null) */
  get combo(): ComboTracker | null {
    const w = gameState.weapon;
    if (this.comboWeapon !== w.id) {
      this.comboWeapon = w.id;
      this.comboTracker = w.def.kind === 'melee' && w.def.combo ? new ComboTracker(w.def.combo) : null;
    }
    return this.comboTracker;
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
    return time >= this.stopFrom && time < this.stopUntil;
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
    const S = this.secondary;
    const mods = gameState.weapon.mods;
    const W = gameState.weapon.def;
    // 49라운드 무기 자원: 회복·장전·냉각 진행 (상태 변화는 WEAPON_RESOURCE 로 알린다)
    const res = this.resource;
    if (res) this.gear.tick(res, time, delta);

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

    // 유지형 보조 동작: 가드(떼면 밀쳐내기) · 조준(차지 완료 후에도 유지, 떼면 발사 — 31라운드 2. 차지 전에 떼면 취소)
    if (this.action === 'guard' && !input.secondaryHeld) {
      this.setAction('normal', 0);
      const payload: GuardReleasedPayload = { x: this.x, y: this.y };
      EventBus.emit(Events.PLAYER_GUARD_RELEASED, payload);
      this.visual.release();
      this.poses.playSpecial(time, 'guardRelease', undefined, input);
    }
    if (this.action === 'aim' && S.kind === 'aimedshot') {
      const charged = time - this.aimStartedAt >= S.chargeMs;
      if (charged && !this.aimReady) {
        this.aimReady = true;
        this.flash(COLORS.PLAYER_PARRY); // 차지 완료 신호 (번쩍 뒤 조준 틴트로 복귀)
        EventBus.emit(Events.PLAYER_SECONDARY, { kind: 'aimedshot', phase: 'ready' } satisfies PlayerSecondaryPayload);
      }
      if (!input.secondaryHeld) {
        this.setAction('normal', 0);
        if (charged) {
          this.secondaryReadyAt = time + S.cooldownMs;
          this.emitAttack(input, time, 'aimed', S.damageMult * (mods.aimedShotMult ?? 1), 1, false);
          // 49라운드 탄창: 조준 사격도 한 발
          if (res?.kind === 'ammo' && res.fire(time)) this.gear.onReloadStart(time);
        } else {
          EventBus.emit(Events.PLAYER_SECONDARY, {
            kind: 'aimedshot',
            phase: 'cancel',
          } satisfies PlayerSecondaryPayload);
        }
      }
    }

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
    // 49라운드: 내딛기·도약 (대검 반 걸음 · 내리찍기 도약 · 대쉬 공격 돌진)
    if (this.lunge && time >= this.lunge.until) this.lunge = null;
    const lunge = this.lunge && time >= this.lunge.from ? this.lunge : null;
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
    } else if (this.action === 'slam' || this.action === 'dashslash' || stopped) {
      // 대검: 내리찍기 착지·대쉬 공격 뒤 멈춤 · 3타 뒤 정지
      this.body.setVelocity(0, 0);
    } else {
      let slow = time < this.attackSlowUntil ? gameState.weapon.attackSlowMult : 1;
      if (this.action === 'guard' && S.kind === 'guard') slow = Math.min(slow, S.moveMult);
      if (this.action === 'aim' && S.kind === 'aimedshot') slow = Math.min(slow, S.moveMult);
      // 49라운드: 기력이 바닥나면 감속
      const tired = res?.moveMult ?? 1;
      const speed = this.speedPx * slow * this.sprintFactor * this.envSpeedMult * tired;
      this.body.setVelocity(dir.x * speed, dir.y * speed);
    }
    this.moving = this.poses.locomotion(input, dir, time);
    this.poses.holdSecondary(input, time);
    this.gear.updateCarry(time);

    const canAct = this.action === 'normal' && !(stopped && this.stopBlocksAct);

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
      // 49라운드 기력: 대쉬 소모 (바닥나도 대쉬는 된다 — 회피 수단은 남긴다, 임시)
      if (res?.def.kind === 'stamina') res.spend(res.def.cost.dash, time);
      this.lunge = null;
      this.setAction('dash', time + D.durationMs);
      this.combo?.reset();
      this.visual.oneShot('dash', facingOf(d.x, d.y, this.visual.facing), time, D.durationMs);
      EventBus.emit(Events.PLAYER_DASHED, { dirX: d.x, dirY: d.y, x: this.x, y: this.y });
      return;
    }

    // 보조 동작 (우클릭): 무기별. 49라운드 휴대: 칼·대검은 보조 동작으로도 뽑은 상태가 된다
    if (input.secondaryPressed && canAct) {
      if (S.kind === 'parry' || S.kind === 'guard') this.gear.markDrawn(time);
      switch (S.kind) {
        case 'parry': {
          const win = P.windowMs * (1 + gameState.passives.total('parryWindowMult'));
          this.setAction('parry', time + win);
          this.poses.playSpecial(time, 'parryStart', win, input);
          return;
        }
        case 'guard':
          this.setAction('guard', 0);
          this.poses.playSpecial(time, 'guardStart', undefined, input);
          EventBus.emit(Events.PLAYER_SECONDARY, { kind: 'guard', phase: 'start' } satisfies PlayerSecondaryPayload);
          return;
        case 'aimedshot':
          // 49라운드 탄창: 화살이 있고 장전 중이 아닐 때만 조준
          if (time >= this.secondaryReadyAt && (!res || res.canFire())) {
            this.aimStartedAt = time;
            this.aimReady = false;
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
            this.poses.playSpecial(time, 'shadowArrive', undefined, input);
          }
          return;
      }
    }

    // 공격 (대쉬 직후면 대쉬 공격). 48라운드: 근접은 3연격 상태 머신(입력 버퍼·다음 타 허용 창·리셋)
    const combo = this.combo;
    if (combo) {
      if (input.attackPressed) combo.press(time);
      if (!canAct || !combo.buffered(time)) return;
      // 49라운드 과열: 냉각 중엔 공격 불가
      if (res && !res.canAttack()) return;
      // 49라운드 휴대: 대검은 등에서 두 손으로 끌어낸 뒤 휘두른다 (버퍼는 유지 → 뽑기가 끝나면 1타)
      const carry = W.carry;
      if (carry && carry.mode !== 'hand' && !this.gear.drawn && carry.drawMs > 0) {
        this.startDraw(input, time, carry);
        return;
      }
      // 49라운드 기력: 바닥나면 강한 타(마지막 타·대쉬 공격·내리찍기) 불가
      const strong = res?.canStrong ?? true;
      const dashWindow = strong && time - this.dashEndedAt <= D.attackWindowMs;
      if (W.dashSlash && dashWindow && time >= combo.readyAt()) {
        startDashSlash(this, input, time, W);
        return;
      }
      combo.setSpeed(res?.speedMult ?? 1);
      const idx = combo.poll(time, true, strong);
      if (idx === null) return;
      const hit = combo.hits[idx];
      const last = idx === combo.hits.length - 1;
      const slam = last && W.slam && mods.shockwave ? W.slam : null;
      if (res?.def.kind === 'stamina') {
        const C = res.def.cost;
        res.spend(slam ? C.slam : dashWindow ? C.dashAttack : (C.hits[Math.min(idx, C.hits.length - 1)] ?? 0), time);
      }
      if (res?.kind === 'heat') res.heatUp(idx, time);
      this.gear.markDrawn(time);
      if (slam) {
        startSlam(this, input, time, { index: idx, count: combo.hits.length, hit, durationMs: hit.durationMs }, slam);
        return;
      }
      const strike: ComboStrike = { index: idx, count: combo.hits.length, hit, durationMs: combo.durationOf(idx) };
      const weight = W.weight;
      this.attackSlowUntil =
        time + Math.max(hit.activeMs, PLAYER_DATA.attackSlowMinMs, weight ? strike.durationMs + weight.postSlowMs : 0);
      const payload = this.fireAttack(input, time, strike, dashWindow);
      // 49라운드 대검 무게감: 타마다 반 걸음 전진. 이동 정지 = 몸 시트 recoverFrames 구간(아트 메모, 마지막 타는 공격·대쉬도),
      // 시트 메모가 없으면 마지막 타만 타격 순간부터 finisherStopMs
      if (weight) {
        this.startLunge(payload.dirX, payload.dirY, weight.stepPx, weight.stepMs, time);
        this.stopUntil = 0;
        this.stopBlocksAct = last;
        const body = payload.bodyAction ? this.visual.sheet(payload.bodyAction) : undefined;
        const rf = body?.recoverFrames;
        if (Array.isArray(rf) && rf.length > 0 && payload.bodyAction !== 'attack') {
          this.stopFrom = time + this.visual.frameStartMs(Math.min(...rf));
          this.stopUntil = time + this.visual.lastDurationMs;
        } else if (last) {
          this.stopFrom = time + payload.swingDelayMs;
          this.stopUntil = this.stopFrom + weight.finisherStopMs;
        }
      }
      return;
    }
    if (input.attackPressed && canAct && time >= this.attackReadyAt) {
      // 49라운드 탄창: 비었으면 장전 (자동 장전이 이미 돌고 있으면 그대로)
      if (res && !res.canAttack()) {
        if (res.kind === 'ammo' && res.startReload(time)) this.gear.onReloadStart(time);
        return;
      }
      this.attackReadyAt = time + gameState.weapon.hitbox.cooldownMs;
      this.attackSlowUntil = time + Math.max(gameState.weapon.hitbox.activeMs, PLAYER_DATA.attackSlowMinMs);
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
   * 49라운드: allowDash 가 false(기력 바닥)면 대쉬 직후라도 일반 공격
   */
  private fireAttack(
    input: InputState,
    time: number,
    combo: ComboStrike | null,
    allowDash = true,
  ): PlayerAttackPayload {
    const D = PLAYER_DATA.dash;
    const m = this.strikeMods(time, allowDash);
    const mult = (combo ? combo.hit.damageMult : 1) * m.mult;
    const size = (m.isDashAttack ? D.attackSizeMult : 1) * (combo ? combo.hit.sizeMult : 1);
    return this.emitAttack(
      input,
      time,
      m.isDashAttack ? 'dashAttack' : 'attack',
      mult,
      size,
      m.forceCrit,
      m.primed,
      combo,
    );
  }

  // --- 49라운드: 대검 무게감 (내딛기·감속·뽑기) — heavyMoves 도 쓴다 ---

  /** 대검: 등에서 두 손으로 끌어냄 (`player_greatsword_draw` + `weapons/greatsword_draw`, drawMs 에 맞춤) */
  private startDraw(input: InputState, time: number, carry: WeaponCarryDef): void {
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

  /** dir 방향으로 distPx 를 ms 동안 내딛는다 (from 은 시작 지연) */
  startLunge(dirX: number, dirY: number, distPx: number, ms: number, time: number, fromMs = 0): void {
    const len = Math.hypot(dirX, dirY) || 1;
    const v = distPx / (Math.max(1, ms) / 1000);
    this.lunge = { vx: (dirX / len) * v, vy: (dirY / len) * v, from: time + fromMs, until: time + fromMs + ms };
  }

  /** 디버그 (49라운드): 자원·휴대·내딛기 상태 */
  debugWeapon(time: number): Record<string, unknown> {
    return {
      weapon: gameState.weapon.id,
      action: this.action,
      carry: {
        mode: this.gear.carryMode,
        drawn: this.gear.drawn,
        overlay: this.overlay.carry,
        lastAttackAt: this.gear.lastAttackAt,
      },
      resource: this.resource?.debug(time) ?? null,
      lunge: this.lunge ? { ...this.lunge } : null,
      stopped: this.isStopped(time),
      sinceDashMs: Number.isFinite(this.dashEndedAt) ? time - this.dashEndedAt : null,
      lastEvent: this.gear.lastEvent,
      vx: this.body.velocity.x,
      vy: this.body.velocity.y,
    };
  }

  private emitAttack(
    input: InputState,
    time: number,
    kind: PlayerAttackPayload['kind'],
    damageMult: number,
    sizeMult: number,
    forceCrit: boolean,
    primed = false,
    combo: ComboStrike | null = null,
  ): PlayerAttackPayload {
    const aim = new Phaser.Math.Vector2(input.aimX - this.x, input.aimY - this.y);
    if (aim.lengthSq() > 0) aim.normalize();
    else aim.copy(this.facing);
    // 공격 애니는 조준 방향으로. 연격이면 그 타의 시트(없으면 attack)를 그 타 길이에, 아니면 다음 공격 가능 시점(쿨다운)에 맞춰
    const comboSheet = combo ? comboAction(gameState.weapon.id, combo.index + 1) : null;
    const action = comboSheet && this.visual.hasAction(comboSheet) ? comboSheet : 'attack';
    const fit = combo ? combo.durationMs : gameState.weapon.hitbox.cooldownMs;
    const aimDir = facingOf(aim.x, aim.y, this.visual.facing);
    // 조준 사격은 활 조준 시트의 발사 프레임 (없으면 기존 attack)
    if (!(kind === 'aimed' && this.poses.playAimRelease(aimDir, time))) this.visual.oneShot(action, aimDir, time, fit);
    // 연격 시트 JSON 메모: hitFrames[0] 시작 = 휘두름 시점, cancelFromFrame 시작 = 다음 타 허용
    const sheet = action !== 'attack' ? this.visual.sheet(action) : undefined;
    const hf = sheet?.hitFrames?.[0];
    if (typeof sheet?.cancelFromFrame === 'number')
      this.combo?.overrideCancel(this.visual.frameStartMs(sheet.cancelFromFrame));
    const payload: PlayerAttackPayload = {
      x: this.x,
      y: this.y,
      dirX: aim.x,
      dirY: aim.y,
      damageMult,
      sizeMult,
      kind,
      forceCrit,
      primed,
      swingDelayMs: hf !== undefined ? this.visual.frameStartMs(hf) : this.visual.lastImpactMs,
      releaseDelayMs: this.visual.frameStartMs(2),
      comboIndex: combo?.index,
      comboCount: combo?.count,
      activeMs: combo ? Math.max(combo.hit.activeMs, this.poses.activeWindowMs(sheet)) : undefined,
      durationMs: combo?.durationMs,
      bodyAction: action,
    };
    // 49라운드 과열: 가열 단계 (이펙트 강화)
    const res = this.gear.resource;
    if (res?.kind === 'heat') payload.heatStage = res.stage;
    EventBus.emit(Events.PLAYER_ATTACKED, payload);
    return payload;
  }

  /** 워프(45라운드): 진행 중 동작·넉백·달리기를 끊고 멈춘다 */
  haltForWarp(): void {
    if (this.action !== 'normal') this.setAction('normal', 0);
    this.lunge = null;
    this.stopUntil = 0;
    this.stopBlocksAct = false;
    this.visual.release();
    this.combo?.reset();
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

  /**
   * 적의 공격을 받는다. 패링 창이면 'parried'(피해 0), 무적이면 'ignored'.
   * 가드 중이면 피해 감소, 공격 중 슈퍼아머(거인)면 추가 감소. 사망하면 'dead'.
   * `source` 는 가해자 → 플레이어 방향 단위벡터(넉백 방향). 없으면 넉백 없음
   */
  takeHit(attack: number, time: number, source?: { dirX: number; dirY: number }): HitResult {
    if (gameState.gameOver) return 'ignored';
    if (this.action === 'parry') {
      // 성공: 창을 닫고 즉시 행동 가능
      this.setAction('normal', 0);
      this.flash(COLORS.PLAYER_PARRY);
      this.poses.playSpecial(time, 'parrySuccess');
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
      EventBus.emit(Events.PLAYER_SECONDARY, { kind: 'guard', phase: 'block' } satisfies PlayerSecondaryPayload);
    }
    if (mods.superArmorReduction && time < this.attackSlowUntil) {
      amount = Math.round(amount * (1 - mods.superArmorReduction));
    }
    gameState.hp = Math.max(0, gameState.hp - amount);
    this.flash(COLORS.PLAYER_HURT);
    if (source && this.action !== 'dash' && (source.dirX !== 0 || source.dirY !== 0)) {
      const K = FEEL.KNOCKBACK;
      const speed = knockSpeed(K.PLAYER_PX, K.PLAYER_MS);
      const len = Math.hypot(source.dirX, source.dirY) || 1;
      if (speed > 0)
        this.shoveState = {
          vx: (source.dirX / len) * speed,
          vy: (source.dirY / len) * speed,
          elapsed: 0,
          ms: K.PLAYER_MS,
        };
    }
    const payload: PlayerDamagedPayload = { hp: gameState.hp, maxHp: gameState.maxHp, amount, source };
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
