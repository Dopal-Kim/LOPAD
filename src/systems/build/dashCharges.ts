/**
 * 57라운드 돌파 세트 6 '대쉬 2회 충전' (Phaser 의존 없음): 충전 수만큼 대쉬를 쓰고, 쓴 것은 하나씩 쿨다운 뒤 돌아온다.
 * 충전 1 = 기존 규칙 (대쉬 뒤 쿨다운).
 */
export class DashCharges {
  /** 쓴 충전이 돌아오는 시각들 (오름차순) */
  private pending: number[] = [];

  /** 지금 쓸 수 있는가 */
  ready(now: number, charges: number): boolean {
    this.pending = this.pending.filter((t) => t > now);
    return this.pending.length < Math.max(1, Math.floor(charges));
  }

  /** 한 번 쓴다 — 마지막 충전이 돌아온 뒤부터 쿨다운 (순차 충전) */
  use(now: number, cooldownMs: number): void {
    const last = this.pending.length > 0 ? this.pending[this.pending.length - 1] : now;
    this.pending.push(Math.max(now, last) + cooldownMs);
  }

  /** 남은 충전 (디버그) */
  left(now: number, charges: number): number {
    return Math.max(0, Math.floor(charges) - this.pending.filter((t) => t > now).length);
  }

  reset(): void {
    this.pending = [];
  }
}
