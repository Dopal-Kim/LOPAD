/**
 * 획 연출 텍스처 (51라운드 정리: strokeFx.ts 에서 분리). 표면(결)·부스러기·불티·펜 끝·빛 번짐을 한 번 만들어 재사용한다.
 * 작은 입자는 LINEAR(1px 아래로 부드럽게).
 */
import Phaser from 'phaser';
import { GAME } from '../core/Constants';
import { PALETTE } from '../data';
import { hexToRgb } from './palette';
import { STROKE_FX } from './strokeFxMath';

export function ensureStrokeFxTextures(scene: Phaser.Scene, rnd: () => number): void {
  const C = STROKE_FX;
  const tex = scene.textures;
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
        if (rnd() < S.GRAIN_DENSITY) c = grains[Math.floor(rnd() * grains.length)];
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
      const x = rnd() * W;
      const y = rnd() * H;
      const a = (rnd() - 0.5) * 0.6;
      const len = 20 + rnd() * 90;
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(x + Math.cos(a) * len, y + Math.sin(a) * len);
      ctx.stroke();
    }
    ctx.globalAlpha = 1;
    canvas.refresh();
  }
  if (!tex.exists(C.DEBRIS.KEY)) {
    // 부스러기: 모서리 한 칸이 빠진 작은 조각 (재·화면 파편)
    const d = C.DEBRIS.SIZE_PX;
    const canvas = tex.createCanvas(C.DEBRIS.KEY, d, d)!;
    const ctx = canvas.context;
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, d, d - 1);
    ctx.fillRect(1, d - 1, d - 1, 1);
    canvas.refresh();
    canvas.setFilter(Phaser.Textures.FilterMode.LINEAR);
  }
  for (const [key, r, linear] of [
    [C.SPARKS.KEY, C.SPARKS.SIZE_PX / 2, true],
    [C.TIP.KEY, C.TIP.RADIUS_PX, true],
    [C.BURST.GLOW_KEY, C.BURST.GLOW_RADIUS_PX, false],
  ] as [string, number, boolean][]) {
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
    if (linear) canvas.setFilter(Phaser.Textures.FilterMode.LINEAR);
  }
}
