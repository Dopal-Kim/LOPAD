/**
 * 61라운드 단계 4 계약 UI §18 스냅샷 조립 (`UiSnapshot.growth`) · 메뉴 줄 갈래·길·개성 형식. Phaser 의존 없음.
 * 미리보기 텍스처 키(lookKey)는 시스템이 로드해 둔 것만 — 호출 쪽이 `look` 으로 알려 준다.
 */
import { GROWTH, growthBranches } from '../../data/growth';
import type { FloorScope } from '../../data/floorScope';
import type { GrowthBranchDef, GrowthPathDef, ResonanceDef, TraitDef } from '../../data/growthTypes';
import type {
  UiGrowth,
  UiGrowthBranch,
  UiGrowthMark,
  UiGrowthPath,
  UiGrowthTrait,
  UiResonance,
  UiTagId,
} from '../../contract/ui';
import type { WeaponState } from '../weapon/weapons';
import { effectiveKind, growthMarks } from './growth';
import { activeResonances, resonancesOf } from './resonance';

/** 미리보기 키 조회 (stage 0 = 기본 · 1 = 1차 모양 · 2 = 2차 모양 — path 가 있으면 그 길 색 완성 그림). 로드돼 있지 않으면 undefined */
export type LookKeyFn = (weapon: string, branch: string | null, stage: 0 | 1 | 2, path?: string) => string | undefined;

export const GUIDE_KINDS = ['trait', 'awaken1', 'awaken2'] as const;
export type GuideKind = (typeof GUIDE_KINDS)[number];

/** 61 단계 5 (§18.1): 개성 카드 그림 텍스처 키 조회 — 로드돼 있지 않으면 undefined */
export type IconKeyFn = (weapon: string, traitId: string) => string | undefined;

export function uiTrait(t: TraitDef, icon?: IconKeyFn): UiGrowthTrait {
  const iconKey = icon?.(t.weapon, t.id);
  return { id: t.id, name: t.name, line: t.line, verb: t.verb, tag: t.tag as UiTagId, ...(iconKey ? { iconKey } : {}) };
}

/** §18.1 공명 한 줄 (알림·카드) */
export function uiResonance(r: ResonanceDef): UiResonance {
  return { tag: r.tag as UiTagId, name: r.name, line: r.line };
}

export function uiPath(weapon: string, b: GrowthBranchDef, p: GrowthPathDef, look?: LookKeyFn): UiGrowthPath {
  const lookKey = look?.(weapon, b.id, 2, p.id);
  return { id: p.id, name: p.name, line: p.line, verb: p.verb, ...(lookKey ? { lookKey } : {}) };
}

export function uiBranch(weapon: string, b: GrowthBranchDef, look?: LookKeyFn): UiGrowthBranch {
  const lookKey = look?.(weapon, b.id, 1);
  return {
    id: b.id,
    name: b.name,
    line: b.line,
    verb: b.verb,
    ...(lookKey ? { lookKey } : {}),
    paths: [uiPath(weapon, b, b.paths[0], look), uiPath(weapon, b, b.paths[1], look)],
  };
}

/** 눈금 표시: 기본 눈금 + (처리한 수 +1) 까지의 단련 눈금 — 지난 것 done */
export function uiMarks(floor: FloorScope, marksDone: number): UiGrowthMark[] {
  return growthMarks(floor, marksDone + 1).map((m) => ({ at: m.at, kind: m.kind, done: m.index < marksDone }));
}

export function uiGrowth(
  w: WeaponState,
  floor: FloorScope,
  opts: { guides: readonly string[]; look?: LookKeyFn; icon?: IconKeyFn },
): UiGrowth {
  const on = new Set(activeResonances(w.id, w.traitDefs).map((r) => r.id));
  const marks = uiMarks(floor, w.marksDone);
  const raw = marks[w.marksDone];
  const next: UiGrowthMark | null = raw ? { ...raw, kind: effectiveKind(raw.kind, w.stage) } : null;
  const baseLookKey = opts.look?.(w.id, null, 0);
  return {
    gauge: Math.floor(w.gauge),
    marks,
    next,
    stage: Math.min(2, w.stage) as 0 | 1 | 2,
    weaponName: w.def.name,
    ...(baseLookKey ? { baseLookKey } : {}),
    branches: growthBranches(w.id).map((b) => uiBranch(w.id, b, opts.look)),
    branch: w.branchId,
    path: w.pathId,
    traits: w.traitDefs.map((t) => uiTrait(t, opts.icon)),
    resonance: resonancesOf(w.id).map((r) => ({ ...uiResonance(r), active: on.has(r.id) })),
    temper: { n: w.temper, max: GROWTH.temper.max },
    firstTime: {
      trait: !opts.guides.includes('trait'),
      awaken1: !opts.guides.includes('awaken1'),
      awaken2: !opts.guides.includes('awaken2'),
    },
  };
}
