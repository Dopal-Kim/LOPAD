/**
 * 디버그 자동 획 (?debug=1, 헤드리스 검증용): 정규화 좌표 경로 3개 · 점 간격 ms · 획 사이 쉼.
 * 실제 포인터 처리 경로(onPointerDown/Move/Up)를 그대로 부른다. 게임 로직이 아니다.
 */
import Phaser from 'phaser';
import { CANVAS_H, CANVAS_W } from '../display';

export type AutoPreset = 'fast' | 'slow' | 'round';

const AUTO_STROKES: Record<AutoPreset, [number, number][][]> = {
  fast: [0.2, 0.42, 0.64].map((y0) =>
    Array.from({ length: 9 }, (_, i) => [0.18 + i * 0.07, y0 + (i % 2 === 0 ? 0 : 0.08)] as [number, number]),
  ),
  slow: [0.25, 0.45, 0.65].map((y0) =>
    Array.from({ length: 14 }, (_, i) => [0.15 + i * 0.05, y0 + i * 0.004] as [number, number]),
  ),
  round: [0.3, 0.5, 0.7].map((cx) =>
    Array.from({ length: 16 }, (_, i) => {
      const a = Math.PI * (1 + i / 10);
      return [cx + 0.12 * Math.cos(a), 0.4 + 0.2 * Math.sin(a)] as [number, number];
    }),
  ),
};
const AUTO_STEP_MS: Record<AutoPreset, number> = { fast: 16, slow: 90, round: 40 };
const AUTO_GAP_MS = 250;

export interface PointerHandlers {
  down(p: Phaser.Input.Pointer): void;
  move(p: Phaser.Input.Pointer): void;
  up(p: Phaser.Input.Pointer): void;
}

/** 3획을 프레임 간격으로 예약한다 */
export function scheduleAutoStrokes(scene: Phaser.Scene, preset: AutoPreset, h: PointerHandlers): void {
  const paths = AUTO_STROKES[preset];
  const stepMs = AUTO_STEP_MS[preset];
  let delay = 0;
  for (const path of paths) {
    // 실제 포인터처럼 캔버스 px (52라운드 1920×1080 — 핸들러가 논리 px 로 바꾼다)
    const pts = path.map(([x, y]) => ({ x: x * CANVAS_W, y: y * CANVAS_H }));
    pts.forEach((pt, i) => {
      scene.time.delayedCall(delay + i * stepMs, () => {
        const t = scene.time.now;
        const p = { x: pt.x, y: pt.y, downTime: t, moveTime: t, upTime: t, isDown: true } as Phaser.Input.Pointer;
        if (i === 0) h.down(p);
        else if (i === pts.length - 1) h.up(p);
        else h.move(p);
      });
    });
    delay += pts.length * stepMs + AUTO_GAP_MS;
  }
}
