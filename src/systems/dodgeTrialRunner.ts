/**
 * 15초 회피 시험의 화면 쪽 (48라운드 Q7 → 49라운드 2절 개편). 수치·모양·갉아먹힘·등급은 `dodgeTrial.ts`.
 *
 * - 경기장 모양은 매번 무작위(원·타원·불규칙 다각형·여러 섬, `buildArena`) — 4px 칸 격자 바닥.
 * - 본 시험 1.5초 뒤부터 가장자리부터 갉아먹혀 좁아진다: 무너지기 전 균열(어두워짐·검은 금·잔불·떨림) → 무너짐(칸이 사라지고
 *   부스러기가 아래로 떨어짐). 무너진 곳은 낙사 영역 — 발밑이 무너지거나 맞고 밀려 바닥 밖으로 나가면 떨어져 즉시 종료.
 * - 주인공(player 시트, WASD + 스페이스 대쉬)은 걸어서·대쉬로는 바닥 밖으로 못 나간다.
 * - 바닥 외곽 타원 + 여백 고리에서 투사체(enemy_bullet · boss_fan_shot 시트, 예고 telegraph 재사용)를
 *   조준탄·부채꼴·교차·원형 확산으로 15초간, 갈수록 촘촘·빠르게, 마지막 3초는 동시 2패턴.
 * - 맞으면 피격 연출 + 투사체 진행 방향으로 밀려남. 체력 없음(피격 횟수만).
 * - 측정: 버틴 시간·피격·떨어짐(등급용) + 회피 거리 분류·대쉬 직전 회피(기록만).
 * 좌표는 월드 px (Setup 이 메인 카메라를 ZOOM 배로 경기장 중심에 맞춘다).
 */
import Phaser from 'phaser';
import { DEPTH, ENEMY_FX, FEEL, GAME, TILE, entityDepth } from '../core/Constants';
import { PALETTE, PLAYER_DATA } from '../data';
import { audio } from './audio';
import { SFX } from './audioMap';
import {
  DODGE_TRIAL,
  buildArena,
  cellIndexAt,
  classifyGap,
  emptySample,
  isDashDodge,
  pickPattern,
  pickShape,
  ringIndices,
  trialStep,
  type ArenaMask,
  type ArenaShape,
  type DodgeSample,
  type PatternKind,
  type TrialStep,
} from './dodgeTrial';
import { FxPool } from './fx';
import { hexToInt, rampFor } from './palette';
import { FX_ACTION, facingOf, type Facing } from './spriteDefs';
import { spriteLibrary } from './sprites';
import { TelegraphFx } from './telegraph';

export type TrialPhase = 'intro' | 'run' | 'done';

export interface TrialInput {
  mx: number;
  my: number;
  dash: boolean;
}

interface Bullet {
  spr: Phaser.GameObjects.Sprite;
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
  born: number;
  alive: boolean;
  minGap: number;
  minAt: number;
  lastGap: number;
}

const TEX_PLAYER_PH = 'trial_player_ph';
const TEX_BULLET_PH = 'trial_bullet_ph';
const TEX_CHIP = 'trial_chip';

/** 바닥 그리기 (표시 전용 임시값): 절벽 면 높이, 잡점 비율, 균열 금 수, 떨림 시작 비율 */
const FLOOR_LOOK = {
  CLIFF_PX: 5,
  SPECK_RATE: 0.12,
  CRACKS: 2,
  JITTER_FROM: 0.65,
  /** 부스러기 파티클 (아래로 떨어져 사라짐) */
  CHIP: { SPEED: [6, 34] as [number, number], LIFE_MS: [420, 900] as [number, number], GRAVITY: 240 },
  /** 떨어질 때 발밑 부스러기 수 */
  FALL_CHIPS: 10,
};

/** 칸 index → 0~1 결정적 값 (잡점·균열 모양) */
function hash01(i: number, salt = 0): number {
  let h = Math.imul(i ^ (salt * 0x9e3779b1), 2654435761) >>> 0;
  h ^= h >>> 15;
  h = Math.imul(h, 2246822519) >>> 0;
  h ^= h >>> 13;
  return (h >>> 0) / 4294967296;
}

export interface TrialRunnerOptions {
  /** 경기장 모양 고정 (디버그). 없으면 무작위 */
  shape?: ArenaShape;
  rnd?: () => number;
}
/** 사수 탄 효과음 id (enemies.json 의 원거리 적) */
const SHOT_SFX_ENEMY = 'archer';

export class DodgeTrialRunner {
  phase: TrialPhase = 'intro';
  readonly sample: DodgeSample = emptySample();
  readonly cx = GAME.WIDTH / 2;
  readonly cy = GAME.HEIGHT / 2;
  readonly mask: ArenaMask;
  /** 바닥 외곽 반폭·반높이 (중심 기준, 타이머 호) */
  readonly outer: { rx: number; ry: number };
  /** 투사체 고리 (타원) */
  readonly spawn: { rx: number; ry: number };
  private readonly rnd: () => number;
  private readonly player: Phaser.GameObjects.Sprite;
  private readonly shadow: Phaser.GameObjects.Ellipse;
  private readonly animated: boolean;
  private readonly arenaG: Phaser.GameObjects.Graphics;
  private readonly timerG: Phaser.GameObjects.Graphics;
  private readonly chips: Phaser.GameObjects.Particles.ParticleEmitter;
  private readonly gray: number[];
  /** 무너짐 처리 위치 (mask.order 기준): 여기까지 부스러기를 냈다 */
  private eatPtr = 0;
  /** 시험이 끝난 시점의 경과 (끝난 뒤 갉아먹힘 멈춤) */
  private frozenElapsed: number | null = null;
  /** 디버그: 맞지 않고 떨어지지 않음 (스크린샷용) */
  god = false;
  private readonly telegraph: TelegraphFx;
  private readonly fx: FxPool;
  private readonly bullets: Bullet[] = [];
  private readonly pending: { at: number; fire: () => void }[] = [];
  private readonly ramp: number[];
  private pos = new Phaser.Math.Vector2();
  private facing: Facing = 'down';
  private lastDir = new Phaser.Math.Vector2(0, 1);
  private introEndAt = 0;
  private runStartAt = 0;
  private endAt = 0;
  private nextWaveAt = 0;
  private dashUntil = 0;
  private dashReadyAt = 0;
  private lastDashAt = -Infinity;
  private dashDir = new Phaser.Math.Vector2();
  private invulnUntil = 0;
  private hurtUntil = 0;
  private flashUntil = 0;
  private knock: { vx: number; vy: number; startAt: number; until: number } | null = null;
  private waves = 0;
  private fired = 0;
  private patternCount: Record<PatternKind, number> = { aimed: 0, fan: 0, cross: 0, ring: 0 };
  private ended = false;
  /** 이번 프레임 이동 입력 (걷기 애니 선택) */
  private movingInput = false;

  constructor(
    private readonly scene: Phaser.Scene,
    private readonly onDone: (sample: DodgeSample) => void,
    opts: TrialRunnerOptions = {},
  ) {
    this.rnd = opts.rnd ?? Math.random;
    this.ramp = (rampFor(PALETTE, 1) ?? []).map(hexToInt);
    this.gray = PALETTE.gray.map(hexToInt);
    this.mask = buildArena(opts.shape ?? pickShape(this.rnd()), this.rnd);
    const b = this.mask.bounds;
    this.outer = { rx: Math.max(-b.minX, b.maxX), ry: Math.max(-b.minY, b.maxY) };
    const pad = DODGE_TRIAL.ARENA.SPAWN_PAD_TILES * TILE;
    this.spawn = { rx: this.outer.rx + pad, ry: Math.min(DODGE_TRIAL.ARENA.SPAWN_MAX_RY_PX, this.outer.ry + pad) };
    this.ensureTextures();
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
      tint: [this.gray[3] ?? 0x2f3033, this.gray[4] ?? 0x3e4044, this.gray[5] ?? 0x4d4f53, this.ramp[3] ?? 0x8a4a1c],
    });
    // 부스러기는 바닥 아래(절벽 뒤로 떨어지는 느낌), 바닥 위로는 그리지 않는다
    this.chips.setDepth(DEPTH.TILES + 0.05);
    this.arenaG = scene.add.graphics().setDepth(DEPTH.TILES + 0.1);
    this.timerG = scene.add.graphics().setDepth(DEPTH.TILES + 0.2);
    this.drawArena(0);
    this.telegraph = new TelegraphFx(scene);
    this.telegraph.setFloor(1);
    this.fx = new FxPool(scene);
    const tex = spriteLibrary.textureKey('player', 'idle');
    const idle = spriteLibrary.sheet('player', 'idle');
    this.animated = Boolean(idle && tex && scene.textures.exists(tex));
    this.player = scene.add.sprite(0, 0, this.animated ? tex! : TEX_PLAYER_PH);
    if (this.animated && idle) this.player.setOrigin(idle.pivot.x / idle.frameWidth, idle.pivot.y / idle.frameHeight);
    else this.player.setOrigin(0.5, 1);
    const SH = DODGE_TRIAL.PLAYER.SHADOW;
    this.shadow = scene.add.ellipse(0, 0, SH.W, SH.H, 0x000000, SH.ALPHA).setDepth(DEPTH.SHADOW);
    this.pos.set(this.cx, this.cy);
    this.syncPlayer(0);
  }

  /** 본 시험 경과 ms (안내 중 0, 끝나면 멈춤) */
  elapsedAt(time: number): number {
    if (this.frozenElapsed !== null) return this.frozenElapsed;
    if (this.phase !== 'run') return 0;
    return Math.max(0, time - this.runStartAt);
  }

  /** 월드 좌표가 지금 바닥인가 */
  private floorAt(x: number, y: number, elapsed: number): boolean {
    const i = cellIndexAt(this.mask, x - this.cx, y - this.cy);
    return i >= 0 && this.mask.floor[i] === 1 && this.mask.erodeAt[i] > elapsed;
  }

  /** 발 자리 점수: 발 중심이 바닥이 아니면 -1, 아니면 둘레 4점 중 바닥 수 */
  private standScore(x: number, y: number, elapsed: number): number {
    const fy = y + DODGE_TRIAL.PLAYER.FOOT_OFFSET_PX;
    if (!this.floorAt(x, fy, elapsed)) return -1;
    const m = DODGE_TRIAL.ARENA.WALK_MARGIN_PX;
    let n = 0;
    for (const [dx, dy] of [
      [m, 0],
      [-m, 0],
      [0, m],
      [0, -m],
    ])
      if (this.floorAt(x + dx, fy + dy, elapsed)) n += 1;
    return n;
  }

  /** 디버그: 본 시험 시계를 ms 만큼 앞당긴다 (안내 중이면 바로 시작) */
  warp(ms: number): void {
    const now = this.scene.time.now;
    if (this.phase === 'intro') this.introEndAt = now;
    if (this.phase !== 'run' || this.ended) return;
    this.runStartAt -= ms;
    this.endAt -= ms;
    this.nextWaveAt = now;
  }

  /** 안내 시작 (이동은 가능, 투사체 없음) → INTRO_MS 뒤 15초 시작 */
  start(time: number): void {
    this.phase = 'intro';
    this.introEndAt = time + DODGE_TRIAL.INTRO_MS;
  }

  get timeLeftMs(): number {
    if (this.phase === 'intro') return DODGE_TRIAL.DURATION_MS;
    if (this.phase === 'done') return 0;
    return Math.max(0, this.endAt - this.scene.time.now);
  }

  update(time: number, delta: number, input: TrialInput): void {
    const dt = Math.min(delta, 50) / 1000;
    if (this.phase === 'intro' && time >= this.introEndAt) {
      this.phase = 'run';
      this.runStartAt = time;
      this.endAt = time + DODGE_TRIAL.DURATION_MS;
      this.nextWaveAt = time + DODGE_TRIAL.CURVE.INTERVAL_MS[0] / 2;
    }
    this.movingInput = input.mx !== 0 || input.my !== 0;
    if (this.phase !== 'done') this.movePlayer(time, dt, input);
    if (this.phase === 'run') {
      this.sample.frames += 1;
      if (input.mx !== 0 || input.my !== 0) this.sample.movingFrames += 1;
      this.erode(time);
      this.spawnWaves(time);
      this.firePending(time);
      this.updateBullets(time, dt);
      if (!this.ended && time >= this.endAt) this.finish(time, false);
    } else if (this.phase === 'done') this.updateBullets(time, dt);
    this.telegraph.update(time);
    this.fx.update(time);
    this.syncPlayer(time);
    this.drawArena(time);
    this.drawTimer(time);
  }

  /** 무너진 칸 부스러기 + 발밑이 무너졌으면 떨어짐 */
  private erode(time: number): void {
    if (this.ended) return;
    const m = this.mask;
    const el = this.elapsedAt(time);
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
    if (!this.knock && !this.god && this.standScore(this.pos.x, this.pos.y, el) < 0) this.fall(time);
  }

  /** 디버그: 즉시 종료 (덮어쓸 집계가 있으면 합친다) */
  forceEnd(override: Partial<DodgeSample> = {}): void {
    if (this.ended) return;
    const now = this.scene.time.now;
    if (this.phase === 'intro') {
      this.runStartAt = now;
      this.endAt = now;
    }
    this.phase = 'run';
    Object.assign(this.sample, override, override.passes ? { passes: { ...override.passes } } : {});
    const fell = Boolean(override.falls && override.falls > 0);
    if (fell && DODGE_TRIAL.FALL_MODE === 'end') this.sinkPlayer();
    this.finish(now, fell, override.survivedMs);
  }

  snapshot(): Record<string, unknown> {
    const d = Phaser.Math.Distance.Between(this.pos.x, this.pos.y, this.cx, this.cy);
    const el = this.elapsedAt(this.scene.time.now);
    const m = this.mask;
    let alive = 0;
    let warn = 0;
    for (const i of m.order) {
      if (m.erodeAt[i] <= el) continue;
      alive += 1;
      if (m.erodeAt[i] - DODGE_TRIAL.EROSION.WARN_MS <= el) warn += 1;
    }
    return {
      phase: this.phase,
      timeLeftMs: Math.round(this.timeLeftMs),
      player: { x: +this.pos.x.toFixed(1), y: +this.pos.y.toFixed(1), fromCenter: +d.toFixed(1), facing: this.facing },
      animated: this.animated,
      anim: this.player.anims.currentAnim?.key ?? null,
      dashing: this.scene.time.now < this.dashUntil,
      invuln: this.scene.time.now < this.invulnUntil,
      knock: Boolean(this.knock),
      bullets: this.bullets.filter((b) => b.alive).length,
      telegraphs: this.telegraph.count,
      waves: this.waves,
      fired: this.fired,
      patterns: { ...this.patternCount },
      sample: JSON.parse(JSON.stringify(this.sample)),
      elapsedMs: Math.round(el),
      onFloor: this.standScore(this.pos.x, this.pos.y, el) >= 0,
      god: this.god,
      arena: {
        shape: m.shape,
        cx: this.cx,
        cy: this.cy,
        cells: m.cells,
        alive,
        aliveFrac: +(alive / Math.max(1, m.cells)).toFixed(3),
        warn,
        bounds: { ...m.bounds },
        spawn: { ...this.spawn },
      },
    };
  }

  destroy(): void {
    this.pending.length = 0;
    this.telegraph.destroy();
    this.fx.destroy();
    for (const b of this.bullets) b.spr.destroy();
    this.bullets.length = 0;
    this.player.destroy();
    this.shadow.destroy();
    this.chips.destroy();
    this.arenaG.destroy();
    this.timerG.destroy();
  }

  // --- 플레이어 ---

  private movePlayer(time: number, dt: number, input: TrialInput): void {
    const D = PLAYER_DATA.dash;
    const dir = new Phaser.Math.Vector2(input.mx, input.my);
    if (dir.lengthSq() > 0) {
      dir.normalize();
      this.lastDir.copy(dir);
      this.facing = facingOf(dir.x, dir.y, this.facing);
    }
    const before = this.pos.clone();
    const el = this.elapsedAt(time);
    if (this.knock) {
      const k = this.knock;
      const p = Math.min(1, (time - k.startAt) / Math.max(1, k.until - k.startAt));
      const f = 1 - p; // 감속
      this.pos.x += k.vx * f * dt;
      this.pos.y += k.vy * f * dt;
      if (time >= k.until) this.knock = null;
      if (!this.god && this.standScore(this.pos.x, this.pos.y, el) < 0) {
        this.fall(time);
        return;
      }
      if (this.god && this.standScore(this.pos.x, this.pos.y, el) < 0) this.pos.copy(before);
      return;
    }
    if (input.dash && time >= this.dashReadyAt && !this.ended) {
      this.dashDir.copy(dir.lengthSq() > 0 ? dir : this.lastDir);
      this.dashUntil = time + D.durationMs;
      this.dashReadyAt = time + D.cooldownMs;
      this.lastDashAt = time;
      if (D.invulnerable) this.invulnUntil = Math.max(this.invulnUntil, this.dashUntil);
      if (this.phase === 'run') this.sample.dashes += 1;
      audio.playSfx(SFX.dash);
      this.spawnGhosts();
    }
    let vx: number;
    let vy: number;
    if (time < this.dashUntil) {
      const v = (D.distanceTiles * TILE) / (D.durationMs / 1000);
      vx = this.dashDir.x * v * dt;
      vy = this.dashDir.y * v * dt;
    } else {
      const v = PLAYER_DATA.stats.speedTiles * TILE;
      vx = dir.x * v * dt;
      vy = dir.y * v * dt;
    }
    // 걸어서·대쉬로는 바닥 밖으로 못 나간다: 가장자리 여유(둘레 4점)가 지금보다 나빠지지 않는 쪽으로만 (축별로 미끄러짐)
    if (vx !== 0 || vy !== 0) {
      const cur = Math.max(0, this.standScore(this.pos.x, this.pos.y, el));
      const ok = (x: number, y: number) => {
        const s = this.standScore(x, y, el);
        return s >= 4 || (s >= 0 && s >= cur);
      };
      const { x, y } = this.pos;
      if (ok(x + vx, y + vy)) this.pos.set(x + vx, y + vy);
      else if (vx !== 0 && ok(x + vx, y)) this.pos.set(x + vx, y);
      else if (vy !== 0 && ok(x, y + vy)) this.pos.set(x, y + vy);
    }
    if (this.phase === 'run') this.sample.travelPx += Phaser.Math.Distance.BetweenPoints(before, this.pos);
  }

  private hit(time: number, b: Bullet): void {
    const P = DODGE_TRIAL.PLAYER;
    if (this.god) return this.killBullet(b, false);
    this.sample.hits += 1;
    this.killBullet(b, false);
    const len = Math.hypot(b.vx, b.vy) || 1;
    const dist = P.KNOCK_TILES * TILE;
    // 감속 이동 거리 = v0 × T / 2 → v0 = 2D / T
    const v0 = (2 * dist) / (P.KNOCK_MS / 1000);
    this.knock = { vx: (b.vx / len) * v0, vy: (b.vy / len) * v0, startAt: time, until: time + P.KNOCK_MS };
    this.dashUntil = 0;
    this.invulnUntil = time + P.INVULN_MS;
    this.hurtUntil = time + P.KNOCK_MS + 120;
    this.flashUntil = time + P.FLASH_MS;
    this.facing = facingOf(-b.vx, -b.vy, this.facing);
    const hurt = spriteLibrary.animKey('player', 'hurt', this.facing);
    if (hurt) this.player.play(hurt);
    this.fx.play(FEEL.FX_IDS.PLAYER_HIT, this.pos.x, this.pos.y, {
      depth: entityDepth(this.pos.y) + DEPTH.OVERLAY_STEP * 3,
    });
    this.scene.cameras.main.shake(P.SHAKE_MS, P.SHAKE_INTENSITY);
    audio.playSfx(SFX.hitPlayer);
  }

  private fall(time: number): void {
    if (this.ended) return;
    this.knock = null;
    this.sample.falls += 1;
    if (DODGE_TRIAL.FALL_MODE === 'return') {
      this.pos.set(this.cx, this.cy);
      this.invulnUntil = time + DODGE_TRIAL.FALL_RETURN_INVULN_MS;
      this.syncPlayer(time);
      return;
    }
    this.sinkPlayer();
    this.finish(time, true);
  }

  /** 떨어짐: 바닥 아래 어둠으로 가라앉는다 (바닥 뒤로 그려 가장자리 너머로 떨어지는 느낌) + 발밑 부스러기 */
  private sinkPlayer(): void {
    const P = DODGE_TRIAL.PLAYER;
    this.chips.emitParticleAt(this.pos.x, this.pos.y + P.FOOT_OFFSET_PX, FLOOR_LOOK.FALL_CHIPS);
    this.player.setDepth(DEPTH.TILES + 0.07);
    this.shadow.setVisible(false);
    this.scene.tweens.add({
      targets: this.player,
      alpha: 0,
      scaleX: 0.5,
      scaleY: 0.5,
      y: `+=${P.FALL_DROP_PX}`,
      duration: P.FALL_MS,
      ease: 'Quad.easeIn',
    });
  }

  /** 운명 문구를 위해 경기장 전체를 흐리게 */
  dim(): void {
    this.scene.tweens.add({
      // 떨어진 주인공은 이미 사라졌다 — 다시 비치지 않게 뺀다
      targets:
        this.sample.falls > 0
          ? [this.arenaG, this.timerG, this.chips]
          : [this.arenaG, this.timerG, this.player, this.shadow, this.chips],
      alpha: DODGE_TRIAL.DIM_ALPHA,
      duration: DODGE_TRIAL.DIM_MS,
    });
  }

  private spawnGhosts(): void {
    const P = DODGE_TRIAL.PLAYER;
    const D = PLAYER_DATA.dash;
    for (let i = 1; i <= P.GHOSTS; i++) {
      const t = i / (P.GHOSTS + 1);
      this.scene.time.delayedCall(D.durationMs * t, () => {
        if (!this.player.active) return;
        const g = this.scene.add
          .image(this.player.x, this.player.y, this.player.texture.key, this.player.frame.name)
          .setOrigin(this.player.originX, this.player.originY)
          .setAlpha(P.GHOST_ALPHA)
          .setTint(this.ramp[8] ?? 0xffffff)
          .setDepth(this.player.depth - DEPTH.OVERLAY_STEP);
        this.scene.tweens.add({ targets: g, alpha: 0, duration: P.GHOST_MS, onComplete: () => g.destroy() });
      });
    }
  }

  private syncPlayer(time: number): void {
    const P = DODGE_TRIAL.PLAYER;
    if (this.ended && this.sample.falls > 0 && DODGE_TRIAL.FALL_MODE === 'end') return;
    const footY = this.pos.y + P.FOOT_OFFSET_PX;
    this.player.setPosition(Math.round(this.pos.x), Math.round(footY)).setDepth(entityDepth(footY));
    this.shadow.setPosition(Math.round(this.pos.x), Math.round(footY));
    // 깜빡임(무적) · 흰 칠(피격 순간)
    const blinking = time < this.invulnUntil && time >= this.dashUntil;
    this.player.setAlpha(blinking && Math.floor(time / P.BLINK_MS) % 2 === 0 ? 0.35 : 1);
    if (time < this.flashUntil) this.player.setTintFill(0xffffff);
    else if (this.animated) this.player.clearTint();
    else this.player.setTint(this.ramp[6] ?? 0xffffff);
    if (!this.animated || time < this.hurtUntil) return;
    const action = time < this.dashUntil ? 'dash' : this.phase !== 'done' && this.movingInput ? 'walk' : 'idle';
    const key =
      spriteLibrary.animKey('player', action, this.facing) ?? spriteLibrary.animKey('player', 'idle', this.facing);
    if (key && this.player.anims.currentAnim?.key !== key) this.player.play(key, true);
  }

  // --- 투사체 ---

  private spawnWaves(time: number): void {
    if (this.ended || time < this.nextWaveAt) return;
    const elapsed = time - this.runStartAt;
    const step = trialStep(elapsed);
    if (time + step.telegraphMs >= this.endAt) return;
    for (let v = 0; v < step.volleys; v++) this.launch(pickPattern(step.patterns, this.rnd()), step, time);
    this.waves += 1;
    this.nextWaveAt = time + step.intervalMs;
  }

  private launch(kind: PatternKind, step: TrialStep, time: number): void {
    this.patternCount[kind] += 1;
    const speed = step.speedTiles * TILE;
    const tele = step.telegraphMs;
    const theta = this.rnd() * Math.PI * 2;
    const ex = this.cx + Math.cos(theta) * this.spawn.rx;
    const ey = this.cy + Math.sin(theta) * this.spawn.ry;
    const aimAt = (x: number, y: number) => Math.atan2(this.pos.y - y, this.pos.x - x);
    switch (kind) {
      case 'aimed': {
        const a = aimAt(ex, ey);
        const len = Phaser.Math.Distance.Between(ex, ey, this.pos.x, this.pos.y) + TILE * 2;
        this.telegraph.line(ex, ey, a, len, tele, { aura: true });
        this.schedule(time + tele, () => this.fire(ex, ey, a, speed, ENEMY_FX.BULLET, SHOT_SFX_ENEMY));
        break;
      }
      case 'fan': {
        const a = aimAt(ex, ey);
        const spread = Phaser.Math.DegToRad(step.fanSpreadDeg);
        this.telegraph.cone(ex, ey, a, spread / 2, Math.max(this.outer.rx, this.outer.ry) * 1.2, tele, { aura: true });
        this.schedule(time + tele, () => {
          const n = step.fanCount;
          for (let i = 0; i < n; i++) {
            const t = n === 1 ? 0.5 : i / (n - 1);
            this.fire(ex, ey, a - spread / 2 + spread * t, speed, ENEMY_FX.FAN_SHOT, null);
          }
          audio.playSfx(SFX.bossFan);
        });
        break;
      }
      case 'cross': {
        // 서로 수직인 두 지점에서 플레이어 자리를 가로지르는 연발
        for (const off of [0, (Math.PI / 2) * (this.rnd() < 0.5 ? 1 : -1)]) {
          const th = theta + off;
          const x = this.cx + Math.cos(th) * this.spawn.rx;
          const y = this.cy + Math.sin(th) * this.spawn.ry;
          const a = aimAt(x, y);
          const len = Phaser.Math.Distance.Between(x, y, this.pos.x, this.pos.y) + TILE * 3;
          this.telegraph.line(x, y, a, len, tele, { aura: true });
          for (let i = 0; i < step.crossStream; i++) {
            this.schedule(time + tele + i * DODGE_TRIAL.CURVE.CROSS_GAP_MS, () =>
              this.fire(x, y, a, speed, ENEMY_FX.BULLET, i === 0 ? SHOT_SFX_ENEMY : null),
            );
          }
        }
        break;
      }
      case 'ring': {
        // 원형 확산: 경기장 밖 한 점에서 사방으로 — 경기장 쪽 반원만 쏜다
        this.telegraph.circle(ex, ey, TILE * 1.5, tele, { aura: true });
        const n = step.ringCount;
        const keep = ringIndices(n, step.ringGaps, DODGE_TRIAL.CURVE.RING_GAP_WIDTH, Math.floor(this.rnd() * n));
        const inward = Math.atan2(this.cy - ey, this.cx - ex);
        const rot = this.rnd() * ((Math.PI * 2) / n);
        this.schedule(time + tele, () => {
          for (const i of keep) {
            const a = rot + (i / n) * Math.PI * 2;
            if (Math.cos(a - inward) <= 0) continue;
            this.fire(ex, ey, a, speed * DODGE_TRIAL.CURVE.RING_SPEED_MULT, ENEMY_FX.FAN_SHOT, null);
          }
          audio.playSfx(SFX.bossFan);
        });
        break;
      }
    }
  }

  private schedule(at: number, fire: () => void): void {
    this.pending.push({ at, fire });
  }

  private firePending(time: number): void {
    if (this.pending.length === 0) return;
    const due = this.pending.filter((p) => p.at <= time);
    if (due.length === 0) return;
    for (let i = this.pending.length - 1; i >= 0; i--) if (this.pending[i].at <= time) this.pending.splice(i, 1);
    for (const p of due) p.fire();
  }

  private fire(x: number, y: number, angle: number, speed: number, sheetId: string, sfxEnemy: string | null): void {
    if (this.ended) return;
    const b = this.acquire();
    if (!b) return;
    const B = DODGE_TRIAL.BULLET;
    b.x = x;
    b.y = y;
    b.vx = Math.cos(angle) * speed;
    b.vy = Math.sin(angle) * speed;
    b.r = sheetId === ENEMY_FX.FAN_SHOT ? B.FAN_RADIUS_PX : B.RADIUS_PX;
    b.born = this.scene.time.now;
    b.alive = true;
    b.minGap = Infinity;
    b.minAt = b.born;
    b.lastGap = Infinity;
    const def = spriteLibrary.sheet(sheetId, FX_ACTION);
    const tex = spriteLibrary.textureKey(sheetId, FX_ACTION);
    const s = b.spr;
    s.anims.stop();
    if (def && tex && this.scene.textures.exists(tex)) {
      s.setTexture(tex, 0)
        .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
        .clearTint();
      s.setRotation(def.rotate ? angle : 0);
      const anim = def.loop && def.frames > 1 ? spriteLibrary.animKey(sheetId, FX_ACTION, 'down') : null;
      if (anim) s.play(anim, true);
    } else {
      s.setTexture(TEX_BULLET_PH).setOrigin(0.5, 0.5).setRotation(0).setTint(B.PLACEHOLDER_COLOR);
    }
    s.setPosition(x, y).setActive(true).setVisible(true).setAlpha(1);
    this.fired += 1;
    if (sfxEnemy) audio.playSfx(SFX.enemyShot(sfxEnemy));
  }

  private acquire(): Bullet | null {
    const free = this.bullets.find((b) => !b.alive);
    if (free) return free;
    if (this.bullets.length >= DODGE_TRIAL.BULLET.POOL) return null;
    const spr = this.scene.add.sprite(0, 0, TEX_BULLET_PH).setDepth(DEPTH.PROJECTILE).setVisible(false);
    const b: Bullet = { spr, x: 0, y: 0, vx: 0, vy: 0, r: 0, born: 0, alive: false, minGap: 0, minAt: 0, lastGap: 0 };
    this.bullets.push(b);
    return b;
  }

  private updateBullets(time: number, dt: number): void {
    const P = DODGE_TRIAL.PLAYER;
    const B = DODGE_TRIAL.BULLET;
    const orx = this.spawn.rx + TILE * 2;
    const ory = this.spawn.ry + TILE * 2;
    const vulnerable = this.phase === 'run' && !this.ended && time >= this.invulnUntil && !this.knock;
    for (const b of this.bullets) {
      if (!b.alive) continue;
      b.x += b.vx * dt;
      b.y += b.vy * dt;
      b.spr.setPosition(b.x, b.y);
      if (this.ended) {
        if (time - b.born > B.LIFE_MS) this.killBullet(b, false);
        continue;
      }
      const gap = Phaser.Math.Distance.Between(b.x, b.y, this.pos.x, this.pos.y) - (P.HIT_RADIUS_PX + b.r);
      if (gap < b.minGap) {
        b.minGap = gap;
        b.minAt = time;
      }
      b.lastGap = gap;
      if (gap <= 0 && vulnerable) {
        this.hit(time, b);
        continue;
      }
      const out = Math.hypot((b.x - this.cx) / orx, (b.y - this.cy) / ory) > 1;
      const outward = (b.x - this.cx) * b.vx + (b.y - this.cy) * b.vy > 0;
      if (time - b.born > B.LIFE_MS || (out && outward)) this.killBullet(b, true);
    }
  }

  /** 투사체 제거. passed = 맞지 않고 지나감 → 최근접 틈으로 회피 분류 */
  private killBullet(b: Bullet, passed: boolean): void {
    if (passed && !this.ended) this.recordPass(b);
    b.alive = false;
    b.spr.anims.stop();
    b.spr.setActive(false).setVisible(false);
  }

  private recordPass(b: Bullet): void {
    const cls = classifyGap(b.minGap);
    if (!cls) return;
    this.sample.passes[cls] += 1;
    this.sample.gapSumPx += Math.max(0, b.minGap);
    if (isDashDodge(b.minGap, b.minAt, this.lastDashAt)) this.sample.dashDodges += 1;
  }

  /** 끝: 이미 최근접을 지난 투사체는 회피로 세고, 나머지는 버린다. 예고·대기 발사 취소 */
  private finish(time: number, fell: boolean, survivedOverride?: number): void {
    if (this.ended) return;
    for (const b of this.bullets) {
      if (!b.alive) continue;
      if (!fell && b.lastGap > b.minGap + 1) this.recordPass(b);
    }
    this.frozenElapsed = this.elapsedAt(time);
    this.ended = true;
    this.phase = 'done';
    this.pending.length = 0;
    this.telegraph.destroy();
    this.sample.survivedMs = survivedOverride ?? Math.min(DODGE_TRIAL.DURATION_MS, Math.max(0, time - this.runStartAt));
    for (const b of this.bullets) {
      if (!b.alive) continue;
      this.scene.tweens.add({ targets: b.spr, alpha: 0, duration: DODGE_TRIAL.BULLET.END_FADE_MS });
    }
    this.onDone(this.sample);
  }

  // --- 경기장 ---

  /**
   * 바닥: 칸 격자를 행 단위로 이어 칠한다. 아래가 빈 칸 밑에는 절벽 면, 빈 쪽 가장자리에 층 램프 테두리,
   * 무너지기 직전(WARN_MS) 칸은 어두워지며 검은 금·잔불이 번지고 끝에 떨린다.
   */
  private drawArena(time: number): void {
    const g = this.arenaG;
    const m = this.mask;
    const el = this.elapsedAt(time);
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

  /** 남은 시간: 바닥 외곽 타원을 따라 줄어드는 호. 마지막 구간은 층 강조색으로 맥동 */
  private drawTimer(time: number): void {
    const g = this.timerG;
    g.clear();
    const left = this.timeLeftMs / DODGE_TRIAL.DURATION_MS;
    if (left <= 0) return;
    const final = this.phase === 'run' && this.timeLeftMs <= DODGE_TRIAL.FINAL_MS;
    const pulse = final ? 0.6 + 0.4 * Math.sin(time / 60) : 1;
    g.lineStyle(2, final ? (this.ramp[10] ?? 0xffffff) : (this.ramp[8] ?? 0xe8b858), 0.9 * pulse);
    const rx = this.outer.rx + 6;
    const ry = this.outer.ry + 6;
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

  private ensureTextures(): void {
    const tex = this.scene.textures;
    if (!tex.exists(TEX_PLAYER_PH)) {
      const g = this.scene.make.graphics({ x: 0, y: 0 }, false);
      g.fillStyle(0xffffff, 1);
      g.fillRect(0, 0, 10, 14);
      g.generateTexture(TEX_PLAYER_PH, 10, 14);
      g.destroy();
    }
    if (!tex.exists(TEX_CHIP)) {
      const g = this.scene.make.graphics({ x: 0, y: 0 }, false);
      g.fillStyle(0xffffff, 1);
      g.fillRect(0, 0, 2, 2);
      g.generateTexture(TEX_CHIP, 2, 2);
      g.destroy();
    }
    if (!tex.exists(TEX_BULLET_PH)) {
      const d = DODGE_TRIAL.BULLET.PLACEHOLDER_PX;
      const g = this.scene.make.graphics({ x: 0, y: 0 }, false);
      g.fillStyle(0xffffff, 1);
      g.fillCircle(d / 2, d / 2, d / 2);
      g.generateTexture(TEX_BULLET_PH, d, d);
      g.destroy();
    }
  }
}
