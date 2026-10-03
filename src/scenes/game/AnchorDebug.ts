/**
 * 52라운드 v3 앵커 확인용 디버그 표시 (`?anchors`): 몸 오른손(초록)·왼손(파랑)·무기 쥔 손(빨강)을 작은 점으로.
 * 아트 handAnchors·gripAnchors 와 실제 화면 정렬을 눈으로 맞춰 보는 용도 — 게임 판정과 무관
 */
import Phaser from 'phaser';
import { DEPTH } from '../../core/Constants';
import type { Player } from '../../objects/Player';

const COLORS = { handR: 0x40ff60, handL: 0x40a0ff, grip: 0xff4040 } as const;
/** 점 반지름 (월드 단위 — v3 도트 1개 = 0.25) */
const DOT = 0.5;

export class AnchorDebug {
  private readonly g: Phaser.GameObjects.Graphics;

  constructor(scene: Phaser.Scene) {
    this.g = scene.add.graphics().setDepth(DEPTH.DEBUG);
  }

  update(player: Player): void {
    const a = player.overlay.anchors();
    this.g.clear();
    for (const k of ['handR', 'handL', 'grip'] as const) {
      const p = a[k];
      if (!p) continue;
      this.g.fillStyle(COLORS[k], 1);
      this.g.fillRect(p.x - DOT / 2, p.y - DOT / 2, DOT, DOT);
    }
  }

  destroy(): void {
    this.g.destroy();
  }
}
