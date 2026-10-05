/**
 * 53라운드 Q6 Gemini 외벽 테두리 그림 (계약 art §13, 배치 계산은 `border.ts`).
 * 그리기 순서: 바닥 → 서·동 → 북 → Y 정렬 층 → 남(전경) → 조명(곱하기) → 발광(가산). 충돌은 격자 그대로.
 *
 * 그림이 크다(북 띠 6214×818 등, 한 지역 GPU 약 75MB) → Preloader 는 border.json 만 읽고, 그림은 그 지역
 * 노드에 들어갈 때 지연 로드한다. 다른 지역의 테두리 텍스처는 그때 내린다. 로드가 실패하면 `onFail`(기존 벽 타일로).
 * 57라운드 Q17·Q38: 그림은 WebP, 4096px 초과 띠는 조각(`BorderImage`) 여러 장 — 배치(`planBorder`)가 조각마다 자른 사각형을 준다.
 */
import Phaser from 'phaser';
import { ASSETS, BORDER } from '../core/Constants';
import { lightRegistryOf, type LightSource } from '../systems/lighting/lightRegistry';
import { hexColor } from '../systems/lighting/lightMath';
import { ROUTE } from '../systems/route';
import { spawnWisp } from './SetPieceView';
import {
  WORLD_PER_LOGICAL,
  bandImageFiles,
  borderDefs,
  borderFileRel,
  borderFiles,
  borderTextureKey,
  doorPlacement,
  gapIsBandGate,
  northLookUp,
  planBorder,
  wispSpots,
  type BandSide,
  type BorderDef,
  type BorderDoor,
  type BorderGap,
  type BorderLight,
  type BorderPiece,
  type BorderPlan,
  type WorldRect,
} from './border';

const DEPTH_OF: Record<BandSide, number> = {
  west: BORDER.DEPTH_SIDE,
  east: BORDER.DEPTH_SIDE,
  north: BORDER.DEPTH_NORTH,
  south: BORDER.DEPTH_SOUTH,
};

type PieceRect = Pick<BorderPiece, 'x' | 'y' | 'cropX' | 'cropY' | 'cropW' | 'cropH' | 'scale'>;

interface SouthPiece {
  piece: PieceRect;
  /** 가림 때 함께 비칠 그림 (띠·발광·문 자리) */
  images: { setAlpha(a: number): unknown }[];
  /** 남 띠 그림 조각이면 그 그림의 하늘 윤곽(열 → 처음 불투명한 줄)으로, null 이면(문 조각·틈·윤곽 없음) 사각형으로 겹침 판정 */
  sky: Float32Array | null;
}

export class BorderView {
  readonly plan: BorderPlan;
  /** 그림이 다 올라왔는지 (디버그) */
  ready = false;
  failed = false;
  loadMs = 0;
  private readonly objects: Phaser.GameObjects.GameObject[] = [];
  /** 알베도(띠·문) 그림 — 주변광 보정 틴트 대상 */
  private readonly albedo: Phaser.GameObjects.Image[] = [];
  private tint = 0xffffff;
  private readonly tweens: Phaser.Tweens.Tween[] = [];
  wisps = 0;
  private readonly lights: LightSource[] = [];
  private readonly south: SouthPiece[] = [];
  private southAlpha = 1;
  private destroyed = false;
  doorPieces = 0;
  /** 띠의 성문이 곧 출구인 문 칸 수 */
  gateExits = 0;
  doorCuts = 0;

  constructor(
    private readonly scene: Phaser.Scene,
    readonly def: BorderDef,
    readonly floor: WorldRect,
    gaps: BorderGap[],
    private readonly onFail: () => void,
    /** 혼불 자리 시드 (노드 시드) */
    private readonly seed = 0,
  ) {
    this.plan = planBorder(def, floor, gaps);
    releaseBorderTextures(scene, def.region);
    const sides = [...new Set(gaps.map((g) => g.side))];
    const missing = borderFiles(def, sides).filter((f) => !scene.textures.exists(borderTextureKey(def.region, f)));
    if (missing.length === 0) {
      this.build();
      return;
    }
    const t0 = performance.now();
    // 61라운드 단계 2: 씬 로더 대신 모듈 단위로 받는다 — 노드를 빨리 넘기면 씬 로더가 초기화돼도 앞 요청이 살아 있어
    // 같은 키를 두 번 받아 'Texture key already in use: border_<지역>_*' 가 나던 문제 (같은 키는 한 번만, 끝나면 이어 쓴다)
    void Promise.all(
      missing.map((f) =>
        loadBorderTexture(
          scene.textures,
          borderTextureKey(def.region, f),
          `${ASSETS.URL}/${borderFileRel(def.region, f)}`,
        ),
      ),
    ).then(() => {
      this.loadMs = performance.now() - t0;
      if (!this.destroyed) this.build();
    });
  }

  private key(file: string): string {
    return borderTextureKey(this.def.region, file);
  }

  private build(): void {
    const scene = this.scene;
    if (bandImageFiles(this.def).some((f) => !scene.textures.exists(this.key(f)))) {
      this.failed = true;
      this.onFail();
      return;
    }
    const reg = lightRegistryOf(scene);
    const skylines = this.southSkylines();
    for (const p of this.plan.pieces) {
      const images = [this.albedoImage(p.image, p, DEPTH_OF[p.side])];
      if (p.emissive && scene.textures.exists(this.key(p.emissive)))
        images.push(this.image(p.emissive, p, BORDER.DEPTH_EMISSIVE).setBlendMode(Phaser.BlendModes.ADD));
      if (p.side === 'south') this.south.push({ piece: p, images, sky: skylines.get(p.image) ?? null });
    }
    for (const l of this.plan.lights) this.addLight(reg, l.light, l.x, l.y);
    for (const g of this.plan.gaps) this.drawGap(g);
    // 53라운드 Q22~25 황무지: 둑 위 혼불 (빛 포함)
    const V = ROUTE.view;
    if (V)
      wispSpots(this.def.region, this.floor, this.seed).forEach((w, i, all) => {
        const r = spawnWisp(scene, V, w.x, w.y, i, all.length, BORDER.DEPTH_WISP);
        this.objects.push(r.obj);
        this.tweens.push(r.tween);
        this.wisps++;
      });
    this.ready = true;
  }

  /** 남 띠 그림 조각마다 하늘 윤곽 (바닥과 겹치는 기준선 위 줄만 — 조각의 띠 안 세로 위치를 뺀다) */
  private southSkylines(): Map<string, Float32Array | null> {
    const S = this.def.bands.south;
    const ps = this.def.pixelScale;
    const out = new Map<string, Float32Array | null>();
    for (const im of S.images)
      if (!out.has(im.image))
        out.set(im.image, southSkyline(this.scene, this.key(im.image), (S.baselineY - im.y) / ps));
    return out;
  }

  private image(file: string, p: PieceRect, depth: number, flipX = false) {
    const img = this.scene.add
      .image(p.x, p.y, this.key(file))
      .setOrigin(0, 0)
      .setScale(p.scale)
      .setFlipX(flipX)
      .setCrop(Math.floor(p.cropX), Math.floor(p.cropY), Math.ceil(p.cropW), Math.ceil(p.cropH))
      .setDepth(depth);
    this.objects.push(img);
    return img;
  }

  private albedoImage(file: string, p: PieceRect, depth: number, flipX = false) {
    const img = this.image(file, p, depth, flipX).setTint(this.tint);
    this.albedo.push(img);
    return img;
  }

  /**
   * 53라운드 Q22~25 밝기: 전투 바닥을 밝히려고 주변광을 올려도 테두리 명도·분위기는 그대로 — 테두리 알베도에 (기준 주변광 ÷ 실제
   * 주변광) 틴트를 곱해 주변광만 받는 자리의 밝기를 기준(border.json ambient, 없으면 Q9 중립 숯빛)과 같게 둔다. 조명 꺼짐이면 1
   */
  matchAmbient(actual: string | null): void {
    if (!actual) this.tint = 0xffffff;
    else {
      const ref = hexColor(this.def.ambient ?? BORDER.REF_AMBIENT, 0xffffff);
      const cur = hexColor(actual, 0xffffff);
      const ch = (sh: number) => {
        const r = (ref >> sh) & 0xff;
        const c = (cur >> sh) & 0xff;
        return Math.round(255 * Math.min(1, c > 0 ? r / c : 1));
      };
      this.tint = (ch(16) << 16) | (ch(8) << 8) | ch(0);
    }
    for (const img of this.albedo) img.setTint(this.tint);
  }

  private addLight(reg: ReturnType<typeof lightRegistryOf>, l: BorderLight, x: number, y: number): void {
    this.lights.push(
      reg.add(
        {
          color: l.color,
          radius: l.radius * WORLD_PER_LOGICAL,
          intensity: l.intensity,
          flicker: typeof l.flicker === 'number' ? l.flicker : (l.flicker?.amp ?? 0),
        },
        { x, y },
      ),
    );
  }

  /** 문·출구 자리: 골목 입구 조각이 있으면 덧그리고, 없으면 어둠으로 잘라 둔다 */
  private drawGap(g: BorderGap): void {
    const k = WORLD_PER_LOGICAL;
    if (gapIsBandGate(this.def, this.floor, g)) {
      this.gateExits++;
      return;
    }
    const door = this.def.doors[g.side];
    if (door && this.scene.textures.exists(this.key(door.image))) {
      this.drawDoor(door, g);
      return;
    }
    const gfx = this.scene.add.graphics();
    const c = BORDER.DOOR_DARK_COLOR;
    const w = g.x1 - g.x0;
    if (g.side === 'north') {
      const h = BORDER.DOOR_DARK_HEIGHT_PX * k;
      const fade = h * BORDER.DOOR_DARK_FADE;
      gfx.fillGradientStyle(c, c, c, c, 0, 0, 1, 1);
      gfx.fillRect(g.x0, g.y - h, w, fade);
      gfx.fillStyle(c, 1);
      gfx.fillRect(g.x0, g.y - h + fade, w, h - fade);
      gfx.setDepth(BORDER.DEPTH_DOOR);
    } else {
      // 남쪽 틈: 바닥 끝 아래만 (처마 겹침 줄은 바닥이라 남긴다), 남 띠와 함께 비친다
      const S = this.def.bands.south;
      const h = (S.height - S.baselineY) * k;
      gfx.fillStyle(c, 1);
      gfx.fillRect(g.x0, g.y, w, h);
      gfx.setDepth(BORDER.DEPTH_SOUTH_DOOR);
      const piece: PieceRect = { x: g.x0, y: g.y, cropX: 0, cropY: 0, cropW: w, cropH: h, scale: 1 };
      this.south.push({ piece, images: [gfx], sky: null });
    }
    this.objects.push(gfx);
    this.doorCuts++;
  }

  private drawDoor(door: BorderDoor, g: BorderGap): void {
    const k = WORLD_PER_LOGICAL;
    const scale = this.def.pixelScale * k;
    const { x, y } = doorPlacement(door, g);
    const p = {
      x,
      y,
      cropX: 0,
      cropY: 0,
      cropW: door.width / this.def.pixelScale,
      cropH: door.height / this.def.pixelScale,
      scale,
    };
    const depth = g.side === 'north' ? BORDER.DEPTH_DOOR : BORDER.DEPTH_SOUTH_DOOR;
    const imgs = [this.albedoImage(door.image, p, depth, door.flipX)];
    if (door.emissive && this.scene.textures.exists(this.key(door.emissive)))
      imgs.push(this.image(door.emissive, p, BORDER.DEPTH_EMISSIVE, door.flipX).setBlendMode(Phaser.BlendModes.ADD));
    if (g.side === 'south') this.south.push({ piece: p, images: imgs, sky: null });
    const reg = lightRegistryOf(this.scene);
    for (const l of door.lights) this.addLight(reg, l, x + l.x * k, y + l.y * k);
    this.doorPieces++;
  }

  /**
   * 매 프레임: 남 띠(전경)의 불투명 픽셀이 주인공 그림 사각형(발 피벗 x,y · 폭 w · 높이 h, 월드)과 겹치면 반투명으로
   */
  update(target: { x: number; y: number; w: number; h: number }, deltaMs: number): void {
    if (!this.ready || this.south.length === 0) return;
    const fade = this.def.bands.south.fadeAlpha ?? BORDER.SOUTH_FADE_ALPHA;
    const want = this.southOverlaps(target) ? fade : 1;
    const t = 1 - Math.pow(1 - BORDER.SOUTH_FADE_LERP, deltaMs / (1000 / 60));
    this.southAlpha += (want - this.southAlpha) * t;
    if (Math.abs(want - this.southAlpha) < 0.01) this.southAlpha = want;
    for (const s of this.south) for (const img of s.images) img.setAlpha(this.southAlpha);
  }

  private southOverlaps(t: { x: number; y: number; w: number; h: number }): boolean {
    const left = t.x - t.w / 2;
    const right = t.x + t.w / 2;
    const S = this.def.bands.south;
    const top = this.floor.y1 - S.baselineY * WORLD_PER_LOGICAL;
    if (t.y <= top) return false;
    for (const { piece: p, sky } of this.south) {
      const x0 = p.x + p.cropX * p.scale;
      if (x0 > right || x0 + p.cropW * p.scale < left) continue;
      if (!sky) {
        if (p.y < t.y) return true;
        continue;
      }
      const from = Math.max(Math.floor(p.cropX), Math.floor((left - p.x) / p.scale));
      const to = Math.min(Math.ceil(p.cropX + p.cropW) - 1, Math.ceil((right - p.x) / p.scale));
      for (let c = from; c <= to; c += 2) {
        const row = sky[Math.min(sky.length - 1, c)];
        if (row !== Infinity && p.y + row * p.scale < t.y) return true;
      }
    }
    return false;
  }

  /** 53라운드 Q8: 카메라 북쪽 치우침 목표 (월드) */
  lookUpAt(footY: number): number {
    return northLookUp(this.def, this.floor, footY);
  }

  /** 디버그 */
  summary(): Record<string, unknown> {
    return {
      region: this.def.region,
      ready: this.ready,
      failed: this.failed,
      loadMs: Math.round(this.loadMs),
      pieces: this.plan.pieces.map(
        (p) =>
          `${p.side}:${p.image}@${Math.round(p.x)},${Math.round(p.y)} +${Math.round(p.cropX)},${Math.round(p.cropY)} ${Math.round(p.cropW)}×${Math.round(p.cropH)}`,
      ),
      lights: this.lights.length,
      gaps: this.plan.gaps.map((g) => `${g.side} ${g.x0}-${g.x1}`),
      doorPieces: this.doorPieces,
      doorCuts: this.doorCuts,
      gateExits: this.gateExits,
      southAlpha: +this.southAlpha.toFixed(2),
      tint: '#' + this.tint.toString(16).padStart(6, '0'),
      wisps: this.wisps,
      camera: this.plan.camera,
    };
  }

  destroy(): void {
    this.destroyed = true;
    for (const t of this.tweens) t.remove();
    this.tweens.length = 0;
    for (const o of this.objects) o.destroy();
    this.albedo.length = 0;
    this.objects.length = 0;
    this.south.length = 0;
    const reg = lightRegistryOf(this.scene);
    for (const l of this.lights) reg.remove(l);
    this.lights.length = 0;
  }
}

/** 받는 중인 외벽 그림 (텍스처 키 → 끝나면 텍스처가 있는지) */
const pendingBorder = new Map<string, Promise<boolean>>();
/** 지금 필요한 지역 — 받는 사이 다른 지역으로 넘어갔으면 다 받은 그림을 올리지 않는다 (GPU 메모리) */
let wantedBorderRegion: string | null = null;

/**
 * 외벽 그림 한 장을 받아 텍스처로 올린다 (이미 있으면 바로 true · 받는 중이면 같은 약속). 실패하면 false — BorderView 가 벽 타일로.
 * 텍스처 키는 `border_<지역>_<파일>` 이라 지역은 키에서 읽는다
 */
function loadBorderTexture(textures: Phaser.Textures.TextureManager, key: string, url: string): Promise<boolean> {
  if (textures.exists(key)) return Promise.resolve(true);
  const had = pendingBorder.get(key);
  if (had) return had;
  const region = [...borderDefs.keys()].find((r) => key.startsWith(borderTextureKey(r, ''))) ?? null;
  const p = new Promise<boolean>((resolve) => {
    if (typeof Image === 'undefined') return resolve(false);
    const img = new Image();
    img.decoding = 'async';
    img.onload = () => {
      if (!textures.exists(key) && (region === null || region === wantedBorderRegion)) textures.addImage(key, img);
      resolve(textures.exists(key));
    };
    img.onerror = () => resolve(false);
    img.src = url;
  }).finally(() => pendingBorder.delete(key));
  pendingBorder.set(key, p);
  return p;
}

/** 지금 지역(keep)이 아닌 테두리 텍스처를 내린다 (GPU 메모리 — 한 지역 약 75MB) */
export function releaseBorderTextures(scene: Phaser.Scene, keep: string | null): void {
  wantedBorderRegion = keep;
  for (const def of borderDefs.values()) {
    if (def.region === keep) continue;
    for (const f of borderFiles(def)) {
      const key = borderTextureKey(def.region, f);
      if (scene.textures.exists(key)) scene.textures.remove(key);
    }
  }
}

/** 남 띠 위쪽(바닥과 겹치는 기준선 위) 열마다 처음 불투명한 줄 — 한 번만 (캔버스에 윗부분만 그려 읽는다) */
function southSkyline(scene: Phaser.Scene, key: string, rows: number): Float32Array | null {
  const src = scene.textures.get(key).getSourceImage() as HTMLImageElement | HTMLCanvasElement;
  const w = src.width;
  const h = Math.max(1, Math.min(src.height, Math.ceil(rows)));
  if (!(w > 0)) return null;
  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  if (!ctx) return null;
  ctx.drawImage(src, 0, 0, w, h, 0, 0, w, h);
  const data = ctx.getImageData(0, 0, w, h).data;
  const out = new Float32Array(w).fill(Infinity);
  for (let x = 0; x < w; x++)
    for (let y = 0; y < h; y++)
      if (data[(y * w + x) * 4 + 3] >= BORDER.SOUTH_OPAQUE_ALPHA) {
        out[x] = y;
        break;
      }
  return out;
}
