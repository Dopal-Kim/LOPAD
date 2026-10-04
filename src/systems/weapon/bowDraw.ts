/**
 * 56라운드 Q9·Q20 활 우클릭 당김·놓기 (Phaser 의존 없음). 누르는 동안 당김(가득까지 fullMs), 떼면 발사, 자동 발사 없음.
 * - 가득 전에 떼면 약한 1발 · 가득 직후 perfectWindowMs 안 = 완벽(강화·화살 미소모·숨 회복) · 그 뒤 = 보통 가득
 * - 가득 뒤 strainAfterMs 넘게 쥐면 흔들림 — strainRampMs 동안 위력이 strainMinMult 까지 줄고 조준이 흔들린다
 * - 숨 집중(감속 정밀 조준) 중에는 완벽 창이 넓고 흔들림이 없다
 * 몸 시트 `player_bow_draw_hold` 열: 진행 progressFrames(f0~5) → 유지 holdLoop(f6~9) → 흔들림 strainLoop(f10~13)
 */
import type { BowDrawDef } from '../../data/types';

export type DrawPower = 'weak' | 'perfect' | 'full' | 'strained';

export interface DrawState {
  /** 당김 진행도 0..1 */
  progress: number;
  /** drawing = 당기는 중 · hold = 가득 유지 · strain = 오래 쥐어 흔들림 */
  phase: 'drawing' | 'hold' | 'strain';
  /** 가득 뒤 경과 ms (가득 전이면 -1) */
  sinceFullMs: number;
  /** 흔들림 정도 0..1 (흔들림 전이면 0) */
  strain: number;
}

/** 당김 시작부터 elapsedMs 의 상태 */
export function drawState(def: BowDrawDef, elapsedMs: number, focus = false): DrawState {
  const progress = Math.max(0, Math.min(1, elapsedMs / Math.max(1, def.fullMs)));
  if (progress < 1) return { progress, phase: 'drawing', sinceFullMs: -1, strain: 0 };
  const since = elapsedMs - def.fullMs;
  if (focus || since < def.strainAfterMs) return { progress: 1, phase: 'hold', sinceFullMs: since, strain: 0 };
  const strain = Math.max(0, Math.min(1, (since - def.strainAfterMs) / Math.max(1, def.strainRampMs)));
  return { progress: 1, phase: 'strain', sinceFullMs: since, strain };
}

export interface ReleaseResult {
  power: DrawPower;
  /** 조준 사격 배율(secondary.damageMult)에 곱할 값 — 약한 화살은 조준 배율 대신 이 값만 */
  damageMult: number;
  /** 약한 화살: 조준 배율을 쓰지 않는다 */
  replacesAimed: boolean;
  /** 화살 미소모 (완벽) */
  refund: boolean;
  /** 관통 (가득 이상) */
  pierce: boolean;
}

/** 놓는 순간 분류 */
export function releaseShot(
  def: BowDrawDef,
  elapsedMs: number,
  opts: { focus?: boolean; windowMult?: number } = {},
): ReleaseResult {
  const st = drawState(def, elapsedMs, opts.focus);
  if (st.progress < 1)
    return { power: 'weak', damageMult: def.weakDamageMult, replacesAimed: true, refund: false, pierce: false };
  const win = def.perfectWindowMs * (opts.windowMult ?? 1);
  if (st.sinceFullMs <= win)
    return { power: 'perfect', damageMult: def.perfectDamageMult, replacesAimed: false, refund: true, pierce: true };
  if (st.phase === 'strain') {
    const mult = 1 - (1 - def.strainMinMult) * st.strain;
    return { power: 'strained', damageMult: mult, replacesAimed: false, refund: false, pierce: true };
  }
  return { power: 'full', damageMult: 1, replacesAimed: false, refund: false, pierce: true };
}

/** 몸 시트 열 고르기: 진행 프레임(min(5, floor(p × 5))) → 유지 반복 → 흔들림 반복 */
export function drawFrame(
  st: DrawState,
  sheet: {
    progressFrames?: number[];
    holdLoop?: [number, number];
    strainLoop?: [number, number];
    frameDurationsMs?: number[];
  },
): number {
  const prog = sheet.progressFrames ?? [0, 1, 2, 3, 4, 5];
  if (st.phase === 'drawing') return prog[Math.min(prog.length - 1, Math.floor(st.progress * (prog.length - 1)))] ?? 0;
  const loop = st.phase === 'strain' ? sheet.strainLoop : sheet.holdLoop;
  if (!loop) return prog[prog.length - 1] ?? 0;
  const [a, b] = loop;
  const dur = sheet.frameDurationsMs ?? [];
  const cols: number[] = [];
  for (let c = a; c <= b; c++) cols.push(c);
  const total = cols.reduce((s, c) => s + (dur[c] ?? 90), 0);
  let t = (st.phase === 'strain' ? st.sinceFullMs : Math.max(0, st.sinceFullMs)) % Math.max(1, total);
  for (const c of cols) {
    const d = dur[c] ?? 90;
    if (t < d) return c;
    t -= d;
  }
  return b;
}

/** 조준 흔들림 각(라디안) — 흔들림 정도 × 최대 각, 두 사인 합(결정적, 시간 ms) */
export function strainShakeRad(def: BowDrawDef, strain: number, timeMs: number): number {
  if (strain <= 0) return 0;
  const amp = ((def.strainShakeDeg * Math.PI) / 180) * strain;
  return amp * (0.6 * Math.sin(timeMs * 0.021) + 0.4 * Math.sin(timeMs * 0.047 + 1.3));
}
