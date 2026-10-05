import Phaser from 'phaser';
import { GlowText } from './glow';
import { takeKey } from './keyGate';
import { accentHex, cursor as makeCursor } from './kit';
import { diamondRing, pixelDiamond } from './routeGlyph';
import { LAYOUT, SEPIA, type TextStyleName, hexToNum } from './theme';

export interface SelectLine {
  key: string;
  label: string;
  enabled: boolean;
  /** 항목 아래 작은 글씨로 보이는 설명 (evolve 등) */
  detail?: string;
  /** 49라운드: 들여쓰기 px (무기 시험장 갈래 트리) */
  indent?: number;
  /** 60라운드 §14.6: 이 줄 위에 그릴 묶음 머리글 (상점 고정·진열·리롤 등, page_faint) */
  header?: string;
  /** 60라운드 §14.4·§14.6: 못 고르는 줄의 꼬리 글 (기본 '(불가)' — 잠김·팔림) */
  note?: string;
  /** 61라운드: 화면에 보이고 누르는 단축키 (시스템 키가 'd1'·'reroll' 처럼 길 때 menuHotkeys 가 준다). 없으면 key */
  hotkey?: string;
  /** 61라운드: 희귀도 칸 수 1~4 — 라벨 오른쪽 마름모(글 대신 색·문양) */
  rarity?: number;
}

/** 선택 목록 줄 간격 (계약 1.2절: 글꼴 높이 + 4 이상) */
export const SELECT_ROW = { line: LAYOUT.row, detail: LAYOUT.detail, gap: LAYOUT.gap } as const;

export interface SelectListOptions {
  /** 종이(page) 위인지 잉크(ink)·어두운 바탕 위인지 — 글자 스타일·커서가 다르다 */
  surface?: 'page' | 'ink';
  stageIndex?: number;
  /** detail 줄바꿈 폭 (1배 px) */
  detailWrap?: number;
}

/**
 * 선택 목록: 숫자 키 / 위아래(W·S) + Enter / 마우스. 항목이 바뀌면 setLines 로 다시 그린다.
 * 선택 항목은 `page_selected`(할로 = 층 강조색) + 커서 촉, 비선택 `page_unsel`, 비활성 흐림 + '(불가)', detail 은 `page_faint`.
 * 잉크 바탕(타이틀)에서는 `ink_body` / `ink_faint` + `cursor_light`.
 */
export class SelectList {
  private items: GlowText[] = [];
  private details: (GlowText | null)[] = [];
  private headers: (GlowText | null)[] = [];
  /** 61라운드: 희귀도 마름모 */
  private marks: (Phaser.GameObjects.Graphics | null)[] = [];
  private cursorIdx = 0;
  private lines: SelectLine[] = [];
  private cursorSprite: Phaser.GameObjects.Sprite;
  private onKeyDown?: (e: KeyboardEvent) => void;
  private surface: 'page' | 'ink';
  private stageIndex: number;
  private detailWrap?: number;
  /** false 면 키·마우스 입력을 받지 않는다 (위에 다른 패널이 떠 있을 때, 53라운드 '싸우는 법' 다시 보기) */
  private enabled = true;

  constructor(
    private scene: Phaser.Scene,
    private x: number,
    private y: number,
    private onSelect: (key: string) => void,
    opts: SelectListOptions = {},
  ) {
    this.surface = opts.surface ?? 'page';
    this.stageIndex = opts.stageIndex ?? 0;
    this.detailWrap = opts.detailWrap;
    this.cursorSprite = makeCursor(scene, this.surface === 'ink').setVisible(false);
    // 동작할 때만 takeKey — 고른 결과로 다음 메뉴가 열려도 같은 키 이벤트가 다시 넘어와 또 고르지 않게 (keyGate.ts)
    this.onKeyDown = (e: KeyboardEvent) => {
      if (!this.enabled) return;
      if (e.key === 'ArrowUp' || e.key === 'w' || e.key === 'W') {
        if (takeKey(e)) this.move(-1);
      } else if (e.key === 'ArrowDown' || e.key === 's' || e.key === 'S') {
        if (takeKey(e)) this.move(1);
      } else if (e.key === 'Enter' || e.key === ' ') {
        if (takeKey(e)) this.choose(this.cursorIdx);
      } else {
        const idx = this.lines.findIndex((l) => (l.hotkey ?? l.key) === e.key);
        if (idx >= 0 && takeKey(e)) this.choose(idx);
      }
    };
    scene.input.keyboard?.on('keydown', this.onKeyDown);
  }

  /** 항목 높이 합 (패널 크기 계산용). detail 줄 수를 모르면 1줄로 센다 */
  static measure(lines: SelectLine[]): number {
    return lines.reduce(
      (h, l) =>
        h + (l.header ? SELECT_ROW.detail : 0) + SELECT_ROW.line + (l.detail ? SELECT_ROW.detail + SELECT_ROW.gap : 0),
      0,
    );
  }

  /** 실제 그린 높이 (detail 이 여러 줄로 접힌 경우 포함) */
  height(): number {
    let h = 0;
    this.items.forEach((_, i) => {
      if (this.headers[i]) h += SELECT_ROW.detail;
      h += SELECT_ROW.line;
      const d = this.details[i];
      if (d) h += d.textH + 4 + SELECT_ROW.gap;
    });
    return h;
  }

  setLines(lines: SelectLine[]): void {
    this.lines = lines;
    for (const t of this.items) t.destroy();
    for (const d of this.details) d?.destroy();
    for (const d of this.headers) d?.destroy();
    for (const g of this.marks) g?.destroy();
    this.items = [];
    this.details = [];
    this.headers = [];
    this.marks = [];
    let y = this.y;
    lines.forEach((l, i) => {
      const ind = Math.max(0, Math.round(l.indent ?? 0));
      if (l.header) {
        this.headers.push(new GlowText(this.scene, this.x + 4 + ind, y, l.header, 'page_faint'));
        y += SELECT_ROW.detail;
      } else this.headers.push(null);
      const t = new GlowText(this.scene, this.x + 14 + ind, y, this.itemLabel(l), this.unselStyle(), {
        stageIndex: this.stageIndex,
      }).makeInteractive();
      t.on('pointerover', () => this.enabled && this.setCursor(i));
      t.on('pointerdown', () => this.choose(i));
      this.items.push(t);
      this.marks.push(l.rarity ? this.rarityMarks(t, l.rarity) : null);
      y += SELECT_ROW.line;
      if (l.detail) {
        // 61라운드 플레이 점검 #13: 설명 줄 대비 — 흐림(α0.55) 대신 종이 본문 글자
        const d = new GlowText(this.scene, this.x + 14 + ind + 26, y - 2, l.detail, 'page_body', {
          wrap: this.detailWrap,
        }).makeInteractive();
        d.on('pointerover', () => this.enabled && this.setCursor(i));
        d.on('pointerdown', () => this.choose(i));
        this.details.push(d);
        y += d.textH + 4 + SELECT_ROW.gap;
      } else this.details.push(null);
    });
    this.cursorIdx = Math.min(this.cursorIdx, Math.max(0, lines.length - 1));
    this.render();
  }

  /** 가장 넓은 항목의 픽셀 폭 (커서 자리·라벨·설명 포함) */
  maxWidth(): number {
    let w = 0;
    for (const t of this.items) w = Math.max(w, t.x - this.x + t.textW + 4);
    for (const d of this.details) if (d) w = Math.max(w, d.x - this.x + d.textW + 4);
    for (const d of this.headers) if (d) w = Math.max(w, d.x - this.x + d.textW + 4);
    return w;
  }

  /** 목록 원점을 옮긴다 (패널 폭을 항목에 맞춘 뒤 재배치할 때) */
  setPosition(x: number, y: number): this {
    const dx = x - this.x;
    const dy = y - this.y;
    this.x = x;
    this.y = y;
    for (const t of this.items) t.setPosition(t.x + dx, t.y + dy);
    for (const g of this.marks) g?.setPosition(g.x + dx, g.y + dy);
    for (const d of this.details) d?.setPosition(d.x + dx, d.y + dy);
    for (const d of this.headers) d?.setPosition(d.x + dx, d.y + dy);
    this.render();
    return this;
  }

  setDepth(d: number): this {
    for (const t of this.items) t.setDepth(d);
    for (const t of this.details) t?.setDepth(d);
    for (const t of this.headers) t?.setDepth(d);
    for (const g of this.marks) g?.setDepth(d);
    this.cursorSprite.setDepth(d + 1);
    return this;
  }

  /** 60라운드: 커서가 옮겨질 때 알림 (접은 설명을 목록 아래 한 칸에 보일 때) */
  setOnCursor(fn: ((index: number) => void) | null): this {
    this.onCursor = fn ?? undefined;
    this.onCursor?.(this.cursorIdx);
    return this;
  }
  private onCursor?: (index: number) => void;

  /** 입력 받기 켜기·끄기 */
  setEnabled(on: boolean): this {
    this.enabled = on;
    return this;
  }

  /** 현재 커서 위치 (같은 메뉴를 다시 그릴 때 유지용, 47라운드) */
  cursorIndex(): number {
    return this.cursorIdx;
  }

  /** 커서를 옮긴다 (범위 밖이면 끝으로) */
  setCursorIndex(i: number): this {
    if (!this.lines.length) return this;
    this.setCursor(Math.max(0, Math.min(this.lines.length - 1, i)));
    return this;
  }

  private itemLabel(l: SelectLine): string {
    const k = l.hotkey ?? l.key;
    return `${k ? `[${k}] ` : ''}${l.label}${l.enabled ? '' : `  ${l.note ?? '(불가)'}`}`;
  }

  /** 61라운드: 희귀도 = 라벨 오른쪽 작은 마름모 4칸 (켜진 칸 층 강조 22, 전설은 25, 꺼진 칸 세피아 S3 테) */
  private rarityMarks(t: GlowText, rank: number): Phaser.GameObjects.Graphics {
    const g = this.scene.add.graphics();
    const on = hexToNum(accentHex(this.scene, this.stageIndex, rank >= 4 ? 25 : 22));
    const off = hexToNum(SEPIA[3]);
    const r = 2;
    let cx = t.x + t.displayWidth + 4 + r;
    const cy = t.y + 8;
    for (let k = 0; k < 4; k++) {
      if (k < rank) pixelDiamond(g, r, on, 1, cx, cy);
      else diamondRing(g, r, 1, off, 1, cx, cy);
      cx += r * 2 + 3;
    }
    return g;
  }
  private selStyle(): TextStyleName {
    return this.surface === 'page' ? 'page_selected' : 'ink_body';
  }
  private unselStyle(): TextStyleName {
    return this.surface === 'page' ? 'page_unsel' : 'ink_faint';
  }

  private move(d: number): void {
    if (!this.lines.length) return;
    this.setCursor((this.cursorIdx + d + this.lines.length) % this.lines.length);
  }

  private setCursor(i: number): void {
    const moved = i !== this.cursorIdx;
    this.cursorIdx = i;
    this.render();
    if (moved) this.onCursor?.(i);
  }

  private choose(i: number): void {
    if (!this.enabled) return;
    const l = this.lines[i];
    if (l && l.enabled) this.onSelect(l.key);
  }

  private render(): void {
    this.lines.forEach((l, i) => {
      const sel = i === this.cursorIdx;
      const t = this.items[i];
      t.setGlowStyle(!l.enabled ? 'page_faint' : sel ? this.selStyle() : this.unselStyle());
      t.setAlpha(l.enabled ? 1 : LAYOUT.disabledAlpha);
      this.details[i]?.setAlpha(l.enabled ? (sel ? 1 : 0.8) : LAYOUT.disabledAlpha);
      if (sel) {
        // 커서 피벗 (4,4): 글자 상자 왼쪽에서 10px, 세로 가운데(글자 12px + 링 2)
        this.cursorSprite.setVisible(true).setPosition(t.x - 6, t.y + 8);
      }
    });
    if (!this.lines.length) this.cursorSprite.setVisible(false);
  }

  destroy(): void {
    if (this.onKeyDown) this.scene.input.keyboard?.off('keydown', this.onKeyDown);
    for (const t of this.items) t.destroy();
    for (const d of this.details) d?.destroy();
    for (const d of this.headers) d?.destroy();
    for (const g of this.marks) g?.destroy();
    this.cursorSprite.destroy();
    this.items = [];
    this.details = [];
    this.headers = [];
  }
}
