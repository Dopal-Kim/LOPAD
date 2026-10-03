/**
 * 획 그리기 (51라운드 1절): 캔버스 2D 로 그린다 — 안티앨리어싱이 켜져 있어 가장자리가 캔버스 픽셀 1칸보다 잘게
 * (부분 덮임 알파로) 나뉜다. 게임 설정 pixelArt 의 nearest 와 무관(이 캔버스는 1:1 로 붙는다).
 *
 * - 자국(보통 합성, 투명 바탕): 표본 폭을 따르는 **리본 다각형 하나**(+ 둥근 끝)로 칠한다 — 한 경로라 겹침이 진해지지 않는다.
 * - 빛(검정 불투명 바탕, 'lighten' = 채널별 최댓값): 조각마다 열기가 달라 여러 번 칠하지만 최댓값이라 겹친 곳이 진해지지 않는다.
 *   이 캔버스는 Phaser 에서 ADD 로 얹는다(검정 = 더하지 않음).
 * Phaser 의존 없음.
 */
import type { StrokeSample } from './strokeFxSpline';

export type Ctx = CanvasRenderingContext2D;

/** 0xRRGGBB × k (k > 1 이면 남는 만큼 흰색 쪽으로) → 'rgb(…)' (검정 바탕에 미리 곱한 빛) */
export function lightColor(color: number, k: number): string {
  const r = (color >> 16) & 0xff;
  const g = (color >> 8) & 0xff;
  const b = color & 0xff;
  const a = Math.max(0, Math.min(1, k));
  const over = Math.max(0, Math.min(1, k - 1));
  const ch = (c: number) => Math.round(Math.min(255, c * a + (255 - c * a) * over));
  return `rgb(${ch(r)},${ch(g)},${ch(b)})`;
}

/** 0xRRGGBB + 알파 → 'rgba(…)' */
export function rgba(color: number, a: number): string {
  return `rgba(${(color >> 16) & 0xff},${(color >> 8) & 0xff},${color & 0xff},${Math.max(0, Math.min(1, a))})`;
}

/** 표본 j 의 단위 법선 (앞뒤 표본 방향, 배열 전체 기준이라 조각 경계에서도 이어진다) */
function normalAt(pts: StrokeSample[], j: number): { nx: number; ny: number } {
  const a = pts[Math.max(0, j - 1)];
  const b = pts[Math.min(pts.length - 1, j + 1)];
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  const len = Math.hypot(dx, dy) || 1;
  return { nx: -dy / len, ny: dx / len };
}

/** 리본 폭 기준: 'w' = 흔들림 있는 폭(자국), 'wb' = 흔들림 없는 폭(빛) */
export type WidthKey = 'w' | 'wb';

/**
 * 표본 [a, b] 를 폭(폭 × scale + add, 최소 minW)의 리본 다각형 + 양 끝 원으로 현재 경로에 더한다.
 * 원의 감는 방향을 다각형과 맞춰 nonzero 채우기에서 합집합이 되게 한다.
 */
export function addRibbon(
  ctx: Ctx,
  pts: StrokeSample[],
  a: number,
  b: number,
  scale: number,
  add = 0,
  minW = 0.2,
  key: WidthKey = 'w',
): void {
  if (b < a || pts.length === 0) return;
  const half = (j: number) => Math.max(minW, pts[j][key] * scale + add) / 2;
  if (a === b) {
    ctx.moveTo(pts[a].x + half(a), pts[a].y);
    ctx.arc(pts[a].x, pts[a].y, half(a), 0, Math.PI * 2);
    return;
  }
  const L: number[] = [];
  const R: number[] = [];
  for (let j = a; j <= b; j++) {
    const { nx, ny } = normalAt(pts, j);
    const h = half(j);
    L.push(pts[j].x + nx * h, pts[j].y + ny * h);
    R.push(pts[j].x - nx * h, pts[j].y - ny * h);
  }
  // 다각형: L 정방향 → R 역방향
  let area = 0;
  const poly: number[] = [...L];
  for (let k = R.length - 2; k >= 0; k -= 2) poly.push(R[k], R[k + 1]);
  ctx.moveTo(poly[0], poly[1]);
  for (let k = 2; k < poly.length; k += 2) {
    ctx.lineTo(poly[k], poly[k + 1]);
    area += poly[k - 2] * poly[k + 1] - poly[k] * poly[k - 1];
  }
  area += poly[poly.length - 2] * poly[1] - poly[0] * poly[poly.length - 1];
  ctx.closePath();
  const ccw = area < 0;
  for (const j of [a, b]) {
    const h = half(j);
    ctx.moveTo(pts[j].x + h, pts[j].y);
    ctx.arc(pts[j].x, pts[j].y, h, 0, Math.PI * 2, ccw);
  }
}

/** 리본 하나를 채운다 */
export function fillRibbon(
  ctx: Ctx,
  pts: StrokeSample[],
  a: number,
  b: number,
  style: string,
  scale: number,
  add = 0,
  minW = 0.2,
  key: WidthKey = 'w',
): void {
  ctx.beginPath();
  addRibbon(ctx, pts, a, b, scale, add, minW, key);
  ctx.fillStyle = style;
  ctx.fill('nonzero');
}

/** 틈 가장자리에서 off(px) 밖(부호 sign) 을 따라가는 가는 선 */
export function strokeEdge(
  ctx: Ctx,
  pts: StrokeSample[],
  sign: 1 | -1,
  off: (p: StrokeSample) => number,
  style: string,
  lineWidth: number,
): void {
  if (pts.length < 2) return;
  ctx.beginPath();
  for (let j = 0; j < pts.length; j++) {
    const { nx, ny } = normalAt(pts, j);
    const o = off(pts[j]) * sign;
    const x = pts[j].x + nx * o;
    const y = pts[j].y + ny * o;
    if (j === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.strokeStyle = style;
  ctx.lineWidth = lineWidth;
  ctx.lineJoin = 'round';
  ctx.lineCap = 'round';
  ctx.stroke();
}

/** 중심선 (가는 심) */
export function strokeCenter(ctx: Ctx, pts: StrokeSample[], style: string, lineWidth: number): void {
  if (pts.length < 2) return;
  ctx.beginPath();
  ctx.moveTo(pts[0].x, pts[0].y);
  for (let j = 1; j < pts.length; j++) ctx.lineTo(pts[j].x, pts[j].y);
  ctx.strokeStyle = style;
  ctx.lineWidth = lineWidth;
  ctx.lineJoin = 'round';
  ctx.lineCap = 'round';
  ctx.stroke();
}

/** 결정적 0~1 (표본 번호 → 들뜬 조각 자리) */
export function hash01(i: number, salt = 0): number {
  let h = Math.imul(i ^ Math.imul(salt + 1, 0x9e3779b1), 2654435761) >>> 0;
  h ^= h >>> 15;
  h = Math.imul(h, 2246822519) >>> 0;
  h ^= h >>> 13;
  return (h >>> 0) / 4294967296;
}

/** 빛의 방사 점 (섬광 머리·펜 끝) — 'lighter' 로 더한다 */
export function glowDot(ctx: Ctx, x: number, y: number, r: number, color: number, a: number): void {
  const g = ctx.createRadialGradient(x, y, 0, x, y, r);
  g.addColorStop(0, lightColor(color, a * 1.4));
  g.addColorStop(0.4, lightColor(color, a * 0.6));
  g.addColorStop(1, 'rgb(0,0,0)');
  ctx.fillStyle = g;
  ctx.beginPath();
  ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.fill();
}
