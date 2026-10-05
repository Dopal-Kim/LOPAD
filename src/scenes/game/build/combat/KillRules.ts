/**
 * 57라운드 빌드 축 — 처치 규칙 (BuildCombat 에서 분리, 60라운드 6-1 정리 — 동작 그대로, Progression.onKill):
 * 연쇄 2(공속)·4(자원)·6(살기) · 표식 4 옮겨감 · 사냥 표지 · 지속 피해 옮겨붙음(상흔 6·피 냄새) · 도미노 ·
 * 웅덩이 위 처치(취기 2)·엎지른 술·술바다 · 무기 자원 회복(restoreResource — 갈래도 쓴다).
 */
import { BUILD_ART } from '../../../../core/Constants';
import type { Mob } from '../../../../objects/Mob';
import { param } from '../../../../systems/build/buildMods';
import type { Game } from '../../../Game';
import { T } from '../../shared';
import type { BuildRuntime } from '../BuildRuntime';
import { buildAttack, emitProc } from './common';

export class KillRules {
  /** 연쇄 2: 공속 +15% 끝 · 연쇄 6 살기 끝 · 최근 처치 시각들 */
  private hasteUntil = -Infinity;
  private bloodlustUntil = -Infinity;
  private killTimes: number[] = [];

  constructor(
    private readonly g: Game,
    private readonly rt: BuildRuntime,
    /** 처치된 적의 치명 금(급소 6) 지우기 */
    private readonly forget: (mob: Mob) => void,
  ) {}

  hasteActive(now: number): boolean {
    return now < this.hasteUntil;
  }

  bloodlustActive(now: number): boolean {
    return now < this.bloodlustUntil;
  }

  onKill(mob: Mob, kind: string): void {
    const now = this.g.time.now;
    const at = { x: mob.x, y: mob.y };
    const marks = this.rt.marks.take(mob);
    const brands = this.g.strikes.brands.marksOf(mob);
    const dot = this.rt.dots.snapshot(mob, now);
    const hadDot = dot.length > 0;
    this.rt.dots.forget(mob);
    this.forget(mob);
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
        // chain_bloodlust 루프 + set_flash(6행) 시작
        this.rt.art.bloodlustUntil = this.bloodlustUntil;
        this.rt.art.onPlayer(BUILD_ART.SET_FLASH, { dir: '6' });
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
    this.spreadDots(mob, at, kind, dot);
    // 도미노: 가장 가까운 적에게 재 파편
    const dom = this.rt.rule('killShard');
    if (dom) {
      const m = this.rt.fx.nearest(at.x, at.y, T(param(dom, 'rangeTiles', 8)), new Set([mob]));
      if (m) emitProc(dom);
      if (m)
        this.rt.fx.shot(at.x, at.y, m.x - at.x, m.y - at.y, buildAttack() * param(dom, 'damageMult'), {
          tag: 'shard',
          speedTiles: 12,
          lifeMs: 900,
        });
    }
    this.liquorOnKill(at);
    this.rt.branch.onKill(mob, kind, { marks, brands, hadDot });
  }

  /** 지속 피해로 죽은 적 → 옮겨붙음 (상흔 6 · 피 냄새) */
  private spreadDots(
    mob: Mob,
    at: { x: number; y: number },
    kind: string,
    dot: ReturnType<BuildRuntime['dots']['snapshot']>,
  ): void {
    const now = this.g.time.now;
    const hadDot = dot.length > 0;
    const spreadN =
      (hadDot && kind === 'environment' && this.rt.rule('dotSpread')
        ? param(this.rt.rule('dotSpread')!, 'count', 2)
        : 0) + (hadDot && this.rt.rule('dotKillSpread') ? param(this.rt.rule('dotKillSpread')!, 'count', 1) : 0);
    const scent = hadDot ? this.rt.rule('dotKillSpread') : null;
    if (scent) emitProc(scent);
    if (spreadN <= 0) return;
    const used = new Set([mob]);
    for (let i = 0; i < spreadN; i++) {
      const m = this.rt.fx.nearest(at.x, at.y, T(3), used);
      if (!m) break;
      used.add(m);
      for (const d of dot) this.rt.dots.apply(m, d.kind, now, d.ms, d.tickMs, d.dmg);
    }
  }

  /** 웅덩이 위 처치 = 마시기 (취기 2) · 엎지른 술 · 술바다 */
  private liquorOnKill(at: { x: number; y: number }): void {
    const onPool = this.rt.fx.onPool(at.x, at.y);
    if (onPool && this.rt.stage('drunk') >= 2) this.rt.drink('poolKill');
    const spill = this.rt.rule('spillPool');
    if (spill && this.g.rng.chance(param(spill, 'chance'))) {
      this.rt.fx.liquorPool(at.x, at.y, T(param(spill, 'radiusTiles', 1)), param(spill, 'ms'));
      emitProc(spill);
    }
    const sea = this.rt.rule('drunkSea');
    if (sea && this.rt.drunkActive)
      this.rt.fx.liquorPool(at.x, at.y, T(param(sea, 'poolRadiusTiles')), param(sea, 'poolMs'));
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

  /** 개성 배율 (살기 ×2) */
  personalityMult(): number {
    const bl = this.rt.rule('bloodlust');
    return bl && this.g.time.now < this.bloodlustUntil ? param(bl, 'personalityMult', 1) : 1;
  }
}
