/** 시트 방향 (4방향·대각·8방향)과 벡터 → 방향 변환 (57라운드 B7: spriteDefs 에서 분리). Phaser 의존 없음. */

export type Facing = 'down' | 'up' | 'left' | 'right';

export const FACINGS: readonly Facing[] = ['down', 'up', 'left', 'right'];

/**
 * 56라운드 Q6 대각 4방향 (아트 `directionRows`·`dirTransform: drawn8` 시트의 행 이름 — 기존 4행 뒤에 down-right, down-left, up-right, up-left).
 * 이동·대기 그림은 4방향 그대로, 8행 시트(대검 연격·차지·꽂아내리기·이펙트)만 조준각 8분할로 행을 고른다
 */
export type Diagonal = 'down-right' | 'down-left' | 'up-right' | 'up-left';

export const DIAGONALS: readonly Diagonal[] = ['down-right', 'down-left', 'up-right', 'up-left'];

/** 시트 행 방향 (4방향 + 대각) */
export type Dir8 = Facing | Diagonal;

export const DIRS8: readonly Dir8[] = [...FACINGS, ...DIAGONALS];

/** 지배 축으로 4방향 결정. 0 벡터면 fallback */
export function facingOf(dx: number, dy: number, fallback: Facing): Facing {
  if (dx === 0 && dy === 0) return fallback;
  if (Math.abs(dx) >= Math.abs(dy)) return dx > 0 ? 'right' : 'left';
  return dy > 0 ? 'down' : 'up';
}

/**
 * 56라운드 Q6: 조준각 8분할 (아트 directionNote: −22.5°~22.5° = right, 시계 방향으로 down-right, down, …). 0 벡터면 fallback
 */
export function facing8Of(dx: number, dy: number, fallback: Dir8): Dir8 {
  if (dx === 0 && dy === 0) return fallback;
  const deg = (Math.atan2(dy, dx) * 180) / Math.PI;
  const sector = ((Math.round(deg / 45) % 8) + 8) % 8;
  return (['right', 'down-right', 'down', 'down-left', 'left', 'up-left', 'up', 'up-right'] as const)[sector];
}

/** 대각 → 가로 성분 4방향 (대각 행이 없는 시트의 대체 행) · 4방향은 그대로 */
export function cardinalOf(dir: Dir8): Facing {
  if (dir === 'down-right' || dir === 'up-right') return 'right';
  if (dir === 'down-left' || dir === 'up-left') return 'left';
  return dir;
}
