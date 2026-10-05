/**
 * 57라운드 빌드 축 — 완벽 성공 사건 (간파 태그, 계약 §14.11 PERFECT_SUCCESS): 패링 · 퍼펙트 가드 · 완벽 놓기 · **완벽 회피(57 Q28 신설)**.
 * 완벽 회피 = 대쉬·그림자 걸음을 시작한 뒤 windowMs(0.15초) 안에 그 자리를 노린 적 공격 판정 — 무적으로 흘린 피격, 무장한 자리
 * 반경 안 적 탄, 그 자리 가까이서 공격한 적(ENEMY_ATTACK·BOSS_ATTACK). 월드 문구 'PERFECT EVADE'(§13 방식).
 * 세트 간파 2(치명 확정)·4(반향)·6(정적) · 아슬아슬 · 이중 개성 물 위의 달 · 각성 만월 명경(패링 일섬) · 갈래 반향(BranchStrikes).
 */
import { BUILD_ART, BUILD_FX, TILE } from '../../../core/Constants';
import {
  EventBus,
  Events,
  type BossAttackPayload,
  type PerfectSuccessPayload,
  type SetEffectPayload,
} from '../../../core/EventBus';
import { facingOf } from '../../../systems/sprites/spriteDefs';
import { PLAYER_RENDER_SCALE } from '../../../systems/weapon/playerScale';
import { gameState } from '../../../core/GameState';
import { BUILD } from '../../../data/build';
import { UI_EVENTS, __system, type UiPerfectSuccess } from '../../../contract/ui';
import type { Mob } from '../../../objects/Mob';
import type { Projectile } from '../../../objects/Projectile';
import { param } from '../../../systems/build/buildMods';
import type { Game } from '../../Game';
import type { BuildRuntime } from './BuildRuntime';

export type PerfectKind = UiPerfectSuccess['kind'];

const T = (tiles: number) => tiles * TILE;

export class BuildPerfect {
  /** 간파 6: 완벽 성공 횟수 · 정적 끝 */
  private count = 0;
  private stillUntil = -Infinity;
  private stillOn = false;
  /** 간파 2: 다음 공격 치명 확정 창 */
  critUntil = -Infinity;
  /** 디버그 */
  private last: { kind: PerfectKind; t: number } | null = null;
  private evades = 0;

  constructor(
    private readonly g: Game,
    private readonly rt: BuildRuntime,
  ) {
    EventBus.on(Events.BOSS_ATTACK, this.onBossAttack, this);
  }

  private get now(): number {
    return this.g.time.now;
  }

  /** 완벽 성공 한 번 (attack = 막은 공격의 공격력, 없으면 0) */
  onPerfect(kind: PerfectKind, attack = 0, dirX?: number, dirY?: number): void {
    const now = this.now;
    this.last = { kind, t: Math.round(now) };
    __system.emit(UI_EVENTS.PERFECT_SUCCESS, { kind } satisfies UiPerfectSuccess);
    EventBus.emit(Events.PERFECT_SUCCESS, { kind } satisfies PerfectSuccessPayload);
    this.rt.record('perfect', kind);
    const pl = this.g.player;
    const fx = pl.facingVec;
    const dx = dirX ?? fx.x;
    const dy = dirY ?? fx.y;
    // 간파 2: 1초 안 다음 공격 치명 확정
    const c2 = this.rt.rule('perfectNextCrit');
    if (c2) this.critUntil = now + param(c2, 'windowMs');
    // 간파 4: 반향 — 앞 120°·2.5칸에 막은 피해 ×2 (최소 공격 ×1.0)
    const echo = this.rt.rule('perfectEcho');
    if (echo) {
      const r = T(param(echo, 'rangeTiles'));
      const arc = param(echo, 'arcDeg', 120);
      const counter = 1 + this.rt.stat('perfectCounterMult');
      const raw =
        Math.max(attack * param(echo, 'blockedMult'), gameState.attack * param(echo, 'minAttackMult')) * counter;
      this.rt.fx.coneFx(pl.x, pl.y, dx, dy, r, arc, BUILD_FX.COLOR.ECHO);
      for (const m of this.rt.fx.inCone(pl.x, pl.y, dx, dy, r, arc))
        this.rt.fx.raw(m, raw, { dirX: dx, dirY: dy, killKind: 'parry' });
    }
    // 간파 6: 3회마다 정적 1초 (적·탄 40% 감속)
    const still = this.rt.rule('perfectStillness');
    if (still) {
      this.count += 1;
      if (this.count >= param(still, 'every', 3)) {
        this.count = 0;
        this.startStill(param(still, 'ms'), param(still, 'slow'), T(param(still, 'radiusTiles', 0)));
      }
    }
    if (kind === 'parry') this.onParry(dx, dy);
    if (kind === 'perfectEvade') {
      const emp = this.rt.rule('evadeEmpower');
      if (emp) this.rt.combat.empowerNext(param(emp, 'mult'), param(emp, 'windowMs', 2000));
    }
    this.rt.branch.onPerfect(kind, attack, dx, dy);
  }

  /** 패링: 물 위의 달(분신 일섬) · 각성 명경(자동 일섬 반격) */
  private onParry(dx: number, dy: number): void {
    const pl = this.g.player;
    const at = { x: pl.x, y: pl.y };
    for (const r of [this.rt.rule('parryClone'), this.rt.rule('parryIssen')]) {
      if (!r) continue;
      const delay = param(r, 'delayMs', 0);
      const range = T(param(r, 'rangeTiles', 4));
      const mult = param(r, 'damageMult', 1.6);
      const fire = () => {
        if (!this.g.scene.isActive()) return;
        const target = this.rt.fx.nearest(at.x, at.y, range);
        const vx = target ? target.x - at.x : dx;
        const vy = target ? target.y - at.y : dy;
        const len = Math.hypot(vx, vy) || 1;
        this.rt.fx.clone(at.x, at.y);
        this.rt.fx.lineFx(at.x, at.y, vx / len, vy / len, range, TILE / 2, BUILD_FX.COLOR.MOON);
        for (const m of this.rt.fx.inLine(at.x, at.y, vx / len, vy / len, range, TILE / 2))
          this.rt.fx.damage(m, mult, { dirX: vx / len, dirY: vy / len, heavy: true, killKind: 'parry' });
      };
      if (delay > 0) this.g.time.delayedCall(delay, fire);
      else fire();
    }
  }

  /** 간파 2: 다음 공격 치명 확정을 쓴다 */
  takeCrit(): boolean {
    if (this.now >= this.critUntil) return false;
    this.critUntil = -Infinity;
    return true;
  }

  /** 완벽 회피 확정 → 문구·완벽 성공 · perfect_dodge (회피가 시작된 발 자리 고정, 행 = 이동 방향) */
  onEvade(): void {
    this.evades += 1;
    this.rt.fx.callout(BUILD_FX.TEXT.PERFECT_EVADE);
    const o = this.rt.evade.origin;
    const pl = this.g.player;
    const dir = facingOf(pl.x - o.x, pl.y - o.y, pl.facingDir);
    this.rt.art.once(BUILD_ART.PERFECT_DODGE, o.x, o.y, { dir, scaleMult: PLAYER_RENDER_SCALE });
    this.onPerfect('perfectEvade');
  }

  private get window(): number {
    return BUILD.events.perfectEvadeWindowMs + this.rt.stat('perfectWindowAddMs');
  }

  private get threatR(): number {
    return T(BUILD.events.perfectEvadeThreatRadiusTiles);
  }

  /** 적 공격 판정 (접촉·돌진·탄 발사): 무장한 자리 가까이서면 완벽 회피 */
  onEnemyAttack(id: string): void {
    if (!this.rt.evade.armed(this.now, this.window)) return;
    const o = this.rt.evade.origin;
    const mob = this.findMob(id, o.x, o.y);
    if (!mob) return;
    const r = this.threatR + Math.max(mob.body.halfWidth, mob.body.halfHeight);
    if (this.rt.evade.check(this.now, this.window, mob.body.center.x, mob.body.center.y, r)) this.onEvade();
  }

  private onBossAttack(p: BossAttackPayload): void {
    this.onEnemyAttack(p.id);
  }

  private findMob(id: string, x: number, y: number): Mob | null {
    let best: Mob | null = null;
    let bd = Infinity;
    for (const m of this.rt.fx.mobs()) {
      if (m.spriteId !== id) continue;
      const d = Math.hypot(m.x - x, m.y - y);
      if (d < bd) {
        bd = d;
        best = m;
      }
    }
    return best;
  }

  /**
   * 정적 (간파 6): radiusPx > 0 이면 (60 Q3 아트 제안 채택 — 정적 파동 반경 약 5.6칸, 데이터 radiusTiles) 반경 안 적·적 탄만
   * slow 만큼 감속 (`status_slowed` 표시, 파동 `set_stasis_wave` — 주인공 발, 바닥). 반경이 없으면 예전처럼 물리 배속 전체
   * (활 숨 집중과 같은 방식 — 집중 중이면 건너뜀). 주인공은 제 속도
   */
  private startStill(ms: number, slow: number, radiusPx = 0): void {
    const g = this.g;
    const pl = g.player;
    EventBus.emit(Events.SET_EFFECT, { tag: 'insight', effect: 'stillness' } satisfies SetEffectPayload);
    this.stillUntil = this.now + ms;
    if (radiusPx > 0) {
      if (
        !this.rt.art.once(BUILD_ART.STASIS_WAVE, pl.x, pl.y, { depth: pl.depth - 1e-6, scaleMult: PLAYER_RENDER_SCALE })
      )
        this.rt.fx.ring(pl.x, pl.y, radiusPx, BUILD_FX.STILL_FLASH.COLOR);
      const k = Math.max(0, 1 - slow);
      for (const m of this.rt.fx.inCircle(pl.x, pl.y, radiusPx)) {
        m.statusSlowUntil = this.now + ms;
        m.statusSlowMult = k;
      }
      for (const child of g.projectiles.getChildren()) {
        const pr = child as Projectile;
        if (!pr.active || pr.reflected || pr.owner !== 'enemy') continue;
        if (Math.hypot(pr.x - pl.x, pr.y - pl.y) > radiusPx) continue;
        pr.body.velocity.scale(k);
        this.slowedShots.push({ shot: pr, k });
      }
      g.screenFx.flash(BUILD_FX.STILL_FLASH.COLOR, BUILD_FX.STILL_FLASH.MS, BUILD_FX.STILL_FLASH.ALPHA);
      this.stillOn = true;
      this.stillLocal = true;
      this.rt.record('stillness');
      return;
    }
    if (g.feedback.focusScale !== 1) return;
    const world = g.physics.world;
    const ts = 1 / Math.max(0.1, 1 - slow);
    if (world) world.timeScale = ts;
    pl.timeComp = ts;
    this.stillOn = true;
    this.stillLocal = false;
    g.screenFx.flash(BUILD_FX.STILL_FLASH.COLOR, BUILD_FX.STILL_FLASH.MS, BUILD_FX.STILL_FLASH.ALPHA);
    this.rt.record('stillness');
  }

  /** 반경 정적으로 늦춘 적 탄 (끝날 때 속도 되돌림) · 반경 정적인가 */
  private slowedShots: { shot: Projectile; k: number }[] = [];
  private stillLocal = false;

  private endStill(): void {
    if (!this.stillOn) return;
    this.stillOn = false;
    for (const { shot, k } of this.slowedShots) if (shot.active && k > 0) shot.body.velocity.scale(1 / k);
    this.slowedShots = [];
    if (this.stillLocal) return;
    const g = this.g;
    if (g.feedback.focusScale !== 1) return;
    if (g.physics.world) g.physics.world.timeScale = 1;
    if (g.player) g.player.timeComp = 1;
  }

  update(now: number): void {
    if (this.stillOn && now >= this.stillUntil) this.endStill();
    // 무장한 자리 반경 안으로 들어온 적 탄 = 완벽 회피
    if (!this.rt.evade.armed(now, this.window)) return;
    for (const child of this.g.projectiles.getChildren()) {
      const pr = child as Projectile;
      if (!pr.active || pr.reflected || pr.owner !== 'enemy') continue;
      if (this.rt.evade.check(now, this.window, pr.x, pr.y, this.threatR)) {
        this.onEvade();
        return;
      }
    }
  }

  debug(): Record<string, unknown> {
    return {
      last: this.last,
      count: this.count,
      evades: this.evades,
      still: this.stillOn,
      critReady: this.now < this.critUntil,
    };
  }

  destroy(): void {
    EventBus.off(Events.BOSS_ATTACK, this.onBossAttack, this);
    this.endStill();
  }
}
