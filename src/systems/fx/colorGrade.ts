/**
 * P21 월드 화면 톤 (계약 dark-brutal §7): `data/grade.json`(아트 A 값 — 의미는 `gradeMath.ts`) 을 월드 카메라에만 건다 (HUD 는 별도 씬).
 * - WebGL: 카메라 postFX ColorMatrix 한 장(채도 → 대비 → 명도 → shadowTint, `ColorMatrix.set`). ScreenFx 의 채도 감소(보스 국면·히트스톱)는
 *   따로 ColorMatrix 를 붙이지 않고 이 행렬의 채도에 곱한다 (`ScreenFx.desatSink`). Canvas 면 행렬 없음.
 * - 비네트: Phaser 기본 Vignette(반지름 밖을 검게 칠함)는 모양이 달라 쓰지 않고, ×(1 − strength·smoothstep(radius, 1, d)) 를 구운
 *   화면 그림 한 장 (WebGL·Canvas 같음 — lighting.json vignette 는 0, 이중 비네트 금지).
 * - 그레인: 작은 노이즈 텍스처 타일(가산, grain.amount) — grain.fps 마다 무늬 자리를 바꾼다.
 * - 보정 없는 층 (`ungradedOf(scene)`): 예고 색(free-combat §2)·광원 빛 번짐(위험물 빛)·주인공 불씨는 이 층(별도 카메라 — 월드 카메라와
 *   같은 스크롤·배율, postFX 없음)에 옮겨 원래 색으로 보인다. 그 카메라는 이 층만 그린다.
 * - 저HP(≤ 25%): 채도를 lowHp.saturation 으로 0.4초에 옮기고, vignetteColor 가 있으면 그 색 비네트로 pulseHz 맥동(비면 끔 — UI 피 비네트가 맡음).
 * `?grade=0` 이면 아무것도 걸지 않는다 (비교용).
 */
import Phaser from 'phaser';
import { BRUTAL, DEPTH } from '../../core/Constants';
import { GRADE } from '../../data';
import type { GradeData } from '../../data/types';
import { hexToInt } from '../palette';
import { gradeMatrix, pulseAt, vignetteAlpha } from './gradeMath';

const TEX_GRAIN = 'grade_grain';
const TEX_VIGNETTE = 'grade_vignette';
const TEX_LOWHP = 'grade_vignette_lowhp';
const VIG_W = 480;
const VIG_H = 270;
/** 저HP 채도 전환 (아트 A _semantics) */
const LOW_HP_SAT_MS = 400;

type PostFx = Phaser.GameObjects.Components.FX;
type Controller = Phaser.FX.Controller;

const registry = new WeakMap<Phaser.Scene, ColorGrade>();

/** 보정을 받지 않는 층 (없으면 null — 보정이 꺼진 씬·Canvas) */
export function ungradedOf(scene: Phaser.Scene): ColorGrade | null {
  const g = registry.get(scene);
  return g && g.layered ? g : null;
}

/** 지역 덮어쓰기를 합친 값 (얕은 병합) */
export function gradeFor(region: string | null | undefined, d: GradeData = GRADE): GradeData {
  const o = region ? d.byRegion?.[region] : undefined;
  return o ? { ...d, ...o, vignette: { ...d.vignette, ...o.vignette }, grain: { ...d.grain, ...o.grain } } : d;
}

/** 비네트 그림: 색 color, 알파 = strength·smoothstep(radius, 1, d) (원형, d = 가운데 → 모서리 1). 지역마다 값이 달라 매번 다시 굽는다 */
function bakeVignette(scene: Phaser.Scene, key: string, color: number, strength: number, radius: number): void {
  if (scene.textures.exists(key)) scene.textures.remove(key);
  const tex = scene.textures.createCanvas(key, VIG_W, VIG_H)!;
  const ctx = tex.context;
  const img = ctx.createImageData(VIG_W, VIG_H);
  const cx = VIG_W / 2;
  const cy = VIG_H / 2;
  const corner = Math.hypot(cx, cy);
  for (let y = 0; y < VIG_H; y++)
    for (let x = 0; x < VIG_W; x++) {
      const i = (y * VIG_W + x) * 4;
      img.data[i] = (color >> 16) & 0xff;
      img.data[i + 1] = (color >> 8) & 0xff;
      img.data[i + 2] = color & 0xff;
      img.data[i + 3] = Math.round(
        255 * vignetteAlpha(strength, radius, Math.hypot(x + 0.5 - cx, y + 0.5 - cy) / corner),
      );
    }
  ctx.putImageData(img, 0, 0);
  tex.refresh();
  tex.setFilter(Phaser.Textures.FilterMode.LINEAR);
}

function ensureGrain(scene: Phaser.Scene): void {
  if (scene.textures.exists(TEX_GRAIN)) return;
  const n = BRUTAL.GRAIN_TEX;
  const tex = scene.textures.createCanvas(TEX_GRAIN, n, n)!;
  const ctx = tex.context;
  const img = ctx.createImageData(n, n);
  for (let i = 0; i < n * n; i++) {
    const v = Math.floor(Math.random() * 256);
    img.data[i * 4] = v;
    img.data[i * 4 + 1] = v;
    img.data[i * 4 + 2] = v;
    img.data[i * 4 + 3] = 255;
  }
  ctx.putImageData(img, 0, 0);
  tex.refresh();
}

export class ColorGrade {
  readonly webgl: boolean;
  private readonly d: GradeData;
  private matrix: Phaser.FX.ColorMatrix | null = null;
  private vignette: Phaser.GameObjects.Image | null = null;
  private lowVignette: Phaser.GameObjects.Image | null = null;
  private grain: Phaser.GameObjects.TileSprite | null = null;
  private grainAt = 0;
  private layer: Phaser.GameObjects.Layer | null = null;
  private ugCam: Phaser.Cameras.Scene2D.Camera | null = null;
  private capturing: Phaser.GameObjects.GameObject[] | null = null;
  private extraDesat = 0;
  private lowHp = false;
  /** 저HP 채도 전환 진행 0 → 1 (0.4초) */
  private lowK = 0;
  private lastTime = 0;
  private appliedSat = Number.NaN;
  /** 디버그: 층에 옮긴 개체 수 */
  lifted = 0;

  constructor(
    private readonly scene: Phaser.Scene,
    region: string | null | undefined,
  ) {
    this.webgl = scene.sys.game.renderer.type === Phaser.WEBGL;
    this.d = gradeFor(region);
    registry.set(scene, this);
    const cam = scene.cameras.main;
    const pfx = (cam as unknown as { postFX?: PostFx }).postFX;
    if (this.webgl && pfx) {
      this.matrix = pfx.addColorMatrix();
      this.makeLayer();
    }
    const V = this.d.vignette;
    if (V.strength > 0) {
      bakeVignette(scene, TEX_VIGNETTE, 0x000000, V.strength, V.radius);
      this.vignette = this.screenImage(TEX_VIGNETTE, DEPTH.SCREEN_FX - 3);
    }
    if (this.d.grain.amount > 0) {
      ensureGrain(scene);
      this.grain = scene.add
        .tileSprite(0, 0, cam.width, cam.height, TEX_GRAIN)
        .setOrigin(0, 0)
        .setScrollFactor(0)
        .setDepth(DEPTH.SCREEN_FX - 2)
        .setBlendMode(Phaser.BlendModes.ADD)
        .setAlpha(this.d.grain.amount);
    }
    this.applyMatrix();
    scene.events.once(Phaser.Scenes.Events.SHUTDOWN, () => this.destroy());
  }

  /** 보정을 받지 않는 층이 있는가 (WebGL) */
  get layered(): boolean {
    return this.layer !== null;
  }

  /** fn 안에서 씬에 더해진 개체를 보정 없는 층으로 옮긴다 (예고 마커처럼 여러 개체를 만드는 함수) */
  capture<T>(fn: () => T): T {
    if (!this.layer || this.capturing) return fn();
    const got: Phaser.GameObjects.GameObject[] = [];
    this.capturing = got;
    try {
      return fn();
    } finally {
      this.capturing = null;
      for (const o of got) this.add(o);
    }
  }

  /** 개체 하나를 보정 없는 층으로 */
  add<T extends Phaser.GameObjects.GameObject>(obj: T): T {
    if (this.layer && obj.active !== false && obj.displayList !== this.layer) {
      this.layer.add(obj);
      this.lifted += 1;
    }
    return obj;
  }

  /** ScreenFx 채도 감소(0~1) — 따로 ColorMatrix 를 붙이지 않고 여기 곱한다 */
  setExtraDesat(v: number): void {
    this.extraDesat = v;
    this.applyMatrix();
  }

  setLowHp(on: boolean): void {
    if (this.lowHp === on) return;
    this.lowHp = on;
    const V = this.d.vignette;
    // 빈 vignetteColor = 붉은 맥박은 UI(HudP21) 몫 — 월드는 채도만 뺀다 (P21 통합)
    if (on && !this.lowVignette && V.strength > 0 && this.d.lowHp.vignetteColor) {
      bakeVignette(this.scene, TEX_LOWHP, hexToInt(this.d.lowHp.vignetteColor), V.strength, V.radius);
      this.lowVignette = this.screenImage(TEX_LOWHP, DEPTH.SCREEN_FX - 3).setVisible(false);
    }
  }

  /** 매 프레임 (씬 시계): 그레인 무늬 · 저HP 채도 전환·맥박 · 화면 그림 배율(줌) */
  update(time: number): void {
    const dt = Math.max(0, Math.min(100, time - this.lastTime));
    this.lastTime = time;
    const target = this.lowHp ? 1 : 0;
    if (this.lowK !== target) {
      const step = dt / LOW_HP_SAT_MS;
      this.lowK = this.lowK < target ? Math.min(1, this.lowK + step) : Math.max(0, this.lowK - step);
      this.applyMatrix();
    }
    const z = this.scene.cameras.main.zoom || 1;
    if (this.grain) {
      this.grain.setTileScale(1 / z);
      const every = 1000 / Math.max(1, this.d.grain.fps);
      if (time - this.grainAt >= every) {
        this.grainAt = time;
        this.grain.setTilePosition(Math.random() * BRUTAL.GRAIN_TEX, Math.random() * BRUTAL.GRAIN_TEX);
      }
    }
    if (this.vignette) this.fitScreen(this.vignette, z).setVisible(!this.lowHp || !this.lowVignette);
    if (this.lowVignette) {
      this.fitScreen(this.lowVignette, z).setVisible(this.lowHp);
      if (this.lowHp) this.lowVignette.setAlpha(pulseAt(time, this.d.lowHp.pulseHz));
    }
  }

  /** 디버그 */
  summary(): {
    webgl: boolean;
    saturation: number;
    lowHp: boolean;
    extraDesat: number;
    layered: boolean;
    lifted: number;
  } {
    return {
      webgl: this.webgl,
      saturation: +this.appliedSat.toFixed(3),
      lowHp: this.lowHp,
      extraDesat: this.extraDesat,
      layered: this.layered,
      lifted: this.lifted,
    };
  }

  destroy(): void {
    if (registry.get(this.scene) === this) registry.delete(this.scene);
    const cam = this.scene.cameras?.main as unknown as { postFX?: PostFx } | undefined;
    if (this.matrix) cam?.postFX?.remove(this.matrix as unknown as Controller);
    this.matrix = null;
    if (this.ugCam) this.scene.cameras?.remove(this.ugCam);
    this.ugCam = null;
    this.layer = null;
    this.grain = null;
    this.vignette = null;
    this.lowVignette = null;
  }

  private applyMatrix(): void {
    const base = this.d.saturation + (this.d.lowHp.saturation - this.d.saturation) * this.lowK;
    // 채도 배율(1 + saturation)에 ScreenFx 채도 감소를 곱한다
    const s = (1 + base) * (1 - Math.min(1, Math.max(0, this.extraDesat))) - 1;
    if (s === this.appliedSat) return;
    this.appliedSat = s;
    this.matrix?.set(
      gradeMatrix({
        saturation: s,
        contrast: this.d.contrast,
        brightness: this.d.brightness,
        shadowTint: hexToInt(this.d.shadowTint),
      }),
    );
  }

  /**
   * 보정 없는 층: 이 층만 그리는 둘째 카메라 (월드 카메라 다음에 그려 위에 얹힌다). 월드 카메라는 이 층을 무시하고,
   * 둘째 카메라는 층 밖의 모든 개체를 무시한다 (씬에 더해질 때마다 표시)
   */
  private makeLayer(): void {
    const scene = this.scene;
    const main = scene.cameras.main;
    const layer = scene.add.layer();
    const cam = scene.cameras.add(main.x, main.y, main.width, main.height, false, 'ungraded');
    main.ignore(layer);
    this.layer = layer;
    this.ugCam = cam;
    const mark = (o: Phaser.GameObjects.GameObject) => {
      if ((o as unknown) === layer) return;
      if (o.displayList === layer) o.cameraFilter &= ~cam.id;
      else o.cameraFilter |= cam.id;
    };
    for (const o of scene.children.list) mark(o);
    const onAdded = (o: Phaser.GameObjects.GameObject) => {
      mark(o);
      if (this.capturing && o.displayList !== layer) this.capturing.push(o);
    };
    scene.events.on(Phaser.Scenes.Events.ADDED_TO_SCENE, onAdded);
    scene.events.once(Phaser.Scenes.Events.SHUTDOWN, () =>
      scene.events.off(Phaser.Scenes.Events.ADDED_TO_SCENE, onAdded),
    );
    // 월드 카메라와 같은 스크롤·배율·기울기 (월드 카메라의 preRender 가 먼저 돈 뒤 — 카메라 순서)
    const pre = cam.preRender.bind(cam);
    cam.preRender = () => {
      cam
        .setScroll(main.scrollX, main.scrollY)
        .setZoom(main.zoom)
        .setRotation((main as unknown as { rotation: number }).rotation);
      cam.setOrigin(main.originX, main.originY);
      pre();
    };
  }

  private screenImage(key: string, depth: number): Phaser.GameObjects.Image {
    const cam = this.scene.cameras.main;
    const img = this.scene.add
      .image(cam.width / 2, cam.height / 2, key)
      .setOrigin(0.5)
      .setScrollFactor(0)
      .setDepth(depth);
    return this.fitScreen(img, cam.zoom || 1);
  }

  private fitScreen(img: Phaser.GameObjects.Image, z: number): Phaser.GameObjects.Image {
    const cam = this.scene.cameras.main;
    return img.setScale(cam.width / (VIG_W * z), cam.height / (VIG_H * z));
  }
}
