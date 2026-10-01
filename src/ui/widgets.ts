import Phaser from 'phaser';
import { THEME } from './theme';

/** 패널 사각형 */
export function panel(
  scene: Phaser.Scene,
  x: number,
  y: number,
  w: number,
  h: number,
  alpha = THEME.panelAlpha,
): Phaser.GameObjects.Graphics {
  const g = scene.add.graphics();
  g.fillStyle(THEME.panel, alpha);
  g.fillRect(x, y, w, h);
  g.lineStyle(1, THEME.border, 1);
  g.strokeRect(x + 0.5, y + 0.5, w - 1, h - 1);
  return g;
}

/** 수평 게이지 (0..1) */
export class Bar {
  private g: Phaser.GameObjects.Graphics;
  constructor(
    scene: Phaser.Scene,
    private x: number,
    private y: number,
    private w: number,
    private h: number,
    private color: number,
    private back: number,
  ) {
    this.g = scene.add.graphics();
  }

  set(ratio: number, color = this.color): this {
    const r = Math.max(0, Math.min(1, ratio));
    this.g.clear();
    this.g.fillStyle(this.back, 1);
    this.g.fillRect(this.x, this.y, this.w, this.h);
    this.g.fillStyle(color, 1);
    this.g.fillRect(this.x, this.y, Math.round(this.w * r), this.h);
    this.g.lineStyle(1, THEME.border, 1);
    this.g.strokeRect(this.x + 0.5, this.y + 0.5, this.w - 1, this.h - 1);
    return this;
  }

  setDepth(d: number): this {
    this.g.setDepth(d);
    return this;
  }

  setVisible(v: boolean): this {
    this.g.setVisible(v);
    return this;
  }

  destroy(): void {
    this.g.destroy();
  }
}

export function label(
  scene: Phaser.Scene,
  x: number,
  y: number,
  text: string,
  font = THEME.font,
  color: string = THEME.text,
): Phaser.GameObjects.Text {
  return scene.add.text(x, y, text, { font, color });
}

/**
 * 선택 목록: 숫자 키 / 위아래 + Enter / 마우스 클릭. 항목이 바뀌면 setLines 로 다시 그린다.
 */
export class SelectList {
  private items: Phaser.GameObjects.Text[] = [];
  private cursor = 0;
  private lines: { key: string; label: string; enabled: boolean }[] = [];
  private onKeyDown?: (e: KeyboardEvent) => void;

  constructor(
    private scene: Phaser.Scene,
    private x: number,
    private y: number,
    private onSelect: (key: string) => void,
    private lineHeight = 16,
  ) {
    this.onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowUp' || e.key === 'w' || e.key === 'W') this.move(-1);
      else if (e.key === 'ArrowDown' || e.key === 's' || e.key === 'S') this.move(1);
      else if (e.key === 'Enter' || e.key === ' ') this.choose(this.cursor);
      else {
        const idx = this.lines.findIndex((l) => l.key === e.key);
        if (idx >= 0) this.choose(idx);
      }
    };
    scene.input.keyboard?.on('keydown', this.onKeyDown);
  }

  setLines(lines: { key: string; label: string; enabled: boolean }[]): void {
    this.lines = lines;
    for (const t of this.items) t.destroy();
    this.items = lines.map((_l, i) => {
      const t = this.scene.add
        .text(this.x, this.y + i * this.lineHeight, '', { font: THEME.font, color: THEME.text })
        .setInteractive({ useHandCursor: true });
      t.on('pointerover', () => this.setCursor(i));
      t.on('pointerdown', () => this.choose(i));
      return t;
    });
    this.cursor = Math.min(this.cursor, Math.max(0, lines.length - 1));
    this.render();
  }

  private move(d: number): void {
    if (!this.lines.length) return;
    this.setCursor((this.cursor + d + this.lines.length) % this.lines.length);
  }

  private setCursor(i: number): void {
    this.cursor = i;
    this.render();
  }

  private choose(i: number): void {
    const l = this.lines[i];
    if (l && l.enabled) this.onSelect(l.key);
  }

  private render(): void {
    this.lines.forEach((l, i) => {
      const sel = i === this.cursor;
      const color = !l.enabled ? THEME.textDim : sel ? '#fff0a0' : THEME.text;
      this.items[i].setText(`${sel ? '▶' : ' '} [${l.key}] ${l.label}${l.enabled ? '' : '  (불가)'}`).setColor(color);
    });
  }

  destroy(): void {
    if (this.onKeyDown) this.scene.input.keyboard?.off('keydown', this.onKeyDown);
    for (const t of this.items) t.destroy();
  }
}
