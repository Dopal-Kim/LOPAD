/**
 * 54라운드 Q18 보스 불타기 상태 (Phaser 없음 — 단위 테스트용). 국면: off → ignite(1회) → loop(반복) → out(1회) → off.
 * 불 위에 있으면 ignite 로 시작하고, 벗어나면 lingerMs 동안은 그대로 타다가 out. ignite·loop 중 다시 불 위면 그대로(loop 유지),
 * out 중 다시 불 위면 ignite 부터.
 */
export type BurnPhase = 'off' | 'ignite' | 'loop' | 'out';

export interface BurnState {
  phase: BurnPhase;
  /** 지금 국면 시작 시각 */
  since: number;
  /** 불에서 벗어난 시각 (0 = 불 위) */
  leftAt: number;
}

export interface BurnTiming {
  igniteMs: number;
  outMs: number;
  lingerMs: number;
}

export function newBurnState(): BurnState {
  return { phase: 'off', since: 0, leftAt: 0 };
}

/** 타는 중 (불 피해·불빛 최대) — out 은 꺼지는 중이라 아님 */
export function isBurning(s: BurnState): boolean {
  return s.phase === 'ignite' || s.phase === 'loop';
}

/** 한 프레임 진행. 이번 프레임에 불붙었으면 'ignited' */
export function stepBurn(s: BurnState, onFire: boolean, now: number, t: BurnTiming): 'ignited' | null {
  if (s.phase === 'off' || s.phase === 'out') {
    if (onFire) {
      s.phase = 'ignite';
      s.since = now;
      s.leftAt = 0;
      return 'ignited';
    }
    if (s.phase === 'out' && now - s.since >= t.outMs) {
      s.phase = 'off';
      s.since = now;
    }
    return null;
  }
  if (s.phase === 'ignite' && now - s.since >= t.igniteMs) {
    s.phase = 'loop';
    s.since += t.igniteMs;
  }
  if (onFire) s.leftAt = 0;
  else {
    if (s.leftAt === 0) s.leftAt = now;
    if (now - s.leftAt >= t.lingerMs) {
      s.phase = 'out';
      s.since = now;
      s.leftAt = 0;
    }
  }
  return null;
}

/**
 * 국면 안 경과 ms → 그 국면의 열. loop 면 반복, 아니면 마지막 열 유지. durations = 시트 전체 프레임 길이(열 번호로 찾음)
 */
export function burnColumn(
  cols: readonly number[],
  durations: readonly number[],
  elapsedMs: number,
  loop: boolean,
  fallbackMs = 100,
): number {
  if (cols.length === 0) return 0;
  const len = (c: number) => Math.max(1, durations[c] ?? fallbackMs);
  const total = cols.reduce((a, c) => a + len(c), 0);
  let t = Math.max(0, elapsedMs);
  if (loop) t %= total;
  else if (t >= total) return cols[cols.length - 1];
  for (const c of cols) {
    if (t < len(c)) return c;
    t -= len(c);
  }
  return cols[cols.length - 1];
}

/** 국면 전체 길이 ms (열이 없으면 fallbackMs) */
export function phaseLengthMs(
  cols: readonly number[] | undefined,
  durations: readonly number[],
  fallbackMs: number,
): number {
  if (!cols || cols.length === 0) return fallbackMs;
  return cols.reduce((a, c) => a + Math.max(1, durations[c] ?? 100), 0);
}
