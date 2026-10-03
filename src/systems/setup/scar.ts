/**
 * 53라운드 Q4 준비: 플레이어가 등에 그은 상흔(3획)의 저장 형식. Phaser 의존 없음.
 * 획 좌표(논리 px)를 등 그림의 상흔 기준 사각형(`BACK.SCAR_RECT`)으로 정규화(0~1, 밖은 잘라 붙임)하고,
 * 거의 직선인 점은 줄여(RDP) 런 상태·세이브에 넣는다. 게임 속 몸 위 그리기(scarAnchor)는 다음 단계.
 */

/** 저장 형식 v1: strokes[i] = [x0, y0, x1, y1, …] (정규화 0~1, 소수 3자리). aspect = 기준 사각형 가로/세로 */
export interface ScarData {
  v: 1;
  aspect: number;
  strokes: number[][];
}

export const SCAR = {
  /** 줄이기 허용 오차 (논리 px) · 획당 최대 점 수 · 최대 획 수 · 소수 자리 */
  SIMPLIFY_PX: 0.9,
  MAX_POINTS: 64,
  MAX_STROKES: 8,
  DECIMALS: 3,
};

export interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
}

/** 획 점 목록(논리 px) → 저장 형식 */
export function encodeScar(strokes: { x: number; y: number }[][], rect: Rect): ScarData {
  const q = 10 ** SCAR.DECIMALS;
  const round = (v: number) => Math.round(Math.max(0, Math.min(1, v)) * q) / q;
  const out: number[][] = [];
  for (const s of strokes.slice(0, SCAR.MAX_STROKES)) {
    if (s.length < 2) continue;
    let pts = simplify(s, SCAR.SIMPLIFY_PX);
    if (pts.length > SCAR.MAX_POINTS) pts = resample(pts, SCAR.MAX_POINTS);
    const flat: number[] = [];
    for (const p of pts) flat.push(round((p.x - rect.x) / rect.w), round((p.y - rect.y) / rect.h));
    out.push(flat);
  }
  return { v: 1, aspect: +(rect.w / rect.h).toFixed(4), strokes: out };
}

/** 세이브에서 읽은 값 검사 (형식이 틀리면 null) */
export function sanitizeScar(d: unknown): ScarData | null {
  if (!d || typeof d !== 'object') return null;
  const o = d as Partial<ScarData>;
  if (o.v !== 1 || typeof o.aspect !== 'number' || !Array.isArray(o.strokes)) return null;
  const strokes = o.strokes
    .slice(0, SCAR.MAX_STROKES)
    .filter(
      (s): s is number[] =>
        Array.isArray(s) &&
        s.length >= 4 &&
        s.length % 2 === 0 &&
        s.every((v) => typeof v === 'number' && v >= 0 && v <= 1),
    );
  return { v: 1, aspect: o.aspect, strokes: strokes.map((s) => s.slice(0, SCAR.MAX_POINTS * 2)) };
}

/** Ramer–Douglas–Peucker (끝점 유지) */
export function simplify<T extends { x: number; y: number }>(pts: T[], eps: number): T[] {
  if (pts.length <= 2) return pts.slice();
  const keep = new Uint8Array(pts.length);
  keep[0] = 1;
  keep[pts.length - 1] = 1;
  const stack: [number, number][] = [[0, pts.length - 1]];
  while (stack.length) {
    const [a, b] = stack.pop()!;
    let best = -1;
    let dmax = eps;
    for (let i = a + 1; i < b; i++) {
      const d = segDist(pts[i], pts[a], pts[b]);
      if (d > dmax) {
        dmax = d;
        best = i;
      }
    }
    if (best >= 0) {
      keep[best] = 1;
      stack.push([a, best], [best, b]);
    }
  }
  return pts.filter((_, i) => keep[i]);
}

/** 길이 기준 n 점으로 다시 찍기 (끝점 포함) */
function resample(pts: { x: number; y: number }[], n: number): { x: number; y: number }[] {
  const cum = [0];
  for (let i = 1; i < pts.length; i++)
    cum.push(cum[i - 1] + Math.hypot(pts[i].x - pts[i - 1].x, pts[i].y - pts[i - 1].y));
  const L = cum[cum.length - 1] || 1;
  const out: { x: number; y: number }[] = [];
  let j = 1;
  for (let k = 0; k < n; k++) {
    const at = (k / (n - 1)) * L;
    while (j < pts.length - 1 && cum[j] < at) j++;
    const seg = cum[j] - cum[j - 1] || 1;
    const t = Math.max(0, Math.min(1, (at - cum[j - 1]) / seg));
    out.push({ x: pts[j - 1].x + (pts[j].x - pts[j - 1].x) * t, y: pts[j - 1].y + (pts[j].y - pts[j - 1].y) * t });
  }
  return out;
}

function segDist(p: { x: number; y: number }, a: { x: number; y: number }, b: { x: number; y: number }): number {
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  const l2 = dx * dx + dy * dy;
  const t = l2 > 0 ? Math.max(0, Math.min(1, ((p.x - a.x) * dx + (p.y - a.y) * dy) / l2)) : 0;
  return Math.hypot(p.x - (a.x + dx * t), p.y - (a.y + dy * t));
}
