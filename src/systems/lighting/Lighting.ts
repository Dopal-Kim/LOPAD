/**
 * 50라운드 동적 조명 + 어둠 (결정 round-50 Q3, 계약 art §9) — 라이트맵 RenderTexture 방식.
 *
 * 매 프레임: 화면 크기 × lightmapScale 의 라이트맵을 주변광(어둠) 색으로 채우고, 보이는 광원(주인공 빛 + 등록 광원 + 예고 경고광,
 * 상한 maxLights)을 방사형 그라데이션으로 가산(ADD) 스탬프 → 라이트맵을 월드 위(DEPTH.LIGHTMAP)에 곱하기(MULTIPLY)로 덮는다.
 * 비네팅(가장자리 어둠)은 라이트맵에 함께 구워 화면 전체 합성은 1장(곱하기)뿐이다. 그 위에 빛 번짐(광원마다 가산 그라데이션,
 * 월드 좌표)을 얹는다. 투사체·드랍·공격 판정·피격 이펙트·데미지 숫자·
 * 화면 섬광은 라이트맵보다 위 깊이라 어둠에 묻히지 않는다.
 *
 * Light2D(노멀맵 없음) 대신 이 방식을 고른 이유: 모든 개체(타일·Graphics·텍스트 포함)에 파이프라인을 따로 걸 필요가 없고,
 * 광원 수가 셰이더 상수(maxLights)에 묶이지 않으며 광원 1개 = 쿼드 1장이라 60fps 예산이 예측 가능하다. 빛 번짐·비네팅도 같은 틀.
 */
import Phaser from 'phaser';
import { DEPTH } from '../../core/Constants';
import { RES } from '../display';
import { LIGHTING } from '../../data';
import type { LightingAmbient } from '../../data/types';
import { flickerFactor, hexColor, lightFalloff, pickLights, type LightPick } from './lightMath';
import { dropLightRegistry, lightRegistryOf, type LightRegistry, type LightSource } from './lightRegistry';

const TEX_LIGHT = 'light_radial';
const TEX_GLOW = 'light_glow';
const TEX_VIGNETTE = 'light_vignette';
/** 방사형 텍스처 크기 (반경 = 크기/2) */
const LIGHT_TEX = 256;
const VIGNETTE_W = 480;
const VIGNETTE_H = 270;

/**
 * 라이트맵 해상도 = 실제 캔버스 px × 이 값. data `lightmapScale` 은 **논리 화면**(960×540) 기준이라 52라운드 1920×1080 캔버스에서도
 * 라이트맵 크기(480×270)·비용이 그대로다 (선형 필터로 부드럽게 늘어나는 어둠이라 해상도를 올릴 이유가 없다)
 */
function lightmapK(): number {
  return LIGHTING.lightmapScale / RES;
}

export interface LightingOptions {
  /** 어둠 색 (null = 조명 끔) */
  ambient: LightingAmbient | null;
  /** 주인공 (빛이 따라간다) */
  player: { x: number; y: number; visible: boolean };
  /** 예고 마커 위치 (경고광) */
  telegraphs?: () => { x: number; y: number; radius: number }[];
}

interface Drawn extends LightPick {
  color: number;
  intensity: number;
}

export class Lighting {
  readonly enabled: boolean;
  private readonly registry: LightRegistry;
  private rt: Phaser.GameObjects.RenderTexture | null = null;
  private readonly glows: Phaser.GameObjects.Image[] = [];
  private readonly ambient: number;
  private readonly playerSeed = 17;
  /** 디버그: 지난 프레임에 그린 광원 수 · 후보 수 */
  drawn = 0;
  candidates = 0;
  /** 디버그: 조명 갱신 CPU 시간 (ms, 지수 평균) */
  cpuMs = 0;

  constructor(
    private readonly scene: Phaser.Scene,
    private readonly opts: LightingOptions,
  ) {
    this.registry = lightRegistryOf(scene);
    this.enabled = opts.ambient !== null;
    this.ambient = hexColor(opts.ambient?.ambient, 0xffffff);
    if (!this.enabled) return;
    ensureTextures(scene);
    const cam = scene.cameras.main;
    const k = lightmapK();
    this.rt = scene.add
      .renderTexture(cam.width / 2, cam.height / 2, Math.ceil(cam.width * k), Math.ceil(cam.height * k))
      .setOrigin(0.5)
      .setScrollFactor(0)
      .setBlendMode(Phaser.BlendModes.MULTIPLY)
      .setDepth(DEPTH.LIGHTMAP);
    this.rt.texture.setFilter(Phaser.Textures.FilterMode.LINEAR);
  }

  /** 매 프레임 (카메라 스크롤·배율이 정해진 뒤) */
  update(time: number): void {
    if (!this.enabled || !this.rt) return;
    const t0 = performance.now();
    const cam = this.scene.cameras.main;
    const z = cam.zoom || 1;
    const k = lightmapK();
    // 화면 고정 개체는 카메라 배율만큼 화면 가운데 기준으로 커진다 → 역배율로 화면을 정확히 덮는다
    this.rt.setScale(1 / (k * z));
    const lights = this.collect(time);
    const halfW = cam.width / (2 * z);
    const halfH = cam.height / (2 * z);
    const cx = cam.scrollX + cam.width / 2;
    const cy = cam.scrollY + cam.height / 2;
    const picked = pickLights(lights, cx, cy, halfW, halfH, LIGHTING.maxLights);
    this.candidates = lights.length;
    this.drawn = picked.length;
    const rt = this.rt;
    rt.fill(this.ambient, 1);
    rt.beginDraw();
    for (const i of picked) {
      const l = lights[i];
      // 월드 → 화면 → 라이트맵
      const sx = ((l.x - cam.scrollX - cam.width / 2) * z + cam.width / 2) * k;
      const sy = ((l.y - cam.scrollY - cam.height / 2) * z + cam.height / 2) * k;
      const r = l.radius * z * k;
      rt.stamp(TEX_LIGHT, undefined, sx, sy, {
        scale: (r * 2) / LIGHT_TEX,
        tint: l.color,
        alpha: Math.min(1, l.intensity),
        blendMode: Phaser.BlendModes.ADD,
        skipBatch: true,
      });
    }
    // 비네팅: 라이트맵 가장자리를 어둡게 (검정 그라데이션을 덮는다 = 곱하기 (1 - a))
    const V = LIGHTING.vignette;
    if (V.alpha > 0)
      rt.stamp(TEX_VIGNETTE, undefined, rt.width / 2, rt.height / 2, {
        scaleX: rt.width / VIGNETTE_W,
        scaleY: rt.height / VIGNETTE_H,
        alpha: V.alpha,
        skipBatch: true,
      });
    rt.endDraw();
    this.drawGlows(lights, picked);
    this.cpuMs = this.cpuMs * 0.9 + (performance.now() - t0) * 0.1;
  }

  /** 빛 번짐: 광원마다 가산 그라데이션 (월드 좌표, 라이트맵 위) */
  private drawGlows(lights: Drawn[], picked: number[]): void {
    const G = LIGHTING.glow;
    let n = 0;
    if (G.alpha > 0)
      for (const i of picked) {
        const l = lights[i];
        let img = this.glows[n];
        if (!img) {
          img = this.scene.add
            .image(0, 0, TEX_GLOW)
            .setBlendMode(Phaser.BlendModes.ADD)
            .setDepth(DEPTH.LIGHTMAP + DEPTH.LIGHT_LAYER_STEP);
          this.glows.push(img);
        }
        img
          .setPosition(l.x, l.y)
          .setScale((l.radius * G.radiusMult * 2) / LIGHT_TEX)
          .setTint(l.color)
          .setAlpha(G.alpha * Math.min(G.maxIntensity, l.intensity))
          .setVisible(true);
        n++;
      }
    for (let j = n; j < this.glows.length; j++) this.glows[j].setVisible(false);
  }

  /** 이번 프레임 후보: 주인공 빛(고정) + 등록 광원(깜빡임·순간광 감쇠) + 예고 경고광 */
  private collect(time: number): Drawn[] {
    const out: Drawn[] = [];
    const hz = LIGHTING.flickerHz;
    const P = LIGHTING.player;
    const p = this.opts.player;
    if (p.visible)
      out.push({
        x: p.x,
        y: p.y - (P.offsetY ?? 0),
        radius: P.radius,
        color: hexColor(P.color, 0xffffff),
        intensity: (P.intensity ?? 1) * flickerFactor(time, this.playerSeed, P.flicker ?? 0, hz),
        pinned: true,
      });
    for (const s of this.registry.live(time)) out.push(this.drawnOf(s, time));
    const T = LIGHTING.telegraph;
    const tc = hexColor(T.color, 0xff5a3c);
    for (const t of this.opts.telegraphs?.() ?? [])
      out.push({
        x: t.x,
        y: t.y,
        radius: Math.max(T.radius, t.radius),
        color: tc,
        intensity: (T.intensity ?? 1) * flickerFactor(time, t.x * 0.37 + t.y, T.flicker ?? 0, hz),
      });
    return out;
  }

  private drawnOf(s: LightSource, time: number): Drawn {
    let intensity = s.intensity * flickerFactor(time, s.id * 7.13, s.flicker, LIGHTING.flickerHz);
    if (s.fade && Number.isFinite(s.until) && s.until > s.bornAt)
      intensity *= Math.max(0, (s.until - time) / (s.until - s.bornAt));
    return { x: s.x, y: s.y, radius: s.radius, color: s.color, intensity };
  }

  /** 디버그 요약 */
  summary(): Record<string, unknown> {
    return {
      enabled: this.enabled,
      ambient: '#' + this.ambient.toString(16).padStart(6, '0'),
      registered: this.registry.size,
      candidates: this.candidates,
      drawn: this.drawn,
      max: LIGHTING.maxLights,
      lightmap: this.rt ? { w: this.rt.width, h: this.rt.height } : null,
      cpuMs: +this.cpuMs.toFixed(3),
    };
  }

  destroy(): void {
    this.rt?.destroy();
    for (const g of this.glows) g.destroy();
    this.glows.length = 0;
    dropLightRegistry(this.scene);
  }
}

/** 방사형 빛(중심 밝고 falloff 밖으로 0)·번짐·비네팅 텍스처 (부드러운 선형 필터) */
function ensureTextures(scene: Phaser.Scene): void {
  const radial = (key: string, stops: [number, number][]) => {
    if (scene.textures.exists(key)) return;
    const tex = scene.textures.createCanvas(key, LIGHT_TEX, LIGHT_TEX)!;
    const ctx = tex.context;
    const h = LIGHT_TEX / 2;
    const g = ctx.createRadialGradient(h, h, 0, h, h, h);
    for (const [at, a] of stops) g.addColorStop(at, `rgba(255,255,255,${a})`);
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, LIGHT_TEX, LIGHT_TEX);
    tex.refresh();
    tex.setFilter(Phaser.Textures.FilterMode.LINEAR);
  };
  // 52라운드 Q9: 감쇠 = 아트 목업과 같은 (1 - d²)² (d = 중심 거리 / 반경)
  if (!scene.textures.exists(TEX_LIGHT)) {
    const tex = scene.textures.createCanvas(TEX_LIGHT, LIGHT_TEX, LIGHT_TEX)!;
    const ctx = tex.context;
    const img = ctx.createImageData(LIGHT_TEX, LIGHT_TEX);
    const h = LIGHT_TEX / 2;
    for (let y = 0; y < LIGHT_TEX; y++)
      for (let x = 0; x < LIGHT_TEX; x++) {
        const d2 = ((x + 0.5 - h) ** 2 + (y + 0.5 - h) ** 2) / (h * h);
        const a = d2 >= 1 ? 0 : lightFalloff(Math.sqrt(d2));
        const i = (y * LIGHT_TEX + x) * 4;
        img.data[i] = img.data[i + 1] = img.data[i + 2] = 255;
        img.data[i + 3] = Math.round(a * 255);
      }
    ctx.putImageData(img, 0, 0);
    tex.refresh();
    tex.setFilter(Phaser.Textures.FilterMode.LINEAR);
  }
  radial(TEX_GLOW, [
    [0, 0.9],
    [0.35, 0.35],
    [1, 0],
  ]);
  if (!scene.textures.exists(TEX_VIGNETTE)) {
    const tex = scene.textures.createCanvas(TEX_VIGNETTE, VIGNETTE_W, VIGNETTE_H)!;
    const ctx = tex.context;
    const cx = VIGNETTE_W / 2;
    const cy = VIGNETTE_H / 2;
    const r = Math.hypot(cx, cy);
    const g = ctx.createRadialGradient(cx, cy, r * LIGHTING.vignette.inner, cx, cy, r);
    g.addColorStop(0, 'rgba(0,0,0,0)');
    g.addColorStop(1, 'rgba(0,0,0,1)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, VIGNETTE_W, VIGNETTE_H);
    tex.refresh();
    tex.setFilter(Phaser.Textures.FilterMode.LINEAR);
  }
}
