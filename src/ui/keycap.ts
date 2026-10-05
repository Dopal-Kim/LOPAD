import Phaser from 'phaser';
import { GlowText } from './glow';
import { GRAY, hexToNum } from './theme';

/** 키 모양 크기 (53라운드): 높이 16, 글 양옆 여백 4, 최소 폭 16 */
export const KEYCAP = { h: 16, padX: 4, minW: 16 } as const;

/**
 * 키 아이콘 (53라운드 F 표시·튜토리얼 안내). 스킬 버튼 규약대로 Container → Graphics → 글자.
 * 잉크 바탕 위: 면 G02 · 테두리 G08(흐림이면 G05) · 아래 두께 G01. 글은 ink_body(흐림이면 ink_faint).
 * 좌표는 왼쪽 위 기준 정수. `width` 는 키 폭.
 */
export class KeyCap extends Phaser.GameObjects.Container {
  private g: Phaser.GameObjects.Graphics;
  private label: GlowText;
  private faint = false;
  /** 61라운드: 넓은 키(Space)처럼 글보다 넓게 그릴 최소 폭 */
  private minW: number = KEYCAP.minW;

  constructor(scene: Phaser.Scene, x: number, y: number, text: string, faint = false) {
    super(scene, x, y);
    this.g = scene.add.graphics();
    this.label = new GlowText(scene, 0, 0, text, faint ? 'ink_faint' : 'ink_body');
    this.add([this.g, this.label]);
    this.faint = faint;
    this.redraw();
    scene.add.existing(this);
  }

  setFaint(faint: boolean): this {
    if (faint === this.faint) return this;
    this.faint = faint;
    this.label.setGlowStyle(faint ? 'ink_faint' : 'ink_body');
    this.redraw();
    return this;
  }

  /** 61라운드 키캡 안내: 최소 폭 (넓은 키) */
  setMinWidth(w: number): this {
    this.minW = Math.max(KEYCAP.minW, Math.round(w));
    this.redraw();
    return this;
  }

  setLabel(text: string): this {
    this.label.setText(text);
    this.redraw();
    return this;
  }

  private redraw(): void {
    const w = Math.max(this.minW, this.label.textW + KEYCAP.padX * 2);
    const h = KEYCAP.h;
    const g = this.g;
    g.clear();
    g.fillStyle(hexToNum(GRAY[1]), 1).fillRect(0, 1, w, h);
    g.fillStyle(hexToNum(GRAY[2]), 1).fillRect(0, 0, w, h - 1);
    g.lineStyle(1, hexToNum(this.faint ? GRAY[5] : GRAY[8]), 1).strokeRect(0.5, 0.5, w - 1, h - 1);
    // 글 상자(링 2px 포함)를 키 가운데로
    this.label.setPosition(
      Math.round((w - this.label.displayWidth) / 2),
      Math.round((h - 1 - this.label.displayHeight) / 2),
    );
    this.setSize(w, h);
  }
}
