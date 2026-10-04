/**
 * 공격 예고 부품 그리기 (57라운드 B8: telegraph.ts 에서 분리): 화살촉 · 수렴 오라 · 시트가 없을 때의 Graphics 도형
 * (점선·꺾은 점선·원·부채꼴·닫히는 원). 깊이는 전부 바닥(`DEPTH.FX_GROUND`) 띠.
 */
import Phaser from 'phaser';
import { DEPTH, ENEMY_FX } from '../../core/Constants';
import { spriteLibrary } from '../sprites/sprites';
import { FX_ACTION, fxDrawScale } from '../sprites/spriteDefs';
import type { AuraObject, Point, TelegraphStyle } from './types';

/** 화살촉: +x 를 향한 삼각형(끝 = 원점), 층 램프 몸 + 테두리 1px */
export function makeTip(scene: Phaser.Scene, style: TelegraphStyle): Phaser.GameObjects.Graphics {
  const B = ENEMY_FX.BOLD;
  const g = scene.add.graphics().setDepth(DEPTH.FX_GROUND + 0.001);
  g.fillStyle(style.tipColor, 1);
  g.fillTriangle(0, 0, -B.TIP_LENGTH, -B.TIP_HALF_WIDTH, -B.TIP_LENGTH, B.TIP_HALF_WIDTH);
  g.lineStyle(1, style.tipEdge, 1);
  g.strokeTriangle(0, 0, -B.TIP_LENGTH, -B.TIP_HALF_WIDTH, -B.TIP_LENGTH, B.TIP_HALF_WIDTH);
  return g;
}

/** 수렴 오라: telegraph_aura 시트(루프, 배율 AURA_SCALE) → 없으면 Graphics 원 */
export function makeAura(scene: Phaser.Scene, x: number, y: number, style: TelegraphStyle): AuraObject {
  const B = ENEMY_FX.BOLD;
  const id = ENEMY_FX.AURA_ID;
  const def = spriteLibrary.sheet(id, FX_ACTION);
  const texture = spriteLibrary.textureKey(id, FX_ACTION);
  const anim = spriteLibrary.animKey(id, FX_ACTION, 'down');
  if (def && texture && anim && scene.textures.exists(texture)) {
    const s = scene.add
      .sprite(x, y, texture, 0)
      .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
      .setScale(B.AURA_SCALE * fxDrawScale(def))
      .setDepth(DEPTH.FX_GROUND + 0.002);
    s.play(anim, true);
    return s;
  }
  const g = scene.add
    .graphics()
    .setDepth(DEPTH.FX_GROUND + 0.002)
    .setPosition(x, y);
  g.lineStyle(ENEMY_FX.PLACEHOLDER.LINE_WIDTH, style.tipColor, 1);
  g.strokeCircle(0, 0, B.AURA_PLACEHOLDER_RADIUS);
  g.setAlpha(ENEMY_FX.PLACEHOLDER.ALPHA);
  return g;
}

/** 깜빡임 낮은 위상의 플레이스홀더(Graphics) 알파 */
export function placeholderAlpha(low: boolean): number {
  return low ? ENEMY_FX.PLACEHOLDER.ALPHA * 0.45 : ENEMY_FX.PLACEHOLDER.ALPHA;
}

/** 마감 직전 가속: 시트 오라 애니 배속 (Graphics 오라는 깜빡임에서 알파로) */
export function speedUpAura(aura: AuraObject | undefined): void {
  if (aura instanceof Phaser.GameObjects.Sprite) aura.anims.timeScale = ENEMY_FX.BOLD.FINAL_BLINK_DIV;
}

// --- 플레이스홀더 (시트가 없을 때) ---

/** 점선: 원점에서 +x 로 lengthPx */
export function drawDashedLine(g: Phaser.GameObjects.Graphics, lengthPx: number): void {
  const P = ENEMY_FX.PLACEHOLDER;
  g.lineStyle(ENEMY_FX.BOLD.PLACEHOLDER_LINE_WIDTH, P.COLOR, 1);
  for (let x = 0; x < lengthPx; x += P.DASH_PX + P.GAP_PX) {
    g.beginPath();
    g.moveTo(x, 0);
    g.lineTo(Math.min(lengthPx, x + P.DASH_PX), 0);
    g.strokePath();
  }
}

/** 꺾은 점선: 누적 거리로 DASH·GAP 을 이어 간다 (월드 좌표, g 는 원점에 둔다) */
export function drawDashedPolyline(g: Phaser.GameObjects.Graphics, points: readonly Point[]): void {
  const P = ENEMY_FX.PLACEHOLDER;
  g.clear();
  g.lineStyle(ENEMY_FX.BOLD.PLACEHOLDER_LINE_WIDTH, P.COLOR, 1);
  let acc = 0;
  for (let i = 0; i < points.length - 1; i++) {
    const a = points[i];
    const b = points[i + 1];
    const len = Math.hypot(b.x - a.x, b.y - a.y);
    if (len <= 0) continue;
    const ux = (b.x - a.x) / len;
    const uy = (b.y - a.y) / len;
    for (let t = 0; t < len;) {
      const cyc = (acc + t) % (P.DASH_PX + P.GAP_PX);
      if (cyc < P.DASH_PX) {
        const e = Math.min(len, t + (P.DASH_PX - cyc));
        g.beginPath();
        g.moveTo(a.x + ux * t, a.y + uy * t);
        g.lineTo(a.x + ux * e, a.y + uy * e);
        g.strokePath();
        t = e;
      } else t += P.DASH_PX + P.GAP_PX - cyc;
    }
    acc += len;
  }
  g.setAlpha(P.ALPHA);
}

export function drawCircle(g: Phaser.GameObjects.Graphics, r: number): void {
  const P = ENEMY_FX.PLACEHOLDER;
  g.lineStyle(ENEMY_FX.BOLD.PLACEHOLDER_LINE_WIDTH, P.COLOR, 1);
  g.strokeCircle(0, 0, r);
}

/** 부채꼴: +x 기준 ±half (통째로 회전해 쓴다) */
export function drawCone(g: Phaser.GameObjects.Graphics, r: number, half: number): void {
  const P = ENEMY_FX.PLACEHOLDER;
  g.lineStyle(ENEMY_FX.BOLD.PLACEHOLDER_LINE_WIDTH, P.COLOR, 1);
  g.beginPath();
  g.moveTo(0, 0);
  g.lineTo(Math.cos(-half) * r, Math.sin(-half) * r);
  g.arc(0, 0, r, -half, half, false);
  g.lineTo(0, 0);
  g.strokePath();
}

/** 닫히는 원: 남은 시간 비율(ratio)로 반지름이 줄어드는 안쪽 원 */
export function drawClosing(g: Phaser.GameObjects.Graphics, radiusPx: number, ratio: number): void {
  const B = ENEMY_FX.BOLD;
  const r = Math.max(1, Math.round(radiusPx * Math.max(B.CLOSING_MIN_RATIO, ratio)));
  g.clear();
  g.fillStyle(ENEMY_FX.PLACEHOLDER.COLOR, B.CLOSING_FILL_ALPHA);
  g.fillCircle(0, 0, r);
  g.lineStyle(B.CLOSING_LINE_WIDTH, ENEMY_FX.PLACEHOLDER.COLOR, B.CLOSING_LINE_ALPHA);
  g.strokeCircle(0, 0, r);
}

/** 디버그 요약: 오라 종류 (시트 텍스처 키 / 'graphics' / 없음) */
export function auraLabel(aura: AuraObject | undefined): string | null {
  return aura ? (aura instanceof Phaser.GameObjects.Sprite ? aura.texture.key : 'graphics') : null;
}
