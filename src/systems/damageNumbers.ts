/**
 * 데미지 숫자 (35라운드 1단계). 시스템 씬이 월드 좌표에 직접 그린다(HUD 가 아님).
 * - 적중점 위에서 떠올라(RISE_PX) 사라진다(DURATION_MS, 끝 FADE_MS 페이드). Text 풀(POOL)로 재사용.
 * - 일반 = G13 흰색, 치명타 = 층 강조 램프 light1 + '!' + 1.5배, 플레이어 피격 = G11 + '-', 지속 피해 틱 = 0.8배.
 * - 글꼴 Galmuri11 (34라운드 규칙, 11px). 로드 전·실패면 monospace.
 */
import Phaser from 'phaser';
import { COLORS, DEPTH, FEEL } from '../core/Constants';
import { PALETTE } from '../data';
import { rampFor } from './palette';
import { fontFamilyOr } from './fonts';
import { feelSettings } from './feel';

export type DamageKind = 'hit' | 'crit' | 'tick' | 'player';

export interface DamageNumberSummary {
  text: string;
  x: number;
  y: number;
  alpha: number;
  scale: number;
  color: string;
  font: string;
}

export class DamageNumberPool {
  private readonly pool: Phaser.GameObjects.Text[] = [];
  private readonly active = new Set<Phaser.GameObjects.Text>();
  private critColor: string = COLORS.DAMAGE_TEXT_FALLBACK_CRIT;
  /** 디버그: 표시 횟수 */
  count = 0;

  constructor(
    private readonly scene: Phaser.Scene,
    private readonly random: () => number = Math.random,
  ) {}

  /** 층 진입: 치명타 색 = 그 층 램프의 light1 (없으면 폴백 호박색) */
  setFloor(floor: number): void {
    const ramp = rampFor(PALETTE, floor);
    this.critColor = ramp?.[FEEL.DAMAGE_TEXT.CRIT_RAMP_INDEX] ?? COLORS.DAMAGE_TEXT_FALLBACK_CRIT;
  }

  get fontFamily(): string {
    return fontFamilyOr(FEEL.DAMAGE_TEXT.FONT_FAMILY, FEEL.DAMAGE_TEXT.FONT_FALLBACK);
  }

  show(x: number, y: number, amount: number, kind: DamageKind): Phaser.GameObjects.Text | null {
    if (!feelSettings.numbers) return null;
    const D = FEEL.DAMAGE_TEXT;
    const t = this.acquire();
    if (!t) return null;
    const label = kind === 'player' ? `-${amount}` : kind === 'crit' ? `${amount}!` : `${amount}`;
    const color = kind === 'crit' ? this.critColor : kind === 'player' ? COLORS.DAMAGE_TEXT_PLAYER : COLORS.DAMAGE_TEXT;
    const scale = kind === 'crit' ? D.CRIT_SCALE : kind === 'tick' ? D.TICK_SCALE : 1;
    const jitter = Math.round((this.random() - 0.5) * 2 * D.JITTER_X);
    const startY = Math.round(y + D.OFFSET_Y);
    t.setFontFamily(this.fontFamily)
      .setFontSize(D.FONT_PX)
      .setColor(color)
      .setText(label)
      .setScale(scale)
      .setAlpha(1)
      .setPosition(Math.round(x + jitter), startY)
      .setActive(true)
      .setVisible(true);
    this.active.add(t);
    this.count += 1;
    this.scene.tweens.add({
      targets: t,
      y: startY - D.RISE_PX,
      duration: D.DURATION_MS,
      ease: Phaser.Math.Easing.Quadratic.Out,
    });
    this.scene.tweens.add({
      targets: t,
      alpha: 0,
      delay: D.DURATION_MS - D.FADE_MS,
      duration: D.FADE_MS,
      onComplete: () => this.release(t),
    });
    return t;
  }

  summary(): DamageNumberSummary[] {
    return [...this.active].map((t) => ({
      text: t.text,
      x: t.x,
      y: t.y,
      alpha: t.alpha,
      scale: t.scaleX,
      color: t.style.color as string,
      font: t.style.fontFamily,
    }));
  }

  destroy(): void {
    for (const t of this.pool) {
      this.scene.tweens.killTweensOf(t);
      t.destroy();
    }
    this.pool.length = 0;
    this.active.clear();
  }

  private acquire(): Phaser.GameObjects.Text | null {
    const idle = this.pool.find((t) => !this.active.has(t));
    if (idle) return idle;
    if (this.pool.length >= FEEL.DAMAGE_TEXT.POOL) {
      // 가득 차면 가장 오래된 것을 재사용
      const oldest = this.active.values().next().value as Phaser.GameObjects.Text | undefined;
      if (!oldest) return null;
      this.scene.tweens.killTweensOf(oldest);
      this.active.delete(oldest);
      return oldest;
    }
    const t = this.scene.add
      .text(0, 0, '', {
        fontFamily: this.fontFamily,
        fontSize: `${FEEL.DAMAGE_TEXT.FONT_PX}px`,
        color: COLORS.DAMAGE_TEXT,
      })
      .setOrigin(0.5, 1)
      .setDepth(DEPTH.DAMAGE_TEXT)
      .setActive(false)
      .setVisible(false);
    this.pool.push(t);
    return t;
  }

  private release(t: Phaser.GameObjects.Text): void {
    this.active.delete(t);
    t.setActive(false).setVisible(false);
  }
}
