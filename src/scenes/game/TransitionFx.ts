/**
 * 61 단계 6 (P14 §3) 그림 속 입구 전환의 씬 쪽 도우미: UI 가 없을 때의 대체 덮기(짧은 암전) · 월드 → 논리 화면 좌표(from).
 * 전환 순서·안전장치는 systems/transition/transitionGate.
 */
import { GAME, ROUTE_FX } from '../../core/Constants';
import type { Game } from '../Game';

/** 대체 덮기: 카메라 암전이 끝나면 go (씬이 이미 끝났으면 아무것도) */
export function fadeCover(g: Game, go: () => void): void {
  const C = ROUTE_FX.FADE_COLOR;
  g.cameras.main.fadeOut(ROUTE_FX.FADE_OUT_MS, C.R, C.G, C.B);
  g.time.delayedCall(ROUTE_FX.FADE_OUT_MS, () => {
    if (g.scene.isActive()) go();
  });
}

/** 월드 좌표 → 논리 화면 좌표 (960×540, 카메라 확대·스크롤 반영) */
export function screenOfWorld(g: Game, x: number, y: number): { x: number; y: number } {
  const v = g.cameras.main.worldView;
  if (!(v.width > 0) || !(v.height > 0)) return { x: GAME.WIDTH / 2, y: GAME.HEIGHT / 2 };
  // 화면 밖(출구가 가장자리 너머)이면 화면 안으로 붙인다 — 줌 중심이므로
  return {
    x: Math.max(0, Math.min(GAME.WIDTH, Math.round(((x - v.x) / v.width) * GAME.WIDTH))),
    y: Math.max(0, Math.min(GAME.HEIGHT, Math.round(((y - v.y) / v.height) * GAME.HEIGHT))),
  };
}
