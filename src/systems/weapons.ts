import { WEAPON_RULES } from '../data';
import type { AttackHitbox, WeaponDef, WeaponEvolution, WeaponMods, WeaponRules } from '../data/types';

/** 세이브에 들어가는 무기 개성 상태 */
export interface WeaponProgress {
  personality: number;
  /** 선택한 진화 노드 id 경로 (1차, 2차) */
  path: string[];
  /** 강화 누적 횟수 */
  reinforce: number;
  /** 임계 도달 후 아직 3지선다를 고르지 않음 */
  choicePending: boolean;
}

/**
 * 무기 개성 상태 (기획 4장, 27라운드 분기 트리).
 * 적 처치로 개성 수치를 얻고, 현 단계 임계에 닿으면 `choicePending` 이 되어 게이지가 멈춘다.
 * 3지선다(변환 A / 변환 B / 강화)를 `choose()`·`reinforceNow()` 로 고르면 수치는 0으로 초기화된다.
 * 2차까지 끝나고 강화가 최대면 게이지는 멈춘다. 사망 시 무기도 초기화(기획 3장).
 */
export class WeaponState {
  personality = 0;
  path: string[] = [];
  reinforce = 0;
  choicePending = false;

  constructor(
    readonly id: string,
    readonly def: WeaponDef,
    private readonly rules: WeaponRules = WEAPON_RULES,
  ) {}

  /** 진화 단계 = 선택한 노드 수 (0 = 기본) */
  get stage(): number {
    return this.path.length;
  }

  /** 경로를 따라가는 노드들 */
  get nodes(): WeaponEvolution[] {
    const out: WeaponEvolution[] = [];
    let options: WeaponEvolution[] | undefined = this.def.personality.branches;
    for (const id of this.path) {
      const node: WeaponEvolution | undefined = options?.find((n) => n.id === id);
      if (!node) break;
      out.push(node);
      options = node.next;
    }
    return out;
  }

  /** 현재(마지막) 진화 노드 */
  get evolution(): WeaponEvolution | null {
    const n = this.nodes;
    return n.length ? n[n.length - 1] : null;
  }

  /** 다음 단계 선택지 (트리가 끝났으면 빈 배열) */
  get options(): WeaponEvolution[] {
    if (this.stage >= this.def.personality.thresholds.length) return [];
    const last = this.evolution;
    return last ? (last.next ?? []) : this.def.personality.branches;
  }

  /** 현 단계 임계. 트리가 끝났으면 마지막 임계를 계속 쓴다 */
  get threshold(): number {
    const T = this.def.personality.thresholds;
    return T[Math.min(this.stage, T.length - 1)];
  }

  get canReinforce(): boolean {
    return this.reinforce < this.rules.reinforceMax;
  }

  /** 게이지가 아직 의미가 있는지 (선택지나 강화가 남아 있음) */
  get canEvolve(): boolean {
    return this.options.length > 0 || this.canReinforce;
  }

  get displayName(): string {
    const ev = this.evolution;
    const plus = this.reinforce > 0 ? ` +${this.reinforce}` : '';
    return ev ? `${this.def.name} · ${ev.name}${plus}` : `${this.def.name}${plus}`;
  }

  /** 경로를 따라 병합한 효과 (뒤 노드가 같은 키를 덮어쓴다) */
  get mods(): WeaponMods {
    const out: WeaponMods = {};
    for (const n of this.nodes) Object.assign(out, n.mods);
    return out;
  }

  /** 강화 배율 (피해·범위 공통) */
  get reinforceMult(): number {
    return 1 + this.rules.reinforceBonus * this.reinforce;
  }

  get damageMult(): number {
    let m = this.def.damageMult;
    for (const n of this.nodes) m *= n.damageMult;
    return m * this.reinforceMult;
  }

  get hitbox(): AttackHitbox {
    let m = this.reinforceMult;
    for (const n of this.nodes) m *= n.hitboxMult;
    const h = this.def.hitbox;
    return {
      width: h.width * m,
      height: h.height * m,
      reach: h.reach * m,
      activeMs: h.activeMs,
      cooldownMs: h.cooldownMs,
    };
  }

  /** 공격 중 이동 배율 (중압은 덮어쓴다) */
  get attackSlowMult(): number {
    return this.mods.attackSlowMult ?? this.def.attackSlowMult;
  }

  toProgress(): WeaponProgress {
    return {
      personality: this.personality,
      path: [...this.path],
      reinforce: this.reinforce,
      choicePending: this.choicePending,
    };
  }

  /** 세이브에서 복원. 트리에 없는 id 가 나오면 그 앞까지만 */
  restore(p: Partial<WeaponProgress>): void {
    this.path = [];
    let options: WeaponEvolution[] | undefined = this.def.personality.branches;
    for (const id of p.path ?? []) {
      const node: WeaponEvolution | undefined = options?.find((n) => n.id === id);
      if (!node) break;
      this.path.push(id);
      options = node.next;
    }
    this.reinforce = Math.max(0, Math.min(p.reinforce ?? 0, this.rules.reinforceMax));
    this.personality = Math.max(0, p.personality ?? 0);
    this.choicePending = Boolean(p.choicePending) && this.canEvolve;
  }

  /**
   * 개성 수치를 더한다. 임계에 닿으면 선택 대기 상태가 되고 true 를 반환한다.
   * 선택 대기 중이거나 더 오를 곳이 없으면 무시.
   */
  gainPersonality(amount: number): boolean {
    if (this.choicePending || !this.canEvolve) return false;
    this.personality += amount;
    if (this.personality >= this.threshold) {
      this.personality = this.threshold;
      this.choicePending = true;
      return true;
    }
    return false;
  }

  /** 변환 선택. 선택지에 없는 id 면 null */
  choose(id: string): WeaponEvolution | null {
    const node = this.options.find((n) => n.id === id);
    if (!node) return null;
    this.path.push(id);
    this.personality = 0;
    this.choicePending = false;
    return node;
  }

  /** 현재 개성 강화 (+reinforceBonus, 최대 reinforceMax 회). 불가하면 false */
  reinforceNow(): boolean {
    if (!this.canReinforce) return false;
    this.reinforce += 1;
    this.personality = 0;
    this.choicePending = false;
    return true;
  }
}
