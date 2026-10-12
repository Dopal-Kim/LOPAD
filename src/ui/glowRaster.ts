import Phaser from 'phaser';

/**
 * 62 루프 2 UI D (렉): 발광 글자 한 줄을 **캔버스 하나**에 굽는다.
 *
 * 예전 GlowText 는 같은 글을 Phaser Text 13개(그늘 8 · 할로 4 · 본색 1)로 겹쳤다. Text 하나마다
 *  ① 만들 때 글꼴 높이 측정(MeasureText — 캔버스에 그려 픽셀을 훑는다) ② 빈 글·글·색 세 번 다시 그리기 ③ 그때마다 GPU 업로드
 * 가 일어나, 카드 3장 메뉴(글 30여 개)를 열 때 Text 400개 · 측정 400번 · 업로드 1,200번이 한 프레임에 몰렸다.
 * 이제는 게임마다 **공유 래스터 Text 하나**(표시 목록 밖, GPU 업로드 없음)가 흰 글자를 한 번 그리고, 글자마다 자기 캔버스 하나에
 * 색 입힌 사본을 그늘 → 할로 → 본색 순서로 찍어 **한 번만** 올린다. 글꼴 높이는 글꼴·크기마다 한 번 재어 둔다.
 * 겹치는 순서·알파(각 사본 globalAlpha 로 source-over)는 예전 Text 겹치기와 같은 식이다.
 */

/** 그릴 글의 모양 */
export interface RasterStyle {
  fontFamily: string;
  px: number;
  align: 'left' | 'center' | 'right';
  /** 줄바꿈 폭 (없으면 한 줄) */
  wrap?: number;
  /** 글꼴 읽기가 끝났는가 (끝난 뒤에만 높이 측정을 저장한다 — 폴백 글꼴 값이 남지 않게) */
  settled: boolean;
}

/** 찍을 한 겹: 색 · 알파 · 자리 (글자 상자 왼쪽 위 기준) */
export interface RasterLayer {
  color: string;
  alpha: number;
  offsets: readonly (readonly [number, number])[];
}

/** 줄 간격 (px) */
const LINE_SPACING = 4;

type Metrics = Phaser.Types.GameObjects.Text.TextMetrics;

const rasters = new WeakMap<Phaser.Game, Phaser.GameObjects.Text>();
const metricsCache = new Map<string, Metrics>();
let tintCanvas: HTMLCanvasElement | null = null;

/** 통계 (헤드리스 측정용): 그린 횟수 · 측정 횟수 */
export const rasterStats = { draws: 0, measures: 0 };

function rasterOf(scene: Phaser.Scene): Phaser.GameObjects.Text {
  let r = rasters.get(scene.game);
  if (!r) {
    // 씬에 붙이지 않는다 (표시 목록 밖) — 씬이 꺼져도 남는다. 그리기만 하고 GPU 로 올리지 않는다
    // 줄 간격은 TextStyle 이 아니라 Text 가 갖는다 (할로·그늘 때문에 줄 간격 ≥ 글꼴 높이 + 4, 계약 1.2절)
    r = new Phaser.GameObjects.Text(scene, 0, 0, '', { resolution: 1, lineSpacing: LINE_SPACING });
    (r as unknown as { renderer: unknown }).renderer = null;
    rasters.set(scene.game, r);
  }
  return r;
}

function tint(w: number, h: number): CanvasRenderingContext2D | null {
  if (typeof document === 'undefined') return null;
  if (!tintCanvas) tintCanvas = document.createElement('canvas');
  if (tintCanvas.width < w) tintCanvas.width = w;
  if (tintCanvas.height < h) tintCanvas.height = h;
  return tintCanvas.getContext('2d');
}

/**
 * 흰 글자를 공유 래스터에 그린다. 글자 상자(폭·높이 — 예전 Text 의 width·height 와 같다)를 돌려준다.
 * 돌려받은 캔버스는 다음 호출 때 바뀌므로 곧바로 `stamp` 로 옮긴다.
 */
export function rasterize(
  scene: Phaser.Scene,
  text: string,
  s: RasterStyle,
): { canvas: HTMLCanvasElement; w: number; h: number } {
  const r = rasterOf(scene);
  const key = `${s.fontFamily}|${s.px}`;
  const cached = metricsCache.get(key);
  // 측정해 둔 높이가 없으면 setStyle(updateText true) 로 이 글꼴을 잰다 (false 면 앞 글꼴의 측정값이 그대로 남는다)
  r.style.setStyle(
    {
      fontFamily: s.fontFamily,
      fontSize: `${s.px}px`,
      color: '#ffffff',
      align: s.align,
      resolution: 1,
      wordWrap: s.wrap ? { width: s.wrap, useAdvancedWrap: false } : undefined,
      metrics: cached,
    },
    !cached,
    true,
  );
  if (!cached) {
    rasterStats.measures++;
    if (s.settled) metricsCache.set(key, r.style.getTextMetrics());
  }
  if (r.text !== text) r.setText(text);
  else r.updateText();
  rasterStats.draws++;
  return { canvas: r.canvas, w: Math.ceil(r.width), h: Math.ceil(r.height) };
}

/**
 * 래스터(흰 글자)를 겹마다 색을 입혀 `dst` 에 찍는다 (`pad` = 글자 상자 바깥 여백, 예전 RING).
 * dst 는 미리 (w + pad*2)×(h + pad*2) 로 맞춰 둔다.
 */
export function stamp(
  dst: CanvasRenderingContext2D,
  src: { canvas: HTMLCanvasElement; w: number; h: number },
  pad: number,
  layers: RasterLayer[],
): void {
  const { w, h } = src;
  dst.clearRect(0, 0, dst.canvas.width, dst.canvas.height);
  if (w <= 0 || h <= 0) return;
  const t = tint(w, h);
  if (!t) return;
  for (const l of layers) {
    if (!l.offsets.length || l.alpha <= 0) continue;
    t.globalCompositeOperation = 'copy';
    t.globalAlpha = 1;
    t.drawImage(src.canvas, 0, 0, w, h, 0, 0, w, h);
    t.globalCompositeOperation = 'source-in';
    t.fillStyle = l.color;
    t.fillRect(0, 0, w, h);
    dst.globalAlpha = l.alpha;
    for (const [dx, dy] of l.offsets) dst.drawImage(t.canvas, 0, 0, w, h, pad + dx, pad + dy, w, h);
  }
  dst.globalAlpha = 1;
  t.globalCompositeOperation = 'source-over';
}
