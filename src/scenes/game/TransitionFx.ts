/**
 * 61 단계 6 (P14 §3) 그림 속 입구 전환의 씬 쪽 도우미: UI 가 없을 때의 대체 덮기(짧은 암전).
 * 전환 순서·안전장치는 systems/transition/transitionGate.
 */
import { ROUTE_FX } from '../../core/Constants';
import type { Game } from '../Game';

/** 대체 덮기: 카메라 암전이 끝나면 go (씬이 이미 끝났으면 아무것도) */
export function fadeCover(g: Game, go: () => void): void {
  const C = ROUTE_FX.FADE_COLOR;
  g.cameras.main.fadeOut(ROUTE_FX.FADE_OUT_MS, C.R, C.G, C.B);
  g.time.delayedCall(ROUTE_FX.FADE_OUT_MS, () => {
    if (g.scene.isActive()) go();
  });
}
