import Phaser from 'phaser';
import { UI_SCREEN } from '../contract/ui';

/**
 * P21 가장자리 비네트 그림 (캔버스 한 장, 가운데 투명 → 가장자리 `hex`). 색을 텍스처에 구워 둔다 — Canvas 렌더러는 tint 를
 * 못 쓰므로. 화면 크기로 늘려 쓰는 Image 를 돌려준다(원점 가운데). 같은 키면 텍스처를 다시 만들지 않는다.
 */
const TEX_W = 192;
const TEX_H = 108;

export function vignetteImage(scene: Phaser.Scene, hex: string, depth: number): Phaser.GameObjects.Image {
  const key = `ui-vignette-${hex.replace('#', '')}`;
  if (!scene.textures.exists(key)) {
    const tex = scene.textures.createCanvas(key, TEX_W, TEX_H);
    if (tex) {
      const ctx = tex.getContext();
      const n = parseInt(hex.slice(1), 16);
      const rgb = `${(n >> 16) & 255},${(n >> 8) & 255},${n & 255}`;
      // 타원: 세로를 눌러 그린 원
      ctx.save();
      ctx.scale(1, TEX_H / TEX_W);
      const c = TEX_W / 2;
      const g = ctx.createRadialGradient(c, c, TEX_W * 0.3, c, c, TEX_W * 0.66);
      g.addColorStop(0, `rgba(${rgb},0)`);
      g.addColorStop(0.55, `rgba(${rgb},0.4)`);
      g.addColorStop(1, `rgba(${rgb},1)`);
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, TEX_W, TEX_W);
      ctx.restore();
      tex.setFilter(Phaser.Textures.FilterMode.LINEAR);
      tex.refresh();
    }
  }
  return scene.add
    .image(UI_SCREEN.WIDTH / 2, UI_SCREEN.HEIGHT / 2, key)
    .setDisplaySize(UI_SCREEN.WIDTH, UI_SCREEN.HEIGHT)
    .setDepth(depth)
    .setScrollFactor(0);
}
