/**
 * 개성 선택 획 연출 — "화면이 찢기며 빛이 새어 나옴" (48라운드 Q8).
 * 도영 님 원문: "개성 발현 연출도 내가 긋는 획이 더 빛나고 화면을 긁어내는 듯한 리얼한 연출".
 *
 * 레이어 (아래 → 위):
 * 1. 표면: 절차 생성한 어두운 결 텍스처 (긁히는 바탕)
 * 2. 자국 RenderTexture: 지나간 자리마다 즉시 찢긴 틈(검정) + 들뜬 가장자리 + 식은 잔불 선을 굽는다 → 필기처럼 남는다
 * 3. 빛 Graphics (ADD): 최근 조각만 매 프레임 다시 그린다. 백열 코어(fx.core X0/X1) → 층 강조(27/26/25) 순으로 식는다
 * 4. 불티 파티클 (ADD) + 펜 끝 빛 번짐, 빠르게 그을 때 미세 흔들림
 * 5. 부스러기 파티클 (보통 혼합, 49라운드 1절): 긁힌 화면 조각·검은 재·잔불 조각이 튀었다가 중력으로 떨어진다
 * 속도가 빠를수록 틈이 넓고 밝다. 획을 떼면 그 획 전체가 한 번 더 번쩍(FLARE)하고 COOL_MS 동안 식는다.
 * 3획을 다 그으면 `burst()` (49라운드 1절): 살짝 흔들림 + 획 맥동 → 백열 섬광이 획을 따라 달림 → 광선이 퍼짐
 * → 화면이 하얗게 번쩍(이때 onPeak: 다음 장면 시작) → 걷힘(onDone).
 * 판정(strokeFeatures)과 무관한 표시 전용.
 */
import Phaser from 'phaser';
import { GAME } from '../core/Constants';
import { PALETTE } from '../data';
import { fxCoreColor, hexToInt, hexToRgb, rampFor } from './palette';
import {
  STROKE_FX,
  burstAt,
  burstRays,
  gapIntensity,
  gapWidth,
  heatAt,
  jaggedPoints,
  offsetPoints,
  pathPointAt,
  pathPrefix,
  type BurstRay,
} from './strokeFxMath';

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
  debrisAlive: number;
  debrisEmitted: number;
  /** 빛 터짐: null = 시작 전, 아니면 경과 ms·단계 */
  burst: { t: number; trace: number; rays: number; white: number; peaked: boolean } | null;
}

export class StrokeFx {
  private readonly surface: Phaser.GameObjects.Image;
  private readonly scar: Phaser.GameObjects.RenderTexture;
  private readonly scarG: Phaser.GameObjects.Graphics;
  private readonly hotG: Phaser.GameObjects.Graphics;
  private readonly sparks: Phaser.GameObjects.Particles.ParticleEmitter;
  private readonly tip: Phaser.GameObjects.Image;
  private readonly debris: Phaser.GameObjects.Particles.ParticleEmitter;
  private debrisEmitted = 0;
  /** 획별 원래 점 [x0,y0,x1,y1,…] (빛 터짐 경로) */
  private paths: number[][] = [];
  private burstStart: number | null = null;
  /** 디버그: 빛 터짐 시계를 이 ms 에 멈춤 (스크린샷용) */
  private burstHold: number | null = null;
  private burstG?: Phaser.GameObjects.Graphics;
  private glow?: Phaser.GameObjects.Image;
  private white?: Phaser.GameObjects.Rectangle;
  private rays: BurstRay[] = [];
  private peakFired = false;
  private onPeak?: () => void;
  private onDone?: () => void;
  private destroyed = false;
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
    const D = C.DEBRIS;
    this.debris = scene.add.particles(0, 0, D.KEY, {
      emitting: false,
      speed: { min: D.SPEED[0], max: D.SPEED[1] },
      angle: { min: D.ANGLE[0], max: D.ANGLE[1] },
      lifespan: { min: D.LIFE_MS[0], max: D.LIFE_MS[1] },
      gravityY: D.GRAVITY,
      scale: { min: D.SCALE[0], max: D.SCALE[1] },
      alpha: { start: 1, end: 0, ease: 'Quad.easeIn' },
      rotate: { min: 0, max: 360 },
      tint: [
        ...D.GRAYS.map((i) => this.gray[i] ?? 0x5c5e62),
        ...Array.from({ length: D.ASH }, () => 0x000000),
        ...D.EMBER_RAMP.map((i) => this.rampColor(i)),
      ],
    });
    this.debris.setDepth(C.DEPTH_DEBRIS);
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
    // 누른 자리에 작은 불티 한 줌 + 부스러기 (긁기 시작)
    this.sparks.setEmitterAngle({ min: 0, max: 360 });
    this.sparks.emitParticleAt(x, y, Math.ceil(STROKE_FX.SPARKS.MAX_PER_MOVE / 2));
    this.emitDebris(x, y, STROKE_FX.DEBRIS.ON_BEGIN);
    this.paths.push([x, y]);
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
    this.emitDebris(x, y, Math.min(C.DEBRIS.MAX_PER_MOVE, Math.round(dist * C.DEBRIS.PER_PX * (0.5 + I))));
    this.paths[this.paths.length - 1]?.push(x, y);
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
    // 뗄 때: 그 획을 따라 부스러기가 한 번 더 우수수
    const path = this.paths[this.paths.length - 1];
    if (path && path.length >= 4)
      for (let k = 0; k < STROKE_FX.DEBRIS.ON_END; k++) {
        const p = pathPointAt(path, this.rnd());
        this.emitDebris(p.x, p.y, 1);
      }
  }

  update(time: number): void {
    if (this.destroyed) return;
    if (this.burstStart !== null) this.updateBurst(time);
    if (this.destroyed || this.peakFired) return;
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

  /**
   * 3획을 다 그은 뒤 빛 터짐 (49라운드 1절). onPeak = 화면이 가장 하얀 순간(뒤에서 다음 장면 시작),
   * onDone = 하얀 빛이 걷히고 이 연출이 스스로 파괴된 뒤.
   */
  burst(onPeak?: () => void, onDone?: () => void): void {
    if (this.burstStart !== null || this.destroyed) return;
    const C = STROKE_FX;
    const B = C.BURST;
    this.fading = true;
    this.drawing = false;
    this.tip.setVisible(false);
    this.onPeak = onPeak;
    this.onDone = onDone;
    this.burstStart = this.scene.time.now;
    this.rays = burstRays(this.paths, this.rnd);
    this.burstG = this.scene.add.graphics().setDepth(C.DEPTH_RAYS).setBlendMode(Phaser.BlendModes.ADD);
    let sx = 0;
    let sy = 0;
    let n = 0;
    for (const p of this.paths)
      for (let i = 0; i < p.length; i += 2) {
        sx += p[i];
        sy += p[i + 1];
        n += 1;
      }
    this.glow = this.scene.add
      .image(n ? sx / n : GAME.WIDTH / 2, n ? sy / n : GAME.HEIGHT / 2, B.GLOW_KEY)
      .setBlendMode(Phaser.BlendModes.ADD)
      .setDepth(C.DEPTH_RAYS)
      .setTint(this.x1)
      .setAlpha(0);
    this.white = this.scene.add
      .rectangle(0, 0, GAME.WIDTH, GAME.HEIGHT, this.x0, 1)
      .setOrigin(0, 0)
      .setScrollFactor(0)
      .setDepth(B.DEPTH_WHITE)
      .setAlpha(0);
    this.scene.cameras.main.shake(B.CHARGE_MS, B.SHAKE_INTENSITY);
  }

  /** 디버그: 빛 터짐 시계를 ms 에 멈춘다 (null = 풀고 그 자리부터 계속). 시작 전에 걸어 둘 수도 있다 */
  holdBurst(ms: number | null): void {
    if (ms === null && this.burstHold !== null && this.burstStart !== null)
      this.burstStart = this.scene.time.now - this.burstHold;
    this.burstHold = ms;
  }

  private burstT(time: number): number {
    return this.burstHold ?? time - (this.burstStart ?? time);
  }

  /** 획 단계를 떠날 때(빛 터짐 없이, 폴백): 전부 서서히 사라지고 파괴 */
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
      debrisAlive: this.debris.active ? this.debris.getAliveParticleCount() : 0,
      debrisEmitted: this.debrisEmitted,
      burst:
        this.burstStart === null
          ? null
          : (() => {
              const t = this.burstT(this.scene.time.now);
              const st = burstAt(t);
              return {
                t: Math.round(t),
                trace: +st.trace.toFixed(2),
                rays: +st.rays.toFixed(2),
                white: +st.white.toFixed(2),
                peaked: st.peaked,
              };
            })(),
    };
  }

  destroy(): void {
    if (this.destroyed) return;
    this.destroyed = true;
    this.hot = [];
    this.surface.destroy();
    this.scar.destroy();
    this.scarG.destroy();
    this.hotG.destroy();
    this.sparks.destroy();
    this.debris.destroy();
    this.tip.destroy();
    this.burstG?.destroy();
    this.glow?.destroy();
    this.white?.destroy();
  }

  // --- 내부 ---

  private emitDebris(x: number, y: number, n: number): void {
    if (n <= 0) return;
    this.debris.emitParticleAt(x, y, n);
    this.debrisEmitted += n;
  }

  /** 빛 터짐 한 프레임 */
  private updateBurst(time: number): void {
    const C = STROKE_FX;
    const B = C.BURST;
    const t = this.burstT(time);
    const st = burstAt(t);
    const g = this.burstG!;
    g.clear();
    if (!st.peaked) {
      // 1) 모음: 획 전체가 맥동하며 달아오름 + 부스러기
      const pulse = 1 + 0.18 * Math.sin((t / B.PULSE_MS) * Math.PI * 2);
      const heat = (B.CHARGE_HEAT[0] + (B.CHARGE_HEAT[1] - B.CHARGE_HEAT[0]) * st.charge) * pulse;
      const w = (C.WIDTH.MIN_PX + C.WIDTH.MAX_PX) / 2;
      for (const p of this.paths) if (p.length >= 4) this.glowPath(g, p, heat, w);
      if (st.shaking)
        for (let k = 0; k < B.CHARGE_DEBRIS; k++) {
          const p = this.paths[Math.floor(this.rnd() * this.paths.length)];
          if (!p || p.length < 4) continue;
          const q = pathPointAt(p, this.rnd());
          this.emitDebris(q.x, q.y, 1);
        }
      // 2) 백열 섬광이 획을 따라 달린다
      if (st.trace > 0) {
        for (const p of this.paths) {
          if (p.length < 4) continue;
          const pre = pathPrefix(p, st.trace);
          this.glowPath(g, pre, B.TRACE_HEAT, C.WIDTH.MAX_PX * 1.4);
          if (st.trace < 1) {
            const hx = pre[pre.length - 2];
            const hy = pre[pre.length - 1];
            this.sparks.setEmitterAngle({ min: 0, max: 360 });
            this.sparks.emitParticleAt(hx, hy, 2);
            g.fillStyle(this.x0, 1);
            g.fillCircle(hx, hy, C.WIDTH.MAX_PX);
          }
        }
      }
      // 3) 광선
      if (st.rays > 0) this.drawRays(g, st.rays);
      if (this.glow) {
        const e = 1 - Math.pow(1 - st.rays, 3);
        this.glow.setAlpha(0.95 * e).setScale(0.2 + (B.GLOW_SCALE - 0.2) * e);
      }
    }
    this.white?.setAlpha(st.white);
    if (st.peaked && !this.peakFired) {
      // 가장 하얀 순간: 긁힌 화면을 걷어내고 다음 장면을 뒤에서 시작
      this.peakFired = true;
      for (const o of [this.surface, this.scar, this.hotG, this.sparks, this.debris, this.tip, this.glow])
        o?.setVisible(false);
      g.clear();
      this.onPeak?.();
    }
    if (st.done) {
      const done = this.onDone;
      this.destroy();
      done?.();
    }
  }

  /** 경로 전체를 HOT_LAYERS 로 (열기 heat, 폭 width) */
  private glowPath(g: Phaser.GameObjects.Graphics, pts: number[], heat: number, width: number): void {
    for (const L of STROKE_FX.HOT_LAYERS) {
      const a = L.alpha * Math.pow(Math.min(1, heat), L.pow) * (heat > 1 ? heat : 1);
      if (a < 0.01) continue;
      const color = L.color === 'x0' ? this.x0 : L.color === 'x1' ? this.x1 : this.rampColor(L.color);
      g.lineStyle(Math.max(1, width * L.width), color, Math.min(1, a));
      this.strokePts(g, pts);
    }
  }

  /** 광선: 획 위 점에서 바깥으로 넓어지는 쐐기 3겹 (바깥 층 강조 → X1 → X0 코어) */
  private drawRays(g: Phaser.GameObjects.Graphics, p: number): void {
    const layers = [
      { lf: 1, wf: 1, color: this.rampColor(10), a: 0.2 },
      { lf: 0.68, wf: 0.55, color: this.x1, a: 0.32 },
      { lf: 0.38, wf: 0.24, color: this.x0, a: 0.6 },
    ];
    for (const r of this.rays) {
      const q = Math.max(0, Math.min(1, (p - r.delay) / (1 - r.delay)));
      if (q <= 0) continue;
      const e = 1 - Math.pow(1 - q, 3);
      const fade = q < 0.6 ? 1 : 1 - ((q - 0.6) / 0.4) * 0.45;
      const ca = Math.cos(r.angle);
      const sa = Math.sin(r.angle);
      for (const L of layers) {
        const len = r.len * e * L.lf;
        const w0 = 1.5;
        const w1 = (r.width * L.wf) / 2;
        const tx = r.x + ca * len;
        const ty = r.y + sa * len;
        g.fillStyle(L.color, L.a * fade);
        g.beginPath();
        g.moveTo(r.x - sa * w0, r.y + ca * w0);
        g.lineTo(tx - sa * w1, ty + ca * w1);
        g.lineTo(tx + sa * w1, ty - ca * w1);
        g.lineTo(r.x + sa * w0, r.y - ca * w0);
        g.closePath();
        g.fillPath();
      }
    }
  }

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
    if (!tex.exists(C.DEBRIS.KEY)) {
      // 부스러기: 모서리 한 칸이 빠진 작은 조각 (재·화면 파편)
      const d = C.DEBRIS.SIZE_PX;
      const g = this.scene.make.graphics({ x: 0, y: 0 }, false);
      g.fillStyle(0xffffff, 1);
      g.fillRect(0, 0, d, d - 1);
      g.fillRect(1, d - 1, d - 1, 1);
      g.generateTexture(C.DEBRIS.KEY, d, d);
      g.destroy();
    }
    for (const [key, r] of [
      [C.TIP.KEY, C.TIP.RADIUS_PX],
      [C.BURST.GLOW_KEY, C.BURST.GLOW_RADIUS_PX],
    ] as [string, number][]) {
      if (tex.exists(key)) continue;
      const canvas = tex.createCanvas(key, r * 2, r * 2)!;
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
