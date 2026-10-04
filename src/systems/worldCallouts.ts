/**
 * 56라운드 Q7·Q8 월드 문구 (PERFECT GUARD · PARRY — 영문). 데미지 숫자처럼 시스템 씬이 월드 좌표에 그린다(HUD 가 아님).
 * 몸 위에서 떠올라(RISE_PX) 머물렀다(HOLD_MS) 사라진다(FADE_MS). 시간은 트윈 — 히트스톱 동안에도 읽힌다. Text 풀 재사용.
 */
import Phaser from 'phaser';
import { DEPTH, FEEDBACK, FEEL } from '../core/Constants';
import { fontFamilyOr } from './fonts';

export interface CalloutSummary {
  text: string;
  x: number;
  y: number;
  alpha: number;
}

export class WorldCallouts {
  private readonly pool: Phaser.GameObjects.Text[] = [];
  private readonly active = new Set<Phaser.GameObjects.Text>();
  /** 디버그: 표시 횟수 · 마지막 문구 */
  count = 0;
  last: string | null = null;

  constructor(private readonly scene: Phaser.Scene) {}

  show(x: number, y: number, text: string): Phaser.GameObjects.Text | null {
    const C = FEEDBACK.CALLOUT;
    const t = this.acquire();
    if (!t) return null;
    const startY = Math.round(y + C.OFFSET_Y);
    t.setText(text)
      .setFontFamily(fontFamilyOr(FEEL.DAMAGE_TEXT.FONT_FAMILY, FEEL.DAMAGE_TEXT.FONT_FALLBACK))
      .setFontSize(C.FONT_PX)
      .setColor(C.COLOR)
      .setStroke(C.STROKE, C.STROKE_PX)
      .setOrigin(0.5, 1)
      .setPosition(Math.round(x), startY)
      .setAlpha(1)
      .setDepth(DEPTH.DAMAGE_TEXT + 0.1)
      .setVisible(true)
      .setActive(true);
    this.scene.tweens.killTweensOf(t);
    this.scene.tweens.add({ targets: t, y: startY - C.RISE_PX, duration: C.HOLD_MS, ease: 'Quad.easeOut' });
    this.scene.tweens.add({
      targets: t,
      alpha: 0,
      delay: C.HOLD_MS,
      duration: C.FADE_MS,
      onComplete: () => this.release(t),
    });
    this.count += 1;
    this.last = text;
    return t;
  }

  summary(): CalloutSummary[] {
    return [...this.active].map((t) => ({ text: t.text, x: t.x, y: t.y, alpha: t.alpha }));
  }

  destroy(): void {
    for (const t of [...this.pool, ...this.active]) {
      this.scene.tweens.killTweensOf(t);
      t.destroy();
    }
    this.pool.length = 0;
    this.active.clear();
  }

  private acquire(): Phaser.GameObjects.Text | null {
    let t = this.pool.pop();
    if (!t) {
      if (this.active.size >= FEEDBACK.CALLOUT.POOL) {
        // 가장 오래된 것을 다시 쓴다
        const oldest = this.active.values().next().value as Phaser.GameObjects.Text | undefined;
        if (!oldest) return null;
        this.active.delete(oldest);
        t = oldest;
      } else t = this.scene.add.text(0, 0, '', { fontSize: `${FEEDBACK.CALLOUT.FONT_PX}px` });
    }
    this.active.add(t);
    return t;
  }

  private release(t: Phaser.GameObjects.Text): void {
    if (!this.active.delete(t)) return;
    t.setVisible(false).setActive(false);
    this.pool.push(t);
  }
}
