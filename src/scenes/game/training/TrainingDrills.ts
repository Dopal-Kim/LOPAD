/**
 * 61 단계 6 (P14 §1 '막고 받아치기') 훈련 예고: 원·선·부채를 주인공 자리에 차례로 그리고, 끝나는 순간 안에 있으면 맞는다.
 * 그릴 때 TRAINING_DRILL{shape} — 과제 '예고 피하기'는 그 뒤 맞지 않으면 완료(systems/training/tasks dodge 창).
 * 기하는 systems/training/drills (순수), 그림은 기존 적 예고(TelegraphFx).
 */
import Phaser from 'phaser';
import { TILE } from '../../../core/Constants';
import { EventBus, Events, type TrainingDrillPayload } from '../../../core/EventBus';
import type { TrainingTuning } from '../../../data/training';
import {
  aimDrill,
  insideDrill,
  nextDrillShape,
  type DrillGeom,
  type DrillShape,
} from '../../../systems/training/drills';
import type { Game } from '../../Game';

export class TrainingDrills {
  private active: { geom: DrillGeom; endAt: number } | null = null;
  private nextAt: number;
  private last = -1;

  constructor(
    private readonly g: Game,
    private readonly order: readonly DrillShape[],
    private readonly tuning: TrainingTuning,
    /** 이 모양은 이미 피했다 */
    private readonly cleared: (shape: DrillShape) => boolean,
    /** 아직 이 방 과제가 남았나 */
    private readonly wanted: () => boolean,
  ) {
    this.nextAt = g.time.now + tuning.drillEveryMs;
  }

  update(now: number): void {
    const g = this.g;
    if (this.active) {
      if (now < this.active.endAt) return;
      const d = this.active.geom;
      this.active = null;
      this.nextAt = now + this.tuning.drillEveryMs;
      if (insideDrill(d, g.player.x, g.player.y)) {
        const dx = g.player.x - d.x;
        const dy = g.player.y - d.y;
        const len = Math.hypot(dx, dy) || 1;
        g.player.takeHit(this.tuning.drillHit, now, { dirX: dx / len, dirY: dy / len });
      }
      return;
    }
    if (now < this.nextAt || !this.wanted() || g.frozen || g.menu.isOpen) return;
    const done = new Set(this.order.filter((s) => this.cleared(s)));
    const i = nextDrillShape(this.order, done, this.last);
    if (i < 0) return;
    this.last = i;
    this.fire(this.order[i], now);
  }

  private fire(shape: DrillShape, now: number): void {
    const g = this.g;
    const T = this.tuning;
    const geom = aimDrill(shape, g.player.x, g.player.y, g.rng.next(), {
      radiusPx: T.drillRadiusTiles * TILE,
      lineLengthPx: T.drillLineTiles * TILE,
      lineHalfPx: T.drillLineHalfTiles * TILE,
      coneRadiusPx: T.drillConeTiles * TILE,
      coneHalfAngle: Phaser.Math.DegToRad(T.drillConeDeg / 2),
    });
    if (shape === 'circle') g.telegraph.circle(geom.x, geom.y, geom.reachPx, T.drillMs, { aura: true });
    else if (shape === 'line') g.telegraph.line(geom.x, geom.y, geom.angle, geom.reachPx, T.drillMs, { aura: true });
    else g.telegraph.cone(geom.x, geom.y, geom.angle, geom.halfAngle, geom.reachPx, T.drillMs, { aura: true });
    this.active = { geom, endAt: now + T.drillMs };
    EventBus.emit(Events.TRAINING_DRILL, { shape } satisfies TrainingDrillPayload);
  }

  debug(): Record<string, unknown> {
    return {
      active: this.active ? { shape: this.active.geom.shape, endAt: this.active.endAt } : null,
      nextAt: this.nextAt,
    };
  }
}
