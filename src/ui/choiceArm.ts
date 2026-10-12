import Phaser from 'phaser';
import { ChoiceGate } from './choiceGate';
import { heldNow, lastUp } from './inputHeld';

/**
 * 62 루프 2 UI D: 선택 메뉴 무장 (choiceGate.ts) 의 Phaser 쪽 — 게이트 열기 · 이벤트 시각 · 무장 진행 그림.
 *  - 카드: 테두리를 따라 차오르는 선 (왼쪽 위 → 시계 방향, 강조색 2px). 무장되면 한 바퀴가 닫히고 사라진다.
 *  - 목록: 제목 아래 괘선 위로 왼쪽 → 오른쪽 차오르는 선.
 */

/** 무장 그림 수치 */
export const ARM_FX = {
  /** 선 두께 (px) */
  line: 2,
  /** 무장된 뒤 선이 사라지는 시간 (ms) */
  fadeMs: 220,
  /** 카드 들어오기: 아래에서 올라오는 거리 (px) · 시간 · 카드 사이 지연 (ms) */
  enterDy: 10,
  enterMs: 260,
  enterStagger: 60,
} as const;

/** 메뉴가 그려진 지금 게이트를 연다 (지금 눌려 있는 키·버튼을 찍어 둔다) */
export function openGate(armMs?: number): ChoiceGate {
  return new ChoiceGate(performance.now(), { armMs, held: heldNow(), lastUp });
}

/** 키 이벤트 시각 (렉으로 늦게 처리돼도 눌린 때) */
export function keyTime(e: KeyboardEvent): number {
  return typeof e.timeStamp === 'number' && e.timeStamp > 0 ? e.timeStamp : performance.now();
}

/** 마우스 이벤트 시각 */
export function pointerTime(p?: Phaser.Input.Pointer): number {
  const t = p?.event?.timeStamp;
  return typeof t === 'number' && t > 0 ? t : performance.now();
}

/** 좌클릭인가 (가운데·오른쪽 버튼은 고르지 않는다) */
export function leftButton(p?: Phaser.Input.Pointer): boolean {
  return !p || p.button === 0;
}

export interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
}

/** 사각형 둘레를 왼쪽 위에서 시계 방향으로 p(0..1) 만큼 */
function tracePerimeter(g: Phaser.GameObjects.Graphics, r: Rect, p: number, lw: number): void {
  const x0 = r.x - lw;
  const y0 = r.y - lw;
  const w = r.w + lw * 2;
  const h = r.h + lw * 2;
  let left = (w * 2 + h * 2) * p;
  const seg = (len: number, draw: (n: number) => void): void => {
    if (left <= 0) return;
    const n = Math.min(len, left);
    draw(Math.round(n));
    left -= n;
  };
  seg(w, (n) => g.fillRect(x0, y0, n, lw));
  seg(h, (n) => g.fillRect(x0 + w - lw, y0, lw, n));
  seg(w, (n) => g.fillRect(x0 + w - n, y0 + h - lw, n, lw));
  seg(h, (n) => g.fillRect(x0, y0 + h - n, lw, n));
}

/**
 * 무장 진행 그림: 매 프레임 `draw(g, p)` (p = 0..1). 무장되면 p=1 로 한 번 그리고 사라진다. 씬이 꺼지면 함께 치운다.
 * 반환 = 치우는 함수.
 */
function armFx(
  scene: Phaser.Scene,
  gate: ChoiceGate,
  depth: number,
  draw: (g: Phaser.GameObjects.Graphics, p: number) => void,
): () => void {
  const g = scene.add.graphics().setDepth(depth);
  let done = false;
  const stop = (): void => {
    if (done) return;
    done = true;
    scene.events.off(Phaser.Scenes.Events.UPDATE, tick);
    scene.events.off(Phaser.Scenes.Events.SHUTDOWN, stop);
    scene.tweens.killTweensOf(g);
    g.destroy();
  };
  const tick = (): void => {
    if (!g.active) return stop();
    const now = performance.now();
    g.clear();
    draw(g, gate.progress(now));
    if (gate.armed(now)) {
      scene.events.off(Phaser.Scenes.Events.UPDATE, tick);
      scene.tweens.add({ targets: g, alpha: 0, duration: ARM_FX.fadeMs, onComplete: stop });
    }
  };
  scene.events.on(Phaser.Scenes.Events.UPDATE, tick);
  scene.events.once(Phaser.Scenes.Events.SHUTDOWN, stop);
  tick();
  return stop;
}

/** 카드 테두리를 따라 차오르는 선 (카드마다 — `rects()` 는 지금 카드 자리) */
export function armTrace(
  scene: Phaser.Scene,
  gate: ChoiceGate,
  rects: () => Rect[],
  color: number,
  depth: number,
): () => void {
  return armFx(scene, gate, depth, (g, p) => {
    g.fillStyle(color, 1);
    for (const r of rects()) tracePerimeter(g, r, p, ARM_FX.line);
  });
}

/** 가로 한 줄이 왼쪽 → 오른쪽으로 차오른다 (목록 메뉴 — 제목 아래 괘선 위) */
export function armBar(
  scene: Phaser.Scene,
  gate: ChoiceGate,
  x: number,
  y: number,
  w: number,
  color: number,
  depth: number,
): () => void {
  return armFx(scene, gate, depth, (g, p) => {
    g.fillStyle(color, 1).fillRect(x, y, Math.round(w * p), ARM_FX.line);
  });
}
