/**
 * 61라운드 P9 헤드리스 수치 추정 (순수 — Phaser·물리 없음). 피해 공식·적 HP·무기 연격 데이터로 노드 하나의 길이·처치·받는 피해를 어림한다.
 * 1층 길이(P3 목표 10~12분·노드당 처치 12~16)와 무기 DPS 기준선(P2) 점검용. 가정값은 `SIM`(core/constants/settings) — 런 로그 실측으로 맞춘다.
 *
 * 모델
 * - 무기 DPS·타 피해 = 무기 쪽 기준선 `systems/weapon/dps.ts`(baselineDps·expectedHit·sustainedSpeed·bowTapDps) 그대로
 * - 근접: 적마다 연격 1타부터, 타 간격 = cancelFromMs (마지막 타는 durationMs + finisherRecoverMs, 순환 연격은 계속 cancelFromMs) ÷ 지속 공속.
 *   한 휘두름이 맞히는 적 수 = 1 + 호/360 × CROWD_DENSITY (웨이브 평균 생존 수 상한). 방패 적은 정면 비율만큼 감소.
 * - 활: 짧게 쏘기 한 발 = 탄창 한 통 + 장전 사이클의 평균.
 * - 실제 전투 시간 = 처치 시간 합 / 공격 비율(UPTIME) + 자리 잡기·추격 + 첫 접근.
 * - 받는 피해 = Σ 적 생존 시간 / 공격 간격 × 맞는 비율 × max(1, 적 공격 × 층 배율 − 방어).
 */
import { ENEMY_INCOMING, ROUTE_FX, SIM, TILE } from '../../core/Constants';
import type { EnemyDef, WaveEntry, WeaponDef } from '../../data/types';
import { baselineDps, bowTapDps, expectedHit, sustainedSpeed } from '../weapon/dps';

/** 무기 데이터 그대로 (DPS 는 무기 쪽 `systems/weapon/dps.ts` 기준선과 같은 식) */
export type SimWeapon = WeaponDef;

export interface SimPlayer {
  attack: number;
  defense: number;
  /** 치명 확률 % (무기 critBonus 제외) */
  crit: number;
  critDamageMult: number;
  /** 이동 속도 (칸/초) */
  speedTiles: number;
}

export interface WeaponDpsEstimate {
  kind: 'melee' | 'ranged';
  /** 한 사이클(연격 한 바퀴·화살 한 발)의 평균 타 피해 */
  avgHit: number;
  /** 단일 대상 지속 DPS (자리 잡기·공격 비율 미반영) */
  dps: number;
  /** 휘두름 하나가 맞히는 적 수 (최대) */
  targets: number;
}

export interface NodeEstimate {
  kills: number;
  /** 노드 진입 → 다음 노드 고르기까지 (ms) */
  totalMs: number;
  combatMs: number;
  /** 받는 피해 기대값 */
  damageTaken: number;
  /** 처치 개성 (일반 처치 배율 반영) · 전표 */
  personality: number;
  gold: number;
  waves: { enemies: number; ms: number; damageTaken: number }[];
}

function dpsOpts(p: SimPlayer) {
  return { attack: p.attack, crit: p.crit, critMult: p.critDamageMult };
}

/**
 * 근접 연격 타 목록: 기대 피해 · 다음 타까지 ms. 타 간격은 `comboCycleMs` 와 같은 규칙에 지속 공속(단검 가속 최대 단·대검 관성 최대,
 * `sustainedSpeed`)을 나눈다 — 기준선 DPS 와 일치
 */
export function meleeSequence(p: SimPlayer, w: SimWeapon): { dmg: number; ms: number }[] {
  const c = w.combo;
  if (!c || c.hits.length === 0) return [];
  const speed = Math.max(0.01, sustainedSpeed(w));
  const chance = (p.crit + w.critBonus) / 100;
  return c.hits.map((h, i) => ({
    dmg: expectedHit(p.attack, h.damageMult, w.damageMult, chance, p.critDamageMult),
    ms: (i < c.hits.length - 1 || c.loop ? h.cancelFromMs : h.durationMs + c.finisherRecoverMs) / speed,
  }));
}

/** 활 한 발 평균 (짧게 쏘기 기준선 `bowTapDps` 한 사이클 = 탄창 한 통 + 장전, 연사 감쇠 포함) */
export function bowShot(p: SimPlayer, w: SimWeapon): { dmg: number; ms: number } {
  const e = bowTapDps(w, dpsOpts(p));
  const shots = w.resource?.kind === 'ammo' ? Math.max(1, w.resource.max) : 1;
  return { dmg: e.cycleDamage / shots, ms: e.cycleMs / shots };
}

export function weaponDps(p: SimPlayer, w: SimWeapon): WeaponDpsEstimate {
  const e = baselineDps(w, dpsOpts(p));
  if (w.kind !== 'ranged' && w.combo && w.combo.hits.length > 0)
    return {
      kind: 'melee',
      avgHit: e.cycleDamage / w.combo.hits.length,
      dps: e.dps,
      targets: 1 + ((w.combo.arcDeg ?? 0) / 360) * SIM.CROWD_DENSITY,
    };
  if (w.ranged) return { kind: 'ranged', avgHit: bowShot(p, w).dmg, dps: e.dps, targets: 1 };
  return { kind: 'melee', avgHit: 0, dps: 0, targets: 1 };
}

/** 단일 대상 처치 시간 (ms, 연격 1타부터 — 공격 비율 미반영). dmgMult = 방패 등 받는 피해 배율 */
export function timeToKill(p: SimPlayer, w: SimWeapon, hp: number, dmgMult = 1): number {
  const seq =
    w.kind !== 'ranged' && w.combo && w.combo.hits.length > 0 ? meleeSequence(p, w) : w.ranged ? [bowShot(p, w)] : [];
  if (seq.length === 0 || hp <= 0) return Infinity;
  let left = hp;
  let ms = 0;
  for (let i = 0; i < 1000; i++) {
    const s = seq[i % seq.length];
    left -= Math.max(1, s.dmg * dmgMult);
    if (left <= 0) {
      // 마지막 타는 판정까지만 — 간격 대신 그 타의 절반(판정 시점 근사)
      return ms + s.ms / 2;
    }
    ms += s.ms;
  }
  return ms;
}

export interface NodeSimInput {
  player: SimPlayer;
  weapon: SimWeapon;
  enemies: Record<string, EnemyDef>;
  waves: readonly (readonly WaveEntry[])[];
  enemyScale: { hp: number; attack: number };
  /** 웨이브 스폰 최소 거리 (칸) */
  spawnDistTiles: number;
  /** 일반 처치 개성 배율 (BUILD.personality.normalKillMult) */
  personalityKillMult?: number;
}

/** 전투 노드 하나 */
export function estimateBattleNode(input: NodeSimInput): NodeEstimate {
  const { player: p, weapon: w, enemies } = input;
  const dps = weaponDps(p, w);
  const uptime = dps.kind === 'ranged' ? SIM.UPTIME.ranged : SIM.UPTIME.melee;
  const waves: NodeEstimate['waves'] = [];
  let kills = 0;
  let personality = 0;
  let gold = 0;
  for (const wave of input.waves) {
    const list: EnemyDef[] = [];
    for (const e of wave) for (let i = 0; i < e.count; i++) if (enemies[e.enemy]) list.push(enemies[e.enemy]);
    if (list.length === 0) continue;
    const n = list.length;
    // 첫 접근: 스폰 거리 → 사거리까지, 플레이어·가장 빠른 근접 적이 서로 다가감 (원거리 무기는 거의 없음)
    const fastest = Math.max(...list.map((e) => (e.behavior === 'ranged' ? 0 : e.speedTiles)));
    const engageMs =
      dps.kind === 'ranged'
        ? 0
        : (Math.max(0, input.spawnDistTiles - SIM.ENGAGE_RANGE_TILES) / Math.max(0.1, p.speedTiles + fastest)) * 1000;
    const targets = Math.max(1, Math.min(dps.targets, (n + 1) / 2));
    // 처치 순서: 약한 적부터 (실제로는 다가오는 순)
    const ttks = list
      .map((e) => {
        const hp = Math.round(e.hp * input.enemyScale.hp);
        const shield = e.shield ? 1 - e.shield.reduction * SIM.SHIELD_FRONT_SHARE : 1;
        const chase = dps.kind === 'melee' && e.behavior === 'ranged' ? SIM.CHASE_RANGED_MS : 0;
        return { e, ms: timeToKill(p, w, hp, shield) / uptime / targets + SIM.REPOSITION_MS + chase };
      })
      .sort((a, b) => a.ms - b.ms);
    let t = engageMs;
    let dmgTaken = 0;
    for (const k of ttks) {
      t += k.ms;
      // 이 적은 웨이브 시작부터 t 까지 살아 있다
      const atk = Math.max(1, Math.round(k.e.attack * input.enemyScale.attack) - p.defense);
      dmgTaken += (t / k.e.attackIntervalMs) * SIM.HIT_RATE * atk;
      personality += k.e.personalityValue * (input.personalityKillMult ?? 1);
      gold += k.e.gold;
    }
    kills += n;
    const ms = ENEMY_INCOMING.WAVE_DELAY_MS + t;
    waves.push({ enemies: n, ms: Math.round(ms), damageTaken: Math.round(dmgTaken) });
  }
  const combatMs = waves.reduce((a, x) => a + x.ms, 0);
  const overhead = ROUTE_FX.ENTER_LOCK_MS + ROUTE_FX.EXIT_DELAY_MS + SIM.EXIT_WALK_MS + SIM.CHOOSE_MS;
  return {
    kills,
    totalMs: Math.round(combatMs + overhead),
    combatMs: Math.round(combatMs),
    damageTaken: waves.reduce((a, x) => a + x.damageTaken, 0),
    personality: Math.round(personality),
    gold,
    waves,
  };
}

/** 보스 노드 시간 (ms): HP / (단일 DPS × 보스 공격 비율) + 국면 전환 연출 */
export function estimateBossMs(p: SimPlayer, w: SimWeapon, boss: { hp: number; phases: unknown[] }): number {
  const d = weaponDps(p, w).dps;
  if (d <= 0) return Infinity;
  return Math.round((boss.hp / (d * SIM.UPTIME.boss)) * 1000 + (boss.phases.length - 1) * SIM.BOSS_PHASE_MS);
}

/** 플레이어 기본값 (공격·방어·치명 = player.json, 치명 배율 = economy) */
export function simPlayerOf(
  stats: { attack: number; defense: number; crit: number; speedTiles: number },
  critDamageMult: number,
): SimPlayer {
  return { ...stats, critDamageMult };
}

/** 전투 노드 개수별 칸 → px (디버그 출력용) */
export const tilesToPx = (t: number): number => t * TILE;
