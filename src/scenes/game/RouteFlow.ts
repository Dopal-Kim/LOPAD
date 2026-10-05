/**
 * 48라운드 노드 지도 (계약 §10): 노드 진입(밝아짐·입력 잠금) · 클리어 → 출구 · 다음 노드 선택 · 전환,
 * 그리고 층 출구(방+복도 층·보스 노드 → 다음 층).
 */
import { ROUTE_FX, TILE } from '../../core/Constants';
import { EventBus, Events, type NodeEnteredPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { UI_EVENTS, __system, type UiRouteEntered } from '../../contract/ui';
import { minBattlesOnAnyPath } from '../../systems/route';
import { oncePerKeyEvent } from '../../systems/keyEvents';
import type { Game } from '../Game';
import { urlParams, type GameInitData } from './shared';

export class RouteFlow {
  /** 출구 열림 · 열림 예약 */
  exitOpen = false;
  private exitScheduled = false;
  /** 노드 진입 직후 입력·전투 시작 잠금 끝 시각 */
  enterLockUntil = 0;
  /** 출구에서 벗어나야 다시 선택을 연다 (UI 없이 메뉴로 고를 때) */
  private exitArmed = true;

  constructor(private readonly g: Game) {
    if (g.routeMode) {
      gameState.exitOpen = false;
      gameState.rewardPending = false;
    }
  }

  /** HUD 진행 표시 재해석 (임시): 시련 총수 = 어느 길로 가도 거치는 최소 전투 수, 보스 해금 = 다음이 보스 */
  syncProgress(): void {
    const route = gameState.route;
    if (!route) return;
    gameState.trialsTotal = minBattlesOnAnyPath(route.graph);
    gameState.bossUnlocked = this.g.nodeKind === 'boss' || route.nextOptions().some((n) => n.kind === 'boss');
  }

  /** 노드 진입: 밝아짐 · 입력 잠금 · ROUTE_NODE_ENTERED · 새 런 첫 노드면 탄생 · 진입 갈림이면 바로 선택 */
  enterNode(): void {
    const g = this.g;
    const now = g.time.now;
    g.cameras.main.fadeIn(ROUTE_FX.FADE_IN_MS, ROUTE_FX.FADE_COLOR.R, ROUTE_FX.FADE_COLOR.G, ROUTE_FX.FADE_COLOR.B);
    this.enterLockUntil = now + ROUTE_FX.ENTER_LOCK_MS;
    this.syncProgress();
    const node = g.node;
    if (node) {
      __system.emit(UI_EVENTS.ROUTE_NODE_ENTERED, {
        id: node.id,
        type: node.type,
        name: node.name,
      } satisfies UiRouteEntered);
      // 61라운드 P9 런 로그 (시험장은 노드 지도가 없어 오지 않는다)
      EventBus.emit(Events.NODE_ENTERED, {
        id: node.id,
        kind: g.nodeKind ?? node.type,
        type: node.type,
        name: node.name,
        stageIndex: gameState.stageIndex,
      } satisfies NodeEnteredPayload);
    }
    if (g.nodeKind === 'birth' && gameState.birthPending && !urlParams().has('nobirth')) g.birth.start();
    else if (g.nodeKind === 'birth') gameState.birthPending = false;
    if (!node) g.time.delayedCall(ROUTE_FX.ENTER_LOCK_MS, () => this.openChooser());
  }

  /** 진입 직후 · 선택 중 · 전환 중 입력 잠금 */
  locked(time: number): boolean {
    if (!this.g.routeMode) return false;
    return time < this.enterLockUntil || Boolean(gameState.route?.choosing) || this.g.transitioning;
  }

  /** 노드 클리어 → (잠시 뒤) 출구. 출구에 서면 다음 노드 선택 */
  update(time: number): void {
    const g = this.g;
    const route = gameState.route;
    if (!route || !g.node || g.transitioning || time < this.enterLockUntil) return;
    const room = g.layout?.rooms[0];
    if (!room) return;
    if (
      !route.currentCleared &&
      g.nodeKind !== 'boss' &&
      (!g.tutorial || g.tutorial.done) &&
      g.director.stateOf(room.id) === 'cleared' &&
      !g.director.inCombat
    ) {
      route.markCleared();
      g.clearedRooms.add(room.id);
      this.syncProgress();
      if (!this.exitScheduled) {
        this.exitScheduled = true;
        g.time.delayedCall(ROUTE_FX.EXIT_DELAY_MS, () => this.openNodeExit());
      }
    }
    if (!this.exitOpen || route.choosing) return;
    const onExit = g.world.isExitAt(g.player.x, g.player.y);
    if (onExit && this.exitArmed && !g.director.inCombat && !g.menu.isOpen && !g.frozen) {
      this.exitArmed = false;
      this.openChooser();
    } else if (!onExit) this.exitArmed = true;
  }

  /**
   * 다음 층 출구: 방+복도 층 · 노드 지도의 보스 노드 (그 밖의 노드 출구는 update 가 노드 선택을 연다).
   * 전환을 시작했으면 true (그 프레임 나머지 갱신을 멈춘다)
   */
  checkFloorExit(): boolean {
    const g = this.g;
    const floorExit = !g.routeMode || g.nodeKind === 'boss';
    if (!floorExit || !gameState.exitOpen || g.transitioning || !g.world.isExitAt(g.player.x, g.player.y)) return false;
    g.transitioning = true;
    const next = () => g.scene.restart({ mode: 'next' } satisfies GameInitData);
    if (g.routeMode) this.fadeThen(next);
    else next();
    return true;
  }

  /** 노드 출구 (오른쪽 2×2) */
  private openNodeExit(): void {
    const g = this.g;
    if (!g.scene.isActive() || this.exitOpen || !g.layout?.arena) return;
    const e = g.layout.arena.exit;
    g.world.placeExitAt(e.x, e.y);
    this.exitOpen = true;
    gameState.exitOpen = true;
    EventBus.emit(Events.EXIT_OPENED, { stageIndex: gameState.stageIndex });
  }

  /** 다음 노드 선택 열기 (계약 §10.2): 입력 잠금 + ROUTE_CHOOSE_OPEN. UI 렌더러가 없으면 숫자 키로 고른다 */
  openChooser(): boolean {
    const g = this.g;
    const route = gameState.route;
    if (!route || route.choosing || g.transitioning || g.director.inCombat) return false;
    const options = route.nextOptions();
    if (options.length === 0) return false;
    route.choosing = true;
    g.player.haltForWarp();
    g.motion.stopLoops();
    if (g.economy.shopOpen) g.economy.closeShop();
    __system.emit(UI_EVENTS.ROUTE_CHOOSE_OPEN, route.toUi());
    if (!__system.rendererRegistered()) {
      const onKey = oncePerKeyEvent((e: KeyboardEvent) => {
        const n = options[Number(e.key) - 1];
        if (n && this.chooseNode(n.id)) g.input.keyboard?.off('keydown', onKey);
      });
      g.input.keyboard?.on('keydown', onKey);
    }
    return true;
  }

  /** uiCommands.chooseNode (계약 §10.2): available 노드만. 층 상태를 들고 암전 뒤 그 노드 전투장을 연다 */
  chooseNode(id: string): boolean {
    const g = this.g;
    const route = gameState.route;
    if (!route || !route.choosing || g.transitioning || !route.canChoose(id)) return false;
    g.transitioning = true;
    gameState.structureCarry = g.structures.exportFloorState();
    route.enter(id);
    this.fadeThen(() => g.scene.restart({ mode: 'node' } satisfies GameInitData));
    return true;
  }

  /**
   * 53라운드 Q47 uiCommands.cancelChoose: 고르기를 닫고 출구에서 한 걸음 물러난다 (출구 가운데 → 주인공 방향, 막혀 있으면
   * 전투장 가운데 쪽). 출구를 벗어났다 다시 들어서면 다시 연다. 고르는 중이 아니거나 진입 갈림(현재 노드 없음)이면 false
   */
  cancelChoose(): boolean {
    const g = this.g;
    const route = gameState.route;
    if (!route || !route.choosing || g.transitioning || !g.node || !g.layout?.arena) return false;
    route.choosing = false;
    this.exitArmed = false;
    const e = g.layout.arena.exit;
    const ex = (e.x + 1) * TILE;
    const ey = (e.y + 1) * TILE;
    const c = g.layout.arena.center ?? g.layout.arena.spawn;
    const step = ROUTE_FX.CANCEL_STEP_TILES * TILE + TILE; // 2×2 출구 반폭 + 한 걸음
    const away = (tx: number, ty: number) => {
      const dx = tx - ex;
      const dy = ty - ey;
      const len = Math.hypot(dx, dy) || 1;
      return { x: ex + (dx / len) * step, y: ey + (dy / len) * step };
    };
    const tries = [away(g.player.x, g.player.y), away((c.x + 0.5) * TILE, (c.y + 0.5) * TILE)];
    const to = tries.find((p) => g.world.isWalkableAt(p.x, p.y) && !g.world.isExitAt(p.x, p.y));
    if (to) g.player.body.reset(to.x, to.y);
    return true;
  }

  /** 디버그: 링크 무시하고 노드로 (층 상태 유지) */
  gotoNode(id: string): boolean {
    const g = this.g;
    const route = gameState.route;
    if (!route || g.transitioning || !route.node(id)) return false;
    g.transitioning = true;
    gameState.structureCarry = g.structures.exportFloorState();
    route.currentId = id;
    route.path.push(id);
    route.choosing = false;
    g.scene.restart({ mode: 'node' } satisfies GameInitData);
    return true;
  }

  /** 짧은 암전 뒤 실행 */
  private fadeThen(fn: () => void): void {
    const g = this.g;
    const C = ROUTE_FX.FADE_COLOR;
    g.cameras.main.fadeOut(ROUTE_FX.FADE_OUT_MS, C.R, C.G, C.B);
    g.time.delayedCall(ROUTE_FX.FADE_OUT_MS, () => {
      if (g.scene.isActive()) fn();
    });
  }
}
