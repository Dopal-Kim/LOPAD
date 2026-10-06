/**
 * 61 단계 5 (P13 §3) 보스 기둥 숨기 방지의 순수 기하 (Phaser 의존 없음 — 단위 테스트·bossSim 기둥 시뮬이 함께 쓴다).
 * - 가려짐: 보스 → 주인공 선분이 서 있는 기둥 발자국(사각형)을 지나는지
 * - 가려짐 누적: 가려진 동안 +dt, 보이면 −dt × decay (잠깐 고개를 내밀어도 0 으로 돌아가지 않게)
 * - 우회 조향: 보스 몸 반폭만큼 부풀린 기둥이 앞을 막으면, 그 기둥의 네 모서리 중 (보스 → 모서리 → 주인공) 이 가장 짧은 곳으로
 */

export interface Pt {
  x: number;
  y: number;
}

export interface Box {
  x: number;
  y: number;
  w: number;
  h: number;
}

/** 사각형을 사방 (px, py) 만큼 부풀림 */
export function inflate(r: Box, px: number, py = px): Box {
  return { x: r.x - px, y: r.y - py, w: r.w + px * 2, h: r.h + py * 2 };
}

export function contains(r: Box, p: Pt): boolean {
  return p.x > r.x && p.x < r.x + r.w && p.y > r.y && p.y < r.y + r.h;
}

/**
 * 선분 a→b 가 사각형 안쪽을 지나는지 (Liang–Barsky). 변에 스치기만 하면 false — 모서리 웨이포인트로 가는 선이 막히지 않게
 * 안쪽으로 eps 만큼 줄여 잰다
 */
export function segmentHitsBox(a: Pt, b: Pt, r: Box, eps = 0.5): boolean {
  const x0 = r.x + eps;
  const y0 = r.y + eps;
  const x1 = r.x + r.w - eps;
  const y1 = r.y + r.h - eps;
  if (x1 <= x0 || y1 <= y0) return false;
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  let t0 = 0;
  let t1 = 1;
  const clip = (p: number, q: number): boolean => {
    if (p === 0) return q >= 0;
    const t = q / p;
    if (p < 0) {
      if (t > t1) return false;
      if (t > t0) t0 = t;
    } else {
      if (t < t0) return false;
      if (t < t1) t1 = t;
    }
    return true;
  };
  return clip(-dx, a.x - x0) && clip(dx, x1 - a.x) && clip(-dy, a.y - y0) && clip(dy, y1 - a.y) && t0 < t1;
}

/** 선분이 지나는 첫 사각형의 번호 (a 에서 가까운 순, 없으면 -1) */
export function firstBlocker(a: Pt, b: Pt, boxes: readonly Box[]): number {
  let best = -1;
  let bd = Infinity;
  boxes.forEach((r, i) => {
    if (!segmentHitsBox(a, b, r)) return;
    const d = Math.hypot(r.x + r.w / 2 - a.x, r.y + r.h / 2 - a.y);
    if (d < bd) {
      bd = d;
      best = i;
    }
  });
  return best;
}

/** 보스 → 주인공이 기둥에 가려졌나 */
export function lineBlocked(from: Pt, to: Pt, boxes: readonly Box[]): boolean {
  return firstBlocker(from, to, boxes) >= 0;
}

/** 가려짐 누적 (ms): 가려지면 +dt, 보이면 −dt × decay (0 아래로 내려가지 않음) */
export function stepHidden(prevMs: number, hidden: boolean, dtMs: number, decay: number): number {
  return hidden ? prevMs + dtMs : Math.max(0, prevMs - dtMs * decay);
}

/** 사각형의 네 모서리를 밖으로 margin 만큼 민 점 (왼위·오위·오아래·왼아래) */
export function corners(r: Box, margin: number): Pt[] {
  return [
    { x: r.x - margin, y: r.y - margin },
    { x: r.x + r.w + margin, y: r.y - margin },
    { x: r.x + r.w + margin, y: r.y + r.h + margin },
    { x: r.x - margin, y: r.y + r.h + margin },
  ];
}

export interface SteerMemo {
  /** 지금 돌아가는 기둥 번호 · 고른 모서리 (-1 = 없음) */
  box: number;
  corner: number;
}

export function newSteerMemo(): SteerMemo {
  return { box: -1, corner: -1 };
}

/**
 * 다음 웨이포인트: from(보스 바디 중심) → to(주인공) 가 부풀린 기둥(`boxes` — 이미 보스 반폭만큼 부풀린 것)에 막히면 그 기둥 모서리,
 * 아니면 to. 모서리는 (from → 모서리 → to) 가 가장 짧고 from 에서 곧장 갈 수 있는 것 — 이미 고른 모서리는 다른 곳이
 * stickPx 이상 짧아야 바꾼다(떨림 방지). 모서리에 reachPx 안으로 닿으면 다음 모서리를 다시 고른다
 */
export function steerWaypoint(
  from: Pt,
  to: Pt,
  boxes: readonly Box[],
  memo: SteerMemo,
  o: { marginPx: number; stickPx: number; reachPx: number },
): Pt {
  const i = firstBlocker(from, to, boxes);
  if (i < 0) {
    memo.box = -1;
    memo.corner = -1;
    return to;
  }
  const r = boxes[i];
  // 주인공이 기둥에 붙어 부풀린 사각형 안이면: 사각형 밖 가장 가까운 자리를 목표로 돌고, 거기서 곧장 보이면 주인공에게
  const goal = contains(r, to) ? pushOut(r, to, o.marginPx) : to;
  if (goal !== to && !segmentHitsBox(from, goal, r)) {
    memo.box = -1;
    memo.corner = -1;
    return to;
  }
  const cs = corners(r, o.marginPx);
  const inside = contains(r, from);
  // 모서리에 거의 닿았으면 그 모서리에 선 것으로 보고 다음 모서리를 본다 (모서리 직전에서 기둥을 긁는 선이 막혀 되도는 것 방지)
  const at = cs.find((c) => Math.hypot(c.x - from.x, c.y - from.y) <= o.reachPx) ?? from;
  const rest = cornerDistances(cs, goal, r);
  const cost = (k: number) => Math.hypot(cs[k].x - from.x, cs[k].y - from.y) + rest[k];
  let best = -1;
  let bc = Infinity;
  cs.forEach((c, k) => {
    if (Math.hypot(c.x - from.x, c.y - from.y) <= o.reachPx) return;
    // 부풀린 기둥에 이미 닿아 있으면(몸이 붙음) 그 모서리로 미끄러진다 — 막힘 검사 생략
    if (!inside && segmentHitsBox(at, c, r)) return;
    const v = cost(k);
    if (v < bc) {
      bc = v;
      best = k;
    }
  });
  if (best < 0) return to;
  if (memo.box === i && memo.corner >= 0 && memo.corner !== best) {
    const keep = cs[memo.corner];
    const reach = Math.hypot(keep.x - from.x, keep.y - from.y) > o.reachPx;
    const free = inside || !segmentHitsBox(at, keep, r);
    if (reach && free && cost(memo.corner) <= bc + o.stickPx) best = memo.corner;
  }
  memo.box = i;
  memo.corner = best;
  return cs[best];
}

/** 사각형 안의 점을 가장 가까운 변 밖으로 margin 만큼 */
export function pushOut(r: Box, p: Pt, margin: number): Pt {
  const left = p.x - r.x;
  const right = r.x + r.w - p.x;
  const top = p.y - r.y;
  const bottom = r.y + r.h - p.y;
  const m = Math.min(left, right, top, bottom);
  if (m === left) return { x: r.x - margin, y: p.y };
  if (m === right) return { x: r.x + r.w + margin, y: p.y };
  if (m === top) return { x: p.x, y: r.y - margin };
  return { x: p.x, y: r.y + r.h + margin };
}

/**
 * 모서리마다 to 까지 기둥을 돌아가는 최단 거리 (모서리 4 + to 의 작은 그래프 — 서로 곧장 갈 수 있는 점끼리만 잇는다).
 * 모서리 → to 가 기둥에 막혀도 이웃 모서리를 거치는 길이를 쓴다 (되돌아가는 모서리를 싸게 보지 않게)
 */
function cornerDistances(cs: readonly Pt[], to: Pt, r: Box): number[] {
  const d = cs.map((c) => (segmentHitsBox(c, to, r) ? Infinity : Math.hypot(to.x - c.x, to.y - c.y)));
  const done = cs.map(() => false);
  for (let n = 0; n < cs.length; n++) {
    let u = -1;
    for (let k = 0; k < cs.length; k++) if (!done[k] && (u < 0 || d[k] < d[u])) u = k;
    if (u < 0 || d[u] === Infinity) break;
    done[u] = true;
    for (let k = 0; k < cs.length; k++) {
      if (done[k] || segmentHitsBox(cs[u], cs[k], r)) continue;
      const v = d[u] + Math.hypot(cs[k].x - cs[u].x, cs[k].y - cs[u].y);
      if (v < d[k]) d[k] = v;
    }
  }
  return d;
}
