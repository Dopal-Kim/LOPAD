/**
 * 57라운드 빌드 축: Player(피격·대쉬·완벽 창)가 부르는 훅 — 씬 BuildRuntime(BuildDefense)이 구현해 `player.buildHooks` 에 넣는다.
 * 없으면 기본 규칙.
 */
/** PlayerDefense 가 부르는 훅 (Player.buildHooks) */
export interface PlayerBuildHooks {
  /** 피해 계산 전 — true 면 이 공격을 흘린다 (취보 휘청) */
  evadeHit(time: number, source?: { dirX: number; dirY: number }): boolean;
  /** 무적으로 흘린 피격 (대쉬 무적 — 완벽 회피 검사) */
  onIgnoredHit(time: number): void;
  /** 받는 피해 조정 */
  adjustDamage(amount: number, time: number): number;
  /** 60라운드: 맞으면서 버티는 중 (거인 차지 — 끊기지 않음 · 흡수 fx greatsword_brace_absorb, 울분 없음) */
  absorbing(time: number): boolean;
  /** 가드 피해 감소 추가 (굳은살 칼·대검) */
  guardReductionAdd(): number;
  /** HP 0 직전 — true 면 버텼다 (HP 를 채움) */
  preventDeath(time: number): boolean;
  /** 피격 경직·밀려남 없음 (취기 상태 · 강공 중 끊기지 않음) */
  noFlinch(time: number): boolean;
  /** 완벽 창 추가 ms (퍼펙트 가드·패링) */
  perfectWindowAddMs(baseMs: number): number;
  /** 대쉬 가능 · 쿨다운 배율 · 충전 수 */
  dashAllowed(): boolean;
  dashCooldownMult(): number;
  dashCharges(): number;
  /** 그림자 걸음 쿨다운 배율 (각성 백귀는 고정 ms) */
  shadowStepCooldown(baseMs: number): number;
}
