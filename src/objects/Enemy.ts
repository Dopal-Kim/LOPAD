import Phaser from 'phaser';
import { COLORS, DEPTH, ENEMY_FX, TILE, entityDepth } from '../core/Constants';
import {
  EventBus,
  type EnemyDiedPayload,
  Events,
  type EnemyAttackPayload,
  type EnemyBehaviorPayload,
  type EnemyTelegraphPayload,
} from '../core/EventBus';
import { ENEMIES } from '../data';
import type { EnemyDef, EnemyScale } from '../data/types';
import type { TelegraphHandle } from '../systems/telegraph';
import { anchorOffset } from '../systems/sprites/spriteMeta';
import type { Facing } from '../systems/sprites/spriteDefs';
import { Mob, type MobContext } from './Mob';

type ChargeState = 'approach' | 'telegraph' | 'dash' | 'cooldown';
type RangedState = 'move' | 'aim' | 'reload';

/**
 * 일반 적. 행동은 data/enemies.json 의 behavior 로 결정.
 * 35라운드 2단계: 결사병 돌진 예고선·방패 막기, 사수 조준선·총구 화염·재장전, 징집병 집단 돌격.
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
  /** 활성 예고 마커 (돌진 경로·조준선) */
  private marker: TelegraphHandle | null = null;
  /** 집단 돌격: 마지막으로 이벤트를 낸 발동 시각 */
  private packEmittedAt = -Infinity;
  private packActive = false;

  private readonly stageScale: EnemyScale;

  constructor(scene: Phaser.Scene, x: number, y: number, id: string, scale: EnemyScale = { hp: 1, attack: 1 }) {
    const def = ENEMIES[id];
    if (!def) throw new Error(`[enemy] 정의 없음: ${id}`);
    super(scene, x, y, id, def.size, def.color, Math.round(def.hp * scale.hp));
    this.def = def;
    this.id = id;
    this.stageScale = scale;
    this.once(Phaser.GameObjects.Events.DESTROY, () => this.clearMarker());
  }

  /** 스테이지 배율이 적용된 공격력 */
  private atk(base: number): number {
    return Math.round(base * this.stageScale.attack);
  }

  /** 디버그: 행동 상태 */
  get behaviorState(): string {
    if (this.def.behavior === 'charge') return this.chargeState;
    if (this.def.behavior === 'ranged') return this.rangedState;
    return this.packActive ? 'pack' : 'chase';
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

  protected currentContactAttack(): number {
    if (this.def.behavior === 'charge' && this.def.charge) {
      return this.atk(this.chargeState === 'dash' ? this.def.charge.dashAttack : this.def.charge.idleAttack);
    }
    return this.atk(this.def.attack);
  }

  protected contactIntervalMs(): number {
    return this.def.attackIntervalMs;
  }

  protected onDeath(): void {
    this.clearMarker();
    EventBus.emit(Events.ENEMY_DIED, { id: this.id, elite: this.elite !== null } satisfies EnemyDiedPayload);
  }

  protected onStunned(): void {
    this.clearMarker();
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
    this.moveToward(ctx.player.x, ctx.player.y, speed);
  }

  // --- 사수: 거리 유지 → 조준선 → 발사(총구 화염·탄) → n발 뒤 재장전(후퇴) ---

  private updateRanged(ctx: MobContext): void {
    const R = this.def.ranged!;
    const dist = Phaser.Math.Distance.Between(this.x, this.y, ctx.player.x, ctx.player.y);
    const speed = this.def.speedTiles * TILE;
    const away = () => new Phaser.Math.Vector2(this.x - ctx.player.x, this.y - ctx.player.y).normalize().scale(speed);

    if (this.rangedState === 'reload') {
      // 재장전: 사격 없이 뒤로 물러난다 (애니는 걷기/대기 그대로)
      const v = away().scale(R.reload?.retreatSpeedMult ?? 1);
      this.body.setVelocity(v.x, v.y);
      if (ctx.time >= this.rangedUntil) {
        this.rangedState = 'move';
        this.shotsFired = 0;
        this.nextShotAt = ctx.time + (this.def.attackIntervalMs * 0.5) / Math.max(0.1, this.attackRateMult);
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
      }
      return;
    }

    if (dist < R.keepMinTiles * TILE) {
      const v = away();
      this.body.setVelocity(v.x, v.y);
    } else if (dist > R.keepMaxTiles * TILE) {
      this.moveToward(ctx.player.x, ctx.player.y, speed);
    } else {
      this.body.setVelocity(0, 0);
    }
    if (ctx.time >= this.nextShotAt && dist <= R.keepMaxTiles * TILE * 1.5) {
      this.nextShotAt = ctx.time + this.def.attackIntervalMs / Math.max(0.1, this.attackRateMult);
      const tele = R.telegraphMs ?? 0;
      if (tele > 0) {
        this.rangedState = 'aim';
        this.rangedUntil = ctx.time + tele;
        this.body.setVelocity(0, 0);
        const a = Math.atan2(ctx.player.y - this.y, ctx.player.x - this.x);
        const c = this.body.center;
        this.marker = ctx.telegraph.line(c.x, c.y, a, (R.telegraphTiles ?? 3) * TILE, tele);
        EventBus.emit(Events.ENEMY_TELEGRAPH, { id: this.id, kind: 'shot' } satisfies EnemyTelegraphPayload);
      } else this.shoot(ctx);
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
          this.chargeState = 'telegraph';
          this.chargeUntil = ctx.time + C.telegraphMs;
          this.body.setVelocity(0, 0);
          this.paint(COLORS.TELEGRAPH);
          this.playAttack(ctx.time, C.telegraphMs + C.dashMs);
          // 돌진 경로 예고선: 길이 = 돌진 거리, 방향은 예고 끝까지 플레이어를 따라간다
          const c = this.body.center;
          const a = Math.atan2(ctx.player.y - this.y, ctx.player.x - this.x);
          this.marker = ctx.telegraph.line(c.x, c.y, a, this.dashDistancePx(), C.telegraphMs, { aura: true });
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
      case 'dash':
        this.body.setVelocity(this.dashDir.x * C.dashSpeedTiles * TILE, this.dashDir.y * C.dashSpeedTiles * TILE);
        if (ctx.time >= this.chargeUntil || this.body.blocked.none === false) {
          this.chargeState = 'cooldown';
          this.chargeUntil = ctx.time + C.cooldownMs;
          this.body.setVelocity(0, 0);
        }
        break;
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
