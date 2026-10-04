/**
 * 56라운드 2단계 활 화살비 순수 규칙 (Phaser 의존 없음 — 계약 art §18.9): 원 안 무작위 낙하점 · 예고 원 시트 열 시간표
 * (appear [0,1] 1회 → 첫 낙하까지 wait 루프 [2..5] → 낙하 동안 rain [6,7](마지막 칸 유지) → out [8,9]).
 */

export interface Pt {
  x: number;
  y: number;
}

/** 원(중심·반지름) 안 고른 분포 n 점. rand = 0..1 난수 */
export function rainPoints(cx: number, cy: number, radius: number, n: number, rand: () => number): Pt[] {
  const out: Pt[] = [];
  for (let i = 0; i < n; i++) {
    const r = radius * Math.sqrt(rand());
    const a = rand() * Math.PI * 2;
    out.push({ x: cx + Math.cos(a) * r, y: cy + Math.sin(a) * r });
  }
  return out;
}

/** 예고 원 열 구간 (시트 frameRoles 순서 — 시트가 다르면 호출 쪽이 넘긴다) */
export interface MarkPhases {
  appear: number[];
  wait: number[];
  rain: number[];
  out: number[];
}

export const DEFAULT_MARK_PHASES: MarkPhases = { appear: [0, 1], wait: [2, 3, 4, 5], rain: [6, 7], out: [8, 9] };

/**
 * 시각 e(좌클릭부터 ms)의 예고 원 열. 끝났으면 -1.
 * rainFrom = 첫 낙하 · rainTo = 마지막 꽂힘 (그 사이 rain 열을 차례로, 마지막 칸 유지) · d = 시트 프레임 길이
 */
export function markColumn(
  e: number,
  rainFrom: number,
  rainTo: number,
  d: readonly number[],
  ph = DEFAULT_MARK_PHASES,
): number {
  const dur = (c: number) => Math.max(1, d[c] ?? 60);
  let t = e;
  // 등장 (첫 낙하가 그보다 이르면 등장 중에도 낙하로 넘어간다)
  if (e < rainFrom) {
    for (const c of ph.appear) {
      if (t < dur(c)) return c;
      t -= dur(c);
    }
    const loop = ph.wait.reduce((a, c) => a + dur(c), 0);
    let w = loop > 0 ? t % loop : 0;
    for (const c of ph.wait) {
      if (w < dur(c)) return c;
      w -= dur(c);
    }
    return ph.wait[ph.wait.length - 1] ?? 0;
  }
  if (e < rainTo) {
    let r = e - rainFrom;
    for (const c of ph.rain) {
      if (r < dur(c)) return c;
      r -= dur(c);
    }
    return ph.rain[ph.rain.length - 1] ?? 0;
  }
  let o = e - rainTo;
  for (const c of ph.out) {
    if (o < dur(c)) return c;
    o -= dur(c);
  }
  return -1;
}
