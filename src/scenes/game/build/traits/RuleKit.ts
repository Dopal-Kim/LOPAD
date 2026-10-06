/**
 * 61 G 개성·셋째 갈래 규칙 공용 도우미: 규칙 수치 · 한 번 피해(빌드 배율·처치 경로) · 밀기·당기기·경직 · 분신 선 베기 · 투사체 ·
 * 음향 훅(BRANCH_EFFECT — branch = 개성 id 또는 갈래 노드 id → 개성이면 TraitRules 가 TRAIT_PROC). 그림이 없으면 윤곽(BuildEffects).
 * 61 단계 5 (P13): 보이는 새 행동(띄움·처박기·끌어당김·묶음·불똥)은 `moves`(TraitMoves). 개성 피해를 받은 적은 `traitHitAt`(공명).
 */
import { BUILD_FX, TILE } from '../../../../core/Constants';
import { EventBus, Events, type BranchEffectPayload, type PlayerAttackPayload } from '../../../../core/EventBus';
import type { Mob } from '../../../../objects/Mob';
import type { Projectile } from '../../../../objects/Projectile';
import { param, type ActiveRule } from '../../../../systems/build/buildMods';
import type { Game } from '../../../Game';
import type { BuildRuntime } from '../BuildRuntime';
import { TraitMoves } from './TraitMoves';

export type Pt = { x: number; y: number };

export const T = (tiles: number): number => tiles * TILE;

export class RuleKit {
  /** 마지막 공격 페이로드 (처치가 어느 타였는지) */
  lastAttack: { p: PlayerAttackPayload; at: number } | null = null;
  /** 디버그: 마지막 규칙 발동 */
  last: Record<string, unknown> = {};
  /** 61 단계 5: 보이는 새 행동 도구 */
  readonly moves: TraitMoves;
  /** 61 단계 5 공명: 개성 피해를 마지막으로 받은 시각 */
  readonly traitHitAt = new WeakMap<Mob, number>();

  constructor(
    readonly g: Game,
    readonly rt: BuildRuntime,
  ) {
    this.moves = new TraitMoves(this);
  }

  get now(): number {
    return this.g.time.now;
  }

  /** 규칙 수치 */
  p(r: ActiveRule, key: string, fallback = 0): number {
    return param(r, key, fallback);
  }

  /** 발동 기록 + 음향 훅 */
  fire(rule: string, effect: string, info?: Record<string, unknown>): void {
    this.last = { traitRule: rule, effect, t: Math.round(this.now), ...(info ?? {}) };
    this.rt.record(`rule:${rule}`, effect);
    EventBus.emit(Events.BRANCH_EFFECT, { branch: rule, effect } satisfies BranchEffectPayload);
  }

  /** 공격력 × mult 피해 (빌드 배율·치명 굴림 · 처치면 처치 경로). 처치면 true */
  hit(mob: Mob, mult: number, dir: Pt, o: { heavy?: boolean; forceCrit?: boolean } = {}): boolean {
    if (!mob.active || mult <= 0) return false;
    this.traitHitAt.set(mob, this.now);
    return this.rt.fx.damage(mob, mult, {
      dirX: dir.x,
      dirY: dir.y,
      heavy: o.heavy,
      forceCrit: o.forceCrit,
    });
  }

  /** 밀기 (+ 보스는 밀지 않는다) */
  push(mob: Mob, dir: Pt, tiles: number, ms = 160): void {
    if (!mob.active || mob.isBoss) return;
    mob.shove(dir.x, dir.y, T(tiles), ms);
  }

  /** 경직 (+ 비틀 표시) */
  stun(mob: Mob, ms: number): void {
    if (!mob.active || ms <= 0) return;
    mob.stun(this.now, ms, 'hit');
    this.rt.art.stagger(mob, ms);
  }

  /** 분신이 선을 벤다 (윤곽 + 분신 표시) — 맞은 적 */
  cloneLine(
    from: Pt,
    dir: Pt,
    len: number,
    halfPx: number,
    mult: number,
    color: number = BUILD_FX.COLOR.MOON,
    /** 61 단계 5: 개성 전용 fx 가 이미 그렸으면 false (분신 복사·윤곽 띠를 그리지 않는다) */
    outline = true,
  ): Mob[] {
    const l = Math.hypot(dir.x, dir.y) || 1;
    const d = { x: dir.x / l, y: dir.y / l };
    if (outline) {
      this.rt.fx.clone(from.x, from.y);
      this.rt.fx.lineFx(from.x, from.y, d.x, d.y, len, halfPx, color);
    }
    const hits = this.rt.fx.inLine(from.x, from.y, d.x, d.y, len, halfPx);
    for (const m of hits) this.hit(m, mult, d, { heavy: true });
    return hits;
  }

  /** 원 피해 (윤곽) — 맞은 적 */
  ring(at: Pt, r: number, mult: number, color: number = BUILD_FX.COLOR.RING, outline = true): Mob[] {
    if (outline) this.rt.fx.ring(at.x, at.y, r, color);
    const hits = this.rt.fx.inCircle(at.x, at.y, r);
    for (const m of hits) this.hit(m, mult, { x: m.x - at.x, y: m.y - at.y });
    return hits;
  }

  /** 빌드 투사체 (공격력 × mult, 치명 굴림) */
  shot(
    from: Pt,
    dir: Pt,
    mult: number,
    o: { tag: string; speedTiles: number; rangeTiles: number; pierce?: number; tint?: number; sprite?: string },
  ): Projectile | null {
    const { dmg, crit } = this.g.combat.rollDamage(mult, false, 'other');
    const sm = this.rt.combat.shotMods();
    const speed = o.speedTiles * sm.speedMult;
    return this.rt.fx.shot(from.x, from.y, dir.x, dir.y, dmg, {
      tag: o.tag,
      speedTiles: speed,
      lifeMs: (o.rangeTiles / speed) * 1000,
      pierce: o.pierce ?? 0,
      crit,
      ...(o.sprite && this.g.fx.has(o.sprite) ? { sprite: o.sprite } : { tint: o.tint ?? BUILD_FX.COLOR.THROW }),
    });
  }

  /** 마지막 공격이 windowMs 안이고 조건에 맞는가 */
  recentAttack(windowMs: number, test: (p: PlayerAttackPayload) => boolean): boolean {
    const a = this.lastAttack;
    return Boolean(a && this.now - a.at <= windowMs && test(a.p));
  }
}
