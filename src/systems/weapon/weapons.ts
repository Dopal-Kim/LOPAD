import { WEAPON_RULES } from '../../data';
import { GROWTH, branchByNode, pathByNode, traitDef } from '../../data/growth';
import type { TraitDef } from '../../data/growthTypes';
import type { WeaponDef, WeaponEvolution, WeaponMods, WeaponRules } from '../../data/types';

/** 세이브에 들어가는 무기 성장 상태 (61 G — P12) */
export interface WeaponProgress {
  /** 각성 게이지 (누적, 줄지 않음) */
  gauge: number;
  /** 고른 노드 id 경로 (1차 갈래 노드, 2차 길 노드) */
  path: string[];
  /** 얻은 개성 카드 id */
  traits: string[];
  /** 단련 횟수 */
  temper: number;
  /** 처리한 눈금 수 (눈금 목록 앞에서부터) */
  marksDone: number;
}

/**
 * 무기 성장 상태 (61라운드 단계 4 P12 — 옛 개성 임계·0 리셋·강화 대체).
 * 처치·성과로 각성 게이지가 쌓이고(줄지 않음) 눈금(`systems/growth/marks`)을 넘을 때마다 메뉴 하나가 대기한다 —
 * ◇ 개성 발현 · ◆ 1차 각성(갈래) · ◆ 2차 각성(길) · 단련. 대기 순서·메뉴 열기는 씬 `GrowthFlow`.
 * 사망 시 무기도 초기화(기획 3장).
 */
export class WeaponState {
  gauge = 0;
  path: string[] = [];
  traits: string[] = [];
  temper = 0;
  marksDone = 0;

  constructor(
    readonly id: string,
    readonly def: WeaponDef,
    private readonly rules: WeaponRules = WEAPON_RULES,
  ) {}

  /** 각성 단계 = 선택한 노드 수 (0 기본 · 1 1차 각성 · 2 2차 각성) */
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
    if (this.stage >= 2) return [];
    const last = this.evolution;
    return last ? (last.next ?? []) : this.def.personality.branches;
  }

  /** 고른 1차 갈래 id (art §26 — growth.json) */
  get branchId(): string | null {
    return branchByNode(this.id, this.path[0])?.id ?? null;
  }

  /** 고른 2차 길 id */
  get pathId(): string | null {
    return pathByNode(this.id, this.path[1])?.path.id ?? null;
  }

  get temperMax(): number {
    return GROWTH.temper.max;
  }

  get canTemper(): boolean {
    return this.temper < this.temperMax;
  }

  get traitDefs(): TraitDef[] {
    return this.traits.map((id) => traitDef(id)).filter((t): t is TraitDef => Boolean(t));
  }

  get displayName(): string {
    const b = branchByNode(this.id, this.path[0]);
    const p = pathByNode(this.id, this.path[1]);
    const plus = this.temper > 0 ? ` +${this.temper}` : '';
    const name = p ? `${b?.name ?? ''} · ${p.path.name}` : b ? b.name : '';
    return name ? `${this.def.name} · ${name}${plus}` : `${this.def.name}${plus}`;
  }

  /** 경로를 따라 병합한 효과 (뒤 노드가 같은 키를 덮어쓴다) */
  get mods(): WeaponMods {
    const out: WeaponMods = {};
    for (const n of this.nodes) Object.assign(out, n.mods);
    return out;
  }

  /** 단련 배율 (피해) */
  get temperDamageMult(): number {
    return 1 + GROWTH.temper.damageBonus * this.temper;
  }

  /** 단련 배율 (범위) */
  get temperRangeMult(): number {
    return 1 + GROWTH.temper.rangeBonus * this.temper;
  }

  /** 옛 이름 호환 — 갈래 수단이 쓰는 '강화' 피해 배율 = 단련 피해 배율 */
  get reinforceMult(): number {
    return this.temperDamageMult;
  }

  get damageMult(): number {
    let m = this.def.damageMult;
    for (const n of this.nodes) m *= n.damageMult;
    return m * this.temperDamageMult;
  }

  /** 판정 크기 배율 = 단련 × 경로 노드 hitboxMult */
  get rangeMult(): number {
    let m = this.temperRangeMult;
    for (const n of this.nodes) m *= n.hitboxMult;
    return m;
  }

  /** 판정 기준 거리 px (배율 전): 근접 = 연격 반경 `combo.radiusPx`, 원거리 = 화살이 생기는 거리 `ranged.spawnPx` */
  get baseReachPx(): number {
    return this.def.combo?.radiusPx ?? this.def.ranged?.spawnPx ?? 0;
  }

  /** 판정 기준 거리 px (단련·갈래 배율 반영) — 패시브·갈래 효과의 사거리 기준 */
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

  /** 무기 규칙 (DPS 기준선 등) */
  get weaponRules(): WeaponRules {
    return this.rules;
  }

  toProgress(): WeaponProgress {
    return {
      gauge: this.gauge,
      path: [...this.path],
      traits: [...this.traits],
      temper: this.temper,
      marksDone: this.marksDone,
    };
  }

  /** 세이브에서 복원. 트리에 없는 id 가 나오면 그 앞까지만, 없는 개성은 버린다 */
  restore(p: Partial<WeaponProgress>): void {
    this.setPath(p.path ?? []);
    this.traits = (p.traits ?? []).filter((id) => traitDef(id)?.weapon === this.id);
    this.temper = Math.max(0, Math.min(Math.floor(p.temper ?? 0), this.temperMax));
    this.gauge = Math.max(0, Number(p.gauge) || 0);
    this.marksDone = Math.max(0, Math.floor(Number(p.marksDone) || 0));
  }

  /** 경로를 바로 정한다 (시험장·복원) — 트리에 없는 id 는 그 앞까지 */
  setPath(ids: readonly string[]): void {
    this.path = [];
    let options: WeaponEvolution[] | undefined = this.def.personality.branches;
    for (const id of ids.slice(0, 2)) {
      const node: WeaponEvolution | undefined = options?.find((n) => n.id === id);
      if (!node) break;
      this.path.push(id);
      options = node.next;
    }
  }

  /** 각성 게이지를 더한다 (음수·NaN 은 무시). 더한 양 */
  gain(amount: number): number {
    const a = Math.max(0, Number(amount) || 0);
    this.gauge += a;
    return a;
  }

  /** 갈래·길 선택 (지금 단계의 선택지에 있을 때만). 고른 노드 */
  choose(nodeId: string): WeaponEvolution | null {
    const node = this.options.find((n) => n.id === nodeId);
    if (!node) return null;
    this.path.push(nodeId);
    return node;
  }

  /** 개성 하나 얻기 (이 무기 것·아직 없는 것만) */
  addTrait(id: string): boolean {
    if (this.traits.includes(id) || traitDef(id)?.weapon !== this.id) return false;
    this.traits.push(id);
    return true;
  }

  /** 단련 +1 (상한이면 false) */
  temperNow(): boolean {
    if (!this.canTemper) return false;
    this.temper += 1;
    return true;
  }
}
