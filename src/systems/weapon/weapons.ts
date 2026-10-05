import { WEAPON_RULES } from '../../data';
import type { WeaponDef, WeaponEvolution, WeaponMods, WeaponRules } from '../../data/types';

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
  /** 57라운드 Q37: 각성 후 강화 상한 (null = 규칙 reinforceMax) */
  reinforceCapOverride: number | null = null;

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

  /** 강화 상한 (57라운드: 각성 후 5) */
  get reinforceCap(): number {
    return this.reinforceCapOverride ?? this.rules.reinforceMax;
  }

  get canReinforce(): boolean {
    return this.reinforce < this.reinforceCap;
  }

  /**
   * 게이지가 아직 의미가 있는지 (선택지나 강화가 남아 있음). 57라운드 Q37: 트리가 끝난 뒤에도 피의 계약·각성 칸이 있으므로
   * 호출 쪽(Progression)이 칸 계산으로 덮어쓴다 — `gainPersonality(amount, canEvolve)`
   */
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

  /** 61라운드 P9 (옛 hitbox 대체): 판정 크기 배율 = 강화 × 경로 노드 hitboxMult */
  get rangeMult(): number {
    let m = this.reinforceMult;
    for (const n of this.nodes) m *= n.hitboxMult;
    return m;
  }

  /** 판정 기준 거리 px (배율 전): 근접 = 연격 반경 `combo.radiusPx`, 원거리 = 화살이 생기는 거리 `ranged.spawnPx` */
  get baseReachPx(): number {
    return this.def.combo?.radiusPx ?? this.def.ranged?.spawnPx ?? 0;
  }

  /** 판정 기준 거리 px (강화·갈래 배율 반영) — 패시브·갈래 효과의 사거리 기준 */
  get reachPx(): number {
    return this.baseReachPx * this.rangeMult;
  }

  /**
   * 51라운드 Q2·Q3 활 템포: 다음 발 간격 · 시위 당김(클릭 → 화살이 떠나는 프레임) · 그 프레임. 속사 fireRateMult 로 나눈다.
   * 원거리가 아니면 drawMs 0
   */
  get shotTiming(): { cooldownMs: number; drawMs: number; releaseFrame: number } {
    const k = Math.max(0.1, this.mods.fireRateMult ?? 1);
    const R = this.def.ranged;
    return {
      cooldownMs: (R?.cooldownMs ?? 0) / k,
      drawMs: (R?.drawMs ?? 0) / k,
      releaseFrame: R?.releaseFrame ?? 2,
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
    this.reinforce = Math.max(0, Math.min(p.reinforce ?? 0, this.reinforceCap));
    this.personality = Math.max(0, p.personality ?? 0);
    this.choicePending = Boolean(p.choicePending) && this.canEvolve;
  }

  /**
   * 개성 수치를 더한다. 임계에 닿으면 선택 대기 상태가 되고 true 를 반환한다.
   * 선택 대기 중이거나 더 오를 곳이 없으면 무시.
   */
  gainPersonality(amount: number, canEvolve = this.canEvolve): boolean {
    if (this.choicePending || !canEvolve) return false;
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

  /** 개성 3지선다의 강화 아닌 칸(피의 계약·각성)을 골랐다: 수치 0, 대기 끝 */
  consumeChoice(): void {
    this.personality = 0;
    this.choicePending = false;
  }

  /** 현재 개성 강화 (+reinforceBonus, 최대 reinforceCap 회). 불가하면 false */
  reinforceNow(): boolean {
    if (!this.canReinforce) return false;
    this.reinforce += 1;
    this.personality = 0;
    this.choicePending = false;
    return true;
  }
}
