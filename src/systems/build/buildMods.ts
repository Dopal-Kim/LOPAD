/**
 * 57라운드 빌드 축 합산 (Phaser 의존 없음): 태그 점수 → 세트 단계 → 수치(stats 합) + 사건 규칙(rules) 목록.
 * 원천: 패시브(effects·byLevel·rule) · 세트(2/4/6 누적) · 갈래 노드 규칙(1차 갈래·2차 길) · 개성 카드(61 G P12) · 저주(이득·대가).
 * 원칙(설계안 0.3): 갈래는 '하는 일', 패시브는 '수치', 세트는 '규칙'. 실행은 씬 쪽 `BuildRuntime`.
 */
import {
  BUILD_STAT_KEYS,
  TAG_IDS,
  ruleParams,
  type BuildData,
  type BuildStatKey,
  type RuleDef,
  type SetThreshold,
  type TagId,
} from '../../data/buildTypes';
import type { WeaponEvolution } from '../../data/types';
import type { TraitDef } from '../../data/growthTypes';
import { onFloor, type FloorScope } from '../../data/floorScope';
import type { PassiveSet } from '../passives';
import { scaledBenefit, type CurseState } from './curses';
import { setStage, tagScores, type TagScores } from './tagScore';

export type RuleSource = 'set' | 'passive' | 'trait' | 'branch' | 'curse';

export interface ActiveRule {
  kind: string;
  params: Record<string, unknown>;
  /** 패시브 레벨 (그 밖은 1) */
  level: number;
  source: RuleSource;
  /** 원천 id (패시브 id · 태그 id · 개성 id · 노드 id …) */
  id: string;
}

export interface BuildFlags {
  /** 대쉬·그림자 걸음 불가 (맨손 맹세) */
  noDash: boolean;
  /** 물약 사용 불가 (깨진 잔) */
  noPotion: boolean;
  /** 취기 상태 유지 (만취 서약 — QC-8) */
  drunkAlways: boolean;
  /** 피격 시 HP 비율 손실 (저주 궤짝) — 0 이면 없음 */
  hitHpLoss: number;
  /** 그로기 ms 덮어쓰기 (피멍 — 0 이면 없음) */
  groggyMs: number;
  /** 과열 식힘·재장전 배율 (피멍 — 1 이면 없음) */
  coolMult: number;
}

export interface BuildMods {
  scores: TagScores;
  stages: Record<TagId, 0 | SetThreshold>;
  stats: Record<BuildStatKey, number>;
  rules: ActiveRule[];
  flags: BuildFlags;
}

export interface BuildModsInput {
  data: BuildData;
  passives: PassiveSet;
  /** 갈래 경로 노드 */
  nodes: readonly WeaponEvolution[];
  /** 61 G P12: 얻은 개성 카드 (규칙 + 태그 점수) */
  traits: readonly TraitDef[];
  curse: CurseState | null;
  /** 영구 태그 보너스 (불붙은 혀) */
  permanentTags: Partial<Record<TagId, number>>;
  /** 61라운드 P4 층 노출: 이 층에서 꺼진 태그는 점수 0, 꺼진 세트 단계(1층판 6단계)는 켜지지 않는다. 없거나 null = 제한 없음 */
  floor?: FloorScope;
}

function zeroStats(): Record<BuildStatKey, number> {
  const out = {} as Record<BuildStatKey, number>;
  for (const k of BUILD_STAT_KEYS) out[k] = 0;
  return out;
}

function addRule(out: ActiveRule[], rule: RuleDef, source: RuleSource, id: string, level = 1): void {
  out.push({ kind: rule.kind, params: ruleParams(rule), level, source, id });
}

export function computeBuildMods(i: BuildModsInput): BuildMods {
  const D = i.data;
  const curse = i.curse;
  const curseDef = curse?.def ?? null;
  const pactMult = D.pact.benefitMult;
  // 태그 점수: 패시브 · 갈래 · 강화 · 영구 · 저주 이득(만취 서약 취기 +1)
  const passiveList = Object.entries(i.passives.owned)
    .map(([id, level]) => ({ def: i.passives.def(id), level }))
    .filter((p): p is { def: NonNullable<ReturnType<PassiveSet['def']>>; level: number } => Boolean(p.def));
  const extra: Partial<Record<TagId, number>>[] = [i.permanentTags];
  for (const t of i.traits) extra.push({ [t.tag]: D.scoring.perTrait });
  if (curseDef?.benefits.tagBonus) extra.push(curseDef.benefits.tagBonus);
  const scores = tagScores(
    {
      passives: passiveList.map((p) => ({ tags: p.def.tags, level: p.level, maxLevel: i.passives.maxLevel })),
      branchNodes: i.nodes,
      extra,
    },
    D.scoring,
  );
  const floor = i.floor ?? null;
  const stages = {} as Record<TagId, 0 | SetThreshold>;
  for (const t of TAG_IDS) {
    if (
      !onFloor(
        D.tags.find((d) => d.id === t),
        floor,
      )
    )
      scores[t] = 0;
    const allowed = D.scoring.thresholds.filter((th) =>
      onFloor(
        D.sets[t].find((st) => st.threshold === th),
        floor,
      ),
    );
    stages[t] = setStage(scores[t], allowed);
  }

  const stats = zeroStats();
  const rules: ActiveRule[] = [];
  // 패시브
  for (const k of BUILD_STAT_KEYS) stats[k] += i.passives.total(k);
  for (const r of i.passives.rules()) addRule(rules, r.rule, 'passive', r.def.id, r.level);
  // 세트 (2/4/6 누적)
  for (const t of TAG_IDS) {
    for (const st of D.sets[t]) {
      if (stages[t] < st.threshold || !onFloor(st, floor)) continue;
      if (st.effect.kind === 'stat') {
        for (const [k, v] of Object.entries(st.effect.stats ?? {})) stats[k as BuildStatKey] += v ?? 0;
      } else addRule(rules, st.effect, 'set', `${t}${st.threshold}`);
    }
  }
  // 갈래 노드 규칙 (1차 갈래 · 2차 길)
  for (const n of i.nodes) if (n.rule) addRule(rules, n.rule, 'branch', n.id);
  // 개성 카드 (61 G P12)
  for (const t of i.traits) addRule(rules, t.effect, 'trait', t.id);
  // 저주 (이득은 피의 계약이면 ×pactMult)
  const flags: BuildFlags = {
    noDash: false,
    noPotion: false,
    drunkAlways: false,
    hitHpLoss: 0,
    groggyMs: 0,
    coolMult: 1,
  };
  if (curseDef && curse) {
    const B = curseDef.benefits;
    const P = curseDef.penalties;
    if (B.attackMult) stats.attackMult += scaledBenefit(B.attackMult, curse.pact, pactMult);
    if (B.drunkAlways) flags.drunkAlways = true;
    if (P.damageTakenMult) stats.damageTakenMult += P.damageTakenMult;
    if (P.killGoldMult !== undefined) stats.killGoldMult += P.killGoldMult - 1;
    if (P.shopPriceMult) stats.shopPriceMult += P.shopPriceMult;
    if (P.noPotion) flags.noPotion = true;
    if (P.noDash) flags.noDash = true;
    if (P.hitHpLoss) flags.hitHpLoss = P.hitHpLoss;
    if (P.groggyMs) flags.groggyMs = P.groggyMs;
    if (P.coolMult) flags.coolMult = P.coolMult;
  }
  return { scores, stages, stats, rules, flags };
}

/** 이 종류의 규칙들 */
export function rulesOf(m: BuildMods, kind: string): ActiveRule[] {
  return m.rules.filter((r) => r.kind === kind);
}

/** 이 종류의 첫 규칙 (없으면 null) */
export function ruleOf(m: BuildMods, kind: string): ActiveRule | null {
  return m.rules.find((r) => r.kind === kind) ?? null;
}

/** 숫자 인자 (배열이면 규칙 레벨 칸) */
export function param(r: ActiveRule, key: string, fallback = 0): number {
  const v = r.params[key];
  if (Array.isArray(v)) return Number(v[Math.max(0, Math.min(v.length - 1, r.level - 1))]) || fallback;
  return typeof v === 'number' ? v : fallback;
}
