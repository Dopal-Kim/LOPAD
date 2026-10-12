/**
 * 62 루프 2 시스템 D 스냅샷 재료 (UiRelay → contract/snapshotLoop2D): 장터 노점 카드 · 허수아비 팻말 · 자동 저장 표시.
 */
import type { UiWorldSign } from '../../contract/ui';
import type { Loop2DSnapshotContext } from '../../contract/snapshotLoop2D';
import { worldToLogicalScreen } from '../../systems/display';
import type { LabDummy } from '../../objects/LabDummy';
import type { Game } from '../Game';

/** 화면 안 허수아비 팻말 (시험장 허수아비 · 수련장 방 허수아비) */
export function signsOf(g: Game): UiWorldSign[] {
  const dummies: readonly LabDummy[] = [...(g.labMode?.dummies ?? []), ...(g.training?.dummies ?? [])];
  const cam = g.cameras.main;
  const out: UiWorldSign[] = [];
  for (const d of dummies) {
    if (!d.active) continue;
    const s = d.sign();
    const p = worldToLogicalScreen(cam, s.x, s.y);
    out.push({
      id: s.id,
      kind: s.kind,
      title: s.title,
      value: s.value,
      screen: { x: Math.round(p.x), y: Math.round(p.y) },
    });
  }
  return out;
}

export function loop2DSnapshot(g: Game): Loop2DSnapshotContext {
  return {
    shopOffer: g.economy?.shopOffer() ?? null,
    signs: signsOf(g),
    autoSave: Boolean(g.runExit?.enabled),
  };
}
