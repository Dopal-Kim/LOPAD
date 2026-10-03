/**
 * 획 예시 패널 (30라운드): "이런 방식으로 그린다"만 보여준다. 어떤 획이 어떤 무기로 이어지는지는 표시하지 않는다.
 * 각 예시는 정규화 좌표(0~1)의 점 목록이며, durationMs 동안 천천히 그려지는 것을 반복한다.
 * 51라운드: 실제 획이 가늘어진 것에 맞춰 예시 선도 가늘게(1px). 시스템 파트 플레이스홀더 — UI 파트 산출물로 교체 대상.
 */
import Phaser from 'phaser';
import { COLORS, DEPTH, GAME, PLACEHOLDER_UI } from '../../core/Constants';

interface StrokeExample {
  caption: string;
  points: [number, number][];
  durationMs: number;
}

const STROKE_EXAMPLES: StrokeExample[] = [
  {
    caption: '길게, 곧게',
    points: [
      [0.05, 0.55],
      [0.95, 0.45],
    ],
    durationMs: 1400,
  },
  {
    caption: '짧게, 빠르게',
    points: [
      [0.3, 0.3],
      [0.45, 0.7],
      [0.55, 0.3],
      [0.7, 0.7],
    ],
    durationMs: 450,
  },
  {
    caption: '크게, 둥글게',
    points: Array.from({ length: 13 }, (_, i) => {
      const a = Math.PI * (1 + i / 12);
      return [0.5 + 0.42 * Math.cos(a), 0.55 + 0.4 * Math.sin(a) * -1] as [number, number];
    }),
    durationMs: 2000,
  },
  {
    caption: '한 번에 내려긋기',
    points: [
      [0.5, 0.1],
      [0.5, 0.9],
    ],
    durationMs: 700,
  },
];

/** 예시 선 굵기 · 펜 끝 반지름 · 선 알파 */
const LOOK = { LINE_PX: 1, TIP_R: 1.5, ALPHA: 0.6 };

export class StrokeExamples {
  private gfx?: Phaser.GameObjects.Graphics;
  private texts: Phaser.GameObjects.Text[] = [];

  constructor(private readonly scene: Phaser.Scene) {}

  /** 제목 + 예시별 캡션. 선은 draw() 에서 시간에 따라 다시 그린다 */
  show(): void {
    const P = PLACEHOLDER_UI.EXAMPLE_PANEL;
    this.gfx = this.scene.add.graphics().setDepth(DEPTH.ATTACK);
    const n = STROKE_EXAMPLES.length;
    const cellW = (GAME.WIDTH - P.gap * (n + 1)) / n;
    const style = { font: PLACEHOLDER_UI.FONT_CAPTION, color: '#8a8aa0', align: 'center' as const };
    this.texts.push(
      this.scene.add
        .text(GAME.WIDTH / 2, P.y - 12, '예시 — 이런 식으로 그어도 된다 (길게·짧게, 곧게·둥글게, 빠르게·느리게)', style)
        .setOrigin(0.5, 0)
        .setDepth(DEPTH.DEBUG),
    );
    STROKE_EXAMPLES.forEach((ex, i) => {
      const cx = P.gap + cellW * i + cellW / 2;
      this.texts.push(
        this.scene.add
          .text(cx, P.y + P.h + 2, ex.caption, style)
          .setOrigin(0.5, 0)
          .setDepth(DEPTH.DEBUG),
      );
    });
  }

  hide(): void {
    this.gfx?.destroy();
    this.gfx = undefined;
    this.texts.forEach((t) => t.destroy());
    this.texts = [];
  }

  /** 예시 획을 각자 duration 동안 진행률만큼 그린다 (끝나면 잠시 멈췄다가 반복) */
  draw(time: number): void {
    const g = this.gfx;
    if (!g) return;
    g.clear();
    const P = PLACEHOLDER_UI.EXAMPLE_PANEL;
    const n = STROKE_EXAMPLES.length;
    const cellW = (GAME.WIDTH - P.gap * (n + 1)) / n;
    STROKE_EXAMPLES.forEach((ex, i) => {
      const x0 = P.gap + cellW * i;
      g.lineStyle(1, 0x3a3a50, 1);
      g.strokeRect(x0, P.y, cellW, P.h);
      const cycle = ex.durationMs + P.pauseMs;
      const progress = Math.min(1, (time % cycle) / ex.durationMs);
      const pts = ex.points.map(([px, py]) => ({ x: x0 + px * cellW, y: P.y + py * P.h }));
      let total = 0;
      const seg: number[] = [];
      for (let k = 1; k < pts.length; k++) {
        const d = Phaser.Math.Distance.BetweenPoints(pts[k - 1], pts[k]);
        seg.push(d);
        total += d;
      }
      let remain = total * progress;
      g.lineStyle(LOOK.LINE_PX, COLORS.STROKE, LOOK.ALPHA);
      for (let k = 1; k < pts.length && remain > 0; k++) {
        const d = seg[k - 1];
        const t = Math.min(1, remain / d);
        const ex2 = pts[k - 1].x + (pts[k].x - pts[k - 1].x) * t;
        const ey2 = pts[k - 1].y + (pts[k].y - pts[k - 1].y) * t;
        g.lineBetween(pts[k - 1].x, pts[k - 1].y, ex2, ey2);
        if (t >= 1) remain -= d;
        else {
          g.fillStyle(COLORS.STROKE, 0.9);
          g.fillCircle(ex2, ey2, LOOK.TIP_R);
          remain = 0;
        }
      }
    });
  }
}
