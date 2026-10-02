/**
 * 49라운드 Q4·Q6: 무기 자원 상태 머신 (Phaser 의존 없음, 시간은 호출 쪽이 넣는다).
 * - 기력(stamina, 칼·대검): 공격·대쉬·강한 타가 소모, 마지막 소모 뒤 regenDelayMs 가 지나면 회복.
 *   0 이 되면 exhausted — max × recoverRatio 까지 차야 풀린다. exhausted 동안 이동 감속·강한 타 불가.
 * - 화살 탄창(ammo, 활): 한 발마다 1, 비면 자동 장전(reloadMs). 수동 장전은 탄창이 덜 찼을 때.
 * - 과열(heat, 단검): 공격마다 가열, 마지막 가열 뒤 decayDelayMs 가 지나면 식는다. 경계(stages)를 넘을 때마다
 *   단계 +1(공격 속도 배율 speedMults). 최대 열을 overheatHoldMs 동안 유지하면 과열 → cooldownMs 냉각(공격 불가).
 * 계약 §11.1 `UiWeaponResource` 로 내보낸다.
 */
import type { AmmoResourceDef, HeatResourceDef, StaminaResourceDef, WeaponResourceDef } from '../data/types';
import type { UiWeaponResource } from '../contract/ui';

export class WeaponResource {
  value: number;
  /** 기력: 바닥난 상태 */
  private exhausted = false;
  /** 기력: 마지막 소모 · 과열: 마지막 가열 */
  private lastUseAt = -Infinity;
  /** 탄창: 장전 시작 시각 (-1 = 장전 중 아님) */
  private reloadStart = -1;
  /** 과열: 최대 열 유지 누적 ms · 과열 시작 시각 (-1 = 아님) */
  private atMaxMs = 0;
  private overheatStart = -1;
  /** 과열 시작 순간의 열 (냉각 동안 선형으로 0 까지) */
  private overheatFrom = 0;

  constructor(readonly def: WeaponResourceDef) {
    this.value = def.kind === 'heat' ? 0 : def.max;
  }

  get kind(): WeaponResourceDef['kind'] {
    return this.def.kind;
  }

  get max(): number {
    return this.def.max;
  }

  /** 매 프레임. dtMs = 이번 프레임 길이 */
  tick(now: number, dtMs: number): void {
    const d = this.def;
    const dt = Math.max(0, dtMs);
    if (d.kind === 'stamina') {
      if (now - this.lastUseAt >= d.regenDelayMs && this.value < d.max)
        this.value = Math.min(d.max, this.value + (d.regenPerSec * dt) / 1000);
      if (this.exhausted && this.value >= d.max * d.recoverRatio) this.exhausted = false;
    } else if (d.kind === 'ammo') {
      if (this.reloadStart >= 0 && now - this.reloadStart >= d.reloadMs) {
        this.reloadStart = -1;
        this.value = d.max;
      }
    } else {
      this.tickHeat(d, now, dt);
    }
  }

  private tickHeat(d: HeatResourceDef, now: number, dt: number): void {
    if (this.overheatStart >= 0) {
      const p = (now - this.overheatStart) / d.cooldownMs;
      if (p >= 1) {
        this.overheatStart = -1;
        this.value = 0;
        this.atMaxMs = 0;
      } else this.value = this.overheatFrom * (1 - p);
      return;
    }
    if (now - this.lastUseAt >= d.decayDelayMs && this.value > 0)
      this.value = Math.max(0, this.value - (d.decayPerSec * dt) / 1000);
    if (this.value >= d.max) {
      this.atMaxMs += dt;
      if (this.atMaxMs >= d.overheatHoldMs) {
        this.overheatStart = now;
        this.overheatFrom = this.value;
        this.atMaxMs = 0;
      }
    } else this.atMaxMs = 0;
  }

  // --- 기력 ---

  /** 기력 소모. 0 에 닿으면 exhausted */
  spend(amount: number, now: number): void {
    if (this.def.kind !== 'stamina' || amount <= 0) return;
    this.lastUseAt = now;
    this.value = Math.max(0, this.value - amount);
    if (this.value <= 0) this.exhausted = true;
  }

  get isExhausted(): boolean {
    return this.def.kind === 'stamina' && this.exhausted;
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

  // --- 과열 ---

  /** 연격 n 번째 타(0부터) 가열 */
  heatUp(hitIndex: number, now: number): void {
    const d = this.def;
    if (d.kind !== 'heat' || this.overheatStart >= 0) return;
    const g = d.gainPerHit[Math.min(hitIndex, d.gainPerHit.length - 1)] ?? 0;
    this.lastUseAt = now;
    this.value = Math.min(d.max, this.value + g);
  }

  get overheated(): boolean {
    return this.def.kind === 'heat' && this.overheatStart >= 0;
  }

  /** 가열 단계 0..stages.length (과열 냉각 중엔 0) */
  get stage(): number {
    const d = this.def;
    if (d.kind !== 'heat' || this.overheatStart >= 0) return 0;
    let s = 0;
    for (const b of d.stages) if (this.value >= b) s++;
    return s;
  }

  /** 공격 속도 배율 (과열 단계) */
  get speedMult(): number {
    const d = this.def;
    if (d.kind !== 'heat') return 1;
    return d.speedMults[Math.min(this.stage, d.speedMults.length - 1)] ?? 1;
  }

  /** 냉각 진행도 0..1 */
  cooldownProgress(now: number): number {
    if (this.def.kind !== 'heat' || this.overheatStart < 0) return 0;
    return clamp01((now - this.overheatStart) / this.def.cooldownMs);
  }

  // --- 공통 ---

  /** 지금 공격(연격 한 타·화살 한 발)을 시작할 수 있는가 */
  canAttack(): boolean {
    if (this.def.kind === 'ammo') return this.canFire();
    if (this.def.kind === 'heat') return !this.overheated;
    return true;
  }

  /** 계약 §11.1 게이지 */
  toUi(now: number): UiWeaponResource {
    const d = this.def;
    const base = { kind: d.kind, label: d.label, max: d.max };
    if (d.kind === 'stamina') return { ...base, value: round1(this.value), state: staminaState(d, this) };
    if (d.kind === 'ammo') {
      if (this.reloading)
        return { ...base, value: Math.floor(this.value), state: 'reloading', progress: this.reloadProgress(now) };
      return { ...base, value: Math.floor(this.value), state: this.value <= d.lowCount ? 'low' : 'ok' };
    }
    if (this.overheated)
      return { ...base, value: round1(this.value), state: 'overheat', progress: this.cooldownProgress(now), stage: 0 };
    return { ...base, value: round1(this.value), state: 'ok', stage: this.stage };
  }

  /** 디버그 */
  debug(now: number): Record<string, unknown> {
    return {
      kind: this.kind,
      value: this.value,
      max: this.max,
      exhausted: this.isExhausted,
      reloading: this.reloading,
      overheated: this.overheated,
      stage: this.stage,
      speedMult: this.speedMult,
      atMaxMs: this.atMaxMs,
      ui: this.toUi(now),
    };
  }
}

function staminaState(d: StaminaResourceDef, r: WeaponResource): UiWeaponResource['state'] {
  if (r.isExhausted) return 'exhausted';
  return r.value < d.max * d.lowRatio ? 'low' : 'ok';
}

function clamp01(v: number): number {
  return Math.max(0, Math.min(1, v));
}

function round1(v: number): number {
  return Math.round(v * 10) / 10;
}

/** 타입 좁히기 도우미 (테스트·호출 쪽) */
export function isAmmo(d: WeaponResourceDef): d is AmmoResourceDef {
  return d.kind === 'ammo';
}
