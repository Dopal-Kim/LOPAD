/**
 * 61라운드 단계 4 P12 개성 카드·셋째 갈래(만월·광전·백귀·유성 계열) 규칙 실행 창구 (BuildRuntime 의 일부).
 * 규칙은 합산(`currentBuild` — 개성 카드·공명 source 'trait', 갈래·길 노드 source 'branch')에 있고, 여기서는 사건을 무기별 실행기로
 * 나눠 보낸다: 칼 `KatanaRules` · 대검 `GreatswordRules` · 단검 `DaggerRules` · 활 `BowRules` · 공명 `ResonanceRules`.
 * 61 단계 5 (P13): 보이는 새 행동 도구 `moves`(TraitMoves — 갈래 실행기 branch/* 도 쓴다), 개성 발동 이벤트 TRAIT_PROC
 * (BRANCH_EFFECT 의 branch 가 지금 무기의 얻은 개성·켜진 공명이면 — 같은 id 는 TRAIT_FX.PROC_GATE_MS 안 한 번), 개성 fx 지연 로드.
 * 옛 이중 개성에서 옮긴 카드(피바람·술 회오리·불똥 내려베기·갈라진 길·짓눌린 숨·술독·쌍낙인·독주 투척·그림자 사냥·취한 그림자·
 * 흩날리는 살·불화살·별 표적·술별·걸으며 연사)는 원래 자리(branch/*·ArrowRain·BranchMoves)가 실행한다.
 */
import { TRAIT_FX } from '../../../../core/Constants';
import {
  EventBus,
  Events,
  type BranchEffectPayload,
  type PlayerAttackPayload,
  type PlayerSecondaryPayload,
  type PlayerSkillPayload,
  type TraitGainedPayload,
  type TraitProcPayload,
} from '../../../../core/EventBus';
import { gameState } from '../../../../core/GameState';
import { RESONANCES, traitDef } from '../../../../data/growth';
import type { Mob } from '../../../../objects/Mob';
import type { Projectile } from '../../../../objects/Projectile';
import { traitFxId } from '../../../../systems/growth/traitArt';
import { loadSheetsNow } from '../../../../systems/sprites/lazySheets';
import { FX_ACTION } from '../../../../systems/sprites/spriteActions';
import type { Game } from '../../../Game';
import type { PerfectKind } from '../BuildPerfect';
import type { BuildRuntime } from '../BuildRuntime';
import { BowRules } from './BowRules';
import { DaggerRules } from './DaggerRules';
import { GreatswordRules } from './GreatswordRules';
import { KatanaRules } from './KatanaRules';
import { ResonanceRules } from './ResonanceRules';
import { RuleKit, type Pt } from './RuleKit';
import type { TraitMoves } from './TraitMoves';

type Sub = [event: string, fn: (p: never) => void];

/** 개성 fx 부위 (art 요청 목록 — `trait_<무기>_<개성>[_<part>]`) */
export const TRAIT_FX_PARTS: readonly string[] = [
  '',
  'launch',
  'land',
  'impact',
  'bind',
  'in',
  'out',
  'soak',
  'snap',
  'fire',
  'burst',
  'mark',
];

export class TraitRules {
  private readonly kit: RuleKit;
  readonly katana: KatanaRules;
  readonly greatsword: GreatswordRules;
  readonly dagger: DaggerRules;
  readonly bow: BowRules;
  readonly resonance: ResonanceRules;
  private subs: Sub[] = [];
  /** TRAIT_PROC 간격 (개성·공명 id → 마지막 시각) · 디버그 발동 수 */
  private readonly procAt = new Map<string, number>();
  readonly procs: Record<string, number> = {};

  constructor(
    private readonly g: Game,
    rt: BuildRuntime,
  ) {
    this.kit = new RuleKit(g, rt);
    this.katana = new KatanaRules(this.kit);
    this.greatsword = new GreatswordRules(this.kit);
    this.dagger = new DaggerRules(this.kit);
    this.bow = new BowRules(this.kit);
    this.resonance = new ResonanceRules(this.kit, this.greatsword, this.dagger, this.bow);
    this.subs = [
      [Events.PLAYER_ATTACKED, (p: PlayerAttackPayload) => this.onAttack(p)],
      [Events.PLAYER_DASHED, (p: { x: number; y: number; dirX: number; dirY: number }) => this.onDash(p)],
      [Events.PLAYER_SKILL, (p: PlayerSkillPayload) => this.onSkill(p)],
      [Events.PLAYER_SECONDARY, (p: PlayerSecondaryPayload) => this.onSecondary(p)],
      [Events.PLAYER_GUARD_RELEASED, () => this.greatsword.onGuardReleased()],
      [Events.BRANCH_EFFECT, (p: BranchEffectPayload) => this.onEffect(p)],
      [Events.TRAIT_GAINED, (p: TraitGainedPayload) => this.loadFx([p.id])],
    ];
    for (const [ev, fn] of this.subs) EventBus.on(ev, fn, this);
    // 61 단계 5: 얻은 개성·이 무기 공명의 전용 fx (아트가 넣으면 — 매니페스트에 없으면 아무것도 안 함)
    this.loadFx([...gameState.weapon.traits, ...RESONANCES.filter((r) => r.weapon === this.weapon).map((r) => r.id)]);
  }

  private get weapon(): string {
    return gameState.weapon.id;
  }

  /** 61 단계 5 보이는 새 행동 도구 (branch/* 도 쓴다) */
  get moves(): TraitMoves {
    return this.kit.moves;
  }

  // --- 개성 발동 이벤트 · 그림 로드 ---

  /** BRANCH_EFFECT → 얻은 개성·켜진 공명이면 TRAIT_PROC (음향 발동음·런 로그 후보) */
  private onEffect(p: BranchEffectPayload): void {
    const w = gameState.weapon;
    const id = p.branch;
    let payload: TraitProcPayload | null = null;
    if (w.traits.includes(id)) {
      const t = traitDef(id);
      if (t) payload = { weapon: w.id, trait: id, act: t.act };
    } else if (this.kit.rt.mods.rules.some((r) => r.id === id && r.source === 'trait')) {
      const r = RESONANCES.find((x) => x.id === id);
      if (r) payload = { weapon: w.id, trait: id, act: 'resonance', resonance: id };
    }
    if (!payload) return;
    const now = this.g.time.now;
    if (now - (this.procAt.get(id) ?? -Infinity) < TRAIT_FX.PROC_GATE_MS) return;
    this.procAt.set(id, now);
    this.procs[id] = (this.procs[id] ?? 0) + 1;
    EventBus.emit(Events.TRAIT_PROC, payload);
  }

  /** 개성 전용 fx 를 지연 로드 (fx/v3/trait_<무기>_<개성>[_부위] — 매니페스트에 있는 것만) */
  private loadFx(ids: readonly string[]): void {
    const w = this.weapon;
    const reqs = ids.flatMap((id) =>
      TRAIT_FX_PARTS.map((part) => ({
        category: 'fx' as const,
        name: traitFxId(w, id, part || undefined),
        action: FX_ACTION,
      })),
    );
    if (reqs.length > 0) loadSheetsNow(this.g, reqs);
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
    else if (w === 'bow') this.bow.onDash(p);
    this.resonance.onDash({ x: p.x, y: p.y });
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
    const w = this.weapon;
    if (w === 'greatsword') this.greatsword.afterStrike(mob, p, died);
    else if (w === 'katana') this.katana.afterStrike(mob, p, died);
    else if (w === 'dagger') this.dagger.afterStrike(mob, p, died);
  }

  /** 처치 (BuildCombat.onKill) */
  onKill(mob: Mob, _kind: string): void {
    const w = this.weapon;
    if (w === 'katana') this.katana.onKill(mob);
    else if (w === 'greatsword') this.greatsword.onKill();
    else if (w === 'dagger') this.dagger.onKill(mob);
    this.resonance.onKill(mob);
  }

  /** 투사체 (BuildRuntime) */
  onArrowSpawn(shot: Projectile, p: PlayerAttackPayload): void {
    if (this.weapon === 'bow') this.bow.onArrowSpawn(shot, p);
  }

  onShotHit(shot: Projectile, mob: Mob, died: boolean): void {
    if (this.weapon === 'bow') this.bow.onShotHit(shot, mob, died);
  }

  /** 그림자 걸음 (BuildRuntime.onShadowStep) — 출발 · 도착 */
  onShadowStep(from: Pt, to: Pt): void {
    if (this.weapon === 'dagger') this.dagger.onShadowStep(from, to);
    this.resonance.onShadowStep(from, to);
  }

  /** 그림자 매듭 (BrandMarks): 낙인이 남은 적을 묶는다 */
  onShadowKnot(mob: Mob, ms: number): void {
    if (this.weapon === 'dagger') this.dagger.onShadowKnot(mob, ms);
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

  /** 화살비 한 발 적중 (ArrowRain) — 낙하점 · 화살비 한가운데 */
  onRainHit(mob: Mob, died: boolean, at: Pt, center: Pt): void {
    if (this.weapon === 'bow') this.bow.onRainHit(mob, died, at, center);
  }

  /** 화살비 범위 배율 (성우) */
  rainScale(): number {
    const r = this.kit.rt.rule('starfall');
    return r ? this.kit.p(r, 'rainScale', 1) : 1;
  }

  /** 피격을 흘림 (BuildDefense.evadeHit) — 분신 방패 */
  evadeHit(time: number): boolean {
    return this.weapon === 'dagger' && this.dagger.evadeHit(time);
  }

  /** 피격 경직 없음 (폭주) */
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
    this.kit.moves.update(now);
    this.resonance.update(now);
  }

  debug(): Record<string, unknown> {
    return {
      ...this.kit.last,
      ...this.greatsword.debug(),
      ...this.dagger.debug(),
      moves: this.kit.moves.debug(),
      resonance: this.resonance.debug(),
      procs: { ...this.procs },
    };
  }

  destroy(): void {
    for (const [ev, fn] of this.subs) EventBus.off(ev, fn, this);
    this.subs = [];
    this.katana.destroy();
    this.greatsword.destroy();
    this.dagger.destroy();
    this.bow.destroy();
    this.resonance.destroy();
    this.kit.moves.destroy();
  }
}
