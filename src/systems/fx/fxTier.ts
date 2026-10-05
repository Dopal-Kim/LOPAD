/**
 * 55라운드 Q15·Q16 (계약 §10 갱신): 갈래 단계별 이펙트 시트 고르기. Phaser 의존 없음.
 *
 * 대체 순서 = 2단 전용 시트 → 1단 갈래 시트(+ secondaryVariants colorSwap 대체) → 기본 시트.
 * - 2단 전용 시트 id: 1단 시트 JSON `secondarySheets[<2단 id>]` → `secondaryVariants[<2단 id>].sheet` → 이름 규칙 `<1단 id>_<2단 id>`
 *   (`fx/` 접두는 뗀다). 로드돼 있으면 그 시트 + 그 JSON `runtime`(+ heatVariants), colorSwap 은 쓰지 않는다.
 * - 없으면 1단 시트 + `resolveFxVariant`(colorSwap·overlay·덮어쓰기) — 52·53라운드 대체 경로.
 * 활 화살·저격 꼬리도 같은 규칙(2단 화살 JSON `tailSheets` 가 2단 꼬리를 가리킨다).
 */
import { stripFxPrefix } from './branchFx';
import { resolveFxVariant, runtimeFxVariant, type FxVariant } from './fxVariants';

/** 고르기에 필요한 시트 JSON 필드 (SheetJson 에 섞여 온다) */
export interface TierSheetFields {
  secondarySheets?: unknown;
  secondaryVariants?: unknown;
  heatVariants?: unknown;
  runtime?: unknown;
}

export interface TierLookup {
  /** 시트 텍스처가 로드돼 있는지 */
  has(id: string): boolean;
  sheet(id: string): TierSheetFields | null;
}

export type FxTier = 'secondary' | 'branch' | 'base';

export interface TierPick {
  id: string;
  tier: FxTier;
  variant: FxVariant | null;
}

function asObj(v: unknown): Record<string, unknown> | null {
  return v && typeof v === 'object' && !Array.isArray(v) ? (v as Record<string, unknown>) : null;
}

/** 1단 시트가 가리키는 2단 전용 시트 id (JSON → 이름 규칙) */
export function secondarySheetId(tier1Id: string, def: TierSheetFields | null, secondary: string): string {
  const direct = asObj(def?.secondarySheets)?.[secondary];
  if (typeof direct === 'string' && direct) return stripFxPrefix(direct);
  const viaVariant = asObj(asObj(def?.secondaryVariants)?.[secondary])?.sheet;
  if (typeof viaVariant === 'string' && viaVariant) return stripFxPrefix(viaVariant);
  return `${tier1Id}_${secondary}`;
}

/**
 * 시트 고르기. `tier1Id` = 이미 고른 1단 갈래 시트(갈래 시트가 없으면 기본 시트 — `isBranch` false),
 * `secondary` = 경로의 2단 노드 id, `heat` = 단검 가열 단계
 */
export function pickTierSheet(
  tier1Id: string,
  isBranch: boolean,
  opts: { secondary?: string | null; heat?: number },
  lookup: TierLookup,
): TierPick {
  const heat = opts.heat ?? 0;
  const def = lookup.sheet(tier1Id);
  if (isBranch && opts.secondary) {
    const id = secondarySheetId(tier1Id, def, opts.secondary);
    if (id !== tier1Id && lookup.has(id))
      return { id, tier: 'secondary', variant: runtimeFxVariant(lookup.sheet(id), heat) };
  }
  return {
    id: tier1Id,
    tier: isBranch ? 'branch' : 'base',
    variant: resolveFxVariant(def, { secondary: isBranch ? (opts.secondary ?? null) : null, heat }),
  };
}
