/**
 * 스프라이트 시트 라이브러리 (계약 contracts/art-assets.md §1·§2).
 * Preloader 가 시트를 등록하고, Game 이 층 진입 시 `activate(scene, floor)` 로 팔레트 변형을 만든다.
 * 엔티티는 `animKey(name, action, dir)` 만 묻는다 — 시트가 없으면 null (플레이스홀더 유지).
 */
import Phaser from 'phaser';
import { PALETTE } from '../data';
import { BASE_FLOOR, buildSwapTable, rampFor, recolorPixels, variantSuffix } from './palette';
import {
  FACINGS,
  animKey,
  frameDurations,
  frameIndices,
  sheetId,
  sheetTextureKey,
  type Facing,
  type SheetDef,
} from './spriteDefs';

class SpriteLibrary {
  private readonly sheets = new Map<string, SheetDef>();
  /** 현재 층 변형 접미 ('' = 1층 원본) */
  private suffix = '';
  private readonly builtVariants = new Set<string>();

  /** Preloader: 텍스처가 실제로 로드된 시트만 등록한다 */
  register(def: SheetDef): void {
    this.sheets.set(sheetId(def.name, def.action), def);
  }

  has(name: string, action = 'idle'): boolean {
    return this.sheets.has(sheetId(name, action));
  }

  sheet(name: string, action: string): SheetDef | undefined {
    return this.sheets.get(sheetId(name, action));
  }

  get variant(): string {
    return this.suffix;
  }

  /** 현재 층 변형이 적용된 텍스처 키 */
  textureKey(name: string, action: string): string | null {
    return this.has(name, action) ? sheetTextureKey(name, action, this.suffix) : null;
  }

  /** 현재 층 변형이 적용된 애니 키. 시트가 없으면 null */
  animKey(name: string, action: string, dir: Facing): string | null {
    return this.has(name, action) ? animKey(name, action, dir, this.suffix) : null;
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
      const key = sheetTextureKey(def.name, def.action, suffix);
      if (!scene.textures.exists(key)) {
        const base = scene.textures.get(def.textureKey);
        const src = base.getSourceImage() as HTMLImageElement | HTMLCanvasElement;
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
  summary(scene?: Phaser.Scene): { sheets: string[]; anims: string[]; variant: string } {
    const anims: string[] = [];
    if (scene) for (const a of scene.anims['anims'].getArray()) anims.push(a.key);
    return { sheets: [...this.sheets.keys()].sort(), anims: anims.sort(), variant: this.suffix };
  }

  /** 테스트·리셋용 */
  clear(): void {
    this.sheets.clear();
    this.builtVariants.clear();
    this.suffix = '';
  }
}

export const spriteLibrary = new SpriteLibrary();
