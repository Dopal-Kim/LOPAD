import Phaser from 'phaser';
import { COLORS, DEPTH, ENEMY_FX, ENEMY_SQUAD, TILE, entityDepth, type TelegraphTier } from '../core/Constants';
import {
  EventBus,
  type EnemyDiedPayload,
  Events,
  type EnemyAttackPayload,
  type EnemyBehaviorPayload,
  type EnemyStaggeredPayload,
  type EnemyTelegraphPayload,
} from '../core/EventBus';
import { ENEMIES } from '../data';
import type { EnemyDef, EnemyScale } from '../data/types';
import type { TelegraphHandle } from '../systems/telegraph';
import { anchorOffset } from '../systems/sprites/spriteMeta';
import type { Facing } from '../systems/sprites/spriteDefs';
import { Mob, type MobContext } from './Mob';
import { PeddlerBrain, PorterBrain, type BrainBody } from './enemy/hazardBrains';
import { BombBrain, DrumBrain, MeleeSwing, SwarmBrain } from './enemy/squadBrains';
import type { MobSquad } from '../systems/squad';
import type { EnemyHazardApi } from '../systems/hazards/enemyHazardTypes';

type ChargeState = 'approach' | 'telegraph' | 'dash' | 'cooldown';
type RangedState = 'move' | 'aim' | 'reload';

/**
 * 일반 적. 행동은 data/enemies.json 의 behavior 로 결정.
 * 35라운드 2단계: 결사병 돌진 예고선·방패 막기, 사수 조준선·총구 화염·재장전, 징집병 집단 돌격.
 * P19 (계약 free-combat §2): 접촉 피해 없음 — 예고·공격은 공격 토큰(MobContext.squad)을 받아야 시작한다.
 * 징집병 포위·휘두르기(SwarmBrain) · 사수 근접 밀치기 · 결사병 벽에 박히면 스스로 기절 · 깃발 고수 · 술배 자폭병.
 */
export class Enemy extends Mob {
  readonly def: EnemyDef;
  readonly id: string;
  private nextShotAt = 0;
  private chargeState: ChargeState = 'approach';
  private chargeUntil = 0;
  private dashDir = new Phaser.Math.Vector2(1, 0);
  /** 사수: 조준 → 발사 → (n발 뒤) 재장전 */
  private rangedState: RangedState = 'move';
  private rangedUntil = 0;
  private shotsFired = 0;
  /** P19 사수: 토큰이 없을 때 옆으로 흘러가는 쪽 (막히면 뒤집는다) */
  private strafe: 1 | -1;
  /** 활성 예고 마커 (돌진 경로·조준선) */
  private marker: TelegraphHandle | null = null;
  /** 집단 돌격: 마지막으로 이벤트를 낸 발동 시각 */
  private packEmittedAt = -Infinity;
  private packActive = false;

  private readonly stageScale: EnemyScale;
  /** 61라운드 단계 2: 독주 행상·술통 짐꾼 행동 · P19 깃발 고수·술배 자폭병 (그 밖의 적은 null) */
  private readonly brain: PeddlerBrain | PorterBrain | DrumBrain | BombBrain | null;
  /** P19 징집병 포위·휘두르기 · 사수 근접 밀치기 */
  private readonly swarm: SwarmBrain | null;
  private readonly closeSwing: MeleeSwing | null;
  /** P19 마지막으로 받은 무리 조율 (토큰 반납·북 배율) */
  private squad: MobSquad | null = null;
  /** 마지막으로 받은 위험물 창구 (쓰러질 때 술 웅덩이) */
  private hazards: EnemyHazardApi | null = null;

  constructor(scene: Phaser.Scene, x: number, y: number, id: string, scale: EnemyScale = { hp: 1, attack: 1 }) {
    const def = ENEMIES[id];
    if (!def) throw new Error(`[enemy] 정의 없음: ${id}`);
    super(scene, x, y, id, def.size, def.color, Math.round(def.hp * scale.hp));
    this.def = def;
    this.id = id;
    this.stageScale = scale;
    // P19 버팀 (정예 배율은 reactions.effectivePoise)
    this.poise = def.poise ?? 0;
    const body = this.brainBody();
    this.brain =
      def.behavior === 'throw'
        ? new PeddlerBrain(body)
        : def.behavior === 'roll'
          ? new PorterBrain(body)
          : def.behavior === 'drum' && def.drum
            ? new DrumBrain(body, def.drum, scene)
            : def.behavior === 'bomb' && def.bomb
              ? new BombBrain(body, def.bomb)
              : null;
    this.swarm = def.behavior === 'chase' && def.swing ? new SwarmBrain(body, def.swing) : null;
    this.closeSwing = def.behavior === 'ranged' && def.swing ? new MeleeSwing(body, def.swing) : null;
    this.strafe = Math.floor(x) % 2 === 0 ? 1 : -1;
    this.once(Phaser.GameObjects.Events.DESTROY, () => {
      this.clearMarker();
      this.brain?.interrupt(0);
      this.squad?.release(this);
      if (this.brain instanceof DrumBrain) this.brain.destroy();
    });
  }

  /** 스테이지 배율이 적용된 공격력 */
  private atk(base: number): number {
    return Math.round(base * this.stageScale.attack);
  }

  /** 61라운드 단계 2 행동이 몸에 요구하는 것 */
  private brainBody(): BrainBody {
    // eslint-disable-next-line @typescript-eslint/no-this-alias
    const self = this;
    return {
      get x() {
        return self.x;
      },
      get y() {
        return self.y;
      },
      get body() {
        return self.body;
      },
      get visual() {
        return self.visual;
      },
      get def() {
        return self.def;
      },
      get attackRateMult() {
        return self.rate;
      },
      get active() {
        return self.active;
      },
      get elite() {
        return self.elite !== null;
      },
      self,
      id: self.id,
      attackScale: () => self.stageScale.attack,
      moveTo: (x, y, speed) => self.moveToward(x, y, speed),
      attackAnim: (time, fitMs) => self.playAttack(time, fitMs),
      paint: (color) => self.paint(color),
      restore: () => self.restoreColor(),
    };
  }

  /** P19 공격 속도 배율 = 엘리트 접두어 × 깃발 고수 북 */
  private get rate(): number {
    return this.attackRateMult * (this.squad?.drumMult(this.x, this.y, this.scene.time.now) ?? 1);
  }

  /** P19 공격 토큰 (squad 가 없으면 늘 받음) */
  private takeToken(ctx: MobContext): boolean {
    return ctx.squad ? ctx.squad.take(this, this.id, this.elite !== null) : true;
  }

  /** 디버그: 행동 상태 */
  get behaviorState(): string {
    if (this.brain) return this.brain.state;
    if (this.def.behavior === 'charge') return this.chargeState;
    if (this.def.behavior === 'ranged') return this.closeSwing?.busy ? this.closeSwing.phase : this.rangedState;
    if (this.swarm) return this.swarm.state;
    return this.packActive ? 'pack' : 'chase';
  }

  /** P19 예고·공격 중인 위협 단계 (계약 free-combat §2·§4) */
  override get threat(): TelegraphTier | null {
    if (this.brain) return this.brain.threat;
    if (this.swarm) return this.swarm.threat;
    if (this.closeSwing?.busy) return 'warn';
    if (this.def.behavior === 'charge')
      return this.chargeState === 'telegraph' || this.chargeState === 'dash' ? 'warn' : null;
    if (this.def.behavior === 'ranged') return this.rangedState === 'aim' ? 'ranged' : null;
    return null;
  }

  /** 62 루프 4 소매치기: 돌진 예고 · 조준선 · 술병·술통 들어 올림 */
  override get windingUp(): boolean {
    if (this.brain) return this.brain.state === 'windup' || this.brain.state === 'fuse';
    if (this.swarm) return this.swarm.state === 'windup';
    return this.chargeState === 'telegraph' || this.rangedState === 'aim' || this.closeSwing?.phase === 'windup';
  }

  get shotsSinceReload(): number {
    return this.shotsFired;
  }

  protected think(ctx: MobContext): void {
    if (this.isKnockedBack(ctx.time)) return;
    if (this.isStunned(ctx.time)) {
      this.body.setVelocity(0, 0);
      return;
    }
    this.hazards = ctx.hazards ?? null;
    this.squad = ctx.squad ?? null;
    // 62 루프 4 맨손: 공격 없이 주인공에게서 물러선다
    if (this.isDisarmed(ctx.time)) {
      const v = new Phaser.Math.Vector2(this.x - ctx.player.x, this.y - ctx.player.y)
        .normalize()
        .scale(this.def.speedTiles * TILE);
      this.body.setVelocity(v.x, v.y);
      return;
    }
    if (this.brain) {
      this.brain.think(ctx);
      return;
    }
    switch (this.def.behavior) {
      case 'chase':
        this.updateChase(ctx);
        break;
      case 'ranged':
        this.updateRanged(ctx);
        break;
      case 'charge':
        this.updateCharge(ctx);
        break;
    }
  }

  get isBoss(): boolean {
    return false;
  }

  get personalityValue(): number {
    return this.def.personalityValue;
  }

  get goldValue(): number {
    return this.def.gold;
  }

  /** P19 접촉 피해 없음: 결사병 돌진 중만 몸이 공격이다 */
  protected currentContactAttack(): number {
    return this.def.charge && this.chargeState === 'dash' ? this.atk(this.def.charge.dashAttack) : 0;
  }

  protected contactIntervalMs(): number {
    return this.def.attackIntervalMs;
  }

  protected onDeath(): void {
    this.clearMarker();
    this.brain?.interrupt(this.scene.time.now);
    // P19 술배 자폭병: 쓰러진 자리에서 잠시 뒤 터진다 (스스로 터졌으면 없음)
    if (this.brain instanceof BombBrain) this.brain.onDeath(this.scene);
    // 61라운드 단계 2: 독주 행상·술통 짐꾼은 쓰러진 자리에 술 웅덩이 (불이 닿으면 술불)
    const P = this.def.deathPool;
    if (P && this.def.liquor && this.hazards)
      this.hazards.liquorPool(this.x, this.y, P.radiusTiles * TILE, P.ms, this.def.liquor, this.stageScale.attack);
    EventBus.emit(Events.ENEMY_DIED, { id: this.id, elite: this.elite !== null } satisfies EnemyDiedPayload);
  }

  /** P19: 결사병 돌진 중에는 움찔하지 않는다 (돌진은 벽에 박혀야 멈춘다) */
  override canStagger(time: number): boolean {
    return super.canStagger(time) && !(this.def.behavior === 'charge' && this.chargeState === 'dash');
  }

  /** P19 2단계: 휘두르기 예고 중 버팀 (data swing.windupPoise — 몸 번쩍임 = 버팀, 약한 타로는 예고가 끊기지 않는다) */
  override poiseAgainst(dirX: number, dirY: number): number {
    const base = super.poiseAgainst(dirX, dirY);
    const w = this.def.swing?.windupPoise;
    return w && this.windingUp ? Math.max(base, w) : base;
  }

  /** P19 술배 자폭병: 맞으면 불이 붙는다 (날아간 자리에서 터진다) */
  override takeDamage(amount: number, info: Parameters<Mob['takeDamage']>[1] = {}): boolean {
    const died = super.takeDamage(amount, info);
    if (!died && !info.tick && this.brain instanceof BombBrain) this.brain.onHit();
    return died;
  }

  protected onStunned(): void {
    this.clearMarker();
    const now = this.scene.time.now;
    this.brain?.interrupt(now);
    // P19: 징집병은 짧은 움찔이면 토큰을 쥔 채 다시 붙는다 (경직·맨손·띄움이면 내려놓는다)
    const flinchOnly = !this.isStunned(now) && !this.isDisarmed(now) && !this.airborne;
    const keep = this.swarm?.interrupt(now, flinchOnly) ?? false;
    this.closeSwing?.interrupt();
    // P19: 끊긴 공격의 토큰을 반납 (자폭병의 불붙은 심지는 꺼지지 않는다 — 토큰도 그대로)
    if (!keep && !(this.brain instanceof BombBrain && this.brain.phase === 'fuse')) this.squad?.release(this);
    if (this.def.behavior === 'charge') this.chargeState = 'approach';
    if (this.def.behavior === 'ranged' && this.rangedState === 'aim') this.rangedState = 'move';
  }

  /**
   * 방패 막기: 정면 `frontDeg`(전체 각) 안에서 오는 공격만. `dir` 은 공격 진행 방향(공격자 → 나)이므로
   * 공격자는 -dir 쪽에 있다. 돌진 중엔 돌진 방향이 정면. 경직 중엔 막지 않는다
   */
  override guardReduction(dirX: number, dirY: number, time: number): number {
    const S = this.def.shield;
    if (!S || this.isStunned(time)) return 0;
    const len = Math.hypot(dirX, dirY);
    if (len === 0) return 0;
    const f = this.chargeState === 'dash' ? { x: this.dashDir.x, y: this.dashDir.y } : this.facingVector();
    // 공격자 방향(-dir) 과 정면의 각
    const cos = (-dirX / len) * f.x + (-dirY / len) * f.y;
    const half = Phaser.Math.DegToRad(S.frontDeg / 2);
    if (cos < Math.cos(half)) return 0;
    EventBus.emit(Events.ENEMY_BEHAVIOR, { id: this.id, kind: 'block' } satisfies EnemyBehaviorPayload);
    return S.reduction;
  }

  // --- 징집병: 추격 + 집단 돌격 ---

  private updateChase(ctx: MobContext): void {
    let speed = this.def.speedTiles * TILE;
    const P = this.def.pack;
    if (P) {
      const dist = Phaser.Math.Distance.Between(this.x, this.y, ctx.player.x, ctx.player.y) / TILE;
      const active = ctx.pack.report(this.id, P, ctx.countMobs(this.id), dist, ctx.time);
      if (active) {
        speed *= P.speedMult;
        const started = ctx.pack.startedAt(this.id, P);
        if (started > this.packEmittedAt) {
          this.packEmittedAt = started;
          EventBus.emit(Events.ENEMY_BEHAVIOR, { id: this.id, kind: 'pack' } satisfies EnemyBehaviorPayload);
        }
      }
      this.packActive = active;
    }
    if (this.swarm) this.swarm.think(ctx, speed);
    else this.moveToward(ctx.player.x, ctx.player.y, speed);
  }

  // --- 사수: 거리 유지 → 조준선 → 발사(총구 화염·탄) → n발 뒤 재장전(후퇴) ---

  private updateRanged(ctx: MobContext): void {
    const R = this.def.ranged!;
    const dist = Phaser.Math.Distance.Between(this.x, this.y, ctx.player.x, ctx.player.y);
    const speed = this.def.speedTiles * TILE;
    const away = () => new Phaser.Math.Vector2(this.x - ctx.player.x, this.y - ctx.player.y).normalize().scale(speed);

    // P19 근접 밀치기: 붙은 주인공을 뒷걸음치며 밀친다 (토큰)
    const S = this.closeSwing;
    if (S && !S.busy && this.rangedState === 'move' && S.inReach(ctx) && this.takeToken(ctx)) S.start(ctx);
    if (S?.busy) {
      if (S.update(ctx)) this.squad?.release(this);
      return;
    }

    if (this.rangedState === 'reload') {
      // 재장전: 사격 없이 뒤로 물러난다 (애니는 걷기/대기 그대로)
      const v = away().scale(R.reload?.retreatSpeedMult ?? 1);
      this.body.setVelocity(v.x, v.y);
      if (ctx.time >= this.rangedUntil) {
        this.rangedState = 'move';
        this.shotsFired = 0;
        this.nextShotAt = ctx.time + (this.def.attackIntervalMs * 0.5) / Math.max(0.1, this.rate);
      }
      return;
    }

    if (this.rangedState === 'aim') {
      // 조준: 멈춰서 조준선이 플레이어를 따라간다
      this.body.setVelocity(0, 0);
      const a = Math.atan2(ctx.player.y - this.y, ctx.player.x - this.x);
      this.marker?.aim(this.body.center.x, this.body.center.y, a);
      if (ctx.time >= this.rangedUntil) {
        this.clearMarker();
        this.rangedState = 'move';
        this.shoot(ctx);
        this.squad?.release(this);
      }
      return;
    }

    if (dist < R.keepMinTiles * TILE) {
      const v = away();
      this.body.setVelocity(v.x, v.y);
    } else if (dist > R.keepMaxTiles * TILE) {
      this.moveToward(ctx.player.x, ctx.player.y, speed);
    } else {
      // P19: 거리 안에서는 옆으로 흘러간다 (서서 기다리지 않는다)
      if (!this.body.blocked.none) this.strafe = this.strafe === 1 ? -1 : 1;
      const v = away().normalize();
      const k = speed * 0.5 * this.strafe;
      this.body.setVelocity(-v.y * k, v.x * k);
    }
    if (ctx.time >= this.nextShotAt && dist <= R.keepMaxTiles * TILE * 1.5) {
      if (!this.takeToken(ctx)) {
        this.nextShotAt = ctx.time + ENEMY_SQUAD.RETRY_MS;
        return;
      }
      this.nextShotAt = ctx.time + this.def.attackIntervalMs / Math.max(0.1, this.rate);
      const tele = R.telegraphMs ?? 0;
      if (tele > 0) {
        this.rangedState = 'aim';
        this.rangedUntil = ctx.time + tele;
        this.body.setVelocity(0, 0);
        const a = Math.atan2(ctx.player.y - this.y, ctx.player.x - this.x);
        const c = this.body.center;
        this.marker = ctx.telegraph.line(c.x, c.y, a, (R.telegraphTiles ?? 3) * TILE, tele, { tier: 'ranged' });
        EventBus.emit(Events.ENEMY_TELEGRAPH, { id: this.id, kind: 'shot' } satisfies EnemyTelegraphPayload);
      } else {
        this.shoot(ctx);
        this.squad?.release(this);
      }
    }
  }

  /** 발사: attack 애니 → 총구 화염 프레임(2번째)에 총구 화염 + 탄 생성. 사격 수를 세어 재장전으로 */
  private shoot(ctx: MobContext): void {
    const R = this.def.ranged!;
    this.playAttack(ctx.time);
    const spec = {
      speedPx: R.projectileSpeedTiles * TILE,
      attack: this.atk(this.def.attack),
      size: R.projectileSize,
      lifeMs: R.projectileLifeMs,
      sprite: R.sprite,
    };
    const fire = () => {
      if (!this.active) return;
      const c = this.body.center;
      const dir = new Phaser.Math.Vector2(ctx.player.x - c.x, ctx.player.y - c.y).normalize();
      // 총구 = 바디 중심에서 바라보는 방향으로 전방·살짝 위 (아트 JSON pivotNote)
      const facing = this.visual.facing;
      const fx = facing === 'left' ? -1 : facing === 'right' ? 1 : 0;
      const fy = facing === 'up' ? -1 : facing === 'down' ? 1 : 0;
      const mx = c.x + fx * ENEMY_FX.MUZZLE_FORWARD_PX;
      const my = c.y + fy * ENEMY_FX.MUZZLE_FORWARD_PX - ENEMY_FX.MUZZLE_UP_PX;
      // 53라운드 적 v3: 총구 화염은 시트 총구 자리(muzzleAnchors, 발사 프레임)에 — 탄 생성점(판정)은 그대로
      const flash = this.muzzleAt(facing) ?? { x: mx, y: my };
      if (R.muzzle)
        ctx.playFx(R.muzzle, flash.x, flash.y, { dir: facing, depth: entityDepth(this.y) + DEPTH.OVERLAY_STEP * 3 });
      ctx.fire(mx, my, dir.x, dir.y, spec);
      EventBus.emit(Events.ENEMY_ATTACK, { id: this.id, kind: 'shot' } satisfies EnemyAttackPayload);
    };
    const delay = this.visual.impactDelayMs('attack');
    if (delay > 0) this.scene.time.delayedCall(delay, fire);
    else fire();
    this.shotsFired += 1;
    const RL = R.reload;
    if (RL && this.shotsFired >= RL.shots) {
      this.rangedState = 'reload';
      this.rangedUntil = ctx.time + Math.max(delay, 0) + RL.reloadMs;
      EventBus.emit(Events.ENEMY_BEHAVIOR, { id: this.id, kind: 'reload' } satisfies EnemyBehaviorPayload);
    }
  }

  /** 53라운드 적 v3: 발사 프레임의 총구 월드 좌표 (시트에 muzzleAnchors 가 없으면 null) */
  private muzzleAt(facing: Facing): { x: number; y: number } | null {
    const def = this.visual.sheet('attack');
    const f = def?.fireFrame;
    const p = def && typeof f === 'number' ? def.muzzleAnchors?.[facing]?.[f] : null;
    if (!def || !p) return null;
    const o = anchorOffset(def, p);
    return { x: this.x + o.x, y: this.y + o.y };
  }

  // --- 결사병: 접근 → 예고(경로선) → 돌진 → 재정비 ---

  private updateCharge(ctx: MobContext): void {
    const C = this.def.charge!;
    const dist = Phaser.Math.Distance.Between(this.x, this.y, ctx.player.x, ctx.player.y);
    switch (this.chargeState) {
      case 'approach':
        this.moveToward(ctx.player.x, ctx.player.y, this.def.speedTiles * TILE);
        if (dist <= C.triggerTiles * TILE) {
          // P19 공격 토큰: 못 받으면 돌진 거리에서 버티고 선다
          if (!this.takeToken(ctx)) {
            this.body.setVelocity(0, 0);
            break;
          }
          this.chargeState = 'telegraph';
          this.chargeUntil = ctx.time + C.telegraphMs;
          this.body.setVelocity(0, 0);
          this.paint(COLORS.TELEGRAPH);
          this.playAttack(ctx.time, C.telegraphMs + C.dashMs);
          // 돌진 경로 예고선: 길이 = 돌진 거리, 방향은 예고 끝까지 플레이어를 따라간다
          const c = this.body.center;
          const a = Math.atan2(ctx.player.y - this.y, ctx.player.x - this.x);
          this.marker = ctx.telegraph.line(c.x, c.y, a, this.dashDistancePx(), C.telegraphMs, {
            aura: true,
            tier: 'warn',
          });
          EventBus.emit(Events.ENEMY_TELEGRAPH, { id: this.id, kind: 'dash' } satisfies EnemyTelegraphPayload);
        }
        break;
      case 'telegraph':
        this.marker?.aim(
          this.body.center.x,
          this.body.center.y,
          Math.atan2(ctx.player.y - this.y, ctx.player.x - this.x),
        );
        if (ctx.time >= this.chargeUntil) {
          this.clearMarker();
          this.dashDir.set(ctx.player.x - this.x, ctx.player.y - this.y).normalize();
          this.chargeState = 'dash';
          this.chargeUntil = ctx.time + C.dashMs;
          this.restoreColor();
          EventBus.emit(Events.ENEMY_ATTACK, { id: this.id, kind: 'dash' } satisfies EnemyAttackPayload);
        }
        break;
      case 'dash': {
        this.body.setVelocity(this.dashDir.x * C.dashSpeedTiles * TILE, this.dashDir.y * C.dashSpeedTiles * TILE);
        const wall = this.body.blocked.none === false;
        if (ctx.time >= this.chargeUntil || wall) {
          this.squad?.release(this);
          this.chargeState = 'cooldown';
          this.chargeUntil = ctx.time + C.cooldownMs;
          this.body.setVelocity(0, 0);
          // P19: 벽·엄폐에 박히면 스스로 기절 (벽꽝 교재)
          if (wall && C.wallStunMs) {
            this.stun(ctx.time, C.wallStunMs, 'hit');
            EventBus.emit(Events.ENEMY_STAGGERED, {
              id: this.id,
              x: this.x,
              y: this.y,
              kind: 'stagger',
              ms: C.wallStunMs,
            } satisfies EnemyStaggeredPayload);
          }
        }
        break;
      }
      case 'cooldown':
        this.body.setVelocity(0, 0);
        if (ctx.time >= this.chargeUntil) this.chargeState = 'approach';
        break;
    }
  }

  /** 돌진 거리 px = 속도 × 시간 */
  private dashDistancePx(): number {
    const C = this.def.charge!;
    return (C.dashSpeedTiles * TILE * C.dashMs) / 1000;
  }

  private clearMarker(): void {
    this.marker?.end();
    this.marker = null;
  }
}
