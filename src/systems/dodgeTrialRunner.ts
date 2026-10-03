/**
 * 회피 시험 진행 (화면 쪽, 51라운드 2절 "짧은 과제 5개"): 과제마다
 * 제목 카드(CARD_MS, 새 경기장이 나타나고 주인공은 중앙에 선다) → 정비(PREP_MS, 움직일 수 있고 위협 없음)
 * → 과제(cue 표대로 위협, 끝나면 남은 위협이 사라질 때까지) → 과제 결과(CLEAR_MS) → 다음 과제 … → 끝(onDone).
 * 맞으면 밀려난다(피격 수). 밀려나 떨어지면 그 과제만 실패(떨어짐)하고 다음 과제 카드에서 중앙으로 돌아온다.
 * 경기장 = 과제별 무작위 모양(`dodgeTrialArena`), 갉아먹힘은 ②·⑤ 만. 수치·박자 = `dodgeTrial.ts`·`dodgeTrialTasks.ts`.
 * 좌표는 월드 px (Setup 이 메인 카메라를 ZOOM 배로 경기장 중심에 맞춘다).
 */
import Phaser from 'phaser';
import { GAME, TILE } from '../core/Constants';
import { PALETTE } from '../data';
import { DODGE_TRIAL, TASK_IDS, emptyTaskResult, type ArenaShape, type TaskId, type TaskResult } from './dodgeTrial';
import { buildArena, isFloorAt, pickShape, placePillars, type ArenaMask } from './dodgeTrialArena';
import { TrialArenaView } from './dodgeTrialArenaView';
import { TrialHazards, type HazardArena } from './dodgeTrialHazards';
import { TrialPlayer, type TrialGround, type TrialInput } from './dodgeTrialPlayer';
import { taskCues, cueFireMs, taskDurationMs } from './dodgeTrialTasks';
import { FxPool } from './fx';
import { fxCoreColor, hexToInt, rampFor } from './palette';

export type { TrialInput } from './dodgeTrialPlayer';
export type TrialPhase = 'card' | 'prep' | 'run' | 'clear' | 'done';

export interface TrialStatus {
  phase: TrialPhase;
  /** 0-based 과제 번호 */
  index: number;
  task: TaskId;
  total: number;
  hits: number;
  /** 끝난 과제 결과 */
  results: TaskResult[];
  /** 지금 과제 진행 0~1 (run 중) */
  progress: number;
  /** 이번 과제에서 떨어졌다 */
  fell: boolean;
}

export interface TrialRunnerOptions {
  /** 경기장 모양 고정 (디버그). 없으면 과제별 목록에서 무작위 */
  shape?: ArenaShape;
  rnd?: () => number;
}

export class DodgeTrialRunner {
  phase: TrialPhase = 'card';
  readonly cx = GAME.WIDTH / 2;
  readonly cy = GAME.HEIGHT / 2;
  readonly results: TaskResult[] = [];
  mask!: ArenaMask;
  /** 탄 고리 (타원) */
  spawn = { rx: 0, ry: 0 };
  private readonly rnd: () => number;
  private readonly fx: FxPool;
  private readonly view: TrialArenaView;
  private readonly hazards: TrialHazards;
  private readonly player: TrialPlayer;
  private readonly ground: TrialGround;
  private index = 0;
  private current: TaskResult = emptyTaskResult('lines');
  private phaseEnd = 0;
  private taskStart = 0;
  /** 과제 경과 (갉아먹힘 기준, run 밖에서는 멈춤) */
  private elapsed = 0;
  private fallAt: number | null = null;
  private lastFireMs = 0;
  private durationMs = 1;
  private finished = false;

  constructor(
    private readonly scene: Phaser.Scene,
    private readonly onDone: (results: TaskResult[]) => void,
    private readonly opts: TrialRunnerOptions = {},
  ) {
    this.rnd = opts.rnd ?? Math.random;
    const ramp = (rampFor(PALETTE, 1) ?? []).map(hexToInt);
    const gray = PALETTE.gray.map(hexToInt);
    const x0 = hexToInt(fxCoreColor(PALETTE, 0) ?? '#ffffff');
    this.fx = new FxPool(scene);
    this.view = new TrialArenaView(scene, this.cx, this.cy, ramp, gray);
    this.hazards = new TrialHazards(scene, this.fx, ramp, x0, this.rnd, (x, y) => this.view.emitChips(x, y, 4));
    this.player = new TrialPlayer(scene, this.fx, ramp[8] ?? 0xffffff, ramp[6] ?? 0xffffff);
    this.ground = {
      standScore: (x, y) => this.standScore(x, y),
      pushOut: (x, y) => this.pushOut(x, y),
    };
  }

  /** 디버그: 맞지 않고 떨어지지 않음 */
  get god(): boolean {
    return this.player.god;
  }

  set god(on: boolean) {
    this.player.god = on;
  }

  get task(): TaskId {
    return TASK_IDS[this.index];
  }

  start(time: number): void {
    this.beginTask(0, time);
  }

  status(): TrialStatus {
    return {
      phase: this.phase,
      index: this.index,
      task: this.task,
      total: TASK_IDS.length,
      hits: this.current.hits,
      results: this.results.map((r) => ({ ...r })),
      progress: this.phase === 'run' ? Math.min(1, this.elapsed / this.durationMs) : this.phase === 'clear' ? 1 : 0,
      fell: this.current.fell,
    };
  }

  update(time: number, delta: number, input: TrialInput): void {
    const dt = Math.min(delta, 50) / 1000;
    if (this.phase === 'card' && time >= this.phaseEnd) this.beginPrep(time);
    else if (this.phase === 'prep' && time >= this.phaseEnd) this.beginRun(time);
    else if (this.phase === 'clear' && time >= this.phaseEnd) this.next(time);
    if (this.phase === 'run') this.elapsed = time - this.taskStart;
    const canAct = this.phase === 'prep' || this.phase === 'run' || this.phase === 'clear';
    if (this.phase !== 'done' && this.fallAt === null) {
      if (this.player.update(time, dt, input, this.ground, canAct) === 'fell') this.fall(time);
      else if (this.phase === 'run' && !this.player.god && this.standScore(this.player.pos.x, this.player.pos.y) < 0)
        this.fall(time); // 발밑이 무너졌다
    }
    if (this.phase === 'run') this.updateRun(time, dt);
    this.fx.update(time);
    this.player.sync(time, canAct);
    this.view.update(time, this.elapsed, this.phase === 'run' ? this.elapsed / this.durationMs : null);
  }

  private updateRun(time: number, dt: number): void {
    const P = this.player;
    const hit = this.hazards.update(time, dt, {
      x: P.pos.x,
      y: P.pos.y,
      vulnerable: this.fallAt === null && P.vulnerable(time),
    });
    if (hit) {
      this.current.hits += 1;
      P.hit(time, hit.dx, hit.dy);
    }
    if (this.fallAt !== null) {
      if (time - this.fallAt >= DODGE_TRIAL.PLAYER.FALL_MS) this.endTask(time);
      return;
    }
    const over = this.elapsed >= this.lastFireMs && this.hazards.idle;
    const cap = this.elapsed >= this.durationMs + DODGE_TRIAL.SETTLE_MAX_MS;
    if (over || cap) this.endTask(time);
  }

  // --- 진행 ---

  private beginTask(i: number, time: number): void {
    this.index = i;
    const id = TASK_IDS[i];
    const def = DODGE_TRIAL.TASKS[id];
    this.current = emptyTaskResult(id);
    this.phase = 'card';
    this.phaseEnd = time + (i === 0 ? DODGE_TRIAL.FIRST_CARD_MS : DODGE_TRIAL.CARD_MS);
    this.elapsed = 0;
    this.fallAt = null;
    this.hazards.clear(true);
    const shape = this.opts.shape ?? pickShape(this.rnd(), def.shapes);
    this.mask = buildArena(shape, this.rnd, def.erosion);
    const [lo, hi] = def.pillars;
    if (hi > 0) placePillars(this.mask, lo + Math.floor(this.rnd() * (hi - lo + 1)), this.rnd);
    const b = this.mask.bounds;
    const pad = DODGE_TRIAL.ARENA.SPAWN_PAD_TILES * TILE;
    this.spawn = {
      rx: Math.max(-b.minX, b.maxX) + pad,
      ry: Math.min(DODGE_TRIAL.ARENA.SPAWN_MAX_RY_PX, Math.max(-b.minY, b.maxY) + pad),
    };
    this.view.setMask(this.mask);
    this.player.reset(this.cx, this.cy, time);
    this.durationMs = Math.max(1, taskDurationMs(id));
    this.lastFireMs = Math.max(0, ...taskCues(id).map((c) => cueFireMs(c, id)));
  }

  private beginPrep(time: number): void {
    this.phase = 'prep';
    this.phaseEnd = time + DODGE_TRIAL.PREP_MS;
  }

  private beginRun(time: number): void {
    this.phase = 'run';
    this.taskStart = time;
    this.elapsed = 0;
    const arena: HazardArena = {
      mask: this.mask,
      cx: this.cx,
      cy: this.cy,
      spawn: this.spawn,
      floorAt: (x, y) => isFloorAt(this.mask, x - this.cx, y - this.cy, this.elapsed),
    };
    this.hazards.begin(this.task, arena, time);
  }

  /** 과제 끝: 위협 정리, 결과 기록 → CLEAR_MS 동안 결과 한 줄 */
  private endTask(time: number, over: Partial<TaskResult> = {}): void {
    if (this.phase === 'done' || this.phase === 'clear') return;
    this.hazards.clear(true);
    this.current.dashes = this.player.dashes;
    Object.assign(this.current, over);
    this.results.push({ ...this.current });
    this.phase = 'clear';
    this.phaseEnd = time + DODGE_TRIAL.CLEAR_MS;
  }

  private next(time: number): void {
    if (this.index + 1 < TASK_IDS.length) this.beginTask(this.index + 1, time);
    else this.finish();
  }

  private finish(): void {
    if (this.finished) return;
    this.finished = true;
    this.phase = 'done';
    this.hazards.clear(true);
    this.onDone(this.results.map((r) => ({ ...r })));
  }

  private fall(time: number): void {
    if (this.fallAt !== null || this.phase === 'done') return;
    this.player.sink();
    this.view.emitChips(this.player.pos.x, this.player.pos.y + DODGE_TRIAL.PLAYER.FOOT_OFFSET_PX, 10);
    this.fallAt = time;
    this.current.fell = true;
    // 정비·결과 중 떨어질 일은 없지만(걸어서는 못 나간다), 혹시 그러면 run 처럼 끝낸다
    if (this.phase !== 'run') {
      this.phase = 'run';
      this.taskStart = time;
    }
  }

  // --- 바닥 ---

  /** 발 자리 점수: 발 중심이 바닥이 아니면 -1, 아니면 둘레 4점 중 바닥 수 */
  private standScore(x: number, y: number): number {
    const fy = y + DODGE_TRIAL.PLAYER.FOOT_OFFSET_PX;
    const floor = (px: number, py: number) => isFloorAt(this.mask, px - this.cx, py - this.cy, this.elapsed);
    if (!floor(x, fy)) return -1;
    const m = DODGE_TRIAL.ARENA.WALK_MARGIN_PX;
    let n = 0;
    for (const [dx, dy] of [
      [m, 0],
      [-m, 0],
      [0, m],
      [0, -m],
    ])
      if (floor(x + dx, fy + dy)) n += 1;
    return n;
  }

  /** 발이 기둥에 겹치면 기둥 밖으로 */
  private pushOut(x: number, y: number): { x: number; y: number } {
    const P = DODGE_TRIAL.PLAYER;
    const fy = y + P.FOOT_OFFSET_PX;
    for (const p of this.mask.pillars) {
      const px = this.cx + p.x;
      const py = this.cy + p.y;
      const d = Math.hypot(x - px, fy - py);
      const min = p.r + P.FOOT_RADIUS_PX;
      if (d >= min) continue;
      const ux = d > 1e-3 ? (x - px) / d : 1;
      const uy = d > 1e-3 ? (fy - py) / d : 0;
      x = px + ux * min;
      y = py + uy * min - P.FOOT_OFFSET_PX;
    }
    return { x, y };
  }

  // --- 디버그 ---

  /** 지금 과제를 바로 끝낸다 (결과 덮어쓰기 가능). 카드·정비 중이면 그 과제를 건너뛴 것으로 */
  skipTask(over: Partial<TaskResult> = {}): boolean {
    if (this.phase === 'done' || this.phase === 'clear') return false;
    const t = this.scene.time.now;
    if (this.phase !== 'run') {
      this.phase = 'run';
      this.taskStart = t;
    }
    this.endTask(t, over);
    return true;
  }

  /** n 번째(0-based) 과제부터 다시 (앞 과제는 건너뜀 = 무피격으로 친다) */
  startTask(n: number): boolean {
    if (n < 0 || n >= TASK_IDS.length || this.finished) return false;
    this.results.length = 0;
    for (let i = 0; i < n; i++) this.results.push({ ...emptyTaskResult(TASK_IDS[i]), skipped: true });
    this.beginTask(n, this.scene.time.now);
    return true;
  }

  /** 즉시 시험 종료 (결과 통째로) */
  forceEnd(results: TaskResult[]): void {
    if (this.finished) return;
    this.results.length = 0;
    this.results.push(...results.map((r) => ({ ...r })));
    this.finish();
  }

  /** 카드·정비면 바로 과제 시작, 과제 중이면 시계를 ms 앞당김 (갉아먹힘·예약) */
  warp(ms: number): void {
    const now = this.scene.time.now;
    if (this.phase === 'card' || this.phase === 'prep') {
      this.beginRun(now);
      return;
    }
    if (this.phase !== 'run') return;
    this.taskStart -= ms;
    this.hazards.warp(ms);
  }

  snapshot(): Record<string, unknown> {
    const now = this.scene.time.now;
    const P = this.player;
    const m = this.mask;
    let alive = 0;
    let warn = 0;
    for (const i of m.order) {
      if (m.erodeAt[i] <= this.elapsed) continue;
      alive += 1;
      if (m.erodeAt[i] - DODGE_TRIAL.EROSION.WARN_MS <= this.elapsed) warn += 1;
    }
    return {
      ...this.status(),
      elapsedMs: Math.round(this.elapsed),
      durationMs: Math.round(this.durationMs),
      player: {
        x: +P.pos.x.toFixed(1),
        y: +P.pos.y.toFixed(1),
        fromCenter: +Math.hypot(P.pos.x - this.cx, P.pos.y - this.cy).toFixed(1),
        facing: P.facingDir,
        dashing: P.dashing(now),
        invuln: P.invulnerable(now),
        knock: P.knocked,
        fallen: P.fallen,
        onFloor: this.standScore(P.pos.x, P.pos.y) >= 0,
      },
      animated: P.isAnimated,
      anim: P.animKey,
      god: P.god,
      hazards: this.hazards.counts(),
      arena: {
        shape: m.shape,
        cx: this.cx,
        cy: this.cy,
        cells: m.cells,
        alive,
        aliveFrac: +(alive / Math.max(1, m.cells)).toFixed(3),
        warn,
        erosion: m.erosion,
        pillars: m.pillars.map((p) => ({ x: Math.round(p.x), y: Math.round(p.y), r: +p.r.toFixed(1) })),
        bounds: { ...m.bounds },
        spawn: { ...this.spawn },
      },
    };
  }

  /** 운명 문구를 위해 경기장 전체를 흐리게 */
  dim(): void {
    // 떨어진 주인공은 이미 사라졌다 — 다시 비치지 않게 뺀다
    const targets = [
      ...this.view.dimTargets,
      ...this.hazards.dimTargets,
      ...(this.player.fallen ? [] : this.player.objects),
    ];
    this.scene.tweens.add({ targets, alpha: DODGE_TRIAL.DIM_ALPHA, duration: DODGE_TRIAL.DIM_MS });
  }

  destroy(): void {
    this.hazards.destroy();
    this.fx.destroy();
    this.player.destroy();
    this.view.destroy();
  }
}
