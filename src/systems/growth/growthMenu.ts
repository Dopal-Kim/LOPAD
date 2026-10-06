/**
 * 61라운드 단계 4 계약 UI §18 무기 성장 메뉴 (`evolve` — Phaser 의존 없음): 눈금 종류별 줄.
 * trait = 개성 3장 · awaken1 = 1차 갈래 3장 · awaken2 = 내 갈래의 2차 길 2장 · temper = [단련 / 개성 / 개성].
 * 라벨 = 이름만(수치·내부 용어 없음), detail = 한 줄. 줄 key '1'..
 */
import { GROWTH, growthBranch, growthBranches } from '../../data/growth';
import { tagOn } from '../../data/build';
import type { FloorScope } from '../../data/floorScope';
import type { GrowthMarkKind, TraitDef } from '../../data/growthTypes';
import type { UiMenuLine, UiTagId } from '../../contract/ui';
import { fill } from '../story';
import type { WeaponState } from '../weapon/weapons';
import { pickTraits, traitPool } from './growth';
import { newlyActive, partnerTags } from './resonance';
import { uiBranch, uiPath, uiResonance, uiTrait, type IconKeyFn, type LookKeyFn } from './uiGrowth';

export type GrowthChoice =
  | { kind: 'trait'; id: string }
  | { kind: 'awaken1'; node: string; branch: string }
  | { kind: 'awaken2'; node: string; path: string }
  | { kind: 'temper' };

export interface GrowthMenu {
  kind: GrowthMarkKind;
  title: string;
  footer: string;
  lines: UiMenuLine[];
  choices: GrowthChoice[];
}

function traitLine(key: string, t: TraitDef, floor: FloorScope, w: WeaponState, icon?: IconKeyFn): UiMenuLine {
  // 61 단계 5 (§18.1): 이 카드로 켜지는 공명
  const res = newlyActive(w.id, w.traitDefs, [...w.traitDefs, t])[0];
  return {
    key,
    kind: 'trait',
    label: t.name,
    enabled: true,
    detail: t.line,
    verb: t.verb,
    // 1층에서 꺼진 태그는 카드에 표시하지 않는다 (P12 UI 5)
    ...(tagOn(t.tag, floor) ? { tags: [t.tag as UiTagId] } : {}),
    trait: uiTrait(t, icon),
    ...(res ? { resonance: uiResonance(res) } : {}),
  };
}

/**
 * 이 눈금의 메뉴. 고를 것이 하나도 없으면 null (눈금은 그냥 지나간다). rnd = 개성 제시 난수
 */
export function growthMenu(
  w: WeaponState,
  kind: GrowthMarkKind,
  floor: FloorScope,
  rnd: () => number,
  look?: LookKeyFn,
  icon?: IconKeyFn,
): GrowthMenu | null {
  const T = GROWTH.text;
  const lines: UiMenuLine[] = [];
  const choices: GrowthChoice[] = [];
  const key = () => String(lines.length + 1);
  const weapon = w.def.name;
  if (kind === 'awaken1') {
    for (const b of growthBranches(w.id)) {
      if (!w.options.some((n) => n.id === b.node)) continue;
      lines.push({
        key: key(),
        kind: 'awaken1',
        label: b.name,
        enabled: true,
        detail: b.line,
        verb: b.verb,
        branch: uiBranch(w.id, b, look),
      });
      choices.push({ kind: 'awaken1', node: b.node, branch: b.id });
    }
    return lines.length
      ? { kind, title: fill(T.awaken1Title, { weapon }), footer: T.awaken1Footer, lines, choices }
      : null;
  }
  if (kind === 'awaken2') {
    const b = growthBranch(w.id, w.branchId);
    if (!b) return null;
    for (const p of b.paths) {
      if (!w.options.some((n) => n.id === p.node)) continue;
      lines.push({
        key: key(),
        kind: 'awaken2',
        label: p.name,
        enabled: true,
        detail: p.line,
        verb: p.verb,
        path: uiPath(w.id, b, p, look),
      });
      choices.push({ kind: 'awaken2', node: p.node, path: p.id });
    }
    return lines.length
      ? { kind, title: fill(T.awaken2Title, { branch: b.name }), footer: T.awaken2Footer, lines, choices }
      : null;
  }
  const pool = traitPool(w.id, w.branchId, w.traits);
  // 61 단계 5 (P13): 한 장 모자란 공명 태그의 짝 카드 한 장
  const partners = partnerTags(w.id, w.traitDefs);
  if (kind === 'temper') {
    if (w.canTemper) {
      lines.push({ key: key(), kind: 'temper', label: GROWTH.temper.name, enabled: true, detail: GROWTH.temper.line });
      choices.push({ kind: 'temper' });
    }
    for (const t of pickTraits(pool, GROWTH.traitChoices - lines.length, rnd, partners)) {
      lines.push(traitLine(key(), t, floor, w, icon));
      choices.push({ kind: 'trait', id: t.id });
    }
    return lines.length
      ? { kind, title: fill(T.temperTitle, { weapon }), footer: T.temperFooter, lines, choices }
      : null;
  }
  for (const t of pickTraits(pool, GROWTH.traitChoices, rnd, partners)) {
    lines.push(traitLine(key(), t, floor, w, icon));
    choices.push({ kind: 'trait', id: t.id });
  }
  return lines.length ? { kind, title: fill(T.traitTitle, { weapon }), footer: T.traitFooter, lines, choices } : null;
}
