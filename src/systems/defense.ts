/**
 * 56라운드 Q7·Q8 방어 판정 (Phaser 의존 없음): 칼 패링 · 대검 가드(퍼펙트 가드 창) · 그 밖 피격.
 * - 패링 창 안 = parried (튕겨냄 — 기존 규칙, 문구 'PARRY')
 * - 가드를 누른 직후 perfectWindowMs 안 = perfect (피해 0, 튕겨내지 않음, 문구 'PERFECT GUARD') — 56라운드 Q48 칼 가드는
 *   같은 창이 패링(parried — 튕겨냄·'PARRY')
 * - 그 뒤 가드 = guarded (피해 × (1 − 감소)) — 그로기 중 가드도 같은 감소(울분은 더 많이)
 */
export type DefenseOutcome =
  | { kind: 'parried' }
  | { kind: 'perfect'; blocked: number }
  | { kind: 'guarded'; amount: number; blocked: number; groggy: boolean }
  | { kind: 'hit'; amount: number };

export interface DefenseInput {
  /** 지금 상태 (parry = 패링 창 · guard = 가드 유지 · other) */
  action: 'parry' | 'guard' | 'other';
  /** 가드 시작 시각 (가드가 아니면 무시) · 지금 */
  guardStartedAt: number;
  now: number;
  /** 퍼펙트 가드 창 (0 이면 없음) · 창 안 피격의 종류 (guard = 퍼펙트 가드, parry = 패링) */
  perfectWindowMs: number;
  perfectKind?: 'guard' | 'parry';
  /** 가드 피해 감소 비율 (0.7 = 70%) */
  guardReduction: number;
  /** 방어력 적용 뒤 피해 */
  damage: number;
  groggy: boolean;
}

/** 가드를 누른 직후 창 안인가 */
export function isPerfectGuard(guardStartedAt: number, now: number, windowMs: number): boolean {
  return windowMs > 0 && now >= guardStartedAt && now - guardStartedAt <= windowMs;
}

export function resolveDefense(i: DefenseInput): DefenseOutcome {
  if (i.action === 'parry') return { kind: 'parried' };
  if (i.action === 'guard') {
    if (isPerfectGuard(i.guardStartedAt, i.now, i.perfectWindowMs))
      return i.perfectKind === 'parry' ? { kind: 'parried' } : { kind: 'perfect', blocked: i.damage };
    const amount = Math.round(i.damage * (1 - i.guardReduction));
    return { kind: 'guarded', amount, blocked: Math.max(0, i.damage - amount), groggy: i.groggy };
  }
  return { kind: 'hit', amount: i.damage };
}
