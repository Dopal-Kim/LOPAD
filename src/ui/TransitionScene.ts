import Phaser from 'phaser';
import { UI_EVENTS, UI_SCREEN, uiBus, uiCommands, type UiTransitionBegin } from '../contract/ui';
import { debugExpose, debugTune } from './debug';
import { ensureImage, keyartKey, keyartUrl, mapBgKey } from './kit';
import { UI_SCENE_KEYS } from './keys';
import { brushOrderFrom, coverPixels, fallbackDoor, makeCanvas, paintedCanvas, readPixels, type Img } from './paintFx';
import { artJson, artTex, paintUrl, uiCopy } from './paintArt';
import { regionArtKey } from './regionView';
import { FLOOR1_RAMP, GRAY, SEPIA, hexToNum } from './theme';
import { TRANSITION } from './themeTransition';
import { setTransitionBusy, setTransitionCovered, takeTransitionOrigin } from './transitionState';
import {
  clamp01,
  diveFocus,
  diveZoom,
  easeIn,
  easeInOut,
  easeOut,
  freezeAlpha,
  planFor,
  readBegin,
  readDoorMeta,
  readId,
  regionKeyart,
  revealAlpha,
  skipAction,
  smooth,
  worldTransform,
  type BeginInfo,
  type DoorRect,
  type TransitionPlan,
} from './transitionView';

type Phase = 'prep' | 'intro' | 'frame' | 'move' | 'covered' | 'reveal';

/** 그림 한 장 (입구 그림·키아트) — 텍스처 키 · 크기 · 입구 사각형 · 안쪽 빛 */
interface Painting {
  key: string;
  w: number;
  h: number;
  rect: DoorRect;
  light: string;
}

interface Run {
  info: BeginInfo;
  plan: TransitionPlan;
  phase: Phase;
  phaseAt: number;
  startedAt: number;
  ready: boolean;
  /** 건너뛰기를 눌렀다 (READY 뒤 걷힘을 짧게) */
  fast: boolean;
  revealMs: number;
  covered: boolean;
  shook: boolean;
  waitShown: boolean;
  settings: { shake: number; flash: boolean };
  objs: Phaser.GameObjects.GameObject[];
  world?: Phaser.GameObjects.Container;
  dim?: Phaser.GameObjects.Rectangle;
  paper?: Phaser.GameObjects.Image;
  art?: Phaser.GameObjects.Container;
  pic?: Phaser.GameObjects.Container;
  frame?: Phaser.GameObjects.Container;
  target: { x: number; y: number };
  zEnd: number;
  /** 'exitRoom' 굳음: 붓 그림 RGBA · 출구에서의 거리 · 잡음 */
  freeze?: { px: Uint8ClampedArray; dist: Float32Array; noise: Float32Array; done: boolean };
  order: Float32Array;
  /** 붓질 앞쪽 부드러움 (그림 마스크 0.05 · 코드 붓질 0.14) */
  soft: number;
  cover: Uint8ClampedArray;
  light: string;
  painting?: Painting;
  /** 입구 그림을 직접 읽어 봤다 (한 번만) */
  doorTried?: boolean;
}

const CAP_KEY = 'ui-tr-cap';
const DOOR_KEY = 'ui-tr-door';
const VEIL_KEY = 'ui-tr-veil';
const PAINT_KEY = 'ui-tr-paint';
const PAPER_KEY = 'ui-tr-paper';
/** 대체 그림 크기 (입구 그림 규격 640×360, 키아트 큰 그림 800×450) */
/** 방 → 지도 전환인가 */
const exitMode = (m: string): boolean => m === 'exitRoom';
const DOOR_W = 640;
const DOOR_H = 360;
const ART_W = 800;
const ART_H = 450;
/** 키아트를 아직 못 읽었을 때 기다리는 최대 시간 (넘으면 종이 바탕) */
const ART_WAIT_MS = 350;
/** 층 전환은 키아트가 주인공이라 조금 더 기다린다 (시스템 덮임 안전장치 3초 안) */
const ART_WAIT_FLOOR_MS = 900;
/** 붓 마스크 번호 (아트 §28): 0 가로 · 1 대각 · 2 가운데에서 바깥(입구용) · 3 세로 */
const MASK_ENTER = 2;
const MASK_EXIT = [0, 1, 3] as const;
/** 액자 그림 9-slice 여백(그림 픽셀) · 표시 배율 · 그림 둘레로 내미는 폭(논리 px) · 이 폭 이상에서만 그림 액자 */
const FRAME_SLICE = 44;
const FRAME_SCALE = 0.5;
const FRAME_OUT = 16;
const FRAME_MIN_W = 300;
/** 캡처가 오지 않을 때 기다리는 최대 시간 */
const CAP_WAIT_MS = 250;

const PW = TRANSITION.paintW;
const PH = TRANSITION.paintH;

/**
 * 61 단계 6 (P14 §3, 계약 §19) 그림 속 입구 전환 씬 — 모든 UI 씬 위에 떠 있고, `ui:transition-begin` 때만 그린다.
 * - 'enterNode'·'training': 지금 화면(노드 지도·수련장 지도)을 캡처해 두고, 고른 노드 자리에서 입구 그림(`doorKey`, 없으면 지역 키아트 +
 *   붓으로 그린 입구)이 액자로 피어난 뒤 입구 사각형으로 파고든다 → 입구 안 어둠이 화면을 채움(`ui:transition-covered`) →
 *   시스템 `ui:transition-ready` 뒤 먹 붓질(`paint/brush_reveal_*`, 없으면 코드 붓질)로 걷히며 방이 드러남 → `ui:transition-end`.
 * - 'exitRoom': 방 화면을 캡처해 출구 자리에서부터 붓 그림으로 굳히고(색 줄임·먹 윤곽·종이 결·가장자리 번짐) 액자를 둘러 줌 아웃,
 *   두루마리(지도 바탕·종이)가 덮음 → READY 뒤 지도가 드러남.
 * - 'floor': 다음 지역 키아트 큰 그림이 액자로 떠오르고 그 입구로 파고든다.
 * 아무 키·클릭 = 건너뛰기(`skippable`). 설정 흔들림 배율·섬광 끔을 따른다. 셰이더 없음(캔버스 처리 + 선형 필터).
 */
export class TransitionScene extends Phaser.Scene {
  private run: Run | null = null;
  private veil?: Phaser.GameObjects.Image;
  private veilTex?: Phaser.Textures.CanvasTexture;
  private veilData?: ImageData;
  private waitDots?: Phaser.GameObjects.Graphics;
  private flashRect?: Phaser.GameObjects.Rectangle;
  private handlers: [string, (p: never) => void][] = [];
  private seq = 0;
  /** 붓질 순서 캐시 (마스크 그림 키 또는 코드 붓질 번호) */
  private orders = new Map<string, Float32Array>();

  constructor() {
    super(UI_SCENE_KEYS.TRANSITION);
  }

  create(): void {
    this.run = null;
    this.seq = 0;
    const veilTex = this.textures.exists(VEIL_KEY)
      ? (this.textures.get(VEIL_KEY) as Phaser.Textures.CanvasTexture)
      : this.textures.createCanvas(VEIL_KEY, PW, PH);
    if (!veilTex) return;
    veilTex.setFilter(Phaser.Textures.FilterMode.LINEAR);
    this.veilTex = veilTex;
    this.veilData = veilTex.getContext().createImageData(PW, PH);
    this.veil = this.add
      .image(0, 0, VEIL_KEY)
      .setOrigin(0, 0)
      .setScale(UI_SCREEN.WIDTH / PW, UI_SCREEN.HEIGHT / PH)
      .setDepth(10)
      .setVisible(false);
    // 아트 붓 마스크·액자를 미리 읽어 둔다 (없으면 코드 붓질·코드 액자)
    // (시스템이 이미 읽었으면 그것을 쓰고, 아니면 UI 사본 키로 — paintArt.ts)
    for (let n = 0; n < 4; n++) {
      const key = `paint/brush_reveal_${n}`;
      if (!artTex(this, key)) ensureImage(this, uiCopy(key), `${paintUrl(key)}.png`);
    }
    if (!artTex(this, 'paint/frame'))
      ensureImage(this, uiCopy('paint/frame'), `${paintUrl('paint/frame')}.png`, (ok) => {
        if (ok) this.textures.get(uiCopy('paint/frame')).setFilter(Phaser.Textures.FilterMode.LINEAR);
      });
    this.waitDots = this.add.graphics().setDepth(30).setVisible(false);
    this.flashRect = this.add
      .rectangle(0, 0, UI_SCREEN.WIDTH, UI_SCREEN.HEIGHT, 0xffffff, 1)
      .setOrigin(0, 0)
      .setDepth(31)
      .setVisible(false);
    this.on(UI_EVENTS.TRANSITION_BEGIN, (p: UiTransitionBegin) => this.begin(p));
    this.on(UI_EVENTS.TRANSITION_READY, (p: unknown) => this.onReady(p));
    this.input.keyboard?.on('keydown', this.onKey);
    this.input.on('pointerdown', this.onPointer);
    this.events.once('shutdown', () => {
      this.input.keyboard?.off('keydown', this.onKey);
      this.input.off('pointerdown', this.onPointer);
      for (const [e, h] of this.handlers) uiBus.off(e, h);
      this.handlers = [];
      if (this.run) this.clearRun();
      setTransitionBusy(false);
    });
  }

  private on<T>(event: string, handler: (p: T) => void): void {
    uiBus.on(event, handler);
    this.handlers.push([event, handler as (p: never) => void]);
  }

  // ---------------------------------------------------------------------------------------------
  private begin(p: unknown): void {
    const info = readBegin(p);
    if (!info) return;
    // 앞 전환이 아직이면 바로 끝낸다 (덮임·끝 알림은 빠짐없이)
    if (this.run) this.finish(true);
    this.scene.bringToTop();
    setTransitionBusy(true);
    const now = this.time.now;
    const settings = uiCommands.getUiSnapshot().settings;
    const plan = planFor(info.mode);
    const center = { x: UI_SCREEN.WIDTH / 2, y: UI_SCREEN.HEIGHT / 2 };
    const wallNow = performance.now();
    const origin =
      info.mode === 'enterNode'
        ? (takeTransitionOrigin('route', info.nodeId, wallNow) ?? info.from)
        : info.mode === 'training'
          ? (takeTransitionOrigin('training', info.nodeId, wallNow) ?? info.from)
          : info.from;
    this.seq += 1;
    const run: Run = {
      info,
      plan,
      phase: 'prep',
      phaseAt: now,
      startedAt: now,
      ready: false,
      fast: false,
      revealMs: plan.revealMs,
      covered: false,
      shook: false,
      waitShown: false,
      settings: { shake: clamp01(settings?.shake ?? 1), flash: settings?.flash !== false },
      objs: [],
      target: origin ? { x: origin.x, y: origin.y } : center,
      zEnd: 1,
      order: new Float32Array(0),
      soft: TRANSITION.brushSoft,
      cover: new Uint8ClampedArray(0),
      light: SEPIA[5],
    };
    this.run = run;
    debugExpose('transition', { id: info.id, mode: info.mode, phase: 'prep' });
    // 1) 지금 화면 캡처 → 2) 그림 준비 → 3) 시작
    this.capture((cap) => {
      if (this.run !== run) return;
      this.prepareArt(run, (painting) => {
        if (this.run !== run) return;
        this.build(run, cap, painting);
        this.setPhase(run, 'intro');
      });
    });
  }

  /**
   * 지금 화면을 논리 크기(960×540) 캔버스로 — 렌더 직후(같은 작업 안) 게임 캔버스를 그대로 줄여 그린다.
   * WebGL 버퍼가 비어 있으면(알파 0) renderer.snapshot 으로 한 번 더. 그래도 안 오면 null.
   */
  private capture(done: (c: HTMLCanvasElement | null) => void): void {
    let finished = false;
    const finish = (c: HTMLCanvasElement | null): void => {
      if (finished) return;
      finished = true;
      done(c);
    };
    const W = UI_SCREEN.WIDTH;
    const H = UI_SCREEN.HEIGHT;
    const toCanvas = (src: CanvasImageSource): HTMLCanvasElement => {
      const c = makeCanvas(W, H);
      const ctx = c.getContext('2d', { willReadFrequently: true });
      if (ctx) {
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        ctx.drawImage(src, 0, 0, W, H);
      }
      return c;
    };
    const blank = (c: HTMLCanvasElement): boolean => {
      const ctx = c.getContext('2d', { willReadFrequently: true });
      if (!ctx) return true;
      const d = ctx.getImageData(W / 2 - 8, H / 2 - 8, 16, 16).data;
      for (let i = 3; i < d.length; i += 4) if (d[i] !== 0) return false;
      return true;
    };
    this.game.events.once(Phaser.Core.Events.POST_RENDER, () => {
      const c = toCanvas(this.game.canvas);
      if (!blank(c)) {
        finish(c);
        return;
      }
      this.game.renderer.snapshot(
        (img) => {
          if (img instanceof HTMLImageElement) finish(toCanvas(img));
          else finish(null);
        },
        'image/jpeg',
        0.9,
      );
    });
    this.time.delayedCall(CAP_WAIT_MS, () => finish(null));
  }

  /** 입구 그림·키아트 준비 (exitRoom 은 없음) */
  private prepareArt(run: Run, done: (p: Painting | null) => void): void {
    const info = run.info;
    if (info.mode === 'exitRoom') {
      done(null);
      return;
    }
    const lightDefault = ['shop', 'rest', 'event', 'training'].includes(info.nodeKind) ? FLOOR1_RAMP[7] : SEPIA[5];
    // 0) 입구 그림 키를 받았는데 아직 안 읽혔으면 아트 경로에서 읽어 본다 (그림 + 같은 키 메타 JSON, 잠깐만 기다림)
    if (info.doorKey && !artTex(this, info.doorKey) && !run.doorTried) {
      run.doorTried = true;
      this.loadDoor(info.doorKey, () => {
        if (this.run === run) this.prepareArt(run, done);
      });
      return;
    }
    // 1) 시스템이 로드한 입구 그림
    const doorTex = artTex(this, info.doorKey);
    if (info.doorKey && doorTex) {
      const tex = this.textures.get(doorTex);
      tex.setFilter(Phaser.Textures.FilterMode.LINEAR);
      const src = tex.getSourceImage() as Img;
      const meta = readDoorMeta(artJson(this, info.doorKey) ?? this.texMeta(tex), src.width, src.height);
      const rect = meta.rect ?? {
        x: Math.round(src.width * 0.42),
        y: Math.round(src.height * 0.4),
        w: Math.round(src.width * 0.16),
        h: Math.round(src.height * 0.45),
      };
      done({ key: doorTex, w: src.width, h: src.height, rect, light: meta.light ?? lightDefault });
      return;
    }
    // 2) 지역 키아트 위에 붓으로 그린 입구 (없으면 종이 + 먹 번짐)
    const artKey = regionKeyart(info.region) ?? regionArtKey(info.region);
    const floor = info.mode === 'floor';
    const make = (base: Img | null): void => {
      const w = floor ? ART_W : DOOR_W;
      const h = floor ? ART_H : DOOR_H;
      if (floor && base) {
        // 층: 다음 지역 키아트 큰 그림(붓 그림 처리) 가운데로 (키아트 doorRect 는 아직 없다 — 아트 §28)
        const c = paintedCanvas(base, w, h, (info.id * 7919 + this.seq) >>> 0);
        if (this.textures.exists(DOOR_KEY)) this.textures.remove(DOOR_KEY);
        this.textures.addCanvas(DOOR_KEY, c)?.setFilter(Phaser.Textures.FilterMode.LINEAR);
        const rw = Math.round(w * 0.16);
        const rh = Math.round(h * 0.3);
        done({ key: DOOR_KEY, w, h, rect: { x: (w - rw) / 2, y: (h - rh) / 2, w: rw, h: rh }, light: lightDefault });
        return;
      }
      const kind = floor ? info.nodeKind || 'boss' : info.nodeKind;
      const fb = fallbackDoor(base, w, h, kind, lightDefault, (info.id * 7919 + this.seq) >>> 0);
      if (this.textures.exists(DOOR_KEY)) this.textures.remove(DOOR_KEY);
      const tex = this.textures.addCanvas(DOOR_KEY, fb.canvas);
      tex?.setFilter(Phaser.Textures.FilterMode.LINEAR);
      done({ key: DOOR_KEY, w, h, rect: fb.rect, light: lightDefault });
    };
    if (!artKey) {
      make(null);
      return;
    }
    const k = keyartKey(artKey);
    if (this.textures.exists(k)) {
      make(this.textures.get(k).getSourceImage() as Img);
      return;
    }
    let waited = false;
    const timer = this.time.delayedCall(floor ? ART_WAIT_FLOOR_MS : ART_WAIT_MS, () => {
      waited = true;
      make(null);
    });
    ensureImage(this, k, keyartUrl(artKey), (ok) => {
      if (waited) return;
      timer.remove();
      make(ok && this.textures.exists(k) ? (this.textures.get(k).getSourceImage() as Img) : null);
    });
  }

  /** 입구 그림 `paint/door_*` 를 UI 사본 키로 읽기 (그림 + 메타 JSON). 다 읽거나 ART_WAIT_FLOOR_MS 가 지나면 done 한 번 */
  private loadDoor(key: string, done: () => void): void {
    const copy = uiCopy(key);
    let finished = false;
    const finish = (): void => {
      if (finished) return;
      finished = true;
      done();
    };
    let left = 2;
    const step = (): void => {
      left -= 1;
      if (left <= 0) finish();
    };
    ensureImage(this, copy, `${paintUrl(key)}.png`, step);
    if (artJson(this, key)) step();
    else {
      this.load.once(`filecomplete-json-${copy}`, step);
      this.load.json(copy, `${paintUrl(key)}.json`);
      if (!this.load.isLoading()) this.load.start();
    }
    this.time.delayedCall(ART_WAIT_FLOOR_MS, finish);
  }

  /** 텍스처에 붙은 메타 (customData) */
  private texMeta(tex: Phaser.Textures.Texture): unknown {
    return (tex as unknown as { customData?: unknown }).customData ?? null;
  }

  // ---------------------------------------------------------------------------------------------
  private build(run: Run, cap: HTMLCanvasElement | null, painting: Painting | null): void {
    const W = UI_SCREEN.WIDTH;
    const H = UI_SCREEN.HEIGHT;
    const info = run.info;
    const seed = (info.id * 2654435761 + this.seq) >>> 0;
    if (this.textures.exists(CAP_KEY)) this.textures.remove(CAP_KEY);
    let capImg: Phaser.GameObjects.Image | null = null;
    if (cap) {
      this.textures.addCanvas(CAP_KEY, cap)?.setFilter(Phaser.Textures.FilterMode.LINEAR);
      capImg = this.add.image(0, 0, CAP_KEY).setOrigin(0, 0);
    }
    run.painting = painting ?? undefined;
    run.light = painting?.light ?? SEPIA[5];
    // 붓질 순서: 마스크 그림 4장 중 하나 (없으면 코드 붓질 4가지 중 하나)
    const maskN = exitMode(info.mode) ? MASK_EXIT[info.id % MASK_EXIT.length] : MASK_ENTER;
    const mask = this.brushOrder(maskN);
    run.order = mask.order;
    run.soft = mask.soft;
    const exit = exitMode(info.mode);
    const under =
      exit && this.textures.exists(mapBgKey(1)) ? (this.textures.get(mapBgKey(1)).getSourceImage() as Img) : null;
    run.cover = coverPixels(exit ? 'paper' : 'dark', PW, PH, run.light, seed, under);
    this.writeVeil(run, () => 255);
    this.veil
      ?.setAlpha(0)
      .setVisible(true)
      .setDepth(exit ? 10 : 20);

    if (exit) {
      // 방 화면 → (굳음) 붓 그림 + 액자 → 줌 아웃
      const pic = this.add.container(W / 2, H / 2).setDepth(25);
      if (capImg) pic.add(capImg.setPosition(-W / 2, -H / 2));
      if (cap) {
        const painted = paintedCanvas(cap, PW, PH, seed);
        const px = readPixels(painted);
        this.canvasTexture(PAINT_KEY, PW, PH);
        const img = this.add
          .image(-W / 2, -H / 2, PAINT_KEY)
          .setOrigin(0, 0)
          .setScale(W / PW, H / PH);
        pic.add(img);
        const from = info.from ?? { x: W / 2, y: H / 2 };
        const fx = (from.x / W) * PW;
        const fy = (from.y / H) * PH;
        const maxD = Math.hypot(Math.max(fx, PW - fx), Math.max(fy, PH - fy));
        const dist = new Float32Array(PW * PH);
        const noise = new Float32Array(PW * PH);
        for (let i = 0; i < PW * PH; i++) {
          dist[i] = Math.hypot((i % PW) - fx, Math.floor(i / PW) - fy) / maxD;
          noise[i] = run.order[i] ?? 0.5;
        }
        run.freeze = { px, dist, noise, done: false };
        this.writeFreeze(run, 0);
      }
      const frame = this.frameBox(-W / 2, -H / 2, W, H).setAlpha(0);
      pic.add(frame);
      run.pic = pic;
      run.frame = frame;
      run.objs.push(pic);
      return;
    }

    // enterNode·training·floor: 세계(캡처 + 그림) 를 파고든다
    const world = this.add.container(0, 0).setDepth(5);
    if (capImg) world.add(capImg);
    const dim = this.add.rectangle(0, 0, W, H, hexToNum(GRAY[0]), 1).setOrigin(0, 0).setAlpha(0);
    world.add(dim);
    run.dim = dim;
    const p = painting as Painting;
    const floor = info.mode === 'floor';
    let artCx: number;
    let artCy: number;
    let s: number;
    if (floor) {
      // 종이 바탕 + 가운데 큰 액자
      const paperTex = this.canvasTexture(PAPER_KEY, PW, PH);
      const ctx = paperTex.getContext();
      const cov = coverPixels('paper', PW, PH, run.light, seed + 3);
      const id = ctx.createImageData(PW, PH);
      id.data.set(cov);
      ctx.putImageData(id, 0, 0);
      paperTex.refresh();
      run.paper = this.add
        .image(0, 0, PAPER_KEY)
        .setOrigin(0, 0)
        .setScale(W / PW, H / PH)
        .setAlpha(0);
      world.add(run.paper);
      s = (W * TRANSITION.floorArtW) / p.w;
      artCx = W / 2;
      artCy = H / 2;
    } else {
      s = TRANSITION.bloomW / p.w;
      artCx = run.target.x;
      artCy = run.target.y;
    }
    const art = this.add.container(artCx, artCy);
    const dw = p.w * s;
    const dh = p.h * s;
    const frame = this.frameBox(
      -dw / 2,
      -dh / 2,
      dw,
      dh,
      floor ? TRANSITION.frameW : Math.max(2, TRANSITION.frameW * 0.35),
    );
    const img = this.add.image(0, 0, p.key).setScale(s).setOrigin(0.5, 0.5);
    art.add([img, frame]);
    art.setAlpha(0);
    world.add(art);
    run.art = art;
    run.world = world;
    run.objs.push(world);
    // 파고들 목표: 입구 사각형 가운데 (세계 좌표), 끝 배율: 입구가 화면을 덮을 만큼
    const rcx = artCx + (p.rect.x + p.rect.w / 2 - p.w / 2) * s;
    const rcy = artCy + (p.rect.y + p.rect.h / 2 - p.h / 2) * s;
    run.target = { x: rcx, y: rcy };
    // 시작 초점은 화면 그대로 — 목표 자리는 세계 좌표의 그 점
    run.zEnd = TRANSITION.diveCover * Math.max(H / (p.rect.h * s), W / (p.rect.w * s));
  }

  private canvasTexture(key: string, w: number, h: number): Phaser.Textures.CanvasTexture {
    if (this.textures.exists(key)) this.textures.remove(key);
    const t = this.textures.createCanvas(key, w, h) as Phaser.Textures.CanvasTexture;
    t.setFilter(Phaser.Textures.FilterMode.LINEAR);
    return t;
  }

  /** 붓질 순서 (마스크 그림 `paint/brush_reveal_{n}` — `v <= p·255` 이면 걷힘, 없으면 코드 붓질) — 번호마다 한 번만 만든다 */
  private brushOrder(n: number): { order: Float32Array; soft: number } {
    const key = artTex(this, `paint/brush_reveal_${n}`);
    const has = Boolean(key);
    const cacheKey = key ?? `code${n}`;
    let o = this.orders.get(cacheKey);
    if (!o) {
      o = brushOrderFrom(key ? (this.textures.get(key).getSourceImage() as Img) : null, PW, PH, 1009 + n * 7);
      this.orders.set(cacheKey, o);
    }
    return { order: o, soft: has ? TRANSITION.maskSoft : TRANSITION.brushSoft };
  }

  /** 액자: 코드 액자(옻칠 나무 · 바랜 금 선 · 안쪽 그늘) + 그림 `paint/frame`(9-slice) 이 있으면 그 위에 */
  private frameBox(
    x: number,
    y: number,
    w: number,
    h: number,
    t: number = TRANSITION.frameW,
  ): Phaser.GameObjects.Container {
    const box = this.add.container(0, 0);
    const g = this.add.graphics();
    const m = Math.max(1, Math.round(t * 0.3));
    const inner = Math.max(1, t - m * 2);
    g.fillStyle(hexToNum(SEPIA[1]), 1);
    g.fillRect(x - t, y - t, w + t * 2, t);
    g.fillRect(x - t, y + h, w + t * 2, t);
    g.fillRect(x - t, y, t, h);
    g.fillRect(x + w, y, t, h);
    g.fillStyle(hexToNum(SEPIA[3]), 1);
    g.fillRect(x - t + m, y - t + m, w + (t - m) * 2, inner);
    g.fillRect(x - t + m, y + h + m, w + (t - m) * 2, inner);
    g.fillRect(x - t + m, y, inner, h);
    g.fillRect(x + w + m, y, inner, h);
    g.lineStyle(1, hexToNum(SEPIA[5]), 0.9).strokeRect(x - 1.5, y - 1.5, w + 3, h + 3);
    g.lineStyle(1, hexToNum(GRAY[0]), 0.8).strokeRect(x - 0.5, y - 0.5, w + 1, h + 1);
    const frameTex = artTex(this, 'paint/frame');
    if (w >= FRAME_MIN_W && frameTex) {
      // 아트 액자 (128×128, 9-slice 여백 44, 가운데 투명) — 0.5배로 그림 둘레에
      g.destroy();
      const o = FRAME_OUT;
      const k = FRAME_SCALE;
      const sl = FRAME_SLICE;
      box.add(
        this.add
          .nineslice(x - o, y - o, frameTex, undefined, (w + o * 2) / k, (h + o * 2) / k, sl, sl, sl, sl)
          .setOrigin(0, 0)
          .setScale(k),
      );
      return box;
    }
    box.add(g);
    return box;
  }

  // ---------------------------------------------------------------------------------------------
  /** 덮개 캔버스: 덮개 색 + 알파(점마다) */
  private writeVeil(run: Run, alpha: (i: number) => number): void {
    const tex = this.veilTex;
    const data = this.veilData;
    if (!tex || !data || run.cover.length < PW * PH * 4) return;
    const d = data.data;
    const c = run.cover;
    for (let i = 0, n = PW * PH; i < n; i++) {
      const p = i * 4;
      d[p] = c[p];
      d[p + 1] = c[p + 1];
      d[p + 2] = c[p + 2];
      d[p + 3] = alpha(i);
    }
    tex.getContext().putImageData(data, 0, 0);
    tex.refresh();
  }

  /** 'exitRoom' 굳음: 출구에서부터 붓 그림이 번져 나간다 */
  private writeFreeze(run: Run, t: number): void {
    const f = run.freeze;
    if (!f || f.done || !this.textures.exists(PAINT_KEY)) return;
    const tex = this.textures.get(PAINT_KEY) as Phaser.Textures.CanvasTexture;
    const ctx = tex.getContext();
    const img = ctx.createImageData(PW, PH);
    const d = img.data;
    d.set(f.px);
    for (let i = 0, n = PW * PH; i < n; i++) d[i * 4 + 3] = Math.round(freezeAlpha(f.dist[i], f.noise[i], t) * 255);
    ctx.putImageData(img, 0, 0);
    tex.refresh();
    if (t >= 1) f.done = true;
  }

  private setPhase(run: Run, phase: Phase): void {
    run.phase = phase;
    run.phaseAt = this.time.now;
    debugExpose('transition', { id: run.info.id, mode: run.info.mode, phase, ready: run.ready });
  }

  update(time: number): void {
    const run = this.run;
    if (!run || run.phase === 'prep') return;
    const P = run.plan;
    // 디버그(uidebug): 단계별 캡처를 위해 느리게
    const el = (time - run.phaseAt) / debugTune('transitionSlow', 1);
    switch (run.phase) {
      case 'intro': {
        const t = clamp01(el / Math.max(1, P.introMs));
        this.drawIntro(run, t);
        if (t >= 1) this.setPhase(run, P.frameMs > 0 ? 'frame' : 'move');
        break;
      }
      case 'frame': {
        const t = clamp01(el / Math.max(1, P.frameMs));
        this.drawFrameIn(run, t);
        if (t >= 1) this.setPhase(run, 'move');
        break;
      }
      case 'move': {
        const t = clamp01(el / Math.max(1, P.moveMs));
        this.drawMove(run, t);
        if (t >= 1) this.toCovered(run);
        break;
      }
      case 'covered': {
        if (run.ready) {
          this.startReveal(run);
          break;
        }
        if (!run.waitShown && el >= TRANSITION.waitHintMs) {
          run.waitShown = true;
          this.waitDots?.setVisible(true);
        }
        if (run.waitShown) this.drawWait(el);
        if (el >= TRANSITION.failsafeMs) {
          console.warn(`[ui] 전환 ${run.info.id}: READY 가 ${TRANSITION.failsafeMs}ms 동안 오지 않아 덮개를 걷는다`);
          this.startReveal(run);
        }
        break;
      }
      case 'reveal': {
        const t = clamp01(el / Math.max(1, run.revealMs));
        this.drawReveal(run, t);
        if (t >= 1) this.finish(false);
        break;
      }
    }
  }

  private drawIntro(run: Run, t: number): void {
    const mode = run.info.mode;
    if (mode === 'exitRoom') {
      this.writeFreeze(run, easeOut(t));
      return;
    }
    if (mode === 'floor') {
      const e = easeOut(t);
      run.paper?.setAlpha(e);
      run.art?.setAlpha(e).setScale(0.92 + 0.08 * e);
      return;
    }
    // 노드 자리에서 입구 그림이 피어난다
    const e = easeOut(t);
    run.art?.setAlpha(e).setScale(0.5 + 0.5 * e);
    run.dim?.setAlpha(0.35 * e);
  }

  private drawFrameIn(run: Run, t: number): void {
    const e = easeInOut(t);
    run.frame?.setAlpha(e);
    run.pic?.setScale(1 - 0.06 * e);
    this.veil?.setAlpha(e);
  }

  private drawMove(run: Run, t: number): void {
    const W = UI_SCREEN.WIDTH;
    const H = UI_SCREEN.HEIGHT;
    if (run.info.mode === 'exitRoom') {
      const e = easeInOut(t);
      run.pic?.setScale(0.94 + (TRANSITION.zoomOutTo - 0.94) * e);
      this.veil?.setAlpha(1);
      return;
    }
    const center = { x: W / 2, y: H / 2 };
    const z = diveZoom(t, run.zEnd);
    const f = diveFocus(easeInOut(t), z, run.target, center);
    const tr = worldTransform(f, z, center);
    run.world?.setPosition(tr.x, tr.y).setScale(tr.scale);
    // 마지막에 입구 안 어둠이 짙어진다
    this.veil?.setAlpha(smooth(TRANSITION.darkenFrom, 1, t));
    if (!run.shook && t >= 0.8 && run.settings.shake > 0) {
      run.shook = true;
      this.cameras.main.shake(TRANSITION.shakeMs, (TRANSITION.shakePx * run.settings.shake) / W);
    }
  }

  private toCovered(run: Run): void {
    if (run.covered) return;
    run.covered = true;
    // 덮였다: 세계(캡처·그림)는 이제 보이지 않는다
    run.world?.setVisible(false);
    if (run.info.mode === 'exitRoom') {
      if (run.freeze) this.writeFreeze(run, 1);
      run.frame?.setAlpha(1);
      run.pic?.setScale(TRANSITION.zoomOutTo);
    }
    this.veil?.setAlpha(1);
    if (run.info.mode !== 'exitRoom' && run.settings.flash && !run.fast) this.flash(run.light);
    this.setPhase(run, 'covered');
    setTransitionCovered();
    uiBus.emit(UI_EVENTS.TRANSITION_COVERED, { id: run.info.id });
  }

  private flash(color: string): void {
    const r = this.flashRect;
    if (!r) return;
    r.setFillStyle(hexToNum(color), 1).setAlpha(TRANSITION.flashAlpha).setVisible(true);
    this.tweens.add({
      targets: r,
      alpha: 0,
      duration: TRANSITION.flashMs,
      onComplete: () => r.setVisible(false),
    });
  }

  private startReveal(run: Run): void {
    this.waitDots?.setVisible(false);
    run.revealMs = run.fast ? TRANSITION.skipRevealMs : run.plan.revealMs;
    this.setPhase(run, 'reveal');
  }

  private drawReveal(run: Run, t: number): void {
    const order = run.order;
    this.writeVeil(run, (i) => Math.round(revealAlpha(order[i] ?? 1, t, run.soft) * 255));
    if (run.pic) {
      // 액자 그림은 지도 위에 놓이듯 작아지며 사라진다
      const e = easeIn(clamp01(t / 0.6));
      run.pic.setScale(TRANSITION.zoomOutTo * (1 - 0.5 * e)).setAlpha(1 - e);
    }
  }

  private drawWait(el: number): void {
    const g = this.waitDots;
    if (!g) return;
    g.clear();
    const x0 = UI_SCREEN.WIDTH - 48;
    const y = UI_SCREEN.HEIGHT - 24;
    for (let i = 0; i < 3; i++) {
      const a = 0.35 + 0.65 * Math.max(0, Math.sin(el / 220 - i * 0.9));
      g.fillStyle(hexToNum(SEPIA[5]), a).fillCircle(x0 + i * 10, y, 2.5);
    }
  }

  // ---------------------------------------------------------------------------------------------
  private onReady(p: unknown): void {
    const id = readId(p);
    const run = this.run;
    if (!run || id !== run.info.id) return;
    run.ready = true;
    debugExpose('transition', { id, mode: run.info.mode, phase: run.phase, ready: true });
  }

  private onKey = (e: KeyboardEvent): void => {
    if (e.repeat) return;
    this.skip();
  };

  private onPointer = (): void => {
    this.skip();
  };

  /** 아무 키·클릭: 덮기 전이면 바로 덮고, 덮였거나 걷히는 중이면 짧게 걷는다 */
  private skip(): void {
    const run = this.run;
    if (!run || !run.info.skippable || run.phase === 'prep') return;
    if (this.time.now - run.startedAt < TRANSITION.skipGuardMs) return;
    run.fast = true;
    const act = skipAction(run.phase === 'frame' ? 'intro' : run.phase, run.ready);
    if (act === 'toCovered') this.toCovered(run);
    else if (act === 'fastReveal') {
      if (run.phase === 'reveal') {
        // 지금 진행 비율을 지키며 남은 시간을 줄인다
        const t = clamp01((this.time.now - run.phaseAt) / Math.max(1, run.revealMs));
        run.revealMs = TRANSITION.skipRevealMs;
        run.phaseAt = this.time.now - t * run.revealMs;
      } else this.startReveal(run);
    }
  }

  /** 끝: 덮개를 걷고 `ui:transition-end`. force = 새 전환이 끼어들어 바로 끝냄 (덮임 알림이 아직이면 먼저) */
  private finish(force: boolean): void {
    const run = this.run;
    if (!run) return;
    if (force && !run.covered) uiBus.emit(UI_EVENTS.TRANSITION_COVERED, { id: run.info.id });
    this.clearRun();
    setTransitionBusy(false);
    debugExpose('transition', { id: run.info.id, mode: run.info.mode, phase: 'end' });
    uiBus.emit(UI_EVENTS.TRANSITION_END, { id: run.info.id });
  }

  private clearRun(): void {
    const run = this.run;
    this.run = null;
    if (!run) return;
    for (const o of run.objs) o.destroy();
    run.objs = [];
    this.veil?.setVisible(false).setAlpha(0);
    this.waitDots?.setVisible(false);
    this.cameras.main.resetFX();
  }
}

/**
 * 전환 씬이 떠 있게 한다 (HUD·타이틀 create 에서). 시스템이 `uiScenes` 로 등록했으면 launch, 등록돼 있지 않으면 직접 더한다 —
 * 전환을 시작할 씬이 없으면 시스템이 덮임(`ui:transition-covered`)을 영영 받지 못한다.
 */
export function ensureTransitionScene(scene: Phaser.Scene): void {
  const key = UI_SCENE_KEYS.TRANSITION;
  const mgr = scene.scene;
  if (!mgr.get(key)) {
    mgr.add(key, TransitionScene, true);
    return;
  }
  if (!mgr.isActive(key) && !mgr.isSleeping(key)) mgr.launch(key);
}
