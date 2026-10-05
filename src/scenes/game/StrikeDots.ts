/**
 * 남는 피해 (51라운드 정리 — PlayerStrikes 에서 분리): 잔월(남은 궤적 지속 피해) · 출혈(적별 지속 피해 + bleed 루프 이펙트).
 * 매 프레임 `update` 가 틱을 처리한다.
 */
import type Phaser from 'phaser';
import { COLORS, DEPTH } from '../../core/Constants';
import type { PlayerAttackPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import type { Mob } from '../../objects/Mob';
import type { FxHandle } from '../../systems/fx/fx';
import type { Game } from '../Game';

/** 잔월: 남아 있는 베기 궤적 (지속 피해 영역) */
interface DotZone {
  x: number;
  y: number;
  w: number;
  h: number;
  until: number;
  nextAt: number;
  tickMs: number;
  dmg: number;
}

/** 출혈: 적별 지속 피해 (+ 적에 붙은 bleed 루프 이펙트) */
interface Bleed {
  mob: Mob;
  dmg: number;
  ticksLeft: number;
  nextAt: number;
  tickMs: number;
  fx: FxHandle | null;
}

export class StrikeDots {
  private dotZones: DotZone[] = [];
  private bleeds: Bleed[] = [];

  constructor(private readonly g: Game) {}

  /** 잔월(옛 mods.trailDot): 판정 사각형 자리에 지속 피해 영역 + 남는 궤적 윤곽 */
  leaveTrailDot(p: PlayerAttackPayload, r: { cx: number; cy: number; w: number; h: number }): void {
    const g = this.g;
    const T = gameState.weapon.mods.trailDot!;
    const now = g.time.now;
    const { dmg } = g.combat.rollDamage(p.damageMult * T.damageMult);
    const dot: DotZone = {
      x: r.cx,
      y: r.cy,
      w: r.w,
      h: r.h,
      until: now + T.lingerMs,
      nextAt: now + T.tickMs,
      tickMs: T.tickMs,
      dmg,
    };
    this.dotZones.push(dot);
    // 60라운드 (57 Q42): 옛 잔월·거합 진화 그림은 끔 — 남는 궤적은 윤곽 사각형
    const rect = g.add.rectangle(r.cx, r.cy, r.w, r.h, COLORS.TRAIL_DOT, 0.35).setDepth(DEPTH.ATTACK);
    g.tweens.add({ targets: rect, alpha: 0, duration: T.lingerMs, onComplete: () => rect.destroy() });
  }

  /** 출혈(2차): 적중한 적에 지속 피해를 건다 (재적중이면 횟수를 채우고 루프를 다시 시작) */
  applyBleed(mob: Mob): void {
    const B = gameState.weapon.mods.bleed;
    if (!B) return;
    const g = this.g;
    const now = g.time.now;
    const tick = Math.max(1, Math.round(gameState.attack * gameState.weapon.damageMult * B.damageMult));
    const cur = this.bleeds.find((b) => b.mob === mob);
    if (cur) {
      cur.ticksLeft = B.ticks;
      cur.dmg = Math.max(cur.dmg, tick);
      // 재적중: 루프를 다시 시작해 0프레임(글린트) = 다음 틱에 맞춘다
      cur.nextAt = now + B.tickMs;
      if (g.fx.isActive(cur.fx)) g.fx.stop(cur.fx, 0, false);
      cur.fx = this.playBleedFx(mob);
    } else
      this.bleeds.push({
        mob,
        dmg: tick,
        ticksLeft: B.ticks,
        nextAt: now + B.tickMs,
        tickMs: B.tickMs,
        fx: this.playBleedFx(mob),
      });
  }

  /** 출혈(옛 mods.bleed): 60라운드 (57 Q42) 옛 진화 루프 그림은 끔 — 피격 번쩍임만 */
  private playBleedFx(_mob: Mob): FxHandle | null {
    return null;
  }

  update(time: number): void {
    this.tickDotZones(time);
    this.tickBleeds(time);
  }

  /** 잔월: 남은 궤적 영역이 주기마다 겹친 적에게 피해 */
  private tickDotZones(time: number): void {
    if (this.dotZones.length === 0) return;
    const g = this.g;
    for (const z of this.dotZones) {
      if (time < z.nextAt) continue;
      z.nextAt = time + z.tickMs;
      const bodies = g.physics.overlapRect(z.x - z.w / 2, z.y - z.h / 2, z.w, z.h, true, false);
      for (const b of bodies) {
        const go = (b as Phaser.Physics.Arcade.Body).gameObject as unknown;
        if (!g.mobs.contains(go as Phaser.GameObjects.GameObject)) continue;
        const mob = go as Mob;
        if (!mob.active) continue;
        if (g.combat.hitMob(mob, z.dmg, { crit: false, dirX: 0, dirY: 0, tick: true }))
          g.progress.onKill(mob, 'attack');
      }
    }
    this.dotZones = this.dotZones.filter((z) => time < z.until);
  }

  /** 출혈: 주기마다 피해, 횟수 소진·적 사망 시 제거 */
  private tickBleeds(time: number): void {
    if (this.bleeds.length === 0) return;
    const g = this.g;
    for (const b of this.bleeds) {
      if (!b.mob.active || time < b.nextAt) continue;
      b.nextAt = time + b.tickMs;
      b.ticksLeft -= 1;
      if (g.combat.hitMob(b.mob, b.dmg, { crit: false, dirX: 0, dirY: 0, tick: true }))
        g.progress.onKill(b.mob, 'attack');
      else b.mob.flashColor(COLORS.BLEED);
    }
    for (const b of this.bleeds) {
      if (b.mob.active && b.ticksLeft > 0) continue;
      if (g.fx.isActive(b.fx)) g.fx.stop(b.fx);
    }
    this.bleeds = this.bleeds.filter((b) => b.mob.active && b.ticksLeft > 0);
  }
}
