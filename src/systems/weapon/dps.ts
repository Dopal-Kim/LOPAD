/**
 * 61라운드 P2 수치 기준선: 무기 기본 공격(4동사 '좌')의 단일 대상 지속 DPS 추정 (Phaser 의존 없음, 순수 함수).
 * 기준 = 데이터 `weapons.rules.dpsBaseline` (공격 5 — 단검 21~23 · 칼 20 · 대검 19(+경직·범위) · 활 14~16). `dps.test.ts` 가 지킨다.
 *
 * 계산식 (GameCombat.rollDamage 와 같은 꼴, 패시브·구조물·빌드 배율 = 1):
 * - 한 타 피해 = round(공격 × 타 배율 × 무기 배율), 치명이면 round(… × 치명 배율). 기대값 = (1 − p) × 보통 + p × 치명,
 *   p = (기본 치명 + 무기 critBonus) / 100.
 * - 근접 한 바퀴 시간 = Σ 다음 타 허용(cancelFromMs) — 순환이 아닌 연격의 마지막 타는 durationMs + finisherRecoverMs (ComboTracker 와 같음).
 *   '지속' 속도 = 계속 이어 칠 때 도달하는 공속: 단검 가속 최대 단(speedMults 마지막) · 대검 관성 최대(1 + momentum.max). 칼은 1.
 * - 활 짧게 쏘기 = 탄창 한 통(resource.max 발 × ranged.cooldownMs) + 장전(reloadMs) 한 사이클. 연사 감쇠(rapidDecay)가 있으면 반영.
 * - 참고값: 활 완벽 놓기 반복(당김 fullMs + 놓기 releaseMs, 화살 미소모) — 기준선 밖(기술 상한).
 * 히트스톱·이동·적 경직은 넣지 않는다 (실측은 런 로그로).
 */
import type { ComboDef, WeaponDef } from '../../data/types';

export interface DpsOptions {
  attack: number;
  /** 기본 치명 확률 % (무기 critBonus 는 더한다) */
  crit?: number;
  /** 치명 피해 배율 (economy.critDamageMult) */
  critMult?: number;
}

export interface DpsEstimate {
  /** 단일 대상 지속 DPS */
  dps: number;
  /** 한 사이클 피해 기대값 · 시간 ms */
  cycleDamage: number;
  cycleMs: number;
  /** 지속 공속 배율 (단검 가속·대검 관성 최대) */
  speed: number;
}

/** 한 타 기대 피해 (게임처럼 타마다 정수 반올림) */
export function expectedHit(
  attack: number,
  mult: number,
  weaponMult: number,
  critChance: number,
  critMult: number,
): number {
  const base = attack * mult * weaponMult;
  const p = Math.min(1, Math.max(0, critChance));
  return (1 - p) * Math.round(base) + p * Math.round(base * critMult);
}

/** 연격 한 바퀴 시간 ms (공속 배율 speed 로 나눈다) */
export function comboCycleMs(c: ComboDef, speed = 1): number {
  const n = c.hits.length;
  let ms = 0;
  c.hits.forEach((h, i) => {
    ms += !c.loop && i === n - 1 ? h.durationMs + c.finisherRecoverMs : h.cancelFromMs;
  });
  return ms / Math.max(0.01, speed);
}

/** 계속 이어 칠 때의 공속 배율 (단검 가속 최대 단 · 대검 관성 최대) */
export function sustainedSpeed(def: WeaponDef): number {
  let k = 1;
  const r = def.resource;
  if (r?.kind === 'heat') k *= r.speedMults[r.speedMults.length - 1] ?? 1;
  const m = def.combo?.momentum;
  if (m) k *= 1 + m.max;
  return k;
}

function critOf(def: WeaponDef, o: DpsOptions): { p: number; mult: number } {
  return { p: ((o.crit ?? 0) + def.critBonus) / 100, mult: o.critMult ?? 1.5 };
}

/** 근접 연격 지속 DPS (연격이 없으면 0) */
export function meleeDps(def: WeaponDef, o: DpsOptions): DpsEstimate {
  const c = def.combo;
  if (!c || c.hits.length === 0) return { dps: 0, cycleDamage: 0, cycleMs: 0, speed: 1 };
  const { p, mult } = critOf(def, o);
  const speed = sustainedSpeed(def);
  const cycleDamage = c.hits.reduce((a, h) => a + expectedHit(o.attack, h.damageMult, def.damageMult, p, mult), 0);
  const cycleMs = comboCycleMs(c, speed);
  return { dps: (cycleDamage / cycleMs) * 1000, cycleDamage, cycleMs, speed };
}

/** 활 짧게 쏘기 지속 DPS (탄창 한 통 + 장전) */
export function bowTapDps(def: WeaponDef, o: DpsOptions): DpsEstimate {
  const R = def.ranged;
  const r = def.resource;
  if (!R) return { dps: 0, cycleDamage: 0, cycleMs: 0, speed: 1 };
  const { p, mult } = critOf(def, o);
  const shots = r?.kind === 'ammo' ? r.max : 1;
  const reload = r?.kind === 'ammo' ? r.reloadMs : 0;
  // 연사 감쇠: 간격이 창 안이면 발마다 rapidDecay 씩 rapidMin 까지 (한 통 안에서)
  const decays = R.cooldownMs <= R.rapidWindowMs && R.rapidDecay > 0;
  let cycleDamage = 0;
  for (let i = 0; i < shots; i++) {
    const k = decays ? Math.max(R.rapidMin, 1 - R.rapidDecay * i) : 1;
    cycleDamage += expectedHit(o.attack, k, def.damageMult, p, mult);
  }
  const cycleMs = shots * R.cooldownMs + reload;
  return { dps: (cycleDamage / cycleMs) * 1000, cycleDamage, cycleMs, speed: 1 };
}

/** 참고: 활 완벽 놓기 반복 DPS (당김 + 놓기, 화살 미소모 — 기술 상한) */
export function bowPerfectDps(def: WeaponDef, o: DpsOptions): DpsEstimate {
  const S = def.secondary;
  const D = def.draw;
  if (S.kind !== 'aimedshot' || !D) return { dps: 0, cycleDamage: 0, cycleMs: 0, speed: 1 };
  const { p, mult } = critOf(def, o);
  const cycleDamage = expectedHit(o.attack, S.damageMult * D.perfectDamageMult, def.damageMult, p, mult);
  const cycleMs = D.fullMs + D.releaseMs;
  return { dps: (cycleDamage / cycleMs) * 1000, cycleDamage, cycleMs, speed: 1 };
}

/** 무기 기본 공격(좌)의 지속 DPS — 근접 = 연격, 원거리 = 짧게 쏘기 */
export function baselineDps(def: WeaponDef, o: DpsOptions): DpsEstimate {
  return def.kind === 'ranged' ? bowTapDps(def, o) : meleeDps(def, o);
}
