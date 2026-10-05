/**
 * 57라운드 빌드 축 1차 데이터 로더·검증 (index.ts 와 분리 — 병행 작업 충돌을 줄이려고 따로 둔다).
 * `data/build.json`(태그·세트·규칙 수치) · `data/curses.json` + `data/weapons.json` 갈래 노드의 태그·동작·규칙.
 * 61 G (P12): 옛 이중 개성(dualTraits.json)·최종 각성(awakenings.json)은 무기 성장(`data/growth.ts` — growth.json·traits.json)으로.
 */
import buildJson from '../../data/build.json';
import cursesJson from '../../data/curses.json';
import { WEAPONS } from './index';
import {
  TAG_IDS,
  isBuildStatKey,
  isTagId,
  type BuildData,
  type CurseDef,
  type CursesData,
  type SetThreshold,
  type TagId,
} from './buildTypes';
import type { WeaponEvolution, WeaponTable } from './types';
import { byFloor, onFloor, type FloorScope } from './floorScope';

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
  for (const t of b.tags) {
    if (!t.name) fail(`build.tags.${t.id}.name 없음`);
    if (t.floor !== undefined && !(Number.isInteger(t.floor) && t.floor >= 1))
      fail(`build.tags.${t.id}.floor 는 1 이상 정수`);
  }
  const S = b.scoring;
  for (const k of ['perPassive', 'passiveMaxLevelBonus', 'perBranchNode', 'perTrait'] as const)
    num(S[k], `build.scoring.${k}`);
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
  num(b.pact.benefitMult, 'build.pact.benefitMult');
  num(b.pact.extraNodes, 'build.pact.extraNodes');
  num(b.pool.themeWeightMult, 'build.pool.themeWeightMult');
  for (const k of ['bossChoices', 'chestChoices', 'nodeChoices'] as const)
    num(b.acquisition[k], `build.acquisition.${k}`);
  for (const [k, v] of Object.entries(b.drunk.liquorPool)) if (k !== '_note') num(v, `build.drunk.liquorPool.${k}`);
  return b;
}

/** 무기 갈래 노드 (61 G P12: 1차 갈래 3 → 갈래마다 2차 길 2 = 무기당 9): 태그 1~2개, 1차는 새 동작(move) 또는 규칙(rule) */
export function validateBranchNodes(weapons: WeaponTable): void {
  for (const [wid, w] of Object.entries(weapons)) {
    const visit = (n: WeaponEvolution, depth: number) => {
      const at = `weapons.${wid}.personality ${n.id}`;
      if (!Array.isArray(n.tags) || n.tags.length < 1 || n.tags.length > 2 || !n.tags.every(isTagId))
        fail(`${at}.tags 는 태그 1~2개`);
      if (depth === 1 && typeof n.move !== 'string' && !n.rule) fail(`${at}: 1차 노드는 move(새 동작) 또는 rule 필요`);
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

export const BUILD: BuildData = validateBuild(buildJson as unknown as BuildData);
validateBranchNodes(WEAPONS);
export const CURSES: CursesData = validateCurses(cursesJson as unknown as CursesData);

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

// --- 61라운드 P4 빌드 축 1층판 (층 노출 — `data/floorScope`) ---

/** 이 층에서 켜진 태그인가 (층 null = 제한 없음) */
export function tagOn(id: TagId, floor: FloorScope): boolean {
  return onFloor(
    BUILD.tags.find((t) => t.id === id),
    floor,
  );
}

/** 이 층에서 켜진 태그 목록 (TAG_IDS 순서) */
export function tagsOn(floor: FloorScope): TagId[] {
  return TAG_IDS.filter((t) => tagOn(t, floor));
}

/** 이 층에서 켜진 세트 임계 (1층판 = 2·4) */
export function setThresholdsOn(tag: TagId, floor: FloorScope): SetThreshold[] {
  return BUILD.sets[tag].filter((s) => onFloor(s, floor)).map((s) => s.threshold);
}

/** 이 층에서 나오는 저주인가 */
export function curseOn(def: CurseDef | undefined, floor: FloorScope): boolean {
  return Boolean(def) && onFloor(def, floor);
}

/** 이 층에서 이 길(riskNode · event · structure · pact)로 저주를 얻을 수 있나 */
export function curseSourceOn(source: string, floor: FloorScope): boolean {
  const list = byFloor(CURSES.sourcesByFloor, floor, null as string[] | null);
  return !list || list.includes(source);
}
