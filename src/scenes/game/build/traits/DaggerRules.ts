/**
 * 단검 개성·셋째 갈래 '백귀' 규칙 (61 G → 61 단계 5 P13 전투 양상):
 * 뽑아 던지기(찌르기 처치 → 다음 적에게 단검 투척) · 낙인 사슬(낙인 셋 이상 적 → 가장 가까운 적을 끌어와 부딪침) ·
 * 그림자 매듭(낙인 유지 + 묶음 — BrandMarks) · 되짚어 걷기(그림자 걸음 뒤 처음 자리로 되돌아오며 벰) · 스치는 낙인 · 꿰찌르기 ·
 * 휘감는 난타 · 불티 난타(난타 끝 → 술 웅덩이 점화·화상) · 분신 방패 / 백귀 길: 야행 · 귀화.
 * 백귀 1차(그림자)·그림자 사냥(묶음)·취한 그림자(점화)·돌아오는 칼(끌고 옴)·독주 투척은 DaggerBranch·BuildDefense 가 실행한다.
 */
import { BUILD_ART, BUILD_FX, DEPTH, TILE } from '../../../../core/Constants';
import type { PlayerAttackPayload, PlayerSkillPayload } from '../../../../core/EventBus';
import { gameState } from '../../../../core/GameState';
import type { Mob } from '../../../../objects/Mob';
import { T, type Pt, type RuleKit } from './RuleKit';

export class DaggerRules {
  /** 스치는 낙인: 대쉬가 끝나는 시각 · 이번 대쉬에 낙인을 준 적 */
  private dashUntil = -Infinity;
  private readonly dashMarked = new Set<Mob>();
  /** 휘감는 난타 중 · 다음 당김 시각 */
  private flurryOn = false;
  private pullAt = -Infinity;
  /** 분신 방패 창 · 야행 흐려짐 끝 */
  private shieldUntil = -Infinity;
  private veilUntil = -Infinity;
  private chainReadyAt = -Infinity;
  /** 스치는 낙인 그림 방향 (대쉬 가로 방향) · 휘감는 난타 그림 각도 */
  private dashDirX = 1;
  private pullAngle = 0;
  /** 공명(얽힌 급소)이 듣는 '낙인 터짐' */
  onBurst: ((mob: Mob) => void) | null = null;

  constructor(private readonly k: RuleKit) {}

  onAttack(p: PlayerAttackPayload): void {
    const k = this.k;
    const r = k.rt.rule('dashPierce');
    if (!r || p.kind !== 'dashAttack') return;
    k.g.time.delayedCall(Math.max(0, p.swingDelayMs), () => {
      if (!k.g.scene.isActive()) return;
      const pl = k.g.player;
      const dir = { x: p.dirX, y: p.dirY };
      const from = { x: pl.x + dir.x * TILE * 0.5, y: pl.y + dir.y * TILE * 0.5 };
      const played = k.moves.fx('d_dashPierce', from, {
        angle: Math.atan2(dir.y, dir.x),
        fallbacks: ['dagger_combo3_double'],
      });
      const hits = k.cloneLine(
        from,
        dir,
        T(k.p(r, 'lengthTiles', 2.5)),
        T(k.p(r, 'widthTiles', 0.8)) / 2,
        k.p(r, 'damageMult', 0.7),
        BUILD_FX.COLOR.THROW,
        played?.own !== true,
      );
      k.fire('d_dashPierce', 'pierce', { hits: hits.length });
    });
  }

  onDash(p: { x: number; y: number; dirX: number; dirY: number }): void {
    this.dashDirX = p.dirX;
    if (!this.k.rt.rule('dashBrand')) return;
    this.dashUntil = this.k.now + 260;
    this.dashMarked.clear();
  }

  onSkill(p: PlayerSkillPayload): void {
    const k = this.k;
    if (p.move !== 'flurry') return;
    if (p.phase === 'start') this.flurryOn = true;
    if (p.phase !== 'end') return;
    this.flurryOn = false;
    // 불티 난타: 난타가 끝나면 불티 — 둘레 술 웅덩이 점화 · 맞은 적 화상
    const r = k.rt.rule('flurrySparks');
    if (!r) return;
    const pl = k.g.player;
    const rad = T(k.p(r, 'radiusTiles', 2));
    for (let i = 0; i < 3; i++)
      k.g.time.delayedCall(i * 60, () => {
        if (k.g.scene.isActive()) k.moves.sparks({ x: pl.x + (i - 1) * 8, y: pl.y - 10 });
      });
    if (!k.moves.fx('d_sparkFlurry', pl, { fallbacks: ['dagger_hotwind_burst', 'fire_bottle_burst'], scale: 0.7 }))
      k.rt.fx.ring(pl.x, pl.y, rad, BUILD_FX.COLOR.BURN, 240);
    const lit = k.moves.igniteCircle(pl, rad);
    const hits = k.rt.fx.inCircle(pl.x, pl.y, rad);
    for (const m of hits)
      k.rt.combat.applyDot(m, 'burn', k.p(r, 'burnMs', 1500), k.p(r, 'burnTickMs', 500), k.p(r, 'burnMult', 0.2));
    k.fire('d_sparkFlurry', lit > 0 ? 'ignite' : 'sparks', { hits: hits.length, lit });
  }

  /** 그림자 걸음 (BuildRuntime.onShadowStep): 되짚어 걷기 · 야행 */
  onShadowStep(from: Pt, to: Pt): void {
    const k = this.k;
    const pl = k.g.player;
    const back = k.rt.rule('stepReturn');
    if (back && Math.hypot(to.x - from.x, to.y - from.y) > TILE) {
      k.g.time.delayedCall(k.p(back, 'delayMs', 450), () => {
        if (!k.g.scene.isActive() || !pl.active || !k.g.world.isWalkableAt(from.x, from.y)) return;
        const at = { x: pl.x, y: pl.y };
        const d = { x: from.x - at.x, y: from.y - at.y };
        const len = Math.hypot(d.x, d.y);
        if (len < TILE * 0.5) return;
        // 그림 = 처음 자리가 왼쪽 — 오른쪽이면 뒤집는다 (art §27 flipNote)
        const flipX = from.x > at.x;
        const played = k.moves.fx('d_stepBack', at, { part: 'out', fallbacks: ['shadowstep_ghost'], flipX });
        pl.teleportTo(from.x, from.y);
        k.cloneLine(
          at,
          d,
          len,
          T(k.p(back, 'widthTiles', 0.9)) / 2,
          k.p(back, 'damageMult', 0.6),
          BUILD_FX.COLOR.CLONE,
          played?.own !== true,
        );
        k.moves.fx('d_stepBack', from, { part: 'in', fallbacks: ['shadowstep_ghost'], flipX });
        k.fire('d_stepBack', 'return');
      });
    }
    const nw = k.rt.rule('nightwalk');
    if (nw) {
      const ms = k.p(nw, 'invulnMs', 1000);
      pl.grantInvulnerable(k.now + ms);
      this.veilUntil = k.now + ms;
      pl.setAlpha(k.p(nw, 'alpha', 0.45));
      k.fire('nightwalk', 'veil');
    }
  }

  /** 그림자 매듭 (BrandMarks.onShadowStep): 낙인이 남은 적을 그림자로 묶는다 */
  onShadowKnot(mob: Mob, ms: number): void {
    const k = this.k;
    if (!k.moves.bind(mob, ms, 'd_shadowKnot')) return;
    k.moves.fx('d_shadowKnot', { x: mob.x, y: mob.y }, { fallbacks: ['dagger_brand_mark'] });
    k.fire('d_shadowKnot', 'bind');
  }

  onBrandBurst(mob: Mob, marks: number, _died: boolean): void {
    const k = this.k;
    // 분신 방패 창 (쌍격 분신 교차 베기 직후)
    const sh = k.rt.rule('cloneShield');
    if (sh && k.rt.hasBranch('twin')) this.shieldUntil = k.now + k.p(sh, 'windowMs', 1500);
    this.onBurst?.(mob);
    // 귀화: 낙인 불이 옆 적에게 번진다
    const oni = k.rt.rule('onibi');
    if (!oni || marks <= 0) return;
    const at = mob.body ? { x: mob.body.center.x, y: mob.body.center.y } : { x: mob.x, y: mob.y - 8 };
    const skip = new Set<Mob>([mob]);
    const n = k.p(oni, 'targets', 2);
    for (let i = 0; i < n; i++) {
      const next = k.rt.fx.nearest(at.x, at.y, T(k.p(oni, 'rangeTiles', 2.5)), skip);
      if (!next) break;
      skip.add(next);
      k.rt.branch.dagger.hopBrands(at, next, k.p(oni, 'brands', 2), { x: next.x - at.x, y: next.y - at.y });
    }
    if (skip.size > 1) k.fire('onibi', 'spread', { targets: skip.size - 1 });
  }

  /** 낙인 사슬: 낙인 셋 이상 적을 찌르면 가장 가까운 적을 사슬로 끌어와 부딪친다 */
  afterStrike(mob: Mob, _p: PlayerAttackPayload, died: boolean): void {
    const k = this.k;
    const r = k.rt.rule('brandChain');
    if (!r || died || !mob.active || k.now < this.chainReadyAt) return;
    if (k.g.strikes.brands.marksOf(mob) < k.p(r, 'min', 3)) return;
    const other = k.rt.fx.nearest(mob.x, mob.y, T(k.p(r, 'rangeTiles', 4)), new Set([mob]));
    if (!other || other.isBoss) return;
    this.chainReadyAt = k.now + k.p(r, 'cooldownMs', 700);
    k.moves.chainLine({ x: mob.x, y: mob.y - 8 }, { x: other.x, y: other.y - 8 });
    k.moves.fx(
      'd_brandChain',
      { x: (mob.x + other.x) / 2, y: (mob.y + other.y) / 2 - 8 },
      {
        angle: Math.atan2(other.y - mob.y, other.x - mob.x),
        lengthPx: Math.hypot(other.x - mob.x, other.y - mob.y),
        fallbacks: ['dagger_brand_hop'],
      },
    );
    // 이 적은 조금 끌려가고, 옆 적은 이 적에게 끌려와 부딪친다
    if (!mob.isBoss) mob.shove(other.x - mob.x, other.y - mob.y, TILE * 0.3, 120);
    k.moves.pull(other, mob, Math.hypot(other.x - mob.x, other.y - mob.y) / TILE, 'd_brandChain', {
      stopTiles: 0,
      slamMult: k.p(r, 'slamMult', 0.5),
      slamStunMs: k.p(r, 'slamStunMs', 600),
    });
    k.fire('d_brandChain', 'chain');
  }

  onKill(mob: Mob): void {
    const k = this.k;
    const r = k.rt.rule('killThrow');
    if (!r || !k.recentAttack(k.p(r, 'windowMs', 400), (p) => p.comboIndex !== undefined)) return;
    // 뽑아 던지기: 쓰러진 적에게서 단검을 뽑아 가장 가까운 적에게
    const at = { x: mob.x, y: mob.y - 8 };
    const next = k.rt.fx.nearest(at.x, at.y, T(k.p(r, 'rangeTiles', 5)), new Set([mob]));
    if (!next) return;
    k.shot(at, { x: next.x - at.x, y: next.y - 8 - at.y }, k.p(r, 'damageMult', 0.7), {
      tag: 'pullThrow',
      speedTiles: k.p(r, 'speedTiles', 16),
      rangeTiles: k.p(r, 'rangeTiles', 5) + 1,
      sprite: BUILD_ART.THROWN,
    });
    k.moves.fx('d_pullThrow', at, { fallbacks: ['dagger_brand_burst'], scale: 0.6 });
    k.fire('d_pullThrow', 'throw');
  }

  /** 분신 방패: 창 안 처음 맞는 한 번은 분신이 대신 맞는다 */
  evadeHit(time: number): boolean {
    if (time >= this.shieldUntil) return false;
    this.shieldUntil = -Infinity;
    const k = this.k;
    const pl = k.g.player;
    pl.grantInvulnerable(time + 300);
    k.rt.fx.clone(pl.x + TILE * 0.4, pl.y);
    // 그림 = 오른쪽에서 맞음 — 왼쪽을 보고 있으면(왼쪽에서 맞았다고 보고) 뒤집는다
    k.moves.fx('d_cloneShield', pl, { fallbacks: ['dagger_frenzy_clone_out'], flipX: pl.facingVec.x < 0 });
    k.fire('d_cloneShield', 'block');
    return true;
  }

  update(now: number): void {
    const k = this.k;
    const pl = k.g.player;
    if (!pl) return;
    // 스치는 낙인: 대쉬 중 몸에 스친 적
    if (now < this.dashUntil) {
      const r = k.rt.rule('dashBrand');
      if (r)
        for (const m of k.rt.fx.inCircle(pl.x, pl.y, T(k.p(r, 'radiusTiles', 0.8)))) {
          if (this.dashMarked.has(m)) continue;
          this.dashMarked.add(m);
          k.g.strikes.brands.onHit(m, m.x - pl.x, m.y - pl.y);
          k.moves.fx('d_dashBrand', { x: m.x, y: m.y - 8 }, { fallbacks: ['hit_dagger'], flipX: this.dashDirX < 0 });
          k.fire('d_dashBrand', 'mark');
        }
    }
    // 휘감는 난타: 난타 중 둘레 적을 조금씩 끌어당긴다
    const pull = k.rt.rule('flurryPull');
    if (pull && this.flurryOn && now >= this.pullAt) {
      this.pullAt = now + k.p(pull, 'everyMs', 250);
      let n = 0;
      for (const m of k.rt.fx.inCircle(pl.x, pl.y, T(k.p(pull, 'radiusTiles', 2.5)))) {
        const d = Math.hypot(m.x - pl.x, m.y - pl.y);
        if (d <= TILE * 0.8) continue;
        k.push(m, { x: pl.x - m.x, y: pl.y - m.y }, k.p(pull, 'pullTiles', 0.5), 120);
        k.moves.chainLine(m, pl, BUILD_FX.COLOR.CLONE, 160);
        n += 1;
      }
      if (n > 0) {
        // art §27: 250ms 마다 다시 틀며 칸마다 22° 돌려 계속 감기게
        this.pullAngle += Math.PI / 8.2;
        k.moves.fx('d_flurryPull', pl, { depth: DEPTH.FX_GROUND, angle: this.pullAngle });
        k.fire('d_flurryPull', 'pull');
      }
    }
    // 야행: 흐려짐 끝
    if (this.veilUntil > -Infinity && now >= this.veilUntil) {
      this.veilUntil = -Infinity;
      pl.setAlpha(1);
    }
  }

  debug(): Record<string, unknown> {
    return { shield: this.k.now < this.shieldUntil, flurryPull: this.flurryOn, weapon: gameState.weapon.id };
  }

  destroy(): void {
    this.dashMarked.clear();
    this.onBurst = null;
    if (this.veilUntil > -Infinity) this.k.g.player?.setAlpha(1);
  }
}
