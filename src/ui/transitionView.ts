/**
 * 61 단계 6 (P14 §3, 계약 §19) 그림 속 입구 전환 — 순수 계산 (Phaser·DOM 없음, 테스트한다).
 * 단계 계획 · 파고들기 줌/초점 · 붓질 마스크 · 붓 그림(색 줄임·먹 윤곽·종이 결·가장자리 번짐) · 입구 메타 읽기.
 */
import { TRANSITION } from './themeTransition';

export type TransitionMode = 'enterNode' | 'exitRoom' | 'floor' | 'training';

/** 들어오는 시작 페이로드를 읽은 값 (모르는 값은 기본) */
export interface BeginInfo {
  id: number;
  mode: TransitionMode;
  region: string;
  nodeKind: string;
  doorKey: string | null;
  from: { x: number; y: number } | null;
  /** enterNode: 고른 노드 id · training: 고른 방 id (시스템 추가 필드) */
  nodeId: string | null;
  skippable: boolean;
}

const MODES: readonly TransitionMode[] = ['enterNode', 'exitRoom', 'floor', 'training'];

/** `ui:transition-begin` 페이로드 읽기. id·mode 가 없으면 null */
export function readBegin(p: unknown): BeginInfo | null {
  if (!p || typeof p !== 'object') return null;
  const o = p as Record<string, unknown>;
  const id = typeof o.id === 'number' && Number.isFinite(o.id) ? o.id : null;
  const mode = MODES.find((m) => m === o.mode) ?? null;
  if (id === null || !mode) return null;
  const f = o.from as { x?: unknown; y?: unknown } | null | undefined;
  const from =
    f && typeof f.x === 'number' && typeof f.y === 'number' && Number.isFinite(f.x) && Number.isFinite(f.y)
      ? { x: f.x, y: f.y }
      : null;
  return {
    id,
    mode,
    region: typeof o.region === 'string' ? o.region : '',
    nodeKind: typeof o.nodeKind === 'string' ? o.nodeKind : '',
    doorKey: typeof o.doorKey === 'string' && o.doorKey ? o.doorKey : null,
    from,
    nodeId: typeof o.nodeId === 'string' && o.nodeId ? o.nodeId : null,
    skippable: o.skippable !== false,
  };
}

/** `{ id }` 페이로드의 id (없으면 null) */
export function readId(p: unknown): number | null {
  const id = p && typeof p === 'object' ? (p as { id?: unknown }).id : undefined;
  return typeof id === 'number' && Number.isFinite(id) ? id : null;
}

/** 덮기까지의 단계 (ms) — 걷힘 길이 포함. 모두 합해 1.2~1.8초 */
export interface TransitionPlan {
  /** 입구 그림이 피어나는(floor: 키아트가 떠오르는 · exit: 굳는) 시간 */
  introMs: number;
  /** 액자가 둘러지는 시간 (exit 만) */
  frameMs: number;
  /** 파고들기(줌 인) 또는 줌 아웃 */
  moveMs: number;
  /** 덮개가 걷히는 시간 */
  revealMs: number;
}

export function planFor(mode: TransitionMode): TransitionPlan {
  const T = TRANSITION;
  if (mode === 'floor') return { introMs: T.floorShowMs, frameMs: 0, moveMs: T.floorDiveMs, revealMs: T.floorRevealMs };
  if (mode === 'exitRoom')
    return { introMs: T.freezeMs, frameMs: T.frameMs, moveMs: T.zoomOutMs, revealMs: T.exitRevealMs };
  return { introMs: T.bloomMs, frameMs: 0, moveMs: T.diveMs, revealMs: T.revealMs };
}

export function planTotal(p: TransitionPlan): number {
  return p.introMs + p.frameMs + p.moveMs + p.revealMs;
}

/** 덮이기까지 (READY 를 기다리기 전) */
export function coverAt(p: TransitionPlan): number {
  return p.introMs + p.frameMs + p.moveMs;
}

export const clamp01 = (v: number): number => (v < 0 ? 0 : v > 1 ? 1 : v);
export const easeInOut = (t: number): number => {
  const x = clamp01(t);
  return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
};
export const easeOut = (t: number): number => 1 - Math.pow(1 - clamp01(t), 3);
export const easeIn = (t: number): number => Math.pow(clamp01(t), 3);
export const smooth = (e0: number, e1: number, x: number): number => {
  if (e1 === e0) return x < e0 ? 0 : 1;
  const t = clamp01((x - e0) / (e1 - e0));
  return t * t * (3 - 2 * t);
};

/** 파고들기 배율: 1 → zEnd 를 지수로 (일정한 속도로 빨려 드는 느낌). t 0~1 */
export function diveZoom(t: number, zEnd: number): number {
  const e = easeInOut(t);
  return Math.exp(Math.log(Math.max(1e-3, zEnd)) * e);
}

/**
 * 파고들기 초점: 화면 가운데 C 에 놓일 세계 좌표. 목표 T 는 처음엔 제자리(화면 T)에 있다가 끝에 화면 가운데로 온다.
 * 화면 좌표 = (세계 − f)·z + C. pan = 목표가 가운데로 옮겨 간 정도(0~1).
 */
export function diveFocus(
  pan: number,
  z: number,
  target: { x: number; y: number },
  center: { x: number; y: number },
): { x: number; y: number } {
  const k = (1 - clamp01(pan)) / Math.max(1e-6, z);
  return { x: target.x - (target.x - center.x) * k, y: target.y - (target.y - center.y) * k };
}

/** 세계 → 화면 (container 위치·배율로 쓴다) */
export function worldTransform(
  f: { x: number; y: number },
  z: number,
  center: { x: number; y: number },
): { x: number; y: number; scale: number } {
  return { x: center.x - f.x * z, y: center.y - f.y * z, scale: z };
}

/** 입구 사각형 (그림 픽셀 기준) */
export interface DoorRect {
  x: number;
  y: number;
  w: number;
  h: number;
}

/** 입구 그림 메타: doorRect · light (아트 §28). 그림 크기 밖이면 자른다. 읽을 수 없으면 null */
export function readDoorMeta(
  meta: unknown,
  imgW: number,
  imgH: number,
): { rect: DoorRect | null; light: string | null } {
  if (!meta || typeof meta !== 'object') return { rect: null, light: null };
  const m = meta as Record<string, unknown>;
  const r = (m.doorRect ?? (m.meta as Record<string, unknown> | undefined)?.doorRect) as
    { x?: unknown; y?: unknown; w?: unknown; h?: unknown; width?: unknown; height?: unknown } | unknown[] | undefined;
  let rect: DoorRect | null = null;
  const num = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null);
  if (Array.isArray(r) && r.length >= 4) {
    const [x, y, w, h] = r.map(num);
    if (x !== null && y !== null && w !== null && h !== null) rect = { x, y, w, h };
  } else if (r && typeof r === 'object') {
    const o = r as Record<string, unknown>;
    const x = num(o.x);
    const y = num(o.y);
    const w = num(o.w ?? o.width);
    const h = num(o.h ?? o.height);
    if (x !== null && y !== null && w !== null && h !== null) rect = { x, y, w, h };
  }
  if (rect) {
    const x = Math.max(0, Math.min(imgW - 1, rect.x));
    const y = Math.max(0, Math.min(imgH - 1, rect.y));
    const w = Math.max(1, Math.min(imgW - x, rect.w));
    const h = Math.max(1, Math.min(imgH - y, rect.h));
    rect = { x, y, w, h };
  }
  const lightRaw = m.light ?? (m.meta as Record<string, unknown> | undefined)?.light;
  let light: string | null = null;
  if (typeof lightRaw === 'string' && /^#?[0-9a-f]{6}$/i.test(lightRaw.trim()))
    light = `#${lightRaw.trim().replace('#', '').toLowerCase()}`;
  else if (Array.isArray(lightRaw) && lightRaw.length >= 3 && lightRaw.every((v) => typeof v === 'number'))
    light = rgbHex(lightRaw[0] as number, lightRaw[1] as number, lightRaw[2] as number);
  return { rect, light };
}

export function rgbHex(r: number, g: number, b: number): string {
  const h = (v: number) =>
    Math.max(0, Math.min(255, Math.round(v)))
      .toString(16)
      .padStart(2, '0');
  return `#${h(r)}${h(g)}${h(b)}`;
}

export function hexRgb(hex: string): [number, number, number] {
  const n = parseInt(hex.replace('#', ''), 16) || 0;
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

/** 대체 입구 모양 (그림이 없을 때 코드로 그린다): 아치(전투·엘리트·보스) · 문(상점·수련장) · 동굴(쉼터·이벤트) */
export type DoorShape = 'arch' | 'gate' | 'door' | 'cave';
export function doorShape(nodeKind: string): DoorShape {
  const k = nodeKind.toLowerCase();
  if (k === 'boss') return 'gate';
  if (k === 'shop' || k === 'training') return 'door';
  if (k === 'rest' || k === 'event') return 'cave';
  return 'arch';
}

/** 대체 입구 사각형 (그림 w×h 안, 가운데 조금 아래) */
export function fallbackDoorRect(shape: DoorShape, w: number, h: number): DoorRect {
  const sz: Record<DoorShape, [number, number]> = {
    arch: [0.15, 0.42],
    gate: [0.22, 0.5],
    door: [0.12, 0.38],
    cave: [0.2, 0.36],
  };
  const [fw, fh] = sz[shape];
  const dw = Math.round(w * fw);
  const dh = Math.round(h * fh);
  return { x: Math.round((w - dw) / 2), y: Math.round(h * 0.88 - dh), w: dw, h: dh };
}

/** 지역 코드(계약 §19 region) → UI 키아트 키. boss → 연회장, training·모름 → null (그때는 지역 이름 낱말로 한 번 더 찾는다) */
export function regionKeyart(region: string): string | null {
  const r = region.trim().toLowerCase();
  if (['waste', 'outer', 'gate', 'hall', 'brewery'].includes(r)) return r;
  if (r === 'boss') return 'hall';
  return null;
}

// ---------------------------------------------------------------------------------------------
/** 시드 난수 (mulberry32) */
export function rng(seed: number): () => number {
  let a = seed >>> 0 || 1;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** 값 잡음 (격자 보간) — 0~1 */
function valueNoise(w: number, h: number, cell: number, rand: () => number): Float32Array {
  const gw = Math.ceil(w / cell) + 2;
  const gh = Math.ceil(h / cell) + 2;
  const grid = new Float32Array(gw * gh);
  for (let i = 0; i < grid.length; i++) grid[i] = rand();
  const out = new Float32Array(w * h);
  for (let y = 0; y < h; y++) {
    const gy = y / cell;
    const y0 = Math.floor(gy);
    const fy = gy - y0;
    const sy = fy * fy * (3 - 2 * fy);
    for (let x = 0; x < w; x++) {
      const gx = x / cell;
      const x0 = Math.floor(gx);
      const fx = gx - x0;
      const sx = fx * fx * (3 - 2 * fx);
      const a = grid[y0 * gw + x0];
      const b = grid[y0 * gw + x0 + 1];
      const c = grid[(y0 + 1) * gw + x0];
      const d = grid[(y0 + 1) * gw + x0 + 1];
      out[y * w + x] = a + (b - a) * sx + (c - a) * sy + (a - b - c + d) * sx * sy;
    }
  }
  return out;
}

/**
 * 먹 붓질 걷힘 순서 (그림 마스크 `paint/brush_reveal_*` 가 없을 때). 0 = 먼저 걷힘, 1 = 마지막.
 * 화면을 비스듬한 붓 줄 `strokes` 개로 나눠 위에서부터 차례로, 줄 안에서는 왼쪽(짝수 줄)·오른쪽(홀수 줄)에서 쓸어 간다.
 * 줄 경계는 물결, 붓털 결(가로로 긴 잡음)이 앞쪽을 들쭉날쭉하게 한다.
 */
export function brushOrder(
  w: number,
  h: number,
  seed: number,
  strokes: number = TRANSITION.brushStrokes,
): Float32Array {
  const rand = rng(seed);
  const wave = valueNoise(w, h, Math.max(8, Math.round(w / 6)), rand);
  const bristle = new Float32Array(w * h);
  // 붓털: 줄마다 가로로 길게 늘인 잡음 (세로 1~2px 마다 다른 값)
  const rows = new Float32Array(h);
  for (let y = 0; y < h; y++) rows[y] = rand();
  const fine = valueNoise(w, h, 6, rand);
  for (let y = 0; y < h; y++) {
    const r = rows[y] * 0.7 + rows[Math.max(0, y - 1)] * 0.3;
    for (let x = 0; x < w; x++) bristle[y * w + x] = r * 0.75 + fine[y * w + x] * 0.25;
  }
  const out = new Float32Array(w * h);
  const slope = 0.18;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const i = y * w + x;
      const u = x / Math.max(1, w - 1);
      // 비스듬한 줄 + 물결 경계
      const band = (y / h + (u - 0.5) * slope + (wave[i] - 0.5) * 0.16) * strokes;
      const k = Math.max(0, Math.min(strokes - 1, Math.floor(band)));
      const along = k % 2 === 0 ? u : 1 - u;
      const v = (k + along * 0.92 + (bristle[i] - 0.5) * 0.22) / strokes;
      out[i] = clamp01(v);
    }
  }
  return out;
}

/** 붓질 덮개 알파 (0~1): t 0 = 다 덮임, 1 = 다 걷힘. soft = 앞쪽 번짐 폭 */
export function revealAlpha(order: number, t: number, soft: number = TRANSITION.brushSoft): number {
  const front = t * (1 + soft) - soft;
  return smooth(front, front + soft, order);
}

/** 굳음(붓 그림)이 출구 점에서 번져 나가는 정도 (0 = 아직 사진, 1 = 그림). d = 출구에서의 거리 0~1, n = 잡음 0~1 */
export function freezeAlpha(d: number, n: number, t: number, soft: number = TRANSITION.freezeSoft): number {
  const reach = t * (1 + soft);
  const v = d * 0.85 + n * 0.15;
  return 1 - smooth(reach - soft, reach, v);
}

/** 가장자리 번짐: 테두리에서 bleed(비율) 안쪽까지 종이로 스며드는 정도 0~1 (1 = 종이) */
export function edgeBleed(
  x: number,
  y: number,
  w: number,
  h: number,
  n: number,
  bleed: number = TRANSITION.bleed,
): number {
  const d = Math.min(x / w, y / h, (w - 1 - x) / w, (h - 1 - y) / h);
  const edge = bleed * (0.55 + n * 0.9);
  return 1 - smooth(0, edge, d);
}

export interface PaintOpts {
  levels: number;
  keepSat: number;
  warm: number;
  inkEdge: number;
  grain: number;
  bleed: number;
  paper: [number, number, number];
  seed: number;
}

/**
 * 붓 그림 처리 (RGBA 제자리): 색 단계 줄임 + 채도 줄여 따뜻하게 + 먹 윤곽(밝기 경사) + 종이 결 + 가장자리 종이 번짐.
 * 알파는 255 로 채운다.
 */
export function paintPixels(px: Uint8ClampedArray, w: number, h: number, o: PaintOpts): void {
  const n = w * h;
  const lum = new Float32Array(n);
  for (let i = 0; i < n; i++) lum[i] = (px[i * 4] * 0.299 + px[i * 4 + 1] * 0.587 + px[i * 4 + 2] * 0.114) / 255;
  const rand = rng(o.seed);
  const blot = valueNoise(w, h, 24, rand);
  const fiber = valueNoise(w, h, 3, rand);
  const step = 255 / Math.max(1, o.levels - 1);
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const i = y * w + x;
      const p = i * 4;
      const L = lum[i];
      // 밝기만 단계로 줄이고(붓 얼룩으로 경계를 살짝 흔듦) 색은 채도를 줄여 그 위에 얹는다 — 채널마다 반올림하면 색 테가 생긴다
      const jitter = (blot[i] - 0.5) * step * 0.35;
      const Lq = Math.max(0, Math.min(255, Math.round((L * 255 + jitter) / step) * step));
      const Lm = L * 255 * 0.5 + Lq * 0.5;
      let r = Lm + (px[p] - L * 255) * o.keepSat + o.warm * 40;
      let g = Lm + (px[p + 1] - L * 255) * o.keepSat + o.warm * 18;
      let b = Lm + (px[p + 2] - L * 255) * o.keepSat - o.warm * 22;
      // 먹 윤곽: 밝기 경사가 크면 어둡게
      const xl = x > 0 ? lum[i - 1] : L;
      const xr = x < w - 1 ? lum[i + 1] : L;
      const yu = y > 0 ? lum[i - w] : L;
      const yd = y < h - 1 ? lum[i + w] : L;
      const grad = Math.min(1, Math.hypot(xr - xl, yd - yu) * 2.2);
      const ink = 1 - grad * o.inkEdge * 0.75;
      r *= ink;
      g *= ink;
      b *= ink;
      // 종이 결
      const gr = (fiber[i] - 0.5) * 255 * o.grain;
      r += gr;
      g += gr;
      b += gr * 0.8;
      // 가장자리 번짐 (종이 색으로)
      const e = edgeBleed(x, y, w, h, blot[i], o.bleed);
      r = r + (o.paper[0] - r) * e;
      g = g + (o.paper[1] - g) * e;
      b = b + (o.paper[2] - b) * e;
      px[p] = r;
      px[p + 1] = g;
      px[p + 2] = b;
      px[p + 3] = 255;
    }
  }
}

/** 종이 결 한 장 (RGBA 새 배열) — 바탕 색에 큰 얼룩 + 섬유 */
export function paperPixels(w: number, h: number, base: [number, number, number], seed: number): Uint8ClampedArray {
  const px = new Uint8ClampedArray(w * h * 4);
  const rand = rng(seed);
  const blot = valueNoise(w, h, 40, rand);
  const fiber = valueNoise(w, h, 2, rand);
  for (let i = 0; i < w * h; i++) {
    const k = (blot[i] - 0.5) * 18 + (fiber[i] - 0.5) * 10;
    px[i * 4] = base[0] + k;
    px[i * 4 + 1] = base[1] + k * 0.9;
    px[i * 4 + 2] = base[2] + k * 0.75;
    px[i * 4 + 3] = 255;
  }
  return px;
}

/** 회색 마스크 그림(RGBA) → 걷힘 순서 0~1 (빨강 채널, 밝을수록 늦게) */
export function orderFromGray(px: Uint8ClampedArray, n: number): Float32Array {
  const out = new Float32Array(n);
  for (let i = 0; i < n; i++) out[i] = px[i * 4] / 255;
  return out;
}

/** 건너뛰기: 지금 단계에서 무엇을 할지 */
export type SkipAction = 'toCovered' | 'fastReveal' | 'none';
export function skipAction(phase: 'intro' | 'move' | 'covered' | 'reveal' | 'idle', ready: boolean): SkipAction {
  if (phase === 'intro' || phase === 'move') return 'toCovered';
  if (phase === 'reveal') return 'fastReveal';
  if (phase === 'covered' && ready) return 'fastReveal';
  return 'none';
}
