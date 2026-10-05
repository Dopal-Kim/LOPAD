/**
 * 데미지 숫자 (35라운드 1단계). 시스템 씬이 월드 좌표에 직접 그린다(HUD 가 아님).
 * - 적중점 위에서 떠올라(RISE_PX) 사라진다(DURATION_MS, 끝 FADE_MS 페이드). Text 풀(POOL)로 재사용.
 * - 일반 = G13 흰색, 치명타 = 층 강조 램프 light1 + '!' + 2배(39라운드, 정수 배율), 플레이어 피격 = G11 + '-', 지속 피해 틱 = 0.8배.
 * - 글꼴 Galmuri11 (34라운드 규칙, 11px). 로드 전·실패면 monospace.
 * - 61라운드 플레이 점검: 같은 자리 짧은 간격 피해는 합쳐 다시 띄우고, 아니면 비켜 띄운다(`damageNumberLayout`, FEEL.DAMAGE_TEXT.STACK).
 *   설정 §15 `damageNumbers`(= feelSettings.numbers)가 꺼지면 새 숫자를 띄우지 않고 떠 있는 것도 지운다.
 */
import Phaser from 'phaser';
import { COLORS, DEPTH, FEEL } from '../../core/Constants';
import { PALETTE } from '../../data';
import { rampFor } from '../palette';
import { fontFamilyOr } from '../fonts';
import { feelSettings } from '../feel';
import { numberLabel, placeNumber, type PlacedNumber } from './damageNumberLayout';

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
  /** 61라운드: 떠 있는 숫자의 원점·양 (합치기·비켜 띄우기) */
  private readonly placed = new Map<Phaser.GameObjects.Text, PlacedNumber & { startY: number }>();
  private nextId = 1;
  /** 디버그: 합친 횟수 */
  merged = 0;
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
    if (!feelSettings.numbers) {
      if (this.active.size > 0) for (const t of [...this.active]) this.release(t);
      return null;
    }
    const D = FEEL.DAMAGE_TEXT;
    const now = this.scene.time.now;
    const place = placeNumber([...this.placed.values()], { x, y, kind, amount, now }, D.STACK, D.DURATION_MS);
    if (place.merge) {
      const t = [...this.placed.entries()].find(([, p]) => p.id === place.id)?.[0];
      const p = t ? this.placed.get(t) : undefined;
      if (t && p) {
        p.amount = place.amount;
        p.kind = place.kind;
        p.at = now;
        this.merged += 1;
        this.count += 1;
        this.style(t, place.kind, place.amount);
        t.setAlpha(1).setY(p.startY);
        this.animate(t, p.startY, true);
        return t;
      }
    }
    const t = this.acquire();
    if (!t) return null;
    const dx = place.merge ? 0 : place.dx;
    const dy = place.merge ? 0 : place.dy;
    const jitter = dx === 0 ? Math.round((this.random() - 0.5) * 2 * D.JITTER_X) : 0;
    const startY = Math.round(y + D.OFFSET_Y + dy);
    this.style(t, kind, amount);
    t.setAlpha(1)
      .setPosition(Math.round(x + jitter + dx), startY)
      .setActive(true)
      .setVisible(true);
    this.active.add(t);
    this.placed.set(t, { id: this.nextId++, ox: x, oy: y, at: now, kind, amount, startY });
    this.count += 1;
    this.animate(t, startY, false);
    return t;
  }

  private style(t: Phaser.GameObjects.Text, kind: DamageKind, amount: number): void {
    const D = FEEL.DAMAGE_TEXT;
    const color = kind === 'crit' ? this.critColor : kind === 'player' ? COLORS.DAMAGE_TEXT_PLAYER : COLORS.DAMAGE_TEXT;
    const scale = kind === 'crit' ? D.CRIT_SCALE : kind === 'tick' ? D.TICK_SCALE : 1;
    t.setFontFamily(this.fontFamily)
      .setFontSize(D.FONT_PX)
      .setColor(color)
      .setText(numberLabel(kind, amount))
      .setScale(scale);
  }

  /** 떠오름 + 끝 페이드 (합친 숫자는 처음부터 다시, 짧게 커졌다 돌아온다) */
  private animate(t: Phaser.GameObjects.Text, startY: number, pop: boolean): void {
    const D = FEEL.DAMAGE_TEXT;
    this.scene.tweens.killTweensOf(t);
    if (pop) {
      const s = t.scaleX;
      t.setScale(s * D.STACK.POP_SCALE);
      this.scene.tweens.add({ targets: t, scaleX: s, scaleY: s, duration: D.STACK.POP_MS });
    }
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
    this.placed.clear();
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
      this.placed.delete(oldest);
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
    this.scene.tweens.killTweensOf(t);
    this.active.delete(t);
    this.placed.delete(t);
    t.setActive(false).setVisible(false);
  }
}
