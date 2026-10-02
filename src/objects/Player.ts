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
import type { SecondaryDef } from '../data/types';
import { applyDefense } from '../systems/Combat';
import type { InputState } from '../systems/InputSystem';
import {
  aimAction,
  comboAction,
  facingOf,
  frameDurations,
  progressFrame,
  specialAction,
  type Facing,
} from '../systems/spriteDefs';
import { ComboTracker } from '../systems/combo';
import type { ComboHitDef } from '../data/types';
import { knockFactor, knockSpeed } from '../systems/feel';
import { sprintStep } from '../systems/traversal';
import { EntityVisual, placeholderTexture } from './EntityVisual';
import { spriteLibrary } from '../systems/sprites';
import { WeaponOverlay } from './WeaponOverlay';

type Body = Phaser.Physics.Arcade.Body;

/** 48라운드 특수 자세 구간 */
type SpecialStep = 'parryStart' | 'parrySuccess' | 'parryFail' | 'guardStart' | 'guardRelease' | 'shadowArrive';

/** 유지형 보조 동작 자세를 매 프레임 이만큼 유지 (다음 프레임에 갱신) */
const SECONDARY_HOLD_MS = 80;

/** 시트 정의 (연격·특수 시트 JSON 메모 필드) */
function spriteLibrarySheet(visual: EntityVisual, action: string) {
  return spriteLibrary.sheet(visual.name, action);
}

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

  constructor(scene: Phaser.Scene, x: number, y: number) {
    const [w, h] = PLAYER_DATA.size;
    super(scene, x, y, placeholderTexture(scene, w, h));
    scene.add.existing(this);
    scene.physics.add.existing(this);
    this.visual = new EntityVisual(this, 'player', w, h, COLORS.PLAYER);
    this.overlay = new WeaponOverlay(this, () => this.visual.current);
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

    // 진행 중인 동작 종료 처리
    if (this.action !== 'normal' && this.actionUntil > 0 && time >= this.actionUntil) {
      if (this.action === 'dash') {
        this.dashEndedAt = time;
        this.body.setVelocity(0, 0);
        this.setAction('normal', 0);
      } else if (this.action === 'parry') {
        // 창이 닫혔는데 아무것도 못 막음 → 후딜
        EventBus.emit(Events.PLAYER_PARRY_FAILED);
        this.playSpecial(time, 'parryFail', P.failRecoveryMs);
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
      this.playSpecial(time, 'guardRelease', undefined, input);
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
        } else {
          EventBus.emit(Events.PLAYER_SECONDARY, {
            kind: 'aimedshot',
            phase: 'cancel',
          } satisfies PlayerSecondaryPayload);
        }
      }
    }

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
    if (this.action === 'dash') {
      this.body.setVelocity(this.dashVel.x, this.dashVel.y);
    } else if (sh) {
      // 피격 넉백: 조작 대신 감쇠 속도 (아주 짧음). 프레임 구간 중점 비율로 적분
      const f = sh.elapsed >= sh.ms ? 0 : knockFactor(sh.elapsed + delta / 2, sh.ms);
      sh.elapsed += delta;
      if (f <= 0) this.shoveState = null;
      this.body.setVelocity(sh.vx * f, sh.vy * f);
    } else {
      let slow = time < this.attackSlowUntil ? gameState.weapon.attackSlowMult : 1;
      if (this.action === 'guard' && S.kind === 'guard') slow = Math.min(slow, S.moveMult);
      if (this.action === 'aim' && S.kind === 'aimedshot') slow = Math.min(slow, S.moveMult);
      const speed = this.speedPx * slow * this.sprintFactor * this.envSpeedMult;
      this.body.setVelocity(dir.x * speed, dir.y * speed);
    }
    this.animateLocomotion(input, dir, time);
    this.holdSecondaryPose(input, time);

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
      this.combo?.reset();
      this.visual.oneShot('dash', facingOf(d.x, d.y, this.visual.facing), time, D.durationMs);
      EventBus.emit(Events.PLAYER_DASHED, { dirX: d.x, dirY: d.y, x: this.x, y: this.y });
      return;
    }

    // 보조 동작 (우클릭): 무기별
    if (input.secondaryPressed && canAct) {
      switch (S.kind) {
        case 'parry': {
          const win = P.windowMs * (1 + gameState.passives.total('parryWindowMult'));
          this.setAction('parry', time + win);
          this.playSpecial(time, 'parryStart', win, input);
          return;
        }
        case 'guard':
          this.setAction('guard', 0);
          this.playSpecial(time, 'guardStart', undefined, input);
          EventBus.emit(Events.PLAYER_SECONDARY, { kind: 'guard', phase: 'start' } satisfies PlayerSecondaryPayload);
          return;
        case 'aimedshot':
          if (time >= this.secondaryReadyAt) {
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
            this.playSpecial(time, 'shadowArrive', undefined, input);
          }
          return;
      }
    }

    // 공격 (대쉬 직후면 대쉬 공격). 48라운드: 근접은 3연격 상태 머신(입력 버퍼·다음 타 허용 창·리셋)
    const combo = this.combo;
    if (combo) {
      if (input.attackPressed) combo.press(time);
      const idx = combo.poll(time, canAct);
      if (idx !== null) {
        const hit = combo.hits[idx];
        this.attackSlowUntil = time + Math.max(hit.activeMs, PLAYER_DATA.attackSlowMinMs);
        this.fireAttack(input, time, { index: idx, count: combo.hits.length, hit });
      }
      return;
    }
    if (input.attackPressed && canAct && time >= this.attackReadyAt) {
      this.attackReadyAt = time + gameState.weapon.hitbox.cooldownMs;
      this.attackSlowUntil = time + Math.max(gameState.weapon.hitbox.activeMs, PLAYER_DATA.attackSlowMinMs);
      this.fireAttack(input, time, null);
    }
  }

  /** 공격 1회 (대쉬 공격·그림자 걸음 직후 확정 치명 판정 포함). combo 가 있으면 그 타의 배율·길이 */
  private fireAttack(
    input: InputState,
    time: number,
    combo: { index: number; count: number; hit: ComboHitDef } | null,
  ): void {
    const D = PLAYER_DATA.dash;
    const mods = gameState.weapon.mods;
    const isDashAttack = time - this.dashEndedAt <= D.attackWindowMs;
    let mult = combo ? combo.hit.damageMult : 1;
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
    const size = (isDashAttack ? D.attackSizeMult : 1) * (combo ? combo.hit.sizeMult : 1);
    this.emitAttack(input, time, isDashAttack ? 'dashAttack' : 'attack', mult, size, forceCrit, primed, combo);
  }

  /**
   * 48라운드 §6.2: 보조 동작 순간 무기를 든 자세 (`player_<무기>_special`). 시트가 없으면 아무것도 하지 않는다 (기존 틴트만).
   * 구간은 시트 JSON `phases` (없으면 기본 열): 패링 창 ready+window → 성공 riposte+recover / 실패 recover,
   * 가드 enter → (누르는 동안 loopFrames 반복) → 떼면 release+recover, 그림자 걸음 arrive+primed
   */
  private playSpecial(time: number, step: SpecialStep, fitMs?: number, input?: InputState): void {
    const action = specialAction(gameState.weapon.id);
    if (!this.visual.hasAction(action)) return;
    const def = spriteLibrarySheet(this.visual, action)!;
    const ph = (name: string, fallback: number[]) => {
      const v = (def.phases as Record<string, number[]> | undefined)?.[name];
      return Array.isArray(v) && v.length > 0 ? v : fallback;
    };
    const cols: Record<SpecialStep, number[]> = {
      parryStart: [...ph('ready', [0]), ...ph('window', [1, 2])],
      parrySuccess: [...ph('riposte', [3]), ...ph('recover', [4])],
      parryFail: ph('recover', [def.frames - 1]),
      guardStart: ph('enter', [0]),
      guardRelease: [...ph('release', [3, 4]), ...ph('recover', [5])],
      shadowArrive: [...ph('arrive', [2, 3]), ...ph('primed', [4])],
    };
    const dir = input ? facingOf(input.aimX - this.x, input.aimY - this.y, this.visual.facing) : this.visual.facing;
    this.visual.playFrames(action, dir, cols[step], time, fitMs);
  }

  /** 유지형 보조 동작 자세: 가드 = 특수 자세 loopFrames 반복, 조준 = 활 조준 시트의 진행도 프레임 (min(5, floor(p×5))) */
  private holdSecondaryPose(input: InputState, time: number): void {
    const id = gameState.weapon.id;
    const dir = facingOf(input.aimX - this.x, input.aimY - this.y, this.visual.facing);
    if (this.action === 'aim') {
      const action = aimAction(id);
      if (!this.visual.hasAction(action)) return;
      const def = spriteLibrarySheet(this.visual, action)!;
      const prog = def.progressFrames ?? [0, 1, 2, 3, 4, 5];
      const f = prog[progressFrame(this.aimProgress(time), prog.length, FEEL.SECONDARY.AIM_CHARGE_DIVISOR)] ?? 0;
      this.visual.hold(action, dir, f, time, SECONDARY_HOLD_MS);
    } else if (this.action === 'guard') {
      const action = specialAction(id);
      if (!this.visual.hasAction(action) || this.visual.isBusy(time)) return;
      const def = spriteLibrarySheet(this.visual, action)!;
      const loop = def.loopFrames ?? [1, 2];
      const d = frameDurations(def);
      if (!this.visual.current?.includes(`#p${loop.join('-')}`) || this.visual.facing !== dir)
        this.visual.loopFrames(action, dir, loop, d[loop[0]] ?? 160);
    }
  }

  /** 연격 시트 activeFrames 구간 길이 ms (첫 열 시작 ~ 마지막 열 끝, 재생 배속 반영). 없으면 0 */
  private activeWindowMs(sheet: { activeFrames?: number[]; frames: number } | undefined): number {
    const af = sheet?.activeFrames;
    if (!af || af.length === 0) return 0;
    const first = Math.min(...af);
    const last = Math.max(...af);
    const starts = this.visual.lastFrameStarts;
    const end = last + 1 < sheet.frames ? starts[last + 1] : this.visual.lastDurationMs;
    return Math.max(0, (end ?? 0) - (starts[first] ?? 0));
  }

  /** 조준 사격 발사 순간: 활 조준 시트의 발사 프레임(releaseFrame) 1회. 시트가 없으면 false */
  private playAimRelease(dir: Facing, time: number): boolean {
    const action = aimAction(gameState.weapon.id);
    if (!this.visual.hasAction(action)) return false;
    const def = spriteLibrarySheet(this.visual, action)!;
    this.visual.release();
    return this.visual.playFrames(action, dir, [def.releaseFrame ?? def.frames - 1], time) > 0;
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
    primed = false,
    combo: { index: number; count: number; hit: ComboHitDef } | null = null,
  ): void {
    const aim = new Phaser.Math.Vector2(input.aimX - this.x, input.aimY - this.y);
    if (aim.lengthSq() > 0) aim.normalize();
    else aim.copy(this.facing);
    // 공격 애니는 조준 방향으로. 연격이면 그 타의 시트(없으면 attack)를 그 타 길이에, 아니면 다음 공격 가능 시점(쿨다운)에 맞춰
    const comboSheet = combo ? comboAction(gameState.weapon.id, combo.index + 1) : null;
    const action = comboSheet && this.visual.hasAction(comboSheet) ? comboSheet : 'attack';
    const fit = combo ? combo.hit.durationMs : gameState.weapon.hitbox.cooldownMs;
    const aimDir = facingOf(aim.x, aim.y, this.visual.facing);
    // 조준 사격은 활 조준 시트의 발사 프레임 (없으면 기존 attack)
    if (!(kind === 'aimed' && this.playAimRelease(aimDir, time))) this.visual.oneShot(action, aimDir, time, fit);
    // 연격 시트 JSON 메모: hitFrames[0] 시작 = 휘두름 시점, cancelFromFrame 시작 = 다음 타 허용
    const sheet = action !== 'attack' ? spriteLibrarySheet(this.visual, action) : undefined;
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
      activeMs: combo ? Math.max(combo.hit.activeMs, this.activeWindowMs(sheet)) : undefined,
      durationMs: combo?.hit.durationMs,
      bodyAction: action,
    };
    EventBus.emit(Events.PLAYER_ATTACKED, payload);
  }

  /** 워프(45라운드): 진행 중 동작·넉백·달리기를 끊고 멈춘다 */
  haltForWarp(): void {
    if (this.action !== 'normal') this.setAction('normal', 0);
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
      this.playSpecial(time, 'parrySuccess');
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
