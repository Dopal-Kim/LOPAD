import Phaser from 'phaser';
import { COLORS, ENEMY_FX, SPRITES, TILE } from '../core/Constants';
import {
  EventBus,
  Events,
  type BossAttackPayload,
  type BossPattern,
  type BossPhasePayload,
  type BossTelegraphPayload,
  type BossWallHitPayload,
} from '../core/EventBus';
import { gameState } from '../core/GameState';
import { BOSSES } from '../data';
import type { BossDef, BossPhase } from '../data/types';
import { Rng, hashSeed } from '../systems/rng';
import { spriteLibrary } from '../systems/sprites';
import { facingOf, frameDurations, type Facing, type PhaseFrames } from '../systems/spriteDefs';
import type { TelegraphHandle } from '../systems/telegraph';
import { Mob, type MobContext } from './Mob';

type BossState =
  | 'approach'
  | 'telegraph'
  | 'dash'
  | 'stun'
  | 'fanTelegraph'
  | 'slamTelegraph'
  | 'volleyTelegraph'
  | 'volley'
  | 'recover';

/**
 * 보스. 페이즈·패턴 수치는 data/bosses.json.
 * 35라운드 2단계: 패턴 4종(돌진·부채꼴·내리찍기·소환 / 황제는 정렬 사격) 을 페이즈별 `patterns` 목록에서 시드 RNG 로 고른다.
 * 모든 예고는 바닥 마커(선·원·부채꼴)와 `BOSS_TELEGRAPH`, 실행은 `BOSS_ATTACK` 을 발행한다.
 * attack 시트에 `phaseFrames` 가 있으면(결정 로그 J) 돌진 예고 = frame 0 유지, 돌진 = 1↔2 반복,
 * 멈춤·벽 경직·부채꼴·내리찍기·정렬 사격 예고 = frame 3. 없으면 attack 애니를 통째로 재생한다.
 */
export class Boss extends Mob {
  readonly def: BossDef;
  readonly id: string;
  private phaseIndex = 0;
  private bossState: BossState = 'approach';
  private stateUntil = 0;
  private nextPatternAt = 0;
  /** 패턴별 다음 사용 가능 시각 */
  private readonly readyAt = new Map<BossPattern, number>();
  private dashDir = new Phaser.Math.Vector2(1, 0);
  private dashesLeft = 0;
  private marker: TelegraphHandle | null = null;
  /** 내리찍기 목표 / 정렬 사격 방향·남은 발 */
  private slamTarget = new Phaser.Math.Vector2();
  private volleyDir = new Phaser.Math.Vector2(1, 0);
  private volleyLeft = 0;
  private volleyNextAt = 0;
  private readonly rng: Rng;
  /** 디버그: 사용한 패턴 기록·소환 수 */
  readonly patternLog: BossPattern[] = [];
  summoned = 0;
  private currentPattern: BossPattern | null = null;

  constructor(scene: Phaser.Scene, x: number, y: number, id: string) {
    const def = BOSSES[id];
    if (!def) throw new Error(`[boss] 정의 없음: ${id}`);
    super(scene, x, y, id, def.size, def.color, def.hp);
    this.def = def;
    this.id = id;
    this.rng = new Rng(hashSeed(`${gameState.floorSeed}:boss:${id}`));
    gameState.bossHp = this.hp;
    gameState.bossMaxHp = this.maxHp;
    gameState.bossPhase = 1;
    this.once(Phaser.GameObjects.Events.DESTROY, () => this.clearMarker());
  }

  get phase(): BossPhase {
    return this.def.phases[this.phaseIndex];
  }

  /** 디버그 */
  get patternState(): string {
    return this.bossState;
  }

  get pattern(): BossPattern | null {
    return this.currentPattern;
  }

  /** attack 시트의 국면 프레임 (없으면 null → 기존 attack 재생) */
  private get phaseFrames(): PhaseFrames | null {
    return spriteLibrary.sheet(this.id, 'attack')?.phaseFrames ?? null;
  }

  /** 이 페이즈의 패턴 후보 (없으면 돌진 + 부채꼴) */
  private patternsOf(P: BossPhase): BossPattern[] {
    if (P.patterns?.length) return P.patterns;
    return P.fan ? ['dash', 'fan'] : ['dash'];
  }

  protected think(ctx: MobContext): void {
    if (this.isKnockedBack(ctx.time)) return;
    if (this.nextPatternAt === 0) this.scheduleNext(ctx.time);
    if (this.isStunned(ctx.time)) {
      this.body.setVelocity(0, 0);
      gameState.bossHp = this.hp;
      return;
    }
    const P = this.phase;
    switch (this.bossState) {
      case 'approach':
        this.moveToward(ctx.player.x, ctx.player.y, this.def.approachSpeedTiles * TILE);
        if (ctx.time >= this.nextPatternAt) this.begin(this.choosePattern(ctx), ctx);
        break;
      case 'telegraph':
        this.marker?.aim(this.body.center.x, this.body.center.y, this.angleTo(ctx.player.x, ctx.player.y));
        if (ctx.time >= this.stateUntil) {
          this.clearMarker();
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
          this.scheduleNext(ctx.time);
          EventBus.emit(Events.BOSS_WALL_HIT, { id: this.id, x: this.x, y: this.y } satisfies BossWallHitPayload);
        } else if (ctx.time >= this.stateUntil) {
          this.body.setVelocity(0, 0);
          if (this.dashesLeft > 0) {
            // 연속 돌진: 짧은 예고 후 다시
            this.dashesLeft -= 1;
            this.beginTelegraph(ctx, P.dash.telegraphMs * 0.5, false);
          } else {
            this.showRecover(ctx.time);
            this.finishPattern(ctx.time);
            this.afterDash(ctx);
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
          this.afterDash(ctx);
        }
        break;
      case 'fanTelegraph':
        this.body.setVelocity(0, 0);
        this.marker?.aim(this.body.center.x, this.body.center.y, this.angleTo(ctx.player.x, ctx.player.y));
        if (ctx.time >= this.stateUntil) {
          this.clearMarker();
          this.fireFan(ctx);
          this.finishPattern(ctx.time);
        }
        break;
      case 'slamTelegraph':
        this.body.setVelocity(0, 0);
        if (ctx.time >= this.stateUntil) {
          this.clearMarker();
          const S = this.def.slam!;
          ctx.areaHit(this.slamTarget.x, this.slamTarget.y, S.radiusTiles * TILE, S.attack);
          EventBus.emit(Events.BOSS_ATTACK, { id: this.id, attack: 'slam' } satisfies BossAttackPayload);
          this.showRecover(ctx.time);
          this.finishPattern(ctx.time);
        }
        break;
      case 'volleyTelegraph':
        this.body.setVelocity(0, 0);
        this.marker?.aim(this.body.center.x, this.body.center.y, this.angleTo(ctx.player.x, ctx.player.y));
        if (ctx.time >= this.stateUntil) {
          this.clearMarker();
          this.volleyDir.set(ctx.player.x - this.body.center.x, ctx.player.y - this.body.center.y).normalize();
          this.volleyLeft = this.def.volley!.count;
          this.volleyNextAt = ctx.time;
          this.bossState = 'volley';
          EventBus.emit(Events.BOSS_ATTACK, { id: this.id, attack: 'volley' } satisfies BossAttackPayload);
        }
        break;
      case 'volley': {
        this.body.setVelocity(0, 0);
        const V = this.def.volley!;
        if (ctx.time >= this.volleyNextAt && this.volleyLeft > 0) {
          this.volleyLeft -= 1;
          this.volleyNextAt = ctx.time + V.shotGapMs;
          const c = this.body.center;
          ctx.fire(c.x, c.y, this.volleyDir.x, this.volleyDir.y, {
            speedPx: V.projectileSpeedTiles * TILE,
            attack: V.attack,
            size: V.projectileSize,
            lifeMs: V.projectileLifeMs,
            sprite: V.sprite,
          });
        }
        if (this.volleyLeft <= 0) this.finishPattern(ctx.time);
        break;
      }
      case 'recover':
        this.body.setVelocity(0, 0);
        if (ctx.time >= this.stateUntil) this.finishPattern(ctx.time);
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
    // 패링 경직은 진행 중인 패턴을 끊는다
    this.clearMarker();
    this.bossState = 'approach';
    this.currentPattern = null;
    this.visual.release();
    this.scheduleNext(this.scene.time.now);
  }

  protected onDeath(): void {
    this.clearMarker();
    gameState.bossHp = 0;
    EventBus.emit(Events.BOSS_DIED, { id: this.id });
  }

  // --- 패턴 선택·시작·종료 ---

  /** 후보 중 쿨타임·조건이 맞는 것에서 시드 RNG 로 고른다. 아무것도 못 쓰면 돌진 */
  private choosePattern(ctx: MobContext): BossPattern {
    const ready = this.patternsOf(this.phase).filter((p) => this.isReady(p, ctx));
    if (ready.length === 0) return 'dash';
    return this.rng.pick(ready);
  }

  private isReady(p: BossPattern, ctx: MobContext): boolean {
    if (ctx.time < (this.readyAt.get(p) ?? 0)) return false;
    switch (p) {
      case 'dash':
        return true;
      case 'fan':
        return Boolean(this.phase.fan);
      case 'slam':
        return Boolean(this.def.slam);
      case 'summon': {
        const S = this.def.summon;
        return Boolean(S) && ctx.countMobs(S!.enemy) < S!.max;
      }
      case 'volley':
        return Boolean(this.def.volley);
    }
  }

  private begin(p: BossPattern, ctx: MobContext): void {
    this.currentPattern = p;
    this.patternLog.push(p);
    const P = this.phase;
    switch (p) {
      case 'dash':
        this.dashesLeft = (P.dash.repeat ?? 1) - 1;
        this.beginTelegraph(ctx, P.dash.telegraphMs, true);
        break;
      case 'fan':
        this.beginFan(ctx);
        break;
      case 'slam':
        this.beginSlam(ctx);
        break;
      case 'summon':
        this.doSummon(ctx);
        break;
      case 'volley':
        this.beginVolley(ctx);
        break;
    }
  }

  /** 패턴 끝: 쿨타임 기록, 접근으로, 다음 패턴 예약 */
  private finishPattern(time: number): void {
    const p = this.currentPattern;
    if (p) this.readyAt.set(p, time + this.cooldownOf(p));
    this.currentPattern = null;
    this.bossState = 'approach';
    this.scheduleNext(time);
  }

  private cooldownOf(p: BossPattern): number {
    switch (p) {
      case 'dash':
        return 0;
      case 'fan':
        return this.phase.fan?.intervalMs ?? 0;
      case 'slam':
        return this.def.slam?.cooldownMs ?? 0;
      case 'summon':
        return this.def.summon?.cooldownMs ?? 0;
      case 'volley':
        return this.def.volley?.cooldownMs ?? 0;
    }
  }

  private scheduleNext(time: number): void {
    const P = this.phase;
    this.nextPatternAt = time + (P.patternIntervalMs ?? P.dash.intervalMs);
  }

  /** 돌진이 끝난 뒤 부채꼴 연계 (fan.afterDash, 쿨타임이 끝났을 때만) */
  private afterDash(ctx: MobContext): void {
    const F = this.phase.fan;
    if (!F?.afterDash || ctx.time < (this.readyAt.get('fan') ?? 0)) return;
    this.currentPattern = 'fan';
    this.patternLog.push('fan');
    this.beginFan(ctx);
  }

  // --- 돌진 ---

  private angleTo(x: number, y: number): number {
    const c = this.body.center;
    return Math.atan2(y - c.y, x - c.x);
  }

  private facingTo(x: number, y: number): Facing {
    return facingOf(x - this.x, y - this.y, this.visual.facing);
  }

  /** 예고 시작: frame 0 유지 (없으면 attack 전체를 예고+돌진 길이에 맞춰 재생) + 경로 예고선. 첫 예고만 이벤트 */
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
    const c = this.body.center;
    const lengthPx = (P.dash.speedTiles * TILE * P.dash.durationMs) / 1000;
    this.clearMarker();
    this.marker = ctx.telegraph.line(c.x, c.y, this.angleTo(ctx.player.x, ctx.player.y), lengthPx, telegraphMs);
    if (emit) EventBus.emit(Events.BOSS_TELEGRAPH, { id: this.id, attack: 'dash' } satisfies BossTelegraphPayload);
  }

  /** 돌진 중: frame 1↔2 반복 */
  private showDash(): void {
    const pf = this.phaseFrames;
    if (!pf?.dash?.length) return;
    const dir = facingOf(this.dashDir.x, this.dashDir.y, this.visual.facing);
    this.visual.loopFrames('attack', dir, pf.dash, SPRITES.BOSS_DASH_FRAME_MS);
  }

  /** 멈춤·벽 경직·부채꼴·내리찍기: frame 3 을 `ms`(기본값 = 그 프레임 길이) 동안 유지 */
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

  /** 예고 자세: 플레이어를 보며 frame 3 유지(없으면 attack 재생). ms 가 없으면 그 프레임 길이만큼 */
  private holdFacing(ctx: MobContext, ms?: number): void {
    if (this.phaseFrames?.recover_or_fan?.length) {
      this.visual.facing = this.facingTo(ctx.player.x, ctx.player.y);
      this.showRecover(ctx.time, ms);
    } else this.playAttack(ctx.time, ms);
  }

  // --- 부채꼴 ---

  private beginFan(ctx: MobContext): void {
    const F = this.phase.fan!;
    const tele = F.telegraphMs ?? 0;
    if (tele <= 0) {
      this.fireFan(ctx);
      this.finishPattern(ctx.time);
      return;
    }
    this.bossState = 'fanTelegraph';
    this.stateUntil = ctx.time + tele;
    this.body.setVelocity(0, 0);
    this.holdFacing(ctx, tele);
    const c = this.body.center;
    const half = Phaser.Math.DegToRad(F.spreadDeg / 2);
    this.clearMarker();
    this.marker = ctx.telegraph.cone(
      c.x,
      c.y,
      this.angleTo(ctx.player.x, ctx.player.y),
      half,
      (F.telegraphTiles ?? 5) * TILE,
      tele,
    );
    EventBus.emit(Events.BOSS_TELEGRAPH, { id: this.id, attack: 'fan' } satisfies BossTelegraphPayload);
  }

  private fireFan(ctx: MobContext): void {
    const F = this.phase.fan;
    if (!F) return;
    this.holdFacing(ctx);
    EventBus.emit(Events.BOSS_ATTACK, { id: this.id, attack: 'fan' } satisfies BossAttackPayload);
    const c = this.body.center;
    const base = Math.atan2(ctx.player.y - c.y, ctx.player.x - c.x);
    const spread = Phaser.Math.DegToRad(F.spreadDeg);
    for (let i = 0; i < F.count; i++) {
      const a = F.count === 1 ? base : base - spread / 2 + (spread * i) / (F.count - 1);
      ctx.fire(c.x, c.y, Math.cos(a), Math.sin(a), {
        speedPx: F.projectileSpeedTiles * TILE,
        attack: F.attack,
        size: F.projectileSize,
        lifeMs: F.projectileLifeMs,
        sprite: F.sprite,
      });
    }
    this.readyAt.set('fan', ctx.time + F.intervalMs);
  }

  // --- 내리찍기 ---

  private beginSlam(ctx: MobContext): void {
    const S = this.def.slam!;
    this.bossState = 'slamTelegraph';
    this.stateUntil = ctx.time + S.telegraphMs;
    this.body.setVelocity(0, 0);
    this.slamTarget.set(ctx.player.x, ctx.player.y);
    this.holdFacing(ctx, S.telegraphMs);
    this.clearMarker();
    this.marker = ctx.telegraph.circle(this.slamTarget.x, this.slamTarget.y, S.radiusTiles * TILE, S.telegraphMs);
    EventBus.emit(Events.BOSS_TELEGRAPH, { id: this.id, attack: 'slam' } satisfies BossTelegraphPayload);
  }

  // --- 소환 ---

  private doSummon(ctx: MobContext): void {
    const S = this.def.summon!;
    const room = Math.max(0, S.max - ctx.countMobs(S.enemy));
    const n = Math.min(S.count, room);
    const gap = this.body.halfWidth + ENEMY_FX.SUMMON_GAP_PX;
    let placed = 0;
    for (let i = 0; i < n; i++) {
      const side = i % 2 === 0 ? -1 : 1;
      const ring = 1 + Math.floor(i / 2);
      if (ctx.summon(S.enemy, this.x + side * gap * ring, this.y)) placed++;
    }
    EventBus.emit(Events.BOSS_ATTACK, { id: this.id, attack: 'summon' } satisfies BossAttackPayload);
    const def = spriteLibrary.sheet(this.id, 'attack');
    const col = this.phaseFrames?.recover_or_fan?.[0];
    const holdMs = def && col !== undefined ? (frameDurations(def)[col] ?? 0) : 0;
    this.holdFacing(ctx);
    this.bossState = 'recover';
    this.stateUntil = ctx.time + Math.max(holdMs, SPRITES.BOSS_DASH_FRAME_MS);
    this.summoned += placed;
  }

  // --- 정렬 사격 (황제) ---

  private beginVolley(ctx: MobContext): void {
    const V = this.def.volley!;
    this.bossState = 'volleyTelegraph';
    this.stateUntil = ctx.time + V.telegraphMs;
    this.body.setVelocity(0, 0);
    this.holdFacing(ctx, V.telegraphMs);
    const c = this.body.center;
    this.clearMarker();
    this.marker = ctx.telegraph.line(
      c.x,
      c.y,
      this.angleTo(ctx.player.x, ctx.player.y),
      V.telegraphTiles * TILE,
      V.telegraphMs,
    );
    EventBus.emit(Events.BOSS_TELEGRAPH, { id: this.id, attack: 'volley' } satisfies BossTelegraphPayload);
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
      this.nextPatternAt = 0; // 다음 update 에서 새 페이즈 간격으로 재설정
    }
  }

  private clearMarker(): void {
    this.marker?.end();
    this.marker = null;
  }
}
