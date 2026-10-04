/**
 * 56라운드 2단계 활 화살비 (씬 쪽, Q43·Q52·Q55 · 계약 art §18.9): PLAYER_ARROW_RAIN 을 받아
 * - 예고 원 `bow_arrow_rain_mark` 행 m(32 월드 px) 을 좌클릭 순간 커서 원 중심에 (등장 → 대기 루프 → 낙하 → 식음 — `arrowRainMath.markColumn`)
 * - 발사 프레임마다 솟는 화살 `bow_arrow_rain_rise` (무기 JSON arrowSpawnAnchors[방향][발사 열] = 피벗)
 * - 원 안 무작위 낙하점마다 `bow_arrow_rain_fall`(12° 고정 + 좌우 뒤집기) — 그 시트 판정 프레임 시작에 낙하점 작은 판정
 * 시각은 씬 시계(히트스톱 동안 멈춤) · 예고 원 열은 플레이 시계. 시트가 없으면 작은 원·점 플레이스홀더.
 */
import { DEPTH, MOVE_FX, entityDepth } from '../../core/Constants';
import { EventBus, Events, type ArrowRainPayload, type PlayerSkillPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import type { Mob } from '../../objects/Mob';
import { markColumn, rainPoints, type Pt } from '../../systems/weapon/arrowRainMath';
import type { FxHandle } from '../../systems/fx/fxTypes';
import { circleHit } from '../../systems/weapon/hitShapes';
import { artScale, frameDurations, frameStarts, fxImpactFrame } from '../../systems/sprites/spriteDefs';
import { spriteLibrary } from '../../systems/sprites/sprites';
import type { Game } from '../Game';
import { HIT_ORIGIN_UP_PX } from './shared';
import { PLAYER_RENDER_SCALE } from '../../systems/weapon/playerScale';

interface RainRun {
  p: ArrowRainPayload;
  bornAt: number;
  mark: FxHandle | null;
  markDur: number[];
  rainTo: number;
}

export class ArrowRain {
  /** 디버그: 마지막 화살비 */
  debugLast: Record<string, unknown> | null = null;
  private runs: RainRun[] = [];

  constructor(private readonly g: Game) {}

  private get live(): boolean {
    return this.g.scene.isActive() && !this.g.frozen && !gameState.gameOver;
  }

  private at(ms: number, fn: () => void): void {
    if (ms <= 0) fn();
    else
      this.g.time.delayedCall(ms, () => {
        if (this.live) fn();
      });
  }

  private skill(phase: PlayerSkillPayload['phase']): void {
    EventBus.emit(Events.PLAYER_SKILL, {
      weapon: gameState.weapon.id,
      move: 'arrow_rain',
      phase,
    } satisfies PlayerSkillPayload);
  }

  start(p: ArrowRainPayload): void {
    const g = this.g;
    const fallDef = g.fx.sheet(p.fallFx);
    const fallImpact = fallDef ? (frameStarts(fallDef)[fxImpactFrame(fallDef)] ?? 0) : MOVE_FX.RAIN_FALL_IMPACT_MS;
    const lastImpact = p.firstDropAtMs + (p.drops - 1) * p.dropIntervalMs + fallImpact;
    // 예고 원 (좌클릭 순간 — Q55)
    const markDef = g.fx.sheet(p.markFx);
    let mark: FxHandle | null = null;
    if (markDef && g.fx.has(p.markFx)) {
      const size = (markDef as { sizeInfo?: Record<string, { radiusPx?: number }> }).sizeInfo?.[p.markRow];
      const drawn = typeof size?.radiusPx === 'number' ? size.radiusPx * artScale(markDef) : p.radiusPx;
      mark = g.fx.play(p.markFx, p.x, p.y, {
        dir: p.markRow,
        depth: DEPTH.FX_GROUND,
        staticFrame: 0,
        scaleMult: drawn > 0 ? p.radiusPx / drawn : 1,
        hooks: false,
      });
    } else this.placeholderRing(p.x, p.y, p.radiusPx, lastImpact);
    this.runs.push({
      p,
      bornAt: g.playNow(),
      mark,
      markDur: markDef ? frameDurations(markDef) : [],
      rainTo: lastImpact,
    });
    // 솟는 화살 (발사 프레임마다) · 발사 소리
    p.releasesAtMs.forEach((ms, i) => this.at(ms, () => this.rise(p, i)));
    this.at(p.releasesAtMs[0] ?? 0, () => this.skill('launch'));
    // 낙하점 (원 안 무작위 · 간격) · 낙하 소리 (첫 꽂힘 0.1s 앞)
    const pts = rainPoints(p.x, p.y, p.radiusPx, p.drops, () => g.rng.next());
    pts.forEach((pt, i) => this.at(p.firstDropAtMs + i * p.dropIntervalMs, () => this.drop(p, pt, fallImpact)));
    this.at(p.firstDropAtMs + fallImpact - MOVE_FX.RAIN_IMPACT_SFX_LEAD_MS, () => this.skill('impact'));
    this.debugLast = {
      time: g.time.now,
      x: Math.round(p.x),
      y: Math.round(p.y),
      mark: mark !== null,
      rises: 0,
      drops: 0,
      hits: 0,
    };
  }

  /** 솟는 화살: 무기 JSON arrowSpawnAnchors (무기 시트 좌표 — 피벗 기준 × 도트 배율), 없으면 몸 위 */
  private rise(p: ArrowRainPayload, i: number): void {
    const g = this.g;
    const pl = g.player;
    const def = gameState.weapon.def.moves?.arrowRain;
    const sheet = def ? spriteLibrary.sheet(gameState.weapon.id, def.art) : undefined;
    const anchors = (sheet as { arrowSpawnAnchors?: Record<string, ([number, number] | null)[]> } | undefined)
      ?.arrowSpawnAnchors;
    const col = p.releaseFrames[i];
    const pt = col !== undefined ? anchors?.[p.facing]?.[col] : null;
    const k = sheet ? artScale(sheet) * PLAYER_RENDER_SCALE : 0;
    const x = sheet && pt ? pl.x + (pt[0] - sheet.pivot.x) * k : pl.x;
    const y = sheet && pt ? pl.y + (pt[1] - sheet.pivot.y) * k : pl.y - HIT_ORIGIN_UP_PX * 2;
    if (g.fx.has(p.riseFx)) g.fx.play(p.riseFx, x, y, { dir: p.facing, depth: pl.depth + DEPTH.OVERLAY_STEP * 3 });
    if (this.debugLast) this.debugLast.rises = (this.debugLast.rises as number) + 1;
  }

  /** 낙하: 화살 fx (좌우 뒤집기 섞기) → 그 시트 판정 프레임 시작에 낙하점 작은 판정 */
  private drop(p: ArrowRainPayload, pt: Pt, impactMs: number): void {
    const g = this.g;
    if (g.fx.has(p.fallFx))
      g.fx.play(p.fallFx, pt.x, pt.y, {
        depth: entityDepth(pt.y) + DEPTH.OVERLAY_STEP * 2,
        flipX: g.rng.chance(0.5),
      });
    else this.placeholderDot(pt.x, pt.y);
    if (this.debugLast) this.debugLast.drops = (this.debugLast.drops as number) + 1;
    this.at(impactMs, () => this.hit(p, pt));
  }

  private hit(p: ArrowRainPayload, pt: Pt): void {
    const g = this.g;
    for (const child of [...g.mobs.getChildren()]) {
      const mob = child as Mob;
      if (!mob.active) continue;
      const b = mob.body;
      if (
        !circleHit(pt.x, pt.y, p.dropRadiusPx, { x: b.center.x, y: b.center.y, r: Math.min(b.halfWidth, b.halfHeight) })
      )
        continue;
      const { dmg, crit } = g.combat.rollDamage(p.damageMult, false, 'attack');
      if (this.debugLast) this.debugLast.hits = (this.debugLast.hits as number) + 1;
      if (g.combat.hitMob(mob, dmg, { crit, dirX: 0, dirY: 1, knock: false })) g.progress.onKill(mob, 'attack');
    }
  }

  private placeholderRing(x: number, y: number, r: number, ms: number): void {
    const gfx = this.g.add.graphics().setDepth(DEPTH.FX_GROUND);
    gfx.lineStyle(1, MOVE_FX.RAIN_PLACEHOLDER_COLOR, 0.8).strokeCircle(x, y, r);
    this.g.tweens.add({
      targets: gfx,
      alpha: 0,
      delay: ms,
      duration: MOVE_FX.RAIN_PLACEHOLDER_MS,
      onComplete: () => gfx.destroy(),
    });
  }

  private placeholderDot(x: number, y: number): void {
    const dot = this.g.add.circle(x, y, 2, MOVE_FX.RAIN_PLACEHOLDER_COLOR, 0.9).setDepth(entityDepth(y));
    this.g.tweens.add({
      targets: dot,
      alpha: 0,
      duration: MOVE_FX.RAIN_PLACEHOLDER_MS,
      onComplete: () => dot.destroy(),
    });
  }

  /** 매 프레임: 예고 원 열 */
  update(): void {
    if (this.runs.length === 0) return;
    const g = this.g;
    const now = g.playNow();
    this.runs = this.runs.filter((r) => {
      const col = markColumn(now - r.bornAt, r.p.firstDropAtMs, r.rainTo, r.markDur);
      if (col < 0 || !g.fx.isActive(r.mark)) {
        g.fx.stop(r.mark, 0, false);
        return false;
      }
      g.fx.setFrame(r.mark, r.p.markFx, col, r.p.markRow);
      return true;
    });
  }

  destroy(): void {
    this.runs = [];
  }
}
