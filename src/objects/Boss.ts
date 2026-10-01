import Phaser from 'phaser';
import { COLORS, TILE } from '../core/Constants';
import { EventBus, Events, type BossPhasePayload } from '../core/EventBus';
import { gameState } from '../core/GameState';
import { BOSSES } from '../data';
import type { BossDef, BossPhase } from '../data/types';
import { Mob, type MobContext } from './Mob';

type BossState = 'approach' | 'telegraph' | 'dash' | 'stun';

/** 1층 보스 플레이스홀더. 페이즈·패턴 수치는 data/bosses.json. */
export class Boss extends Mob {
  readonly def: BossDef;
  readonly id: string;
  private phaseIndex = 0;
  private bossState: BossState = 'approach';
  private stateUntil = 0;
  private nextDashAt = 0;
  private nextFanAt = 0;
  private dashDir = new Phaser.Math.Vector2(1, 0);

  constructor(scene: Phaser.Scene, x: number, y: number, id: string) {
    const def = BOSSES[id];
    if (!def) throw new Error(`[boss] 정의 없음: ${id}`);
    super(scene, x, y, def.size, def.color, def.hp);
    this.def = def;
    this.id = id;
    gameState.bossHp = this.hp;
    gameState.bossMaxHp = this.maxHp;
    gameState.bossPhase = 1;
  }

  get phase(): BossPhase {
    return this.def.phases[this.phaseIndex];
  }

  update(ctx: MobContext): void {
    if (!this.active) return;
    if (this.nextDashAt === 0) {
      this.nextDashAt = ctx.time + this.phase.dash.intervalMs;
      this.nextFanAt = ctx.time + (this.phase.fan?.intervalMs ?? 0);
    }
    const P = this.phase;
    switch (this.bossState) {
      case 'approach':
        this.moveToward(ctx.player.x, ctx.player.y, this.def.approachSpeedTiles * TILE);
        if (ctx.time >= this.nextDashAt) {
          this.bossState = 'telegraph';
          this.stateUntil = ctx.time + P.dash.telegraphMs;
          this.body.setVelocity(0, 0);
          this.setFillStyle(COLORS.TELEGRAPH);
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
          this.setFillStyle(COLORS.STUN);
          this.scheduleNextDash(ctx.time);
        } else if (ctx.time >= this.stateUntil) {
          this.bossState = 'approach';
          this.body.setVelocity(0, 0);
          this.scheduleNextDash(ctx.time);
          if (P.fan?.afterDash) this.fireFan(ctx);
        }
        break;
      }
      case 'stun':
        this.body.setVelocity(0, 0);
        if (ctx.time >= this.stateUntil) {
          this.bossState = 'approach';
          this.restoreColor();
          if (P.fan?.afterDash) this.fireFan(ctx);
        }
        break;
    }
    gameState.bossHp = this.hp;
  }

  protected currentContactAttack(): number {
    return this.bossState === 'dash' ? this.phase.dash.attack : this.def.contactAttack;
  }

  protected contactIntervalMs(): number {
    return this.def.contactIntervalMs;
  }

  override takeDamage(amount: number): boolean {
    const died = super.takeDamage(amount);
    if (!died) this.checkPhase();
    gameState.bossHp = Math.max(0, this.hp);
    return died;
  }

  protected onDeath(): void {
    gameState.bossHp = 0;
    EventBus.emit(Events.BOSS_DIED, { id: this.id });
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
