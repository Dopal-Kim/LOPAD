/**
 * 62 루프 2 G (UI 요청): 시트 칸의 **보이는 그림 윗변** — 칸(예 드랍 시트 80×96) 위쪽 투명 줄 수.
 * 장터 노점 카드 자리(`UiShopOffer.screen`)를 칸 윗변이 아니라 물건 그림 윗변에 맞추려고 쓴다. 칸마다 한 번 읽고 기억한다.
 */
import type Phaser from 'phaser';

/** 이 알파(0..255) 이상이면 보이는 픽셀 */
const OPAQUE_ALPHA = 16;

/** RGBA 바이트 배열에서 처음 보이는 줄 (없으면 h) — Phaser 없음 (테스트) */
export function firstOpaqueRow(data: ArrayLike<number>, w: number, h: number, alphaMin = OPAQUE_ALPHA): number {
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) if (data[(y * w + x) * 4 + 3] >= alphaMin) return y;
  return h;
}

const cache = new Map<string, number>();

/**
 * 칸 원 크기(realHeight) 기준 위쪽 투명 줄 수 (텍스처 픽셀). 트림 칸이면 잘린 위 여백까지 더한다.
 * 읽을 수 없으면(캔버스 없음·다른 출처) 0 — 칸 윗변 그대로
 */
export function frameOpaqueTop(textures: Phaser.Textures.TextureManager, key: string, frame: string | number): number {
  const id = `${key}#${frame}`;
  const hit = cache.get(id);
  if (hit !== undefined) return hit;
  let rows = 0;
  try {
    const f = textures.getFrame(key, frame);
    const src = f?.source.image as HTMLImageElement | HTMLCanvasElement | undefined;
    if (f && src && f.cutWidth > 0 && f.cutHeight > 0) {
      const canvas = document.createElement('canvas');
      canvas.width = f.cutWidth;
      canvas.height = f.cutHeight;
      const ctx = canvas.getContext('2d', { willReadFrequently: true });
      if (ctx) {
        ctx.drawImage(src, f.cutX, f.cutY, f.cutWidth, f.cutHeight, 0, 0, f.cutWidth, f.cutHeight);
        const top = firstOpaqueRow(ctx.getImageData(0, 0, f.cutWidth, f.cutHeight).data, f.cutWidth, f.cutHeight);
        // 다 투명한 칸이면 칸 윗변 그대로
        rows = top >= f.cutHeight ? 0 : top + (f.trimmed ? f.y : 0);
      }
    }
  } catch {
    rows = 0;
  }
  cache.set(id, rows);
  return rows;
}
