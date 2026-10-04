/**
 * 56라운드 Q13~Q20 무기별 고유 자원 (Phaser 의존 없음, 시간은 호출 쪽이 넣는다). 기력·과열·탄창(`weaponResource`)과 따로 돈다.
 * - 칼 검기(劍氣) 3단 `KenkiGauge` · 대검 울분(鬱憤) `GrudgeGauge` · 활 숨(呼吸) `BreathGauge` — 무기 하나에 하나
 * - 단검 낙인(烙印)은 적마다 쌓이므로 `BrandBook`(대상 → 표식 수)
 * HUD 표시는 UI 계약 §13 `UiSnapshot.gauge`(승인 #20) — 값은 PlayerGauges.toUi · BrandMarks.toUi 가 만든다.
 */
import type { BrandGaugeDef, BreathGaugeDef, GrudgeGaugeDef, KenkiGaugeDef, WeaponGaugeDef } from '../../data/types';

/** 칼 검기: 단(0..stages) = floor(값 / perStage) */
export class KenkiGauge {
  value = 0;
  constructor(readonly def: KenkiGaugeDef) {}

  get max(): number {
    return this.def.stages * this.def.perStage;
  }

  get stage(): number {
    return Math.min(this.def.stages, Math.floor(this.value / this.def.perStage + 1e-9));
  }

  /** 근접 적중 1회 → 단이 바뀌었으면 새 단 (아니면 null) */
  gainHit(): number | null {
    return this.add(this.def.gainPerHit);
  }

  /** 패링 성공 → 단을 즉시 채운다 (다음 단 경계까지 올린 뒤 남은 단만큼) */
  gainParry(): number | null {
    const before = this.stage;
    const target = Math.min(this.def.stages, before + this.def.parryGainStages) * this.def.perStage;
    this.value = Math.max(this.value, Math.min(this.max, target));
    return this.stage !== before ? this.stage : null;
  }

  /** 일섬: 전부 소모 → 소모한 단 수 · 피해 배율 · 분신 여부 */
  consume(): { stages: number; damageMult: number; clone: boolean } {
    const stages = this.stage;
    this.value = 0;
    return {
      stages,
      damageMult: 1 + stages * this.def.issenDamagePerStage,
      clone: stages >= this.def.cloneAtStages,
    };
  }

  private add(n: number): number | null {
    const before = this.stage;
    this.value = Math.min(this.max, this.value + Math.max(0, n));
    return this.stage !== before ? this.stage : null;
  }
}

export type GuardBlockMode = 'normal' | 'perfect' | 'groggy';

/** 대검 울분: 가드로 막은 피해가 쌓이고 차지가 전부 소모 */
export class GrudgeGauge {
  value = 0;
  constructor(readonly def: GrudgeGaugeDef) {}

  get max(): number {
    return this.def.max;
  }

  get full(): boolean {
    return this.value >= this.def.max;
  }

  get ratio(): number {
    return Math.max(0, Math.min(1, this.value / this.def.max));
  }

  /**
   * 가드로 막음: blocked = 줄어든 피해량(퍼펙트면 원래 피해 전부). 반환 = 이번에 가득 찼는가
   */
  addBlocked(blocked: number, mode: GuardBlockMode): boolean {
    const d = this.def;
    const was = this.full;
    const mult = d.blockGainMult * (mode === 'perfect' ? d.perfectMult : mode === 'groggy' ? d.groggyMult : 1);
    this.value = Math.min(d.max, this.value + Math.max(0, blocked) * mult);
    return !was && this.full;
  }

  /** 차지 내려찍기·꽂아내리기: 전부 소모 → 피해·판정 길이 배율 */
  consume(): { ratio: number; damageMult: number; rangeMult: number } {
    const ratio = this.ratio;
    this.value = 0;
    return { ratio, damageMult: 1 + ratio * this.def.slamDamageBonus, rangeMult: 1 + ratio * this.def.slamRangeBonus };
  }
}

/** 활 숨: 완벽 놓기마다 회복, 가득이면 다음 당김이 집중(감속 정밀 조준) */
export class BreathGauge {
  value = 0;
  private focusUntil = -Infinity;
  constructor(readonly def: BreathGaugeDef) {}

  get max(): number {
    return this.def.max;
  }

  get full(): boolean {
    return this.value >= this.def.max;
  }

  /** 완벽 놓기 → 이번에 가득 찼는가 */
  addPerfect(): boolean {
    const was = this.full;
    this.value = Math.min(this.def.max, this.value + this.def.perfectGain);
    return !was && this.full;
  }

  /** 가득일 때 집중 시작 (숨 소모). 시작했으면 true */
  startFocus(now: number): boolean {
    if (!this.full || this.focusing(now)) return false;
    this.focusUntil = now + this.def.focusMs;
    this.value = 0;
    return true;
  }

  focusing(now: number): boolean {
    return now < this.focusUntil;
  }

  /** 놓거나 취소하면 집중 끝. 진행 중이었으면 true */
  endFocus(now: number): boolean {
    const was = this.focusing(now);
    this.focusUntil = -Infinity;
    return was;
  }

  focusLeftMs(now: number): number {
    return Math.max(0, this.focusUntil - now);
  }
}

/** 무기 하나의 고유 자원 (낙인은 BrandBook — 무기 자원이 아니라 적마다) */
export type WeaponGauge = KenkiGauge | GrudgeGauge | BreathGauge;

export function makeGauge(def: WeaponGaugeDef | undefined): WeaponGauge | null {
  if (!def) return null;
  if (def.kind === 'kenki') return new KenkiGauge(def);
  if (def.kind === 'grudge') return new GrudgeGauge(def);
  if (def.kind === 'breath') return new BreathGauge(def);
  return null;
}

interface BrandEntry {
  marks: number;
  /** 소수 획득(과열 단계 배율) 누적 */
  carry: number;
  lastAt: number;
}

/**
 * 단검 낙인 장부: 대상 → 표식. 같은 대상을 칠 때마다 perHit(등 뒤 backGain) × (1 + 과열 단계 × heatGainPerStage),
 * 최대 max, lifeMs 동안 새 표식이 없으면 사라진다.
 */
export class BrandBook<K> {
  private readonly entries = new Map<K, BrandEntry>();
  constructor(readonly def: BrandGaugeDef) {}

  /** 표식 추가 → 이전·이후 표식 수 */
  add(target: K, now: number, opts: { back: boolean; heatStage: number }): { before: number; after: number } {
    const d = this.def;
    const e = this.entries.get(target) ?? { marks: 0, carry: 0, lastAt: now };
    const before = e.marks;
    const base = opts.back ? d.backGain : d.perHit;
    const gain = base * (1 + Math.max(0, opts.heatStage) * d.heatGainPerStage) + e.carry;
    const whole = Math.floor(gain + 1e-9);
    e.carry = gain - whole;
    e.marks = Math.min(d.max, e.marks + whole);
    if (e.marks >= d.max) e.carry = 0;
    e.lastAt = now;
    this.entries.set(target, e);
    return { before, after: e.marks };
  }

  marks(target: K): number {
    return this.entries.get(target)?.marks ?? 0;
  }

  /** 대상의 표식을 전부 떼어 낸다 (폭발) → 표식 수 */
  take(target: K): number {
    const n = this.marks(target);
    this.entries.delete(target);
    return n;
  }

  /** 조건에 맞는 대상의 표식을 전부 떼어 낸다 (과열 일괄 폭발) */
  takeWhere(pred: (target: K) => boolean): [K, number][] {
    const out: [K, number][] = [];
    for (const [k, e] of this.entries)
      if (e.marks > 0 && pred(k)) {
        out.push([k, e.marks]);
        this.entries.delete(k);
      }
    return out;
  }

  /** 오래된 표식·사라진 대상 정리 */
  expire(now: number, alive: (target: K) => boolean = () => true): void {
    for (const [k, e] of this.entries) if (!alive(k) || now - e.lastAt >= this.def.lifeMs) this.entries.delete(k);
  }

  /** 표식이 있는 대상 목록 */
  list(): [K, number][] {
    return [...this.entries].filter(([, e]) => e.marks > 0).map(([k, e]) => [k, e.marks]);
  }

  clear(): void {
    this.entries.clear();
  }
}

/**
 * 등 뒤 판정: 대상이 바라보는 방향(단위벡터)과 공격 진행 방향 사이 각이 maxDeg 이하 = 대상의 등 뒤에서 침
 */
export function isBackHit(
  facing: { x: number; y: number },
  attackDir: { x: number; y: number },
  maxDeg: number,
): boolean {
  const fl = Math.hypot(facing.x, facing.y);
  const al = Math.hypot(attackDir.x, attackDir.y);
  if (fl === 0 || al === 0) return false;
  const cos = (facing.x * attackDir.x + facing.y * attackDir.y) / (fl * al);
  return cos >= Math.cos((maxDeg * Math.PI) / 180) - 1e-9;
}
