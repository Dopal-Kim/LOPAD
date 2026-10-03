/**
 * 회피 시험 과제 박자·기하 (Phaser 의존 없음, 51라운드 2절).
 * 과제의 위협은 `DODGE_TRIAL.TASKS[id].cues` 표대로만 나온다(정해진 박자, 무작위는 방향·틈 위치뿐) → "읽으면 피할 수 있게".
 * 여기에는 박자 → 예고 시간·끝 시각 계산, 고리(조여옴·틈 판정), 유도탄 회전, 벽 위치 계산을 둔다.
 */
import { DODGE_TRIAL, type Cue, type TaskId, type TrialConfig } from './dodgeTrial';

export function taskCues(id: TaskId, C: TrialConfig = DODGE_TRIAL): Cue[] {
  return [...C.TASKS[id].cues].sort((a, b) => a.at - b.at);
}

/** ① 예고선 예고 시간: 과제 안에서 처음 → 끝으로 짧아진다 */
export function lineTelegraphMs(at: number, id: TaskId, C: TrialConfig = DODGE_TRIAL): number {
  const cues = taskCues(id, C);
  const last = cues[cues.length - 1]?.at ?? 0;
  const k = last > 0 ? Math.max(0, Math.min(1, at / last)) : 0;
  const [a, b] = C.LINES.TELEGRAPH_MS;
  return a + (b - a) * k;
}

/** 기준 경기장 반지름으로 어림한 벽 횡단 시간 (실제는 경기장 크기에 따라 조금 다르다) */
export function wallCrossMs(C: TrialConfig = DODGE_TRIAL): number {
  const R = C.ARENA.RADIUS_TILES * 16 * 1.25;
  return ((2 * R + 2 * C.WALL.PAD_PX) / (C.WALL.SPEED_TILES * 16)) * 1000;
}

/** 위협이 실제로 쏘이는(예고가 끝나는) 시각 */
export function cueFireMs(cue: Cue, id: TaskId, C: TrialConfig = DODGE_TRIAL): number {
  switch (cue.kind) {
    case 'line':
      return cue.at + lineTelegraphMs(cue.at, id, C);
    case 'ring':
      return cue.at + C.RING.WARN_MS;
    case 'homing':
      return cue.at + C.HOMING.TELEGRAPH_MS;
    case 'wall':
      return cue.at + C.WALL.WARN_MS;
  }
}

/** 위협이 끝나는 어림 시각 (진행 호·과제 길이용) */
export function cueEndMs(cue: Cue, id: TaskId, C: TrialConfig = DODGE_TRIAL): number {
  const fire = cueFireMs(cue, id, C);
  switch (cue.kind) {
    case 'line': {
      const travel = ((C.ARENA.RADIUS_TILES * 16 * 2.4) / (C.LINES.SPEED_TILES * 16)) * 1000;
      return fire + (C.LINES.BURST - 1) * C.LINES.BURST_GAP_MS + travel * 0.6;
    }
    case 'ring':
      return fire + cue.closeMs;
    case 'homing':
      return fire + C.HOMING.CHASE_EST_MS;
    case 'wall':
      return fire + wallCrossMs(C);
  }
}

/** 과제 길이 어림 (마지막 위협이 끝나는 시각) */
export function taskDurationMs(id: TaskId, C: TrialConfig = DODGE_TRIAL): number {
  return Math.max(0, ...taskCues(id, C).map((c) => cueEndMs(c, id, C)));
}

// --- ② 고리 ---

/** 예고 시작부터 t ms 뒤 고리 반지름 (예고 동안 R0, 이후 closeMs 동안 0 까지) */
export function ringRadius(t: number, closeMs: number, R0: number, C: TrialConfig = DODGE_TRIAL): number {
  const k = (t - C.RING.WARN_MS) / Math.max(1, closeMs);
  return R0 * (1 - Math.max(0, Math.min(1, k)));
}

/** 각도 차 (-π, π] */
export function angleDiff(a: number, b: number): number {
  let d = (a - b) % (Math.PI * 2);
  if (d > Math.PI) d -= Math.PI * 2;
  if (d <= -Math.PI) d += Math.PI * 2;
  return d;
}

/**
 * 고리 판정: 고리 중심(cx, cy)·반지름 R·틈 방향 gapAngle·틈 폭 gapDeg. 주인공 판정 원(px, py, hitR) 이 고리 띠
 * (± hitR + beadR) 에 걸리고, 몸 전체가 틈 안에 들어가 있지 않으면 맞는다. 중심 가까이(고리가 다 조여 듦)는 어디든 맞는다.
 */
export function ringHits(
  cx: number,
  cy: number,
  R: number,
  gapAngle: number,
  gapDeg: number,
  px: number,
  py: number,
  hitR: number,
  beadR: number,
): boolean {
  const d = Math.hypot(px - cx, py - cy);
  if (Math.abs(d - R) > hitR + beadR) return false;
  if (d < 1e-3) return true;
  const half = (gapDeg * Math.PI) / 360;
  const body = Math.asin(Math.min(1, hitR / d));
  return Math.abs(angleDiff(Math.atan2(py - cy, px - cx), gapAngle)) + body > half;
}

/** 고리 구슬 각도 (틈 제외, R0 에서 간격 spacing) — 조여 들면서 촘촘해진다 */
export function ringBeadAngles(R0: number, gapAngle: number, gapDeg: number, spacing: number): number[] {
  const n = Math.max(8, Math.round((Math.PI * 2 * R0) / spacing));
  const half = (gapDeg * Math.PI) / 360;
  const out: number[] = [];
  for (let k = 0; k < n; k++) {
    const a = gapAngle + Math.PI / n + (k / n) * Math.PI * 2;
    if (Math.abs(angleDiff(a, gapAngle)) > half) out.push(a);
  }
  return out;
}

// --- ③ 유도탄 ---

/** 지금 방향 cur 를 목표 desired 쪽으로 최대 maxTurn(rad) 만큼 돌린다 */
export function steer(cur: number, desired: number, maxTurn: number): number {
  const d = angleDiff(desired, cur);
  return cur + Math.max(-maxTurn, Math.min(maxTurn, d));
}

// --- ④ 벽 ---

/**
 * 벽 자리: 진행 방향 angle 로 경기장 외곽 상자(bounds)를 가로지른다. from = 시작 위치(중심에서 진행 방향 반대쪽 거리, 음수),
 * to = 끝, half = 벽 반길이(진행 방향에 수직, 경기장을 다 덮게).
 */
export function wallFrame(
  b: { minX: number; maxX: number; minY: number; maxY: number },
  angle: number,
  pad: number,
): { from: number; to: number; half: number } {
  const ux = Math.cos(angle);
  const uy = Math.sin(angle);
  const corners = [
    [b.minX, b.minY],
    [b.maxX, b.minY],
    [b.minX, b.maxY],
    [b.maxX, b.maxY],
  ];
  let lo = Infinity;
  let hi = -Infinity;
  let side = 0;
  for (const [x, y] of corners) {
    const along = x * ux + y * uy;
    lo = Math.min(lo, along);
    hi = Math.max(hi, along);
    side = Math.max(side, Math.abs(-x * uy + y * ux));
  }
  return { from: lo - pad, to: hi + pad, half: side + pad };
}

/** 벽 진행 방향 8방 중 하나 — 직전 방향과 90° 이상 다르게 (같은 쪽에서 연달아 오지 않게) */
export function pickWallAngle(prev: number | null, rnd: () => number): number {
  const dirs = Array.from({ length: 8 }, (_, k) => (k * Math.PI) / 4);
  const ok = prev === null ? dirs : dirs.filter((a) => Math.abs(angleDiff(a, prev)) >= Math.PI / 2 - 1e-6);
  return ok[Math.min(ok.length - 1, Math.floor(rnd() * ok.length))];
}
