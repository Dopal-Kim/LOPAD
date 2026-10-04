/** 시트 프레임 번호·시간 계산 (방향 행·프레임 길이·적중/유지 프레임·깊이 힌트, 57라운드 B7: spriteDefs 에서 분리). Phaser 의존 없음. */
import { SPRITES } from '../../core/Constants';
import {
  cardinalOf,
  type Diagonal,
  DIAGONALS,
  type Dir8,
  type Facing,
  facing8Of,
  facingOf,
  FACINGS,
} from './spriteDirs';
import type { SheetJson } from './sheetJson';

/** 프레임별 시작 시각(ms) 누적. scale 은 재생 배속 (natural / fit) */
export function frameStarts(def: SheetJson, scale = 1): number[] {
  const d = frameDurations(def);
  const out: number[] = [];
  let acc = 0;
  for (const ms of d) {
    out.push(acc / scale);
    acc += ms;
  }
  return out;
}

/**
 * 51라운드 Q3 템포: 두 구간 맞춤 — `keyFrame` 시작이 `keyAtMs` 에, 전체가 `totalMs` 에 오도록 앞 구간(예비 동작)과
 * 뒤 구간(휘두름·여운)을 따로 늘인다. 값이 맞지 않으면(구간이 비거나 범위 밖) null → 호출 쪽은 균일 맞춤
 */
export function keyedDurations(
  durations: readonly number[],
  keyFrame: number,
  keyAtMs: number,
  totalMs: number,
): number[] | null {
  if (!(keyFrame > 0 && keyFrame < durations.length) || !(keyAtMs > 0 && keyAtMs < totalMs)) return null;
  const pre = durations.slice(0, keyFrame).reduce((a, b) => a + b, 0);
  const post = durations.slice(keyFrame).reduce((a, b) => a + b, 0);
  if (pre <= 0 || post <= 0) return null;
  const a = keyAtMs / pre;
  const b = (totalMs - keyAtMs) / post;
  return durations.map((d, i) => d * (i < keyFrame ? a : b));
}

/** 프레임 길이 목록 → 프레임별 시작 ms */
export function startsOf(durations: readonly number[]): number[] {
  const out: number[] = [];
  let acc = 0;
  for (const ms of durations) {
    out.push(acc);
    acc += ms;
  }
  return out;
}

/** 발사 프레임 시작 ms: `fireFrame`(53라운드 적 v3) 시작, 없으면 첫 프레임 길이 (구 시트의 2번째 프레임 시작) */
export function fireDelayMs(def: SheetJson): number {
  const d = frameDurations(def);
  const f = def.fireFrame;
  if (typeof f === 'number' && f > 0 && f < d.length) return d.slice(0, f).reduce((a, b) => a + b, 0);
  return d[0] ?? 0;
}

/** 이 열 이후 spawn 시점에 맞출 프레임 키 (43라운드: 휘두름 시트 f0 = 40ms 예비 프레임) */
const LEAD_SPAWNS: readonly string[] = ['attack_frame2'];

/**
 * 타격 프레임 = spawn 시점에 보여야 하는 프레임 열. `impactFrame` 이 있으면 그것,
 * 없으면 `spawn: attack_frame2` 이고 2프레임 이상이면 1 (f0 예비, fx-design §4·결정 43 임시 5), 그 외 0
 */
export function fxImpactFrame(def: Pick<SheetJson, 'impactFrame' | 'spawn' | 'frames'>): number {
  if (typeof def.impactFrame === 'number') return Math.max(0, Math.min(def.frames - 1, Math.floor(def.impactFrame)));
  return def.spawn && LEAD_SPAWNS.includes(def.spawn) && def.frames >= 2 ? 1 : 0;
}

/**
 * 히트스톱 동안 멈출 프레임 = `holdFrame`(적중 스파크) → 56라운드 Q37: 붓획 시트(`brushStroke`)는 붓획이 다 그어진 다음 칸
 * (판정 백열 `glowFrames` 마지막 다음 — 백열 프레임에 멈춰 흰 막대가 보이지 않게, 55라운드 Q14 규칙 대체) → 타격 프레임(`fxImpactFrame`)
 */
export function fxHoldFrame(
  def: Pick<SheetJson, 'holdFrame' | 'impactFrame' | 'spawn' | 'frames' | 'brushStroke' | 'glowFrames' | 'frameRoles'>,
): number {
  if (typeof def.holdFrame === 'number') return Math.max(0, Math.min(def.frames - 1, Math.floor(def.holdFrame)));
  if (def.brushStroke) return strokeDoneFrame(def);
  return fxImpactFrame(def);
}

/**
 * 56라운드 Q37·Q51: 붓획이 다 그어진 다음 칸 — `frameRoles` 로 계산(시스템): 'draw(끝까지 …)' 다음 칸, 없으면 마지막
 * draw·impact 역할 다음 칸. 역할 표가 없으면 백열(glowFrames) 마지막 + 1 (없으면 타격 프레임 + 1). 마지막 프레임까지
 */
export function strokeDoneFrame(
  def: Pick<SheetJson, 'impactFrame' | 'spawn' | 'frames' | 'glowFrames' | 'frameRoles'>,
): number {
  const roles = Array.isArray(def.frameRoles) ? def.frameRoles.map((r) => (typeof r === 'string' ? r : '')) : null;
  let base: number | null = null;
  if (roles) {
    const done = roles.findIndex((r) => r.includes('끝까지'));
    if (done >= 0) base = done;
    else
      for (let i = roles.length - 1; i >= 0; i--)
        if (/^(draw|impact)/.test(roles[i])) {
          base = i;
          break;
        }
  }
  if (base === null) {
    const glow = Array.isArray(def.glowFrames) && def.glowFrames.length > 0 ? Math.max(...def.glowFrames) : null;
    base = glow ?? fxImpactFrame(def);
  }
  return Math.max(0, Math.min(def.frames - 1, base + 1));
}

/**
 * 55라운드 Q14 ①③: 휘두름 이펙트를 띄울 시각 = 몸 판정 프레임 시작(실제 재생, `hitAtMs`) − 이펙트 판정 프레임까지(`leadMs`).
 * 그러면 적중(히트스톱 시작) 순간 이펙트가 판정 백열 프레임에 있다. 몸이 그보다 빨리 치면 즉시(0)
 */
export function swingFxDelayMs(hitAtMs: number, leadMs: number): number {
  return Math.max(0, hitAtMs - Math.max(0, leadMs));
}

/**
 * 연타 판정 간격: `hitFrames` 의 각 프레임 시작 시각을 첫 타격 프레임 기준으로 뺀 값 (ms, 길이 = hits).
 * 시트·hitFrames 가 없거나 짧으면 null → 호출 쪽 기본 간격
 */
export function hitFrameOffsets(def: SheetJson | null | undefined, hits: number): number[] | null {
  const hf = def?.hitFrames;
  if (!def || !hf || hf.length < hits || hits < 1) return null;
  const starts = frameStarts(def);
  const at = (f: number) => starts[Math.max(0, Math.min(def.frames - 1, f))] ?? 0;
  const base = at(hf[0]);
  return hf.slice(0, hits).map((f) => Math.max(0, at(f) - base));
}

/** 진행도 주도 프레임: min(last, floor(progress × divisor)). 예고 원 = (6프레임, ÷6), 조준 차지 = (6프레임, ÷5) */
export function progressFrame(progress: number, frames: number, divisor = frames): number {
  const last = Math.max(0, frames - 1);
  return Math.max(0, Math.min(last, Math.floor(Math.max(0, progress) * divisor)));
}

/**
 * 49라운드 §7.1 무기 오버레이 깊이: JSON `depth` 가 문자열이면 그것, 방향별 값이 문자열이면 그것,
 * 방향별 배열이면 그 열(프레임) 값. 없으면 above (기존 §3.1 처리와 같음)
 */
export function overlayDepthAt(
  def: Pick<SheetJson, 'depth' | 'depthByFrame' | 'occlusionBaked'>,
  dir: Dir8,
  column: number,
): 'above' | 'below' {
  // 52라운드 v3: 가림을 시트에 구웠으면 늘 위, 프레임별 표가 있으면 그것 (56라운드: 대각 표가 없으면 가로 성분 방향)
  if (def.occlusionBaked) return 'above';
  const byFrame = def.depthByFrame?.[dir] ?? def.depthByFrame?.[cardinalOf(dir)];
  if (Array.isArray(byFrame) && byFrame.length > 0) {
    const c = byFrame[Math.max(0, Math.min(byFrame.length - 1, column))];
    if (c === 'above' || c === 'below') return c;
  }
  const d = def.depth;
  if (d === 'above' || d === 'below') return d;
  if (d && typeof d === 'object') {
    const v = d[dir] ?? d[cardinalOf(dir)];
    if (v === 'above' || v === 'below') return v;
    if (Array.isArray(v) && v.length > 0) {
      const c = v[Math.max(0, Math.min(v.length - 1, column))];
      if (c === 'above' || c === 'below') return c;
    }
  }
  return 'above';
}

/** 이펙트 JSON `depth` 문자열 (무기 오버레이의 방향별 표는 무시) */
export function fxDepthHint(def: Pick<SheetJson, 'depth'>): 'above' | 'below' | null {
  return def.depth === 'above' || def.depth === 'below' ? def.depth : null;
}

/** 프레임별 길이(ms). frameDurationsMs 가 없거나 길이가 다르면 fps 균등 */
export function frameDurations(def: SheetJson): number[] {
  const d = def.frameDurationsMs;
  if (d && d.length === def.frames && d.every((v) => v > 0)) return d;
  // 55라운드: 시간 애니가 아닌 시트(입자·리본: frameDurationsMs 전부 0, fps 없음)도 유한한 값으로
  const per = 1000 / (Number.isFinite(def.fps) && def.fps > 0 ? def.fps : SPRITES.STATIC_SHEET_FPS);
  return Array.from({ length: def.frames }, () => per);
}

export function animDurationMs(def: SheetJson): number {
  return frameDurations(def).reduce((a, b) => a + b, 0);
}

/**
 * 방향 행 번호 (JSON directions 순서). 56라운드: 대각 이름이 없는 4행 시트면 대각은 가로 성분(right·left) 행 — `facingOf` 의
 * 45° 동률 규칙(가로 우선)과 같다. 크기 행(`s`·`m`·`l` — 균열)처럼 방향이 아닌 행 이름도 그대로 찾는다. 없으면 0
 */
export function directionRow(def: Pick<SheetJson, 'directions'>, dir: string): number {
  const i = def.directions.indexOf(dir);
  if (i >= 0) return i;
  if ((DIAGONALS as readonly string[]).includes(dir)) {
    const j = def.directions.indexOf(cardinalOf(dir as Diagonal));
    if (j >= 0) return j;
  }
  return 0;
}

/** 방향 행의 프레임 번호 목록: row * frames + column */
export function frameIndices(def: SheetJson, dir: string): number[] {
  const row = directionRow(def, dir);
  return Array.from({ length: def.frames }, (_, c) => row * def.frames + c);
}

/** 방향별 프레임 번호의 열 → 시트 프레임 번호. 다른 시트(무기 오버레이)가 같은 열을 같은 시각에 보일 때 */
export function frameAt(def: SheetJson, dir: string, column: number): number {
  const c = Math.max(0, Math.min(def.frames - 1, column));
  return directionRow(def, dir) * def.frames + c;
}

/** 이 시트에 대각 행이 있는가 (`directions` 에 대각 이름) */
export function hasDiagonalRows(def: Pick<SheetJson, 'directions'> | null | undefined): boolean {
  return Boolean(def && def.directions.some((d) => (DIAGONALS as readonly string[]).includes(d)));
}

/**
 * 56라운드 Q6: 조준 벡터로 고르는 시트 행 방향 — 대각 행이 있는 시트(8행)는 8분할, 없으면 기존 4방향(지배 축) 그대로.
 * 4행 시트의 동작은 바뀌지 않는다
 */
export function rowDirFor(
  def: Pick<SheetJson, 'directions'> | null | undefined,
  dx: number,
  dy: number,
  fallback: Facing,
): Dir8 {
  return hasDiagonalRows(def) ? facing8Of(dx, dy, fallback) : facingOf(dx, dy, fallback);
}

/** 애니를 만들 행 이름: 4방향(4행 시트·`any` 시트는 대체 행) + 시트에 있는 다른 행 이름(대각·크기) */
export function animRowNames(def: Pick<SheetJson, 'directions'>): string[] {
  const out: string[] = [...FACINGS];
  for (const d of def.directions) if (d !== 'any' && !out.includes(d)) out.push(d);
  return out;
}
