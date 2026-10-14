/**
 * 48라운드 노드 지도 (계약 §10): 노드 진입(밝아짐·입력 잠금) · 클리어 → 출구 · 다음 노드 선택 · 전환,
 * 그리고 층 출구(방+복도 층·보스 노드 → 다음 층).
 * 62 루프 2 E: 출구 = 외벽 문 (ArenaDoors — 바닥 발판 없음). 문턱에 들어서면 문 안으로 걸어 들어가 전환 · 새 노드는 반대편 문에서
 * 걸어 들어온다 · 노드 고르기(UI)는 열린 직후 MENU_GUARD.ARM_MS 동안 고르기 명령을 받지 않는다.
 * 62 H: 문 안에 들어서면 그림 속 입구 전환 없이 곧바로 노드 지도 (외길이어도) → 고르면 짧은 암전('fade') → 반대편 문으로 입장.
 * 지도 미리보기 그림(UiRouteNode.previewKey)은 RoutePreview. 층 이동('floor')만 입구 그림 전환.
 */
import { MENU_GUARD, ROUTE_FX } from '../../core/Constants';
import { EventBus, Events, type NodeEnteredPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { UI_EVENTS, __system, type UiRouteEntered } from '../../contract/ui';
import { RUN } from '../../data';
import { minBattlesOnAnyPath, regionIdOf } from '../../systems/route';
import { oncePerKeyEvent } from '../../systems/keyEvents';
import { nodeFadeInfo } from '../../systems/transition/fadeFlow';
import { transitionGate } from '../../systems/transition/transitionGate';
import type { Game } from '../Game';
import { doorFor, withDoor } from './PaintArt';
import { RoutePreview } from './RoutePreview';
import { fadeCover } from './TransitionFx';
import { urlParams, type GameInitData } from './shared';
import { MenuGuard } from '../../systems/input/menuGuard';

/** 층 이동 입구 그림의 지역 (다음 층 첫 열 — 없으면 보스 홀). NodePrefetch 도 같은 그림을 미리 받는다 */
export function nextFloorRegion(): string {
  const nextStage = RUN.order[gameState.stageIndex + 1];
  return (nextStage && regionIdOf(nextStage, 0)) || 'boss';
}

/** 입구 그림 한 장을 기다리는 최대 시간 (그 뒤엔 그림 없이 — UI 가 키아트·단색으로 대체) */
const DOOR_WAIT_MS = 1200;

export class RouteFlow {
  /** 출구 열림 · 열림 예약 */
  exitOpen = false;
  private exitScheduled = false;
  /** 노드 진입 직후 입력·전투 시작 잠금 끝 시각 */
  enterLockUntil = 0;
  /** 62 루프 2 E: 노드 고르기 열린 직후 UI 의 고르기 명령 무시 (`UiRoute.openedAt`·`armMs`) */
  private readonly chooseGuard = new MenuGuard(MENU_GUARD.ARM_MS, urlParams().get(MENU_GUARD.PARAM) !== '0');
  /** 62 H: 지도 미리보기 그림 (UiRouteNode.previewKey · 미리 받기) */
  readonly preview: RoutePreview | null;

  constructor(private readonly g: Game) {
    if (g.routeMode) {
      gameState.exitOpen = false;
      gameState.rewardPending = false;
    }
    this.preview = g.routeMode && gameState.route ? new RoutePreview(g) : null;
  }

  /** HUD 진행 표시 재해석 (임시): 시련 총수 = 어느 길로 가도 거치는 최소 전투 수, 보스 해금 = 다음이 보스 */
  syncProgress(): void {
    const route = gameState.route;
    if (!route) return;
    gameState.trialsTotal = minBattlesOnAnyPath(route.graph);
    gameState.bossUnlocked = this.g.nodeKind === 'boss' || route.nextOptions().some((n) => n.kind === 'boss');
  }

  /**
   * 노드 진입: 밝아짐 · 입력 잠금 · ROUTE_NODE_ENTERED · 새 런 첫 노드면 탄생 · 진입 갈림이면 바로 선택.
   * 61 단계 6: revealedByUi = 그림 속 입구 전환을 UI 가 걷어내는 중(카메라 밝아짐 생략) · resume = 수련장에서 맡긴 런으로 돌아옴 —
   * 이미 마친 노드면 출구를 연 채로(노드 진입 보상·전투 없이) 돌려주고 true
   */
  enterNode(revealedByUi = false, resume = false): boolean {
    const g = this.g;
    const now = g.time.now;
    if (!revealedByUi)
      g.cameras.main.fadeIn(ROUTE_FX.FADE_IN_MS, ROUTE_FX.FADE_COLOR.R, ROUTE_FX.FADE_COLOR.G, ROUTE_FX.FADE_COLOR.B);
    this.syncProgress();
    // 62 루프 2 E: 반대편(서쪽) 문에서 걸어 들어온다 — 다 들어올 때까지 입력·전투 시작 잠금 (탄생 전장은 입구 문 없음)
    const walkMs = g.nodeKind === 'birth' ? 0 : g.doors.enter();
    this.enterLockUntil = now + Math.max(ROUTE_FX.ENTER_LOCK_MS, walkMs);
    const node = g.node;
    if (resume && node && gameState.route?.currentCleared) {
      this.resumeCleared();
      return true;
    }
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
    // 62 H: 지도에 보일 노드의 미리보기 그림 (입구 걸음 뒤 — 막지 않는다)
    this.preview?.schedule();
    return false;
  }

  /** 61 단계 6: 수련장에서 돌아옴 — 마친 노드 (전투·보상·튜토리얼 없이 출구 열림) */
  private resumeCleared(): void {
    const g = this.g;
    const room = g.layout?.rooms[0];
    if (room) {
      g.director.markCleared(room.id);
      g.clearedRooms.add(room.id);
    }
    g.tutorial?.skip(true);
    gameState.birthPending = false;
    this.exitScheduled = true;
    // create 중에는 씬이 아직 RUNNING 이 아니다 — 다음 틱에 출구
    g.time.delayedCall(1, () => this.openNodeExit());
  }

  /** 진입 직후 · 선택 중 · 전환 중 입력 잠금 */
  locked(time: number): boolean {
    if (!this.g.routeMode) return false;
    return time < this.enterLockUntil || Boolean(gameState.route?.choosing) || this.g.transitioning;
  }

  /** 62 루프 2 E: 지금 문으로 나가도 되는가 (싸움·메뉴·정지·전환·고르기 중이 아니고, 남은 성장 눈금 메뉴가 없을 때) */
  private canLeave(): boolean {
    const g = this.g;
    return (
      !g.director.inCombat &&
      !g.menu.isOpen &&
      !g.frozen &&
      !g.transitioning &&
      !transitionGate.locked &&
      !gameState.route?.choosing &&
      !gameState.rewardPending &&
      !g.growth.pending()
    );
  }

  /** 노드 클리어 → (잠시 뒤) 출구 문이 열린다. 문턱에 들어서면 문으로 걸어 들어가 다음 노드 (ArenaDoors) */
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
      // 62 H: 방을 비운 순간 다음 열 미리보기 그림을 받아 둔다 (문 → 지도 순간 키아트가 먼저 떴다 바뀌지 않게 — 막지 않는다)
      this.preview?.preload();
      if (!this.exitScheduled) {
        this.exitScheduled = true;
        g.time.delayedCall(ROUTE_FX.EXIT_DELAY_MS, () => this.openNodeExit());
      }
    }
  }

  /**
   * 62 H: 문 안까지 걸어 들어간 뒤 (ArenaDoors onThrough) 곧바로 노드 지도 — 그림 속 입구 전환('exitRoom') 없이, 갈 길이 하나여도
   * (옛 62 P2-1 '외길 자동 진행' 대체 — 지도에서 Enter/클릭 한 번). 못 열면(있을 수 없지만) 문에서 걸어 나온다
   */
  private exitToMap(): void {
    const g = this.g;
    const route = gameState.route;
    if (!route || route.nextOptions().length === 0) return;
    g.player.haltForWarp();
    if (!this.openChooser() && !route.choosing) g.doors.stepBack();
  }

  /**
   * 층 이동 그림 속 입구 전환 ('floor' — 62 H 뒤에도 유지): 입구 그림(art §28 — 정확 → 별칭 → <지역>_battle)을 한 장 받은 뒤
   * (최대 DOOR_WAIT_MS) begin. 문지기가 거부하면(다른 전환 중) 예전 암전으로
   */
  private beginFloorDoor(region: string, swap: () => void): void {
    const g = this.g;
    const nodeKind = 'floor';
    withDoor(g, doorFor(g, region, nodeKind), DOOR_WAIT_MS, (doorKey) => {
      if (!g.scene.isActive()) return;
      const ok = transitionGate.begin(
        { mode: 'floor', region, nodeKind, ...(doorKey ? { doorKey } : {}) },
        swap,
        (cover) => fadeCover(g, cover),
      );
      if (!ok) fadeCover(g, swap);
    });
  }

  /**
   * 다음 층 출구: 방+복도 층 · 노드 지도의 보스 노드 (그 밖의 노드 출구는 update 가 노드 선택을 연다).
   * 전환을 시작했으면 true (그 프레임 나머지 갱신을 멈춘다)
   */
  checkFloorExit(): boolean {
    const g = this.g;
    // 62 루프 2 E: 노드 지도 층(보스 노드 포함)은 외벽 문 (openFloorExit) — 발판은 방+복도 층만
    if (g.routeMode || !gameState.exitOpen || g.transitioning || !g.world.isExitAt(g.player.x, g.player.y))
      return false;
    g.transitioning = true;
    g.scene.restart({ mode: 'next' } satisfies GameInitData);
    return true;
  }

  /**
   * 62 루프 2 E: 보스 노드 보상 뒤 층 출구 = 외벽 문 (Progression.beginStageReward). 문이 없으면 false (방+복도 층 — 발판).
   * 문 안까지 걸어 들어가면 다음 지역 키아트 큰 그림의 입구로 ('floor', 61 단계 6 P14 §3)
   */
  openFloorExit(): boolean {
    const g = this.g;
    if (!g.routeMode || !g.doors.hasExit) return false;
    const ok = g.doors.openExit(
      'floor',
      () => {
        if (g.transitioning) return;
        g.transitioning = true;
        const next = () => g.scene.restart({ mode: 'next' } satisfies GameInitData);
        this.beginFloorDoor(nextFloorRegion(), next);
      },
      () => this.canLeave(),
    );
    if (ok) {
      this.exitOpen = true;
      gameState.exitOpen = true;
    }
    return ok;
  }

  /** 노드 출구 = 진행 방향(동쪽) 외벽 문이 열린다 (62 루프 2 E — 옛 오른쪽 2×2 발판 대체) */
  private openNodeExit(): void {
    const g = this.g;
    if (!g.scene.isActive() || this.exitOpen || !g.layout?.arena) return;
    // 62 H: 문이 열리는 순간에도 (수련장에서 돌아옴·디버그처럼 '비운 순간'을 거치지 않는 경로) — 이미 있거나 받는 중이면 건너뜀
    this.preview?.preload();
    // 문이 없는 전장(있을 수 없지만)이면 문 없이 바로 고르기로
    if (
      !g.doors.openExit(
        'node',
        () => this.exitToMap(),
        () => this.canLeave(),
      )
    )
      g.time.delayedCall(ROUTE_FX.EXIT_DELAY_MS, () => this.exitToMap());
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
    // 62 루프 2 E: 열린 직후 고르기 명령 무시 (UiRoute.openedAt·armMs) · 쌓인 입력 비우기
    route.chooseGuard = { openedAt: this.chooseGuard.arm(), armMs: this.chooseGuard.armMs };
    // 62 H: 미리보기 그림 (이미 받았으면 건너뜀 — 늦은 것은 UI 가 키아트로 대체)
    this.preview?.attach(route);
    this.preview?.preload();
    g.inputSystem?.flush();
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

  /** 62 루프 2 E: uiCommands.chooseNode — 고르기가 열린 직후(armMs)면 무시 */
  chooseFromUi(id: string): boolean {
    if (gameState.route?.choosing && !this.chooseGuard.accepts()) {
      EventBus.emit(Events.MENU_GUARDED, { id: 'route', key: id });
      return false;
    }
    return this.chooseNode(id);
  }

  /** 62 루프 2 E: UI 가 노드 고르기 지도를 실제로 그렸다 (uiCommands.menuShown('route')) — 그때부터 다시 armMs */
  chooserShown(): void {
    if (!gameState.route?.choosing) return;
    this.chooseGuard.shown();
    gameState.route.chooseGuard = { openedAt: this.chooseGuard.openedAt, armMs: this.chooseGuard.armMs };
  }

  /** 노드 고르기 (계약 §10.2 — 디버그는 이것을 직접): available 노드만. 층 상태를 들고 짧은 암전('fade') 뒤 그 노드 전투장을 연다 */
  chooseNode(id: string): boolean {
    const g = this.g;
    const route = gameState.route;
    if (!route || !route.choosing || g.transitioning || !route.canChoose(id)) return false;
    g.transitioning = true;
    gameState.structureCarry = g.structures.exportFloorState();
    route.enter(id);
    const restart = () => g.scene.restart({ mode: 'node' } satisfies GameInitData);
    // 62 H: 입구 그림으로 파고드는 전환('enterNode') 대신 짧은 먹 번짐 암전 — UI 가 덮으면 새 노드 (UI 없으면 카메라 암전)
    const node = route.current;
    const ok =
      node &&
      transitionGate.begin(nodeFadeInfo(gameState.stageId, node, ROUTE_FX.MAP_FADE_MS), restart, (cover) =>
        fadeCover(g, cover),
      );
    if (!ok) fadeCover(g, restart);
    return true;
  }

  /**
   * 53라운드 Q47 uiCommands.cancelChoose: 고르기를 닫는다. 62 루프 2 E: 문 안에서 문턱 안쪽으로 걸어 나온다 (문턱을 벗어났다
   * 다시 들어서면 다시 나간다). 고르는 중이 아니거나 진입 갈림(현재 노드 없음)이면 false
   */
  cancelChoose(): boolean {
    const g = this.g;
    const route = gameState.route;
    if (!route || !route.choosing || g.transitioning || !g.node || !g.layout?.arena) return false;
    route.choosing = false;
    route.chooseGuard = null;
    g.doors.stepBack();
    return true;
  }

  /** 디버그 (62 루프 2 E 헤드리스): 싸움 없이 이 노드를 마친 것으로 하고 출구 문을 연다 */
  debugOpenExit(): boolean {
    const g = this.g;
    const room = g.layout?.rooms[0];
    if (!gameState.route || !room) return false;
    g.director.markCleared(room.id);
    g.clearedRooms.add(room.id);
    gameState.route.markCleared();
    this.exitScheduled = true;
    this.openNodeExit();
    return this.exitOpen;
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
}
