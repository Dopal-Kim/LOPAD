/**
 * 49라운드 Q4·Q6: 무기 자원 상태 머신 (Phaser 의존 없음, 시간은 호출 쪽이 넣는다).
 * - 기력(stamina, 칼·대검): 공격·대쉬·강한 타가 소모, 마지막 소모 뒤 regenDelayMs 가 지나면 회복.
 *   0 이 되면 exhausted — max × recoverRatio 까지 차야 풀린다. exhausted 동안 이동 감속·강한 타 불가.
 * - 화살 탄창(ammo, 활): 한 발마다 1, 비면 자동 장전(reloadMs). 수동 장전은 탄창이 덜 찼을 때.
 * - 가속(heat, 단검 — 61라운드 SY-2 '과열'을 벌칙 없는 가속으로): 공격마다 오르고, 마지막 공격 뒤 decayDelayMs 가 지나면 식는다.
 *   경계(stages)를 넘을 때마다 단계 +1(공격 속도 배율 speedMults). 과열·폭발·식힘 벌칙 없음.
 * 계약 §11.1 `UiWeaponResource` 로 내보낸다 (`hidden` 자원은 null — 단검 가속).
 * 56라운드 Q7·Q19: 기력에 `groggyMs` 가 있으면 0 = 그로기 — 그 시간 동안 회복 없음·공격 불가(가드만), 지나야만 풀리고
 * 기력 = max × recoverRatio. 61라운드: 기력은 대쉬·가드·강공만 소모(일반 연격 무소모) — 그로기는 드물게.
 */
import type { StaminaResourceDef, WeaponMods, WeaponResourceDef } from '../../data/types';
import type { UiWeaponResource } from '../../contract/ui';
import { clamp01 } from '../mathUtil';

export class WeaponResource {
  value: number;
  /** 기력: 바닥난 상태 */
  private exhausted = false;
  /** 기력: 마지막 소모 · 과열: 마지막 가열 */
  private lastUseAt = -Infinity;
  /** 탄창: 장전 시작 시각 (-1 = 장전 중 아님) */
  private reloadStart = -1;
  /** 56라운드: 그로기가 풀리는 시각 (그로기 규칙이 아니거나 그로기가 아니면 -Infinity) */
  private groggyUntil = -Infinity;

  constructor(readonly def: WeaponResourceDef) {
    this.value = def.kind === 'heat' ? 0 : def.max;
  }

  get kind(): WeaponResourceDef['kind'] {
    return this.def.kind;
  }

  get max(): number {
    return this.def.max;
  }

  /**
   * 60라운드 소모품 '냉수 한 바가지': 기력 = 그로기·바닥 해제 + 최대 × staminaRatio 이상 / 가속 0 / 탄창 가득 (장전 끝)
   */
  refresh(staminaRatio: number): void {
    const d = this.def;
    if (d.kind === 'stamina') {
      this.exhausted = false;
      this.groggyUntil = -Infinity;
      this.value = Math.max(this.value, d.max * staminaRatio);
      this.lastUseAt = -Infinity;
    } else if (d.kind === 'ammo') {
      this.reloadStart = -1;
      this.value = d.max;
    } else {
      this.value = 0;
    }
  }

  /** 매 프레임. dtMs = 이번 프레임 길이 */
  tick(now: number, dtMs: number): void {
    const d = this.def;
    const dt = Math.max(0, dtMs);
    if (d.kind === 'stamina') {
      if (this.groggyRule && this.exhausted) {
        // 56라운드 Q19: 그로기는 시간이 지나야만 풀린다 (그동안 회복 없음)
        if (now < this.groggyUntil) return;
        this.exhausted = false;
        this.groggyUntil = -Infinity;
        this.value = Math.max(this.value, d.max * d.recoverRatio);
        this.lastUseAt = -Infinity;
        return;
      }
      if (now - this.lastUseAt >= d.regenDelayMs && this.value < d.max)
        this.value = Math.min(d.max, this.value + (d.regenPerSec * dt) / 1000);
      if (this.exhausted && this.value >= d.max * d.recoverRatio) this.exhausted = false;
    } else if (d.kind === 'ammo') {
      if (this.reloadStart >= 0 && now - this.reloadStart >= d.reloadMs) {
        this.reloadStart = -1;
        this.value = d.max;
      }
    } else if (now - this.lastUseAt >= d.decayDelayMs && this.value > 0) {
      // 가속: 멈추면 식는다 (벌칙 없음)
      this.value = Math.max(0, this.value - (d.decayPerSec * dt) / 1000);
    }
  }

  // --- 기력 ---

  /** 기력 소모. 0 에 닿으면 exhausted (56라운드: 그로기 규칙이면 그로기 시작) */
  spend(amount: number, now: number): void {
    if (this.def.kind !== 'stamina' || amount <= 0) return;
    if (this.groggyRule && this.exhausted) return;
    this.lastUseAt = now;
    this.value = Math.max(0, this.value - amount);
    if (this.value <= 0) {
      this.exhausted = true;
      if (this.def.groggyMs !== undefined) this.groggyUntil = now + this.def.groggyMs;
    }
  }

  get isExhausted(): boolean {
    return this.def.kind === 'stamina' && this.exhausted;
  }

  /** 56라운드: 그로기 규칙(기력 `groggyMs`)을 쓰는가 */
  get groggyRule(): boolean {
    return this.def.kind === 'stamina' && this.def.groggyMs !== undefined;
  }

  /** 56라운드 Q7: 그로기 중 (공격·대쉬 불가, 가드만) */
  get isGroggy(): boolean {
    return this.groggyRule && this.exhausted;
  }

  /** 그로기 남은 ms (그로기가 아니면 0) */
  groggyLeftMs(now: number): number {
    return this.isGroggy ? Math.max(0, this.groggyUntil - now) : 0;
  }

  /** 강한 타(3타·대쉬 공격·내리찍기) 가능 — 기력 무기가 바닥나지 않았을 때 (다른 자원은 항상) */
  get canStrong(): boolean {
    return !this.isExhausted;
  }

  /** 이동 속도 배율 (기력 바닥 감속) */
  get moveMult(): number {
    return this.def.kind === 'stamina' && this.exhausted ? this.def.exhaustedMoveMult : 1;
  }

  // --- 탄창 ---

  get reloading(): boolean {
    return this.def.kind === 'ammo' && this.reloadStart >= 0;
  }

  /** 지금 쏠 수 있는가 (탄창 무기가 아니면 true) */
  canFire(): boolean {
    if (this.def.kind !== 'ammo') return true;
    return !this.reloading && this.value >= 1;
  }

  /** n 발 쏨. 비면 자동 장전을 시작하고 true(장전 시작) */
  fire(now: number, n = 1): boolean {
    if (this.def.kind !== 'ammo') return false;
    this.value = Math.max(0, this.value - n);
    if (this.value <= 0) return this.startReload(now);
    return false;
  }

  /** 장전 시작 (장전 중이 아니고 탄창이 덜 찼을 때). 시작했으면 true */
  startReload(now: number): boolean {
    if (this.def.kind !== 'ammo' || this.reloading || this.value >= this.def.max) return false;
    this.reloadStart = now;
    return true;
  }

  /** 장전 진행도 0..1 (장전 중 아니면 0) */
  reloadProgress(now: number): number {
    if (this.def.kind !== 'ammo' || this.reloadStart < 0) return 0;
    return clamp01((now - this.reloadStart) / this.def.reloadMs);
  }

  // --- 가속 (단검) ---

  /** 연격 n 번째 타(0부터) 가속 */
  heatUp(hitIndex: number, now: number): void {
    const d = this.def;
    if (d.kind !== 'heat') return;
    const g = d.gainPerHit[Math.min(hitIndex, d.gainPerHit.length - 1)] ?? 0;
    this.lastUseAt = now;
    this.value = Math.min(d.max, this.value + g);
  }

  /** 56라운드 2단계 고속 난타: 찌르기마다 정해진 양만큼 가속 */
  heatBy(amount: number, now: number): void {
    const d = this.def;
    if (d.kind !== 'heat' || amount <= 0) return;
    this.lastUseAt = now;
    this.value = Math.min(d.max, this.value + amount);
  }

  /** 가속 단계 0..stages.length */
  get stage(): number {
    const d = this.def;
    if (d.kind !== 'heat') return 0;
    let s = 0;
    for (const b of d.stages) if (this.value >= b) s++;
    return s;
  }

  /** 공격 속도 배율 (가속 단계) */
  get speedMult(): number {
    const d = this.def;
    if (d.kind !== 'heat') return 1;
    return d.speedMults[Math.min(this.stage, d.speedMults.length - 1)] ?? 1;
  }

  /** 가속 비율 0..1 (단검 가속 — 열풍 2단 규칙) */
  get ratio(): number {
    return clamp01(this.value / Math.max(1, this.def.max));
  }

  // --- 공통 ---

  /** 지금 공격(연격 한 타·화살 한 발)을 시작할 수 있는가 */
  canAttack(): boolean {
    if (this.def.kind === 'ammo') return this.canFire();
    if (this.def.kind === 'heat') return true;
    // 56라운드 Q7: 그로기 중 공격 불가
    return !this.isGroggy;
  }

  /** 계약 §11.1 게이지 (61라운드: `hidden` 자원은 null — 단검 가속은 보이지 않고 낙인만 보인다) */
  toUi(now: number): UiWeaponResource | null {
    const d = this.def;
    if (d.hidden) return null;
    const base = { kind: d.kind, label: d.label, max: d.max };
    if (d.kind === 'stamina') return { ...base, value: round1(this.value), state: staminaState(d, this) };
    if (d.kind === 'ammo') {
      if (this.reloading)
        return { ...base, value: Math.floor(this.value), state: 'reloading', progress: this.reloadProgress(now) };
      return { ...base, value: Math.floor(this.value), state: this.value <= d.lowCount ? 'low' : 'ok' };
    }
    return { ...base, value: round1(this.value), state: 'ok', stage: this.stage };
  }

  /** 디버그 */
  debug(now: number): Record<string, unknown> {
    return {
      kind: this.kind,
      value: this.value,
      max: this.max,
      exhausted: this.isExhausted,
      groggy: this.isGroggy,
      groggyLeftMs: this.groggyLeftMs(now),
      reloading: this.reloading,
      stage: this.stage,
      speedMult: this.speedMult,
      ui: this.toUi(now),
    };
  }
}

function staminaState(d: StaminaResourceDef, r: WeaponResource): UiWeaponResource['state'] {
  if (r.isExhausted) return 'exhausted';
  return r.value < d.max * d.lowRatio ? 'low' : 'ok';
}

function round1(v: number): number {
  return Math.round(v * 10) / 10;
}

/** 57라운드 빌드 축 자원 조정: 피멍 최대치 ×maxMult(영구) · 식힘·재장전 ×coolMult · 그로기 ms 덮어쓰기(버팀 4·피멍) */
export interface ResourceAdjust {
  maxMult?: number;
  coolMult?: number;
  groggyMs?: number | null;
}

/** 51라운드 속사: 갈래가 바꾼 탄창 수·장전 시간 (탄창이 아니면 그대로) + 57라운드 빌드 축 조정 */
export function effectiveResource(
  def: WeaponResourceDef,
  mods: WeaponMods,
  adj: ResourceAdjust = {},
): WeaponResourceDef {
  const maxMult = adj.maxMult ?? 1;
  const cool = adj.coolMult ?? 1;
  if (def.kind === 'ammo') {
    if (!mods.magazineBonus && !mods.reloadMult && maxMult === 1 && cool === 1) return def;
    return {
      ...def,
      max: Math.max(1, Math.round((def.max + (mods.magazineBonus ?? 0)) * maxMult)),
      reloadMs: def.reloadMs * (mods.reloadMult ?? 1) * cool,
    };
  }
  if (def.kind === 'heat') {
    if (maxMult === 1) return def;
    return { ...def, max: def.max * maxMult };
  }
  const groggy = def.groggyMs !== undefined && adj.groggyMs ? adj.groggyMs : def.groggyMs;
  if (maxMult === 1 && groggy === def.groggyMs) return def;
  return { ...def, max: def.max * maxMult, ...(groggy !== undefined ? { groggyMs: groggy } : {}) };
}
