/**
 * P19 자유 전투 타격 반응 규칙 (방향 문서 ④B · 계약 free-combat §1). Phaser 의존 없음(테스트 가능).
 * - 넉백 단계 함수 `strikeReaction`: 공격 모양(연격 번호·막타·동작·차지·활 완벽 놓기) + 무기 '반응 모양'(weapons.json feel.reaction) → 단계·띄움·버팀 힘
 * - 버팀 `overcomesPoise`: 힘 > 버팀이면 움찔(200ms, 예고 끊음)
 * - 벽꽝·볼링 피해, 낙하 판정, 연속 처치 셈
 * 적용(물리·이벤트)은 씬 `scenes/game/HitReactions`.
 */
import { REACTION } from '../core/Constants';
import type { KnockTier } from '../core/eventsP19';
import type { WeaponReactionDef } from '../data/types';

/** 한 타의 반응 (hitMob 이 받는다) */
export interface StrikeReaction {
  tier: KnockTier;
  /** 띄움 (넉백 대신 제자리 공중) */
  launch: boolean;
  /** 버팀을 깎는 힘 (단계 + 무기 버팀 무시) */
  power: number;
  /** 띄울 수 있는 버팀 상한 (징집병·사수만 = 0) */
  launchMaxPoise: number;
}

/** 공격 모양 (PlayerAttackPayload 에서 필요한 것만) */
export interface StrikeShapeInfo {
  kind: string;
  comboIndex?: number;
  heavy?: boolean;
  move?: string;
  charge?: number;
  bowPower?: string;
}

const clampTier = (n: number): KnockTier => Math.max(1, Math.min(4, Math.round(n))) as KnockTier;

/**
 * 넉백 단계 함수: 강한 동작(차지·def.strongMoves) → strongTier(3) · 활 완벽 놓기 → perfectTier · 막타·대쉬 공격 → heavyTier(2) ·
 * 연격 타 → comboTiers[번호](1). 띄움 = launchCombo(연격 번호)·launchMoves(동작 id)
 */
export function strikeReaction(def: WeaponReactionDef | undefined, s: StrikeShapeInfo): StrikeReaction {
  const d = def ?? {};
  let tier: number;
  if (s.charge !== undefined || (s.move !== undefined && (d.strongMoves ?? []).includes(s.move)))
    tier = d.strongTier ?? 3;
  else if (s.bowPower === 'perfect') tier = d.perfectTier ?? 2;
  else if (s.heavy || s.kind === 'dashAttack') tier = d.heavyTier ?? 2;
  else tier = (s.comboIndex !== undefined ? d.comboTiers?.[s.comboIndex] : undefined) ?? 1;
  const launch =
    (s.move === undefined && s.comboIndex !== undefined && (d.launchCombo ?? []).includes(s.comboIndex)) ||
    (s.move !== undefined && (d.launchMoves ?? []).includes(s.move));
  const t = clampTier(tier);
  return { tier: t, launch, power: t + (d.poisePierce ?? 0), launchMaxPoise: d.launchMaxPoise ?? 0 };
}

/** 데이터 없이 들어온 타격(개성·환경·틱)의 기본 반응: 막타 2, 그 밖 1 */
export function defaultReaction(heavy: boolean): StrikeReaction {
  const tier: KnockTier = heavy ? 2 : 1;
  return { tier, launch: false, power: tier, launchMaxPoise: 0 };
}

/** 넉백 거리 px: 단계 거리 × (보스 ¼ · 정예 ½) × 추가 배율. 1단계만 무기 무게(feel.knockbackMult)를 곱한다 */
export function knockDistancePx(
  tier: KnockTier,
  tilePx: number,
  o: { boss?: boolean; elite?: boolean; weaponMult?: number; mult?: number } = {},
): number {
  const base = REACTION.KNOCK[tier].TILES * tilePx;
  const w = tier === 1 ? (o.weaponMult ?? 1) : 1;
  return base * w * (o.mult ?? 1) * (o.boss ? REACTION.BOSS_MULT : 1) * (o.elite ? REACTION.ELITE_MULT : 1);
}

export function knockMs(tier: KnockTier): number {
  return REACTION.KNOCK[tier].MS;
}

/** 버팀: 정예는 ×ELITE_POISE_MULT */
export function effectivePoise(poise: number, elite: boolean): number {
  return poise * (elite ? REACTION.ELITE_POISE_MULT : 1);
}

/** 힘이 버팀을 넘는가 (넘으면 움찔) */
export function overcomesPoise(power: number, poise: number): boolean {
  return power > poise;
}

/** 벽꽝 추가 피해: 그 타 피해 × DAMAGE_RATIO × 속도비(MIN_SPEED_RATIO ~ 1). 최소 1 */
export function wallSlamDamage(hitDamage: number, speedRatio: number): number {
  const W = REACTION.WALL_SLAM;
  const k = Math.max(W.MIN_SPEED_RATIO, Math.min(1, speedRatio));
  return Math.max(1, Math.round(hitDamage * W.DAMAGE_RATIO * k));
}

/** 볼링 피해 (둘 다): 그 타 피해 × DAMAGE_RATIO. 최소 1 */
export function bowlDamage(hitDamage: number): number {
  return Math.max(1, Math.round(hitDamage * REACTION.BOWL.DAMAGE_RATIO));
}

/** 밀어 떨어뜨리기: 일반 적 즉사 · 정예 HP 30% 피해 후 문 근처로 · 보스 해당 없음 */
export function fallOutcome(m: { isBoss: boolean; elite: boolean }): 'die' | 'elite' | 'none' {
  if (m.isBoss) return 'none';
  return m.elite ? 'elite' : 'die';
}

/** 띄움 체공: 공중 적을 치면 +EXTEND_MS (MAX_EXTENDS 번까지). 반환 = 새 착지 시각 (늘리지 못하면 그대로) */
export function extendAir(air: { until: number; extends: number }): { until: number; extends: number } {
  const L = REACTION.LAUNCH;
  if (air.extends >= L.MAX_EXTENDS) return air;
  return { until: air.until + L.EXTEND_MS, extends: air.extends + 1 };
}

/** 연속 처치 셈: 처치 사이 ≤ WINDOW_MS 면 이어진다 */
export class StreakCounter {
  private count = 0;
  private lastAt = -Infinity;

  /** 처치 1회 → 지금 연속 수 */
  onKill(now: number): number {
    this.count = now - this.lastAt <= REACTION.STREAK.WINDOW_MS ? this.count + 1 : 1;
    this.lastAt = now;
    return this.count;
  }

  reset(): void {
    this.count = 0;
    this.lastAt = -Infinity;
  }
}
