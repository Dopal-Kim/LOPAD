import Phaser from 'phaser';
import { GlowText } from './glow';
import { keyGlyph } from './keyGuide';
import { swatch } from './StructureHud';
import { GRAY, hexToNum } from './theme';
import { TRAIT_ICON } from './themeGrowth';
import { VOICE_LOOK, type VoiceWeaponId } from './themeStory';

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

/**
 * §18.1 개성·공명 카드 그림 (아트 128×128 도트) — 칸 `size`×`size` 에 맞춰 줄이고(128 → 64 = 도트 그대로, 32 = 1/4),
 * 어두운 바탕 · 무기 빛 테두리(`frame` px, 색 `color`) · 바깥 G00 한 줄을 UI 가 그린다. (x, y) = 그림 칸 왼쪽 위
 * (테두리는 그 바깥). 텍스처가 없으면 null → 부르는 쪽이 키캡으로 대신한다. 테두리까지 포함한 바깥 크기 = size + 2(frame+1).
 */
export function traitIconBox(
  scene: Phaser.Scene,
  key: string | null | undefined,
  x: number,
  y: number,
  size: number,
  color: number,
  frame: number,
  backColor: number,
): Phaser.GameObjects.GameObject[] | null {
  if (!key || !scene.textures.exists(key)) return null;
  const g = scene.add.graphics();
  const o = frame + 1;
  g.fillStyle(0x000000, 1).fillRect(x - o, y - o, size + o * 2, size + o * 2);
  g.fillStyle(color, 1).fillRect(x - frame, y - frame, size + frame * 2, size + frame * 2);
  g.fillStyle(backColor, 1).fillRect(x, y, size, size);
  const img = scene.add.image(0, 0, key).setOrigin(0, 0);
  const w = Math.max(1, img.width);
  const h = Math.max(1, img.height);
  const scale = size / Math.max(w, h);
  img.setScale(scale);
  img.setPosition(Math.round(x + (size - w * scale) / 2), Math.round(y + (size - h * scale) / 2));
  return [g, img];
}

/** 테두리까지 포함한 그림 칸 바깥 한 변 */
export function traitIconOuter(size: number, frame: number): number {
  return size + (frame + 1) * 2;
}

/**
 * 공명 짝 마름모 (`need` 개, 앞 `have` 개 채움) — 왼쪽 마름모 가운데 (x0, cy). 오른쪽 끝 x 를 돌려준다.
 */
export function pairPips(
  g: Phaser.GameObjects.Graphics,
  x0: number,
  cy: number,
  have: number,
  need: number,
  r: number,
  gap: number,
  on: number,
  off: number,
): number {
  const step = r * 2 + gap;
  for (let i = 0; i < need; i++) {
    const filled = i < have;
    diamond(g, x0 + i * step, cy, r, filled ? on : off, filled);
  }
  return x0 + (need - 1) * step + r;
}

/** 무기 빛 테두리 색 (원한의 한마디 세로 줄과 같은 색 — 칼 G13 · 대검 잉걸 21 · 단검 G10 · 활 S5) */
export function weaponFrameColor(scene: Phaser.Scene, weapon: VoiceWeaponId): number {
  return swatch(scene, 0, VOICE_LOOK[weapon].bar);
}

/** 카드·알림 크기 그림 (64 · 테두리 2) — 텍스처가 없으면 null */
export function traitIconCard(
  scene: Phaser.Scene,
  key: string | null | undefined,
  x: number,
  y: number,
  weapon: VoiceWeaponId,
): Phaser.GameObjects.GameObject[] | null {
  return traitIconBox(
    scene,
    key,
    x,
    y,
    TRAIT_ICON.size,
    weaponFrameColor(scene, weapon),
    TRAIT_ICON.frame,
    hexToNum(GRAY[TRAIT_ICON.backGray]),
  );
}
