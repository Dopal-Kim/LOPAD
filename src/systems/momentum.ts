/**
 * 55라운드 Q23 대검 관성 (계약 §17): 이어지는 타마다 공속 +perHit, 최대 +max. 마지막 입력(누름·홀드)에서
 * idleResetMs 동안 입력이 없거나 피격되면 처음부터. 최대일 때 내려찍기 끝점 충격원 확대(maxImpactMult). Phaser 의존 없음.
 */
import type { ComboMomentumDef } from '../data/types';

export class Momentum {
  /** 지금 이어지고 있는 타 수 (다음 타 전까지 시작한 타) */
  private count = 0;
  private lastInputAt = -Infinity;

  constructor(private readonly def: ComboMomentumDef) {}

  /** 좌클릭 누름·홀드 (입력이 이어지는 동안 매 프레임 불러도 된다) */
  input(now: number): void {
    this.expire(now);
    this.lastInputAt = now;
  }

  /** 무입력 시간이 지났으면 초기화 */
  expire(now: number): void {
    if (now - this.lastInputAt > this.def.idleResetMs) this.count = 0;
  }

  /** 지금 더해지는 공속 비율 (0 ~ max) */
  get bonus(): number {
    return Math.min(this.def.max, this.count * this.def.perHit);
  }

  /** 최대 관성인가 (끝점 충격원 확대) */
  get atMax(): boolean {
    return this.def.max > 0 && this.bonus >= this.def.max - 1e-9;
  }

  /** 다음 타의 공속 배율 */
  get speedMult(): number {
    return 1 + this.bonus;
  }

  /** 지금 최대면 충격원 배율, 아니면 1 */
  get impactMult(): number {
    return this.atMax ? this.def.maxImpactMult : 1;
  }

  /**
   * 한 타 시작: 이 타에 쓸 공속 배율·최대 여부를 돌려주고 다음 타를 위해 하나 쌓는다
   */
  onHit(now: number): { speedMult: number; atMax: boolean; bonus: number } {
    this.expire(now);
    const out = { speedMult: this.speedMult, atMax: this.atMax, bonus: this.bonus };
    this.count += 1;
    return out;
  }

  /** 피격 등으로 처음부터 */
  reset(): void {
    this.count = 0;
  }

  debug(now: number): { count: number; bonus: number; atMax: boolean; idleMs: number } {
    return { count: this.count, bonus: this.bonus, atMax: this.atMax, idleMs: now - this.lastInputAt };
  }
}
