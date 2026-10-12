/**
 * 62 루프 2 시스템 G 스냅샷 재료 (UiRelay → contract/snapshot): 주인공 화면 자리 `UiSnapshot.hero` (UI 요청 — 머리 위 연출).
 */
import type { UiHeroScreen } from '../../contract/ui';
import { worldToLogicalScreen } from '../../systems/display';
import type { Game } from '../Game';

const round = (p: { x: number; y: number }) => ({ x: Math.round(p.x), y: Math.round(p.y) });

/** 머리 꼭대기·그림 가운데·발 (논리 화면 좌표). 주인공이 없으면 null */
export function heroScreen(g: Game): UiHeroScreen | null {
  const p = g.player;
  if (!p?.active || !p.visual) return null;
  const cam = g.cameras.main;
  const feetY = p.y - p.visual.liftPx;
  const head = feetY - p.visual.headTopPx;
  return {
    head: round(worldToLogicalScreen(cam, p.x, head)),
    body: round(worldToLogicalScreen(cam, p.x, (feetY + head) / 2)),
    feet: round(worldToLogicalScreen(cam, p.x, feetY)),
    visible: p.visible && p.alpha > 0.05,
  };
}
