/**
 * 61라운드 메뉴 차례 — 가운데 연출(성과 도장 카드·보스 처치 카드)과 보상 메뉴가 함께 뜨지 않게 맞춘다 (UI 씬끼리 공유하는 작은 상태).
 * - 연출이 떠 있는 동안 메뉴가 열리면: 메뉴는 연출이 끝날 때까지(연출마다 상한) 기다린다. 줄일 수 있는 연출(도장 카드)은 그 시각에 맞춰 일찍 사라진다.
 * - 메뉴가 떠 있는 동안 등급이 오면: 카드는 메뉴가 닫힌 뒤에 뜬다 (BuildLayer → GradeCard 대기열).
 * - 61 단계 3 보스 처치(P6·플레이 점검 #5): 처치 카드가 끝나기 전 메뉴는 기다린다. 처치 뒤 대사·한마디가 이어지면 늘이되
 *   처치 시점에서 `deadline` 까지. 시스템이 메뉴를 늦게 열면(연출 뒤) 기다림은 0 이다 — 시스템 이벤트 순서를 그대로 따른다.
 * 시각은 `performance.now()` (씬 시계는 씬마다 다르다).
 */
export const MENU_WAIT_MAX_MS = 1200;

interface Blocker {
  end: number;
  /** 메뉴가 기다릴 최대 ms */
  maxWait: number;
  /** 이 시각 뒤로는 늘이지 않는다 */
  deadline: number;
  /** 메뉴가 기다릴 때 연출을 그 시각까지로 줄인다 (없으면 줄이지 않는다) */
  shorten: ((ms: number) => void) | null;
}

const blockers = new Map<string, Blocker>();

let clock: () => number = () => (typeof performance !== 'undefined' ? performance.now() : Date.now());

/** @internal 테스트용 시계 */
export function setSequenceClock(fn: (() => number) | null): void {
  clock = fn ?? (() => (typeof performance !== 'undefined' ? performance.now() : Date.now()));
  blockers.clear();
}

/** 연출이 떴다: 지금부터 leftMs 동안 메뉴를 막는다 */
export function sequenceShown(
  tag: string,
  leftMs: number,
  opts: { maxWaitMs?: number; deadlineMs?: number; shorten?: (ms: number) => void } = {},
): void {
  const now = clock();
  const deadline = now + Math.max(0, opts.deadlineMs ?? Infinity);
  blockers.set(tag, {
    end: Math.min(deadline, now + Math.max(0, leftMs)),
    maxWait: opts.maxWaitMs ?? Infinity,
    deadline,
    shorten: opts.shorten ?? null,
  });
}

/** 떠 있는 연출을 늘인다 (지금부터 leftMs, 처음 정한 deadline 안). 없으면 무시 */
export function sequenceExtend(tag: string, leftMs: number): void {
  const b = blockers.get(tag);
  if (!b) return;
  b.end = Math.min(b.deadline, Math.max(b.end, clock() + Math.max(0, leftMs)));
}

/** 연출이 사라졌다 */
export function sequenceGone(tag: string): void {
  blockers.delete(tag);
}

/** 그 연출이 아직 메뉴를 막는가 */
export function sequenceActive(tag: string): boolean {
  const b = blockers.get(tag);
  return Boolean(b && b.end > clock());
}

/** 메뉴가 열리려 한다: 기다릴 ms (막는 연출이 없으면 0). 줄일 수 있는 연출은 그때까지로 줄인다 */
export function menuWaitMs(): number {
  const now = clock();
  let wait = 0;
  for (const [tag, b] of blockers) {
    const left = b.end - now;
    if (left <= 0) {
      if (now >= b.deadline) blockers.delete(tag);
      continue;
    }
    const w = Math.min(left, b.maxWait);
    if (b.shorten) {
      b.shorten(w);
      b.end = now + w;
    }
    wait = Math.max(wait, w);
  }
  return Math.round(wait);
}

// ---- 61라운드 플레이 점검 #11 성과 도장 카드 (기존 이름 유지)
const GRADE = 'grade';

/** 카드가 떴다: 사라지는 시각(지금부터 ms)과, 메뉴가 기다릴 때 카드를 줄이는 함수 */
export function gradeCardShown(leftMs: number, shortenTo: (ms: number) => void): void {
  sequenceShown(GRADE, leftMs, { maxWaitMs: MENU_WAIT_MAX_MS, shorten: shortenTo });
}

/** 카드가 사라졌다 (치움) */
export function gradeCardGone(): void {
  sequenceGone(GRADE);
}
