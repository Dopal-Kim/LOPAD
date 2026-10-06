/**
 * 57라운드 빌드 축 — 타격·투사체·처치·이동기 규칙 (BuildRuntime 의 일부): 공격 페이로드 배율 · 대상 배율(살기·표식) ·
 * 확정 치명(급소 6 금·견장) · 타격 뒤 공통(표식·지속 피해·강공 경직·잔불 심장·기폭) · 지속 피해 틱 · 이동·공격 배율.
 * 60라운드 6-1 정리(동작 그대로): 공격·이동 패시브 `combat/AttackPassives` · 투사체 `combat/ShotRules` · 처치 `combat/KillRules`.
 */
import Phaser from 'phaser';
import { BUILD_ART, BUILD_FX, DEPTH } from '../../../core/Constants';
import {
  EventBus,
  Events,
  type MarkChangedPayload,
  type PlayerAttackPayload,
  type StatusBurstPayload,
} from '../../../core/EventBus';
import { gameState } from '../../../core/GameState';
import { BUILD, curseDef } from '../../../data/build';
import type { ComboChangeDef } from '../../../data/buildTypes';
import type { Mob } from '../../../objects/Mob';
import type { Projectile } from '../../../objects/Projectile';
import { param } from '../../../systems/build/buildMods';
import { isStrongAttack } from '../../../systems/build/strikeKinds';
import type { DotKind } from '../../../systems/build/statusBooks';
import type { Game } from '../../Game';
import { T } from '../shared';
import type { BuildRuntime } from './BuildRuntime';
import { AttackPassives } from './combat/AttackPassives';
import { buildAttack, emitProc } from './combat/common';
import { KillRules } from './combat/KillRules';
import { ShotRules } from './combat/ShotRules';

/** 이 공격(페이로드)에 붙은 일회성 배율 (아슬아슬·취보 반격·독한 숨 …) */
interface PayloadBonus {
  mult: number;
  forceCrit: boolean;
}

export class BuildCombat {
  /** 아슬아슬: 다음 공격 배율 (완벽 회피 뒤) */
  private empower: { until: number; mult: number } | null = null;
  /** 급소 6 '금': 치명타를 맞은 적 → 다음 타격 치명 */
  private readonly cracked = new Map<Mob, number>();
  /** 공격 페이로드 → 일회성 배율 */
  private readonly payloadBonus = new WeakMap<PlayerAttackPayload, PayloadBonus>();
  /** 표식 점 그리기 */
  private readonly markGfx: Phaser.GameObjects.Graphics;
  /** 갈라진 길(이중 개성) 가속 끝 · 버팀 4 위기 가속 끝 */
  splitRoadUntil = -Infinity;
  crisisHasteUntil = -Infinity;
  /** 공격·이동 패시브 · 투사체 · 처치 규칙 */
  private readonly passives: AttackPassives;
  private readonly shots: ShotRules;
  private readonly kills: KillRules;

  constructor(
    private readonly g: Game,
    private readonly rt: BuildRuntime,
  ) {
    this.markGfx = g.add.graphics().setDepth(DEPTH.HIT_FX);
    this.passives = new AttackPassives(g, rt);
    this.shots = new ShotRules(g, rt, this);
    this.kills = new KillRules(g, rt, (mob) => this.cracked.delete(mob));
  }

  private get now(): number {
    return this.g.time.now;
  }

  // --- 공격 페이로드 (PLAYER_ATTACKED — PlayerStrikes 보다 먼저 구독) ---

  /** 갈래 연격 한 타 변화 (현재 경로의 1단 노드 comboChange) */
  private comboChange(index: number | undefined): ComboChangeDef[] {
    if (index === undefined) return [];
    const out: ComboChangeDef[] = [];
    for (const n of gameState.weapon.nodes) for (const c of n.comboChange ?? []) if (c.index === index) out.push(c);
    return out;
  }

  onAttack(p: PlayerAttackPayload): void {
    const now = this.now;
    // 연격 한 타 변화: 호 판정 각·판정 크기 (선풍 2타 180°·×1.2)
    for (const c of this.comboChange(p.comboIndex)) {
      if (c.sizeMult) p.sizeMult *= c.sizeMult;
      const hs = p.hitShape;
      if (c.arcDeg && hs?.kind === 'arc') {
        const mid = (hs.fromDeg + hs.toDeg) / 2;
        const sign = hs.toDeg >= hs.fromDeg ? 1 : -1;
        p.hitShape = { ...hs, fromDeg: mid - (sign * c.arcDeg) / 2, toDeg: mid + (sign * c.arcDeg) / 2 };
      }
      if (c.crack) {
        const C = c.crack;
        this.g.time.delayedCall(Math.max(0, p.swingDelayMs), () => this.passives.shortCrack(p, C));
      }
    }
    // 일회성 배율: 아슬아슬 · 취보 반격 · 깨진 거울 · 독한 숨 · 취권
    let mult = 1;
    if (this.empower && now < this.empower.until) {
      mult *= 1 + this.empower.mult;
      this.empower = null;
    }
    const stagger = BUILD.sets.drunk[1].effect;
    if (this.rt.drunk.takeCounter(now)) mult *= 1 + (Number(stagger.counterMult) || 0);
    // 간파 2: 완벽 성공 뒤 다음 공격 1회 치명 확정
    const crit = this.rt.perfect.takeCrit();
    if (mult !== 1 || crit) this.payloadBonus.set(p, { mult, forceCrit: crit });
    // 활 완벽 놓기 = 완벽 성공
    if (p.bowPower === 'perfect') this.rt.perfect.onPerfect('perfectRelease');
    this.rt.branch.onAttack(p);
    this.passives.onAttack(p);
  }

  // --- 타격 (PlayerStrikes.strikeMob · BranchStrikes) ---

  /** 공격 페이로드 배율 (대상 무관): 강공 +중량 · 일회성(아슬아슬·취보 반격·간파 2) */
  payloadMods(p: PlayerAttackPayload & { buildMove?: string }): { mult: number; forceCrit: boolean } {
    let mult = 1;
    let forceCrit = false;
    if (isStrongAttack(p)) mult *= 1 + this.rt.stat('heavyDamageMult');
    const pb = this.payloadBonus.get(p);
    if (pb) {
      mult *= pb.mult;
      forceCrit ||= pb.forceCrit;
    }
    return { mult, forceCrit };
  }

  /** 근접 타격 1회 전: 페이로드 배율 + 대상 확정 치명(급소 6 금·견장) */
  strikeBonus(mob: Mob, p: PlayerAttackPayload & { buildMove?: string }): { mult: number; forceCrit: boolean } {
    const b = this.payloadMods(p);
    return { mult: b.mult, forceCrit: b.forceCrit || this.forceCritOn(mob) };
  }

  /** 이 적에게 확정 치명인가 (급소 6 금 · 장교의 견장 최대 표식) — 쓰면 금은 사라진다 */
  forceCritOn(mob: Mob | undefined): boolean {
    if (!mob) return false;
    const until = this.cracked.get(mob);
    if (until !== undefined) {
      this.cracked.delete(mob);
      if (until > this.now) return true;
    }
    if (this.rt.rule('markedCrit')) {
      const set2 = BUILD.sets.mark[0].effect;
      const maxMarks = Number(set2.max) || 3;
      if (this.rt.marks.marks(mob) >= maxMarks) return true;
      const brands = this.g.strikes.brands.marksOf(mob);
      if (brands > 0 && brands >= this.g.strikes.brands.maxMarks) return true;
    }
    return false;
  }

  /** 모든 피해 굴림에 곱하는 대상 배율: 살기 · 표식(표식당 +5% + 붉은 분필) */
  damageMultFor(mob: Mob | undefined): number {
    let m = 1;
    if (this.kills.bloodlustActive(this.now)) {
      const r = this.rt.rule('bloodlust');
      if (r) m *= 1 + param(r, 'damage');
    }
    if (mob) {
      const marks = this.rt.marks.marks(mob);
      if (marks > 0) {
        const set2 = BUILD.sets.mark[0].effect;
        m *= 1 + marks * ((Number(set2.damagePerMark) || 0) + this.rt.stat('markDamageAdd'));
      }
    }
    return m;
  }

  /** 근접 타격 뒤 (살아 있으면 경직·표식·지속 피해, 강공 효과, 치명 금) */
  afterStrike(mob: Mob, p: PlayerAttackPayload & { buildMove?: string }, crit: boolean, died: boolean): void {
    const now = this.now;
    const strong = isStrongAttack(p);
    if (crit && !died) this.crackOnCrit(mob);
    this.rt.traits?.afterStrike(mob, p, died);
    if (died) return;
    for (const c of this.comboChange(p.comboIndex)) {
      if (c.stunMs) {
        mob.stun(now, c.stunMs, 'hit');
        this.rt.art.stagger(mob, c.stunMs);
      }
      if (c.brandBonus) for (let i = 0; i < c.brandBonus; i++) this.g.strikes.brands.onHit(mob, p.dirX, p.dirY);
    }
    this.onHitCommon(mob, p.dirX, p.dirY, strong);
  }

  /** 61 G 개성 (갈라진 투구·별 표적): 이 적의 다음 타격을 ms 안 확정 치명으로 */
  crackMob(mob: Mob, ms: number): void {
    if (mob.active) this.cracked.set(mob, this.now + ms);
  }

  /** 급소 6 '금': 치명타를 맞고 살아남은 적 → ms 안 다음 타격 확정 치명 */
  crackOnCrit(mob: Mob): void {
    const r = this.rt.rule('critCrack');
    if (r) this.cracked.set(mob, this.now + param(r, 'ms'));
  }

  /** 근접·투사체 공통: 표식 · 지속 피해 부여 · 강공 경직·밀쳐냄 · 기폭 */
  onHitCommon(mob: Mob, dirX: number, dirY: number, strong: boolean): void {
    const now = this.now;
    if (!mob.active) return;
    // 표식 (표식 2 — 같은 적 hits 타마다, 붉은 분필은 세트 없이도)
    const mark2 = this.rt.rule('markOnHits');
    const fallback = this.rt.rule('markFallback');
    if (mark2 || fallback) {
      const set2 = BUILD.sets.mark[0].effect;
      const hits = mark2 ? param(mark2, 'hits', 3) : param(fallback!, 'hits', 3);
      const before = this.rt.marks.marks(mob);
      this.rt.marks.hit(mob, now, hits, Number(set2.max) || 3);
      const after = this.rt.marks.marks(mob);
      if (after !== before)
        EventBus.emit(Events.MARK_CHANGED, { marks: after, delta: after - before } satisfies MarkChangedPayload);
    }
    // 출혈 (깨진 잔 조각) · 화상 (불붙은 혀 영구)
    const bleed = this.rt.rule('bleedOnHit');
    if (bleed && this.g.rng.chance(param(bleed, 'chance'))) {
      this.applyDot(mob, 'bleed', param(bleed, 'ms'), param(bleed, 'tickMs'), param(bleed, 'tickMult'));
      emitProc(bleed);
    }
    const burnChance = gameState.build.permanentBurnChance;
    if (burnChance > 0 && this.g.rng.chance(burnChance)) {
      const B = curseDef('burningTongue')?.burn;
      if (B) this.applyDot(mob, 'burn', B.ms, B.tickMs, B.tickMult);
    }
    if (!strong) return;
    // 중량 4: 강공 경직 +·밀쳐냄
    const impact = this.rt.rule('heavyImpact');
    if (impact) {
      mob.stun(now, param(impact, 'stunMs'), 'hit');
      this.rt.art.stagger(mob, param(impact, 'stunMs'));
      if (!mob.isBoss) mob.shove(dirX, dirY, T(param(impact, 'knockTiles')), 160);
    }
    // 잔불 심장: 강공 적중 지점 불 웅덩이
    const ember = this.rt.rule('emberHeart');
    if (ember) {
      emitProc(ember);
      const c = mob.body.center;
      this.rt.fx.firePatch(
        c.x,
        c.y,
        T(param(ember, 'radiusTiles', 1)),
        param(ember, 'ms'),
        param(ember, 'tickMs'),
        param(ember, 'tickMult'),
      );
    }
    // 표식 6: 표식 3 이상 적에게 강공 → 기폭
    const det = this.rt.rule('markDetonate');
    if (det && this.rt.marks.marks(mob) >= param(det, 'min', 3)) {
      this.rt.marks.take(mob);
      const c = mob.body.center;
      const r = T(param(det, 'radiusTiles'));
      this.rt.fx.ring(c.x, c.y, r, BUILD_FX.COLOR.MARK);
      for (const m of this.rt.fx.inCircle(c.x, c.y, r))
        this.rt.fx.damage(m, param(det, 'attackMult'), { dirX, dirY, heavy: true });
      this.rt.record('markDetonate');
    }
  }

  /** 지속 피해 걸기 (상흔 2 지속 +50%) — 틱 피해 = 공격력 × tickMult. 끓음(상흔 4) 검사 */
  applyDot(mob: Mob, kind: DotKind, ms: number, tickMs: number, tickMult: number): void {
    if (!mob.active) return;
    const now = this.now;
    const dur = ms * (1 + this.rt.stat('dotDurationMult'));
    const dmg = Math.max(1, Math.round(buildAttack() * tickMult));
    this.rt.dots.apply(mob, kind, now, dur, tickMs, dmg);
    const boil = this.rt.rule('dotBoil');
    if (boil && this.rt.dots.has(mob, 'bleed', now) && this.rt.dots.has(mob, 'burn', now)) {
      const total = this.rt.dots.take(mob, now);
      const c = mob.body.center;
      const r = T(param(boil, 'radiusTiles'));
      // status_boil (반지름 96 도트) — 없으면 윤곽
      if (!this.rt.art.onceAtMob(BUILD_ART.BOIL, mob)) this.rt.fx.ring(c.x, c.y, r, BUILD_FX.COLOR.BURN);
      EventBus.emit(Events.STATUS_BURST, { kind: 'boil', x: c.x, y: c.y } satisfies StatusBurstPayload);
      for (const m of this.rt.fx.inCircle(c.x, c.y, r)) this.rt.fx.raw(m, total, { dirX: 0, dirY: 0, tick: true });
      this.rt.record('boil', total);
    }
  }

  // --- 투사체 · 처치 · 이동기 (분리 모듈로) ---

  shotMods(): { speedMult: number; lifeMult: number; pierceAdd: number } {
    return this.shots.shotMods();
  }

  onShotSpawn(shot: Projectile): void {
    this.shots.onShotSpawn(shot);
  }

  shotBonus(shot: Projectile, mob: Mob): { mult: number; forceCrit: boolean } {
    return this.shots.shotBonus(shot, mob);
  }

  afterShot(shot: Projectile, mob: Mob, crit: boolean, died: boolean): void {
    this.shots.afterShot(shot, mob, crit, died);
  }

  onKill(mob: Mob, kind: string): void {
    this.kills.onKill(mob, kind);
    this.rt.traits.onKill(mob, kind);
  }

  restoreResource(pr: Record<string, unknown>): void {
    this.kills.restoreResource(pr);
  }

  onMove(x: number, y: number, dirX: number, dirY: number, kind: 'dash' | 'shadowstep', distPx?: number): void {
    this.passives.onMove(x, y, dirX, dirY, kind, distPx);
  }

  // --- 배율 (매 프레임 Player 에 넣는다) ---

  moveSpeedMult(now: number): number {
    let m = 1;
    const crisis = BUILD.sets.endure[1].effect;
    if (now < this.crisisHasteUntil) m *= 1 + (Number(crisis.haste) || 0);
    const road = this.rt.rule('splitRoad');
    if (road && now < this.splitRoadUntil) m *= 1 + param(road, 'haste');
    m *= this.rt.branch.moveSpeedMult(now);
    return m;
  }

  attackSpeedMult(now: number): number {
    let m = 1;
    const h = this.rt.rule('killHaste');
    if (h && this.kills.hasteActive(now)) m *= 1 + param(h, 'attackSpeed');
    m *= this.rt.branch.attackSpeedMult(now);
    m *= this.rt.traits.attackSpeedMult();
    return m;
  }

  /** 아슬아슬: 완벽 회피 뒤 다음 공격 배율 */
  empowerNext(mult: number, windowMs: number): void {
    this.empower = { until: this.now + windowMs, mult };
  }

  /** 개성 배율 (살기 ×2) */
  personalityMult(): number {
    return this.kills.personalityMult();
  }

  // --- 매 프레임: 지속 피해 틱 · 표식 정리·그리기 ---

  update(now: number): void {
    for (const [mob, kind, dmg] of this.rt.dots.tick(now)) {
      if (!mob.active) continue;
      if (kind === 'bleed') mob.flashColor(BUILD_FX.COLOR.BLEED);
      const died = this.rt.fx.raw(mob, dmg, { dirX: 0, dirY: 0, tick: true, killKind: 'environment' });
      if (died) this.rt.record('dotKill');
    }
    const set2 = BUILD.sets.mark[0].effect;
    this.rt.marks.expire(now, Number(set2.lifeMs) || 8000, (m) => m.active);
    for (const [m, until] of this.cracked) if (!m.active || until <= now) this.cracked.delete(m);
    this.drawMarks();
  }

  private drawMarks(): void {
    const gfx = this.markGfx;
    gfx.clear();
    for (const [m, n] of this.rt.marks.list()) {
      const top = m.body.top - BUILD_FX.MARK_LIFT_PX;
      const x0 = m.body.center.x - ((n - 1) * BUILD_FX.MARK_DOT_GAP) / 2;
      gfx.fillStyle(BUILD_FX.COLOR.MARK, 1);
      for (let i = 0; i < n; i++) gfx.fillCircle(x0 + i * BUILD_FX.MARK_DOT_GAP, top, BUILD_FX.MARK_DOT_R);
    }
    for (const m of this.rt.dots.list()) {
      if (!m.active) continue;
      const now = this.now;
      const c = this.rt.dots.has(m, 'burn', now) ? BUILD_FX.COLOR.BURN : BUILD_FX.COLOR.BLEED;
      gfx
        .lineStyle(1, c, 0.8)
        .strokeCircle(m.body.center.x, m.body.center.y, Math.max(m.body.halfWidth, m.body.halfHeight) + 2);
    }
  }

  debug(): Record<string, unknown> {
    const now = this.now;
    return {
      haste: this.kills.hasteActive(now),
      bloodlust: this.kills.bloodlustActive(now),
      empower: this.empower && now < this.empower.until ? this.empower.mult : 0,
      cracked: this.cracked.size,
      fistChain: this.passives.fistChain,
    };
  }

  destroy(): void {
    this.markGfx.destroy();
    this.cracked.clear();
  }
}
