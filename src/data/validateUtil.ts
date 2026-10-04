/**
 * 데이터 검증·읽기 공용 도우미 (57라운드 B4: validate*·border·ashParticleMath 의 중복 통합).
 * - 검증형(`num`·`str`·`nums`)은 조건이 맞지 않으면 `[data] <경로> …` 오류를 던진다.
 * - 읽기형(`numOr`·`nonEmptyStr`)은 잘못된 값이면 대체값을 돌려준다.
 */

export function num(v: unknown, path: string): void {
  if (typeof v !== 'number' || !Number.isFinite(v))
    throw new Error(`[data] ${path} 는 숫자여야 합니다 (받은 값: ${String(v)})`);
}

export function str(v: unknown, path: string): void {
  if (typeof v !== 'string' || !v) throw new Error(`[data] ${path} 는 문자열이어야 합니다`);
}

export function nums(o: object, keys: readonly string[], path: string): void {
  for (const k of keys) num((o as Record<string, unknown>)[k], `${path}.${k}`);
}

/** 유한한 숫자면 그대로, 아니면 fallback */
export function numOr(v: unknown, fallback: number): number {
  return typeof v === 'number' && Number.isFinite(v) ? v : fallback;
}

/** 비어 있지 않은 문자열이면 그대로, 아니면 null */
export function nonEmptyStr(v: unknown): string | null {
  return typeof v === 'string' && v.length > 0 ? v : null;
}
