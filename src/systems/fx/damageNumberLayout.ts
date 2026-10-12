/**
 * 61라운드 플레이 점검: 피해 숫자 겹침 정리 (순수 — Phaser 의존 없음, damageNumbers 가 쓴다).
 * - 합치기: 같은 무리(일반·치명 / 틱 / 주인공 피격)가 같은 자리(반경)에 짧은 간격으로 오면 앞 숫자에 더한다(치명이 섞이면 치명 표시).
 * - 비켜 띄우기: 합칠 수 없으면 근처에 떠 있는 숫자 수 n 만큼 위로 n × STEP, 좌우로 번갈아 SPREAD 씩.
 */
/** 62라운드 P1-1: heavy = 막타(연격 마지막 타·대쉬 공격·데이터 heavy) — 일반·치명과 같은 무리로 합쳐진다 */
export type NumberKind = 'hit' | 'heavy' | 'crit' | 'tick' | 'player';

export interface PlacedNumber {
  id: number;
  /** 처음 띄운 원점 (적중점) */
  ox: number;
  oy: number;
  /** 마지막으로 띄운(또는 합친) 시각 */
  at: number;
  kind: NumberKind;
  amount: number;
}

export interface StackConfig {
  RADIUS_PX: number;
  MERGE_MS: number;
  STEP_PX: number;
  SPREAD_X: number;
  MAX_STEPS: number;
}

export function groupOfKind(k: NumberKind): 'strike' | 'tick' | 'player' {
  return k === 'hit' || k === 'heavy' || k === 'crit' ? 'strike' : k;
}

export type Placement =
  { merge: true; id: number; amount: number; kind: NumberKind } | { merge: false; dx: number; dy: number };

export function placeNumber(
  active: readonly PlacedNumber[],
  incoming: { x: number; y: number; kind: NumberKind; amount: number; now: number },
  cfg: StackConfig,
  liveMs: number,
): Placement {
  const near = active.filter(
    (a) => Math.abs(a.ox - incoming.x) <= cfg.RADIUS_PX && Math.abs(a.oy - incoming.y) <= cfg.RADIUS_PX,
  );
  const g = groupOfKind(incoming.kind);
  const mergeable = near
    .filter((a) => groupOfKind(a.kind) === g && incoming.now - a.at <= cfg.MERGE_MS)
    .sort((a, b) => b.at - a.at)[0];
  if (mergeable) {
    const kind: NumberKind = strongerKind(incoming.kind, mergeable.kind);
    return { merge: true, id: mergeable.id, amount: mergeable.amount + incoming.amount, kind };
  }
  const n = Math.min(cfg.MAX_STEPS, near.filter((a) => incoming.now - a.at < liveMs).length);
  if (n === 0) return { merge: false, dx: 0, dy: 0 };
  const side = n % 2 === 1 ? 1 : -1;
  return { merge: false, dx: side * cfg.SPREAD_X * Math.ceil(n / 2), dy: -n * cfg.STEP_PX };
}

/** 합친 숫자의 등급: 치명 > 막타 > 그 밖 (들어온 것) */
export function strongerKind(a: NumberKind, b: NumberKind): NumberKind {
  if (a === 'crit' || b === 'crit') return 'crit';
  if (a === 'heavy' || b === 'heavy') return 'heavy';
  return a;
}

/** 숫자 문자열 (주인공 피격 '-n', 치명 'n!') */
export function numberLabel(kind: NumberKind, amount: number): string {
  return kind === 'player' ? `-${amount}` : kind === 'crit' ? `${amount}!` : `${amount}`;
}
