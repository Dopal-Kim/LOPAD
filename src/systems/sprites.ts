/**
 * 스프라이트 시트 라이브러리 (계약 contracts/art-assets.md §1·§2).
 * Preloader 가 시트를 등록하고, Game 이 층 진입 시 `activate(scene, floor)` 로 팔레트 변형을 만든다.
 * 엔티티는 `animKey(name, action, dir)` 만 묻는다 — 시트가 없으면 null (플레이스홀더 유지).
 * 53라운드 Q62: 이펙트·`paletteSwap: "none"` 시트는 층 변형을 만들지 않고 늘 원본 키 (`paletteSwapExempt`).
 * 51·53라운드 계약 §10: 2단 갈래·가열 색 교체는 `recolored` 가 같은 캔버스 재채색으로 변형 텍스처·애니를 만든다.
 */
import Phaser from 'phaser';
import { PALETTE } from '../data';
import { BASE_FLOOR, buildSwapTable, rampFor, recolorPixels, variantSuffix } from './palette';
import { swapTag, type ColorSwap } from './fxVariants';
import {
  FACINGS,
  animKey,
  frameAt,
  frameDurations,
  frameIndices,
  paletteSwapExempt,
  phaseAnimKey,
  sheetId,
  sheetTextureKey,
  type Facing,
  type SheetDef,
} from './spriteDefs';

class SpriteLibrary {
  private readonly sheets = new Map<string, SheetDef>();
  /** 자기 시트가 없는 이름 → 대신 쓰는 시트 이름 (2~7층 보스 → stage1) */
  private readonly aliases = new Map<string, string>();
  /** 현재 층 변형 접미 ('' = 1층 원본) */
  private suffix = '';
  private readonly builtVariants = new Set<string>();

  /** Preloader: 텍스처가 실제로 로드된 시트만 등록한다 */
  register(def: SheetDef): void {
    this.sheets.set(sheetId(def.name, def.action), def);
  }

  /** `name` 의 시트가 없을 때 `target` 시트를 대신 쓴다 (키·애니 모두 target 이름) */
  alias(name: string, target: string): void {
    if (name !== target) this.aliases.set(name, target);
  }

  /** 실제로 쓰이는 시트 이름 (자기 시트가 있으면 자기 이름, 아니면 별칭) */
  resolve(name: string): string {
    if (this.sheets.has(sheetId(name, 'idle'))) return name;
    return this.aliases.get(name) ?? name;
  }

  has(name: string, action = 'idle'): boolean {
    return this.sheets.has(sheetId(this.resolve(name), action));
  }

  sheet(name: string, action: string): SheetDef | undefined {
    return this.sheets.get(sheetId(this.resolve(name), action));
  }

  get variant(): string {
    return this.suffix;
  }

  /** 이 시트에 쓰는 층 변형 접미 (램프 교체 제외 시트는 늘 '') */
  private suffixOf(def: SheetDef): string {
    return paletteSwapExempt(def) ? '' : this.suffix;
  }

  /** 현재 층 변형이 적용된 텍스처 키 */
  textureKey(name: string, action: string): string | null {
    const n = this.resolve(name);
    const def = this.sheets.get(sheetId(n, action));
    return def ? sheetTextureKey(n, action, this.suffixOf(def)) : null;
  }

  /** 현재 층 변형이 적용된 애니 키. 시트가 없으면 null */
  animKey(name: string, action: string, dir: Facing): string | null {
    const n = this.resolve(name);
    const def = this.sheets.get(sheetId(n, action));
    return def ? animKey(n, action, dir, this.suffixOf(def)) : null;
  }

  /**
   * 색 교체 변형 (계약 §10 secondaryVariants·heatVariants colorSwap — 정확 교체, 동시 적용). 현재 층 텍스처를 바탕으로
   * `#cs<태그>` 접미 텍스처·애니를 한 번 만든다. 교체가 없거나 시트가 없으면 null (호출 쪽은 원본)
   */
  recolored(
    scene: Phaser.Scene,
    name: string,
    action: string,
    swaps: readonly ColorSwap[],
  ): { texture: string; anim: (dir: Facing) => string } | null {
    const def = this.sheet(name, action);
    const base = this.textureKey(name, action);
    if (!def || !base || swaps.length === 0 || !scene.textures.exists(base)) return null;
    const suffix = `${this.suffixOf(def)}#cs${swapTag(swaps)}`;
    const texture = sheetTextureKey(def.name, def.action, suffix);
    if (!scene.textures.exists(texture)) {
      const table = buildSwapTable(
        swaps.map((c) => c.from),
        swaps.map((c) => c.to),
      );
      addRecoloredTexture(scene, base, texture, def, table);
    }
    this.createAnims(scene, def, suffix);
    return { texture, anim: (dir) => animKey(def.name, def.action, dir, suffix) };
  }

  /**
   * 특정 열만 반복하는 파생 애니 (보스 돌진 1↔2). 현재 층 변형 텍스처로 1회 생성. 시트가 없으면 null
   */
  phaseAnim(
    scene: Phaser.Scene,
    name: string,
    action: string,
    dir: Facing,
    columns: number[],
    frameMs: number,
  ): string | null {
    const def = this.sheet(name, action);
    const base = this.animKey(name, action, dir);
    const texture = this.textureKey(name, action);
    if (!def || !base || !texture || columns.length === 0) return null;
    const key = phaseAnimKey(base, columns);
    if (!scene.anims.exists(key)) {
      const frames = columns.map((c) => ({ key: texture, frame: frameAt(def, dir, c), duration: frameMs }));
      scene.anims.create({ key, frames, frameRate: 1000 / frameMs, repeat: -1 });
    }
    return key;
  }

  /** 1층 원본 애니 등록 (Preloader) */
  createBaseAnims(scene: Phaser.Scene): void {
    for (const def of this.sheets.values()) this.createAnims(scene, def, '');
  }

  /**
   * 층 진입: 강조 램프 12칸을 현재 층 ramp 로 치환한 텍스처·애니를 만든다 (키에 `@f<n>` 접미).
   * 1층은 치환 없음. 램프가 없는 층은 원본 유지.
   */
  activate(scene: Phaser.Scene, floor: number): void {
    const suffix = variantSuffix(floor);
    const to = rampFor(PALETTE, floor);
    const from = rampFor(PALETTE, BASE_FLOOR);
    if (!suffix || !to || !from) {
      this.suffix = '';
      return;
    }
    this.suffix = suffix;
    if (this.builtVariants.has(suffix)) return;
    const table = buildSwapTable(from, to);
    for (const def of this.sheets.values()) {
      // 53라운드 Q62: 이펙트·paletteSwap "none" 시트는 층 램프를 바꾸지 않는다 (원본 키를 그대로 쓴다)
      if (paletteSwapExempt(def)) continue;
      const key = sheetTextureKey(def.name, def.action, suffix);
      if (!scene.textures.exists(key)) addRecoloredTexture(scene, def.textureKey, key, def, table);
      this.createAnims(scene, def, suffix);
    }
    this.builtVariants.add(suffix);
  }

  private createAnims(scene: Phaser.Scene, def: SheetDef, suffix: string): void {
    const texture = sheetTextureKey(def.name, def.action, suffix);
    const durations = frameDurations(def);
    for (const dir of FACINGS) {
      const key = animKey(def.name, def.action, dir, suffix);
      if (scene.anims.exists(key)) continue;
      const frames = frameIndices(def, dir).map((frame, i) => ({ key: texture, frame, duration: durations[i] }));
      scene.anims.create({ key, frames, frameRate: def.fps, repeat: def.loop ? -1 : 0 });
    }
  }

  /** 디버그 훅용 요약 */
  summary(scene?: Phaser.Scene): {
    sheets: string[];
    anims: string[];
    variant: string;
    aliases: Record<string, string>;
  } {
    const anims: string[] = [];
    if (scene) for (const a of scene.anims['anims'].getArray()) anims.push(a.key);
    return {
      sheets: [...this.sheets.keys()].sort(),
      anims: anims.sort(),
      variant: this.suffix,
      aliases: Object.fromEntries(this.aliases),
    };
  }

  /** 테스트·리셋용 */
  clear(): void {
    this.sheets.clear();
    this.aliases.clear();
    this.builtVariants.clear();
    this.suffix = '';
  }
}

/** 원본 텍스처를 캔버스에 복사해 색 표대로 재채색한 텍스처(프레임 = 시트 격자)를 `key` 로 등록 */
function addRecoloredTexture(
  scene: Phaser.Scene,
  baseKey: string,
  key: string,
  def: SheetDef,
  table: Map<number, [number, number, number]>,
): void {
  const src = scene.textures.get(baseKey).getSourceImage() as HTMLImageElement | HTMLCanvasElement;
  const canvas = document.createElement('canvas');
  canvas.width = src.width;
  canvas.height = src.height;
  const ctx = canvas.getContext('2d', { willReadFrequently: true })!;
  ctx.drawImage(src, 0, 0);
  const img = ctx.getImageData(0, 0, canvas.width, canvas.height);
  recolorPixels(img.data, table);
  ctx.putImageData(img, 0, 0);
  const tex = scene.textures.addCanvas(key, canvas)!;
  tex.setFilter(Phaser.Textures.FilterMode.NEAREST);
  const rows = def.directions.length;
  for (let i = 0; i < rows * def.frames; i++) {
    tex.add(
      i,
      0,
      (i % def.frames) * def.frameWidth,
      Math.floor(i / def.frames) * def.frameHeight,
      def.frameWidth,
      def.frameHeight,
    );
  }
}

export const spriteLibrary = new SpriteLibrary();
