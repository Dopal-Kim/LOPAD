/**
 * 디버그 자동 획 (?debug=1, 헤드리스 검증용): 정규화 좌표 경로 3개 · 점 간격 ms.
 * 62: UI 가 보내는 것과 같은 형식(논리 960×540 점 목록 — 계약 §20 `ritual.stroke`)으로 만든다. 게임 로직이 아니다.
 */
import type { UiRitualPoint } from '../../contract/ui';
import { GAME } from '../../core/Constants';

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

/** 3획 (논리 px · t = 획 시작부터 ms) */
export function autoStrokePoints(preset: AutoPreset): UiRitualPoint[][] {
  const step = AUTO_STEP_MS[preset];
  return AUTO_STROKES[preset].map((path) =>
    path.map(([x, y], i) => ({ x: x * GAME.WIDTH, y: y * GAME.HEIGHT, t: i * step })),
  );
}
