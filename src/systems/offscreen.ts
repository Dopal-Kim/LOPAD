/**
 * P19 S3 화면 밖 적 (계약 free-combat §4 · UiSnapshot.offscreen) — 순수. 카메라 화면(worldView) 밖의 살아 있는 적을
 * 화면 가운데 → 적 방향 · 주인공과의 거리 · 위협 단계로 돌려준다 (UI 가장자리 표식 — 카메라가 방 끝에 막혀 주인공이
 * 화면 가운데가 아닐 때도 표식 방향이 맞게).
 */
import { TILE, type TelegraphTier } from '../core/Constants';
import type { UiOffscreenEnemy } from '../contract/ui';

export interface OffscreenMob {
  x: number;
  y: number;
  active: boolean;
  threat: TelegraphTier | null;
}

const ids = new WeakMap<object, number>();
let nextId = 1;

/** 적마다 같은 번호 (개체가 사라지면 함께 잊힌다) — P21 처형 표식 uid 도 같은 번호 */
export const mobUid = (m: object): number => idOf(m);

function idOf(m: object): number {
  let id = ids.get(m);
  if (id === undefined) ids.set(m, (id = nextId++));
  return id;
}

export function offscreenEnemies(
  view: { x: number; y: number; width: number; height: number },
  from: { x: number; y: number },
  mobs: readonly OffscreenMob[],
): UiOffscreenEnemy[] {
  const out: UiOffscreenEnemy[] = [];
  for (const m of mobs) {
    if (!m.active) continue;
    if (m.x >= view.x && m.x <= view.x + view.width && m.y >= view.y && m.y <= view.y + view.height) continue;
    const cx = view.x + view.width / 2;
    const cy = view.y + view.height / 2;
    out.push({
      id: idOf(m),
      angle: +Math.atan2(m.y - cy, m.x - cx).toFixed(3),
      distTiles: +(Math.hypot(m.x - from.x, m.y - from.y) / TILE).toFixed(1),
      threat: m.threat,
    });
  }
  return out;
}
