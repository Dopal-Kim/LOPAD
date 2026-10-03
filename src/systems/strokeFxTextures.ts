/**
 * 획 연출 텍스처 (51라운드 정리: strokeFx.ts 에서 분리). 부스러기·불티·펜 끝을 한 번 만들어 재사용한다.
 * 53라운드: 긁히는 표면 → 주인공의 등(`strokeFxBack.ts`).
 * 작은 입자는 LINEAR(1px 아래로 부드럽게).
 */
import Phaser from 'phaser';
import { STROKE_FX } from './strokeFxMath';

export function ensureStrokeFxTextures(scene: Phaser.Scene): void {
  const C = STROKE_FX;
  const tex = scene.textures;
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
