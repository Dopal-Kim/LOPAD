/**
 * 개성 선택 획 연출 — "화면이 찢기며 빛이 새어 나옴" (48라운드 Q8, 49라운드 1절, 51라운드 1절).
 * 도영 님 원문(51): "획이 너무 두껍고 부드럽지가 않아. 픽셀이 더 세분화되고 나눠져서 곡선에도 엄청 매끄러운 연출".
 *
 * 51라운드 구조:
 * - 곡선: 입력점 → 구심 Catmull-Rom → 1px 간격 표본(`StrokePath`, strokeFxSpline.ts). 폭은 붓처럼 느리면 굵고 빠르면 가늘다
 *   (0.9~3.2px, 이전 2~9px), 빠를수록 밝다. 시작·끝 가늘어짐 + 낮은 주파수 흔들림.
 * - 그리기: 캔버스 2D(안티앨리어싱) 텍스처 두 장(strokeFxPaint.ts) — 가장자리가 캔버스 픽셀보다 잘게 나뉜다.
 *   1. 바탕: 주인공의 등 (53라운드, 이전엔 긁히는 어두운 표면)
 *   2. 자국 캔버스: 끝난 획은 보관 캔버스에 굽고, 긋는 중인 획은 매 프레임 다시 그린다 — 틈(검정 리본) · 들뜬 가장자리 선 · 잔불 · 심
 *   3. 빛 캔버스 (ADD): 검정 바탕에 'lighten' 으로 백열 코어(fx.core X0/X1) → 층 강조(27/26/25). 표본마다 생성 시각으로 식는다
 *   4. 불티(부드러운 점, 1px 안팎) + 펜 끝 빛 번짐, 빠르게 그을 때 미세 흔들림
 *   5. 부스러기(보통 혼합): 긁힌 화면 조각·검은 재·잔불 조각이 튀었다가 떨어진다 (49라운드 1절, 51라운드 크기 축소)
 * 52라운드 Q8: 자국·빛 캔버스는 실제 캔버스 해상도(1920×1080)로 그린다 — 좌표는 논리 px 그대로, 캔버스 변환(× RESOLUTION)으로
 * 2배 촘촘하게(표본 간격 0.5 논리 px = 실제 1px). 표면 결 텍스처는 논리 해상도(배경이라 충분).
 * 획을 떼면 그 획 전체가 한 번 더 번쩍(FLARE)하고 COOL_MS 동안 식는다.
 * 53라운드 Q3: 바탕 = 화면 가득 찬 주인공의 등(`strokeFxBack.ts`, 어깨 혼불). 3획을 다 그으면 `sear()`:
 * 획이 호박빛으로 타오름 → 살에 스며들며 어두운 균열 + 잔불 심(`strokeFxSear.ts`) → 불티 → 검게 덮임(onPeak: 다음 장면 시작)
 * → 걷힘(onDone). (49라운드 빛 터짐은 폐기)
 * 판정(strokeFeatures)과 무관한 표시 전용.
 */
import Phaser from 'phaser';
import { GAME } from '../core/Constants';
import { CANVAS_H, CANVAS_W, RES } from './display';
import { PALETTE } from '../data';
import { fxCoreColor, hexToInt, rampFor } from './palette';
import { STROKE_FX, heatAt, pathPointAt, searAt, widthRatio, type SearState } from './strokeFxMath';
import { fillRibbon, hash01, lightColor, rgba, strokeCenter, strokeEdge, type Ctx } from './strokeFxPaint';
import { ensureStrokeFxTextures } from './strokeFxTextures';
import { BACK, ShoulderFire, ensureBackTexture } from './strokeFxBack';
import { StrokeSear } from './strokeFxSear';
import { StrokePath, flatten, type StrokeSample } from './strokeFxSpline';

type GlowLayers = typeof STROKE_FX.HOT_LAYERS;

interface StrokeRec {
  path: StrokePath;
  index: number;
  /** 뗀 시각 (획 끝 섬광) */
  flareAt: number | null;
}

export interface StrokeFxSummary {
  /** 아직 빛나는 표본 수 */
  hot: number;
  /** 자국에 구운 표본 수 (끝난 획) */
  scarSegments: number;
  sparksAlive: number;
  strokes: number;
  drawing: boolean;
  lastWidth: number;
  lastSpeed: number;
  shakes: number;
  debrisAlive: number;
  debrisEmitted: number;
  /** 51라운드: 획별 입력점 수·표본 수 · 표본 간격 · 그리기 방식 */
  rawPoints: number[];
  samples: number[];
  stepPx: number;
  render: 'canvas2d';
  /** 53라운드 타오름·스며듦: null = 시작 전, 아니면 경과 ms·단계 */
  sear: {
    t: number;
    ignite: number;
    seep: number;
    heat: number;
    dark: number;
    peaked: boolean;
    embers: number;
  } | null;
}

export class StrokeFx {
  private readonly back: Phaser.GameObjects.Image;
  private readonly fire: ShoulderFire;
  private readonly scarTex: Phaser.Textures.CanvasTexture;
  private readonly lightTex: Phaser.Textures.CanvasTexture;
  private readonly scarImg: Phaser.GameObjects.Image;
  private readonly lightImg: Phaser.GameObjects.Image;
  /** 끝난 획 자국 보관 (화면에 직접 붙지 않는 캔버스) */
  private readonly baked: HTMLCanvasElement;
  private readonly bakedCtx: Ctx;
  private readonly sparks: Phaser.GameObjects.Particles.ParticleEmitter;
  private readonly tip: Phaser.GameObjects.Image;
  private readonly debris: Phaser.GameObjects.Particles.ParticleEmitter;
  private debrisEmitted = 0;
  private strokes: StrokeRec[] = [];
  private active: StrokeRec | null = null;
  private bakedSamples = 0;
  private hotSamples = 0;
  private scarDirty = false;
  /** 직전 프레임에 빛 캔버스에 무언가 그렸다 (꺼질 때 한 번 더 지운다) */
  private lightLive = false;
  private searStart: number | null = null;
  /** 디버그: 마무리 시계를 이 ms 에 멈춤 (스크린샷용) */
  private searHold: number | null = null;
  private searFx?: StrokeSear;
  private peakFired = false;
  private onPeak?: () => void;
  private onDone?: () => void;
  private destroyed = false;
  private readonly ramp: number[];
  private readonly x0: number;
  private readonly x1: number;
  private readonly gray: number[];
  private drawing = false;
  private last = { x: 0, y: 0 };
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
    ensureStrokeFxTextures(this.scene);
    ensureBackTexture(this.scene, this.gray, this.ramp, this.rnd);
    this.back = scene.add
      .image(0, 0, BACK.KEY)
      .setOrigin(0, 0)
      .setScale(1 / RES)
      .setDepth(C.DEPTH_SURFACE);
    this.fire = new ShoulderFire(scene, C.TIP.KEY, this.ramp, C.DEPTH_FIRE);
    this.scarTex = this.makeCanvas(C.CANVAS_KEYS.SCAR);
    this.lightTex = this.makeCanvas(C.CANVAS_KEYS.LIGHT);
    this.scarImg = scene.add
      .image(0, 0, C.CANVAS_KEYS.SCAR)
      .setOrigin(0, 0)
      .setScale(1 / RES)
      .setDepth(C.DEPTH_SCAR);
    this.lightImg = scene.add
      .image(0, 0, C.CANVAS_KEYS.LIGHT)
      .setOrigin(0, 0)
      .setScale(1 / RES)
      .setDepth(C.DEPTH_HOT)
      .setBlendMode(Phaser.BlendModes.ADD)
      .setVisible(false);
    this.baked = document.createElement('canvas');
    this.baked.width = CANVAS_W;
    this.baked.height = CANVAS_H;
    this.bakedCtx = this.baked.getContext('2d')!;
    this.bakedCtx.setTransform(RES, 0, 0, RES, 0, 0);
    const S = C.SPARKS;
    this.sparks = scene.add.particles(0, 0, S.KEY, {
      emitting: false,
      speed: { min: S.SPEED[0], max: S.SPEED[1] },
      lifespan: { min: S.LIFE_MS[0], max: S.LIFE_MS[1] },
      gravityY: S.GRAVITY,
      scale: { start: S.SCALE[0], end: S.SCALE[1] },
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
    const rec: StrokeRec = { path: new StrokePath(this.rnd), index: this.strokes.length + 1, flareAt: null };
    rec.path.push(x, y, t, this.scene.time.now);
    this.strokes.push(rec);
    this.active = rec;
    this.drawing = true;
    this.last = { x, y };
    this.scarDirty = true;
    this.tip
      .setPosition(x, y)
      .setVisible(true)
      .setAlpha(STROKE_FX.TIP.ALPHA * STROKE_FX.INTENSITY.MIN);
    // 누른 자리에 작은 불티 한 줌 + 부스러기 (긁기 시작)
    this.sparks.setEmitterAngle({ min: 0, max: 360 });
    this.sparks.emitParticleAt(x, y, Math.ceil(STROKE_FX.SPARKS.MAX_PER_MOVE / 2));
    this.emitDebris(x, y, STROKE_FX.DEBRIS.ON_BEGIN);
  }

  /** 획 진행: 곡선을 잇고 빛을 넣는다 */
  move(x: number, y: number, t: number): void {
    const rec = this.active;
    if (!this.drawing || this.fading || !rec) return;
    const C = STROKE_FX;
    const dist = Math.hypot(x - this.last.x, y - this.last.y);
    if (dist < C.SPLINE.MIN_INPUT_PX) return;
    rec.path.push(x, y, t, this.scene.time.now);
    const speed = rec.path.lastSpeed;
    const tail = rec.path.samples[rec.path.samples.length - 1];
    this.lastWidth = tail?.w ?? this.lastWidth;
    const I = C.INTENSITY.MIN + (C.INTENSITY.MAX - C.INTENSITY.MIN) * Math.min(1, speed / C.WIDTH.SPEED_REF);
    this.emitSparks(this.last.x, this.last.y, x, y, dist, I);
    this.emitDebris(x, y, Math.min(C.DEBRIS.MAX_PER_MOVE, Math.round(dist * C.DEBRIS.PER_PX * (0.5 + I))));
    this.shake(speed);
    // 펜 끝: 굵을수록(느릴수록) 크게, 빠를수록 밝게
    const r = widthRatio(this.lastWidth);
    this.tip
      .setPosition(x, y)
      .setAlpha(C.TIP.ALPHA * I)
      .setScale(C.TIP.SCALE_MIN + (C.TIP.SCALE_MAX - C.TIP.SCALE_MIN) * r);
    this.last = { x, y };
    this.scarDirty = true;
  }

  /** 획 끝: 그 획 전체가 한 번 번쩍이고 식기 시작한다 */
  end(x: number, y: number, t: number): void {
    const rec = this.active;
    if (!this.drawing || !rec) return;
    this.move(x, y, t);
    const now = this.scene.time.now;
    rec.path.finish(now);
    rec.flareAt = now;
    this.drawing = false;
    this.active = null;
    this.tip.setVisible(false);
    this.paintScar(this.bakedCtx, rec.path.samples, rec.index);
    this.bakedSamples += rec.path.samples.length;
    this.scarDirty = true;
    // 뗄 때: 그 획을 따라 부스러기가 한 번 더 우수수
    const flat = flatten(rec.path.samples);
    if (flat.length >= 4)
      for (let k = 0; k < STROKE_FX.DEBRIS.ON_END; k++) {
        const p = pathPointAt(flat, this.rnd());
        this.emitDebris(p.x, p.y, 1);
      }
  }

  update(time: number): void {
    if (this.destroyed) return;
    if (this.searStart !== null) this.updateSear(time);
    if (this.destroyed || this.peakFired) return;
    this.fire.update(time);
    if (this.scarDirty) this.renderScar(time);
    this.renderLight(time);
  }

  /**
   * 3획을 다 그은 뒤 타오름·스며듦 (53라운드 Q3). onPeak = 화면이 가장 어두운 순간(뒤에서 다음 장면 시작),
   * onDone = 덮개가 걷히고 이 연출이 스스로 파괴된 뒤.
   */
  sear(onPeak?: () => void, onDone?: () => void): void {
    if (this.searStart !== null || this.destroyed) return;
    this.fading = true;
    this.drawing = false;
    this.active = null;
    this.tip.setVisible(false);
    this.onPeak = onPeak;
    this.onDone = onDone;
    this.searStart = this.scene.time.now;
    this.searFx = new StrokeSear(
      this.scene,
      this.strokes.map((r) => r.path.samples),
      (i) => this.rampColor(i),
      (i) => this.gray[i] ?? 0x5c5e62,
      STROKE_FX.SPARKS.KEY,
      this.rnd,
    );
    this.scene.cameras.main.shake(STROKE_FX.SEAR.IGNITE_MS, STROKE_FX.SEAR.SHAKE_INTENSITY);
  }

  /** 디버그: 마무리 시계를 ms 에 멈춘다 (null = 풀고 그 자리부터 계속). 시작 전에 걸어 둘 수도 있다 */
  holdSear(ms: number | null): void {
    if (ms === null && this.searHold !== null && this.searStart !== null)
      this.searStart = this.scene.time.now - this.searHold;
    this.searHold = ms;
  }

  private searT(time: number): number {
    return this.searHold ?? time - (this.searStart ?? time);
  }

  /** 획 단계를 떠날 때(빛 터짐 없이, 폴백): 전부 서서히 사라지고 파괴 */
  fadeOut(onDone?: () => void): void {
    if (this.fading) return;
    this.fading = true;
    this.drawing = false;
    this.tip.setVisible(false);
    this.scene.tweens.add({
      targets: [this.back, this.scarImg, this.lightImg],
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
      hot: this.hotSamples,
      scarSegments: this.bakedSamples,
      sparksAlive: this.sparks.active ? this.sparks.getAliveParticleCount() : 0,
      strokes: this.strokes.length,
      drawing: this.drawing,
      lastWidth: +this.lastWidth.toFixed(2),
      lastSpeed: Math.round(this.active?.path.lastSpeed ?? this.strokes[this.strokes.length - 1]?.path.lastSpeed ?? 0),
      shakes: this.shakes,
      debrisAlive: this.debris.active ? this.debris.getAliveParticleCount() : 0,
      debrisEmitted: this.debrisEmitted,
      rawPoints: this.strokes.map((s) => s.path.rawCount),
      samples: this.strokes.map((s) => s.path.samples.length),
      stepPx: STROKE_FX.SPLINE.STEP_PX,
      render: 'canvas2d',
      sear: this.searSummary(),
    };
  }

  destroy(): void {
    if (this.destroyed) return;
    this.destroyed = true;
    this.strokes = [];
    this.active = null;
    this.back.destroy();
    this.fire.destroy();
    this.scarImg.destroy();
    this.lightImg.destroy();
    const tex = this.scene.textures;
    for (const key of Object.values(STROKE_FX.CANVAS_KEYS)) if (tex.exists(key)) tex.remove(key);
    this.sparks.destroy();
    this.debris.destroy();
    this.tip.destroy();
    this.searFx?.destroy();
  }

  // --- 내부: 그리기 ---

  private makeCanvas(key: string): Phaser.Textures.CanvasTexture {
    const tex = this.scene.textures;
    if (tex.exists(key)) tex.remove(key);
    const canvas = tex.createCanvas(key, CANVAS_W, CANVAS_H)!;
    // 그리기 좌표는 논리 px — 캔버스 변환으로 실제 해상도에 그린다
    canvas.context.setTransform(RES, 0, 0, RES, 0, 0);
    return canvas;
  }

  /** 자국 캔버스 = 보관 캔버스 + 긋는 중인 획 (펜 끝까지) */
  private renderScar(time: number): void {
    const ctx = this.scarTex.context;
    ctx.globalCompositeOperation = 'source-over';
    ctx.clearRect(0, 0, GAME.WIDTH, GAME.HEIGHT);
    // 보관 캔버스는 이미 실제 해상도 → 변환 없이 1:1
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.drawImage(this.baked, 0, 0);
    ctx.restore();
    const a = this.active;
    if (a) this.paintScar(ctx, this.livePoints(a, time), a.index);
    this.scarTex.refresh();
    this.scarDirty = false;
  }

  private livePoints(rec: StrokeRec, time: number): StrokeSample[] {
    return rec === this.active ? rec.path.samples.concat(rec.path.tail(time)) : rec.path.samples;
  }

  /** 자국: 틈(검정 리본) → 들뜬 가장자리 선 2쌍 → 들뜬 조각 → 식은 잔불 → 가는 심 */
  private paintScar(ctx: Ctx, pts: StrokeSample[], strokeIndex: number): void {
    if (pts.length === 0) return;
    const S = STROKE_FX.SCAR;
    const n = pts.length;
    ctx.globalCompositeOperation = 'source-over';
    fillRibbon(ctx, pts, 0, n - 1, rgba(S.GAP_COLOR, S.GAP_ALPHA), 1, S.GAP_EXTRA_PX);
    const lipGray = this.gray[S.LIP_GRAY] ?? 0x5c5e62;
    const edge = (p: StrokeSample) => (p.w + S.GAP_EXTRA_PX) / 2;
    for (const sign of [1, -1] as const) {
      strokeEdge(ctx, pts, sign, (p) => edge(p) + S.LIP_OFFSET_PX, rgba(lipGray, S.LIP_ALPHA), S.LIP_WIDTH);
      strokeEdge(
        ctx,
        pts,
        sign,
        (p) => Math.max(0, edge(p) - S.LIP_HOT_WIDTH / 2),
        rgba(this.rampColor(S.LIP_HOT_RAMP), S.LIP_HOT_ALPHA),
        S.LIP_HOT_WIDTH,
      );
    }
    // 들뜬 조각: 표본 번호로 정해지는 자리 (다시 그려도 같은 곳)
    ctx.fillStyle = rgba(lipGray, Math.min(1, S.LIP_ALPHA * 1.4));
    for (let j = 1; j < n - 1; j++) {
      const h = hash01(j, strokeIndex);
      if (h >= S.CHIP_CHANCE) continue;
      const p = pts[j];
      const q = pts[j + 1];
      const len = Math.hypot(q.x - p.x, q.y - p.y) || 1;
      const sign = hash01(j, strokeIndex + 17) < 0.5 ? 1 : -1;
      const off = (edge(p) + S.LIP_OFFSET_PX + 0.4) * sign;
      const size = S.CHIP_PX[0] + (S.CHIP_PX[1] - S.CHIP_PX[0]) * hash01(j, strokeIndex + 31);
      const cx = p.x + (-(q.y - p.y) / len) * off;
      const cy = p.y + ((q.x - p.x) / len) * off;
      ctx.fillRect(cx - size / 2, cy - size / 2, size, size);
    }
    fillRibbon(ctx, pts, 0, n - 1, rgba(this.rampColor(S.EMBER_RAMP), S.EMBER_ALPHA), S.EMBER_WIDTH);
    strokeCenter(ctx, pts, rgba(this.rampColor(S.CORE_RAMP), S.CORE_ALPHA), S.CORE_WIDTH);
  }

  /** 빛 캔버스: 검정 바탕 + 'lighten'. 식은 뒤 한 번 지우고 멈춘다 */
  private renderLight(time: number): void {
    const C = STROKE_FX;
    const st = this.searStart !== null && !this.peakFired ? searAt(this.searT(time)) : null;
    let hot = 0;
    const ctx = this.lightTex.context;
    const begin = () => {
      ctx.globalCompositeOperation = 'source-over';
      ctx.fillStyle = '#000';
      ctx.fillRect(0, 0, GAME.WIDTH, GAME.HEIGHT);
      ctx.globalCompositeOperation = 'lighten';
    };
    let cleared = false;
    for (const rec of this.strokes) {
      const pts = this.livePoints(rec, time);
      const n = pts.length;
      if (n === 0) continue;
      const fa = rec.flareAt === null ? null : time - rec.flareAt;
      // 끝 표본이 식었으면 그 획은 다 식었다 (앞쪽이 먼저 태어났다)
      if (st || heatAt(time - pts[n - 1].born, fa) <= 0) continue;
      for (let a = 0; a < n; a += C.CHUNK_SAMPLES) {
        const b = Math.min(n - 1, a + C.CHUNK_SAMPLES);
        const mid = pts[(a + b) >> 1];
        const heat = heatAt(time - mid.born, fa) * mid.i;
        if (heat <= 0) continue;
        if (!cleared) {
          begin();
          cleared = true;
        }
        hot += b - a + (b === n - 1 ? 1 : 0);
        this.paintGlow(ctx, pts, a, b, heat, 1);
      }
    }
    this.hotSamples = hot;
    if (st) {
      if (!cleared) begin();
      cleared = true;
      for (const rec of this.strokes) this.paintSearGlow(ctx, rec.path.samples, st);
    }
    if (!cleared && !this.lightLive) return;
    if (!cleared) begin();
    this.lightTex.refresh();
    this.lightImg.setVisible(cleared);
    this.lightLive = cleared;
  }

  /** 표본 [a, b] 를 빛 층(기본 HOT_LAYERS)으로 (열기 heat, 폭 배율 widthMul) */
  private paintGlow(
    ctx: Ctx,
    pts: StrokeSample[],
    a: number,
    b: number,
    heat: number,
    widthMul: number,
    layers: GlowLayers = STROKE_FX.HOT_LAYERS,
  ): void {
    for (const L of layers) {
      const k = L.alpha * Math.pow(Math.min(1, heat), L.pow) * (heat > 1 ? heat : 1);
      if (k < 0.01) continue;
      const color = L.color === 'x0' ? this.x0 : L.color === 'x1' ? this.x1 : this.rampColor(L.color);
      fillRibbon(ctx, pts, a, b, lightColor(color, k), L.width * widthMul, 0, 0.3, 'wb');
    }
  }

  /** 타오름·스며듦: 획 전체를 호박빛 층으로 (조각마다 살짝 다른 일렁임) */
  private paintSearGlow(ctx: Ctx, pts: StrokeSample[], st: SearState): void {
    const n = pts.length;
    if (n < 2) return;
    const step = STROKE_FX.CHUNK_SAMPLES * 4;
    const flick = st.seep < 1 ? STROKE_FX.SEAR.FLICKER * (1 - st.seep) : 0;
    for (let a = 0; a < n - 1; a += step) {
      const b = Math.min(n - 1, a + step);
      const k = 1 + flick * Math.sin(this.scene.time.now / 70 + a * 0.37);
      this.paintGlow(ctx, pts, a, b, Math.min(1, st.heat * k), st.widthMul, STROKE_FX.SEAR_LAYERS);
    }
  }

  // --- 내부: 타오름·스며듦 진행 ---

  private updateSear(time: number): void {
    const S = STROKE_FX.SEAR;
    const st = searAt(this.searT(time));
    const sear = this.searFx;
    if (!sear) return;
    sear.update(st);
    this.scarImg.setAlpha(sear.scarAlpha(st));
    this.fire.setBoost(st.peaked ? 0 : Math.max(0, st.heat - S.EMBER_HEAT));
    if (st.shaking)
      for (let k = 0; k < S.IGNITE_SPARKS; k++) {
        const q = sear.randomPoint();
        if (!q) break;
        this.sparks.setEmitterAngle({ min: 200, max: 340 });
        this.sparks.emitParticleAt(q.x, q.y, 1);
      }
    if (st.peaked && !this.peakFired) {
      // 가장 어두운 순간: 등을 걷어내고 다음 장면을 뒤에서 시작
      this.peakFired = true;
      for (const o of [this.back, this.scarImg, this.lightImg, this.sparks, this.debris, this.tip]) o.setVisible(false);
      this.fire.setVisible(false);
      sear.hideScene();
      this.onPeak?.();
    }
    if (st.done) {
      const done = this.onDone;
      this.destroy();
      done?.();
    }
  }

  private searSummary(): StrokeFxSummary['sear'] {
    if (this.searStart === null) return null;
    const t = this.searT(this.scene.time.now);
    const st = searAt(t);
    return {
      t: Math.round(t),
      ignite: +st.ignite.toFixed(2),
      seep: +st.seep.toFixed(2),
      heat: +st.heat.toFixed(2),
      dark: +st.dark.toFixed(2),
      peaked: st.peaked,
      embers: this.searFx?.embersEmitted ?? 0,
    };
  }

  // --- 내부: 입자 ---

  private emitDebris(x: number, y: number, n: number): void {
    if (n <= 0) return;
    this.debris.emitParticleAt(x, y, n);
    this.debrisEmitted += n;
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

  private rampColor(i: number): number {
    return this.ramp[i] ?? this.x1;
  }
}
