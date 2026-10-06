/**
 * 61라운드 E 아트 2 보스 그림 연결의 순수 규칙 (Phaser 의존 없음 — 테스트용으로 모음):
 * 기둥 균열 단계 · 파훼 고리 머리 꼭대기 표 조회 · 림 시트 VRAM 예산.
 */

/**
 * 다음 균열 단과 재생할 상태 이름. 61 단계 5 (P13 §3): maxStage 다음 충돌은 무너짐(단 = maxStage + 1, state `collapse`).
 * 이미 무너졌으면 null (잔해 — 더 부딪힐 것이 없다)
 */
export function nextCrack(stage: number, maxStage: number): { stage: number; state: string; collapse: boolean } | null {
  if (stage > maxStage) return null;
  if (stage === maxStage) return { stage: maxStage + 1, state: 'collapse', collapse: true };
  const n = stage + 1;
  return { stage: n, state: `crack${n}`, collapse: false };
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

/** 61 단계 4: 소등 때 올릴 림 — 원 림이 예산 안이면 full, 아니면 가벼운 림(lite), 그것도 넘으면 null(tintFill 대체) */
export function pickRim(currentMb: number, fullMb: number, liteMb: number, budgetMb: number): 'full' | 'lite' | null {
  if (rimFits(currentMb, fullMb, budgetMb)) return 'full';
  if (rimFits(currentMb, liteMb, budgetMb)) return 'lite';
  return null;
}
