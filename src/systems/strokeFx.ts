/**
 * 개성 선택 획 연출 — "화면이 찢기며 빛이 새어 나옴" (48라운드 Q8).
 * 도영 님 원문: "개성 발현 연출도 내가 긋는 획이 더 빛나고 화면을 긁어내는 듯한 리얼한 연출".
 *
 * 레이어 (아래 → 위):
 * 1. 표면: 절차 생성한 어두운 결 텍스처 (긁히는 바탕)
 * 2. 자국 RenderTexture: 지나간 자리마다 즉시 찢긴 틈(검정) + 들뜬 가장자리 + 식은 잔불 선을 굽는다 → 필기처럼 남는다
 * 3. 빛 Graphics (ADD): 최근 조각만 매 프레임 다시 그린다. 백열 코어(fx.core X0/X1) → 층 강조(27/26/25) 순으로 식는다
 * 4. 불티 파티클 (ADD) + 펜 끝 빛 번짐, 빠르게 그을 때 미세 흔들림
 * 속도가 빠를수록 틈이 넓고 밝다. 획을 떼면 그 획 전체가 한 번 더 번쩍(FLARE)하고 COOL_MS 동안 식는다.
 * 판정(strokeFeatures)과 무관한 표시 전용.
 */
import Phaser from 'phaser';
import { GAME } from '../core/Constants';
import { PALETTE } from '../data';
import { fxCoreColor, hexToInt, hexToRgb, rampFor } from './palette';
import { STROKE_FX, gapIntensity, gapWidth, heatAt, jaggedPoints, offsetPoints } from './strokeFxMath';

interface HotSeg {
  pts: number[];
  width: number;
  intensity: number;
  born: number;
  stroke: number;
}

export interface StrokeFxSummary {
  hot: number;
  scarSegments: number;
  sparksAlive: number;
  strokes: number;
  drawing: boolean;
  lastWidth: number;
  lastSpeed: number;
  shakes: number;
}

export class StrokeFx {
  private readonly surface: Phaser.GameObjects.Image;
  private readonly scar: Phaser.GameObjects.RenderTexture;
  private readonly scarG: Phaser.GameObjects.Graphics;
  private readonly hotG: Phaser.GameObjects.Graphics;
  private readonly sparks: Phaser.GameObjects.Particles.ParticleEmitter;
  private readonly tip: Phaser.GameObjects.Image;
  private readonly ramp: number[];
  private readonly x0: number;
  private readonly x1: number;
  private readonly gray: number[];
  private hot: HotSeg[] = [];
  private flareAt = new Map<number, number>();
  private scarDirty = false;
  private scarSegments = 0;
  private strokeIndex = 0;
  private drawing = false;
  private last = { x: 0, y: 0, t: 0 };
  private speed = 0;
  private lastWidth = 0;
  private lastShakeAt = -Infinity;
  private shakes = 0;
  private fading = false;

  constructor(
    private readonly scene: Phaser.Scene,
    floor: number = STROKE_FX.FLOOR,
    private readonly rnd: () => number = Math.random,
  ) {
    const C = STROKE_FX;
    this.gray = PALETTE.gray.map(hexToInt);
    this.ramp = (rampFor(PALETTE, floor) ?? rampFor(PALETTE, 1) ?? []).map(hexToInt);
    this.x0 = hexToInt(fxCoreColor(PALETTE, 0) ?? '#ffffff');
    this.x1 = hexToInt(fxCoreColor(PALETTE, 1) ?? '#fff4dc');
    this.ensureTextures();
    this.surface = scene.add.image(0, 0, C.SURFACE.KEY).setOrigin(0, 0).setDepth(C.DEPTH_SURFACE);
    this.scar = scene.add.renderTexture(0, 0, GAME.WIDTH, GAME.HEIGHT).setOrigin(0, 0).setDepth(C.DEPTH_SCAR);
    this.scarG = scene.make.graphics({ x: 0, y: 0 }, false);
    this.hotG = scene.add.graphics().setDepth(C.DEPTH_HOT).setBlendMode(Phaser.BlendModes.ADD);
    const S = C.SPARKS;
    this.sparks = scene.add.particles(0, 0, S.KEY, {
      emitting: false,
      speed: { min: S.SPEED[0], max: S.SPEED[1] },
      lifespan: { min: S.LIFE_MS[0], max: S.LIFE_MS[1] },
      gravityY: S.GRAVITY,
      scale: { start: 1, end: 0.2 },
      alpha: { start: 1, end: 0 },
      tint: [this.x0, this.x1, ...S.RAMP_TINTS.map((i) => this.rampColor(i))],
      blendMode: Phaser.BlendModes.ADD,
    });
    this.sparks.setDepth(C.DEPTH_SPARK);
    this.tip = scene.add
      .image(0, 0, C.TIP.KEY)
      .setBlendMode(Phaser.BlendModes.ADD)
      .setDepth(C.DEPTH_SPARK)
      .setTint(this.rampColor(10))
      .setVisible(false);
  }

  /** 획 시작 */
  begin(x: number, y: number, t: number): void {
    if (this.fading) return;
    this.drawing = true;
    this.strokeIndex += 1;
    this.last = { x, y, t };
    this.speed = 0;
    this.tip
      .setPosition(x, y)
      .setVisible(true)
      .setAlpha(STROKE_FX.TIP.ALPHA * STROKE_FX.INTENSITY.MIN);
    // 누른 자리에 작은 불티 한 줌 (긁기 시작)
    this.sparks.setEmitterAngle({ min: 0, max: 360 });
    this.sparks.emitParticleAt(x, y, Math.ceil(STROKE_FX.SPARKS.MAX_PER_MOVE / 2));
  }

  /** 획 진행: 지나간 조각을 찢고 빛을 넣는다 */
  move(x: number, y: number, t: number): void {
    if (!this.drawing || this.fading) return;
    const C = STROKE_FX;
    const dist = Math.hypot(x - this.last.x, y - this.last.y);
    if (dist < 1) return;
    const dt = Math.max(C.MIN_DT_MS, t - this.last.t);
    const inst = (dist / dt) * 1000;
    this.speed = this.speed === 0 ? inst : this.speed + (inst - this.speed) * C.SPEED_SMOOTH;
    const w = gapWidth(this.speed);
    const I = gapIntensity(this.speed);
    this.lastWidth = w;
    const pts = jaggedPoints(this.last.x, this.last.y, x, y, w, this.rnd);
    this.bakeScar(pts, w);
    this.hot.push({ pts, width: w, intensity: I, born: this.scene.time.now, stroke: this.strokeIndex });
    if (this.hot.length > C.HOT_MAX) this.hot.splice(0, this.hot.length - C.HOT_MAX);
    this.emitSparks(this.last.x, this.last.y, x, y, dist, I);
    this.shake(this.speed);
    const r = (w - C.WIDTH.MIN_PX) / (C.WIDTH.MAX_PX - C.WIDTH.MIN_PX);
    this.tip
      .setPosition(x, y)
      .setAlpha(C.TIP.ALPHA * I)
      .setScale(C.TIP.SCALE_MIN + (C.TIP.SCALE_MAX - C.TIP.SCALE_MIN) * r);
    this.last = { x, y, t };
  }

  /** 획 끝: 그 획 전체가 한 번 번쩍이고 식기 시작한다 */
  end(x: number, y: number, t: number): void {
    if (!this.drawing) return;
    this.move(x, y, t);
    this.drawing = false;
    this.flareAt.set(this.strokeIndex, this.scene.time.now);
    this.tip.setVisible(false);
  }

  update(time: number): void {
    if (this.scarDirty) {
      this.scar.draw(this.scarG);
      this.scarG.clear();
      this.scarDirty = false;
    }
    const g = this.hotG;
    g.clear();
    if (this.hot.length === 0) return;
    const C = STROKE_FX;
    let keep = 0;
    for (const s of this.hot) {
      const fa = this.flareAt.get(s.stroke);
      const heat = heatAt(time - s.born, fa === undefined ? null : time - fa) * s.intensity;
      if (heat <= 0) continue;
      this.hot[keep++] = s;
      for (const L of C.HOT_LAYERS) {
        const a = L.alpha * Math.pow(Math.min(1, heat), L.pow) * (heat > 1 ? heat : 1);
        if (a < 0.01) continue;
        const color = L.color === 'x0' ? this.x0 : L.color === 'x1' ? this.x1 : this.rampColor(L.color);
        g.lineStyle(Math.max(1, s.width * L.width), color, Math.min(1, a));
        this.strokePts(g, s.pts);
      }
    }
    this.hot.length = keep;
  }

  /** 획 단계를 떠날 때: 전부 서서히 사라지고 파괴 */
  fadeOut(onDone?: () => void): void {
    if (this.fading) return;
    this.fading = true;
    this.drawing = false;
    this.tip.setVisible(false);
    this.scene.tweens.add({
      targets: [this.surface, this.scar, this.hotG],
      alpha: 0,
      duration: STROKE_FX.FADE_OUT_MS,
      onComplete: () => {
        this.destroy();
        onDone?.();
      },
    });
  }

  summary(): StrokeFxSummary {
    return {
      hot: this.hot.length,
      scarSegments: this.scarSegments,
      sparksAlive: this.sparks.active ? this.sparks.getAliveParticleCount() : 0,
      strokes: this.strokeIndex,
      drawing: this.drawing,
      lastWidth: +this.lastWidth.toFixed(2),
      lastSpeed: Math.round(this.speed),
      shakes: this.shakes,
    };
  }

  destroy(): void {
    this.hot = [];
    this.surface.destroy();
    this.scar.destroy();
    this.scarG.destroy();
    this.hotG.destroy();
    this.sparks.destroy();
    this.tip.destroy();
  }

  // --- 내부 ---

  /** 자국: 틈(검정, 끝 둥글게) → 들뜬 가장자리 2줄 → 식은 잔불 → 가는 심 */
  private bakeScar(pts: number[], w: number): void {
    const S = STROKE_FX.SCAR;
    const g = this.scarG;
    const gapW = w + S.GAP_EXTRA_PX;
    g.lineStyle(gapW, S.GAP_COLOR, S.GAP_ALPHA);
    this.strokePts(g, pts);
    g.fillStyle(S.GAP_COLOR, S.GAP_ALPHA);
    // 꺾임·끝점만 둥글게 (시작점은 앞 조각의 끝점이 이미 덮었다 — 다시 덮으면 앞 조각 잔불이 끊겨 보인다)
    for (let i = 2; i < pts.length; i += 2) g.fillCircle(pts[i], pts[i + 1], gapW / 2);
    const off = gapW / 2 + S.LIP_OFFSET_PX;
    for (const sign of [1, -1]) {
      const lip = offsetPoints(pts, off * sign);
      g.lineStyle(1, this.gray[S.LIP_GRAY] ?? 0x5c5e62, S.LIP_ALPHA);
      this.strokePts(g, lip);
      const inner = offsetPoints(pts, (off - 1) * sign);
      g.lineStyle(1, this.rampColor(S.LIP_HOT_RAMP), S.LIP_HOT_ALPHA);
      this.strokePts(g, inner);
      // 들뜬 조각
      g.fillStyle(this.gray[S.LIP_GRAY] ?? 0x5c5e62, S.LIP_ALPHA);
      for (let i = 2; i < lip.length - 2; i += 2) {
        if (this.rnd() < S.CHIP_CHANCE) g.fillRect(Math.round(lip[i]), Math.round(lip[i + 1]), S.CHIP_PX, S.CHIP_PX);
      }
    }
    g.lineStyle(Math.max(1, w * S.EMBER_WIDTH), this.rampColor(S.EMBER_RAMP), S.EMBER_ALPHA);
    this.strokePts(g, pts);
    g.lineStyle(1, this.rampColor(S.CORE_RAMP), S.CORE_ALPHA);
    this.strokePts(g, pts);
    this.scarDirty = true;
    this.scarSegments += 1;
  }

  private emitSparks(ax: number, ay: number, bx: number, by: number, dist: number, I: number): void {
    const S = STROKE_FX.SPARKS;
    const n = Math.min(S.MAX_PER_MOVE, Math.ceil(dist * S.PER_PX * I));
    if (n <= 0) return;
    const back = Phaser.Math.RadToDeg(Math.atan2(ay - by, ax - bx));
    this.sparks.setEmitterAngle({ min: back - S.SPREAD_DEG, max: back + S.SPREAD_DEG });
    this.sparks.emitParticleAt(bx, by, n);
  }

  private shake(speed: number): void {
    const K = STROKE_FX.SHAKE;
    const now = this.scene.time.now;
    if (speed < K.MIN_SPEED || now - this.lastShakeAt < K.THROTTLE_MS) return;
    this.lastShakeAt = now;
    const r = Math.min(1, (speed - K.MIN_SPEED) / (STROKE_FX.WIDTH.SPEED_REF - K.MIN_SPEED));
    this.scene.cameras.main.shake(K.MS, K.INTENSITY[0] + (K.INTENSITY[1] - K.INTENSITY[0]) * r);
    this.shakes += 1;
  }

  private strokePts(g: Phaser.GameObjects.Graphics, pts: number[]): void {
    g.beginPath();
    g.moveTo(pts[0], pts[1]);
    for (let i = 2; i < pts.length; i += 2) g.lineTo(pts[i], pts[i + 1]);
    g.strokePath();
  }

  private rampColor(i: number): number {
    return this.ramp[i] ?? this.x1;
  }

  /** 표면(결)·불티·펜 끝 텍스처: 한 번 만들어 재사용 */
  private ensureTextures(): void {
    const C = STROKE_FX;
    const tex = this.scene.textures;
    if (!tex.exists(C.SURFACE.KEY)) {
      const S = C.SURFACE;
      const W = GAME.WIDTH;
      const H = GAME.HEIGHT;
      const canvas = tex.createCanvas(C.SURFACE.KEY, W, H)!;
      const ctx = canvas.context;
      const img = ctx.createImageData(W, H);
      const base = hexToRgb(PALETTE.gray[S.BASE_GRAY] ?? '#141516');
      const grains = S.GRAIN_GRAYS.map((i) => hexToRgb(PALETTE.gray[i] ?? '#212224'));
      const cx = W / 2;
      const cy = H / 2;
      const maxR = Math.hypot(cx, cy);
      for (let y = 0; y < H; y++) {
        for (let x = 0; x < W; x++) {
          const k = (y * W + x) * 4;
          let c = base;
          if (this.rnd() < S.GRAIN_DENSITY) c = grains[Math.floor(this.rnd() * grains.length)];
          const v = 1 - S.VIGNETTE * Math.pow(Math.hypot(x - cx, y - cy) / maxR, 2);
          img.data[k] = c[0] * v;
          img.data[k + 1] = c[1] * v;
          img.data[k + 2] = c[2] * v;
          img.data[k + 3] = 255;
        }
      }
      ctx.putImageData(img, 0, 0);
      // 가는 결 (오래 긁힌 듯한 짧은 선)
      ctx.strokeStyle = PALETTE.gray[S.FIBER_GRAY] ?? '#2f3033';
      ctx.globalAlpha = S.FIBER_ALPHA;
      ctx.lineWidth = 1;
      for (let i = 0; i < S.FIBERS; i++) {
        const x = this.rnd() * W;
        const y = this.rnd() * H;
        const a = (this.rnd() - 0.5) * 0.6;
        const len = 20 + this.rnd() * 90;
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x + Math.cos(a) * len, y + Math.sin(a) * len);
        ctx.stroke();
      }
      ctx.globalAlpha = 1;
      canvas.refresh();
    }
    if (!tex.exists(C.SPARKS.KEY)) {
      const g = this.scene.make.graphics({ x: 0, y: 0 }, false);
      g.fillStyle(0xffffff, 1);
      g.fillRect(0, 0, C.SPARKS.SIZE_PX, C.SPARKS.SIZE_PX);
      g.generateTexture(C.SPARKS.KEY, C.SPARKS.SIZE_PX, C.SPARKS.SIZE_PX);
      g.destroy();
    }
    if (!tex.exists(C.TIP.KEY)) {
      const r = C.TIP.RADIUS_PX;
      const canvas = tex.createCanvas(C.TIP.KEY, r * 2, r * 2)!;
      const ctx = canvas.context;
      const grad = ctx.createRadialGradient(r, r, 0, r, r, r);
      grad.addColorStop(0, 'rgba(255,255,255,1)');
      grad.addColorStop(0.35, 'rgba(255,255,255,0.45)');
      grad.addColorStop(1, 'rgba(255,255,255,0)');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, r * 2, r * 2);
      canvas.refresh();
    }
  }
}
