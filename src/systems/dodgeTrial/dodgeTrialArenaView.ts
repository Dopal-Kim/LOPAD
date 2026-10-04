/**
 * 회피 시험 경기장 그림: 4px 칸 바닥(행 단위로 이어 칠함) · 아래가 빈 칸 밑 절벽 면 · 빈 쪽 가장자리 층 램프 테두리 ·
 * 무너지기 직전(WARN_MS) 칸의 균열(어두워짐·검은 금·잔불·떨림) · 무너질 때 부스러기 · 기둥(③) · 과제 진행 호.
 * 과제마다 `setMask` 로 새 경기장으로 바꾼다(짧게 나타남). 좌표는 월드 px, 경기장 중심 (cx, cy).
 */
import Phaser from 'phaser';
import { DEPTH, entityDepth } from '../core/Constants';
import { DODGE_TRIAL } from './dodgeTrial';
import type { ArenaMask } from './dodgeTrialArena';

/** 바닥 그리기 (표시 전용 임시값): 절벽 면 높이, 잡점 비율, 균열 금 수, 떨림 시작 비율, 새 경기장이 나타나는 시간 */
const FLOOR_LOOK = {
  CLIFF_PX: 5,
  SPECK_RATE: 0.12,
  CRACKS: 2,
  JITTER_FROM: 0.65,
  APPEAR_MS: 260,
  /** 부스러기 파티클 (아래로 떨어져 사라짐) */
  CHIP: { SPEED: [6, 34] as [number, number], LIFE_MS: [420, 900] as [number, number], GRAVITY: 240 },
  /** 진행 호: 바닥 외곽에서 띄우는 거리 · 두께 · 끝 무렵(남은 비율) 맥동 */
  TIMER_PAD_PX: 6,
  TIMER_WIDTH: 2,
  TIMER_FINAL: 0.18,
};

const TEX_CHIP = 'trial_chip';

/** 칸 index → 0~1 결정적 값 (잡점·균열 모양) */
function hash01(i: number, salt = 0): number {
  let h = Math.imul(i ^ (salt * 0x9e3779b1), 2654435761) >>> 0;
  h ^= h >>> 15;
  h = Math.imul(h, 2246822519) >>> 0;
  h ^= h >>> 13;
  return (h >>> 0) / 4294967296;
}

export class TrialArenaView {
  private readonly arenaG: Phaser.GameObjects.Graphics;
  private readonly timerG: Phaser.GameObjects.Graphics;
  private readonly chips: Phaser.GameObjects.Particles.ParticleEmitter;
  private pillarGs: Phaser.GameObjects.Graphics[] = [];
  private mask: ArenaMask | null = null;
  /** 무너짐 처리 위치 (mask.order 기준): 여기까지 부스러기를 냈다 */
  private eatPtr = 0;

  constructor(
    private readonly scene: Phaser.Scene,
    private readonly cx: number,
    private readonly cy: number,
    private readonly ramp: number[],
    private readonly gray: number[],
  ) {
    if (!scene.textures.exists(TEX_CHIP)) {
      const g = scene.make.graphics({ x: 0, y: 0 }, false);
      g.fillStyle(0xffffff, 1);
      g.fillRect(0, 0, 2, 2);
      g.generateTexture(TEX_CHIP, 2, 2);
      g.destroy();
    }
    const C = FLOOR_LOOK.CHIP;
    this.chips = scene.add.particles(0, 0, TEX_CHIP, {
      emitting: false,
      speed: { min: C.SPEED[0], max: C.SPEED[1] },
      angle: { min: 20, max: 160 },
      lifespan: { min: C.LIFE_MS[0], max: C.LIFE_MS[1] },
      gravityY: C.GRAVITY,
      scale: { start: 1, end: 0.25 },
      alpha: { start: 1, end: 0 },
      rotate: { min: 0, max: 90 },
      tint: [gray[3] ?? 0x2f3033, gray[4] ?? 0x3e4044, gray[5] ?? 0x4d4f53, ramp[3] ?? 0x8a4a1c],
    });
    // 부스러기는 바닥 아래(절벽 뒤로 떨어지는 느낌)
    this.chips.setDepth(DEPTH.TILES + 0.05);
    this.arenaG = scene.add.graphics().setDepth(DEPTH.TILES + 0.1);
    this.timerG = scene.add.graphics().setDepth(DEPTH.TILES + 0.2);
  }

  /** 흐리게 할 대상 (운명 문구) */
  get dimTargets(): Phaser.GameObjects.GameObject[] {
    return [this.arenaG, this.timerG, this.chips, ...this.pillarGs];
  }

  /** 새 경기장 (과제 시작): 짧게 나타난다 */
  setMask(m: ArenaMask): void {
    this.mask = m;
    this.eatPtr = 0;
    for (const g of this.pillarGs) g.destroy();
    this.pillarGs = m.pillars.map((p) => this.drawPillar(p.x, p.y, p.r));
    for (const o of [this.arenaG, ...this.pillarGs]) {
      o.setAlpha(0);
      this.scene.tweens.add({ targets: o, alpha: 1, duration: FLOOR_LOOK.APPEAR_MS });
    }
  }

  emitChips(x: number, y: number, n: number): void {
    this.chips.emitParticleAt(x, y, n);
  }

  /** 한 프레임: 무너진 칸 부스러기 → 바닥 → 진행 호 (progress = null 이면 숨김) */
  update(time: number, elapsed: number, progress: number | null): void {
    const m = this.mask;
    if (!m) return;
    this.crumble(m, elapsed);
    this.drawFloor(m, time, elapsed);
    this.drawTimer(m, time, progress);
  }

  destroy(): void {
    for (const g of this.pillarGs) g.destroy();
    this.pillarGs = [];
    this.chips.destroy();
    this.arenaG.destroy();
    this.timerG.destroy();
  }

  private crumble(m: ArenaMask, el: number): void {
    const E = DODGE_TRIAL.EROSION;
    let budget = E.CRUMBLE_CELLS_PER_FRAME;
    while (this.eatPtr < m.order.length && m.erodeAt[m.order[this.eatPtr]] <= el) {
      const i = m.order[this.eatPtr++];
      if (budget-- <= 0) continue;
      const c = i % m.cols;
      const r = Math.floor(i / m.cols);
      this.chips.emitParticleAt(
        this.cx + m.x0 + (c + 0.5) * m.cell,
        this.cy + m.y0 + (r + 0.5) * m.cell,
        E.CRUMBLE_CHIPS,
      );
    }
  }

  /** 기둥: 그림자 · 몸통(아래 어둡게) · 윗면 타원 · 윗면 테두리. 깊이 = 밑동 y (주인공과 앞뒤 정렬) */
  private drawPillar(px: number, py: number, r: number): Phaser.GameObjects.Graphics {
    const H = DODGE_TRIAL.ARENA.PILLAR.HEIGHT_PX;
    const x = this.cx + px;
    const y = this.cy + py;
    const g = this.scene.add.graphics().setDepth(entityDepth(y + r * 0.5));
    const gray = this.gray;
    g.fillStyle(0x000000, 0.35);
    g.fillEllipse(x, y + r * 0.35, r * 2.4, r * 1.1);
    g.fillStyle(gray[3] ?? 0x2f3033, 1);
    g.fillRect(x - r, y - H, r * 2, H);
    g.fillEllipse(x, y, r * 2, r);
    g.fillStyle(gray[2] ?? 0x212224, 1);
    g.fillRect(x - r, y - H * 0.35, r * 2, H * 0.35);
    g.fillStyle(gray[5] ?? 0x4d4f53, 1);
    g.fillEllipse(x, y - H, r * 2, r);
    g.lineStyle(1, this.ramp[3] ?? 0x8a4a1c, 0.8);
    g.strokeEllipse(x, y - H, r * 2, r);
    g.fillStyle(gray[6] ?? 0x5c5e62, 1);
    g.fillRect(x - r + 1, y - H + 1, 1, H - 2);
    return g;
  }

  private drawFloor(m: ArenaMask, time: number, el: number): void {
    const g = this.arenaG;
    const W = DODGE_TRIAL.EROSION.WARN_MS;
    const L = FLOOR_LOOK;
    const gray = this.gray;
    const cs = m.cell;
    const ox = this.cx + m.x0;
    const oy = this.cy + m.y0;
    const alive = (c: number, r: number) => {
      if (c < 0 || r < 0 || c >= m.cols || r >= m.rows) return false;
      const i = r * m.cols + c;
      return m.floor[i] === 1 && m.erodeAt[i] > el;
    };
    g.clear();
    // 1) 절벽 면 (바닥 아래쪽 가장자리)
    g.fillStyle(gray[1] ?? 0x141516, 1);
    for (let r = 0; r < m.rows; r++)
      for (let c = 0; c < m.cols; c++)
        if (alive(c, r) && !alive(c, r + 1)) g.fillRect(ox + c * cs, oy + (r + 1) * cs, cs, L.CLIFF_PX);
    g.fillStyle(this.ramp[1] ?? 0x3a2216, 0.5);
    for (let r = 0; r < m.rows; r++)
      for (let c = 0; c < m.cols; c++)
        if (alive(c, r) && !alive(c, r + 1)) g.fillRect(ox + c * cs, oy + (r + 1) * cs + L.CLIFF_PX - 1, cs, 1);
    // 2) 바닥 (행 단위로 이어서)
    g.fillStyle(gray[2] ?? 0x212224, 1);
    for (let r = 0; r < m.rows; r++) {
      let run = -1;
      for (let c = 0; c <= m.cols; c++) {
        const a = c < m.cols && alive(c, r);
        if (a && run < 0) run = c;
        else if (!a && run >= 0) {
          g.fillRect(ox + run * cs, oy + r * cs, (c - run) * cs, cs);
          run = -1;
        }
      }
    }
    // 3) 잡점 · 가장자리 테두리 · 균열
    const warnCells: number[] = [];
    for (let r = 0; r < m.rows; r++) {
      for (let c = 0; c < m.cols; c++) {
        if (!alive(c, r)) continue;
        const i = r * m.cols + c;
        const x = ox + c * cs;
        const y = oy + r * cs;
        if (hash01(i) < L.SPECK_RATE) {
          g.fillStyle(gray[3] ?? 0x2f3033, 1);
          g.fillRect(x + Math.floor(hash01(i, 1) * (cs - 1)), y + Math.floor(hash01(i, 2) * (cs - 1)), 1, 1);
        }
        if (m.erodeAt[i] - W <= el) warnCells.push(i);
        const n = !alive(c, r - 1);
        const sth = !alive(c, r + 1);
        const w = !alive(c - 1, r);
        const e = !alive(c + 1, r);
        if (!(n || sth || w || e)) continue;
        g.fillStyle(this.ramp[2] ?? 0x653b24, 0.95);
        if (n) g.fillRect(x, y, cs, 1);
        if (sth) g.fillRect(x, y + cs - 1, cs, 1);
        if (w) g.fillRect(x, y, 1, cs);
        if (e) g.fillRect(x + cs - 1, y, 1, cs);
        if (n) {
          g.fillStyle(gray[5] ?? 0x4d4f53, 0.8);
          g.fillRect(x, y + 1, cs, 1);
        }
      }
    }
    for (const i of warnCells) {
      const k = Phaser.Math.Clamp(1 - (m.erodeAt[i] - el) / W, 0, 1);
      const c = i % m.cols;
      const r = Math.floor(i / m.cols);
      const j = k > L.JITTER_FROM && Math.floor(time / 50 + hash01(i, 3) * 4) % 2 === 0 ? 1 : 0;
      const x = ox + c * cs + (hash01(i, 4) < 0.5 ? j : -j);
      const y = oy + r * cs;
      g.fillStyle(gray[0] ?? 0x0a0a0b, 0.25 + 0.5 * k);
      g.fillRect(x, y, cs, cs);
      // 검은 금 + 그 아래 잔불 (획 연출과 같은 1층 램프)
      g.lineStyle(1, 0x000000, 0.5 + 0.5 * k);
      for (let q = 0; q < L.CRACKS; q++) {
        const a = hash01(i, 10 + q) * Math.PI;
        const len = cs * (0.5 + k);
        const mx = x + cs / 2;
        const my = y + cs / 2;
        g.lineBetween(
          mx - Math.cos(a) * len * 0.5,
          my - Math.sin(a) * len * 0.5,
          mx + Math.cos(a) * len * 0.5,
          my + Math.sin(a) * len * 0.5,
        );
      }
      if (k > 0.4) {
        g.fillStyle(this.ramp[4] ?? 0xa35a1c, (k - 0.4) * 0.9);
        g.fillRect(x + Math.floor(hash01(i, 5) * (cs - 1)), y + Math.floor(hash01(i, 6) * (cs - 1)), 1, 1);
      }
    }
  }

  /** 과제 진행: 바닥 외곽 타원을 따라 줄어드는 호. 끝 무렵은 층 강조색으로 맥동 */
  private drawTimer(m: ArenaMask, time: number, progress: number | null): void {
    const g = this.timerG;
    g.clear();
    if (progress === null) return;
    const left = 1 - Math.max(0, Math.min(1, progress));
    if (left <= 0) return;
    const L = FLOOR_LOOK;
    const final = left <= L.TIMER_FINAL;
    const pulse = final ? 0.6 + 0.4 * Math.sin(time / 60) : 1;
    g.lineStyle(L.TIMER_WIDTH, final ? (this.ramp[10] ?? 0xffffff) : (this.ramp[8] ?? 0xe8b858), 0.9 * pulse);
    const b = m.bounds;
    const rx = Math.max(-b.minX, b.maxX) + L.TIMER_PAD_PX;
    const ry = Math.max(-b.minY, b.maxY) + L.TIMER_PAD_PX;
    const start = -Math.PI / 2;
    const n = Math.max(2, Math.ceil(72 * left));
    g.beginPath();
    for (let k = 0; k <= n; k++) {
      const a = start + Math.PI * 2 * left * (k / n);
      const x = this.cx + Math.cos(a) * rx;
      const y = this.cy + Math.sin(a) * ry;
      if (k === 0) g.moveTo(x, y);
      else g.lineTo(x, y);
    }
    g.strokePath();
  }
}
