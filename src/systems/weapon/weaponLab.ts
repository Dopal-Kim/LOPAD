/**
 * 49라운드 계약 §11.4 무기 시험장 메뉴 (Phaser 의존 없음).
 * `lab` = 무기 4종 고르기 (+ 각성 갈래로 · 닫기), `labBranch` = 61 G 무기 성장 시험 (갈래 3·길 6 아무 단계나 즉시 · 각성 게이지 자유 조작 ·
 * 패시브·저주 시험 · 무기 바꾸기 · 닫기). 그만두기 = '0'.
 */
import type { WeaponDef, WeaponTable } from '../../data/types';
import type { TraitDef } from '../../data/growthTypes';
import type { UiMenuLine, UiTagId } from '../../contract/ui';
import { verbsLine, weaponVerbs } from './verbs';

/** 그만두기 (닫기) key — 계약 §9.4 구조물 메뉴와 같은 관례 */
export const LAB_CANCEL_KEY = '0';
/** lab 메뉴: 개성 갈래 메뉴로 */
export const LAB_TO_BRANCH_KEY = '9';
/** labBranch 메뉴: 무기 바꾸기 */
export const LAB_TO_WEAPONS_KEY = '9';
/** 61 G (P12): 각성 게이지 +30 · 다음 눈금까지 · 처음으로 · 패시브 3지선다 · 저주 2택 (숫자 키가 다 차서 글자 키) */
export const LAB_GAUGE_KEY = 'g';
export const LAB_NEXT_MARK_KEY = 'n';
export const LAB_RESET_KEY = 'r';
export const LAB_PASSIVE_KEY = 'p';
export const LAB_CURSE_KEY = 'c';
/** 61 단계 5 (P13): 개성 켜고 끄기 메뉴로 · 그 메뉴의 전부 켜기·전부 끄기·환경 놓기·적 부르기 */
export const LAB_TRAITS_KEY = 't';
export const LAB_TRAITS_ALL_KEY = 'a';
export const LAB_TRAITS_NONE_KEY = 'x';
export const LAB_ENV_KEY = 'w';
export const LAB_ENEMIES_KEY = 'e';
/** 시험장 게이지 한 번에 더하는 양 */
export const LAB_GAUGE_STEP = 30;

export type LabBranchAction =
  | { kind: 'path'; path: string[] }
  | { kind: 'gauge' }
  | { kind: 'nextMark' }
  | { kind: 'reset' }
  | { kind: 'weapons' }
  | { kind: 'close' }
  | { kind: 'passive' }
  | { kind: 'curse' }
  | { kind: 'traits' };

/** 61 단계 5 시험장 개성 메뉴 동작 */
export type LabTraitAction =
  | { kind: 'toggle'; id: string }
  | { kind: 'all' }
  | { kind: 'none' }
  | { kind: 'env' }
  | { kind: 'enemies' }
  | { kind: 'back' }
  | { kind: 'close' };

/** 61 G labBranch 성장 줄 (게이지·다음 눈금·저주 상태) */
export interface LabGrowthInfo {
  gauge: number;
  /** 다음 눈금 (값·종류 이름) */
  next: { at: number; name: string } | null;
  curseActive: boolean;
  /** 갈래·길 화면 이름 (노드 id → 이름·한 줄) */
  names?: Record<string, { name: string; line: string }>;
}

export interface LabWeaponChoice {
  key: string;
  weaponId: string;
}

/** 무기 고르기 메뉴 줄: '1'.. 무기 (현재 무기는 표시), '9' 개성 갈래, '0' 닫기 */
export function labWeaponMenu(
  weapons: WeaponTable,
  currentId: string,
): { lines: UiMenuLine[]; choices: LabWeaponChoice[] } {
  const choices: LabWeaponChoice[] = [];
  const lines: UiMenuLine[] = [];
  Object.entries(weapons).forEach(([id, w], i) => {
    const key = String(i + 1);
    choices.push({ key, weaponId: id });
    lines.push({
      key,
      label: id === currentId ? `${w.name} (지금)` : w.name,
      enabled: true,
      // 61라운드 P1: 4동사 한 줄 · 보이는 자원
      detail: `${verbsLine(weaponVerbs(id, w, []))} · ${resourceLabel(w)}`,
    });
  });
  lines.push({ key: LAB_TO_BRANCH_KEY, label: '각성 갈래 · 게이지', enabled: true });
  lines.push({ key: LAB_CANCEL_KEY, label: '닫기', enabled: true });
  return { lines, choices };
}

/** 보이는 자원 이름 (61라운드 SY-2: 무기당 하나 — 고유 자원이 있으면 그것, 단검 가속처럼 숨은 자원은 빼고) */
function resourceLabel(w: WeaponDef): string {
  const g = w.gauge;
  if (g && !(g.kind === 'breath' && g.branch)) return g.label;
  const r = w.resource;
  if (!r || r.hidden) return '자원 없음';
  return r.label;
}

/**
 * 61 G 시험장 성장 메뉴 줄: 경로 (기본 · 1차 갈래 3 · 각 갈래의 2차 길 2 — 트리 순서, key 'b0'.., 라벨 앞 깊이 표기 '└ ' / '  └ ') ·
 * 'g' 각성 게이지 +30 · 'n' 다음 눈금까지 · 'r' 처음으로 · 'p' 패시브 3지선다 · 'c' 저주 2택 · '9' 무기 바꾸기 · '0' 닫기.
 * 현재 경로는 label 에 '(지금)'
 */
export function labBranchMenu(
  def: WeaponDef,
  currentPath: readonly string[],
  info: LabGrowthInfo | null = null,
): { lines: UiMenuLine[]; actions: Map<string, LabBranchAction> } {
  const lines: UiMenuLine[] = [];
  const actions = new Map<string, LabBranchAction>();
  const cur = currentPath.join('/');
  let n = 0;
  const add = (label: string, path: string[], detail?: string, tags?: readonly UiTagId[]) => {
    const key = `b${n++}`;
    actions.set(key, { kind: 'path', path });
    lines.push({
      key,
      label: path.join('/') === cur ? `${label} (지금)` : label,
      enabled: true,
      detail,
      ...(tags?.length ? { tags: [...tags] } : {}),
    });
  };
  const nm = (id: string, fallback: string) => info?.names?.[id]?.name ?? fallback;
  const ln = (id: string, fallback: string) => info?.names?.[id]?.line ?? fallback;
  add('기본 (각성 전)', []);
  for (const b of def.personality.branches) {
    add(`${treePrefix(1)}${nm(b.id, b.name)}`, [b.id], ln(b.id, b.description), b.tags);
    for (const c of b.next ?? [])
      add(`${treePrefix(2)}${nm(c.id, c.name)}`, [b.id, c.id], ln(c.id, c.description), c.tags);
  }
  if (info) {
    actions.set(LAB_GAUGE_KEY, { kind: 'gauge' });
    lines.push({
      key: LAB_GAUGE_KEY,
      label: `각성 게이지 +${LAB_GAUGE_STEP} (지금 ${Math.floor(info.gauge)})`,
      enabled: true,
      detail: '눈금을 넘으면 그 메뉴가 그대로 열린다',
    });
    actions.set(LAB_NEXT_MARK_KEY, { kind: 'nextMark' });
    lines.push({
      key: LAB_NEXT_MARK_KEY,
      label: info.next ? `다음 눈금까지 (${info.next.at} ${info.next.name})` : '다음 눈금 없음',
      enabled: Boolean(info.next),
    });
    actions.set(LAB_RESET_KEY, { kind: 'reset' });
    lines.push({ key: LAB_RESET_KEY, label: '게이지·개성·단련 처음으로', enabled: true });
    actions.set(LAB_PASSIVE_KEY, { kind: 'passive' });
    lines.push({ key: LAB_PASSIVE_KEY, kind: 'passive', label: '패시브 3지선다 (빌드 시험)', enabled: true });
    actions.set(LAB_TRAITS_KEY, { kind: 'traits' });
    lines.push({ key: LAB_TRAITS_KEY, label: '개성 켜고 끄기 · 환경 · 적', enabled: true });
    actions.set(LAB_CURSE_KEY, { kind: 'curse' });
    lines.push({
      key: LAB_CURSE_KEY,
      kind: 'curse',
      label: '저주 2택 (빌드 시험)',
      enabled: !info.curseActive,
      detail: info.curseActive ? '저주는 동시에 하나' : undefined,
    });
  }
  actions.set(LAB_TO_WEAPONS_KEY, { kind: 'weapons' });
  lines.push({ key: LAB_TO_WEAPONS_KEY, label: '무기 바꾸기', enabled: true });
  actions.set(LAB_CANCEL_KEY, { kind: 'close' });
  lines.push({ key: LAB_CANCEL_KEY, label: '닫기', enabled: true });
  return { lines, actions };
}

/** 갈래 깊이 표기 (UI 가 이걸로 들여쓴다, 계약 §11.4): 깊이 d → 공백 2칸 × (d − 1) + '└ ' */
export function treePrefix(depth: number): string {
  return depth <= 0 ? '' : `${'  '.repeat(depth - 1)}└ `;
}

/**
 * 61 단계 5 (P13) 시험장 개성 메뉴 줄: 이 무기 개성 14장 (key 't<n>' — 켜짐 ■ / 꺼짐 □, 다른 갈래 개성은 잠김) ·
 * 공명 상태(고를 수 없는 줄) · 'a' 전부 켜기(지금 갈래까지) · 'x' 전부 끄기 · 'w' 술 웅덩이 놓기 · 'e' 적 부르기 · '9' 갈래 메뉴 · '0' 닫기
 */
export function labTraitMenu(
  traits: readonly TraitDef[],
  owned: readonly string[],
  branch: string | null,
  info: { branchNames: Record<string, string>; resonance: { name: string; line: string; on: boolean }[] },
): { lines: UiMenuLine[]; actions: Map<string, LabTraitAction> } {
  const lines: UiMenuLine[] = [];
  const actions = new Map<string, LabTraitAction>();
  traits.forEach((t, i) => {
    const key = `t${i}`;
    const locked = Boolean(t.branch && t.branch !== branch);
    const on = owned.includes(t.id);
    lines.push({
      key,
      kind: 'trait',
      label: `${on ? '■' : '□'} ${t.name}${t.env ? ' · 환경' : ''}`,
      enabled: !locked,
      detail: locked ? `${info.branchNames[t.branch ?? ''] ?? t.branch} 갈래를 고르면 켤 수 있다` : t.line,
      verb: t.verb,
      tags: [t.tag as UiTagId],
    });
    if (!locked) actions.set(key, { kind: 'toggle', id: t.id });
  });
  info.resonance.forEach((r, i) =>
    lines.push({ key: `r${i}`, label: `공명 ${r.on ? '켜짐' : '꺼짐'} · ${r.name}`, enabled: false, detail: r.line }),
  );
  const add = (key: string, label: string, a: LabTraitAction, detail?: string) => {
    actions.set(key, a);
    lines.push({ key, label, enabled: true, ...(detail ? { detail } : {}) });
  };
  add(LAB_TRAITS_ALL_KEY, '전부 켜기 (지금 갈래까지)', { kind: 'all' });
  add(LAB_TRAITS_NONE_KEY, '전부 끄기', { kind: 'none' });
  add(LAB_ENV_KEY, '술 웅덩이 놓기', { kind: 'env' }, '허수아비 둘레에 술 웅덩이 셋 (하나는 불)');
  add(LAB_ENEMIES_KEY, '적 부르기', { kind: 'enemies' }, '움직이는 적 넷 (밀기·띄우기·묶기 시험)');
  add(LAB_TO_WEAPONS_KEY, '갈래 · 게이지 메뉴로', { kind: 'back' });
  add(LAB_CANCEL_KEY, '닫기', { kind: 'close' });
  return { lines, actions };
}
