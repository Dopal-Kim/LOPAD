/**
 * 49라운드 계약 §11.4 무기 시험장 메뉴 (Phaser 의존 없음).
 * `lab` = 무기 4종 고르기 (+ 개성 갈래로 · 닫기), `labBranch` = 개성 진화 갈래 트리에서 아무 단계나 즉시 적용
 * (기본 · 1차 2개 · 2차 4개 · 강화 +1 순환 · 무기 바꾸기 · 닫기). 선택지 key 는 숫자 문자, 그만두기 = '0'.
 */
import type { WeaponDef, WeaponTable } from '../../data/types';
import type { UiMenuLine } from '../../contract/ui';

/** 그만두기 (닫기) key — 계약 §9.4 구조물 메뉴와 같은 관례 */
export const LAB_CANCEL_KEY = '0';
/** lab 메뉴: 개성 갈래 메뉴로 */
export const LAB_TO_BRANCH_KEY = '9';
/** labBranch 메뉴: 강화 +1 · 무기 바꾸기 */
export const LAB_REINFORCE_KEY = '8';
export const LAB_TO_WEAPONS_KEY = '9';

export type LabBranchAction =
  { kind: 'path'; path: string[] } | { kind: 'reinforce' } | { kind: 'weapons' } | { kind: 'close' };

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
      detail: `${w.secondary.name} · ${resourceLabel(w)}`,
    });
  });
  lines.push({ key: LAB_TO_BRANCH_KEY, label: '개성 갈래 고르기', enabled: true });
  lines.push({ key: LAB_CANCEL_KEY, label: '닫기', enabled: true });
  return { lines, choices };
}

function resourceLabel(w: WeaponDef): string {
  const r = w.resource;
  if (!r) return '자원 없음';
  return r.label;
}

/**
 * 개성 갈래 메뉴 줄: '1' 기본(갈래 없음) · 1차 A · 2차 A1 · 2차 A2 · 1차 B · 2차 B1 · 2차 B2 (트리 순서, key '2'..'7',
 * 라벨 앞 깊이 표기 '└ ' / '  └ ') ·
 * '8' 강화 +1 (최대면 0 으로) · '9' 무기 바꾸기 · '0' 닫기. 현재 경로는 label 에 표시
 */
export function labBranchMenu(
  def: WeaponDef,
  currentPath: readonly string[],
  reinforce: number,
  reinforceMax: number,
): { lines: UiMenuLine[]; actions: Map<string, LabBranchAction> } {
  const lines: UiMenuLine[] = [];
  const actions = new Map<string, LabBranchAction>();
  const cur = currentPath.join('/');
  let n = 1;
  const add = (label: string, path: string[], detail?: string) => {
    const key = String(n++);
    actions.set(key, { kind: 'path', path });
    lines.push({ key, label: path.join('/') === cur ? `${label} (지금)` : label, enabled: true, detail });
  };
  add('기본 (갈래 없음)', []);
  for (const b of def.personality.branches) {
    add(`${treePrefix(1)}${b.name}`, [b.id], b.description);
    for (const c of b.next ?? []) add(`${treePrefix(2)}${c.name}`, [b.id, c.id], c.description);
  }
  actions.set(LAB_REINFORCE_KEY, { kind: 'reinforce' });
  lines.push({
    key: LAB_REINFORCE_KEY,
    label: `강화 +1 (지금 ${reinforce}/${reinforceMax}${reinforce >= reinforceMax ? ' → 0' : ''})`,
    enabled: true,
  });
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

/** 강화 순환: 최대면 0 으로 */
export function nextReinforce(current: number, max: number): number {
  return current >= max ? 0 : current + 1;
}
