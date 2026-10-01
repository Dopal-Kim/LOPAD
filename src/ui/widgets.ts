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

export interface SelectLine {
  key: string;
  label: string;
  enabled: boolean;
  /** 항목 아래 작은 글씨로 보이는 설명 (evolve 등) */
  detail?: string;
}

/** 선택 목록 줄 간격 */
export const SELECT_ROW = { line: 16, detail: 13, gap: 4 } as const;

/**
 * 선택 목록: 숫자 키 / 위아래 + Enter / 마우스 클릭. 항목이 바뀌면 setLines 로 다시 그린다.
 * detail 이 있는 항목은 아래에 흐린 작은 글씨로 설명을 붙이고, 비활성 항목은 전체를 흐리게 그린다.
 */
export class SelectList {
  private items: Phaser.GameObjects.Text[] = [];
  private details: (Phaser.GameObjects.Text | null)[] = [];
  private cursor = 0;
  private lines: SelectLine[] = [];
  private onKeyDown?: (e: KeyboardEvent) => void;

  constructor(
    private scene: Phaser.Scene,
    private x: number,
    private y: number,
    private onSelect: (key: string) => void,
    private lineHeight: number = SELECT_ROW.line,
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

  /** 항목 높이 합 (패널 크기 계산용). lines 를 주면 그리기 전에 계산할 수 있다 */
  static measure(lines: SelectLine[], lineHeight: number = SELECT_ROW.line): number {
    return lines.reduce((h, l) => h + lineHeight + (l.detail ? SELECT_ROW.detail + SELECT_ROW.gap : 0), 0);
  }

  setLines(lines: SelectLine[]): void {
    this.lines = lines;
    for (const t of this.items) t.destroy();
    for (const d of this.details) d?.destroy();
    this.items = [];
    this.details = [];
    let y = this.y;
    lines.forEach((l, i) => {
      const t = this.scene.add
        .text(this.x, y, '', { font: THEME.font, color: THEME.text })
        .setInteractive({ useHandCursor: true });
      t.on('pointerover', () => this.setCursor(i));
      t.on('pointerdown', () => this.choose(i));
      this.items.push(t);
      y += this.lineHeight;
      if (l.detail) {
        const d = this.scene.add.text(this.x + 26, y - 2, l.detail, { font: THEME.fontSmall, color: THEME.textDim });
        d.setInteractive({ useHandCursor: true });
        d.on('pointerover', () => this.setCursor(i));
        d.on('pointerdown', () => this.choose(i));
        this.details.push(d);
        y += SELECT_ROW.detail + SELECT_ROW.gap;
      } else this.details.push(null);
    });
    this.cursor = Math.min(this.cursor, Math.max(0, lines.length - 1));
    this.render();
  }

  /** 가장 넓은 항목의 픽셀 폭 (라벨·설명 포함) */
  maxWidth(): number {
    let w = 0;
    for (const t of this.items) w = Math.max(w, t.width);
    for (const d of this.details) if (d) w = Math.max(w, d.x - this.x + d.width);
    return w;
  }

  /** 목록 원점을 옮긴다 (패널 폭을 항목에 맞춘 뒤 재배치할 때) */
  setPosition(x: number, y: number): this {
    const dx = x - this.x;
    const dy = y - this.y;
    this.x = x;
    this.y = y;
    for (const t of this.items) t.setPosition(t.x + dx, t.y + dy);
    for (const d of this.details) d?.setPosition(d.x + dx, d.y + dy);
    return this;
  }

  setDepth(d: number): this {
    for (const t of this.items) t.setDepth(d);
    for (const t of this.details) t?.setDepth(d);
    return this;
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
      this.items[i]
        .setText(`${sel ? '▶' : ' '} [${l.key}] ${l.label}${l.enabled ? '' : '  (불가)'}`)
        .setColor(color)
        .setAlpha(l.enabled ? 1 : THEME.disabledAlpha);
      this.details[i]?.setAlpha(l.enabled ? (sel ? 1 : 0.8) : THEME.disabledAlpha);
    });
  }

  destroy(): void {
    if (this.onKeyDown) this.scene.input.keyboard?.off('keydown', this.onKeyDown);
    for (const t of this.items) t.destroy();
    for (const d of this.details) d?.destroy();
    this.items = [];
    this.details = [];
  }
}
