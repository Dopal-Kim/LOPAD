import Phaser from 'phaser';
import { COLORS, DEPTH } from '../core/Constants';

export interface MenuLine {
  key: string; // '1'..'9'
  label: string;
  enabled: boolean;
}

/**
 * 시스템 파트 임시 텍스트 메뉴 (숫자 키 선택). HUD/정식 메뉴는 UI 파트 소유이며
 * 이 클래스는 보상·상점 흐름을 검증하기 위한 플레이스홀더다.
 */
export class TextMenu {
  private text?: Phaser.GameObjects.Text;
  private onKey?: (e: KeyboardEvent) => void;

  constructor(private scene: Phaser.Scene) {}

  get isOpen(): boolean {
    return Boolean(this.text);
  }

  open(title: string, lines: MenuLine[], onSelect: (key: string) => void, footer = ''): void {
    this.close();
    const body = lines.map((l) => `[${l.key}] ${l.label}${l.enabled ? '' : '  (불가)'}`).join('\n');
    this.text = this.scene.add
      .text(
        this.scene.scale.width / 2,
        this.scene.scale.height / 2,
        `${title}\n\n${body}${footer ? `\n\n${footer}` : ''}`,
        {
          font: '11px monospace',
          color: COLORS.GAMEOVER_TEXT,
          backgroundColor: '#000000c0',
          padding: { x: 10, y: 8 },
          align: 'left',
        },
      )
      .setOrigin(0.5)
      .setScrollFactor(0)
      .setDepth(DEPTH.DEBUG);
    this.onKey = (e: KeyboardEvent) => {
      const line = lines.find((l) => l.key === e.key);
      if (line && line.enabled) onSelect(line.key);
    };
    this.scene.input.keyboard?.on('keydown', this.onKey);
  }

  close(): void {
    if (this.onKey) this.scene.input.keyboard?.off('keydown', this.onKey);
    this.onKey = undefined;
    this.text?.destroy();
    this.text = undefined;
  }
}
