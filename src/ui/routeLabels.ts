/**
 * 61라운드 플레이 점검 #10: 노드 지도 이름표가 다른 아이콘·표지(보상·위험·도장)·이름표와 겹치지 않게 자리를 고른다 (순수 계산).
 * 자리 후보: 오른쪽(기본) → 왼쪽 → 아래 → 위 → 오른쪽 조금 아래 → 오른쪽 조금 위. 겹치지 않고 지도 칸 안인 첫 자리,
 * 없으면 겹침이 가장 적은 자리. 먼저 놓을 것(지금·갈 수 있는 곳)부터 놓아 그 이름표가 좋은 자리를 갖는다.
 */
export interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface LabelItem {
  id: string;
  /** 아이콘 가운데 */
  x: number;
  y: number;
  /** 이름표 크기 */
  w: number;
  h: number;
  /** 작을수록 먼저 놓는다 */
  priority: number;
}

export type LabelSide = 'right' | 'left' | 'below' | 'above' | 'rightLow' | 'rightHigh';

export interface PlacedLabel {
  x: number;
  y: number;
  side: LabelSide;
}

function overlap(a: Rect, b: Rect): number {
  const w = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x);
  const h = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
  return w > 0 && h > 0 ? w * h : 0;
}

function outside(r: Rect, area: Rect): number {
  const inside = overlap(r, area);
  return r.w * r.h - inside;
}

/** 이름표 자리 후보 (왼쪽 위 좌표) */
export function labelCandidates(it: LabelItem, iconHalf: number, gap: number): { side: LabelSide; r: Rect }[] {
  const { x, y, w, h } = it;
  const midY = Math.round(y - h / 2);
  const cx = Math.round(x - w / 2);
  return [
    { side: 'right', r: { x: x + iconHalf + gap, y: midY, w, h } },
    { side: 'left', r: { x: x - iconHalf - gap - w, y: midY, w, h } },
    { side: 'below', r: { x: cx, y: y + iconHalf + gap, w, h } },
    { side: 'above', r: { x: cx, y: y - iconHalf - gap - h, w, h } },
    { side: 'rightLow', r: { x: x + iconHalf + gap, y: midY + Math.round(h * 0.75), w, h } },
    { side: 'rightHigh', r: { x: x + iconHalf + gap, y: midY - Math.round(h * 0.75), w, h } },
  ];
}

export function placeLabels(
  items: readonly LabelItem[],
  obstacles: readonly Rect[],
  area: Rect,
  iconHalf: number,
  gap: number,
): Map<string, PlacedLabel> {
  const out = new Map<string, PlacedLabel>();
  const taken: Rect[] = [...obstacles];
  const order = [...items].sort((a, b) => a.priority - b.priority);
  for (const it of order) {
    let best: { side: LabelSide; r: Rect } | null = null;
    let bestCost = Infinity;
    for (const c of labelCandidates(it, iconHalf, gap)) {
      // 지도 칸 밖은 크게, 겹침은 그 넓이만큼
      const cost = outside(c.r, area) * 4 + taken.reduce((s, o) => s + overlap(c.r, o), 0);
      if (cost < bestCost) {
        bestCost = cost;
        best = c;
        if (cost === 0) break;
      }
    }
    if (!best) continue;
    out.set(it.id, { x: Math.round(best.r.x), y: Math.round(best.r.y), side: best.side });
    taken.push(best.r);
  }
  return out;
}
