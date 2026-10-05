import Phaser from 'phaser';

export interface CardTiming {
  inMs: number;
  holdMs: number;
  outMs: number;
  /** 나타날 때 위에서 내려오는 px (정수, 없으면 0) */
  drop?: number;
}

/**
 * 61라운드 단계 2·3 잠깐 떴다 사라지는 카드 (보스 이름·국면·파훼·처치 카드, 신규 적 소개) 공용.
 * Container 하나를 나타남(알파 + 내려옴) → 머묾 → 사라짐 순으로 돌리고, 끝나면 부수고 `onDone`.
 * `cancel()` 은 바로 부순다(onDone 없음). Container 하위 클래스가 아니므로 `w`/`z` 이름 문제와 무관.
 */
export class TimedCard {
  private timer?: Phaser.Time.TimerEvent;
  private done = false;

  constructor(
    private scene: Phaser.Scene,
    readonly box: Phaser.GameObjects.Container,
    t: CardTiming,
    private onDone?: () => void,
  ) {
    const y = box.y;
    const drop = t.drop ?? 0;
    box.setAlpha(0).setY(y - drop);
    scene.tweens.add({ targets: box, alpha: 1, y, duration: t.inMs, ease: drop ? 'Quad.easeIn' : 'Linear' });
    this.timer = scene.time.delayedCall(t.inMs + t.holdMs, () => {
      scene.tweens.add({
        targets: box,
        alpha: 0,
        duration: t.outMs,
        onComplete: () => this.finish(true),
      });
    });
  }

  get alive(): boolean {
    return !this.done;
  }

  cancel(): void {
    this.finish(false);
  }

  private finish(notify: boolean): void {
    if (this.done) return;
    this.done = true;
    this.timer?.remove();
    this.timer = undefined;
    this.scene.tweens.killTweensOf([this.box, ...this.box.list]);
    this.box.destroy();
    if (notify) this.onDone?.();
  }
}

/** 전체 시간 (ms) */
export function cardTotalMs(t: CardTiming): number {
  return t.inMs + t.holdMs + t.outMs;
}
