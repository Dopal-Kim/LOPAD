/**
 * 61라운드 플레이 점검 #11: 가운데 위 성과 도장 카드와 보상 메뉴가 함께 뜨지 않게 차례를 맞춘다 (UI 씬끼리 공유하는 작은 상태).
 * - 카드가 떠 있는 동안 메뉴가 열리면: 메뉴는 카드가 끝날 때까지(최대 `MENU_WAIT_MAX_MS`) 기다리고, 카드는 그 시각에 맞춰 일찍 사라진다.
 * - 메뉴가 떠 있는 동안 등급이 오면: 카드는 메뉴가 닫힌 뒤에 뜬다 (BuildLayer → GradeCard 대기열).
 * 시각은 `performance.now()` (씬 시계는 씬마다 다르다).
 */
export const MENU_WAIT_MAX_MS = 1200;

let cardEnd = 0;
let shorten: ((ms: number) => void) | null = null;

function now(): number {
  return typeof performance !== 'undefined' ? performance.now() : Date.now();
}

/** 카드가 떴다: 사라지는 시각(지금부터 ms)과, 메뉴가 기다릴 때 카드를 줄이는 함수 */
export function gradeCardShown(leftMs: number, shortenTo: (ms: number) => void): void {
  cardEnd = now() + Math.max(0, leftMs);
  shorten = shortenTo;
}

/** 카드가 사라졌다 (치움) */
export function gradeCardGone(): void {
  cardEnd = 0;
  shorten = null;
}

/** 메뉴가 열리려 한다: 기다릴 ms (카드가 없으면 0). 기다리면 카드도 그때까지로 줄인다 */
export function menuWaitMs(): number {
  const left = cardEnd - now();
  if (left <= 0) return 0;
  const wait = Math.min(left, MENU_WAIT_MAX_MS);
  shorten?.(wait);
  cardEnd = now() + wait;
  return Math.round(wait);
}
