/**
 * 61 단계 5 (P13 §1-4) 공명 실행 — 같은 태그 개성 2장이 모이면 두 개성이 엮인다 (정의 `data/traits.json resonance`,
 * 켜짐 판정 `systems/growth/resonance`, 규칙은 합산에 source 'trait'·id = 공명 id 로 들어온다).
 * 칼: 되받는 달(밀치거나 끌어온 적 → 달 분신) · 칼바람 길(대쉬 길에 칼바람) · 끊이지 않는 칼(개성 처치 → 칼바람 퍼짐)
 * 대검: 무너뜨림(처박힌 자리 바닥이 갈라져 둘레가 튀어 오름) · 막고 되치는 대검(퍼펙트 가드·쳐내기 → 둘레 탄 전부 되침)
 * 단검: 얽힌 급소(묶이거나 끌려온 적의 낙인 폭발 → 옆 적까지 사슬 묶음) · 그림자 길(대쉬·그림자 걸음 길에 낙인 그림자)
 * 활: 말뚝 박기(밀쳐 내거나 끌어모은 적에 화살이 따라 꽂혀 묶음) · 덫 비(덫에 묶인 적 위로 하늘 화살)
 * 켜지는 순간: 시스템 RESONANCE_ON · UI `ui:resonance` · 알림 · 주인공 둘레 고리(전투 복귀 뒤). 발동은 BRANCH_EFFECT{branch: 공명 id}
 * → TraitRules 가 TRAIT_PROC{resonance}.
 */
import { BUILD_ART, BUILD_FX, DEPTH, TILE, TRAIT_FX } from '../../../../core/Constants';
import { EventBus, Events, type ResonanceOnPayload } from '../../../../core/EventBus';
import { gameState } from '../../../../core/GameState';
import { UI_EVENTS, __system } from '../../../../contract/ui';
import type { Mob } from '../../../../objects/Mob';
import type { ActiveRule } from '../../../../systems/build/buildMods';
import { activeResonances } from '../../../../systems/growth/resonance';
import { traitFxId } from '../../../../systems/growth/traitArt';
import { PLAYER_RENDER_SCALE } from '../../../../systems/weapon/playerScale';
import { uiResonance } from '../../../../systems/growth/uiGrowth';
import type { BowRules } from './BowRules';
import type { DaggerRules } from './DaggerRules';
import type { GreatswordRules } from './GreatswordRules';
import { T, type Pt, type RuleKit } from './RuleKit';
import type { SlamResult } from './TraitMoves';

interface Path {
  from: Pt;
  to: Pt;
  until: number;
  marked: Set<Mob>;
}

export class ResonanceRules {
  /** 켜진 공명 id (바뀌면 RESONANCE_ON) */
  private on: Set<string>;
  private trailReadyAt = -Infinity;
  private quakeReadyAt = -Infinity;
  /** 얽힌 급소: 묶이거나 끌려온 적 → 시각 */
  private readonly tangled = new Map<Mob, number>();
  private paths: Path[] = [];
  /** 디버그: 발동 수 */
  readonly counts: Record<string, number> = {};

  constructor(
    private readonly k: RuleKit,
    gs: GreatswordRules,
    dagger: DaggerRules,
    private readonly bow: BowRules,
  ) {
    this.on = this.activeIds();
    k.moves.listen({
      onSlam: (r) => this.onSlam(r),
      onDisplaced: (m, trait, how) => this.onDisplaced(m, trait, how),
      onBind: (m) => this.tangle(m),
    });
    gs.onDeflect = () => this.deflectAll(gs);
    dagger.onBurst = (m) => this.bindSpread(m);
    bow.onTrap = (m) => this.trapRain(m);
  }

  private activeIds(): Set<string> {
    const w = gameState.weapon;
    return new Set(activeResonances(w.id, w.traitDefs).map((r) => r.id));
  }

  private rule(kind: string) {
    return this.k.rt.rule(kind);
  }

  private proc(id: string, effect: string): void {
    this.counts[id] = (this.counts[id] ?? 0) + 1;
    this.k.fire(id, effect);
  }

  // --- 켜짐 ---

  /** 매 프레임: 켜진 공명이 늘면 알림 (개성 메뉴에서 고른 뒤 — 전투로 돌아와 고리) */
  private syncOn(): void {
    const now = this.activeIds();
    if (now.size === this.on.size && [...now].every((id) => this.on.has(id))) return;
    const w = gameState.weapon;
    for (const r of activeResonances(w.id, w.traitDefs)) {
      if (this.on.has(r.id)) continue;
      EventBus.emit(Events.RESONANCE_ON, {
        weapon: w.id,
        id: r.id,
        tag: r.tag,
        name: r.name,
      } satisfies ResonanceOnPayload);
      // 알림은 UI (`ui:resonance`) 하나로 — 시스템 notice 자막은 내지 않는다 (같은 말이 두 번 나오지 않게)
      __system.emit(UI_EVENTS.RESONANCE, uiResonance(r));
      this.k.rt.record('resonance', r.id);
      this.k.rt.afterMenu(() => {
        const pl = this.k.g.player;
        if (!pl) return;
        // art §27 공명 켜짐 고리 `trait_<공명 id>_on` (발동 fx `trait_<공명 id>` 와 이름이 겹쳐 부위 on)
        if (!this.k.moves.fx(r.id, pl, { part: 'on', fallbacks: [BUILD_ART.SET_FLASH] }))
          this.k.rt.fx.ring(pl.x, pl.y, TILE * 1.2, TRAIT_FX.RESONANCE_COLOR, 500);
      });
    }
    this.on = now;
  }

  // --- 칼 ---

  /** 되받는 달 · 말뚝 박기: 개성이 적을 밀거나 끌어옴 */
  private onDisplaced(mob: Mob, trait: string, how: 'push' | 'pull'): void {
    const k = this.k;
    if (how === 'pull' || trait === 'k_parryShove') this.tangle(mob);
    const moon = this.rule('resDisplaceClone');
    if (moon && (trait === 'k_parryShove' || trait === 'k_bladeBind')) {
      k.g.time.delayedCall(k.p(moon, 'delayMs', 200), () => {
        if (!k.g.scene.isActive() || !mob.active) return;
        const pl = k.g.player;
        const from = { x: mob.x - (mob.x - pl.x) * 0.3, y: mob.y - (mob.y - pl.y) * 0.3 };
        // art §27: 피벗 = 적 몸 중심(분신이 적 왼쪽에 그려짐) — 적이 주인공 왼쪽이면 뒤집는다
        const c = { x: mob.x, y: mob.y - 8 };
        const played = k.moves.fx('res_katana_insight', c, { flipX: mob.x < pl.x });
        if (!played) k.rt.art.once(BUILD_ART.FULLMOON, from.x, from.y, { scaleMult: PLAYER_RENDER_SCALE });
        k.cloneLine(
          from,
          { x: mob.x - from.x, y: mob.y - from.y },
          Math.hypot(mob.x - from.x, mob.y - from.y) + TILE * 0.6,
          TILE * 0.4,
          k.p(moon, 'damageMult', 0.5),
          BUILD_FX.COLOR.MOON,
          !played,
        );
        this.proc('res_katana_insight', 'clone');
      });
    }
    const pin = this.rule('resPinFollow');
    if (pin && (trait === 'b_pointBlank' || trait === 'b_rainSnare')) {
      k.g.time.delayedCall(k.p(pin, 'delayMs', 160) + (how === 'push' ? 220 : 120), () => {
        if (!k.g.scene.isActive() || !mob.active) return;
        k.hit(mob, k.p(pin, 'damageMult', 0.4), { x: 0, y: 1 });
        if (!mob.active) return;
        k.moves.bind(mob, k.p(pin, 'bindMs', 800), 'res_bow_weight');
        if (!k.moves.fx('res_bow_weight', { x: mob.x, y: mob.y - 4 }, { fallbacks: [BUILD_ART.ARROW_STUCK] }))
          k.rt.fx.ring(mob.x, mob.y, TILE * 0.4, BUILD_FX.COLOR.METEOR, 200);
        this.proc('res_bow_weight', 'pin');
      });
    }
  }

  /** 칼바람 길 · 그림자 길: 대쉬 시작 (끝 자리는 잠시 뒤 주인공 자리) */
  onDash(from: Pt): void {
    const k = this.k;
    const trail = this.rule('resDashTrail');
    const shadow = this.rule('resShadowPath');
    if (!trail && !shadow) return;
    k.g.time.delayedCall(trail ? k.p(trail, 'delayMs', 350) : 220, () => {
      if (!k.g.scene.isActive()) return;
      const to = { x: k.g.player.x, y: k.g.player.y };
      if (trail) this.windTrail(from, to, trail);
      if (shadow) this.addPath(from, to, shadow);
    });
  }

  onShadowStep(from: Pt, to: Pt): void {
    const shadow = this.rule('resShadowPath');
    if (shadow) this.addPath(from, to, shadow);
  }

  private windTrail(from: Pt, to: Pt, r: ActiveRule): void {
    const k = this.k;
    if (k.now < this.trailReadyAt) return;
    const d = { x: to.x - from.x, y: to.y - from.y };
    const len = Math.hypot(d.x, d.y);
    if (len < TILE) return;
    this.trailReadyAt = k.now + k.p(r, 'cooldownMs', 1000);
    const half = T(k.p(r, 'widthTiles', 1)) / 2;
    // art §27 칼바람 길 = 반복 타일 (`tile: true` 주기 64 도트, 피벗 = 길 시작) — 길을 따라 이어 깐다
    const tile = traitFxId(gameState.weapon.id, 'res_katana_breach');
    if (
      !k.rt.fx.tileLine(tile, from.x, from.y, d.x, d.y, len) &&
      !k.moves.fx('res_katana_breach', from, { angle: Math.atan2(d.y, d.x), fallbacks: ['katana_issen_line_t2_solo'] })
    )
      k.rt.fx.lineFx(from.x, from.y, d.x, d.y, len, half, BUILD_FX.COLOR.SPIN, 320);
    for (const m of k.rt.fx.inLine(from.x, from.y, d.x, d.y, len, half)) k.hit(m, k.p(r, 'damageMult', 0.4), d);
    this.proc('res_katana_breach', 'trail');
  }

  /** 끊이지 않는 칼: 개성 피해로 쓰러짐 → 칼바람 */
  onKill(mob: Mob): void {
    const k = this.k;
    const r = this.rule('resTraitKillBurst');
    this.tangled.delete(mob);
    if (!r) return;
    const at = k.traitHitAt.get(mob);
    if (at === undefined || k.now - at > k.p(r, 'windowMs', 300)) return;
    const c = { x: mob.x, y: mob.y - 6 };
    const rad = T(k.p(r, 'radiusTiles', 1.5));
    if (!k.moves.fx('res_katana_chain', c, { fallbacks: ['katana_spin'] }))
      k.rt.fx.ring(c.x, c.y, rad, BUILD_FX.COLOR.SPIN, 220);
    // 칼바람 피해는 개성 피해로 치지 않는다 (끝없이 잇지 않게)
    for (const m of k.rt.fx.inCircle(c.x, c.y, rad, new Set([mob])))
      k.rt.fx.damage(m, k.p(r, 'damageMult', 0.4), { dirX: m.x - c.x, dirY: m.y - c.y });
    this.proc('res_katana_chain', 'burst');
  }

  // --- 대검 ---

  /** 무너뜨림: 처박힌 자리 바닥이 갈라져 둘레가 튀어 오른다 */
  private onSlam(r: SlamResult): void {
    const k = this.k;
    const q = this.rule('resSlamQuake');
    if (!q || r.kind === 'none' || k.now < this.quakeReadyAt) return;
    this.quakeReadyAt = k.now + k.p(q, 'cooldownMs', 400);
    const rad = T(k.p(q, 'radiusTiles', 1.5));
    if (
      !k.moves.fx('res_greatsword_weight', r.at, {
        fallbacks: ['greatsword_quake_fork', 'crush'],
        depth: DEPTH.FX_GROUND,
      })
    )
      k.rt.fx.ring(r.at.x, r.at.y, rad, BUILD_FX.COLOR.CRACK, 260);
    const skip = new Set<Mob>([r.mob, ...(r.other ? [r.other] : [])]);
    for (const m of k.rt.fx.inCircle(r.at.x, r.at.y, rad, skip)) {
      k.rt.fx.damage(m, k.p(q, 'damageMult', 0.4), { dirX: m.x - r.at.x, dirY: m.y - r.at.y });
      k.moves.launch(m, 'res_greatsword_weight', {
        heightTiles: k.p(q, 'heightTiles', 0.9),
        airMs: k.p(q, 'airMs', 500),
      });
    }
    this.proc('res_greatsword_weight', 'quake');
  }

  /** 막고 되치는 대검: 둘레 날아오는 탄 전부 되침 */
  private deflectAll(gs: GreatswordRules): void {
    const k = this.k;
    const r = this.rule('resDeflectAll');
    if (!r) return;
    const pl = k.g.player;
    const n = gs.deflectIn(pl, pl.facingVec, T(k.p(r, 'radiusTiles', 3.5)), 360, k.p(r, 'returnMult', 1.5));
    if (n <= 0) return;
    if (!k.moves.fx('res_greatsword_insight', pl, { fallbacks: ['guard_perfect_fx', 'guard_wave'] }))
      k.rt.fx.ring(pl.x, pl.y, T(k.p(r, 'radiusTiles', 3.5)), BUILD_FX.COLOR.ECHO, 240);
    this.proc('res_greatsword_insight', 'deflect');
  }

  // --- 단검 ---

  private tangle(m: Mob): void {
    if (this.rule('resBindSpread')) this.tangled.set(m, this.k.now);
  }

  /** 얽힌 급소: 묶이거나 끌려온 적의 낙인이 터지면 옆 적까지 사슬로 묶는다 */
  private bindSpread(mob: Mob): void {
    const k = this.k;
    const r = this.rule('resBindSpread');
    const at = this.tangled.get(mob);
    if (!r || at === undefined || k.now - at > k.p(r, 'windowMs', 2000)) return;
    this.tangled.delete(mob);
    const next = k.rt.fx.nearest(mob.x, mob.y, T(k.p(r, 'rangeTiles', 3)), new Set([mob]));
    if (!next) return;
    k.moves.chainLine(mob, next);
    k.moves.fx('res_dagger_vital', { x: next.x, y: next.y - 8 }, { fallbacks: ['dagger_brand_hop'] });
    k.moves.bind(next, k.p(r, 'bindMs', 900), 'res_dagger_vital', { x: mob.x, y: mob.y });
    this.proc('res_dagger_vital', 'spread');
  }

  /** 그림자 길: 지나간 길을 ms 동안 남긴다 */
  private addPath(from: Pt, to: Pt, r: ActiveRule): void {
    const k = this.k;
    const d = { x: to.x - from.x, y: to.y - from.y };
    const len = Math.hypot(d.x, d.y);
    if (len < TILE * 0.5) return;
    const ms = k.p(r, 'ms', 2500);
    k.rt.fx.lineFx(from.x, from.y, d.x, d.y, len, T(k.p(r, 'widthTiles', 0.8)) / 2, BUILD_FX.COLOR.CLONE, ms);
    this.paths.push({ from, to, until: k.now + ms, marked: new Set() });
    this.proc('res_dagger_breach', 'path');
  }

  private tickPaths(now: number): void {
    const k = this.k;
    const r = this.rule('resShadowPath');
    this.paths = this.paths.filter((p) => now < p.until && r);
    if (!r) return;
    const half = T(k.p(r, 'widthTiles', 0.8)) / 2;
    for (const p of this.paths) {
      const d = { x: p.to.x - p.from.x, y: p.to.y - p.from.y };
      for (const m of k.rt.fx.inLine(p.from.x, p.from.y, d.x, d.y, Math.hypot(d.x, d.y), half, p.marked)) {
        p.marked.add(m);
        k.g.strikes.brands.onHit(m, d.x, d.y);
        k.moves.fx('res_dagger_breach', { x: m.x, y: m.y - 8 }, { part: 'mark', fallbacks: ['dagger_brand_mark'] });
      }
    }
  }

  // --- 활 ---

  /** 덫 비: 덫에 묶인 적 위로 하늘 화살 */
  private trapRain(mob: Mob): void {
    const k = this.k;
    const r = this.rule('resTrapRain');
    if (!r) return;
    const at = { x: mob.x, y: mob.y };
    k.g.time.delayedCall(k.p(r, 'delayMs', 300), () => {
      if (!k.g.scene.isActive()) return;
      this.bow.skyArrow(
        mob.active ? { x: mob.x, y: mob.y } : at,
        T(k.p(r, 'radiusTiles', 1)),
        k.p(r, 'damageMult', 0.5),
        'res_bow_breach',
      );
      this.proc('res_bow_breach', 'rain');
    });
  }

  update(now: number): void {
    this.syncOn();
    if (this.paths.length > 0) this.tickPaths(now);
    if (this.tangled.size > 40)
      for (const [m, t] of this.tangled) if (!m.active || now - t > 4000) this.tangled.delete(m);
  }

  debug(): Record<string, unknown> {
    return { on: [...this.on], counts: { ...this.counts }, paths: this.paths.length };
  }

  destroy(): void {
    this.tangled.clear();
    this.paths = [];
  }
}
