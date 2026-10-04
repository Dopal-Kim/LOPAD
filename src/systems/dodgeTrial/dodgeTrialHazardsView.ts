/**
 * 회피 시험 위협 그림 (51라운드 정리: dodgeTrialHazards.ts 에서 분리) — 고리 예고·구슬, 탄막 벽 예고·등뼈.
 * 상태(Ring·Wall)는 TrialHazards 가 들고, 여기서는 매 프레임 그리기만 한다.
 */
import Phaser from 'phaser';
import { DODGE_TRIAL } from './dodgeTrial';
import { ringRadius } from './dodgeTrialTasks';

export interface Ring {
  cx: number;
  cy: number;
  R0: number;
  gapAngle: number;
  gapDeg: number;
  closeMs: number;
  /** 예고 시작 시각 */
  start: number;
  beads: number[];
}

export interface Wall {
  angle: number;
  from: number;
  to: number;
  half: number;
  start: number;
  speed: number;
}

/** 예고 깜빡임 주기(ms) · 마감 직전 가속 구간(ms) */
const BLINK = { SLOW_MS: 120, FAST_MS: 55, FINAL_MS: 200 };

function blinkAlpha(t: number, total: number, lo: number, hi: number): number {
  const period = total - t < BLINK.FINAL_MS ? BLINK.FAST_MS : BLINK.SLOW_MS;
  return Math.floor(t / period) % 2 === 0 ? hi : lo;
}

/** 그리기 입력: 색 · 경기장 중심 · 벽이 주인공보다 얼마나 뒤에 있나(양수 = 다가오는 중) */
export interface HazardDrawOpts {
  hot: number;
  bright: number;
  x0: number;
  cx: number;
  cy: number;
  wallRel: (w: Wall) => number;
}

/** 고리(예고 윤곽·틈·구슬)와 벽(예고 선·화살, 등뼈)을 그린다. g = 바닥 위 선, bg = 구슬 */
export function drawHazards(
  g: Phaser.GameObjects.Graphics,
  bg: Phaser.GameObjects.Graphics,
  rings: Ring[],
  walls: Wall[],
  time: number,
  o: HazardDrawOpts,
): void {
  const R = DODGE_TRIAL.RING;
  const { hot, bright } = o;
  for (const r of rings) {
    const t = time - r.start;
    const half = Phaser.Math.DegToRad(r.gapDeg / 2);
    const a0 = r.gapAngle + half;
    const a1 = r.gapAngle - half + Math.PI * 2;
    if (t < R.WARN_MS) {
      // 예고: 고리 윤곽(깜빡임) + 밝은 틈 + 틈 쪽 화살
      g.lineStyle(1, hot, blinkAlpha(t, R.WARN_MS, 0.5, 0.95));
      g.beginPath();
      g.arc(r.cx, r.cy, r.R0, a0, a1, false);
      g.strokePath();
      g.lineStyle(3, o.x0, 0.9);
      g.beginPath();
      g.arc(r.cx, r.cy, r.R0, r.gapAngle - half, r.gapAngle + half, false);
      g.strokePath();
      const ax = r.cx + Math.cos(r.gapAngle) * r.R0 * 0.55;
      const ay = r.cy + Math.sin(r.gapAngle) * r.R0 * 0.55;
      arrow(g, ax, ay, r.gapAngle, 7, bright, 0.85);
      continue;
    }
    const rad = ringRadius(t, r.closeMs, r.R0);
    // 틈 표시 (조여 드는 동안에도 밝게)
    g.lineStyle(2, o.x0, 0.55);
    g.beginPath();
    g.arc(r.cx, r.cy, rad, r.gapAngle - half, r.gapAngle + half, false);
    g.strokePath();
    for (const a of r.beads) {
      const x = r.cx + Math.cos(a) * rad;
      const y = r.cy + Math.sin(a) * rad;
      bg.fillStyle(hot, 1);
      bg.fillCircle(x, y, R.BEAD_R_PX);
      bg.fillStyle(o.x0, 1);
      bg.fillCircle(x, y, R.BEAD_R_PX * 0.45);
    }
  }
  const Wc = DODGE_TRIAL.WALL;
  for (const w of walls) {
    const t = time - w.start;
    const ux = Math.cos(w.angle);
    const uy = Math.sin(w.angle);
    const along = wallAlong(w, time);
    const px = o.cx + ux * along;
    const py = o.cy + uy * along;
    const ex = -uy * w.half;
    const ey = ux * w.half;
    if (t < Wc.WARN_MS) {
      // 예고: 벽 자리 선(깜빡임) + 진행 방향 화살 줄
      g.lineStyle(2, hot, blinkAlpha(t, Wc.WARN_MS, 0.3, 0.85));
      g.lineBetween(px - ex, py - ey, px + ex, py + ey);
      const step = 36;
      for (let o = -w.half + step / 2; o <= w.half; o += step)
        arrow(g, px - uy * o + ux * 10, py + ux * o + uy * 10, w.angle, 6, bright, 0.75);
      continue;
    }
    // 벽 등뼈: 주인공에게 다가오는 중이고 DASH_HINT_PX 안이면 밝게 (대쉬 박자)
    const rel = o.wallRel(w);
    const near = rel > 0 && rel < Wc.DASH_HINT_PX;
    g.lineStyle(near ? 2 : 1, near ? o.x0 : hot, near ? 0.9 : 0.3);
    g.lineBetween(px - ex, py - ey, px + ex, py + ey);
  }
}

function arrow(
  g: Phaser.GameObjects.Graphics,
  x: number,
  y: number,
  a: number,
  size: number,
  color: number,
  alpha: number,
): void {
  const c = Math.cos(a);
  const s = Math.sin(a);
  g.fillStyle(color, alpha);
  g.fillTriangle(
    x + c * size,
    y + s * size,
    x - c * size * 0.4 - s * size * 0.6,
    y - s * size * 0.4 + c * size * 0.6,
    x - c * size * 0.4 + s * size * 0.6,
    y - s * size * 0.4 - c * size * 0.6,
  );
}

/** 벽 등뼈 위치 (중심 기준 진행 방향 거리) */
export function wallAlong(w: Wall, time: number): number {
  return w.from + (w.speed * Math.max(0, time - w.start - DODGE_TRIAL.WALL.WARN_MS)) / 1000;
}
