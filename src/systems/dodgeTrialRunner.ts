/**
 * 15초 회피 시험의 화면 쪽 (48라운드 Q7). 수치·평가는 `dodgeTrial.ts`.
 *
 * - 화면 중앙 둥근 원(경기장) 안에서 주인공(player 시트, WASD + 스페이스 대쉬). 걸어서는 원을 못 나가고, 맞아서 밀려날 때만 떨어진다.
 * - 원 밖 고리에서 투사체(enemy_bullet · boss_fan_shot 시트, 예고 telegraph 재사용)를 조준탄·부채꼴·교차·원형 확산으로 15초간,
 *   갈수록 촘촘·빠르게, 마지막 3초는 동시 2패턴.
 * - 맞으면 피격 연출 + 투사체 진행 방향으로 밀려남. 체력 없음(피격 횟수만).
 * - 측정: 투사체별 최근접 틈 → 직전/중간/멀찍이, 대쉬 직전 회피, 피격, 이탈, 이동량, 버틴 시간.
 * 좌표는 월드 px (Setup 이 메인 카메라를 ZOOM 배로 경기장 중심에 맞춘다).
 */
import Phaser from 'phaser';
import { DEPTH, ENEMY_FX, FEEL, GAME, TILE, entityDepth } from '../core/Constants';
import { PALETTE, PLAYER_DATA } from '../data';
import { audio } from './audio';
import { SFX } from './audioMap';
import {
  DODGE_TRIAL,
  classifyGap,
  emptySample,
  isDashDodge,
  pickPattern,
  ringIndices,
  trialStep,
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
/** 사수 탄 효과음 id (enemies.json 의 원거리 적) */
const SHOT_SFX_ENEMY = 'archer';

export class DodgeTrialRunner {
  phase: TrialPhase = 'intro';
  readonly sample: DodgeSample = emptySample();
  readonly cx = GAME.WIDTH / 2;
  readonly cy = GAME.HEIGHT / 2;
  readonly radius = DODGE_TRIAL.ARENA.RADIUS_TILES * TILE;
  readonly spawnRadius = (DODGE_TRIAL.ARENA.RADIUS_TILES + DODGE_TRIAL.ARENA.SPAWN_PAD_TILES) * TILE;
  private readonly player: Phaser.GameObjects.Sprite;
  private readonly shadow: Phaser.GameObjects.Ellipse;
  private readonly animated: boolean;
  private readonly arenaG: Phaser.GameObjects.Graphics;
  private readonly timerG: Phaser.GameObjects.Graphics;
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
    private readonly rnd: () => number = Math.random,
  ) {
    this.ramp = (rampFor(PALETTE, 1) ?? []).map(hexToInt);
    this.ensureTextures();
    this.arenaG = scene.add.graphics().setDepth(DEPTH.TILES + 0.1);
    this.timerG = scene.add.graphics().setDepth(DEPTH.TILES + 0.2);
    this.drawArena();
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
      this.spawnWaves(time);
      this.firePending(time);
      this.updateBullets(time, dt);
      if (!this.ended && time >= this.endAt) this.finish(time, false);
    } else if (this.phase === 'done') this.updateBullets(time, dt);
    this.telegraph.update(time);
    this.fx.update(time);
    this.syncPlayer(time);
    this.drawTimer(time);
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
      arena: { cx: this.cx, cy: this.cy, radius: this.radius, spawnRadius: this.spawnRadius },
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
    this.arenaG.destroy();
    this.timerG.destroy();
  }

  // --- 플레이어 ---

  private movePlayer(time: number, dt: number, input: TrialInput): void {
    const A = DODGE_TRIAL.ARENA;
    const D = PLAYER_DATA.dash;
    const dir = new Phaser.Math.Vector2(input.mx, input.my);
    if (dir.lengthSq() > 0) {
      dir.normalize();
      this.lastDir.copy(dir);
      this.facing = facingOf(dir.x, dir.y, this.facing);
    }
    const before = this.pos.clone();
    if (this.knock) {
      const k = this.knock;
      const p = Math.min(1, (time - k.startAt) / Math.max(1, k.until - k.startAt));
      const f = 1 - p; // 감속
      this.pos.x += k.vx * f * dt;
      this.pos.y += k.vy * f * dt;
      if (time >= k.until) this.knock = null;
      if (this.distFromCenter() > this.radius) {
        this.fall(time);
        return;
      }
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
    if (time < this.dashUntil) {
      const v = (D.distanceTiles * TILE) / (D.durationMs / 1000);
      this.pos.x += this.dashDir.x * v * dt;
      this.pos.y += this.dashDir.y * v * dt;
    } else {
      const v = PLAYER_DATA.stats.speedTiles * TILE;
      this.pos.x += dir.x * v * dt;
      this.pos.y += dir.y * v * dt;
    }
    // 걸어서·대쉬로는 원을 못 나간다
    const lim = this.radius - A.WALK_MARGIN_PX;
    const d = this.distFromCenter();
    if (d > lim) {
      this.pos.x = this.cx + ((this.pos.x - this.cx) / d) * lim;
      this.pos.y = this.cy + ((this.pos.y - this.cy) / d) * lim;
    }
    if (this.phase === 'run') this.sample.travelPx += Phaser.Math.Distance.BetweenPoints(before, this.pos);
  }

  private distFromCenter(): number {
    return Phaser.Math.Distance.Between(this.pos.x, this.pos.y, this.cx, this.cy);
  }

  private hit(time: number, b: Bullet): void {
    const P = DODGE_TRIAL.PLAYER;
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
    this.knock = null;
    this.sample.falls += 1;
    if (DODGE_TRIAL.FALL_MODE === 'return') {
      this.pos.set(this.cx, this.cy);
      this.invulnUntil = time + DODGE_TRIAL.FALL_RETURN_INVULN_MS;
      return;
    }
    this.sinkPlayer();
    this.finish(time, true);
  }

  /** 떨어짐: 원 밖 어둠으로 가라앉는다 */
  private sinkPlayer(): void {
    this.scene.tweens.add({
      targets: [this.player, this.shadow],
      alpha: 0,
      scaleX: 0.5,
      scaleY: 0.5,
      duration: DODGE_TRIAL.PLAYER.FALL_MS,
      ease: 'Quad.easeIn',
    });
  }

  /** 운명 문구를 위해 경기장 전체를 흐리게 */
  dim(): void {
    this.scene.tweens.add({
      targets: [this.arenaG, this.timerG, this.player, this.shadow],
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
    const footY = this.pos.y + P.FOOT_OFFSET_PX;
    this.player.setPosition(Math.round(this.pos.x), Math.round(footY)).setDepth(entityDepth(footY));
    this.shadow.setPosition(Math.round(this.pos.x), Math.round(footY));
    if (this.ended && this.sample.falls > 0 && DODGE_TRIAL.FALL_MODE === 'end') return;
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
    const ex = this.cx + Math.cos(theta) * this.spawnRadius;
    const ey = this.cy + Math.sin(theta) * this.spawnRadius;
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
        this.telegraph.cone(ex, ey, a, spread / 2, this.radius * 1.2, tele, { aura: true });
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
          const x = this.cx + Math.cos(th) * this.spawnRadius;
          const y = this.cy + Math.sin(th) * this.spawnRadius;
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
        // 원형 확산: 원 밖 한 점에서 사방으로 — 원 안쪽 반원만 쏜다
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
    const outR = this.spawnRadius + TILE * 2;
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
      const fromC = Phaser.Math.Distance.Between(b.x, b.y, this.cx, this.cy);
      const outward = (b.x - this.cx) * b.vx + (b.y - this.cy) * b.vy > 0;
      if (time - b.born > B.LIFE_MS || (fromC > outR && outward)) this.killBullet(b, true);
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

  private drawArena(): void {
    const g = this.arenaG;
    const gray = PALETTE.gray.map(hexToInt);
    g.clear();
    g.fillStyle(gray[2] ?? 0x212224, 1);
    g.fillCircle(this.cx, this.cy, this.radius);
    g.lineStyle(1, gray[3] ?? 0x2f3033, 0.8);
    for (const f of [0.33, 0.66]) g.strokeCircle(this.cx, this.cy, this.radius * f);
    g.lineStyle(3, this.ramp[2] ?? 0x653b24, 0.9);
    g.strokeCircle(this.cx, this.cy, this.radius + 1);
    g.lineStyle(1, this.ramp[5] ?? 0xd67a11, 0.9);
    g.strokeCircle(this.cx, this.cy, this.radius);
  }

  /** 남은 시간: 원 테두리를 따라 줄어드는 호. 마지막 구간은 층 강조색으로 맥동 */
  private drawTimer(time: number): void {
    const g = this.timerG;
    g.clear();
    const left = this.timeLeftMs / DODGE_TRIAL.DURATION_MS;
    if (left <= 0) return;
    const final = this.phase === 'run' && this.timeLeftMs <= DODGE_TRIAL.FINAL_MS;
    const pulse = final ? 0.6 + 0.4 * Math.sin(time / 60) : 1;
    g.lineStyle(2, final ? (this.ramp[10] ?? 0xffffff) : (this.ramp[8] ?? 0xe8b858), 0.9 * pulse);
    const start = -Math.PI / 2;
    g.beginPath();
    g.arc(this.cx, this.cy, this.radius + 3, start, start + Math.PI * 2 * left, false);
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
