/**
 * 스프라이트 시트 라이브러리 (계약 contracts/art-assets.md §1·§2).
 * Preloader(부팅 묶음)·Game preload(런 무기 묶음, 57라운드 A2 — `sheetLoader`)가 시트를 등록하고, Game 이 층 진입 시
 * `activate(scene, floor)` 로 팔레트 변형을 만든다. 무기를 바꾸면 이전 무기 시트는 `removeSheets` 로 내린다.
 * 엔티티는 `animKey(name, action, dir)` 만 묻는다 — 시트가 없으면 null (플레이스홀더 유지).
 * 53라운드 Q62: 이펙트·`paletteSwap: "none"` 시트는 층 변형을 만들지 않고 늘 원본 키 (`paletteSwapExempt`).
 * 51·53라운드 계약 §10: 2단 갈래·가열 색 교체는 `recolored` 가 같은 캔버스 재채색으로 변형 텍스처·애니를 만든다.
 */
import Phaser from 'phaser';
import { PALETTE } from '../../data';
import { BASE_FLOOR, buildSwapTable, rampFor, recolorPixels, variantSuffix } from '../palette';
import { swapTag, type ColorSwap } from '../fx/fxVariants';
import {
  DIAGONALS,
  FACINGS,
  animKey,
  animRowNames,
  cardinalOf,
  frameAt,
  frameDurations,
  frameIndices,
  paletteSwapExempt,
  phaseAnimKey,
  sheetId,
  sheetTextureKey,
  type Diagonal,
  type SheetDef,
} from './spriteDefs';

class SpriteLibrary {
  private readonly sheets = new Map<string, SheetDef>();
  /** 자기 시트가 없는 이름 → 대신 쓰는 시트 이름 (2~7층 보스 → stage1) */
  private readonly aliases = new Map<string, string>();
  /** 현재 층 변형 접미 ('' = 1층 원본) */
  private suffix = '';
  private readonly builtVariants = new Set<string>();
  /** 만든 층 변형 접미 → 층 번호 (늦게 등록한 시트의 변형을 같은 램프로) */
  private readonly variantFloors = new Map<string, number>();

  /** Preloader: 텍스처가 실제로 로드된 시트만 등록한다 */
  register(def: SheetDef): void {
    this.sheets.set(sheetId(def.name, def.action), def);
  }

  /**
   * 57라운드 A2: 시트를 등록하고 원본 애니 + 이미 만든 층 변형(텍스처·애니)까지 만든다 — 부팅 뒤 늦게 로드한 무기 시트도
   * 층 진입(activate) 때 만든 변형과 같은 상태가 된다. 텍스처가 로드된 시트만 넘긴다
   */
  addSheets(scene: Phaser.Scene, defs: readonly SheetDef[]): void {
    if (defs.length === 0) return;
    for (const def of defs) {
      this.register(def);
      this.createAnims(scene, def, '');
    }
    const from = rampFor(PALETTE, BASE_FLOOR);
    for (const suffix of this.builtVariants) {
      const floor = this.variantFloors.get(suffix);
      const to = floor !== undefined ? rampFor(PALETTE, floor) : null;
      if (!from || !to) continue;
      const table = buildSwapTable(from, to);
      for (const def of defs) this.buildVariant(scene, def, suffix, table);
    }
  }

  /**
   * 57라운드 A2: 시트를 내린다 — 등록 해제 + 원본·층 변형·색 교체 텍스처와 그 텍스처를 쓰는 애니 제거 (GPU 메모리 반환).
   * 그 시트를 쓰던 개체가 남아 있지 않을 때(씬 시작 preload)만 부른다. 내린 텍스처 키 수
   */
  removeSheets(scene: Phaser.Scene, ids: readonly { name: string; action: string }[]): number {
    const bases = new Set<string>();
    for (const { name, action } of ids) {
      const id = sheetId(name, action);
      const def = this.sheets.get(id);
      if (!def) continue;
      this.sheets.delete(id);
      bases.add(def.textureKey);
    }
    if (bases.size === 0) return 0;
    const isOwned = (key: string) => {
      if (bases.has(key)) return true;
      const cut = key.search(/[@#]/);
      return cut > 0 && bases.has(key.slice(0, cut));
    };
    const removed = new Set(scene.textures.getTextureKeys().filter(isOwned));
    const anims = (scene.anims as unknown as { anims: Phaser.Structs.Map<string, Phaser.Animations.Animation> }).anims;
    for (const a of anims.getArray()) if (a.frames.some((f) => removed.has(f.textureKey))) scene.anims.remove(a.key);
    for (const key of removed) scene.textures.remove(key);
    return removed.size;
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

  /**
   * 현재 층 변형이 적용된 애니 키. 시트가 없으면 null. 56라운드: 시트에 없는 행 이름(4행 시트의 대각)은 그 대체 행의 키
   */
  animKey(name: string, action: string, dir: string): string | null {
    const n = this.resolve(name);
    const def = this.sheets.get(sheetId(n, action));
    return def ? animKey(n, action, this.rowName(def, dir), this.suffixOf(def)) : null;
  }

  /** 애니가 있는 행 이름 (시트에 있으면 그대로, 4행 시트의 대각은 가로 성분, 그 밖은 down) */
  private rowName(def: SheetDef, dir: string): string {
    if (animRowNames(def).includes(dir)) return dir;
    return (DIAGONALS as readonly string[]).includes(dir) ? cardinalOf(dir as Diagonal) : FACINGS[0];
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
  ): { texture: string; anim: (dir: string) => string } | null {
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
      addRecoloredTexture(scene, base, texture, table);
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
    dir: string,
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
    for (const def of this.sheets.values()) this.buildVariant(scene, def, suffix, table);
    this.builtVariants.add(suffix);
    this.variantFloors.set(suffix, floor);
  }

  /** 층 변형 텍스처·애니 하나 (53라운드 Q62: 이펙트·paletteSwap "none" 시트는 층 램프를 바꾸지 않는다 — 원본 키를 그대로 쓴다) */
  private buildVariant(
    scene: Phaser.Scene,
    def: SheetDef,
    suffix: string,
    table: Map<number, [number, number, number]>,
  ): void {
    if (paletteSwapExempt(def)) return;
    const key = sheetTextureKey(def.name, def.action, suffix);
    if (!scene.textures.exists(key)) addRecoloredTexture(scene, def.textureKey, key, table);
    this.createAnims(scene, def, suffix);
  }

  private createAnims(scene: Phaser.Scene, def: SheetDef, suffix: string): void {
    const texture = sheetTextureKey(def.name, def.action, suffix);
    const durations = frameDurations(def);
    // 56라운드: 4방향 + 시트의 대각·크기 행 (4행 시트의 대각 키는 만들지 않는다 — animKey 가 4방향 키로 대체)
    for (const dir of animRowNames(def)) {
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
    this.variantFloors.clear();
    this.suffix = '';
  }
}

/**
 * 원본 텍스처를 캔버스에 복사해 색 표대로 재채색한 텍스처를 `key` 로 등록. 프레임은 원본 텍스처의 프레임을 그대로 옮긴다
 * (격자 시트 = 칸, 57라운드 트림 아틀라스 = 잘린 영역 + trim 오프셋 — 프레임 번호·피벗 의미가 원본과 같다)
 */
function addRecoloredTexture(
  scene: Phaser.Scene,
  baseKey: string,
  key: string,
  table: Map<number, [number, number, number]>,
): void {
  const base = scene.textures.get(baseKey);
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
  copyFrames(base, tex);
}

/** 원본 텍스처의 프레임(이름·잘린 영역·trim)을 같은 크기의 다른 텍스처로 옮긴다 (`__BASE` 제외) */
export function copyFrames(from: Phaser.Textures.Texture, to: Phaser.Textures.Texture): void {
  for (const name of from.getFrameNames()) {
    const f = from.get(name);
    // 이름은 원본 그대로 (격자 시트 = 숫자, 아틀라스 = 문자열 번호)
    const nf = to.add(f.name, 0, f.cutX, f.cutY, f.cutWidth, f.cutHeight);
    if (nf && f.trimmed) nf.setTrim(f.realWidth, f.realHeight, f.x, f.y, f.cutWidth, f.cutHeight);
  }
}

export const spriteLibrary = new SpriteLibrary();
