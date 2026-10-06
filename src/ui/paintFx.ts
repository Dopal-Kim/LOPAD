/**
 * 61 단계 6 (P14 §3) 그림 속 입구 — 캔버스 그리기 (DOM 캔버스, 셰이더 없음).
 * - 방 화면 캡처 → 붓 그림(색 줄임·먹 윤곽·종이 결·가장자리 번짐)
 * - 입구 그림이 없을 때 대체 입구 그림: 지역 키아트(있으면) 위에 붓으로 그린 입구(아치·성문·문·동굴) + 안쪽 빛
 * - 덮개: 입구 안 어둠(가운데 빛 번짐) · 종이/지도 바탕
 * 계산은 `transitionView.ts` (순수, 테스트).
 */
import { GRAY, SEPIA } from './theme';
import { TRANSITION } from './themeTransition';
import {
  brushOrder,
  doorShape,
  fallbackDoorRect,
  hexRgb,
  orderFromGray,
  paintPixels,
  paperPixels,
  rng,
  type DoorRect,
} from './transitionView';

export type Img = CanvasImageSource & { width: number; height: number };

export function makeCanvas(w: number, h: number): HTMLCanvasElement {
  const c = document.createElement('canvas');
  c.width = Math.max(1, Math.round(w));
  c.height = Math.max(1, Math.round(h));
  return c;
}

function ctx2d(c: HTMLCanvasElement): CanvasRenderingContext2D {
  const ctx = c.getContext('2d', { willReadFrequently: true });
  if (!ctx) throw new Error('[ui] 2d canvas');
  return ctx;
}

/** 원본을 w×h 로 덮어(비율 유지·가운데 자름) 부드럽게 줄여 그린다 */
function drawCover(ctx: CanvasRenderingContext2D, src: Img, w: number, h: number): void {
  const s = Math.max(w / src.width, h / src.height);
  const sw = w / s;
  const sh = h / s;
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(src, (src.width - sw) / 2, (src.height - sh) / 2, sw, sh, 0, 0, w, h);
}

const PAPER = hexRgb(SEPIA[TRANSITION.paperSepia]);
const PAPER_LIGHT = hexRgb(SEPIA[4]);

/** 캡처(또는 그림) → 붓 그림 캔버스 (w×h) */
export function paintedCanvas(src: Img, w: number, h: number, seed: number): HTMLCanvasElement {
  const c = makeCanvas(w, h);
  const ctx = ctx2d(c);
  drawCover(ctx, src, w, h);
  const data = ctx.getImageData(0, 0, w, h);
  const T = TRANSITION;
  paintPixels(data.data, w, h, {
    levels: T.posterLevels,
    keepSat: T.keepSat,
    warm: T.warm,
    inkEdge: T.inkEdge,
    grain: T.grain,
    bleed: T.bleed,
    paper: PAPER,
    seed,
  });
  ctx.putImageData(data, 0, 0);
  return c;
}

/** 종이 한 장 (바탕 색 + 결) */
export function paperCanvas(
  w: number,
  h: number,
  seed: number,
  base: [number, number, number] = PAPER,
): HTMLCanvasElement {
  const c = makeCanvas(w, h);
  const ctx = ctx2d(c);
  const img = ctx.createImageData(w, h);
  img.data.set(paperPixels(w, h, base, seed));
  ctx.putImageData(img, 0, 0);
  return c;
}

/** 종이 위 원경 먹 번짐 (키아트가 없을 때 대체 그림 바탕) */
function inkHills(ctx: CanvasRenderingContext2D, w: number, h: number, rand: () => number): void {
  for (let k = 0; k < 3; k++) {
    const base = h * (0.55 + k * 0.12);
    ctx.fillStyle = `rgba(20,16,12,${0.18 + k * 0.14})`;
    ctx.beginPath();
    ctx.moveTo(0, h);
    for (let x = 0; x <= w; x += w / 24) {
      const y = base - Math.sin((x / w) * Math.PI * (1.5 + k) + rand() * 0.6) * h * 0.06 - rand() * h * 0.03;
      ctx.lineTo(x, y);
    }
    ctx.lineTo(w, h);
    ctx.closePath();
    ctx.fill();
  }
}

/** 붓 결이 남는 굵은 선 (같은 길을 조금씩 어긋나게 여러 번) */
function roughStroke(
  ctx: CanvasRenderingContext2D,
  path: (dx: number, dy: number) => void,
  width: number,
  color: string,
  rand: () => number,
  passes = 3,
): void {
  ctx.strokeStyle = color;
  ctx.lineJoin = 'round';
  ctx.lineCap = 'round';
  for (let i = 0; i < passes; i++) {
    ctx.lineWidth = width * (0.7 + rand() * 0.5);
    ctx.globalAlpha = 0.55 + rand() * 0.35;
    ctx.beginPath();
    path((rand() - 0.5) * width * 0.4, (rand() - 0.5) * width * 0.4);
    ctx.stroke();
  }
  ctx.globalAlpha = 1;
}

/** 입구 안: 어둠 + 아래쪽 가운데 빛 (light) */
function doorInside(ctx: CanvasRenderingContext2D, r: DoorRect, light: string, clip: () => void): void {
  ctx.save();
  ctx.beginPath();
  clip();
  ctx.clip();
  ctx.fillStyle = GRAY[1];
  ctx.fillRect(r.x - 4, r.y - 4, r.w + 8, r.h + 8);
  const [lr, lg, lb] = hexRgb(light);
  const glow = ctx.createRadialGradient(r.x + r.w / 2, r.y + r.h * 0.82, 1, r.x + r.w / 2, r.y + r.h * 0.7, r.h * 0.75);
  glow.addColorStop(0, `rgba(${lr},${lg},${lb},0.55)`);
  glow.addColorStop(0.45, `rgba(${lr},${lg},${lb},0.16)`);
  glow.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = glow;
  ctx.fillRect(r.x - 4, r.y - 4, r.w + 8, r.h + 8);
  ctx.restore();
}

/** 아치 길 (위 반원 + 기둥) */
function archPath(ctx: CanvasRenderingContext2D, r: DoorRect, dx = 0, dy = 0): void {
  const rad = r.w / 2;
  ctx.moveTo(r.x + dx, r.y + r.h + dy);
  ctx.lineTo(r.x + dx, r.y + rad + dy);
  ctx.arc(r.x + rad + dx, r.y + rad + dy, rad, Math.PI, 0);
  ctx.lineTo(r.x + r.w + dx, r.y + r.h + dy);
}

/** 동굴 입 (울퉁불퉁한 둥근 입) */
function cavePath(ctx: CanvasRenderingContext2D, r: DoorRect, seed: number, dx = 0, dy = 0): void {
  const rand = rng(seed);
  const cx = r.x + r.w / 2 + dx;
  const by = r.y + r.h + dy;
  ctx.moveTo(r.x + dx, by);
  const n = 14;
  for (let i = 0; i <= n; i++) {
    const a = Math.PI + (i / n) * Math.PI;
    const k = 0.86 + rand() * 0.2;
    ctx.lineTo(cx + Math.cos(a) * (r.w / 2) * k, by + Math.sin(a) * r.h * k);
  }
  ctx.lineTo(r.x + r.w + dx, by);
}

/**
 * 대체 입구 그림 (w×h): 바탕(키아트 붓 그림 또는 종이 + 먹 번짐) + 노드 종류에 맞는 입구 + 안쪽 빛, 마지막에 붓 그림 처리.
 * 돌려주는 rect 가 파고들 입구 사각형 (그림 픽셀).
 */
export function fallbackDoor(
  base: Img | null,
  w: number,
  h: number,
  nodeKind: string,
  light: string,
  seed: number,
): { canvas: HTMLCanvasElement; rect: DoorRect } {
  const c = makeCanvas(w, h);
  const ctx = ctx2d(c);
  const rand = rng(seed);
  if (base) drawCover(ctx, base, w, h);
  else {
    ctx.drawImage(paperCanvas(w, h, seed, PAPER_LIGHT), 0, 0);
    inkHills(ctx, w, h, rand);
  }
  // 입구 둘레를 어둡게 (시선이 입구로)
  const vig = ctx.createRadialGradient(w / 2, h * 0.62, h * 0.12, w / 2, h * 0.6, w * 0.62);
  vig.addColorStop(0, 'rgba(0,0,0,0)');
  vig.addColorStop(1, 'rgba(0,0,0,0.45)');
  ctx.fillStyle = vig;
  ctx.fillRect(0, 0, w, h);
  const shape = doorShape(nodeKind);
  const r = fallbackDoorRect(shape, w, h);
  const stone = GRAY[6];
  const dark = GRAY[2];
  const wood = SEPIA[3];
  const ground = () => {
    ctx.fillStyle = 'rgba(12,10,8,0.55)';
    ctx.beginPath();
    ctx.ellipse(r.x + r.w / 2, r.y + r.h + 2, r.w * 0.95, r.h * 0.08, 0, 0, Math.PI * 2);
    ctx.fill();
  };
  ground();
  if (shape === 'cave') {
    // 바위 둘레 → 입
    roughStroke(
      ctx,
      (dx, dy) => cavePath(ctx, { x: r.x - 10, y: r.y - 10, w: r.w + 20, h: r.h + 10 }, seed, dx, dy),
      14,
      stone,
      rand,
      4,
    );
    doorInside(ctx, r, light, () => cavePath(ctx, r, seed));
  } else if (shape === 'door') {
    // 문틀 + 처마 + 등불
    const lw = Math.max(6, r.w * 0.16);
    ctx.fillStyle = wood;
    ctx.fillRect(r.x - lw, r.y - lw * 0.6, r.w + lw * 2, r.h + lw * 0.6);
    doorInside(ctx, r, light, () => ctx.rect(r.x, r.y, r.w, r.h));
    roughStroke(
      ctx,
      (dx, dy) => {
        ctx.moveTo(r.x - lw * 3 + dx, r.y - lw * 0.4 + dy);
        ctx.lineTo(r.x + r.w / 2 + dx, r.y - lw * 2.6 + dy);
        ctx.lineTo(r.x + r.w + lw * 3 + dx, r.y - lw * 0.4 + dy);
      },
      lw * 1.1,
      dark,
      rand,
    );
    const [lr, lg, lb] = hexRgb(light);
    const lx = r.x + r.w + lw * 2;
    const ly = r.y + r.h * 0.25;
    const lamp = ctx.createRadialGradient(lx, ly, 1, lx, ly, lw * 3);
    lamp.addColorStop(0, `rgba(${lr},${lg},${lb},0.9)`);
    lamp.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = lamp;
    ctx.fillRect(lx - lw * 3, ly - lw * 3, lw * 6, lw * 6);
  } else {
    // 아치(전투·엘리트) · 성문(보스): 돌 테 + (성문은 지붕)
    const rim = Math.max(8, r.w * (shape === 'gate' ? 0.22 : 0.18));
    roughStroke(
      ctx,
      (dx, dy) => archPath(ctx, { x: r.x - rim / 2, y: r.y - rim / 2, w: r.w + rim, h: r.h + rim / 2 }, dx, dy),
      rim,
      stone,
      rand,
      4,
    );
    doorInside(ctx, r, light, () => archPath(ctx, r));
    if (shape === 'gate') {
      const top = r.y - rim * 1.4;
      roughStroke(
        ctx,
        (dx, dy) => {
          ctx.moveTo(r.x - rim * 3 + dx, top + rim + dy);
          ctx.quadraticCurveTo(r.x + r.w / 2 + dx, top - rim * 1.2 + dy, r.x + r.w + rim * 3 + dx, top + rim + dy);
        },
        rim * 1.2,
        dark,
        rand,
      );
    }
  }
  // 붓 그림으로 한 번에 (바탕·입구가 같은 결)
  const data = ctx.getImageData(0, 0, w, h);
  const T = TRANSITION;
  paintPixels(data.data, w, h, {
    levels: T.posterLevels + 1,
    keepSat: 0.8,
    warm: T.warm * 0.5,
    inkEdge: T.inkEdge * 0.6,
    grain: T.grain,
    bleed: T.bleed * 0.6,
    paper: PAPER,
    seed: seed + 7,
  });
  ctx.putImageData(data, 0, 0);
  return { canvas: c, rect: r };
}

/** 덮개 색 (RGBA, w×h): 'dark' = 입구 안 어둠 + 가운데 빛 번짐, 'paper' = 종이(또는 주어진 바탕 그림을 어둡게) */
export function coverPixels(
  kind: 'dark' | 'paper',
  w: number,
  h: number,
  light: string,
  seed: number,
  under: Img | null = null,
): Uint8ClampedArray {
  const c = makeCanvas(w, h);
  const ctx = ctx2d(c);
  if (kind === 'dark') {
    ctx.fillStyle = GRAY[TRANSITION.darkGray];
    ctx.fillRect(0, 0, w, h);
    const [lr, lg, lb] = hexRgb(light);
    const g = ctx.createRadialGradient(w / 2, h * 0.62, 1, w / 2, h * 0.58, w * 0.32);
    g.addColorStop(0, `rgba(${lr},${lg},${lb},${TRANSITION.innerGlow})`);
    g.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);
  } else if (under) {
    drawCover(ctx, under, w, h);
    ctx.fillStyle = 'rgba(0,0,0,0.45)';
    ctx.fillRect(0, 0, w, h);
  } else ctx.drawImage(paperCanvas(w, h, seed), 0, 0);
  return ctx.getImageData(0, 0, w, h).data;
}

/** 붓질 마스크 그림(회색) → 걷힘 순서. 그림이 없으면 코드 붓질 */
export function brushOrderFrom(src: Img | null, w: number, h: number, seed: number): Float32Array {
  if (!src) return brushOrder(w, h, seed);
  const c = makeCanvas(w, h);
  const ctx = ctx2d(c);
  ctx.imageSmoothingEnabled = true;
  ctx.drawImage(src, 0, 0, w, h);
  return orderFromGray(ctx.getImageData(0, 0, w, h).data, w * h);
}

/** 캔버스 RGBA 읽기 */
export function readPixels(c: HTMLCanvasElement): Uint8ClampedArray {
  return ctx2d(c).getImageData(0, 0, c.width, c.height).data;
}
