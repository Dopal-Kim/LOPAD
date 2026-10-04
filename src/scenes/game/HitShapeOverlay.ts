/**
 * 55라운드 §17 판정 모양 디버그 오버레이 (`?debug`, `&hitshapes=0` 이면 끔 · `__lopad.hitShapes(on)`) + 시트가 없을 때의 윤곽 플레이스홀더
 * (PlayerStrikes.drawShapeOutline 을 옮김). 판정이 살아 있는 동안 윤곽을 유지하고, 그 뒤 FADE_MS 동안 흐려진다.
 * 색 = 모양별 (호·쐐기·찌르기·고리), 후속 판정(잔상 베기·충격파 링)은 FOLLOW.
 */
import Phaser from 'phaser';
import { COLORS, DEBUG, DEPTH, PROTOTYPE } from '../../core/Constants';
import { shapeOutline, type HitShape, type ShapeFacing } from '../../systems/weapon/hitShapes';
import type { Game } from '../Game';
import { urlParams } from './shared';

export class HitShapeOverlay {
  /** 디버그 오버레이 켜짐 */
  enabled: boolean;
  /** 디버그: 그린 횟수 */
  drawn = 0;

  constructor(private readonly g: Game) {
    const q = urlParams();
    this.enabled = q.has('debug') && q.get(DEBUG.HIT_SHAPES.PARAM_OFF) !== '0';
  }

  /** 디버그 윤곽 (켜져 있을 때만). activeMs 동안 유지 후 흐려짐 */
  debug(
    ox: number,
    oy: number,
    dirX: number,
    dirY: number,
    shape: HitShape,
    facing: ShapeFacing,
    activeMs: number,
    follow: boolean,
  ): void {
    if (!this.enabled) return;
    const H = DEBUG.HIT_SHAPES;
    const color = follow ? H.COLORS.follow : (H.COLORS[shape.kind] ?? COLORS.ATTACK);
    this.draw(ox, oy, dirX, dirY, shape, facing, color, H.FILL_ALPHA, H.LINE_ALPHA, activeMs, H.FADE_MS, DEPTH.DEBUG);
    this.drawn += 1;
  }

  /** 시트가 없을 때의 윤곽 플레이스홀더 (48라운드 규칙 — 곧바로 흐려짐) */
  placeholder(ox: number, oy: number, dirX: number, dirY: number, shape: HitShape, facing: ShapeFacing): void {
    this.draw(ox, oy, dirX, dirY, shape, facing, COLORS.ATTACK, 0.25, 0.8, 0, PROTOTYPE.SLASH_TRAIL_MS, DEPTH.ATTACK);
  }

  private draw(
    ox: number,
    oy: number,
    dirX: number,
    dirY: number,
    shape: HitShape,
    facing: ShapeFacing,
    color: number,
    fillAlpha: number,
    lineAlpha: number,
    holdMs: number,
    fadeMs: number,
    depth: number,
  ): void {
    const gr = this.g.add.graphics().setDepth(depth);
    gr.lineStyle(DEBUG.HIT_SHAPES.LINE_PX, color, lineAlpha);
    const polys = shapeOutline(ox, oy, dirX, dirY, shape, facing);
    polys.forEach((poly, i) => {
      const pts = poly.map((p) => new Phaser.Math.Vector2(p.x, p.y));
      // 고리·초승달의 안쪽 원은 선만 (채우면 빈 곳이 칠해진다)
      if (!(shape.kind === 'ring' && i > 0)) {
        gr.fillStyle(color, fillAlpha);
        gr.fillPoints(pts, true);
      }
      gr.strokePoints(pts, true);
    });
    this.g.tweens.add({
      targets: gr,
      alpha: 0,
      delay: holdMs,
      duration: fadeMs,
      onComplete: () => gr.destroy(),
    });
  }
}
