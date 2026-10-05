/**
 * 61라운드 E 보스 등장 동작 시간표 (아트 2 `bosses/v3/<보스>_intro` — walkLoop·toastLoop·roarFrame·phaseFrames·stride).
 * 걸음 열 반복(walkLoops 번, 그동안 보폭 × 횟수만큼 걸어 들어옴) → 딸꾹·건배 올림 1회 → 건배 유지 반복(포효 시각까지) → 포효·대기 1회.
 * Phaser 의존 없음 — 재생은 scenes/game/BossIntroArt.
 */
export interface IntroSheetMeta {
  frames: number;
  frameDurationsMs?: number[];
  walkLoop?: number[];
  toastLoop?: number[];
  roarFrame?: number;
  stride?: { px: number; cycleMs: number };
}

export interface IntroArtPlan {
  walkCols: number[];
  walkMs: number;
  /** 걸어 들어오는 거리 (시트 도트 — 월드는 × 그림 배율) */
  walkDots: number;
  /** 걸음 다음 1회 (딸꾹 + 건배 올림) */
  raiseCols: number[];
  raiseMs: number;
  toastCols: number[];
  /** 포효 1회 (포효 열부터 끝까지) · 시작 시각 · 길이 */
  roarCols: number[];
  roarAtMs: number;
  roarMs: number;
}

function range(a: number, b: number): number[] {
  const out: number[] = [];
  for (let c = a; c <= b; c++) out.push(c);
  return out;
}

/** 시트 메타로 시간표를 만든다. 걸음·건배·포효 열이 없으면 null (등장 동작 없이 대기 그림) */
export function introArtPlan(
  m: IntroSheetMeta,
  opts: { walkLoops?: number; roarAtMs?: number; speechAtMs: number },
): IntroArtPlan | null {
  const [w0, w1] = m.walkLoop ?? [];
  const [t0, t1] = m.toastLoop ?? [];
  const roar = m.roarFrame;
  if (w0 === undefined || w1 === undefined || t0 === undefined || t1 === undefined || roar === undefined) return null;
  if (!(w0 <= w1 && w1 < t0 && t0 <= t1 && t1 < roar && roar < m.frames)) return null;
  const d = (c: number) => m.frameDurationsMs?.[c] ?? 100;
  const sum = (cols: number[]) => cols.reduce((a, c) => a + d(c), 0);
  const loops = Math.max(0, Math.round(opts.walkLoops ?? 2));
  const walkCols = range(w0, w1);
  const walkMs = sum(walkCols) * loops;
  const raiseCols = range(w1 + 1, t0 - 1);
  const raiseMs = sum(raiseCols);
  const roarCols = range(roar, m.frames - 1);
  // 포효는 건배를 올린 뒤 — 데이터가 없으면 대사 시작 0.7초 뒤
  const roarAtMs = Math.max(walkMs + raiseMs, opts.roarAtMs ?? opts.speechAtMs + 700);
  return {
    walkCols,
    walkMs,
    walkDots: (m.stride?.px ?? 0) * loops,
    raiseCols,
    raiseMs,
    toastCols: range(t0, t1),
    roarCols,
    roarAtMs,
    roarMs: sum(roarCols),
  };
}
