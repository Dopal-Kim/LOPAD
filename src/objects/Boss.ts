import Phaser from 'phaser';
import { TILE } from '../core/Constants';
import {
  EventBus,
  Events,
  type BossActionKind,
  type BossActionPayload,
  type BossAttackPayload,
  type BossLoopKind,
  type BossLoopPayload,
  type BossPhasePayload,
  type BossTelegraphPayload,
  type BossWallHitPayload,
} from '../core/EventBus';
import { gameState } from '../core/GameState';
import { BOSSES } from '../data';
import type { BossPatternName, PatternParams } from '../data/bossPatterns';
import type { BossDef, BossPhase } from '../data/types';
import { bossQuery } from '../debug/bossQuery';
import { Rng, hashSeed } from '../systems/rng';
import { spriteLibrary } from '../systems/sprites/sprites';
import { artScale } from '../systems/sprites/spriteDefs';
import { bossBodySize } from './boss/bodySize';
import { BossBrain, type BossBody } from './boss/BossBrain';
import { BossPose } from './boss/bossPose';
import type { BossHost, PatternEnd, Vec } from './boss/types';
import { Mob, type DamageInfo, type MobContext } from './Mob';

/**
 * 보스. 페이즈·패턴 수치는 data/bosses.json (54라운드 Q4: `patterns.<이름>` 로 통일).
 * 54라운드 정리: 패턴 고르기·예약·쿨타임은 `boss/BossBrain`, 패턴별 동작은 `boss/patterns/*` 모듈(레지스트리 `boss/registry`),
 * 몸 연출은 `boss/bossPose`. 이 클래스는 Phaser 몸(물리·시트)·이벤트 발행·경직·무적을 맡는 얇은 접착부다.
 * 모든 예고는 바닥 마커와 `BOSS_TELEGRAPH`, 실행은 `BOSS_ATTACK`, 패턴 안 국면은 `BOSS_ACTION`(음향 훅).
 */
export class Boss extends Mob implements BossHost, BossBody {
  readonly def: BossDef;
  readonly id: string;
  readonly rng: Rng;
  readonly pose: BossPose;
  private readonly brain: BossBrain;
  /** 디버그: 소환 수 */
  summoned = 0;
  /** 페이즈 전환 들이켜기 동안 피해 무시 (54라운드 임시값) */
  private invulnerableUntil = 0;
  /** 61라운드 등장 연출 동안: 패턴·이동·접촉 공격 없음, 피해 무시 (BossFlow 가 깨운다) */
  private dormant = false;
  /** 61라운드 P6: 파훼로 무너진 동안 (이 시각까지 받는 피해 × breakDamageMult) */
  private brokenUntil = 0;
  /** 지금 파훼 창이 시작된 시각 (UI 게이지 전체 길이) */
  private brokenFrom = 0;
  private readonly posVec = { x: 0, y: 0 };
  private readonly centerVec = { x: 0, y: 0 };

  constructor(scene: Phaser.Scene, x: number, y: number, id: string) {
    const def = BOSSES[id];
    if (!def) throw new Error(`[boss] 정의 없음: ${id}`);
    // 54라운드 Q13~Q16: v3 그림이 있으면 판정 크기를 그림 크기에 비례 (bodyFromArt, 없으면 data size)
    // 61라운드 점검 #6: 그림·판정을 renderScale 배로 (시트 그대로 확대)
    const k = def.renderScale ?? 1;
    const idle = spriteLibrary.sheet(id, 'idle');
    const body = bossBodySize(
      def.size,
      def.bodyFromArt,
      idle ? { frameWidth: idle.frameWidth, frameHeight: idle.frameHeight, scale: artScale(idle) * k } : null,
    );
    super(scene, x, y, id, body, def.color, def.hp);
    if (k !== 1) this.visual.setDrawScale(k);
    this.def = def;
    this.id = id;
    this.rng = new Rng(hashSeed(`${gameState.floorSeed}:boss:${id}`));
    this.pose = new BossPose(this, this.visual, id);
    this.brain = new BossBrain(def, this, this);
    // 54라운드 디버그: ?bossPhase=n (HP 를 그 페이즈 시작 값으로) · ?bossPattern=a,b (그 순서로 되풀이)
    const q = bossQuery();
    if (q.phase !== null && q.phase > 1) {
      const idx = Math.min(def.phases.length - 1, q.phase - 1);
      this.hp = Math.max(1, Math.floor(this.maxHp * def.phases[idx].hpFraction));
      this.brain.setPhase(idx);
    }
    if (q.patterns) this.brain.force(q.patterns);
    gameState.bossHp = this.hp;
    gameState.bossMaxHp = this.maxHp;
    gameState.bossPhase = this.brain.phaseIndex + 1;
    this.once(Phaser.GameObjects.Events.DESTROY, () => this.brain.destroy());
  }

  get phase(): BossPhase {
    return this.brain.phase;
  }

  get phaseIndex(): number {
    return this.brain.phaseIndex;
  }

  /** 디버그 */
  get patternState(): string {
    return this.brain.state;
  }

  get pattern(): BossPatternName | null {
    return this.brain.current;
  }

  get patternLog(): BossPatternName[] {
    return this.brain.log;
  }

  /** 디버그: 다음 패턴 강화 대기 · 지금 판 강화 · 강제 목록 · 무적 */
  get debugInfo(): Record<string, unknown> {
    return {
      phase: this.brain.phaseIndex + 1,
      phaseName: this.phase.name ?? null,
      state: this.brain.state,
      pattern: this.brain.current,
      empowerPending: this.brain.empowered,
      runEmpowered: this.brain.runEmpowered,
      dormant: this.dormant,
      brokenLeftMs: this.brokenLeftMs,
      forced: this.brain.forcedList,
      nextPatternAt: this.brain.nextPatternAt,
      invulnerable: this.isImmune(this.scene.time.now),
      log: [...this.brain.log],
    };
  }

  /** 디버그: 판정·그림 기하 (54라운드 보스 v3 192×240·피벗 확인) */
  get debugGeom(): Record<string, unknown> {
    const b = this.body;
    return {
      now: this.scene.time.now,
      pos: { x: this.x, y: this.y },
      body: { x: b.x, y: b.y, w: b.width, h: b.height, cx: b.center.x, cy: b.center.y },
      sprite: {
        texture: this.texture.key,
        frame: this.frame.name,
        originX: this.originX,
        originY: this.originY,
        scale: this.scaleX,
        w: this.displayWidth,
        h: this.displayHeight,
        top: this.y - this.displayOriginY * this.scaleY,
        rotation: this.rotation,
      },
      anim: {
        key: this.anims.currentAnim?.key ?? null,
        playing: this.anims.isPlaying,
        timeScale: this.anims.timeScale,
        held: this.visual.held,
        busy: this.visual.isBusy(this.scene.time.now),
      },
      shadow: this.visual.shadowInfo,
      hitLift: this.visual.hitLiftPx,
    };
  }

  /** 디버그: 다음 패턴 강제 (목록 순서대로 되풀이, null 이면 해제) · 지금 바로 시작 */
  debugForce(list: BossPatternName[] | null, now = false): void {
    this.brain.force(list);
    if (now && list?.length) this.brain.nextPatternAt = 1;
  }

  /** 디버그: 페이즈 강제 (HP 를 그 페이즈 시작 값으로 내린다 — 진입 연출 포함) */
  debugPhase(n: number): void {
    const idx = Math.max(0, Math.min(this.def.phases.length - 1, n - 1));
    const target = Math.max(1, Math.floor(this.maxHp * this.def.phases[idx].hpFraction));
    if (target < this.hp) this.takeDamage(this.hp - target);
  }

  /** 61라운드 등장 연출: 잠재우기 (BossFlow — BOSS_STARTED 처리기에서 바로) */
  setDormant(on: boolean): void {
    this.dormant = on;
    if (on) this.body.setVelocity(0, 0);
  }

  get isDormant(): boolean {
    return this.dormant;
  }

  /** 61라운드: 전투 시작 — 첫 패턴은 지금 + 국면 간격. 디버그로 2국면 이상에서 시작했으면 국면 곡·카드를 맞춘다 */
  wake(now: number): void {
    if (!this.dormant) return;
    this.dormant = false;
    this.brain.scheduleNext(now);
    if (this.brain.phaseIndex > 0) this.emitPhase(this.brain.phaseIndex);
  }

  protected think(ctx: MobContext): void {
    if (this.dormant) {
      this.body.setVelocity(0, 0);
      return;
    }
    if (this.isKnockedBack(ctx.time)) return;
    if (this.brain.nextPatternAt === 0) this.brain.scheduleNext(ctx.time);
    if (this.isStunned(ctx.time)) {
      this.body.setVelocity(0, 0);
      gameState.bossHp = this.hp;
      return;
    }
    this.brain.update(ctx);
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
    return this.brain.contactAttack();
  }

  protected contactIntervalMs(): number {
    return this.def.contactIntervalMs;
  }

  /** 넘어져 있는 동안(접촉 공격력 0)·등장 연출 동안은 접촉 공격 자체를 하지 않는다 */
  override tryContactAttack(time: number): number {
    if (this.dormant || this.brain.contactAttack() <= 0) return 0;
    return super.tryContactAttack(time);
  }

  override isImmune(time: number): boolean {
    return this.dormant || time < this.invulnerableUntil;
  }

  /** 61라운드 P6: 파훼로 무너진 동안 받는 피해 × breakDamageMult (엘리트 배율과 곱) */
  override damageTakenMultAt(now: number): number {
    const base = super.damageTakenMultAt(now);
    return now < this.brokenUntil ? base * (this.def.breakDamageMult ?? 1) : base;
  }

  markBroken(ms: number): void {
    const now = this.scene.time.now;
    if (now + ms <= this.brokenUntil) return;
    if (now >= this.brokenUntil) this.brokenFrom = now;
    this.brokenUntil = now + ms;
  }

  /** 61라운드 계약 §17: 파훼 창 (UI 스냅샷 boss.broken) — 아니면 null */
  brokenWindow(now: number): { leftMs: number; totalMs: number } | null {
    if (now >= this.brokenUntil) return null;
    return { leftMs: Math.round(this.brokenUntil - now), totalMs: Math.round(this.brokenUntil - this.brokenFrom) };
  }

  /** 디버그: 파훼 피해 창이 남은 ms */
  get brokenLeftMs(): number {
    return Math.max(0, Math.round(this.brokenUntil - this.scene.time.now));
  }

  override takeDamage(amount: number, info: DamageInfo = {}): boolean {
    if (this.isImmune(this.scene.time.now)) return false;
    const died = super.takeDamage(amount, info);
    if (!died && this.brain.checkPhase(this.hp / this.maxHp)) gameState.bossPhase = this.brain.phaseIndex + 1;
    gameState.bossHp = Math.max(0, this.hp);
    return died;
  }

  protected onStunned(): void {
    // 패링 경직(·잔 깨짐 경직)은 진행 중인 패턴을 끊는다
    this.brain.onStunned(this.scene.time.now);
  }

  protected onDeath(): void {
    this.brain.destroy();
    gameState.bossHp = 0;
    EventBus.emit(Events.BOSS_DIED, { id: this.id });
  }

  // =====================================================================
  // BossBody (두뇌 → 몸)
  // =====================================================================

  approach(ctx: MobContext): void {
    this.moveToward(ctx.player.x, ctx.player.y, this.def.approachSpeedTiles * TILE);
  }

  stunSelf(time: number, ms: number, pose?: PatternEnd['stunPose']): void {
    this.stun(time, ms, 'hit');
    if (pose && !this.pose.phase(pose.action, pose.phase, time, { thenLoop: pose.thenLoop })) this.pose.lean(-0.18);
    this.scene.time.delayedCall(ms, () => {
      if (this.active && !this.isStunned(this.scene.time.now)) {
        this.pose.lean(0);
        this.pose.release();
      }
    });
  }

  releasePose(): void {
    this.pose.lean(0);
    this.pose.release();
  }

  emitPhase(index: number): void {
    const payload: BossPhasePayload = { phase: index + 1, hp: this.hp, maxHp: this.maxHp };
    gameState.bossPhase = index + 1;
    EventBus.emit(Events.BOSS_PHASE, payload);
  }

  // =====================================================================
  // BossHost (패턴 → 보스)
  // =====================================================================

  get pos(): Vec {
    this.posVec.x = this.x;
    this.posVec.y = this.y;
    return this.posVec;
  }

  get center(): Vec {
    const c = this.body.center;
    this.centerVec.x = c.x;
    this.centerVec.y = c.y;
    return this.centerVec;
  }

  get halfWidth(): number {
    return this.body.halfWidth;
  }

  get blocked(): boolean {
    return !this.body.blocked.none;
  }

  params<T = PatternParams>(name: BossPatternName): T {
    return this.brain.params<T>(name);
  }

  inPick(name: BossPatternName): boolean {
    return this.brain.inPick(name);
  }

  isReady(name: BossPatternName, ctx: MobContext): boolean {
    return this.brain.isReady(name, ctx);
  }

  readyAt(name: BossPatternName): number {
    return this.brain.readyAt(name);
  }

  setReadyAt(name: BossPatternName, at: number): void {
    this.brain.setReadyAt(name, at);
  }

  scheduleNext(time: number): void {
    this.brain.scheduleNext(time);
  }

  setVelocity(vx: number, vy: number): this {
    this.body.setVelocity(vx, vy);
    return this;
  }

  angleTo(x: number, y: number): number {
    const c = this.body.center;
    return Math.atan2(y - c.y, x - c.x);
  }

  override paint(color: number): void {
    super.paint(color);
  }

  override restoreColor(): void {
    super.restoreColor();
  }

  setInvulnerable(until: number): void {
    this.invulnerableUntil = until;
  }

  addSummoned(n: number): void {
    this.summoned += n;
  }

  emitTelegraph(name: BossPatternName): void {
    EventBus.emit(Events.BOSS_TELEGRAPH, { id: this.id, attack: name } satisfies BossTelegraphPayload);
  }

  emitAttack(name: BossPatternName): void {
    EventBus.emit(Events.BOSS_ATTACK, { id: this.id, attack: name } satisfies BossAttackPayload);
  }

  emitAction(action: BossActionKind, index?: number): void {
    EventBus.emit(Events.BOSS_ACTION, { id: this.id, action, index } satisfies BossActionPayload);
  }

  emitLoop(loop: BossLoopKind, on: boolean): void {
    EventBus.emit(Events.BOSS_LOOP, { loop, on } satisfies BossLoopPayload);
  }

  emitWallHit(): void {
    EventBus.emit(Events.BOSS_WALL_HIT, { id: this.id, x: this.x, y: this.y } satisfies BossWallHitPayload);
  }
}
