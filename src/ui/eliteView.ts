/**
 * 60라운드 계약 §14.9 엘리트 이름표 순수 계산: 아트 트림 아틀라스(§19) 한 프레임을 가로 3조각(왼 캡 · 가운데 · 오른 캡)으로
 * 나누고, 글자 폭에 맞춘 이름표 폭과 화면 안 위치를 구한다. 좌표 단위는 원 프레임 도트(트림 전 `sourceSize`).
 */
export interface TrimFrame {
  frame: { x: number; y: number; w: number; h: number };
  spriteSourceSize: { x: number; y: number; w: number; h: number };
  sourceSize: { w: number; h: number };
}

/** 조각 하나: 텍스처 안 사각형 + 원 프레임 조각 안에서의 왼쪽 어긋남 */
export interface Piece {
  tx: number;
  ty: number;
  w: number;
  h: number;
  /** 원 프레임 조각(왼 캡·가운데·오른 캡) 시작에서 그림이 시작하는 곳 (트림으로 잘린 만큼) */
  dx: number;
  /** 원 프레임 위에서 그림이 시작하는 곳 */
  dy: number;
}

export interface PlateSlices {
  left: Piece | null;
  mid: Piece | null;
  right: Piece | null;
  /** 원 프레임 조각 폭 */
  leftW: number;
  midW: number;
  rightW: number;
  srcW: number;
  srcH: number;
}

/** 원 프레임 [a, b) 구간을 트림된 그림과 겹쳐 텍스처 사각형으로 */
function cut(f: TrimFrame, a: number, b: number): Piece | null {
  const s0 = f.spriteSourceSize.x;
  const s1 = s0 + f.spriteSourceSize.w;
  const from = Math.max(a, s0);
  const to = Math.min(b, s1);
  if (to <= from) return null;
  return {
    tx: f.frame.x + (from - s0),
    ty: f.frame.y,
    w: to - from,
    h: f.frame.h,
    dx: from - a,
    dy: f.spriteSourceSize.y,
  };
}

export function slice3(f: TrimFrame, leftW: number, rightW: number): PlateSlices {
  const W = f.sourceSize.w;
  const l = Math.max(0, Math.min(W, leftW));
  const r = Math.max(0, Math.min(W - l, rightW));
  return {
    left: cut(f, 0, l),
    mid: cut(f, l, W - r),
    right: cut(f, W - r, W),
    leftW: l,
    midW: W - l - r,
    rightW: r,
    srcW: W,
    srcH: f.sourceSize.h,
  };
}

/**
 * 이름표 가운데 폭 (도트): 글자 폭(논리 px ÷ scale) + 좌우 여백, 최소 = minWidth - 캡 두 개.
 * 정수로 올린다.
 */
export function plateMidW(
  textW: number,
  scale: number,
  padDots: number,
  s: Pick<PlateSlices, 'leftW' | 'rightW'>,
  minWidth: number,
): number {
  const need = Math.ceil(textW / Math.max(0.01, scale)) + padDots * 2;
  return Math.max(minWidth - s.leftW - s.rightW, need, 1);
}

/**
 * 이름표 왼쪽 위 (논리 px): 머리 위 점(ax, ay)에서 이름표 아래 끝 = ay - above, 가로 가운데, 화면 여백 안으로.
 * w·h = 이름표 화면 크기(논리 px).
 */
export function platePos(
  ax: number,
  ay: number,
  w: number,
  h: number,
  above: number,
  screenW: number,
  screenH: number,
  margin: number,
): { x: number; y: number } {
  let x = Math.round(ax - w / 2);
  let y = Math.round(ay - above - h);
  x = Math.max(margin, Math.min(screenW - margin - w, x));
  y = Math.max(margin, Math.min(screenH - margin - h, y));
  return { x, y };
}

/** JSON 에서 프레임 '0' 과 nineSlice·글자 자리를 읽는다 (없으면 null — 그 경우 이름표 바탕 없이 글자만) */
export function readPlateJson(j: unknown): {
  frame: TrimFrame;
  leftW: number;
  rightW: number;
  textCenterY: number;
  minWidth: number;
  pivotY: number;
} | null {
  if (!j || typeof j !== 'object') return null;
  const o = j as Record<string, unknown>;
  const frames = o.frames as Record<string, TrimFrame> | undefined;
  const f = frames?.['0'];
  if (!f || !f.frame || !f.spriteSourceSize || !f.sourceSize) return null;
  const ns = (o.nineSlice ?? {}) as { leftWidth?: number; rightWidth?: number };
  const pivot = (o.pivot ?? {}) as { y?: number };
  return {
    frame: f,
    leftW: ns.leftWidth ?? 0,
    rightW: ns.rightWidth ?? 0,
    textCenterY: typeof o.textCenterY === 'number' ? o.textCenterY : Math.round(f.sourceSize.h / 2),
    minWidth: typeof o.minWidth === 'number' ? o.minWidth : 0,
    pivotY: typeof pivot.y === 'number' ? pivot.y : f.sourceSize.h,
  };
}
