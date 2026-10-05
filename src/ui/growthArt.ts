import Phaser from 'phaser';
import { GlowText } from './glow';
import { keyGlyph } from './keyGuide';

/**
 * 61 단계 4 P12 무기 성장 그리기 조각 (HUD 게이지·선택 카드·배너·성장도·안내 카드가 같이 쓴다).
 * 마름모는 글꼴 대신 Graphics 로 그린다(Galmuri 에 ◇◆ 가 없을 수 있다 — '→' 처럼).
 */

/** 마름모 (가운데 cx,cy · 반지름 r). fill 이면 채움, 아니면 1px 테 */
export function diamond(
  g: Phaser.GameObjects.Graphics,
  cx: number,
  cy: number,
  r: number,
  color: number,
  fill: boolean,
  alpha = 1,
): void {
  const pts = [
    new Phaser.Math.Vector2(cx, cy - r),
    new Phaser.Math.Vector2(cx + r, cy),
    new Phaser.Math.Vector2(cx, cy + r),
    new Phaser.Math.Vector2(cx - r, cy),
  ];
  if (fill) g.fillStyle(color, alpha).fillPoints(pts, true);
  else g.lineStyle(1, color, alpha).strokePoints(pts, true);
}

/**
 * 무기 모양 그림 (시스템이 읽어 둔 텍스처 `lookKey`) — 칸 maxW×maxH 안에 도트가 흐려지지 않는 배율로(키우면 정수 배, 줄이면
 * 칸에 맞춤), (cx, top) 가운데 위. 텍스처가 없으면 null.
 */
export function lookImage(
  scene: Phaser.Scene,
  key: string | null | undefined,
  cx: number,
  top: number,
  maxW: number,
  maxH: number,
): Phaser.GameObjects.Image | null {
  if (!key || !scene.textures.exists(key)) return null;
  const img = scene.add.image(0, 0, key).setOrigin(0, 0);
  const w = Math.max(1, img.width);
  const h = Math.max(1, img.height);
  const fit = Math.min(maxW / w, maxH / h);
  const scale = fit >= 1 ? Math.max(1, Math.min(2, Math.floor(fit))) : fit;
  img.setScale(scale);
  img.setPosition(Math.round(cx - (w * scale) / 2), Math.round(top + (maxH - h * scale) / 2));
  return img;
}

/** 그림이 없을 때: 무기 이름 글자(2배, 흐림)를 칸 가운데에 */
export function lookText(scene: Phaser.Scene, text: string, cx: number, top: number, maxH: number): GlowText {
  const t = new GlowText(scene, 0, 0, text, 'page_faint', { scale: 2 });
  return t.placeCenter(cx, Math.round(top + (maxH - t.displayHeight) / 2));
}

/** 키 그림을 `scale` 배로 (Container 하나 — 폭·높이는 배율 반영) */
export function scaledKey(
  scene: Phaser.Scene,
  key: string,
  scale: 1 | 2,
): { obj: Phaser.GameObjects.Container; width: number; height: number } {
  const k = keyGlyph(scene, key);
  k.obj.setScale(scale);
  return { obj: k.obj, width: k.width * scale, height: 16 * scale };
}
