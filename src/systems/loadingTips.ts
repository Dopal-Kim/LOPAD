/**
 * 62 루프 2 시스템 D (P2-6) 로딩 화면 단서 팁 고르기 (Phaser 의존 없음 — 테스트): 같은 생 안 중복 없음 ·
 * requires `clue.<id>` 는 일기장(diary.clues)에 그 단서가 있을 때만 · 다 쓰면 처음부터 다시.
 */
export interface LoadingTip {
  kind: 'tip' | 'lore';
  text: string;
  requires?: string;
}

export function tipAllowed(t: LoadingTip, clues: readonly string[]): boolean {
  if (!t.requires) return true;
  const id = t.requires.startsWith('clue.') ? t.requires.slice(5) : t.requires;
  return clues.includes(id);
}

/** used = 이 생에 이미 보인 줄 (고른 줄을 더해 돌려준다) · r = 0..1 난수 */
export function pickTip(
  tips: readonly LoadingTip[],
  clues: readonly string[],
  used: readonly string[],
  r: number,
): { tip: LoadingTip | null; used: string[] } {
  const ok = tips.filter((t) => tipAllowed(t, clues));
  if (ok.length === 0) return { tip: null, used: [...used] };
  let pool = ok.filter((t) => !used.includes(t.text));
  let next = [...used];
  if (pool.length === 0) {
    pool = ok;
    next = [];
  }
  const tip = pool[Math.min(pool.length - 1, Math.floor(r * pool.length))];
  return { tip, used: [...next, tip.text] };
}
