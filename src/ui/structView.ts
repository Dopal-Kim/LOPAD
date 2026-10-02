/**
 * 47라운드 상호작용 구조물 UI 의 순수 계산 (Phaser 없이 테스트한다).
 * 계약 `ui-system-interface.md` §9.
 */

/** 조작법 템플릿에 빠진 키 안내를 ' · ' 로 덧붙인다 (토큰이 이미 있으면 그대로) */
export function withControlExtras(line: string, extras: { token: RegExp; text: string }[]): string {
  const add = extras.filter((e) => !e.token.test(line)).map((e) => e.text);
  return add.length ? `${line} · ${add.join(' · ')}` : line;
}

/**
 * 말풍선 위치: 기준점(구조물 윗변 중앙) 위로 `gap` 띄운 가운데 정렬, 화면 안(`margin`)으로 자른다. 정수.
 * 위로 넘치면 위 여백에 붙인다.
 */
export function bubblePos(
  anchor: { x: number; y: number },
  w: number,
  h: number,
  screenW: number,
  screenH: number,
  margin: number,
  gap: number,
): { x: number; y: number } {
  const x = Math.round(Math.min(Math.max(anchor.x - w / 2, margin), screenW - margin - w));
  const y = Math.round(Math.min(Math.max(anchor.y - gap - h, margin), screenH - margin - h));
  return { x, y };
}

/** 남은 시간 비율 0..1. 타이머가 없으면 null */
export function timerRatio(s: { remainMs?: number; durationMs?: number }): number | null {
  if (s.remainMs === undefined || !s.durationMs || s.durationMs <= 0) return null;
  return Math.max(0, Math.min(1, s.remainMs / s.durationMs));
}

/** 초 표시 (소수 1자리, 음수는 0) */
export function formatSec(ms: number): string {
  return (Math.max(0, ms) / 1000).toFixed(1);
}

/** 길게 누르기 초 표시 (정수면 정수, 아니면 소수 1자리) */
export function holdSec(ms: number): string {
  const s = Math.max(0, ms) / 1000;
  return Number.isInteger(s) ? String(s) : s.toFixed(1);
}

/** 카드 메뉴 키보드 이동: 카드 n 장 + 그만두기 1 칸. idx 0..n-1 = 카드, n = 그만두기 */
export function cardFocusMove(idx: number, n: number, key: string): number {
  if (n <= 0) return idx;
  const left = key === 'ArrowLeft' || key === 'a' || key === 'A';
  const right = key === 'ArrowRight' || key === 'd' || key === 'D';
  const down = key === 'ArrowDown' || key === 's' || key === 'S';
  const up = key === 'ArrowUp' || key === 'w' || key === 'W';
  if (idx >= n) {
    if (up || left || right) return Math.min(n - 1, Math.floor(n / 2));
    return idx;
  }
  if (left) return (idx - 1 + n) % n;
  if (right) return (idx + 1) % n;
  if (down) return n;
  return idx;
}
