import type { AttackHitbox, WeaponDef, WeaponEvolution } from '../data/types';

/**
 * 무기 개성 상태 (기획 4장): 적 처치로 개성 수치를 얻고, threshold 에 도달하면
 * 다음 진화 단계로 넘어가며 수치는 0으로 초기화된다. 사망 시 무기도 초기화(기획 3장).
 */
export class WeaponState {
  personality = 0;
  stage = 0; // 0 = 기본, 1.. = evolutions[stage-1]

  constructor(
    readonly id: string,
    readonly def: WeaponDef,
  ) {}

  get evolution(): WeaponEvolution | null {
    return this.stage === 0 ? null : this.def.personality.evolutions[this.stage - 1];
  }

  get displayName(): string {
    return this.evolution ? `${this.def.name} · ${this.evolution.name}` : this.def.name;
  }

  get damageMult(): number {
    return this.def.damageMult * (this.evolution?.damageMult ?? 1);
  }

  get hitbox(): AttackHitbox {
    const m = this.evolution?.hitboxMult ?? 1;
    const h = this.def.hitbox;
    return {
      width: h.width * m,
      height: h.height * m,
      reach: h.reach * m,
      activeMs: h.activeMs,
      cooldownMs: h.cooldownMs,
    };
  }

  get canEvolve(): boolean {
    return this.stage < this.def.personality.evolutions.length;
  }

  /** 세이브에서 복원 */
  restore(personality: number, stage: number): void {
    this.personality = personality;
    this.stage = Math.min(stage, this.def.personality.evolutions.length);
  }

  /** 개성 수치를 더하고, 진화가 일어났으면 새 단계 번호를 반환 (아니면 null) */
  gainPersonality(amount: number): number | null {
    if (!this.canEvolve) return null;
    this.personality += amount;
    if (this.personality >= this.def.personality.threshold) {
      this.personality = 0;
      this.stage += 1;
      return this.stage;
    }
    return null;
  }
}
