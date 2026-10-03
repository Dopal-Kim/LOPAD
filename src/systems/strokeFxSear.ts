/**
 * 53라운드 Q3: 3획 뒤 마무리 '상흔이 타오르며 스며듦'의 화면 쪽 부품 (49라운드 빛 터짐 교체).
 * - 스며든 상흔 캔버스: 그을린 살 + 어두운 균열 + 잔불 심. 스며듦(SEEP) 동안 기존 자국 위로 교차해 들어온다.
 * - 불티: 획 위 임의 점에서 위로 떠오르는 ADD 파티클.
 * - 검은 덮개: 가장 어두운 순간(peak)에 다음 장면(회피 시험)이 뒤에서 시작하고, 걷히며 드러난다.
 * 타임라인 계산은 `strokeFxMath.ts` 의 `searAt`. 획 빛(타오름)은 `StrokeFx` 의 빛 캔버스가 SEAR_LAYERS 로 그린다.
 */
import Phaser from 'phaser';
import { GAME } from '../core/Constants';
import { CANVAS_H, CANVAS_W, RES } from './display';
import { STROKE_FX, type SearState } from './strokeFxMath';
import { fillRibbon, rgba, strokeCenter, strokeEdge } from './strokeFxPaint';
import type { StrokeSample } from './strokeFxSpline';

export class StrokeSear {
  private readonly tex: Phaser.Textures.CanvasTexture;
  private readonly settled: Phaser.GameObjects.Image;
  private readonly embers: Phaser.GameObjects.Particles.ParticleEmitter;
  private readonly dark: Phaser.GameObjects.Rectangle;
  /** 불티 낸 수 (디버그) */
  embersEmitted = 0;

  constructor(
    private readonly scene: Phaser.Scene,
    private readonly paths: StrokeSample[][],
    ramp: (i: number) => number,
    gray: (i: number) => number,
    sparkKey: string,
    private readonly rnd: () => number,
  ) {
    const C = STROKE_FX;
    const key = C.CANVAS_KEYS.SETTLED;
    if (scene.textures.exists(key)) scene.textures.remove(key);
    this.tex = scene.textures.createCanvas(key, CANVAS_W, CANVAS_H)!;
    const ctx = this.tex.context;
    ctx.setTransform(RES, 0, 0, RES, 0, 0);
    for (const p of paths) paintSettled(ctx, p, ramp, gray);
    this.tex.refresh();
    this.settled = scene.add
      .image(0, 0, key)
      .setOrigin(0, 0)
      .setScale(1 / RES)
      .setDepth(C.DEPTH_SCAR + 0.1)
      .setAlpha(0);
    const E = C.EMBERS;
    this.embers = scene.add.particles(0, 0, sparkKey, {
      emitting: false,
      speed: { min: E.SPEED[0], max: E.SPEED[1] },
      angle: { min: E.ANGLE[0], max: E.ANGLE[1] },
      lifespan: { min: E.LIFE_MS[0], max: E.LIFE_MS[1] },
      gravityY: E.GRAVITY,
      scale: { start: E.SCALE[0], end: E.SCALE[1] },
      alpha: { start: 1, end: 0, ease: 'Quad.easeIn' },
      tint: E.RAMP_TINTS.map(ramp),
      blendMode: Phaser.BlendModes.ADD,
    });
    this.embers.setDepth(C.DEPTH_SPARK);
    this.dark = scene.add
      .rectangle(0, 0, GAME.WIDTH, GAME.HEIGHT, 0x000000, 1)
      .setOrigin(0, 0)
      .setScrollFactor(0)
      .setDepth(C.SEAR.DEPTH_DARK)
      .setAlpha(0);
  }

  /** 기존 자국 이미지의 알파 (스며든 상흔이 들어오는 만큼 빠진다) */
  scarAlpha(st: SearState): number {
    return 1 - ease(st.seep);
  }

  update(st: SearState): void {
    this.settled.setAlpha(ease(st.seep));
    this.dark.setAlpha(st.dark);
    if (st.embers && !st.peaked)
      for (let k = 0; k < STROKE_FX.SEAR.EMBERS_PER_FRAME; k++) {
        const q = this.randomPoint();
        if (!q) break;
        this.embers.emitParticleAt(q.x, q.y, 1);
        this.embersEmitted += 1;
      }
  }

  /** 획 위 임의 표본 */
  randomPoint(): StrokeSample | null {
    const p = this.paths[Math.floor(this.rnd() * this.paths.length)];
    if (!p || p.length === 0) return null;
    return p[Math.floor(this.rnd() * p.length)];
  }

  /** peak: 덮개만 남기고 숨긴다 */
  hideScene(): void {
    this.settled.setVisible(false);
    this.embers.setVisible(false);
  }

  destroy(): void {
    this.settled.destroy();
    this.embers.destroy();
    this.dark.destroy();
    const key = STROKE_FX.CANVAS_KEYS.SETTLED;
    if (this.scene.textures.exists(key)) this.scene.textures.remove(key);
  }
}

/** 스며든 상흔: 그을린 살(넓고 옅은 어둠) → 균열 → 가장자리 → 잔불 심 → 가는 심 */
export function paintSettled(
  ctx: CanvasRenderingContext2D,
  pts: StrokeSample[],
  ramp: (i: number) => number,
  gray: (i: number) => number,
): void {
  if (pts.length === 0) return;
  const S = STROKE_FX.SETTLED;
  const n = pts.length;
  ctx.globalCompositeOperation = 'source-over';
  for (const c of S.CHAR) fillRibbon(ctx, pts, 0, n - 1, rgba(ramp(S.CHAR_RAMP), c.alpha), 1, c.add);
  fillRibbon(ctx, pts, 0, n - 1, rgba(0x000000, S.GAP_ALPHA), 1, S.GAP_ADD);
  const edge = (p: StrokeSample) => (p.w + S.GAP_ADD) / 2 + 0.35;
  for (const sign of [1, -1] as const) strokeEdge(ctx, pts, sign, edge, rgba(gray(S.LIP_GRAY), S.LIP_ALPHA), 0.5);
  fillRibbon(ctx, pts, 0, n - 1, rgba(ramp(S.EMBER_RAMP), S.EMBER_ALPHA), S.EMBER_SCALE);
  strokeCenter(ctx, pts, rgba(ramp(S.CORE_RAMP), S.CORE_ALPHA), S.CORE_WIDTH);
}

function ease(x: number): number {
  return x * x * (3 - 2 * x);
}
