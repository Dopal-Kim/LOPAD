/**
 * 56라운드 순수 계산 (Phaser 없이 테스트한다). 계약 `ui-system-interface.md` §13 (승인 #20).
 * - 무기 고유 자원 `UiSnapshot.gauge` → 눈금 칸 채움 (검기·울분 3칸, 낙인 0~5 획, 숨 0~3 방울)
 * - 그로기 `UiSnapshot.groggy` → 남은 시간 비율·초 문구·무기 줄 떨림
 * 시스템이 필드를 아직 채우지 않은 빌드에서도 깨지지 않게 모양을 확인한다.
 */
import type { UiGroggy, UiWeaponGauge, UiWeaponGaugeKind } from '../contract/ui';
import { clamp01 } from './resourceView';

const KINDS: ReadonlySet<string> = new Set<UiWeaponGaugeKind>(['kenki', 'grudge', 'brand', 'breath']);

/** 단계형(검기·울분) 칸 수 — 계약 §13 '0~3' */
export const STEP_CELLS = 3;
/** 낙인·숨 칸 수 상한 (max 가 이상하게 커도 줄이 넘치지 않게) */
export const MAX_CELLS = 8;

export interface GaugeView {
  kind: UiWeaponGaugeKind;
  label: string;
  /** 칸마다 채움 0..1 (왼쪽부터) */
  cells: number[];
  /** 0..3 단계 (울분은 색 구간, 검기는 찬 단 수). 단계가 없는 종류는 0 */
  stage: number;
  /** 가득 (검기 3단·울분 100%·낙인 최대·숨 최대) */
  full: boolean;
  /** 숨 감속 정밀 조준 중 */
  focusing: boolean;
}

function num(v: unknown, d = 0): number {
  return typeof v === 'number' && Number.isFinite(v) ? v : d;
}

/** 연속 단위 u 를 n 칸에 나눠 채움 (칸 k = clamp(u - k)) */
export function spreadCells(units: number, n: number): number[] {
  const out: number[] = [];
  for (let k = 0; k < n; k++) out.push(clamp01(units - k));
  return out;
}

/** 칸 수: max 의 정수 (없거나 0 이하면 기본값), 상한 MAX_CELLS */
function cellCount(max: number, fallback: number): number {
  const m = Math.floor(max);
  return Math.max(1, Math.min(MAX_CELLS, m > 0 ? m : fallback));
}

/**
 * 고유 자원 → 눈금 표시.
 * - kenki 검기: 3칸. `stage` = 찬 단 수(0~3), 다음 칸은 비율의 나머지만큼 부분 채움. 비율이 단계와 어긋나면 단계를 믿는다
 * - grudge 울분: 3칸 이어진 막대(비율 그대로 연속), `stage` 는 색 구간(1~33/34~66/67~100%). 없으면 비율로 셈
 * - brand 낙인: max(기본 5)칸, 정수 스택만 (부분 없음)
 * - breath 숨: max(기본 3)칸, 소수면 다음 칸 부분 채움
 */
export function gaugeView(g: UiWeaponGauge | null | undefined): GaugeView | null {
  if (!g || typeof g !== 'object' || !KINDS.has(g.kind)) return null;
  const value = Math.max(0, num(g.value));
  const max = num(g.max);
  const ratio = max > 0 ? clamp01(value / max) : 0;
  const label = typeof g.label === 'string' ? g.label.trim() : '';
  const focusing = g.kind === 'breath' && g.focusing === true;
  const hasStage = typeof g.stage === 'number' && Number.isFinite(g.stage);
  let cells: number[];
  let stage = 0;
  if (g.kind === 'kenki') {
    let u = ratio * STEP_CELLS;
    if (hasStage) {
      stage = Math.max(0, Math.min(STEP_CELLS, Math.floor(num(g.stage))));
      if (!(u >= stage && u < stage + 1)) u = stage;
    } else stage = Math.floor(u + 1e-9);
    cells = spreadCells(u, STEP_CELLS);
  } else if (g.kind === 'grudge') {
    cells = spreadCells(ratio * STEP_CELLS, STEP_CELLS);
    stage = hasStage
      ? Math.max(0, Math.min(STEP_CELLS, Math.floor(num(g.stage))))
      : ratio <= 0
        ? 0
        : Math.min(STEP_CELLS, Math.ceil(ratio * STEP_CELLS - 1e-9));
  } else if (g.kind === 'brand') {
    const n = cellCount(max, 5);
    cells = spreadCells(Math.min(n, Math.floor(value + 1e-9)), n);
  } else {
    const n = cellCount(max, 3);
    cells = spreadCells(Math.min(n, value), n);
  }
  const full = cells.length > 0 && cells.every((c) => c >= 1);
  return { kind: g.kind, label, cells, stage, full, focusing };
}

/** 같은 표시인지 (다시 그릴지 판단). 부분 채움은 1/16 단위로 묶는다 */
export function gaugeKey(v: GaugeView | null): string {
  if (!v) return '';
  return [v.kind, v.label, v.stage, v.focusing ? 1 : 0, v.cells.map((c) => Math.round(c * 16)).join(',')].join('|');
}

/** 부분 채움을 칸 높이(또는 폭) px 로: 0 < f < 1 이면 최소 1px, 가득 직전이면 size-1 까지 */
export function partialPx(size: number, f: number): number {
  const c = clamp01(f);
  if (c <= 0) return 0;
  if (c >= 1) return size;
  return Math.max(1, Math.min(size - 1, Math.round(size * c)));
}

/**
 * 눈금 모양(문자열 행, '.' 빈칸) 의 테두리 칸: 모양 안이면서 상하좌우 중 하나가 모양 밖(또는 가장자리)인 칸.
 * 꺼진 칸은 테두리 G06 · 안쪽 G03 으로 그린다 (열기 단계 눈금과 같은 문체)
 */
export function maskEdges(mask: readonly string[]): boolean[][] {
  const h = mask.length;
  const inside = (x: number, y: number): boolean =>
    y >= 0 && y < h && x >= 0 && x < mask[y].length && mask[y][x] !== '.';
  return mask.map((row, y) =>
    [...row].map(
      (_, x) => inside(x, y) && (!inside(x - 1, y) || !inside(x + 1, y) || !inside(x, y - 1) || !inside(x, y + 1)),
    ),
  );
}

// ---------------------------------------------------------------------------------------------
export interface GroggyView {
  leftMs: number;
  /** 남은 비율 1 → 0 */
  ratio: number;
  /** 남은 초 (0.1 단위 올림, 예 '1.2') */
  seconds: string;
}

/** 남은 ms → '1.2' (0.1초 단위 올림, 0 이하 '0.0') */
export function groggySeconds(ms: number): string {
  const v = num(ms);
  if (v <= 0) return '0.0';
  return (Math.ceil(v / 100 - 1e-9) / 10).toFixed(1);
}

/**
 * 그로기 표시. 활성이 아니면 null. 전체 시간은 계약에 없어 `totalMs`(그로기가 시작될 때 본 가장 큰 leftMs, 없으면 기본 1.5초)로 나눈다.
 */
export function groggyView(g: UiGroggy | null | undefined, totalMs: number): GroggyView | null {
  if (!g || typeof g !== 'object' || g.active !== true) return null;
  const leftMs = Math.max(0, num(g.leftMs));
  const total = Math.max(leftMs, num(totalMs), 1);
  return { leftMs, ratio: clamp01(leftMs / total), seconds: groggySeconds(leftMs) };
}

/** 그로기 중 무기 줄 떨림: 정수 px 계단 [0, 1, 0, -1] 을 stepMs 마다 */
export function groggyShake(now: number, stepMs: number, amp = 1): number {
  const seq = [0, amp, 0, -amp];
  const i = Math.floor(Math.max(0, num(now)) / Math.max(1, stepMs)) % seq.length;
  return seq[i];
}
