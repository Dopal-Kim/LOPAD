/**
 * 61라운드 단계 4 P12 개성 카드·셋째 갈래(만월·광전·백귀·유성 계열) 규칙 실행 창구 (BuildRuntime 의 일부).
 * 규칙은 합산(`currentBuild` — 개성 카드 source 'trait', 갈래·길 노드 source 'branch')에 있고, 여기서는 사건을 무기별 실행기로 나눠 보낸다:
 * 칼 `KatanaRules` · 대검 `GreatswordRules` · 단검 `DaggerRules` · 활 `BowRules`. 옛 이중 개성에서 옮긴 카드(spinChain·helmBreak·
 * splitRoad·ringGrudge·jarCrush·twinBrand·liquorThrow·volleyRefill·longPerfectCrit·fireArrow·liquorWhirl)는 원래 자리(branch/*)가 실행한다.
 */
import {
  EventBus,
  Events,
  type PlayerAttackPayload,
  type PlayerSecondaryPayload,
  type PlayerSkillPayload,
} from '../../../../core/EventBus';
import { gameState } from '../../../../core/GameState';
import type { Mob } from '../../../../objects/Mob';
import type { Projectile } from '../../../../objects/Projectile';
import type { Game } from '../../../Game';
import type { PerfectKind } from '../BuildPerfect';
import type { BuildRuntime } from '../BuildRuntime';
import { BowRules } from './BowRules';
import { DaggerRules } from './DaggerRules';
import { GreatswordRules } from './GreatswordRules';
import { KatanaRules } from './KatanaRules';
import { RuleKit, type Pt } from './RuleKit';

type Sub = [event: string, fn: (p: never) => void];

export class TraitRules {
  private readonly kit: RuleKit;
  readonly katana: KatanaRules;
  readonly greatsword: GreatswordRules;
  readonly dagger: DaggerRules;
  readonly bow: BowRules;
  private subs: Sub[] = [];

  constructor(g: Game, rt: BuildRuntime) {
    this.kit = new RuleKit(g, rt);
    this.katana = new KatanaRules(this.kit);
    this.greatsword = new GreatswordRules(this.kit);
    this.dagger = new DaggerRules(this.kit);
    this.bow = new BowRules(this.kit);
    this.subs = [
      [Events.PLAYER_ATTACKED, (p: PlayerAttackPayload) => this.onAttack(p)],
      [Events.PLAYER_DASHED, (p: { x: number; y: number; dirX: number; dirY: number }) => this.onDash(p)],
      [Events.PLAYER_SKILL, (p: PlayerSkillPayload) => this.onSkill(p)],
      [Events.PLAYER_SECONDARY, (p: PlayerSecondaryPayload) => this.onSecondary(p)],
      [Events.PLAYER_GUARD_RELEASED, () => this.greatsword.onGuardReleased()],
    ];
    for (const [ev, fn] of this.subs) EventBus.on(ev, fn, this);
  }

  private get weapon(): string {
    return gameState.weapon.id;
  }

  // --- 사건 ---

  private onAttack(p: PlayerAttackPayload): void {
    this.kit.lastAttack = { p, at: this.kit.now };
    const w = this.weapon;
    if (w === 'greatsword') this.greatsword.onAttack(p);
    else if (w === 'dagger') this.dagger.onAttack(p);
    else if (w === 'bow') this.bow.onAttack(p);
  }

  private onDash(p: { x: number; y: number; dirX: number; dirY: number }): void {
    const w = this.weapon;
    if (w === 'dagger') this.dagger.onDash(p);
    else if (w === 'bow') this.bow.onDash();
  }

  private onSkill(p: PlayerSkillPayload): void {
    const w = this.weapon;
    if (w === 'katana') this.katana.onSkill(p);
    else if (w === 'greatsword') this.greatsword.onSkill(p);
    else if (w === 'dagger') this.dagger.onSkill(p);
  }

  private onSecondary(p: PlayerSecondaryPayload): void {
    if (this.weapon === 'katana' && p.phase === 'block') this.katana.onGuardBlock();
  }

  /** 완벽 성공 (BuildPerfect) */
  onPerfect(kind: PerfectKind, dx: number, dy: number): void {
    const w = this.weapon;
    if (w === 'katana') this.katana.onPerfect(kind, dx, dy);
    else if (w === 'greatsword') this.greatsword.onPerfect(kind, dx, dy);
  }

  /** 근접 타격 뒤 (BuildCombat.afterStrike) */
  afterStrike(mob: Mob, p: PlayerAttackPayload & { buildMove?: string }, died: boolean): void {
    if (this.weapon === 'greatsword') this.greatsword.afterStrike(mob, p, died);
    if (this.weapon === 'katana') this.katana.afterStrike(mob, p, died);
  }

  /** 이 적에게 확정 치명인가 (BuildCombat.forceCritOn) */
  forceCrit(mob: Mob): boolean {
    const k = this.kit;
    if (k.rt.rule('critOnStunned') && mob.isStunned(k.now)) return true;
    const bc = k.rt.rule('brandCrit');
    if (bc && k.g.strikes.brands.marksOf(mob) >= k.p(bc, 'min', 3)) return true;
    return false;
  }

  /** 처치 (BuildCombat.onKill) */
  onKill(mob: Mob, _kind: string): void {
    const w = this.weapon;
    if (w === 'katana') this.katana.onKill(mob);
    else if (w === 'greatsword') this.greatsword.onKill();
    else if (w === 'dagger') this.dagger.onKill(mob);
  }

  /** 투사체 (BuildRuntime) */
  onArrowSpawn(shot: Projectile, p: PlayerAttackPayload): void {
    if (this.weapon === 'bow') this.bow.onArrowSpawn(shot, p);
  }

  onShotHit(shot: Projectile, mob: Mob, died: boolean): void {
    if (this.weapon === 'bow') this.bow.onShotHit(shot, mob, died);
  }

  /** 그림자 걸음 (BuildRuntime.onShadowStep) */
  onShadowStep(): void {
    if (this.weapon === 'dagger') this.dagger.onShadowStep();
  }

  /** 낙인 기폭 뒤 (BranchStrikes.onBrandBurst) */
  onBrandBurst(mob: Mob, marks: number, died: boolean): void {
    if (this.weapon === 'dagger') this.dagger.onBrandBurst(mob, marks, died);
  }

  /** 일섬이 끝남 (IssenStrikes) — 출발점 · 방향 · 달린 거리 */
  onIssenEnd(start: Pt, dir: Pt, travel: number): void {
    if (this.weapon === 'katana') this.katana.onIssenEnd(start, dir, travel);
  }

  /** 대검 차지 균열 (BranchStrikes.onCrackLine) */
  onCrackLine(origin: Pt, dir: Pt, lengthPx: number, halfPx: number): void {
    if (this.weapon === 'greatsword') this.greatsword.onCrackLine(origin, dir, lengthPx, halfPx);
  }

  /** 화살비 한 발 적중 (ArrowRain) */
  onRainHit(mob: Mob, died: boolean, at: Pt): void {
    if (this.weapon === 'bow') this.bow.onRainHit(mob, died, at);
  }

  /** 화살비 범위 배율 (성우) */
  rainScale(): number {
    const r = this.kit.rt.rule('starfall');
    return r ? this.kit.p(r, 'rainScale', 1) : 1;
  }

  /** 받는 피해 조정 (BuildDefense.adjustDamage) — 휘두르며 막기 */
  adjustDamage(amount: number): number {
    return this.weapon === 'greatsword' ? this.greatsword.adjustDamage(amount) : amount;
  }

  /** 피격을 흘림 (BuildDefense.evadeHit) — 분신 방패 */
  evadeHit(time: number): boolean {
    return this.weapon === 'dagger' && this.dagger.evadeHit(time);
  }

  /** 피격 경직 없음 (폭주 · 버티며 모으기) */
  noFlinch(): boolean {
    return this.weapon === 'greatsword' && this.greatsword.noFlinch();
  }

  /** 공속 배율 (폭주) */
  attackSpeedMult(): number {
    return this.weapon === 'greatsword' ? this.greatsword.attackSpeedMult() : 1;
  }

  update(now: number): void {
    const w = this.weapon;
    if (w === 'greatsword') this.greatsword.update(now);
    else if (w === 'dagger') this.dagger.update(now);
    else if (w === 'bow') this.bow.update(now);
  }

  debug(): Record<string, unknown> {
    return { ...this.kit.last, ...this.greatsword.debug(), ...this.dagger.debug() };
  }

  destroy(): void {
    for (const [ev, fn] of this.subs) EventBus.off(ev, fn, this);
    this.subs = [];
    this.greatsword.destroy();
    this.dagger.destroy();
  }
}
