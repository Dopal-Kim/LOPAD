/**
 * 근접 휘두름 이펙트 시트 고르기 (53라운드 SwingFx 규칙 + 55라운드 Q16 2단 전용 시트). Phaser 의존 없음.
 * 우선순위: 대쉬 공격 재사용(갈래 시트 우선) → 1단 갈래 연격 시트(`<무기>_combo<n>_<갈래>`, 2단이면 2단 전용 시트) →
 * 가열 시트 → 기본 연격(마지막 타는 진화 베기) → 진화 베기 → `<무기>_slash`.
 */
import { WEAPON_FX } from '../../core/Constants';
import { comboFxId, heatComboFxId, slashFxId } from '../fx/fxIds';
import { pickTierSheet, type FxTier, type TierLookup } from '../fx/fxTier';
import { branchComboFxId, resolveFxVariant, type FxVariant } from '../fx/fxVariants';

export interface SwingPickInput {
  weaponId: string;
  /** 연격 번호 (1부터). 연격이 아니면 null */
  comboN: number | null;
  /**
   * 55라운드 §17: 연격 기본 이펙트 id (그림 이름 표에서 고른 `<무기>_<이름>`, 로드 안 됐을 수 있음).
   * 있으면 comboN 대신 — 갈래 `<id>_<1단>`·가열 `<id>_heat<k>` 도 이 id 에서
   */
  comboId?: string | null;
  /** 연격 마지막 타 (진화 베기 자리) */
  finisher: boolean;
  /** 개성 경로 (1단, 2단) */
  path: readonly string[];
  /** 단검 가열 단계 (0 = 없음) */
  heat: number;
  /** 대검 대쉬 공격이 재사용하는 연격 이펙트 id (없으면 null) */
  reuseId: string | null;
  /** 경로의 진화 베기 시트 (만월·거합·난무·쌍격 중 로드된 것, 없으면 null) */
  evoId: string | null;
}

export interface SwingPick {
  id: string;
  /** 고른 단계: 2단 전용·1단 갈래·기본 (가열·진화 베기·slash 는 base) */
  tier: FxTier;
  variant: FxVariant | null;
  /** 가열 시트도 변주도 없을 때 가열 단계만큼 키우는 배율 (없으면 1) */
  heatScale: number;
}

/** 1단 갈래 시트 `<id>_<1단>` (연격 id 는 `<무기>_combo<n>_<1단>`)가 로드돼 있으면 그 id, 아니면 그대로 */
export function branchOf(
  id: string,
  weaponId: string,
  first: string | undefined,
  has: (id: string) => boolean,
): string {
  if (!first) return id;
  const n = /^(.*)_combo(\d+)$/.exec(id);
  const branch = n && n[1] === weaponId ? branchComboFxId(weaponId, Number(n[2]), first) : `${id}_${first}`;
  return has(branch) ? branch : id;
}

export function pickSwingFx(input: SwingPickInput, lookup: TierLookup): SwingPick {
  const { weaponId: w, comboN, finisher, path, heat, evoId } = input;
  const first = path[0];
  const secondary = path[1] ?? null;
  const has = (id: string) => lookup.has(id);
  const reuse = input.reuseId ? branchOf(input.reuseId, w, first, has) : null;
  const comboId = input.comboId !== undefined ? input.comboId : comboN !== null ? comboFxId(w, comboN) : null;
  const branchId = comboId ? branchOf(comboId, w, first, has) : null;
  const branchSheet = branchId !== null && branchId !== comboId;
  const heatId =
    comboId && heat > 0 && !branchSheet
      ? comboN !== null && input.comboId === undefined
        ? heatComboFxId(w, comboN, heat)
        : `${comboId}_heat${heat}`
      : null;
  const heatSheet = heatId !== null && has(heatId);
  const baseId = comboId && has(comboId) ? (finisher && evoId ? evoId : comboId) : (evoId ?? slashFxId(w));
  let pick: { id: string; tier: FxTier; variant: FxVariant | null };
  if (reuse && has(reuse)) pick = pickTierSheet(reuse, reuse !== input.reuseId, { secondary, heat }, lookup);
  else if (branchSheet) pick = pickTierSheet(branchId!, true, { secondary, heat }, lookup);
  else {
    const id = heatSheet && !(finisher && evoId) ? heatId! : baseId;
    pick = { id, tier: 'base', variant: resolveFxVariant(lookup.sheet(id), { secondary, heat }) };
  }
  // 가열: 단계 시트가 없고 시트 JSON 에도 가열 변주가 없으면 그림을 키운다
  const heatVariant = heat > 0 && resolveFxVariant(lookup.sheet(pick.id), { heat }) !== null;
  const heatScale = heat > 0 && !heatSheet && !heatVariant ? 1 + WEAPON_FX.HEAT_SCALE_PER_STAGE * heat : 1;
  return { ...pick, heatScale };
}
