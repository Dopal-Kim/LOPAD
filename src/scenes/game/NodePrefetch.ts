/**
 * 62 루프 2 시스템 D (P2-6 · 계약 UI §22 LOADING) 다음 노드 미리 읽기: 노드 고르기가 열리면(출구에 섬) 고를 수 있는 노드들의
 * 외벽 테두리 그림(한 지역 GPU 약 75MB — 텍스처로 올리지 않고 **HTTP 캐시만 데운다**)을 `fetch` 로 미리 받는다.
 * 62 루프 4 J: 노드 이동은 짧은 암전('fade')이라 큰 입구 그림은 층 이동('floor' — 보스 노드)용 한 장만 (지도 카드 그림은 RoutePreview).
 * 노드에 들어설 때 같은 주소를 다시 받으면 캐시에서 바로 온다(첫 노드 약 5초 → 점검 P2-6). 진행률은 `ui:loading` phase prefetch
 * (배경 — UI 는 막는 화면을 띄우지 않는다). 같은 주소는 게임 수명 동안 한 번만.
 */
import type Phaser from 'phaser';
import { ASSETS, NODE_PREFETCH } from '../../core/Constants';
import { EventBus, Events } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { UI_EVENTS, __system, type UiLoading } from '../../contract/ui';
import { regionIdOf } from '../../systems/route';
import { assetListed } from '../../systems/sprites/sheetLoader';
import { borderFileRel, borderFiles, borderFor } from '../../world/border';
import type { Game } from '../Game';
import { doorFor } from './PaintArt';
import { nextFloorRegion } from './RouteFlow';

const fetched = new Set<string>();

/** 이 노드들에 들어설 때 받을 큰 그림 주소 (assets 기준 상대 경로 — 매니페스트에 있는 것만) */
export function prefetchFiles(regions: readonly (string | null)[], doors: readonly (string | null)[]): string[] {
  const out = new Set<string>();
  for (const r of regions) {
    const def = r ? borderFor(r) : null;
    if (!def) continue;
    for (const f of borderFiles(def)) out.add(borderFileRel(def.region, f));
  }
  for (const d of doors) if (d) out.add(`sprites/paint/${d}.png`);
  return [...out].filter((rel) => assetListed(rel));
}

export class NodePrefetch {
  private timer: Phaser.Time.TimerEvent | null = null;

  /**
   * 노드 지도 런의 씬마다 하나 (Game.create). 시련이 끝나거나 출구가 열리면 바로, 싸움이 없는 노드는 들어선 뒤 잠시 뒤에 시작한다
   * (RouteFlow 를 건드리지 않고 내부 이벤트로 — 출구 연출은 시스템 E)
   */
  constructor(private readonly g: Game) {
    const kick = () => this.start();
    EventBus.on(Events.TRIAL_CLEARED, kick);
    EventBus.on(Events.EXIT_OPENED, kick);
    if (!g.director.inCombat && g.nodeKind !== 'battle' && g.nodeKind !== 'road')
      this.timer = g.time.delayedCall(NODE_PREFETCH.CALM_DELAY_MS, kick);
    g.events.once('shutdown', () => {
      EventBus.off(Events.TRIAL_CLEARED, kick);
      EventBus.off(Events.EXIT_OPENED, kick);
      this.timer?.remove(false);
    });
  }

  /** 다음 노드 그림 미리 받기 (한 번 받은 주소는 건너뜀) */
  start(): void {
    const route = gameState.route;
    if (!route || typeof fetch !== 'function') return;
    const opts = route.nextOptions();
    const regions = opts.map((n) => regionIdOf(route.graph.stageId, n.col));
    const doors = this.g.nodeKind === 'boss' ? [doorFor(this.g, nextFloorRegion(), 'floor')] : [];
    const files = prefetchFiles(regions, doors).filter((f) => !fetched.has(f));
    if (files.length === 0) return;
    let done = 0;
    const nodes = opts.map((n) => n.id);
    EventBus.emit(Events.NODE_PREFETCH, { phase: 'start', nodes, files: files.length });
    const step = () => {
      done += 1;
      __system.emit(UI_EVENTS.LOADING, {
        phase: 'prefetch',
        progress: done / files.length,
        done: done >= files.length,
      } satisfies UiLoading);
      if (done >= files.length) EventBus.emit(Events.NODE_PREFETCH, { phase: 'done', nodes, files: files.length });
    };
    for (const rel of files) {
      fetched.add(rel);
      fetch(`${ASSETS.URL}/${rel}`, { cache: 'force-cache' })
        .then((r) => r.blob())
        .catch(() => fetched.delete(rel))
        .finally(step);
    }
  }
}
