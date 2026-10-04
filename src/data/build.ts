/**
 * 57라운드 빌드 축 1차 데이터 로더·검증 (index.ts 와 분리 — 병행 작업 충돌을 줄이려고 따로 둔다).
 * `data/build.json`(태그·세트·규칙 수치) · `data/dualTraits.json` · `data/curses.json` · `data/awakenings.json` +
 * `data/weapons.json` 갈래 노드의 태그·동작·규칙.
 */
import buildJson from '../../data/build.json';
import dualJson from '../../data/dualTraits.json';
import cursesJson from '../../data/curses.json';
import awakeningsJson from '../../data/awakenings.json';
import { WEAPONS } from './index';
import {
  TAG_IDS,
  isBuildStatKey,
  isTagId,
  type AwakeningDef,
  type BuildData,
  type CurseDef,
  type CursesData,
  type DualTraitDef,
  type SetThreshold,
  type TagId,
} from './buildTypes';
import type { WeaponEvolution, WeaponTable } from './types';

const THRESHOLDS: readonly SetThreshold[] = [2, 4, 6];

function fail(msg: string): never {
  throw new Error(`[data] ${msg}`);
}

function num(v: unknown, path: string): number {
  if (typeof v !== 'number' || Number.isNaN(v)) fail(`${path} 는 숫자여야 합니다 (받은 값: ${String(v)})`);
  return v;
}

export function validateBuild(b: BuildData): BuildData {
  const ids = b.tags.map((t) => t.id);
  if (ids.length !== TAG_IDS.length || !TAG_IDS.every((t) => ids.includes(t)))
    fail(`build.tags 는 ${TAG_IDS.join('·')} ${TAG_IDS.length}개`);
  for (const t of b.tags) if (!t.name) fail(`build.tags.${t.id}.name 없음`);
  const S = b.scoring;
  for (const k of ['perPassive', 'passiveMaxLevelBonus', 'perBranchNode', 'reinforceTagMax'] as const)
    num(S[k], `build.scoring.${k}`);
  if (S.reinforceTagTarget !== 'primary' && S.reinforceTagTarget !== 'all')
    fail('build.scoring.reinforceTagTarget 는 primary | all');
  if (JSON.stringify(S.thresholds) !== JSON.stringify(THRESHOLDS)) fail('build.scoring.thresholds 는 [2, 4, 6]');
  for (const tag of TAG_IDS) {
    const stages = b.sets[tag];
    if (!Array.isArray(stages) || stages.length !== 3) fail(`build.sets.${tag} 는 3단계`);
    stages.forEach((st, i) => {
      const at = `build.sets.${tag}[${i}]`;
      if (st.threshold !== THRESHOLDS[i]) fail(`${at}.threshold 는 ${THRESHOLDS[i]}`);
      if (!st.name || !st.description) fail(`${at}.name·description 없음`);
      if (!st.effect || typeof st.effect.kind !== 'string') fail(`${at}.effect.kind 없음`);
      if (st.effect.kind === 'stat') {
        const stats = st.effect.stats ?? {};
        if (Object.keys(stats).length === 0) fail(`${at}.effect.stats 비어 있음`);
        for (const [k, v] of Object.entries(stats)) {
          if (!isBuildStatKey(k)) fail(`${at}.effect.stats.${k} 알 수 없음`);
          num(v, `${at}.effect.stats.${k}`);
        }
      }
    });
  }
  num(b.events.perfectEvadeWindowMs, 'build.events.perfectEvadeWindowMs');
  num(b.events.perfectEvadeThreatRadiusTiles, 'build.events.perfectEvadeThreatRadiusTiles');
  num(b.events.crisisHpRatio, 'build.events.crisisHpRatio');
  for (const k of ['repeatThreshold', 'reinforceMaxAwakened', 'pactBenefitMult', 'pactExtraNodes'] as const)
    num(b.evolve[k], `build.evolve.${k}`);
  num(b.awaken.tagScore, 'build.awaken.tagScore');
  num(b.awaken.afterBossFloor, 'build.awaken.afterBossFloor');
  num(b.personality.normalKillMult, 'build.personality.normalKillMult');
  num(b.pool.themeWeightMult, 'build.pool.themeWeightMult');
  for (const k of ['bossChoices', 'chestChoices', 'nodeChoices'] as const)
    num(b.acquisition[k], `build.acquisition.${k}`);
  num(b.dual.tier1Score, 'build.dual.tier1Score');
  num(b.dual.tier2Score, 'build.dual.tier2Score');
  for (const [k, v] of Object.entries(b.drunk.liquorPool)) if (k !== '_note') num(v, `build.drunk.liquorPool.${k}`);
  return b;
}

/** 무기 갈래 노드 (1단 2 → 1단마다 2단 2 = 무기당 6, 57 Q22): 태그 1~2개, 1단은 새 동작(move) */
export function validateBranchNodes(weapons: WeaponTable): void {
  for (const [wid, w] of Object.entries(weapons)) {
    const visit = (n: WeaponEvolution, depth: number) => {
      const at = `weapons.${wid}.personality ${n.id}`;
      if (!Array.isArray(n.tags) || n.tags.length < 1 || n.tags.length > 2 || !n.tags.every(isTagId))
        fail(`${at}.tags 는 태그 1~2개`);
      if (depth === 1 && typeof n.move !== 'string') fail(`${at}: 1단 노드는 move(새 동작) 필요`);
      if (depth === 2 && !n.rule && Object.keys(n.mods).length === 0) fail(`${at}: 2단 노드는 rule 또는 mods 필요`);
      for (const c of n.comboChange ?? []) num(c.index, `${at}.comboChange.index`);
      for (const c of n.next ?? []) visit(c, depth + 1);
    };
    for (const b of w.personality.branches) visit(b, 1);
  }
}

/** 갈래 id → 노드 (무기 안) */
export function findBranch(
  weapons: WeaponTable,
  weapon: string,
  id: string,
): { node: WeaponEvolution; depth: number } | null {
  const w = weapons[weapon];
  if (!w) return null;
  for (const a of w.personality.branches) {
    if (a.id === id) return { node: a, depth: 1 };
    for (const b of a.next ?? []) if (b.id === id) return { node: b, depth: 2 };
  }
  return null;
}

export function validateDualTraits(items: DualTraitDef[], weapons: WeaponTable): DualTraitDef[] {
  const ids = new Set<string>();
  for (const d of items) {
    const at = `dualTraits.${d.id}`;
    if (ids.has(d.id)) fail(`dualTraits 중복 id: ${d.id}`);
    ids.add(d.id);
    if (!d.name || !d.description) fail(`${at}.name·description 없음`);
    if (!isTagId(d.tag)) fail(`${at}.tag 알 수 없음`);
    const b = findBranch(weapons, d.weapon, d.branch);
    if (!b) fail(`${at}: ${d.weapon} 에 갈래 ${d.branch} 없음`);
    if (!d.effect || typeof d.effect.kind !== 'string') fail(`${at}.effect.kind 없음`);
  }
  // 57 Q27: 1단 8 + 2단 16 (+ 취기 짝 무기당 1)
  for (const [wid, w] of Object.entries(weapons))
    for (const a of w.personality.branches) {
      if (!items.some((d) => d.weapon === wid && d.branch === a.id && d.tag !== 'drunk'))
        fail(`dualTraits: ${wid}.${a.id} 짝 없음`);
      for (const b of a.next ?? [])
        if (!items.some((d) => d.weapon === wid && d.branch === b.id)) fail(`dualTraits: ${wid}.${b.id} 짝 없음`);
    }
  return items;
}

export function validateCurses(c: CursesData): CursesData {
  const ids = new Set<string>();
  for (const d of c.items) {
    const at = `curses.${d.id}`;
    if (ids.has(d.id)) fail(`curses 중복 id: ${d.id}`);
    ids.add(d.id);
    if (!d.name || !d.benefit || !d.penalty) fail(`${at}.name·benefit·penalty 없음`);
    if ((d.nodes === undefined) === (d.kills === undefined)) fail(`${at}: nodes 또는 kills 중 하나`);
    if (d.nodes !== undefined) num(d.nodes, `${at}.nodes`);
    if (d.kills !== undefined) num(d.kills, `${at}.kills`);
    for (const t of Object.keys({ ...d.benefits.tagBonus, ...d.benefits.permanentTag }))
      if (!isTagId(t)) fail(`${at}: 태그 ${t} 알 수 없음`);
  }
  for (const id of c.pactPool) if (!ids.has(id)) fail(`curses.pactPool: ${id} 없음`);
  return c;
}

export function validateAwakenings(
  t: Record<string, AwakeningDef>,
  weapons: WeaponTable,
): Record<string, AwakeningDef> {
  for (const [wid, w] of Object.entries(weapons)) {
    const a = t[wid];
    if (!a) fail(`awakenings.${wid} 없음 (무기당 1종)`);
    if (!a.name || !a.common || typeof a.common.kind !== 'string') fail(`awakenings.${wid}.name·common 없음`);
    for (const b of w.personality.branches)
      for (const c of b.next ?? []) if (!a.rules[c.id]) fail(`awakenings.${wid}.rules.${c.id} 없음 (2단별 규칙)`);
  }
  return t;
}

export const BUILD: BuildData = validateBuild(buildJson as unknown as BuildData);
validateBranchNodes(WEAPONS);
export const DUAL_TRAITS: readonly DualTraitDef[] = validateDualTraits(
  (dualJson as unknown as { items: DualTraitDef[] }).items,
  WEAPONS,
);
export const CURSES: CursesData = validateCurses(cursesJson as unknown as CursesData);
export const AWAKENINGS: Record<string, AwakeningDef> = validateAwakenings(
  (awakeningsJson as unknown as { items: Record<string, AwakeningDef> }).items,
  WEAPONS,
);

export function tagName(id: TagId): string {
  return BUILD.tags.find((t) => t.id === id)?.name ?? id;
}

export function curseDef(id: string): CurseDef | undefined {
  return CURSES.items.find((c) => c.id === id);
}

/** 층(1부터)의 테마 태그 (1층 = 취기). 없으면 null */
export function themeTagOf(floor: number): TagId | null {
  return BUILD.tags.find((t) => t.themeFloor === floor)?.id ?? null;
}
