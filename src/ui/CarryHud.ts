import Phaser from 'phaser';
import { GlowText } from './glow';
import { carryKey, type CarryView } from './carryView';
import { KeyCap } from './keycap';
import { fill, r53Text } from './text';

/** 키 · 상태 · 첫 타 사이 간격 */
const GAP = 5;

/**
 * 53라운드 F 넣기/뽑기 표시 (51라운드 Q4). HUD 하단 묶음 3행 오른쪽 끝에 작게: [F] 넣음 · 발도 준비 / [F] 뽑음.
 * 넣은 상태는 ink_body, 첫 타 준비는 ink_accent(층 강조), 뽑은 상태는 키·글 모두 흐림. 오른쪽 끝(`right`) 고정.
 * Container 하나라 하단 묶음과 함께 setY 로 움직인다.
 */
export class CarryChip extends Phaser.GameObjects.Container {
  private cap: KeyCap;
  private stateText: GlowText;
  private readyText: GlowText;
  private lastSig = '#init';

  constructor(
    scene: Phaser.Scene,
    private right: number,
    y: number,
    stageIndex: number,
  ) {
    super(scene, 0, y);
    this.cap = new KeyCap(scene, 0, 0, 'F', true);
    this.stateText = new GlowText(scene, 0, 0, '', 'ink_faint');
    this.readyText = new GlowText(scene, 0, 0, '', 'ink_accent', { stageIndex });
    this.add([this.cap, this.stateText, this.readyText]);
    scene.add.existing(this);
    this.setVisible(false);
  }

  setStageIndex(i: number): void {
    this.readyText.setStageIndex(i);
  }

  render(v: CarryView | null): void {
    const k = carryKey(v);
    if (k === this.lastSig) return;
    this.lastSig = k;
    if (!v) {
      this.setVisible(false);
      return;
    }
    this.setVisible(true);
    this.cap.setLabel(v.key).setFaint(!v.sheathed);
    this.stateText
      .setText(r53Text(v.sheathed ? 'carrySheathed' : 'carryDrawn'))
      .setGlowStyle(v.sheathed ? 'ink_body' : 'ink_faint');
    this.readyText.setText(v.ready ? fill(r53Text('carryReady'), { name: v.ready }) : '').setVisible(Boolean(v.ready));
    // 오른쪽 끝에서 왼쪽으로: 첫 타 → 상태 → 키 (글 상자·키 모두 높이 16, 위쪽을 맞춘다)
    let x = 0;
    this.cap.setPosition(x, 0);
    x += this.cap.width + GAP - 2;
    this.stateText.setPosition(x, 0);
    x += this.stateText.displayWidth;
    if (v.ready) {
      x += GAP - 2;
      this.readyText.setPosition(x, 0);
      x += this.readyText.displayWidth;
    }
    this.setX(Math.round(this.right - x));
  }
}
