/**
 * 회피 시험 위협 (화면 쪽, 51라운드 2절): 과제의 cue 표를 시각에 맞춰 실행한다. 모든 위협은 **예고가 먼저**.
 * - 예고선(line): 예고선(TelegraphFx.line + 오라)이 그어진 뒤 그 선을 따라 직선탄 BURST 발.
 * - 고리(ring): 고리 윤곽 + 밝은 틈 예고 → 구슬 고리가 중심으로 조여 든다. 틈으로 빠져나가면 안전(판정은 해석식 `ringHits`).
 * - 유도탄(homing): 원 예고 → 느린 유도탄(회전 한계). 기둥에 닿으면 깨지고, 수명이 다하면 사그라든다.
 * - 탄막 벽(wall): 벽 자리 선 + 진행 화살 예고 → 빈틈 없는 탄 줄이 경기장을 가로지른다(대쉬 무적으로만 통과).
 *   벽이 가까워지면(DASH_HINT_PX) 벽 등뼈가 밝아진다 = 대쉬 박자.
 * 탄 풀(생성·이동·판정) = `dodgeTrialBullets.ts`.
 */
import Phaser from 'phaser';
import { DEPTH, ENEMY_FX, TILE } from '../core/Constants';
import { audio } from './audio';
import { SFX } from './audioMap';
import { DODGE_TRIAL, type Cue, type TaskId } from './dodgeTrial';
import type { ArenaMask } from './dodgeTrialArena';
import { SHOT_SFX_ENEMY, TrialBullets } from './dodgeTrialBullets';
import {
  lineTelegraphMs,
  pickWallAngle,
  ringBeadAngles,
  ringHits,
  ringRadius,
  taskCues,
  wallFrame,
} from './dodgeTrialTasks';
import type { FxPool } from './fx';
import { TelegraphFx } from './telegraph';
import { drawHazards, wallAlong, type Ring, type Wall } from './dodgeTrialHazardsView';

/** 지금 과제의 경기장 (러너가 넘긴다) */
export interface HazardArena {
  mask: ArenaMask;
  cx: number;
  cy: number;
  /** 탄이 나오는 고리 (타원 반지름) */
  spawn: { rx: number; ry: number };
  /** 지금 그 자리가 바닥인가 (월드 px, 갉아먹힘 반영) */
  floorAt(x: number, y: number): boolean;
}

/** 주인공 상태 (판정용) */
export interface HazardTarget {
  x: number;
  y: number;
  vulnerable: boolean;
}

export interface HazardCounts {
  bullets: number;
  homing: number;
  rings: number;
  walls: number;
  telegraphs: number;
  pending: number;
  fired: number;
  broken: number;
  cues: Record<Cue['kind'], number>;
  /** 주인공에게 다가오는(움직이는) 벽까지 가장 가까운 거리 px — 없으면 null (디버그·검증 봇용) */
  wallNear: number | null;
  /** 읽을 수 있는 위협 (디버그·검증 봇용): 예고/비행 중 선 · 고리 · 움직이는 벽 방향 · 유도탄 위치 */
  threats: {
    lines: { x: number; y: number; a: number; fireAt: number }[];
    rings: { cx: number; cy: number; r: number; gapAngle: number; closing: boolean }[];
    /** near = 주인공까지 거리 px (다가오는 중일 때만, 아니면 null) */
    walls: { angle: number; moving: boolean; near: number | null }[];
    homing: { x: number; y: number }[];
  };
}

/** 디버그 위협 목록에 선을 남겨 두는 시간 (발사 뒤) */
const LINE_MARK_MS = 700;

export class TrialHazards {
  private readonly telegraph: TelegraphFx;
  private readonly g: Phaser.GameObjects.Graphics;
  private readonly beadG: Phaser.GameObjects.Graphics;
  private readonly bullets: TrialBullets;
  private pending: { at: number; run: () => void }[] = [];
  private rings: Ring[] = [];
  private walls: Wall[] = [];
  private arena: HazardArena | null = null;
  private task: TaskId = 'lines';
  private target: HazardTarget = { x: 0, y: 0, vulnerable: false };
  private lastWallAngle: number | null = null;
  private cueCount: Record<Cue['kind'], number> = { line: 0, ring: 0, homing: 0, wall: 0 };
  /** 디버그용 선 위협 기록 (예고 시작 ~ 발사 뒤 LINE_MARK_MS) */
  private lineMarks: { x: number; y: number; a: number; fireAt: number }[] = [];

  constructor(
    private readonly scene: Phaser.Scene,
    fx: FxPool,
    private readonly ramp: number[],
    private readonly x0: number,
    private readonly rnd: () => number,
    /** 탄이 기둥에 깨질 때 (부스러기) */
    onBreak: (x: number, y: number) => void,
  ) {
    this.bullets = new TrialBullets(scene, fx, ramp[10] ?? 0xffffff, ramp[9] ?? 0xd8783a, onBreak);
    this.telegraph = new TelegraphFx(scene);
    this.telegraph.setFloor(1);
    this.g = scene.add.graphics().setDepth(DEPTH.FX_GROUND + 0.01);
    this.beadG = scene.add.graphics().setDepth(DEPTH.PROJECTILE);
  }

  /** 과제 시작: cue 표를 시각에 건다 */
  begin(task: TaskId, arena: HazardArena, time: number): void {
    this.clear(false);
    this.task = task;
    this.arena = arena;
    this.lastWallAngle = null;
    this.cueCount = { line: 0, ring: 0, homing: 0, wall: 0 };
    for (const cue of taskCues(task))
      this.pending.push({ at: time + cue.at, run: () => this.startCue(cue, time + cue.at) });
  }

  /** 남은 예약 · 살아 있는 위협이 없다 */
  get idle(): boolean {
    return this.pending.length === 0 && this.rings.length === 0 && this.walls.length === 0 && !this.bullets.anyAlive;
  }

  /** 디버그: 예약을 ms 만큼 앞당긴다 */
  warp(ms: number): void {
    for (const p of this.pending) p.at -= ms;
  }

  /** 한 프레임: 예약 실행 → 탄 이동·판정 → 고리·벽 → 그리기. 맞았으면 밀려날 방향 */
  update(time: number, dt: number, target: HazardTarget): { dx: number; dy: number } | null {
    this.target = target;
    this.runPending(time);
    const A = this.arena;
    let hit = A ? this.bullets.update(time, dt, A, target) : null;
    hit = this.updateRings(time, hit);
    this.updateWalls(time);
    this.telegraph.update(time);
    this.draw(time);
    return hit;
  }

  /** 과제 끝: 예약·예고·고리·벽 제거, 탄은 (fade 면) 사라지며 */
  clear(fade: boolean): void {
    this.pending = [];
    this.lineMarks = [];
    this.rings = [];
    this.walls = [];
    this.telegraph.destroy();
    this.g.clear();
    this.beadG.clear();
    this.bullets.clear(fade);
  }

  counts(): HazardCounts {
    return {
      bullets: this.bullets.count(),
      homing: this.bullets.count('homing'),
      rings: this.rings.length,
      walls: this.walls.length,
      telegraphs: this.telegraph.count,
      pending: this.pending.length,
      fired: this.bullets.fired,
      broken: this.bullets.broken,
      cues: { ...this.cueCount },
      wallNear: this.nearestWall(this.scene.time.now),
      threats: this.threats(this.scene.time.now),
    };
  }

  private threats(time: number): HazardCounts['threats'] {
    const R = DODGE_TRIAL.RING;
    const r2 = (v: number) => Math.round(v * 100) / 100;
    this.lineMarks = this.lineMarks.filter((l) => time - l.fireAt < LINE_MARK_MS);
    return {
      lines: this.lineMarks.map((l) => ({
        x: Math.round(l.x),
        y: Math.round(l.y),
        a: r2(l.a),
        fireAt: Math.round(l.fireAt - time),
      })),
      rings: this.rings.map((r) => ({
        cx: Math.round(r.cx),
        cy: Math.round(r.cy),
        r: Math.round(ringRadius(time - r.start, r.closeMs, r.R0)),
        gapAngle: r2(r.gapAngle),
        closing: time - r.start >= R.WARN_MS,
      })),
      walls: this.walls.map((w) => {
        const moving = time - w.start >= DODGE_TRIAL.WALL.WARN_MS;
        const rel = moving ? this.wallRel(w, time) : -1;
        return { angle: r2(w.angle), moving, near: rel > 0 ? Math.round(rel) : null };
      }),
      homing: this.bullets.homingPositions(),
    };
  }

  private nearestWall(time: number): number | null {
    let best: number | null = null;
    for (const w of this.walls) {
      if (time - w.start < DODGE_TRIAL.WALL.WARN_MS) continue;
      const rel = this.wallRel(w, time);
      if (rel > 0 && (best === null || rel < best)) best = rel;
    }
    return best === null ? null : Math.round(best);
  }

  /** 주인공이 벽 등뼈보다 진행 방향으로 얼마나 앞에 있나 (양수 = 벽이 다가오는 중) */
  private wallRel(w: Wall, time: number): number {
    const A = this.arena;
    if (!A) return -1;
    return (this.target.x - A.cx) * Math.cos(w.angle) + (this.target.y - A.cy) * Math.sin(w.angle) - wallAlong(w, time);
  }

  get dimTargets(): Phaser.GameObjects.GameObject[] {
    return [this.g, this.beadG];
  }

  destroy(): void {
    this.pending = [];
    this.telegraph.destroy();
    this.bullets.destroy();
    this.g.destroy();
    this.beadG.destroy();
  }

  // --- 예약 ---

  private runPending(time: number): void {
    if (this.pending.length === 0) return;
    const due = this.pending.filter((p) => p.at <= time);
    if (due.length === 0) return;
    this.pending = this.pending.filter((p) => p.at > time);
    due.sort((a, b) => a.at - b.at);
    for (const p of due) p.run();
  }

  private schedule(at: number, run: () => void): void {
    this.pending.push({ at, run });
  }

  private spawnPoint(theta: number): { x: number; y: number } {
    const A = this.arena!;
    return { x: A.cx + Math.cos(theta) * A.spawn.rx, y: A.cy + Math.sin(theta) * A.spawn.ry };
  }

  private startCue(cue: Cue, at: number): void {
    const A = this.arena;
    if (!A) return;
    this.cueCount[cue.kind] += 1;
    switch (cue.kind) {
      case 'line':
        return this.startLines(cue.count, at, lineTelegraphMs(cue.at, this.task));
      case 'ring':
        return this.startRing(cue.gapDeg, cue.closeMs, at);
      case 'homing':
        return this.startHoming(at);
      case 'wall':
        return this.startWall(at);
    }
  }

  /** ① 예고선: 주인공이 지금 선 자리를 지나는 선 (1 = 하나, 2 = 수직인 두 곳, 3 = 한 곳에서 부채꼴) */
  private startLines(count: 1 | 2 | 3, at: number, tele: number): void {
    const A = this.arena!;
    const L = DODGE_TRIAL.LINES;
    const theta = this.rnd() * Math.PI * 2;
    const len = 2 * Math.max(A.spawn.rx, A.spawn.ry) + TILE;
    const lines: { x: number; y: number; a: number }[] = [];
    const aim = (o: { x: number; y: number }) => Math.atan2(this.target.y - o.y, this.target.x - o.x);
    if (count === 3) {
      const o = this.spawnPoint(theta);
      const a = aim(o);
      const f = Phaser.Math.DegToRad(L.FAN_DEG);
      for (const d of [-f, 0, f]) lines.push({ ...o, a: a + d });
    } else {
      const thetas = count === 2 ? [theta, theta + (Math.PI / 2) * (this.rnd() < 0.5 ? 1 : -1)] : [theta];
      for (const th of thetas) {
        const o = this.spawnPoint(th);
        lines.push({ ...o, a: aim(o) });
      }
    }
    const speed = L.SPEED_TILES * TILE;
    for (const ln of lines) {
      this.telegraph.line(ln.x, ln.y, ln.a, len, tele, { aura: true });
      this.lineMarks.push({ x: ln.x, y: ln.y, a: ln.a, fireAt: at + tele });
      for (let k = 0; k < L.BURST; k++)
        this.schedule(at + tele + k * L.BURST_GAP_MS, () =>
          this.bullets.fire('line', ln.x, ln.y, ln.a, speed, ENEMY_FX.BULLET, k === 0),
        );
    }
  }

  /** ② 고리: 중심 = 주인공 자리를 경기장 중심 쪽으로 조금, 틈 = 바닥이 이어진 쪽 */
  private startRing(gapDeg: number, closeMs: number, at: number): void {
    const A = this.arena!;
    const R = DODGE_TRIAL.RING;
    const cx = this.target.x + (A.cx - this.target.x) * R.PULL;
    const cy = this.target.y + (A.cy - this.target.y) * R.PULL;
    const ok: number[] = [];
    for (let deg = 0; deg < 360; deg += R.DIR_STEP_DEG) {
      const a = Phaser.Math.DegToRad(deg);
      if (R.PROBE.every((f) => A.floorAt(cx + Math.cos(a) * R.R0_PX * f, cy + Math.sin(a) * R.R0_PX * f))) ok.push(a);
    }
    const gapAngle = ok.length
      ? ok[Math.min(ok.length - 1, Math.floor(this.rnd() * ok.length))]
      : this.rnd() * Math.PI * 2;
    this.rings.push({
      cx,
      cy,
      R0: R.R0_PX,
      gapAngle,
      gapDeg,
      closeMs,
      start: at,
      beads: ringBeadAngles(R.R0_PX, gapAngle, gapDeg, R.BEAD_SPACING_PX),
    });
    this.schedule(at + R.WARN_MS, () => audio.playSfx(SFX.bossFan));
  }

  /** ③ 유도탄: 바깥 고리 한 점에 원 예고 → 주인공 쪽으로 출발 */
  private startHoming(at: number): void {
    const H = DODGE_TRIAL.HOMING;
    const o = this.spawnPoint(this.rnd() * Math.PI * 2);
    this.telegraph.circle(o.x, o.y, TILE * 0.75, H.TELEGRAPH_MS, { aura: true });
    this.schedule(at + H.TELEGRAPH_MS, () => {
      const a = Math.atan2(this.target.y - o.y, this.target.x - o.x);
      this.bullets.fire('homing', o.x, o.y, a, H.SPEED_TILES * TILE, ENEMY_FX.FAN_SHOT, false);
      audio.playSfx(SFX.bossFan);
    });
  }

  /** ④ 벽: 직전과 90° 이상 다른 방향에서, 경기장 외곽 상자를 다 덮는 탄 줄 */
  private startWall(at: number): void {
    const A = this.arena!;
    const W = DODGE_TRIAL.WALL;
    const angle = pickWallAngle(this.lastWallAngle, this.rnd);
    this.lastWallAngle = angle;
    const f = wallFrame(A.mask.bounds, angle, W.PAD_PX);
    const wall: Wall = { angle, from: f.from, to: f.to, half: f.half, start: at, speed: W.SPEED_TILES * TILE };
    this.walls.push(wall);
    this.schedule(at + W.WARN_MS, () => {
      const ux = Math.cos(angle);
      const uy = Math.sin(angle);
      const life = ((wall.to - wall.from) / wall.speed) * 1000 + 120;
      for (let o = -wall.half; o <= wall.half + 1e-6; o += W.SPACING_PX) {
        const x = A.cx + ux * wall.from - uy * o;
        const y = A.cy + uy * wall.from + ux * o;
        this.bullets.fire('wall', x, y, angle, wall.speed, ENEMY_FX.BULLET, false, life);
      }
      audio.playSfx(SFX.enemyShot(SHOT_SFX_ENEMY));
    });
  }

  // --- 고리 · 벽 ---

  private updateRings(time: number, hit: { dx: number; dy: number } | null): { dx: number; dy: number } | null {
    const P = DODGE_TRIAL.PLAYER;
    const R = DODGE_TRIAL.RING;
    const tg = this.target;
    this.rings = this.rings.filter((r) => {
      const t = time - r.start;
      if (t < R.WARN_MS) return true;
      const rad = ringRadius(t, r.closeMs, r.R0);
      if (rad <= 0) return false;
      if (
        !hit &&
        tg.vulnerable &&
        ringHits(r.cx, r.cy, rad, r.gapAngle, r.gapDeg, tg.x, tg.y, P.HIT_RADIUS_PX, R.BEAD_R_PX)
      ) {
        // 바깥쪽으로 밀어낸다 (고리를 넘어 밖으로)
        const dx = tg.x - r.cx;
        const dy = tg.y - r.cy;
        hit = Math.hypot(dx, dy) > 0.5 ? { dx, dy } : { dx: Math.cos(r.gapAngle), dy: Math.sin(r.gapAngle) };
      }
      return true;
    });
    return hit;
  }

  private updateWalls(time: number): void {
    const W = DODGE_TRIAL.WALL;
    this.walls = this.walls.filter((w) => time - w.start < W.WARN_MS || wallAlong(w, time) <= w.to);
  }

  private draw(time: number): void {
    const A = this.arena;
    this.g.clear();
    this.beadG.clear();
    if (!A) return;
    this.bullets.drawTrails(this.beadG);
    drawHazards(this.g, this.beadG, this.rings, this.walls, time, {
      hot: this.ramp[9] ?? 0xd8783a,
      bright: this.ramp[10] ?? 0xffc070,
      x0: this.x0,
      cx: A.cx,
      cy: A.cy,
      wallRel: (w) => this.wallRel(w, time),
    });
  }
}
