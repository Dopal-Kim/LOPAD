/**
 * 62 루프 2 시스템 D (P2-5 · 계약 UI §22): 런에서 나가기 — 나갈 때 자동 저장(횟수 제한 없음) · 런 포기.
 * - 하데스·데드셀처럼 언제 나가도 이어하기가 남는다. 싸우는 중에 나가면 그 노드에 들어선 순간의 상태(노드를 처음부터 — 피해·줍기를
 *   되돌림), 마친 노드면 나갈 때 상태(출구가 열린 채로). 저장 형식은 런 세이브 v6 + `suspend`(systems/save SuspendData).
 * - 이어하기: Progression 이어하기 갈래가 `restoreSuspend` 로 노드 지도·층 덧붙임·상점 진열·층 구조물 상태를 되살린다.
 * - 런 포기: 사망과 같은 결산(영혼은 받은 만큼) — 주인공을 쓰러뜨려 기존 사망 흐름(PLAYER_DIED → 결산 → 결과)을 탄다.
 * 시험장·수련장은 대상이 아니다(세이브 없음).
 */
import { EventBus, Events } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { readSuspend, type SaveData, type SuspendData } from '../../systems/save';
import { RouteState } from '../../systems/route';
import { namedRoute } from '../../systems/routeArena';
import { decorateRoute, type FloorExtras } from '../../systems/bundle2/routeExtras';
import type { ShopStock } from '../../systems/bundle2/BundleState';
import type { StructureFloorCarry } from '../../systems/structures/core';
import type { Game } from '../Game';

const clone = <T>(v: T): T => (v === undefined ? v : (JSON.parse(JSON.stringify(v)) as T));

export class RunExit {
  /** 이 노드에 들어선 순간의 저장 (싸우는 중에 나가면 이것) */
  private entry: SaveData | null = null;

  constructor(private readonly g: Game) {}

  /** 노드 지도 런인가 (시험장·수련장·끝난 런은 아님) */
  get enabled(): boolean {
    const g = this.g;
    return (
      g.routeMode && !g.lab && !g.training && gameState.route !== null && !gameState.gameOver && !gameState.cleared
    );
  }

  /** 노드 진입 직후 (Game.create 끝) — 들어선 순간을 떠 둔다 */
  onNodeReady(): void {
    this.entry = this.enabled ? this.build(false) : null;
  }

  private build(nodeCleared: boolean): SaveData {
    const route = gameState.route!;
    const B = gameState.bundle;
    const g = this.g;
    const structures = nodeCleared ? g.structures.exportFloorState() : gameState.structureCarry;
    const suspend: SuspendData = {
      floor: route.floor,
      currentId: route.currentId,
      path: [...route.path],
      cleared: [...route.cleared],
      nodeCleared,
      extras: clone(B.floor),
      shops: clone(B.shops),
      structures: clone(structures ?? null),
      birthPending: gameState.birthPending,
      ...(route.current ? { nodeKind: route.current.kind } : {}),
    };
    return { ...gameState.toSave(), suspend };
  }

  /** 마친 노드인가 (싸움·보상 대기·연출이 끝나 출구로 나갈 수 있음) */
  private nodeDone(): boolean {
    const g = this.g;
    return Boolean(gameState.route?.currentCleared) && !g.director?.inCombat && !gameState.rewardPending;
  }

  /** 나가기 저장 — 썼으면 true */
  suspend(): boolean {
    if (!this.enabled) return false;
    const d = this.nodeDone() ? this.build(true) : this.entry;
    if (!d) return false;
    this.g.saveSlot.write({ ...d, savedAt: Date.now() });
    EventBus.emit(Events.RUN_SUSPENDED, {
      nodeId: d.suspend?.currentId ?? null,
      cleared: Boolean(d.suspend?.nodeCleared),
    });
    return true;
  }

  /** 런 포기 — 사망과 같은 결산. 받아들였으면 true */
  abandon(): boolean {
    const g = this.g;
    if (!this.enabled || g.lab) return false;
    if (g.menu?.isOpen) g.menu.close();
    g.setFrozen(false);
    gameState.hp = 0;
    gameState.gameOver = true;
    g.player.setAction('normal', 0);
    g.player.deathAnimMs = g.player.visual.oneShot('death', g.player.visual.facing, g.time.now);
    EventBus.emit(Events.RUN_ABANDONED, { nodeId: gameState.route?.currentId ?? null });
    EventBus.emit(Events.PLAYER_DIED);
    return true;
  }
}

/**
 * 이어하기: 자동 저장의 노드 지도·층 덧붙임·상점 진열·층 구조물 상태를 되살린다 (gameState.applySave 뒤).
 * 깨졌거나 맞지 않으면 false (층 처음으로 이어한다)
 */
export function restoreSuspend(raw: unknown): boolean {
  const s = readSuspend(raw);
  if (!s) return false;
  const graph = namedRoute(gameState.stageId, gameState.floorSeed);
  const has = (id: string) => graph.nodes.some((n) => n.id === id);
  if ((s.currentId !== null && !has(s.currentId)) || !s.path.every(has)) return false;
  const route = new RouteState(graph, s.floor);
  route.currentId = s.currentId;
  route.path.push(...s.path);
  for (const id of s.cleared) route.cleared.add(id);
  const B = gameState.bundle;
  const ex = s.extras as FloorExtras | null;
  if (ex && typeof ex === 'object' && ex.nodes && typeof ex.nodes === 'object') {
    B.floor = ex;
    // 숨은 길을 이미 열었으면 지도 그래프에도 다시 잇는다 (revealHidden 은 상태가 found 면 건너뛰므로 직접)
    const h = ex.hidden;
    const src = h && h.state === 'found' ? graph.nodes.find((n) => n.id === h.sourceId) : undefined;
    if (h && src && !src.links.includes(h.nodeId)) src.links.push(h.nodeId);
    route.decorate = (base, st) => (B.floor ? decorateRoute(base, B.floor, st.graph) : base);
  }
  B.shops = (s.shops as ShopStock[]) ?? [];
  gameState.route = route;
  gameState.structureCarry = (s.structures as StructureFloorCarry | null) ?? null;
  gameState.birthPending = s.birthPending;
  return true;
}

/** Game preload (세이브를 아직 적용하기 전): 이어하기 자동 저장이 보스 노드인가 */
export function suspendAtBoss(save: SaveData | null, init: { mode?: string }): boolean {
  return init.mode === undefined && save?.suspend?.nodeKind === 'boss';
}
