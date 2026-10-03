/**
 * 54라운드 Q23·Q28 보스 불길 오버레이 선택 (Phaser 없음 — 단위 테스트용).
 * 아트 `fx/v3/boss1_onfire_down` JSON 의 `useFor`(누운 불길을 쓰는 보스 동작·프레임 열) · `frameOffsets`(그 프레임에서
 * 오버레이를 옮길 [dx, dy] 도트)를 읽어, 지금 보스 그림(동작·열)에 서 있는 불길(boss1_onfire, 보스 방향 행) · 누운 불길(0행) ·
 * 숨김 중 하나를 고른다. 두 시트는 열 배치·프레임 시간이 같아 바꿔 낄 때 국면·열을 그대로 이어 쓴다(bossBurn).
 * - 누운 시트가 있으면: useFor 에 있는 열 = 누운 불길, 나머지(standFor 포함 · 그 밖의 동작) = 서 있는 불길.
 *   useFor 가 없으면 누운 동작(LYING_ACTIONS) 전체를 누운 불길로.
 * - 누운 시트가 없으면: 누운 동작(fall·death) 동안 숨김 (54라운드 2차 동작 그대로).
 */

/** 누운 그림이 있는 보스 동작 */
export const LYING_ACTIONS = ['fall', 'death'] as const;

export interface LyingMap {
  useFor?: Record<string, readonly number[]>;
  frameOffsets?: Record<string, Record<string, readonly number[]>>;
}

export type OverlayChoice =
  | { sheet: 'stand' }
  | { sheet: 'hide' }
  /** dx·dy = 시트 도트 */
  | { sheet: 'lying'; dx: number; dy: number };

const isLyingAction = (a: string | null): boolean => a !== null && (LYING_ACTIONS as readonly string[]).includes(a);

/** 그 보스 프레임에서 누운 불길을 옮길 [dx, dy] 도트 (없으면 0, 0) */
export function lyingOffset(map: LyingMap, action: string, column: number): { dx: number; dy: number } {
  const o = map.frameOffsets?.[action]?.[String(column)];
  const n = (v: unknown) => (typeof v === 'number' && Number.isFinite(v) ? v : 0);
  return Array.isArray(o) ? { dx: n(o[0]), dy: n(o[1]) } : { dx: 0, dy: 0 };
}

/**
 * 지금 보스 그림(action = 보스 시트 동작, 모르면 null · column = 그 시트의 열)에 쓸 불길.
 * lying = 누운 불길 시트 JSON (로드되지 않았으면 null)
 */
export function chooseOverlay(action: string | null, column: number, lying: LyingMap | null): OverlayChoice {
  if (!lying) return isLyingAction(action) ? { sheet: 'hide' } : { sheet: 'stand' };
  if (action === null) return { sheet: 'stand' };
  const cols = lying.useFor?.[action];
  const use = lying.useFor ? Array.isArray(cols) && cols.includes(column) : isLyingAction(action);
  return use ? { sheet: 'lying', ...lyingOffset(lying, action, column) } : { sheet: 'stand' };
}

/** 오버레이 판단에 볼 보스 동작 이름 (useFor·standFor 키 + 누운 동작) */
export function mappedActions(lying: (LyingMap & { standFor?: Record<string, unknown> }) | null): string[] {
  const out = new Set<string>(LYING_ACTIONS);
  for (const k of Object.keys(lying?.useFor ?? {})) out.add(k);
  for (const k of Object.keys(lying?.standFor ?? {})) out.add(k);
  return [...out];
}
