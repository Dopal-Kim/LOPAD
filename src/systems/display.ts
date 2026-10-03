/**
 * 52라운드 Q8 내부 렌더 1920×1080 (계약 art §11). 논리 좌표(960×540)는 그대로, 캔버스만 RENDER.RESOLUTION 배.
 *
 * 카메라 두 종류:
 * - **논리 카메라**(UI 씬·Setup·GameOver 등 화면 고정 씬): zoom = RESOLUTION, 원점 왼쪽 위 → 씬 좌표 (x, y) 가 그대로 논리 화면
 *   (x, y). scrollFactor 0 개체도 같은 자리. `installLogicalCameras` 가 씬 시작(READY, create 전)마다 main 카메라에 건다.
 * - **월드 카메라**(Game·WeaponLab, 회피 시험): 원점 가운데(추종·centerOn 계산 그대로), zoom = 논리 배율 × RESOLUTION (`worldZoom`).
 *
 * 포인터(`pointer.x/y`)는 실제 캔버스 px 다 — 논리 좌표가 필요하면 `toLogical` 또는 `pointer.worldX`(논리 카메라).
 * 창 표시 배율(`displayZoom`)은 52라운드 전과 같은 CSS 크기가 되도록 정한다.
 */
import type Phaser from 'phaser';
import { GAME, RENDER } from '../core/Constants';

export const RES = RENDER.RESOLUTION;
/** 실제 캔버스 크기 */
export const CANVAS_W = GAME.WIDTH * RES;
export const CANVAS_H = GAME.HEIGHT * RES;

/** 실제 캔버스 px → 논리 px */
export function toLogical(v: number): number {
  return v / RES;
}

/** 논리 배율(월드 1단위 = 논리 px 몇 개) → 실제 카메라 zoom */
export function worldZoom(logical: number): number {
  return logical * RES;
}

/** 카메라의 논리 배율 (실제 zoom ÷ RESOLUTION) */
export function logicalZoomOf(cam: Phaser.Cameras.Scene2D.Camera): number {
  return (cam.zoom || 1) / RES;
}

/**
 * 창 크기 → 캔버스 CSS 배율. 52라운드 전(960 캔버스 정수 배율)과 같은 표시 크기:
 * 논리 정수 배율 n = floor(min(창/960×540)), 최소 MIN_ZOOM → 캔버스 배율 n / RESOLUTION (1280×720 창 = 0.5, 1920×1080 = 1)
 */
export function displayZoom(winW: number, winH: number): number {
  const n = Math.floor(Math.min(winW / GAME.WIDTH, winH / GAME.HEIGHT));
  return Math.max(GAME.MIN_ZOOM, n) / RES;
}

/**
 * scrollFactor 0 개체를 논리 화면 (lx, ly) 에 논리 크기로 놓는 씬 좌표·배율 (카메라 종류 무관).
 * 화면 = (x - 원점) × zoom + 원점 + cam.x 를 거꾸로 푼다
 */
export function screenFixed(
  cam: Phaser.Cameras.Scene2D.Camera,
  lx: number,
  ly: number,
): { x: number; y: number; scale: number } {
  const z = cam.zoom || 1;
  const ox = cam.width * cam.originX;
  const oy = cam.height * cam.originY;
  return { x: (lx * RES - cam.x - ox) / z + ox, y: (ly * RES - cam.y - oy) / z + oy, scale: RES / z };
}

/** 월드 좌표 → 논리 화면 좌표 (계약 UiInteractable.screen 등) */
export function worldToLogicalScreen(
  cam: Phaser.Cameras.Scene2D.Camera,
  wx: number,
  wy: number,
): { x: number; y: number } {
  const z = cam.zoom || 1;
  const ox = cam.width * cam.originX;
  const oy = cam.height * cam.originY;
  return {
    x: toLogical((wx - cam.scrollX - ox) * z + ox + cam.x),
    y: toLogical((wy - cam.scrollY - oy) * z + oy + cam.y),
  };
}

const PATCHED = '__lopadLogicalView';
/** Phaser.Scenes.Events.READY · Phaser.Core.Events.READY (값만 — 이 파일은 Phaser 를 런타임 import 하지 않아 단위 테스트 가능) */
const SCENE_READY = 'ready';
const GAME_READY = 'ready';

/**
 * 논리 카메라로 만든다: zoom RESOLUTION · 원점 (0,0) · 스크롤 0. Phaser 의 worldView·midPoint 는 원점을 가운데로 가정해 계산하므로
 * (타일맵 컬링 등에 쓰임) 원점이 (0,0) 인 동안은 preRender 뒤에 바로잡는다
 */
export function makeLogicalCamera(cam: Phaser.Cameras.Scene2D.Camera): Phaser.Cameras.Scene2D.Camera {
  cam.setOrigin(0, 0).setZoom(RES).setScroll(0, 0).setRoundPixels(true);
  const c = cam as Phaser.Cameras.Scene2D.Camera & { [PATCHED]?: boolean };
  if (!c[PATCHED]) {
    c[PATCHED] = true;
    const base = cam.preRender.bind(cam);
    cam.preRender = () => {
      base();
      if (cam.originX !== 0 || cam.originY !== 0) return;
      const w = cam.width / (cam.zoomX || 1);
      const h = cam.height / (cam.zoomY || 1);
      cam.worldView.setTo(cam.scrollX, cam.scrollY, w, h);
      cam.midPoint.set(cam.scrollX + w / 2, cam.scrollY + h / 2);
    };
  }
  return cam;
}

/**
 * 씬 코드가 보는 `this.scale` 을 논리 크기로 (52라운드 호환 층): width·height·gameSize·baseSize 가 960×540 이고 나머지(이벤트·
 * transformX 등)는 실제 ScaleManager 그대로. Phaser 내부는 `sys.scale`(실제)을 쓰므로 영향이 없다.
 * UI 씬이 `this.scale.width` 로 배치해도 논리 960×540 에 맞게 놓이도록 — UI 파트가 계약 상수로 옮기면 걷어낼 수 있다
 */
export function logicalScaleView(real: Phaser.Scale.ScaleManager): Phaser.Scale.ScaleManager {
  const passthrough = <T extends object>(t: T, p: PropertyKey) => {
    const v = Reflect.get(t, p, t) as unknown;
    return typeof v === 'function' ? (v as (...a: unknown[]) => unknown).bind(t) : v;
  };
  const size = (s: Phaser.Structs.Size) =>
    new Proxy(s, {
      get: (t, p) => (p === 'width' ? GAME.WIDTH : p === 'height' ? GAME.HEIGHT : passthrough(t, p)),
    });
  const sizes = new Map<PropertyKey, Phaser.Structs.Size>();
  return new Proxy(real, {
    get(t, p) {
      if (p === 'width') return GAME.WIDTH;
      if (p === 'height') return GAME.HEIGHT;
      if (p === 'gameSize' || p === 'baseSize') {
        let v = sizes.get(p);
        if (!v) sizes.set(p, (v = size(t[p])));
        return v;
      }
      return passthrough(t, p);
    },
  });
}

/**
 * 모든 씬의 main 카메라를 시작 때(READY = create 직전) 논리 카메라로. 월드 카메라를 직접 다루는 씬(`skip`)은 건너뛴다.
 * UI 씬(src/ui)도 이 훅으로 960×540 좌표 그대로 그린다 — UI 코드는 바꾸지 않는다
 */
export function installLogicalCameras(game: Phaser.Game, skip: readonly string[]): void {
  const attach = () => {
    for (const scene of game.scene.scenes) {
      if (skip.includes(scene.sys.settings.key)) continue;
      // 씬 코드의 this.scale → 논리 크기 (Phaser 내부는 sys.scale)
      (scene as { scale: Phaser.Scale.ScaleManager }).scale = logicalScaleView(scene.sys.scale);
      scene.sys.events.on(SCENE_READY, () => makeLogicalCamera(scene.cameras.main));
      // 이미 시작된 씬(첫 씬 Boot 는 씬 목록이 만들어지는 같은 순간에 시작된다)
      if (scene.sys.isActive() && scene.cameras?.main) makeLogicalCamera(scene.cameras.main);
    }
  };
  // 씬 인스턴스는 게임 READY(텍스처 준비) 때 만들어진다 (SceneManager 가 먼저 구독)
  if (game.isRunning) attach();
  else game.events.once(GAME_READY, attach);
}
