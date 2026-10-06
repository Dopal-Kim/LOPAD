import Phaser from 'phaser';
import { uiCommands, type UiRoute, type UiRouteNode, type UiSnapshot } from '../contract/ui';
import { cancelChooseCmd, chooseNodeCmd, debugExpose, withDebug } from './debug';
import { ensureImage, keyartKey, keyartUrl, mapBgKey, mapBgUrl } from './kit';
import { regionArtKey } from './regionView';
import { RouteMap } from './RouteMap';
import { hasRoute } from './routeView';
import { routeText } from './text';
import { MAP_BG_FLOORS } from './theme';
import { noteTransitionOrigin, transitionBusy } from './transitionState';

/** 노드를 고르거나 고르기를 취소한 뒤 '고를 차례인데 지도가 없음' 안전망을 쉬는 시간 (ms) — 스냅샷이 따라올 때까지 */
const ROUTE_CANCEL_SUPPRESS_MS = 1500;
/**
 * 61 단계 6 (§19): 노드를 고른 뒤 그림 속 입구 전환이 시작되기를 기다리는 시간 (ms). 그 사이 지도는 입력 없이 남아 있다가
 * 전환이 덮으면(`ui:transition-covered`) 치운다. 전환이 오지 않으면 이 시간 뒤 치운다(예전처럼).
 */
const ROUTE_LEAVE_WAIT_MS = 400;
/** 전환이 시작됐는데 덮임이 끝내 오지 않을 때 지도를 치우는 시간 (ms) */
const ROUTE_LEAVE_MAX_MS = 3000;

export interface RouteControlHooks {
  /** 워프 지도 닫기 (resume 여부) */
  closeWarp(resume: boolean): void;
  /** 키를 뗀 다음 프레임에 (HUD afterRelease) */
  afterRelease(key: string, fn: () => void): void;
}

/**
 * HUD 노드 지도 다루기 (48·49·53라운드, 61 단계 6 에서 HudScene 에서 분리): 고르기·보기 지도 열기·닫기, 고르기 취소,
 * 고른 뒤 그림 속 입구 전환이 덮을 때까지 지도 남기기(+ 파고들 자리 적기), 큰 그림 미리 읽기.
 */
export class RouteControl {
  /** 지금 열린 지도 (고르기·보기) */
  map?: RouteMap;
  /** 고른 뒤 전환이 덮을 때까지 남긴 지도 (입력 없음) */
  private leaving?: RouteMap;
  private leaveTimer?: Phaser.Time.TimerEvent;
  private suppressUntil = 0;
  private prefetchSig = '';

  constructor(
    private scene: Phaser.Scene,
    private hooks: RouteControlHooks,
  ) {}

  /** 노드를 고르거나 취소한 직후라 안전망이 지도를 다시 열면 안 되는가 */
  suppressed(): boolean {
    return this.scene.time.now <= this.suppressUntil;
  }

  private opts(s: UiSnapshot): ConstructorParameters<typeof RouteMap>[3] {
    return {
      stageIndex: Math.max(0, s.stageIndex),
      floorTitle: s.floorTitle || s.stageName,
      shopName: s.names?.shop,
      onChoose: (id) => this.choose(id),
    };
  }

  /** ROUTE_CHOOSE_OPEN: 고르기 모드로 연다 (게임 입력은 시스템이 잠근다 — 정지하지 않는다) */
  openChoose(r: UiRoute | null | undefined): void {
    const s = withDebug(uiCommands.getUiSnapshot());
    const route = hasRoute(r) ? r : s.route;
    if (!hasRoute(route)) return;
    if (this.map) this.close(this.map.mode === 'view');
    this.hooks.closeWarp(true);
    this.dropLeaving();
    this.map = new RouteMap(this.scene, route, 'choose', this.opts(s));
  }

  /** M·Tab 보기 (게임을 멈춘다) */
  openView(s: UiSnapshot, route: UiRoute): void {
    this.map = new RouteMap(this.scene, route, 'view', this.opts(s));
    uiCommands.pause();
  }

  private choose(id: string): void {
    const m = this.map;
    if (!m || m.mode !== 'choose') return;
    if (chooseNodeCmd(id)) {
      this.suppressUntil = this.scene.time.now + ROUTE_CANCEL_SUPPRESS_MS;
      // 61 단계 6: 고른 노드 자리를 적어 두고(전환이 그 입구로 파고든다) 지도는 덮일 때까지 남긴다
      const pos = m.nodePos(id);
      if (pos) noteTransitionOrigin('route', id, pos.x, pos.y, performance.now());
      this.map = undefined;
      this.leave(m);
    } else m.showMessage(routeText('chooseDenied'));
  }

  private leave(m: RouteMap): void {
    this.dropLeaving();
    m.freeze();
    this.leaving = m;
    const started = this.scene.time.now;
    const check = (): void => {
      if (this.leaving !== m) return;
      const waited = this.scene.time.now - started;
      // 전환이 시작되지 않았으면 예전처럼 치우고, 시작됐으면 덮임(onCovered)을 기다린다 — 끝내 안 오면 치운다
      if (!transitionBusy() || waited >= ROUTE_LEAVE_MAX_MS) this.dropLeaving();
      else this.leaveTimer = this.scene.time.delayedCall(100, check);
    };
    this.leaveTimer = this.scene.time.delayedCall(ROUTE_LEAVE_WAIT_MS, check);
    debugExpose('routeLeaving', { at: Math.round(performance.now()) });
  }

  /** 전환이 화면을 덮었다·끝났다: 남긴 지도를 치운다 */
  dropLeaving(): void {
    this.leaveTimer?.remove();
    this.leaveTimer = undefined;
    this.leaving?.destroy();
    this.leaving = undefined;
  }

  /** 지도를 닫는다. resume=true 면 게임을 재개한다 (보기 모드를 Tab·Esc 로 닫을 때) */
  close(resume: boolean): void {
    if (!this.map) return;
    this.map.destroy();
    this.map = undefined;
    if (resume) uiCommands.resume();
  }

  /**
   * 53라운드 Q47: 노드 고르기 중 Esc — 지도를 닫고 `cancelChoose()` (주인공이 출구에서 한 걸음 물러나는 것은 시스템 몫).
   * 취소는 재개와 같은 까닭으로 Esc 를 뗀 다음 프레임에 보낸다(취소로 풀린 게임 입력이 누르고 있는 Esc 를 받지 않게).
   * 그 사이 스냅샷의 `route.choosing` 이 아직 true 라도 안전망이 지도를 다시 열지 않게 잠깐 막는다.
   */
  cancelChoose(): void {
    this.close(false);
    this.suppressUntil = this.scene.time.now + ROUTE_CANCEL_SUPPRESS_MS;
    this.hooks.afterRelease('Escape', () => {
      const ok = cancelChooseCmd();
      debugExpose('routeCancel', { ok, at: this.scene.time.now });
    });
  }

  /**
   * 50라운드: 노드 지도 층의 큰 그림을 필요해진 때 한 번 읽어 둔다 — 그 층 지도 배경(MAP_BG_FLOORS), 지금 지역 키아트,
   * 바로 다음 단계(지금 노드의 links) 지역 키아트(다음 지역 카드·그림 속 입구가 기다리지 않게). 층·지금 노드가 바뀔 때만 확인한다.
   */
  prefetch(route: UiRoute, cur: UiRouteNode | null): void {
    const sig = `${route.floor}|${cur?.id ?? ''}`;
    if (sig === this.prefetchSig) return;
    this.prefetchSig = sig;
    const scene = this.scene;
    if (MAP_BG_FLOORS.includes(route.floor)) ensureImage(scene, mapBgKey(route.floor), mapBgUrl(route.floor));
    const next = cur ? route.nodes.filter((n) => cur.links.includes(n.id)) : [];
    const arts = new Set([cur, ...next].map((n) => regionArtKey(n?.region)).filter((a): a is string => Boolean(a)));
    for (const art of arts) ensureImage(scene, keyartKey(art), keyartUrl(art));
  }

  destroy(): void {
    this.map?.destroy();
    this.map = undefined;
    this.dropLeaving();
  }
}
