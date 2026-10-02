import Phaser from 'phaser';
import { COLORS, SPRITES, TILE } from '../core/Constants';
import {
  EventBus,
  Events,
  type BossAttackPayload,
  type BossPhasePayload,
  type BossTelegraphPayload,
  type BossWallHitPayload,
} from '../core/EventBus';
import { gameState } from '../core/GameState';
import { BOSSES } from '../data';
import type { BossDef, BossPhase } from '../data/types';
import { spriteLibrary } from '../systems/sprites';
import { facingOf, frameDurations, type Facing, type PhaseFrames } from '../systems/spriteDefs';
import { Mob, type MobContext } from './Mob';

type BossState = 'approach' | 'telegraph' | 'dash' | 'stun';

/**
 * 보스. 페이즈·패턴 수치는 data/bosses.json.
 * attack 시트에 `phaseFrames` 가 있으면(결정 로그 J) 예고 = frame 0 유지, 돌진 = 1↔2 반복,
 * 멈춤·벽 경직·부채꼴 = frame 3. 없으면 attack 애니를 통째로 재생한다.
 */
export class Boss extends Mob {
  readonly def: BossDef;
  readonly id: string;
  private phaseIndex = 0;
  private bossState: BossState = 'approach';
  private stateUntil = 0;
  private nextDashAt = 0;
  private nextFanAt = 0;
  private dashDir = new Phaser.Math.Vector2(1, 0);
  private dashesLeft = 0;

  constructor(scene: Phaser.Scene, x: number, y: number, id: string) {
    const def = BOSSES[id];
    if (!def) throw new Error(`[boss] 정의 없음: ${id}`);
    super(scene, x, y, id, def.size, def.color, def.hp);
    this.def = def;
    this.id = id;
    gameState.bossHp = this.hp;
    gameState.bossMaxHp = this.maxHp;
    gameState.bossPhase = 1;
  }

  get phase(): BossPhase {
    return this.def.phases[this.phaseIndex];
  }

  /** attack 시트의 국면 프레임 (없으면 null → 기존 attack 재생) */
  private get phaseFrames(): PhaseFrames | null {
    return spriteLibrary.sheet(this.id, 'attack')?.phaseFrames ?? null;
  }

  protected think(ctx: MobContext): void {
    if (this.isKnockedBack(ctx.time)) return;
    if (this.nextDashAt === 0) {
      this.nextDashAt = ctx.time + this.phase.dash.intervalMs;
      this.nextFanAt = ctx.time + (this.phase.fan?.intervalMs ?? 0);
    }
    if (this.isStunned(ctx.time)) {
      this.body.setVelocity(0, 0);
      gameState.bossHp = this.hp;
      return;
    }
    const P = this.phase;
    switch (this.bossState) {
      case 'approach':
        this.moveToward(ctx.player.x, ctx.player.y, this.def.approachSpeedTiles * TILE);
        if (ctx.time >= this.nextDashAt) {
          this.dashesLeft = (P.dash.repeat ?? 1) - 1;
          this.beginTelegraph(ctx, P.dash.telegraphMs, true);
        }
        if (P.fan && ctx.time >= this.nextFanAt) {
          this.fireFan(ctx);
          this.nextFanAt = ctx.time + P.fan.intervalMs;
        }
        break;
      case 'telegraph':
        if (ctx.time >= this.stateUntil) {
          this.dashDir.set(ctx.player.x - this.x, ctx.player.y - this.y).normalize();
          this.bossState = 'dash';
          this.stateUntil = ctx.time + P.dash.durationMs;
          this.restoreColor();
          this.showDash();
          EventBus.emit(Events.BOSS_ATTACK, { id: this.id, attack: 'dash' } satisfies BossAttackPayload);
        }
        break;
      case 'dash': {
        const s = P.dash.speedTiles * TILE;
        this.body.setVelocity(this.dashDir.x * s, this.dashDir.y * s);
        if (!this.body.blocked.none) {
          // 벽에 부딪힘 → 경직 (패턴 파훼 창)
          this.bossState = 'stun';
          this.stateUntil = ctx.time + P.dash.wallStunMs;
          this.body.setVelocity(0, 0);
          this.paint(COLORS.STUN);
          this.showRecover(ctx.time, P.dash.wallStunMs);
          this.scheduleNextDash(ctx.time);
          EventBus.emit(Events.BOSS_WALL_HIT, { id: this.id, x: this.x, y: this.y } satisfies BossWallHitPayload);
        } else if (ctx.time >= this.stateUntil) {
          this.body.setVelocity(0, 0);
          if (this.dashesLeft > 0) {
            // 연속 돌진: 짧은 예고 후 다시
            this.dashesLeft -= 1;
            this.beginTelegraph(ctx, P.dash.telegraphMs * 0.5, false);
          } else {
            this.bossState = 'approach';
            this.showRecover(ctx.time);
            this.scheduleNextDash(ctx.time);
            if (P.fan?.afterDash) this.fireFan(ctx);
          }
        }
        break;
      }
      case 'stun':
        this.body.setVelocity(0, 0);
        if (ctx.time >= this.stateUntil) {
          this.bossState = 'approach';
          this.visual.release();
          this.restoreColor();
          if (P.fan?.afterDash) this.fireFan(ctx);
        }
        break;
    }
    gameState.bossHp = this.hp;
  }

  get isBoss(): boolean {
    return true;
  }

  get personalityValue(): number {
    return this.def.personalityValue;
  }

  get goldValue(): number {
    return this.def.gold;
  }

  protected currentContactAttack(): number {
    return this.bossState === 'dash' ? this.phase.dash.attack : this.def.contactAttack;
  }

  protected contactIntervalMs(): number {
    return this.def.contactIntervalMs;
  }

  override takeDamage(amount: number, info: Parameters<Mob['takeDamage']>[1] = {}): boolean {
    const died = super.takeDamage(amount, info);
    if (!died) this.checkPhase();
    gameState.bossHp = Math.max(0, this.hp);
    return died;
  }

  protected onStunned(): void {
    // 패링 경직은 돌진을 끊는다
    this.bossState = 'approach';
    this.visual.release();
    this.scheduleNextDash(this.scene.time.now);
  }

  protected onDeath(): void {
    gameState.bossHp = 0;
    EventBus.emit(Events.BOSS_DIED, { id: this.id });
  }

  // --- 연출: 국면 프레임 ---

  private facingTo(x: number, y: number): Facing {
    return facingOf(x - this.x, y - this.y, this.visual.facing);
  }

  /** 예고 시작: frame 0 유지 (없으면 attack 전체를 예고+돌진 길이에 맞춰 재생). 첫 예고만 이벤트 */
  private beginTelegraph(ctx: MobContext, telegraphMs: number, emit: boolean): void {
    const P = this.phase;
    this.bossState = 'telegraph';
    this.stateUntil = ctx.time + telegraphMs;
    this.body.setVelocity(0, 0);
    this.paint(COLORS.TELEGRAPH);
    const pf = this.phaseFrames;
    const dir = this.facingTo(ctx.player.x, ctx.player.y);
    if (pf?.telegraph?.length) this.visual.hold('attack', dir, pf.telegraph[0], ctx.time);
    else if (emit) this.playAttack(ctx.time, telegraphMs + P.dash.durationMs);
    if (emit) EventBus.emit(Events.BOSS_TELEGRAPH, { id: this.id, attack: 'dash' } satisfies BossTelegraphPayload);
  }

  /** 돌진 중: frame 1↔2 반복 */
  private showDash(): void {
    const pf = this.phaseFrames;
    if (!pf?.dash?.length) return;
    const dir = facingOf(this.dashDir.x, this.dashDir.y, this.visual.facing);
    this.visual.loopFrames('attack', dir, pf.dash, SPRITES.BOSS_DASH_FRAME_MS);
  }

  /** 멈춤·벽 경직·부채꼴: frame 3 을 `ms`(기본값 = 그 프레임 길이) 동안 유지 */
  private showRecover(time: number, ms?: number): void {
    const pf = this.phaseFrames;
    const def = spriteLibrary.sheet(this.id, 'attack');
    if (!pf?.recover_or_fan?.length || !def) {
      this.visual.release();
      return;
    }
    const col = pf.recover_or_fan[0];
    this.visual.hold('attack', this.visual.facing, col, time, ms ?? frameDurations(def)[col] ?? 0);
  }

  private checkPhase(): void {
    const frac = this.hp / this.maxHp;
    let idx = 0;
    this.def.phases.forEach((p, i) => {
      if (frac <= p.hpFraction) idx = i;
    });
    if (idx !== this.phaseIndex) {
      this.phaseIndex = idx;
      gameState.bossPhase = idx + 1;
      const payload: BossPhasePayload = { phase: idx + 1, hp: this.hp, maxHp: this.maxHp };
      EventBus.emit(Events.BOSS_PHASE, payload);
      this.nextDashAt = 0; // 다음 update 에서 새 페이즈 간격으로 재설정
    }
  }

  private scheduleNextDash(time: number): void {
    this.nextDashAt = time + this.phase.dash.intervalMs;
  }

  private fireFan(ctx: MobContext): void {
    const F = this.phase.fan;
    if (!F) return;
    if (this.phaseFrames?.recover_or_fan?.length) {
      this.visual.facing = this.facingTo(ctx.player.x, ctx.player.y);
      this.showRecover(ctx.time);
    } else this.playAttack(ctx.time);
    EventBus.emit(Events.BOSS_ATTACK, { id: this.id, attack: 'fan' } satisfies BossAttackPayload);
    const base = Math.atan2(ctx.player.y - this.y, ctx.player.x - this.x);
    const spread = Phaser.Math.DegToRad(F.spreadDeg);
    for (let i = 0; i < F.count; i++) {
      const a = F.count === 1 ? base : base - spread / 2 + (spread * i) / (F.count - 1);
      ctx.fire(this.x, this.y, Math.cos(a), Math.sin(a), {
        speedPx: F.projectileSpeedTiles * TILE,
        attack: F.attack,
        size: F.projectileSize,
        lifeMs: F.projectileLifeMs,
      });
    }
  }
}
