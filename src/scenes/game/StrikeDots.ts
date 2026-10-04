/**
 * 남는 피해 (51라운드 정리 — PlayerStrikes 에서 분리): 잔월(남은 궤적 지속 피해) · 출혈(적별 지속 피해 + bleed 루프 이펙트).
 * 매 프레임 `update` 가 틱을 처리한다.
 */
import type Phaser from 'phaser';
import { COLORS, DEPTH, entityDepth } from '../../core/Constants';
import type { PlayerAttackPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import type { Mob } from '../../objects/Mob';
import type { FxHandle } from '../../systems/fx/fx';
import { facingOf } from '../../systems/sprites/spriteDefs';
import type { Game } from '../Game';
import { pathFx } from './shared';

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

  /** 잔월: 판정 사각형 자리에 지속 피해 영역 + 남는 궤적 그림 (2차 시트 → 거합 꼬리 → 사각형) */
  leaveTrailDot(
    p: PlayerAttackPayload,
    r: { cx: number; cy: number; w: number; h: number },
    swingFx: string | null,
  ): void {
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
    const zangetsu = pathFx(g.fx, 'zangetsu');
    const dir = facingOf(p.dirX, p.dirY, g.player.facingDir);
    if (zangetsu && swingFx) {
      // 잔월(2차 전용 시트): 거합이 끝난 자리(고정)에 루프, 한 바퀴 = 틱 간격이 되도록 틱을 루프 시작에 맞춘다. 바닥 깊이
      const start = p.swingDelayMs + g.fx.durationOf(swingFx);
      const linger = T.lingerMs - start;
      if (linger > 0) {
        const at = { x: p.x, y: p.y };
        g.time.delayedCall(start, () => {
          if (!g.scene.isActive()) return;
          g.fx.play(zangetsu, at.x, at.y, { dir, depth: DEPTH.FX_GROUND, durationMs: linger });
          dot.nextAt = g.time.now + dot.tickMs;
        });
      }
    } else if (swingFx === 'iai') {
      // 잔월(시트 없음): 거합 이펙트의 꼬리(마지막 3프레임)를 본 재생이 끝난 뒤 남은 시간 동안 반복
      const start = p.swingDelayMs + g.fx.durationOf('iai');
      const linger = T.lingerMs - start;
      if (linger > 0) {
        const at = { x: p.x, y: p.y, depth: entityDepth(p.y) + DEPTH.OVERLAY_STEP * 2 };
        g.time.delayedCall(start, () => {
          if (g.scene.isActive())
            g.fx.play('iai', at.x, at.y, { dir, depth: at.depth, durationMs: linger, tailFrames: 3 });
        });
      }
    } else {
      const rect = g.add.rectangle(r.cx, r.cy, r.w, r.h, COLORS.TRAIL_DOT, 0.35).setDepth(DEPTH.ATTACK);
      g.tweens.add({ targets: rect, alpha: 0, duration: T.lingerMs, onComplete: () => rect.destroy() });
    }
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

  /** 출혈(2차): 적 히트박스 중심에 붙어 루프 (한 바퀴 = 틱 간격, 아트 JSON). 시트가 없으면 null */
  private playBleedFx(mob: Mob): FxHandle | null {
    const id = pathFx(this.g.fx, 'bleed');
    if (!id) return null;
    const c = mob.body.center;
    return this.g.fx.play(id, c.x, c.y, {
      follow: mob,
      followOffset: { x: c.x - mob.x, y: c.y - mob.y },
      depthOffset: DEPTH.OVERLAY_STEP * 3,
    });
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
