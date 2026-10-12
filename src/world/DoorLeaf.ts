/**
 * 62 루프 2 F (art §31-10): 외벽 문 널문 그림 — 닫힘 덮개 `door_<side>_closed` · 열림 시트 `door_<side>_open`(가로 4칸,
 * 0 = 닫힘 → 3 = 다 열림, 칸마다 시간). 문 그림(BorderView 문 조각)과 같은 원점·배율, depth DOORS.DEPTH_BARRIER.
 * 열림 = 시트 재생, 닫힘 = 거꾸로. 시트가 없으면 닫힘 덮개를 옅게 걷는다(OPEN_MS).
 * 시스템 E 의 도형 막힘 판(어둠 + 판자 둘 — DoorView)을 대신한다.
 */
import Phaser from 'phaser';
import { DOORS } from '../core/Constants';

export interface DoorLeafFrames {
  /** 텍스처 프레임 이름 (0 = 닫힘 → 마지막 = 다 열림) */
  names: string[];
  durationsMs: number[];
}

export class DoorLeaf {
  private open = false;
  private readonly timers: Phaser.Time.TimerEvent[] = [];
  private tween: Phaser.Tweens.Tween | null = null;

  constructor(
    private readonly scene: Phaser.Scene,
    readonly image: Phaser.GameObjects.Image,
    /** 열림 시트 (없으면 닫힘 덮개 하나 — 알파로 걷는다) */
    private readonly frames: DoorLeafFrames | null,
    open: boolean,
  ) {
    this.set(open, false);
  }

  get isOpen(): boolean {
    return this.open;
  }

  /** 열기·닫기 (animate false = 바로 그 칸) */
  set(open: boolean, animate: boolean): void {
    if (open === this.open && animate) return;
    this.open = open;
    this.stop();
    const f = this.frames;
    if (!f) {
      const to = open ? 0 : 1;
      if (!animate) {
        this.image.setAlpha(to).setVisible(!open);
        return;
      }
      this.image.setVisible(true);
      this.tween = this.scene.tweens.add({
        targets: this.image,
        alpha: to,
        duration: DOORS.OPEN_MS,
        ease: open ? 'Cubic.easeIn' : 'Cubic.easeOut',
        onComplete: () => this.image.setVisible(!open),
      });
      return;
    }
    const last = f.names.length - 1;
    if (!animate) {
      this.image.setFrame(f.names[open ? last : 0]);
      return;
    }
    // 열림 0 → last (칸 i 를 durations[i] 동안) · 닫힘 last → 0 (거꾸로)
    const order = open ? f.names.map((_, i) => i) : f.names.map((_, i) => last - i);
    let at = 0;
    this.image.setFrame(f.names[order[0]]);
    for (let n = 1; n < order.length; n++) {
      at += f.durationsMs[order[n - 1]] ?? 100;
      const idx = order[n];
      this.timers.push(this.scene.time.delayedCall(at, () => this.image.setFrame(f.names[idx])));
    }
  }

  private stop(): void {
    for (const t of this.timers) t.remove(false);
    this.timers.length = 0;
    this.tween?.remove();
    this.tween = null;
  }

  destroy(): void {
    this.stop();
  }
}

/** 열림 시트 텍스처에 칸 프레임을 더한다 (이미 있으면 그대로). 텍스처 px = 논리 px ÷ pixelScale */
export function addDoorSheetFrames(
  textures: Phaser.Textures.TextureManager,
  key: string,
  frames: number,
  frameWidthTex: number,
  frameHeightTex: number,
): string[] {
  const tex = textures.get(key);
  const names: string[] = [];
  for (let i = 0; i < frames; i++) {
    const name = `door${i}`;
    if (!tex.has(name))
      tex.add(name, 0, Math.round(i * frameWidthTex), 0, Math.round(frameWidthTex), Math.round(frameHeightTex));
    names.push(name);
  }
  return names;
}
