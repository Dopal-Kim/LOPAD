/**
 * 61라운드 P6 보스 싸움 길이 추정 (순수). 목표 90~120초 (공격 5 · 무기 기본 공격 DPS — `systems/weapon/dps.ts`).
 *
 * 실효 DPS = DPS × [(1 − 파훼 비율) × 공격 비율 + 파훼 비율 × 파훼 중 공격 비율 × breakDamageMult]
 * - 공격 비율 = SIM.UPTIME.boss (근접) / bossRanged (활 — 거리를 두고 계속 쏜다)
 * - 파훼 비율·파훼 중 공격 비율 = SIM.BOSS_BREAK
 * 싸움 = 국면별 HP 몫 / 실효 DPS 합 + 국면 전환(무적 들이켜기·등불 끄기 예고) SIM.BOSS_PHASE_MS × (국면 − 1).
 * 연출(등장·처치) = show.intro.fightAtMs + show.defeat.rewardAtMs — 노드 길이에는 더하고 싸움 시간과는 따로 보인다.
 */
import { SIM } from '../../core/Constants';
import type { BossShowDef } from '../../data/bossShowTypes';

export interface BossSimDef {
  hp: number;
  phases: readonly { hpFraction: number }[];
  breakDamageMult?: number;
  show?: BossShowDef;
}

export interface BossFightEstimate {
  /** 실효 DPS */
  effectiveDps: number;
  /** 국면별 싸움 ms (전환 연출 제외) */
  byPhaseMs: number[];
  /** 싸움 ms (국면 전환 포함, 등장·처치 연출 제외) */
  fightMs: number;
  /** 등장 + 처치 연출 ms */
  showMs: number;
  /** 노드 안 보스 시간 = 싸움 + 연출 */
  totalMs: number;
}

export function bossEffectiveDps(dps: number, kind: 'melee' | 'ranged', breakMult = 1): number {
  const up = kind === 'ranged' ? SIM.UPTIME.bossRanged : SIM.UPTIME.boss;
  const B = SIM.BOSS_BREAK;
  return dps * ((1 - B.SHARE) * up + B.SHARE * B.UPTIME * breakMult);
}

export function estimateBossFight(dps: number, kind: 'melee' | 'ranged', boss: BossSimDef): BossFightEstimate {
  const eff = bossEffectiveDps(dps, kind, boss.breakDamageMult ?? 1);
  if (eff <= 0) return { effectiveDps: 0, byPhaseMs: [], fightMs: Infinity, showMs: 0, totalMs: Infinity };
  const fr = boss.phases.map((p) => p.hpFraction);
  const byPhaseMs = fr.map((f, i) => Math.round((((f - (fr[i + 1] ?? 0)) * boss.hp) / eff) * 1000));
  const fightMs = byPhaseMs.reduce((a, b) => a + b, 0) + (boss.phases.length - 1) * SIM.BOSS_PHASE_MS;
  const showMs = boss.show ? boss.show.intro.fightAtMs + boss.show.defeat.rewardAtMs : 0;
  return { effectiveDps: eff, byPhaseMs, fightMs, showMs, totalMs: fightMs + showMs };
}
