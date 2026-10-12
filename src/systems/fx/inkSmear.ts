/**
 * 62 루프 2 시스템 C (P16 §3 · 점검 P1-7) 사망 먹 번짐 화면 효과 — 일기장 위에 먹이 떨어져 번지듯 화면이 덮인다.
 * 화면 고정(scrollFactor 0) Graphics 한 장에 논리 960×540 좌표로 그린다(`screenFixed` — 월드 카메라 확대와 무관).
 * 시간은 씬 update 이벤트(실시간)로 잰다 — Game.update 가 사망 뒤 멈춰도 돈다. 씬이 끝나면 스스로 지운다.
 */
import Phaser from 'phaser';
import { DEPTH, INK_SMEAR } from '../../core/Constants';
import { screenFixed } from '../display';
import { easeOut, inkBlobs, type InkBlob } from './inkBlobs';

export class InkSmear {
  private readonly gfx: Phaser.GameObjects.Graphics;
  private blobs: InkBlob[] = [];
  private start = 0;
  private ms = 1;
  private active = false;
  /** 디버그: 마지막 진행 비 */
  progress = 0;

  constructor(private readonly scene: Phaser.Scene) {
    this.gfx = scene.add
      .graphics()
      .setScrollFactor(0)
      .setDepth(DEPTH.SCREEN_FX + INK_SMEAR.DEPTH_ABOVE_SCREEN_FX)
      .setVisible(false);
    scene.events.on(Phaser.Scenes.Events.UPDATE, this.tick, this);
    scene.events.once(Phaser.Scenes.Events.SHUTDOWN, this.destroy, this);
  }

  /** 시작: center = 주인공 논리 화면 자리 · ms = 번지는 시간 */
  play(center: { x: number; y: number }, ms: number, rnd: () => number = Math.random): void {
    this.blobs = inkBlobs(center, rnd);
    this.start = performance.now();
    this.ms = Math.max(1, ms);
    this.active = true;
    this.gfx.setVisible(true);
    this.draw(0);
  }

  private tick(): void {
    if (!this.active) return;
    const t = Math.min(1, (performance.now() - this.start) / this.ms);
    this.draw(t);
    // 끝까지 번진 뒤에는 덮인 채로 두고 더 그리지 않는다 (결과 화면이 이어받는다)
    if (t >= 1) this.active = false;
  }

  private draw(t: number): void {
    const I = INK_SMEAR;
    this.progress = t;
    const cam = this.scene.cameras.main;
    const at = screenFixed(cam, 0, 0);
    const g = this.gfx.clear().setPosition(at.x, at.y).setScale(at.scale);
    // 번진 테두리(세피아)를 모두 먼저, 속(먹)을 그 위에 — 둘 다 불투명이라 방울이 겹쳐도 고리 무늬가 생기지 않는다
    for (const [color, spread] of [
      [I.EDGE_COLOR, I.EDGE_SPREAD],
      [I.COLOR, 1],
    ] as const) {
      g.fillStyle(color, 1);
      for (const b of this.blobs) {
        const k = b.delay >= 1 ? 0 : Math.max(0, (t - b.delay) / (1 - b.delay));
        if (k <= 0) continue;
        const r = b.r * easeOut(k);
        g.fillCircle(b.x, b.y, r * spread);
        for (const l of b.lobes)
          g.fillCircle(b.x + Math.cos(l.a) * r * l.d, b.y + Math.sin(l.a) * r * l.d, r * l.r * spread);
      }
    }
  }

  get playing(): boolean {
    return this.active;
  }

  destroy(): void {
    this.active = false;
    this.scene.events.off(Phaser.Scenes.Events.UPDATE, this.tick, this);
    this.gfx.destroy();
  }
}
