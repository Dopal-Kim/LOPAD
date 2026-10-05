/**
 * 61 G 단검 개성·셋째 갈래 '백귀' 규칙: 몰아치기 · 급소 낙인(TraitRules.forceCrit) · 그림자 매듭(BrandMarks) · 이어 걷기 · 스치는 낙인 ·
 * 꿰찌르기 · 휘감는 난타 · 마무리 기폭 · 분신 방패 / 백귀 길: 야행(그림자 걸음 뒤 무적·흐려짐) · 귀화(낙인 폭발이 옆 적에게 번짐).
 * 백귀 1차(그림자 걸음 쿨 반감·기폭마다 그림자)·그림자 사냥·취한 그림자·돌아오는 칼은 DaggerBranch·BuildDefense 가 실행한다.
 */
import { BUILD_FX, TILE } from '../../../../core/Constants';
import type { PlayerAttackPayload, PlayerSkillPayload } from '../../../../core/EventBus';
import { gameState } from '../../../../core/GameState';
import type { Mob } from '../../../../objects/Mob';
import { T, type RuleKit } from './RuleKit';

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
      const hits = k.cloneLine(
        from,
        dir,
        T(k.p(r, 'lengthTiles', 2.5)),
        T(k.p(r, 'widthTiles', 0.8)) / 2,
        k.p(r, 'damageMult', 0.7),
        BUILD_FX.COLOR.THROW,
      );
      k.fire('d_dashPierce', 'pierce', { hits: hits.length });
    });
  }

  onDash(_p: { x: number; y: number; dirX: number; dirY: number }): void {
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
    // 마무리 기폭: 난타가 끝나면 가까운 적의 낙인
    const r = k.rt.rule('flurryDetonate');
    if (!r) return;
    const pl = k.g.player;
    const brands = k.g.strikes.brands;
    const near = k.rt.fx
      .inCircle(pl.x, pl.y, T(k.p(r, 'rangeTiles', 2)))
      .filter((m) => brands.marksOf(m) > 0)
      .sort((a, b) => Math.hypot(a.x - pl.x, a.y - pl.y) - Math.hypot(b.x - pl.x, b.y - pl.y))[0];
    if (near && brands.detonate(near, 'flurry')) k.fire('d_flurryBurst', 'burst');
  }

  onShadowStep(): void {
    const k = this.k;
    const pl = k.g.player;
    if (k.rt.rule('stepDashReset')) {
      pl.resetDash();
      k.fire('d_stepReset', 'reset');
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

  onBrandBurst(mob: Mob, marks: number, _died: boolean): void {
    const k = this.k;
    // 분신 방패 창 (쌍격 분신 교차 베기 직후)
    const sh = k.rt.rule('cloneShield');
    if (sh && k.rt.hasBranch('twin')) this.shieldUntil = k.now + k.p(sh, 'windowMs', 1500);
    // 귀화: 낙인 불이 옆 적에게 번진다
    const oni = k.rt.rule('onibi');
    if (!oni || marks <= 0) return;
    const at = { x: mob.body.center.x, y: mob.body.center.y };
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

  onKill(_mob: Mob): void {
    const k = this.k;
    const r = k.rt.rule('killMaxHeat');
    if (!r || !k.recentAttack(k.p(r, 'windowMs', 400), (p) => p.comboIndex !== undefined)) return;
    const res = k.g.player.resource;
    if (res?.kind === 'heat') {
      res.heatBy(res.max, k.now);
      k.fire('d_killRush', 'rush');
    }
  }

  /** 분신 방패: 창 안 처음 맞는 한 번은 분신이 대신 맞는다 */
  evadeHit(time: number): boolean {
    if (time >= this.shieldUntil) return false;
    this.shieldUntil = -Infinity;
    const k = this.k;
    const pl = k.g.player;
    pl.grantInvulnerable(time + 300);
    k.rt.fx.clone(pl.x + TILE * 0.4, pl.y);
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
          k.fire('d_dashBrand', 'mark');
        }
    }
    // 휘감는 난타: 난타 중 둘레 적을 조금씩 끌어당긴다
    const pull = k.rt.rule('flurryPull');
    if (pull && this.flurryOn && now >= this.pullAt) {
      this.pullAt = now + k.p(pull, 'everyMs', 250);
      for (const m of k.rt.fx.inCircle(pl.x, pl.y, T(k.p(pull, 'radiusTiles', 2.5)))) {
        const d = Math.hypot(m.x - pl.x, m.y - pl.y);
        if (d > TILE * 0.8) k.push(m, { x: pl.x - m.x, y: pl.y - m.y }, k.p(pull, 'pullTiles', 0.5), 120);
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
    if (this.veilUntil > -Infinity) this.k.g.player?.setAlpha(1);
  }
}
