/**
 * 62 루프 3 시스템 I (P1-N1): 가장자리가 흐린 바닥 얼룩 — 칸 크기 사각형(술·불 웅덩이 대체 그림)이 돌바닥 위에서
 * 바둑판 빛 판처럼 보이던 것을 둥근 데칼로. 흰 방사형 캔버스 텍스처 하나(씬 사이 공유)를 색 틴트·배율로 쓴다.
 * 이웃 칸 웅덩이가 하나의 얼룩으로 이어지게 칸보다 조금 크게(SPREAD) 그린다.
 */
import Phaser from 'phaser';

const KEY = 'decal_soft_round';
const SIZE = 64;
/** 칸 크기 대비 그림 배율 (이웃 칸과 겹쳐 이음매가 보이지 않게) */
export const SOFT_DECAL_SPREAD = 1.45;

function ensureTexture(scene: Phaser.Scene): string {
  if (scene.textures.exists(KEY)) return KEY;
  const tex = scene.textures.createCanvas(KEY, SIZE, SIZE);
  if (!tex) return KEY;
  const ctx = tex.getContext();
  const r = SIZE / 2;
  const g = ctx.createRadialGradient(r, r, 0, r, r, r);
  g.addColorStop(0, 'rgba(255,255,255,1)');
  g.addColorStop(0.45, 'rgba(255,255,255,0.85)');
  g.addColorStop(0.8, 'rgba(255,255,255,0.3)');
  g.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, SIZE, SIZE);
  tex.refresh();
  return KEY;
}

/** (x, y) 가운데, w×h 칸을 덮는 흐린 얼룩 (색·알파) */
export function softDecal(
  scene: Phaser.Scene,
  x: number,
  y: number,
  w: number,
  h: number,
  color: number,
  alpha: number,
): Phaser.GameObjects.Image {
  const key = ensureTexture(scene);
  return scene.add
    .image(x, y, key)
    .setDisplaySize(w * SOFT_DECAL_SPREAD, h * SOFT_DECAL_SPREAD)
    .setTint(color)
    .setAlpha(alpha);
}
