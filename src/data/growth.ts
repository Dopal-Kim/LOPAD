/**
 * 61라운드 단계 4 P12 무기 성장 데이터 로더·검증 (`data/growth.json` 눈금·갈래·길 · `data/traits.json` 개성 카드).
 * 갈래·길 id = art §26 (화면·그림), node = weapons.json 갈래 트리 노드 id (규칙·동작은 노드에). Phaser 의존 없음.
 */
import growthJson from '../../data/growth.json';
import traitsJson from '../../data/traits.json';
import { WEAPONS } from './index';
import { BUILD, findBranch } from './build';
import { byFloor, type FloorScope } from './floorScope';
import { isTagId } from './buildTypes';
import type { WeaponTable, WeaponVerbSlot } from './types';
import {
  GROWTH_MARK_KINDS,
  type GrowthBranchDef,
  type GrowthData,
  type GrowthMarkDef,
  type GrowthPathDef,
  type TraitDef,
} from './growthTypes';

const VERBS: readonly WeaponVerbSlot[] = ['attack', 'signature', 'dash', 'hold'];

function fail(msg: string): never {
  throw new Error(`[data] ${msg}`);
}

/** 화면 문구 규칙 (P12 '수치·내부 용어 금지'): 숫자·퍼센트·배율 기호가 없다 */
export function plainLine(s: string): boolean {
  return typeof s === 'string' && s.length > 0 && !/[0-9%×+]/.test(s);
}

export function validateGrowth(g: GrowthData, weapons: WeaponTable): GrowthData {
  for (const [floor, marks] of Object.entries(g.marks)) {
    if (!Array.isArray(marks) || marks.length === 0) fail(`growth.marks.${floor} 비어 있음`);
    marks.forEach((m, i) => {
      if (!GROWTH_MARK_KINDS.includes(m.kind)) fail(`growth.marks.${floor}[${i}].kind 알 수 없음`);
      if (!(m.at > 0) || (i > 0 && m.at <= marks[i - 1].at)) fail(`growth.marks.${floor} 는 0 보다 큰 오름차순`);
    });
    if (
      marks.filter((m) => m.kind === 'awaken1').length !== 1 ||
      marks.filter((m) => m.kind === 'awaken2').length !== 1
    )
      fail(`growth.marks.${floor}: 1차·2차 각성 눈금은 하나씩`);
    if (marks.findIndex((m) => m.kind === 'awaken1') > marks.findIndex((m) => m.kind === 'awaken2'))
      fail(`growth.marks.${floor}: 1차 각성이 2차 각성보다 앞`);
  }
  if (!(g.repeatEvery > 0)) fail('growth.repeatEvery 는 양수');
  if (!(g.gain.normalKillMult >= 0)) fail('growth.gain.normalKillMult');
  if (!(g.temper.max >= 0) || typeof g.temper.damageBonus !== 'number') fail('growth.temper');
  if (!(g.traitChoices >= 1)) fail('growth.traitChoices');
  const ids = new Set<string>();
  for (const [wid, w] of Object.entries(weapons)) {
    const gw = g.weapons[wid];
    if (!gw || gw.branches.length !== 3) fail(`growth.weapons.${wid}: 1차 갈래 3개`);
    gw.branches.forEach((b) => {
      const at = `growth.weapons.${wid}.${b.id}`;
      if (ids.has(`${wid}:${b.id}`)) fail(`${at} 중복`);
      ids.add(`${wid}:${b.id}`);
      const n = findBranch(weapons, wid, b.node);
      if (!n || n.depth !== 1) fail(`${at}.node ${b.node} 은 ${wid} 의 1차 노드여야 합니다`);
      if (!b.name || !plainLine(b.line)) fail(`${at}: 이름·한 줄(숫자 없이) 필요`);
      if (!VERBS.includes(b.verb)) fail(`${at}.verb 알 수 없음`);
      if (b.paths.length !== 2) fail(`${at}.paths 는 2개`);
      for (const p of b.paths) {
        if (ids.has(`${wid}:${p.id}`)) fail(`${at}.${p.id} 중복`);
        ids.add(`${wid}:${p.id}`);
        if (!n.node.next?.some((c) => c.id === p.node)) fail(`${at}.${p.id}.node ${p.node} 는 ${b.node} 의 2차 노드`);
        if (!p.name || !plainLine(p.line)) fail(`${at}.${p.id}: 이름·한 줄(숫자 없이) 필요`);
        if (!VERBS.includes(p.verb)) fail(`${at}.${p.id}.verb 알 수 없음`);
        if (!Array.isArray(p.tint) || p.tint.length !== 3) fail(`${at}.${p.id}.tint 는 [r,g,b]`);
      }
    });
    if (w.personality.branches.some((nb) => !gw.branches.some((b) => b.node === nb.id)))
      fail(`growth.weapons.${wid}: weapons.json 갈래가 모두 있어야 합니다`);
  }
  return g;
}

export function validateTraits(items: TraitDef[], g: GrowthData, weapons: WeaponTable): TraitDef[] {
  const ids = new Set<string>();
  for (const t of items) {
    const at = `traits.${t.id}`;
    if (ids.has(t.id)) fail(`traits 중복 id: ${t.id}`);
    ids.add(t.id);
    if (!weapons[t.weapon]) fail(`${at}.weapon 알 수 없음`);
    if (!VERBS.includes(t.verb)) fail(`${at}.verb 알 수 없음`);
    if (!isTagId(t.tag) || !BUILD.tags.find((d) => d.id === t.tag && (d.floor ?? 1) <= 1))
      fail(`${at}.tag 는 1층 태그 (간파·돌파·급소·연쇄·중량·취기)`);
    if (t.branch && !g.weapons[t.weapon]?.branches.some((b) => b.id === t.branch)) fail(`${at}.branch 알 수 없음`);
    if (!t.name || !plainLine(t.line)) fail(`${at}: 이름·한 줄(숫자 없이) 필요`);
    if (!t.effect || typeof t.effect.kind !== 'string') fail(`${at}.effect.kind 없음`);
  }
  // P12: 무기당 기본 8 (4동사 × 2) + 1차 갈래마다 2
  for (const wid of Object.keys(weapons)) {
    const mine = items.filter((t) => t.weapon === wid);
    for (const v of VERBS)
      if (mine.filter((t) => !t.branch && t.verb === v).length !== 2) fail(`traits: ${wid} 기본 ${v} 칸은 2장`);
    for (const b of g.weapons[wid].branches)
      if (mine.filter((t) => t.branch === b.id).length !== 2) fail(`traits: ${wid}.${b.id} 갈래 개성은 2장`);
  }
  return items;
}

export const GROWTH: GrowthData = validateGrowth(growthJson as unknown as GrowthData, WEAPONS);
export const TRAITS: readonly TraitDef[] = validateTraits(
  (traitsJson as unknown as { items: TraitDef[] }).items,
  GROWTH,
  WEAPONS,
);

/** 이 층의 기본 눈금 (표에 없는 층은 가장 가까운 아래 층 · null = 1층) */
export function baseMarksOn(floor: FloorScope): GrowthMarkDef[] {
  return byFloor(GROWTH.marks, floor ?? 1, GROWTH.marks['1']);
}

export function growthBranches(weapon: string): readonly GrowthBranchDef[] {
  return GROWTH.weapons[weapon]?.branches ?? [];
}

/** 갈래(growth id) */
export function growthBranch(weapon: string, id: string | null | undefined): GrowthBranchDef | null {
  return (id && growthBranches(weapon).find((b) => b.id === id)) || null;
}

/** 시스템 노드 id → 갈래 */
export function branchByNode(weapon: string, node: string | undefined): GrowthBranchDef | null {
  return (node && growthBranches(weapon).find((b) => b.node === node)) || null;
}

/** 시스템 노드 id → 길 (+ 그 갈래) */
export function pathByNode(
  weapon: string,
  node: string | undefined,
): { branch: GrowthBranchDef; path: GrowthPathDef } | null {
  if (!node) return null;
  for (const b of growthBranches(weapon)) {
    const p = b.paths.find((x) => x.node === node);
    if (p) return { branch: b, path: p };
  }
  return null;
}

export function traitDef(id: string): TraitDef | undefined {
  return TRAITS.find((t) => t.id === id);
}

/** 길 강조색 (growth.json 길 tint — 시트 JSON pathTint 가 없을 때) — 0xRRGGBB */
export function pathTint(weapon: string, branch: string, path: string): number | null {
  const c = growthBranch(weapon, branch)?.paths.find((p) => p.id === path)?.tint;
  return c ? (c[0] << 16) | (c[1] << 8) | c[2] : null;
}
