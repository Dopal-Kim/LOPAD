import Phaser from 'phaser';
import { UI_SCREEN } from '../contract/ui';
import { debugExpose } from './debug';
import { edgeArrow, waveEdges } from './eventView';
import { accentHex } from './kit';
import { GRAY, hexToNum } from './theme';
import { WAVE_ARROW as A } from './themeLoop2F';

/**
 * 62 루프 2 UI F (계약 D P2-10 `UiEnemyIncoming.side`): 무리가 들어오는 쪽 화면 가장자리에 작은 화살촉(바깥을 가리킴) — 몇 번 깜빡이고 사라진다.
 * 위쪽은 위 가운데 알림 줄(위 끝 40) 보다 위 · 아래쪽은 화면 아래 끝 — '주의' 카드와 겹치지 않는다. flank = 양옆 · around = 사방.
 */
export class WaveArrows {
  private g?: Phaser.GameObjects.Graphics;
  private timer?: Phaser.Time.TimerEvent;

  constructor(private scene: Phaser.Scene) {}

  show(side: unknown, si: number): void {
    const edges = waveEdges(typeof side === 'string' ? side : null);
    if (!edges.length) return;
    this.clear();
    const sc = this.scene;
    const g = sc.add.graphics().setDepth(A.depth);
    const fill = hexToNum(accentHex(sc, si, 22));
    const ink = hexToNum(GRAY[0]);
    const pts = edges.map((e) => edgeArrow(e, UI_SCREEN.WIDTH, UI_SCREEN.HEIGHT, A.inset, A.topY, A.bottomInset));
    for (const p of pts) chevron(g, p.x, p.y, p.angle, A.size, fill, ink);
    this.g = g;
    let n = 0;
    this.timer = sc.time.addEvent({
      delay: A.blinkMs,
      repeat: Math.max(0, Math.floor(A.holdMs / A.blinkMs) - 1),
      callback: () => {
        n++;
        if (!g.active) return;
        if (n < 6) g.setAlpha(g.alpha < 1 ? 1 : 0.4);
        else g.setAlpha(1);
      },
    });
    sc.time.delayedCall(A.holdMs, () => {
      if (this.g !== g) return;
      sc.tweens.add({ targets: g, alpha: 0, duration: A.outMs, onComplete: () => this.g === g && this.clear() });
    });
    debugExpose('waveArrows', { side, edges, pts });
  }

  clear(): void {
    this.timer?.remove(false);
    this.timer = undefined;
    if (this.g) {
      this.scene.tweens.killTweensOf(this.g);
      this.g.destroy();
    }
    this.g = undefined;
  }
}

/** 화살촉 (끝이 angle 쪽 — 먹 외곽 1px + 강조 몸). 픽셀 단위로 채운다 */
function chevron(
  g: Phaser.GameObjects.Graphics,
  x: number,
  y: number,
  angle: number,
  size: number,
  fill: number,
  ink: number,
): void {
  const dx = Math.round(Math.cos(angle));
  const dy = Math.round(Math.sin(angle));
  // 끝(tip)에서 뒤로 size 줄, 줄마다 폭이 늘어나는 삼각형
  const rowsOf = (pad: number): [number, number, number, number][] => {
    const out: [number, number, number, number][] = [];
    for (let i = -pad; i < size + pad; i++) {
      const half = Math.max(0, i) + pad;
      if (dx !== 0) out.push([x - dx * i, y - half, 1, half * 2 + 1]);
      else out.push([x - half, y - dy * i, half * 2 + 1, 1]);
    }
    return out;
  };
  g.fillStyle(ink, 1);
  for (const [rx, ry, rw, rh] of rowsOf(1)) g.fillRect(rx, ry, rw, rh);
  g.fillStyle(fill, 1);
  for (const [rx, ry, rw, rh] of rowsOf(0)) g.fillRect(rx, ry, rw, rh);
}
