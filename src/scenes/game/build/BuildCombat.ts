/**
 * 57라운드 빌드 축 — 타격·투사체·처치·이동기 규칙 (BuildRuntime 의 일부):
 * 세트 급소 6(금)·상흔(지속 피해·끓음·옮겨붙음)·연쇄(공속·자원·살기)·원격(사거리·관통·분열)·중량(강공 피해·경직)·표식(표식·옮겨감·기폭)·
 * 돌파 4(이동 경로 베기) · 취기 6(술바다) · 패시브 규칙(깨진 잔 조각·불붙은 소매·사냥 표지·붉은 분필·아슬아슬·피 냄새·흩어진 촉·도미노·
 * 장교의 견장·깨진 거울·잔불 심장·엎지른 술·독한 숨·취권) · 갈래 연격 한 타 변화 · 저주 화상(불붙은 혀).
 */
import Phaser from 'phaser';
import { BUILD_FX, DEPTH, TILE } from '../../../core/Constants';
import type { PlayerAttackPayload } from '../../../core/EventBus';
import { gameState } from '../../../core/GameState';
import { BUILD, curseDef } from '../../../data/build';
import { PLAYER_DATA } from '../../../data';
import type { ComboChangeDef } from '../../../data/buildTypes';
import type { Mob } from '../../../objects/Mob';
import type { Projectile } from '../../../objects/Projectile';
import { param } from '../../../systems/build/buildMods';
import { isStrongAttack } from '../../../systems/build/strikeKinds';
import type { DotKind } from '../../../systems/build/statusBooks';
import type { Game } from '../../Game';
import type { BuildRuntime } from './BuildRuntime';

const T = (tiles: number) => tiles * TILE;

/** 이 공격(페이로드)에 붙은 일회성 배율 (아슬아슬·취보 반격·독한 숨 …) */
interface PayloadBonus {
  mult: number;
  forceCrit: boolean;
}

export class BuildCombat {
  /** 연쇄 2: 공속 +15% 끝 · 연쇄 6 살기 끝 · 최근 처치 시각들 */
  private hasteUntil = -Infinity;
  private bloodlustUntil = -Infinity;
  private killTimes: number[] = [];
  /** 아슬아슬: 다음 공격 배율 (완벽 회피 뒤) */
  private empower: { until: number; mult: number } | null = null;
  /** 급소 6 '금': 치명타를 맞은 적 → 다음 타격 치명 */
  private readonly cracked = new Map<Mob, number>();
  /** 공격 페이로드 → 일회성 배율 */
  private readonly payloadBonus = new WeakMap<PlayerAttackPayload, PayloadBonus>();
  /** 깨진 거울: 대쉬 뒤 첫 공격을 분신이 한 번 더 (이미 썼으면 true) */
  private mirrorUsed = true;
  /** 취권 연속 횟수 · 비틀 끝 */
  private fistChain = 0;
  private fistStaggerUntil = -Infinity;
  /** 표식 점 그리기 */
  private readonly markGfx: Phaser.GameObjects.Graphics;
  /** 갈라진 길(이중 개성) 가속 끝 · 버팀 4 위기 가속 끝 */
  splitRoadUntil = -Infinity;
  crisisHasteUntil = -Infinity;
  /** 디버그 */
  private last: Record<string, unknown> = {};

  constructor(
    private readonly g: Game,
    private readonly rt: BuildRuntime,
  ) {
    this.markGfx = g.add.graphics().setDepth(DEPTH.HIT_FX);
  }

  private get now(): number {
    return this.g.time.now;
  }

  private get attack(): number {
    return gameState.attack * gameState.weapon.damageMult;
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
        this.g.time.delayedCall(Math.max(0, p.swingDelayMs), () => this.shortCrack(p, C));
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
    this.mirror(p);
    this.liquorBreath(p);
    this.drunkFist(p);
  }

  /** 4타 내려찍기 끝 짧은 균열 (파쇄 연격 변화) */
  private shortCrack(p: PlayerAttackPayload, C: NonNullable<ComboChangeDef['crack']>): void {
    const pl = this.g.player;
    const len = T(C.lengthTiles);
    const half = T(C.widthTiles) / 2;
    const reach = gameState.weapon.hitbox.reach;
    const x0 = pl.x + p.dirX * reach;
    const y0 = pl.y + p.dirY * reach;
    this.rt.fx.lineFx(x0, y0, p.dirX, p.dirY, len, half, BUILD_FX.COLOR.CRACK);
    for (const m of this.rt.fx.inLine(x0, y0, p.dirX, p.dirY, len, half))
      this.rt.fx.damage(m, p.damageMult * C.damageMult, { dirX: p.dirX, dirY: p.dirY, kind: 'attack' });
  }

  /** 깨진 거울: 대쉬 후 windowMs 안 첫 공격을 분신이 delayMs 뒤 한 번 더 (×damageMult) */
  private mirror(p: PlayerAttackPayload): void {
    const r = this.rt.rule('mirrorClone');
    if (!r || this.mirrorUsed || this.now - this.rt.dashAt > param(r, 'windowMs')) return;
    this.mirrorUsed = true;
    const pl = this.g.player;
    const at = { x: pl.x - p.dirX * T(0.6), y: pl.y - p.dirY * T(0.6) };
    const mult = param(r, 'damageMult');
    const reach = gameState.weapon.hitbox.reach * 1.6;
    this.g.time.delayedCall(param(r, 'delayMs'), () => {
      if (!this.g.scene.isActive()) return;
      this.rt.fx.clone(at.x, at.y);
      this.rt.fx.coneFx(at.x, at.y, p.dirX, p.dirY, reach, 120, BUILD_FX.COLOR.CLONE);
      for (const m of this.rt.fx.inCone(at.x, at.y, p.dirX, p.dirY, reach, 120))
        this.rt.fx.damage(m, p.damageMult * mult, {
          dirX: p.dirX,
          dirY: p.dirY,
          kind: p.kind === 'dashAttack' ? 'dashAttack' : 'attack',
        });
    });
    this.rt.record('mirror');
  }

  /** 독한 숨: 마시기 직후 다음 공격 1회 = 앞 원뿔 술 뿜기 (맞은 자리 웅덩이, 술불 위면 ×fireMult) */
  private liquorBreath(p: PlayerAttackPayload): void {
    const r = this.rt.rule('liquorBreath');
    if (!r || this.now >= this.rt.liquorBreathUntil) return;
    this.rt.liquorBreathUntil = -Infinity;
    const pl = this.g.player;
    const range = T(param(r, 'rangeTiles'));
    const arc = param(r, 'arcDeg', 60);
    const onFire = this.g.pools.of('structure').some((q) => q.rect.contains(pl.x, pl.y) && this.g.pools.burning(q));
    const mult = param(r, 'damageMult') * (onFire ? param(r, 'fireMult', 1) : 1);
    this.rt.fx.coneFx(pl.x, pl.y, p.dirX, p.dirY, range, arc, onFire ? BUILD_FX.COLOR.BURN : BUILD_FX.COLOR.LIQUOR);
    for (const m of this.rt.fx.inCone(pl.x, pl.y, p.dirX, p.dirY, range, arc)) {
      const c = m.body.center;
      this.rt.fx.damage(m, mult, { dirX: p.dirX, dirY: p.dirY });
      this.rt.fx.liquorPool(c.x, c.y, T(1), 6000);
    }
    this.rt.record('liquorBreath', { onFire });
  }

  /** 취권: 취기 중 대쉬 직후 windowMs 안 공격 = 휘는 2칸 돌진 베기 (연속 chain 회, 끝나면 비틀) */
  private drunkFist(p: PlayerAttackPayload): void {
    const r = this.rt.rule('drunkFist');
    const now = this.now;
    if (!r || !this.rt.drunkActive || now < this.fistStaggerUntil) return;
    if (now - this.rt.dashAt > param(r, 'windowMs') && this.fistChain === 0) return;
    if (now - this.rt.dashAt > param(r, 'windowMs') + 900) {
      this.fistChain = 0;
      return;
    }
    const pl = this.g.player;
    const dist = T(param(r, 'lungeTiles'));
    const side = this.fistChain % 2 === 0 ? 1 : -1;
    // 휘는 궤적: 진행 방향에서 ±25° 기울인 돌진
    const a = Math.atan2(p.dirY, p.dirX) + side * 0.44;
    pl.startLunge(Math.cos(a), Math.sin(a), dist, 160, now);
    const radius = T(param(r, 'radiusTiles', 1.2));
    const mult = param(r, 'damageMult');
    this.g.time.delayedCall(140, () => {
      if (!this.g.scene.isActive()) return;
      this.rt.fx.ring(pl.x, pl.y, radius, BUILD_FX.COLOR.DRUNK_TINT);
      for (const m of this.rt.fx.inCircle(pl.x, pl.y, radius))
        this.rt.fx.damage(m, mult, { dirX: Math.cos(a), dirY: Math.sin(a), kind: 'dashAttack' });
    });
    this.fistChain += 1;
    this.rt.dashAt = now; // 다음 연속 창
    if (this.fistChain >= param(r, 'chain', 3)) {
      this.fistChain = 0;
      this.fistStaggerUntil = now + param(r, 'staggerMs');
      pl.slowUntil(now + param(r, 'staggerMs'));
    }
    this.rt.record('drunkFist', this.fistChain);
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
    if (this.now < this.bloodlustUntil) {
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
    if (crit && this.rt.rule('critCrack') && !died) {
      const r = this.rt.rule('critCrack')!;
      this.cracked.set(mob, now + param(r, 'ms'));
    }
    if (died) return;
    for (const c of this.comboChange(p.comboIndex)) {
      if (c.stunMs) mob.stun(now, c.stunMs, 'hit');
      if (c.brandBonus) for (let i = 0; i < c.brandBonus; i++) this.g.strikes.brands.onHit(mob, p.dirX, p.dirY);
    }
    this.onHitCommon(mob, p.dirX, p.dirY, strong);
  }

  /** 근접·투사체 공통: 표식 · 지속 피해 부여 · 강공 경직·밀쳐냄 · 기폭 */
  private onHitCommon(mob: Mob, dirX: number, dirY: number, strong: boolean): void {
    const now = this.now;
    if (!mob.active) return;
    // 표식 (표식 2 — 같은 적 hits 타마다, 붉은 분필은 세트 없이도)
    const mark2 = this.rt.rule('markOnHits');
    const fallback = this.rt.rule('markFallback');
    if (mark2 || fallback) {
      const set2 = BUILD.sets.mark[0].effect;
      const hits = mark2 ? param(mark2, 'hits', 3) : param(fallback!, 'hits', 3);
      this.rt.marks.hit(mob, now, hits, Number(set2.max) || 3);
    }
    // 출혈 (깨진 잔 조각) · 화상 (불붙은 혀 영구)
    const bleed = this.rt.rule('bleedOnHit');
    if (bleed && this.g.rng.chance(param(bleed, 'chance')))
      this.applyDot(mob, 'bleed', param(bleed, 'ms'), param(bleed, 'tickMs'), param(bleed, 'tickMult'));
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
      if (!mob.isBoss) mob.shove(dirX, dirY, T(param(impact, 'knockTiles')), 160);
    }
    // 잔불 심장: 강공 적중 지점 불 웅덩이
    const ember = this.rt.rule('emberHeart');
    if (ember) {
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
    const dmg = Math.max(1, Math.round(this.attack * tickMult));
    this.rt.dots.apply(mob, kind, now, dur, tickMs, dmg);
    const boil = this.rt.rule('dotBoil');
    if (boil && this.rt.dots.has(mob, 'bleed', now) && this.rt.dots.has(mob, 'burn', now)) {
      const total = this.rt.dots.take(mob, now);
      const c = mob.body.center;
      const r = T(param(boil, 'radiusTiles'));
      this.rt.fx.ring(c.x, c.y, r, BUILD_FX.COLOR.BURN);
      for (const m of this.rt.fx.inCircle(c.x, c.y, r)) this.rt.fx.raw(m, total, { dirX: 0, dirY: 0, tick: true });
      this.rt.record('boil', total);
    }
  }

  // --- 투사체 (BowShots · GameCombat.onPlayerShotHit) ---

  /** 화살·빌드 투사체 발사 배율: 사거리(수명)·속도·관통 (원격 2·4, 긴 시위) */
  shotMods(): { speedMult: number; lifeMult: number; pierceAdd: number } {
    return {
      speedMult: 1 + this.rt.stat('projectileSpeedMult'),
      lifeMult: (1 + this.rt.stat('projectileRangeMult')) / (1 + this.rt.stat('projectileSpeedMult')),
      pierceAdd: this.rt.stat('pierceAdd'),
    };
  }

  /** 화살 하나가 나감 — 끝날 때 흩어진 촉 */
  onShotSpawn(shot: Projectile): void {
    if (this.rt.rule('shotSplitAtEnd') && !shot.buildTag) shot.onEnd = (s) => this.splitAtEnd(s);
  }

  /** 투사체 적중 배율 (대상 배율 + 무한 관통이면 원격 4 피해 +15%) · 확정 치명 */
  shotBonus(shot: Projectile, mob: Mob): { mult: number; forceCrit: boolean } {
    let mult = this.damageMultFor(mob);
    if (shot.pierceLeft === Infinity) mult *= 1 + this.rt.stat('pierceDamageAdd');
    return { mult, forceCrit: this.forceCritOn(mob) };
  }

  afterShot(shot: Projectile, mob: Mob, crit: boolean, died: boolean): void {
    const v = shot.body.velocity;
    if (crit && !died && this.rt.rule('critCrack'))
      this.cracked.set(mob, this.now + param(this.rt.rule('critCrack')!, 'ms'));
    if (!died) this.onHitCommon(mob, v.x, v.y, this.rt.isStrongShot(shot));
    // 원격 6: 적중 시 확률 분열 (분열·파편은 다시 분열하지 않음)
    const split = this.rt.rule('projectileSplit');
    if (split && !shot.buildTag && this.g.rng.chance(param(split, 'chance'))) {
      const n = param(split, 'count', 2);
      const spread = (param(split, 'spreadDeg', 30) * Math.PI) / 180;
      const base = Math.atan2(v.y, v.x);
      const speed = v.length() / TILE;
      for (let i = 0; i < n; i++) {
        const a = base + (n === 1 ? 0 : (i / (n - 1) - 0.5) * spread);
        const s = this.rt.fx.shot(shot.x, shot.y, Math.cos(a), Math.sin(a), shot.attack * param(split, 'damageMult'), {
          tag: 'split',
          speedTiles: speed || 10,
          lifeMs: 500,
        });
        s?.registerHit(mob);
      }
    }
  }

  /** 흩어진 촉: 화살이 벽·사거리 끝에서 2발로 */
  private splitAtEnd(s: Projectile): void {
    const r = this.rt.rule('shotSplitAtEnd');
    if (!r) return;
    const v = s.body.velocity;
    const base = Math.atan2(v.y, v.x) + Math.PI;
    const spread = (param(r, 'spreadDeg', 50) * Math.PI) / 180;
    const n = param(r, 'count', 2);
    for (let i = 0; i < n; i++) {
      const a = base + (i / Math.max(1, n - 1) - 0.5) * spread;
      this.rt.fx.shot(
        s.x - Math.cos(base) * 2,
        s.y - Math.sin(base) * 2,
        Math.cos(a),
        Math.sin(a),
        s.attack * param(r, 'damageMult'),
        {
          tag: 'split',
          speedTiles: 9,
          lifeMs: 450,
        },
      );
    }
  }

  // --- 처치 (Progression.onKill) ---

  onKill(mob: Mob, kind: string): void {
    const now = this.now;
    const at = { x: mob.x, y: mob.y };
    const marks = this.rt.marks.take(mob);
    const brands = this.g.strikes.brands.marksOf(mob);
    const dot = this.rt.dots.snapshot(mob, now);
    const hadDot = dot.length > 0;
    this.rt.dots.forget(mob);
    this.cracked.delete(mob);
    this.rt.curseKill();
    // 연쇄 2·6
    if (this.rt.rule('killHaste')) this.hasteUntil = now + param(this.rt.rule('killHaste')!, 'ms');
    const bl = this.rt.rule('bloodlust');
    if (bl) {
      this.killTimes = this.killTimes.filter((t) => now - t <= param(bl, 'windowMs'));
      this.killTimes.push(now);
      if (this.killTimes.length >= param(bl, 'kills', 3) && now >= this.bloodlustUntil) {
        this.bloodlustUntil = now + param(bl, 'ms');
        this.killTimes = [];
        this.rt.record('bloodlust');
      }
    }
    // 연쇄 4: 무기 자원 회복
    const res = this.rt.rule('killResource');
    if (res) this.restoreResource(res.params);
    // 표식 4: 옮겨감
    const tr = this.rt.rule('markTransfer');
    if (tr && marks >= param(tr, 'min', 3)) {
      const next = this.rt.fx.nearest(at.x, at.y, T(param(tr, 'rangeTiles', 6)), new Set([mob]));
      if (next) this.rt.marks.set(next, marks, now);
    }
    // 사냥 표지
    const bounty = this.rt.rule('markKillBounty');
    if (bounty && (marks > 0 || brands > 0)) {
      this.g.economy.addGold(param(bounty, 'gold'));
      this.g.player.heal(param(bounty, 'heal'));
    }
    // 지속 피해로 죽은 적 → 옮겨붙음 (상흔 6 · 피 냄새)
    const spreadN =
      (hadDot && kind === 'environment' && this.rt.rule('dotSpread')
        ? param(this.rt.rule('dotSpread')!, 'count', 2)
        : 0) + (hadDot && this.rt.rule('dotKillSpread') ? param(this.rt.rule('dotKillSpread')!, 'count', 1) : 0);
    if (spreadN > 0) {
      const used = new Set([mob]);
      for (let i = 0; i < spreadN; i++) {
        const m = this.rt.fx.nearest(at.x, at.y, T(3), used);
        if (!m) break;
        used.add(m);
        for (const d of dot) this.rt.dots.apply(m, d.kind, now, d.ms, d.tickMs, d.dmg);
      }
    }
    // 도미노: 가장 가까운 적에게 재 파편
    const dom = this.rt.rule('killShard');
    if (dom) {
      const m = this.rt.fx.nearest(at.x, at.y, T(param(dom, 'rangeTiles', 8)), new Set([mob]));
      if (m)
        this.rt.fx.shot(at.x, at.y, m.x - at.x, m.y - at.y, this.attack * param(dom, 'damageMult'), {
          tag: 'shard',
          speedTiles: 12,
          lifeMs: 900,
        });
    }
    // 웅덩이 위 처치 = 마시기 (취기 2) · 엎지른 술 · 술바다
    const onPool = this.rt.fx.onPool(at.x, at.y);
    if (onPool && this.rt.stage('drunk') >= 2) this.rt.drink('poolKill');
    const spill = this.rt.rule('spillPool');
    if (spill && this.g.rng.chance(param(spill, 'chance')))
      this.rt.fx.liquorPool(at.x, at.y, T(param(spill, 'radiusTiles', 1)), param(spill, 'ms'));
    const sea = this.rt.rule('drunkSea');
    if (sea && this.rt.drunkActive)
      this.rt.fx.liquorPool(at.x, at.y, T(param(sea, 'poolRadiusTiles')), param(sea, 'poolMs'));
    this.rt.branch.onKill(mob, kind, { marks, brands, hadDot });
  }

  /** 연쇄 4 · 잔월 · 무한통 등: 무기 자원 회복 (params: kenkiStage 비율·grudge 비율·heat 비율(음수 = 식힘)·ammo 발·breath 점) */
  restoreResource(pr: Record<string, unknown>): void {
    const n = (k: string) => (typeof pr[k] === 'number' ? (pr[k] as number) : 0);
    const pl = this.g.player;
    const k = pl.gauges.kenki;
    if (k && n('kenkiStage')) k.value = Math.min(k.max, k.value + k.def.perStage * n('kenkiStage'));
    const gr = pl.gauges.grudge;
    if (gr && n('grudge')) gr.value = Math.min(gr.max, gr.value + gr.max * n('grudge'));
    const br = pl.gauges.breath;
    if (br && n('breath')) br.value = Math.min(br.max, br.value + n('breath'));
    const res = pl.resource;
    if (res?.kind === 'heat' && n('heat') && !res.overheated)
      res.value = Math.max(0, Math.min(res.max, res.value + res.max * n('heat')));
    if (res?.kind === 'ammo' && n('ammo')) res.value = Math.min(res.max, res.value + n('ammo'));
  }

  // --- 이동기 (대쉬·그림자 걸음) ---

  onMove(x: number, y: number, dirX: number, dirY: number, kind: 'dash' | 'shadowstep', distPx?: number): void {
    const len = distPx ?? this.dashDistance();
    this.mirrorUsed = false;
    // 돌파 4: 경로 베기 1회 (×0.8)
    const trail = this.rt.rule('moveTrail');
    if (trail && len > 0) {
      const half = T(param(trail, 'widthTiles', 1)) / 2;
      this.g.time.delayedCall(kind === 'dash' ? 90 : 0, () => {
        if (!this.g.scene.isActive()) return;
        this.rt.fx.lineFx(x, y, dirX, dirY, len, half, BUILD_FX.COLOR.SPIN);
        for (const m of this.rt.fx.inLine(x, y, dirX, dirY, len, half))
          this.rt.fx.damage(m, param(trail, 'damageMult'), { dirX, dirY, kind: 'dashAttack' });
      });
    }
    // 불붙은 소매: 경로 불씨
    const sleeve = this.rt.rule('dashEmbers');
    if (sleeve && len > 0) {
      const ms = param(sleeve, 'ms');
      const l = Math.hypot(dirX, dirY) || 1;
      const steps = Math.max(1, Math.round(len / TILE));
      for (let i = 0; i <= steps; i++) {
        const px = x + ((dirX / l) * (len * i)) / steps;
        const py = y + ((dirY / l) * (len * i)) / steps;
        this.rt.fx.firePatch(px, py, TILE / 2, ms, param(sleeve, 'tickMs'), param(sleeve, 'tickMult'));
      }
    }
    // 술바다: 취기 중 대쉬가 지나간 웅덩이 점화
    if (this.rt.rule('drunkSea') && this.rt.drunkActive && len > 0) {
      const l = Math.hypot(dirX, dirY) || 1;
      for (let d = 0; d <= len; d += TILE / 2) this.g.pools.igniteAt(x + (dirX / l) * d, y + (dirY / l) * d);
    }
    this.rt.branch.onPlayerMove(kind);
  }

  /** 대쉬 거리 px (데이터 player.dash.distanceTiles) */
  private dashDistance(): number {
    return PLAYER_DATA.dash.distanceTiles * TILE;
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
    if (h && now < this.hasteUntil) m *= 1 + param(h, 'attackSpeed');
    m *= this.rt.branch.attackSpeedMult(now);
    return m;
  }

  /** 아슬아슬: 완벽 회피 뒤 다음 공격 배율 */
  empowerNext(mult: number, windowMs: number): void {
    this.empower = { until: this.now + windowMs, mult };
  }

  /** 개성 배율 (살기 ×2) */
  personalityMult(): number {
    const bl = this.rt.rule('bloodlust');
    return bl && this.now < this.bloodlustUntil ? param(bl, 'personalityMult', 1) : 1;
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
      haste: now < this.hasteUntil,
      bloodlust: now < this.bloodlustUntil,
      empower: this.empower && now < this.empower.until ? this.empower.mult : 0,
      cracked: this.cracked.size,
      fistChain: this.fistChain,
      ...this.last,
    };
  }

  destroy(): void {
    this.markGfx.destroy();
    this.cracked.clear();
  }
}
