/**
 * 62 시스템 H (도영 님 추가 지시 — 키아트 전환 대신 지도에서 고르고 키아트는 작은 미리보기) 노드 지도 미리보기 그림.
 * - `RouteState.previewOf` 를 단다: 노드 → 입구 그림 텍스처 키 `paint/door_<지역>_<종류>` (art §28 규칙 — PaintArt.doorFor, 보스 = door_hall_boss).
 *   62 I (art §32): 위험 노드(elite·curse)면 `door_<지역>_<위험>` 먼저, `_small`(512×288 카드판)이 있으면 그것.
 *   별칭 표(doors.json)를 받은 뒤의 답만 기억한다 (스냅샷마다 부르므로).
 * - 노드에 들어선 뒤 잠시 뒤, 그리고 지도를 열 때: 지도를 열면 보일 노드(고를 수 있는 노드 + 그다음 열)의 그림을 받는다 (`loadPaint` —
 *   queueImageOnce, 지도 열기를 막지 않는다. 늦으면 UI 가 지역 키아트로 대체).
 */
import { ROUTE_FX } from '../../core/Constants';
import { gameState } from '../../core/GameState';
import { nodeRegionId, type RouteNode, type RouteState } from '../../systems/route';
import type { Game } from '../Game';
import { doorIndexReady, loadDoorIndex, loadPaint, paintKey, previewDoorFor } from './PaintArt';

/** `<지역>_<종류>` → 텍스처 키 (없음 = null) — 게임 수명 동안 (매니페스트·별칭은 바뀌지 않는다) */
const memo = new Map<string, string | null>();

/** 62 I (art §32-1): 노드 위험 (elite·curse — bundle2 NodeExtra.risk, 없으면 null) */
function riskOf(n: RouteNode): string | null {
  return gameState.bundle.floor?.nodes[n.id]?.risk ?? null;
}

/** 노드의 미리보기 그림 이름 (`door_…`, 62 I: 위험 그림 먼저 · `_small` 카드판 우선) — 없으면 null */
function previewName(g: Game, regionId: string, n: RouteNode): string | null {
  return previewDoorFor(g, regionId, n.kind, riskOf(n));
}

export class RoutePreview {
  /** 디버그: 미리 받기 기록 (시각 · 그림 이름) */
  readonly log: { t: number; names: string[] }[] = [];

  constructor(private readonly g: Game) {
    loadDoorIndex(g);
    const route = gameState.route;
    if (route) this.attach(route);
  }

  /** 스냅샷·ROUTE_CHOOSE_OPEN 의 `UiRouteNode.previewKey` */
  attach(route: RouteState): void {
    const g = this.g;
    route.previewOf = (n, regionId) => {
      const id = `${regionId}_${n.kind}_${riskOf(n) ?? ''}`;
      const hit = memo.get(id);
      if (hit !== undefined) return hit;
      const name = previewName(g, regionId, n);
      const key = name ? paintKey(name) : null;
      if (doorIndexReady(g)) memo.set(id, key);
      return key;
    };
  }

  /** 노드 진입 뒤 (진입 걸음·밝아짐이 끝난 뒤 — 들어오는 프레임에 디코드·업로드가 겹치지 않게) */
  schedule(): void {
    const g = this.g;
    g.time.delayedCall(ROUTE_FX.PREVIEW_DELAY_MS, () => {
      if (g.scene.isActive()) this.preload();
    });
  }

  /** 지도를 열면 보일 노드들의 미리보기 그림을 받는다 (이미 있거나 받는 중이면 건너뜀). 큐에 넣은 그림 이름 */
  preload(): string[] {
    const route = gameState.route;
    if (!route) return [];
    const names = new Set<string>();
    for (const n of route.previewTargets()) {
      const name = previewName(this.g, nodeRegionId(route.graph.stageId, n), n);
      if (name) names.add(name);
    }
    const list = [...names];
    if (list.length > 0) loadPaint(this.g, list);
    this.log.push({ t: Math.round(this.g.time.now), names: list });
    if (this.log.length > 20) this.log.shift();
    return list;
  }
}
