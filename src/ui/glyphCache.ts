import Phaser from 'phaser';
import { rasterize, stamp, type RasterLayer, type RasterStyle } from './glowRaster';

/**
 * 62 루프 2 UI D (렉): 구운 발광 글자 텍스처 재사용 풀.
 * 같은 글·글꼴·줄바꿈·색 겹(그늘·할로·본색)이면 이미 구워 GPU 에 올린 텍스처를 그대로 쓴다 — 같은 메뉴를 다시 열거나
 * 고름 자리를 옮길 때(선택·비선택 스타일 오가기), 카드 키 [1]·머리표·안내 줄처럼 되풀이되는 글은 굽지도 올리지도 않는다.
 * 쓰는 글자가 없는 텍스처는 바로 지우지 않고 남겨 두었다가, 풀이 `POOL_MAX` 개를 넘으면 쓰지 않는 것 중 오래된 것부터 지운다.
 */

export interface Glyph {
  readonly tex: Phaser.Textures.CanvasTexture;
  /** 글자(링 제외) 폭·높이 */
  readonly textW: number;
  readonly textH: number;
  /** 지금 이 텍스처를 쓰는 글자 수 */
  refs: number;
}

/** 풀 크기 (넘으면 쓰지 않는 텍스처 중 오래된 것부터 지운다 — 쓰는 중인 것은 지우지 않는다) */
const POOL_MAX = 320;

const caches = new WeakMap<Phaser.Game, Map<string, Glyph>>();

/** 통계 (헤드리스 측정용) */
export const glyphStats = { hits: 0, misses: 0, evicted: 0 };

function cacheOf(game: Phaser.Game): Map<string, Glyph> {
  let c = caches.get(game);
  if (!c) {
    c = new Map();
    caches.set(game, c);
  }
  return c;
}

/** 풀 열쇠: 글꼴 · 크기 · 정렬 · 줄바꿈 · 여백 · 겹(색·알파·자리) · 글 */
export function glyphKey(text: string, s: RasterStyle, pad: number, layers: RasterLayer[]): string {
  const ls = layers.map((l) => `${l.color}/${l.alpha}/${l.offsets.map((o) => o.join(',')).join(';')}`).join('|');
  return `${s.fontFamily}\u0001${s.px}\u0001${s.align}\u0001${s.wrap ?? 0}\u0001${pad}\u0001${ls}\u0001${text}`;
}

/** 이 글자 텍스처를 빌린다 (없으면 굽고 올린다). 다 쓰면 `releaseGlyph` */
export function acquireGlyph(
  scene: Phaser.Scene,
  text: string,
  s: RasterStyle,
  pad: number,
  layers: RasterLayer[],
): Glyph {
  const cache = cacheOf(scene.game);
  const key = glyphKey(text, s, pad, layers);
  const hit = cache.get(key);
  if (hit) {
    glyphStats.hits++;
    // 최근에 쓴 것을 뒤로 (지울 때 앞에서부터)
    cache.delete(key);
    cache.set(key, hit);
    hit.refs++;
    return hit;
  }
  glyphStats.misses++;
  const src = rasterize(scene, text, s);
  // 텍스처 관리자 목록에 넣지 않는다 (Text 와 같은 방식 — 키 없음).
  // CanvasTexture 는 만들 때 캔버스 전체를 getImageData 로 읽는다 — 가속 캔버스면 GPU 에서 되읽어 수백 ms 가 걸린다
  // (헤드리스 측정: 글 37개에 6.3초). 1×1 로 만들고 크기를 맞춘 뒤 그려 한 번만 올린다.
  const canvas = Phaser.Display.Canvas.CanvasPool.create(cache, 1, 1);
  const tex = scene.textures.addCanvas(null as unknown as string, canvas, true)!;
  sizeCanvasTexture(tex, src.w + pad * 2, src.h + pad * 2);
  const ctx = canvas.getContext('2d');
  if (ctx) stamp(ctx, src, pad, layers);
  tex.refresh();
  const g: Glyph = { tex, textW: src.w, textH: src.h, refs: 1 };
  cache.set(key, g);
  trim(cache);
  return g;
}

/** CanvasTexture 크기만 맞춘다 (`setSize` 는 바로 올리므로 — 그린 뒤 `refresh` 한 번) */
function sizeCanvasTexture(tex: Phaser.Textures.CanvasTexture, w: number, h: number): void {
  const canvas = tex.getSourceImage() as HTMLCanvasElement;
  canvas.width = w;
  canvas.height = h;
  const source = tex.source[0];
  source.width = w;
  source.height = h;
  tex.get().setSize(w, h, 0, 0);
  const t = tex as unknown as { width: number; height: number };
  t.width = w;
  t.height = h;
}

/** 빌린 텍스처를 돌려준다 */
export function releaseGlyph(game: Phaser.Game, g: Glyph): void {
  g.refs = Math.max(0, g.refs - 1);
  trim(cacheOf(game));
}

function trim(cache: Map<string, Glyph>): void {
  if (cache.size <= POOL_MAX) return;
  for (const [k, e] of cache) {
    if (cache.size <= POOL_MAX) break;
    if (e.refs > 0) continue;
    cache.delete(k);
    const c = e.tex.getSourceImage() as HTMLCanvasElement;
    e.tex.destroy();
    Phaser.Display.Canvas.CanvasPool.remove(c);
    glyphStats.evicted++;
  }
}
