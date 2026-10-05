/**
 * 61라운드 E 아트 2 보스 그림 연결의 순수 규칙 (Phaser 의존 없음 — 테스트용으로 모음):
 * 기둥 균열 단계 · 파훼 고리 머리 꼭대기 표 조회 · 림 시트 VRAM 예산.
 */

/** 다음 균열 단과 재생할 상태 이름 (단은 maxStage 에서 멈춘다 — 그 뒤로는 `crack<max>_hit`) */
export function nextCrack(stage: number, maxStage: number): { stage: number; state: string } {
  if (stage >= maxStage) return { stage: maxStage, state: `crack${maxStage}_hit` };
  const n = stage + 1;
  return { stage: n, state: `crack${n}` };
}

type HeadTable = Record<string, Record<string, ([number, number] | null)[]>>;

/** 머리 꼭대기 (보스 시트 도트) — 동작·방향·열 → 없으면 idle 같은 방향 0 열 → 없으면 null */
export function headTopDot(table: unknown, action: string, dir: string, col: number): [number, number] | null {
  const t = table as HeadTable | null | undefined;
  if (!t || typeof t !== 'object') return null;
  const at = t[action]?.[dir]?.[col];
  if (Array.isArray(at)) return at;
  const idle = t.idle?.[dir]?.[0];
  return Array.isArray(idle) ? idle : null;
}

/** 림 시트를 올려도 예산 안인가 (MB) */
export function rimFits(currentMb: number, rimMb: number, budgetMb: number): boolean {
  return currentMb + rimMb <= budgetMb;
}
