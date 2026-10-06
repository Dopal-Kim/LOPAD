/**
 * 54라운드 Q4 보스 두뇌 (Phaser 의존 없음): 페이즈 · 패턴 고르기(시드 RNG, 쿨타임) · 패턴 한 판 진행 · 연계 · 강화 · 페이즈 진입 연출.
 * 35라운드 Boss.ts 의 switch 상태 머신에서 '고르기·예약·쿨타임' 규칙을 그대로 옮겼고, 패턴별 동작은 모듈(registry)로 나눴다.
 * - 고르기: 페이즈 pick 순서대로 쿨타임·조건이 맞는 것 → rng.pick. 하나도 없으면 'dash'
 * - 끝(finish): 쿨타임 기록(cooldownMs, 없으면 0) · 다음 예약(now + 페이즈 intervalMs). finish:false 면 둘 다 생략
 * - 페이즈가 바뀌면 다음 갱신에서 예약을 새 간격으로 (nextPatternAt = 0). enterPattern 이 있으면 진행 중 패턴을 끊고 바로 시작
 */
import type { BossDef } from '../../data/types';
import { phaseIndexFor, resolvePatternParams, type BossPatternName, type PatternParams } from '../../data/bossPatterns';
import type { MobContext } from '../Mob';
import { patternModule } from './registry';
import type { BossHost, PatternEnd, PatternRun } from './types';

/** 두뇌가 보스 몸에 부탁하는 것 */
export interface BossBody {
  /** 패턴이 없을 때: 플레이어 쪽으로 걷기 */
  approach(ctx: MobContext): void;
  /** 패턴 끝 경직 (잔 깨짐) */
  stunSelf(time: number, ms: number, pose?: PatternEnd['stunPose']): void;
  /** 패턴이 끊겼을 때 몸 자세 해제 */
  releasePose(): void;
  /** 페이즈 전환 알림 (index 0부터) */
  emitPhase(index: number): void;
}

export class BossBrain {
  phaseIndex = 0;
  run: PatternRun | null = null;
  current: BossPatternName | null = null;
  readonly log: BossPatternName[] = [];
  nextPatternAt = 0;
  private readonly ready = new Map<BossPatternName, number>();
  private readonly cache = new Map<string, PatternParams>();
  /** 다음에 시작하는 패턴을 강화 (1층 얼큰 '한 잔 더') · 지금 판이 강화 중인지 */
  private empowerPending = false;
  runEmpowered = false;
  /** 페이즈 진입 연출 대기 */
  private pendingEnter: BossPatternName | null = null;
  /** 디버그 강제 패턴 (순서대로 돌아가며) */
  private forced: BossPatternName[] | null = null;
  private forcedIndex = 0;

  constructor(
    readonly def: BossDef,
    private readonly host: BossHost,
    private readonly body: BossBody,
  ) {}

  get phase(): BossDef['phases'][number] {
    return this.def.phases[this.phaseIndex];
  }

  get empowered(): boolean {
    return this.empowerPending;
  }

  /** 현재 페이즈·강화 여부로 해석한 수치 (페이즈·강화별 캐시) */
  params<T = PatternParams>(name: BossPatternName, empowered = this.runEmpowered): T {
    const key = `${this.phaseIndex}:${name}:${empowered ? 1 : 0}`;
    let p = this.cache.get(key);
    if (!p) {
      p = resolvePatternParams(this.def, this.phaseIndex, name, empowered) ?? {};
      this.cache.set(key, p);
    }
    return p as T;
  }

  inPick(name: BossPatternName): boolean {
    return this.phase.pick.includes(name);
  }

  readyAt(name: BossPatternName): number {
    return this.ready.get(name) ?? 0;
  }

  setReadyAt(name: BossPatternName, at: number): void {
    this.ready.set(name, at);
  }

  isReady(name: BossPatternName, ctx: MobContext): boolean {
    if (ctx.time < this.readyAt(name)) return false;
    const m = patternModule(name);
    return m.isReady ? m.isReady(this.host, ctx) : true;
  }

  scheduleNext(time: number): void {
    this.nextPatternAt = time + this.phase.intervalMs;
  }

  /** 디버그: 강제 패턴 목록 (null 이면 해제) */
  force(list: BossPatternName[] | null): void {
    this.forced = list && list.length > 0 ? [...list] : null;
    this.forcedIndex = 0;
  }

  get forcedList(): readonly BossPatternName[] | null {
    return this.forced;
  }

  /** 후보 중 쿨타임·조건이 맞는 것에서 시드 RNG 로 고른다. 아무것도 못 쓰면 돌진 */
  choose(ctx: MobContext): BossPatternName {
    if (this.forced) {
      const p = this.forced[this.forcedIndex % this.forced.length];
      this.forcedIndex++;
      return p;
    }
    const ready = this.phase.pick.filter((p) => this.isReady(p, ctx));
    if (ready.length === 0) return 'dash';
    return this.host.rng.pick(ready);
  }

  /** 매 프레임 (넉백·경직이 아닐 때) */
  update(ctx: MobContext): void {
    if (this.pendingEnter) {
      const p = this.pendingEnter;
      this.pendingEnter = null;
      this.interrupt();
      this.begin(p, ctx);
      return;
    }
    if (this.run) {
      const end = this.run.update(ctx);
      if (end) this.end(end, ctx);
      return;
    }
    this.body.approach(ctx);
    const urgent = this.urgent(ctx);
    if (urgent) this.begin(urgent, ctx);
    else if (ctx.time >= this.nextPatternAt) this.begin(this.choose(ctx), ctx);
  }

  /** 61 P13: 조건이 맞으면 간격을 기다리지 않는 패턴 (pick 안 · 쿨타임 끝 — 디버그 강제 중에는 없음) */
  private urgent(ctx: MobContext): BossPatternName | null {
    if (this.forced) return null;
    return this.phase.pick.find((p) => patternModule(p).urgent && this.isReady(p, ctx)) ?? null;
  }

  begin(p: BossPatternName, ctx: MobContext): void {
    this.current = p;
    this.log.push(p);
    this.runEmpowered = this.empowerPending;
    this.empowerPending = false;
    const r = patternModule(p).start(this.host, ctx);
    if ('update' in r) this.run = r;
    else this.end(r, ctx);
  }

  private end(end: PatternEnd, ctx: MobContext): void {
    const p = this.current;
    this.run = null;
    this.runEmpowered = false;
    if (end.finish !== false) {
      if (p) this.ready.set(p, ctx.time + (this.params<{ cooldownMs?: number }>(p).cooldownMs ?? 0));
      this.current = null;
      this.scheduleNext(ctx.time);
    }
    if (end.empower) this.empowerPending = true;
    if (end.stunMs && end.stunMs > 0) this.body.stunSelf(ctx.time, end.stunMs, end.stunPose);
    if (end.next) this.begin(end.next, ctx);
  }

  /** 진행 중인 패턴 끊기 (마커·방 효과 정리, 쿨타임 기록 없음) */
  interrupt(): void {
    this.run?.cancel();
    this.run = null;
    this.runEmpowered = false;
    this.current = null;
  }

  /** 패링 등 경직: 패턴을 끊고 다음 예약 */
  onStunned(now: number): void {
    this.interrupt();
    this.body.releasePose();
    this.scheduleNext(now);
  }

  /** 피해 뒤 HP 비율로 페이즈 판정. 바뀌면 true */
  checkPhase(frac: number): boolean {
    const idx = phaseIndexFor(frac, this.def.phases);
    if (idx === this.phaseIndex) return false;
    this.phaseIndex = idx;
    this.body.emitPhase(idx);
    this.nextPatternAt = 0; // 다음 update 에서 새 페이즈 간격으로 재설정
    const enter = this.phase.enterPattern;
    if (enter) this.pendingEnter = enter;
    return true;
  }

  /** 디버그: 페이즈를 바로 (진입 연출 없이) */
  setPhase(idx: number): void {
    this.phaseIndex = Math.max(0, Math.min(this.def.phases.length - 1, idx));
    this.nextPatternAt = 0;
  }

  /** 지금 접촉 공격력 */
  contactAttack(): number {
    return this.run?.contactAttack?.() ?? this.def.contactAttack;
  }

  get state(): string {
    return this.run?.state ?? 'approach';
  }

  destroy(): void {
    this.interrupt();
  }
}
