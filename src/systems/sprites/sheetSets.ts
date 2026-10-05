/**
 * 57라운드 A2 로드 묶음 (결정 round-57 Q16 '고른 무기만 런 시작 때 로드'). Phaser 의존 없음.
 * - 부팅 묶음: 주인공 기본 몸·적·보스·공용 이펙트·구조물 — Preloader 가 한 번 로드한다.
 * - 무기 묶음: 그 무기의 몸 동작·자세 변형·무기 오버레이(고유 자원 단계 포함)·무기 유도 이펙트 — 런 시작(Game 씬 preload)
 *   또는 시험장 무기 교체 때 그 무기만 로드한다. 부팅 묶음에 이미 있는 시트는 빠진다.
 * 부팅 묶음 + 모든 무기 묶음 = 57라운드 전 부팅 목록 (sheetSets.test 가 확인).
 */
import { BOSSES, ENEMIES, WEAPONS } from '../../data';
import { AWAKENINGS } from '../../data/build';
import type { WeaponTable } from '../../data/types';
import { bossFxSheets, bossStructureSheets } from '../boss/bossSheets';
import { branchFxSheetIds } from '../fx/branchFx';
import { allFxSheetIds } from '../fx/fxIds';
import { allStructureSprites } from '../structures/data';
import { bundleSheetRequests } from '../bundle2/bundleSheets';
import { comboArtNames } from '../weapon/comboArt';
import { gaugeOverlaySuffix } from './spriteActions';
import { sheetId, wantedSheets, type SheetRequest } from './sheetPaths';
import { FX_ACTION } from './spriteActions';

/**
 * 무기 표에서 유도하는 이펙트 시트 id (연격·활 1단 화살·갈래 수단 그림 + 공용 고정 목록 — 빈 표면 공용만).
 * 60라운드 (57 Q42): 옛 진화 이펙트(갈래 id 시트·근접 1단 갈래 연격 시트·2단 전용 시트)는 로드하지 않는다
 */
function fxIdsFor(weapons: WeaponTable): string[] {
  return [
    ...allFxSheetIds(weapons),
    ...branchFxSheetIds(weapons),
    ...Object.entries(weapons).flatMap(([id, w]) => [...branchMoveArt(w).fx, ...(AWAKENINGS[id]?.art?.fx ?? [])]),
  ];
}

/** 57라운드 갈래 수단 그림 (1단 노드 `art`): 몸·무기 동작 이름 · 이펙트 id */
export function branchMoveArt(w: WeaponTable[string]): { body: string[]; fx: string[] } {
  const body: string[] = [];
  const fx: string[] = [];
  for (const a of w.personality.branches)
    for (const n of [a, ...(a.next ?? [])]) {
      for (const b of n.art?.body ?? []) if (!body.includes(b)) body.push(b);
      for (const f of n.art?.fx ?? []) if (!fx.includes(f)) fx.push(f);
    }
  return { body, fx };
}

function pick(ids: readonly string[]): WeaponTable {
  return Object.fromEntries(ids.filter((id) => WEAPONS[id]).map((id) => [id, WEAPONS[id]]));
}

/** 무기 목록 → wantedSheets 요청 (무기 유도 이펙트·연격 그림 이름·고유 자원 오버레이 포함) */
function requestsFor(
  enemyIds: string[],
  bossIds: string[],
  weapons: WeaponTable,
  extraFx: string[],
  structures: string[],
) {
  return wantedSheets(
    enemyIds,
    bossIds,
    Object.keys(weapons),
    [...fxIdsFor(weapons), ...extraFx],
    structures,
    Object.fromEntries(
      Object.entries(weapons).map(([id, w]) => [id, [...comboArtNames(w.combo).body, ...branchMoveArt(w).body]]),
    ),
    Object.fromEntries(
      Object.entries(weapons).flatMap(([id, w]) => {
        const sfx = gaugeOverlaySuffix(w.gauge?.kind);
        return sfx ? [[id, sfx]] : [];
      }),
    ),
  );
}

function dedupe(reqs: SheetRequest[]): SheetRequest[] {
  const seen = new Set<string>();
  return reqs.filter((r) => {
    const k = `${r.category}/${sheetId(r.name, r.action)}`;
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });
}

/** 요청 식별자 (분류 포함 — 이펙트와 구조물이 같은 이름을 써도 구분) */
export function requestKey(r: SheetRequest): string {
  return `${r.category}/${sheetId(r.name, r.action)}`;
}

let bootCache: SheetRequest[] | null = null;
let bootKeys: Set<string> | null = null;

/** 부팅 묶음: 무기와 무관한 시트 전부 */
export function bootSheetRequests(): SheetRequest[] {
  bootCache ??= dedupe([
    ...requestsFor(Object.keys(ENEMIES), Object.keys(BOSSES), {}, bossFxSheets(), [
      ...allStructureSprites(),
      ...bossStructureSheets(),
    ]),
    // 60라운드 2차 묶음 (계약 art §22): 소품 · 월드 소모품 · 엘리트 외곽선
    ...bundleSheetRequests(),
  ]);
  return bootCache;
}

/** 무기 묶음: 그 무기만 쓰는 시트 (부팅 묶음에 있는 것은 뺀다). 모르는 무기면 빈 목록 */
export function weaponSheetRequests(weaponId: string): SheetRequest[] {
  if (!WEAPONS[weaponId]) return [];
  bootKeys ??= new Set(bootSheetRequests().map(requestKey));
  const boot = bootKeys;
  return dedupe(requestsFor([], [], pick([weaponId]), [], [])).filter((r) => !boot.has(requestKey(r)));
}

/** 각성 오버레이 접미 (계약 art §21 `<무기 시트>_awaken`) */
export const AWAKEN_OVERLAY_SUFFIX = 'awaken';
/** 60라운드 계약 art §21 각성 순간 fx 접미 (`<무기>_awaken_in`) */
export const AWAKEN_IN_SUFFIX = 'awaken_in';

/** 각성 순간 fx id (`<무기>_awaken_in` — 각성을 얻은 순간 1회, 주인공 피벗을 따라감) */
export function awakenInFxId(weaponId: string): string {
  return `${weaponId}_${AWAKEN_IN_SUFFIX}`;
}

/**
 * 60라운드 계약 art §21 각성 전용 궤적 교체 표: 그 무기 이름으로 시작하는 무기 fx(연격·일섬 선·화살 …)마다
 * `<fx>_awaken` (JSON `swapRule` — 같은 틀·프레임·ms·피벗·행, 1:1). 실제 파일이 없는 것은 매니페스트가 걸러 로드되지 않고,
 * FxPool 교체 표는 교체 시트가 로드돼 있을 때만 쓴다(`FxPool.resolve`)
 */
export function awakenFxAliases(weaponId: string): Record<string, string> {
  if (!WEAPONS[weaponId]) return {};
  const own = `${weaponId}_`;
  const out: Record<string, string> = {};
  for (const id of fxIdsFor(pick([weaponId])))
    if (id.startsWith(own) && !id.endsWith(`_${AWAKEN_OVERLAY_SUFFIX}`) && id !== awakenInFxId(weaponId))
      out[id] = `${id}_${AWAKEN_OVERLAY_SUFFIX}`;
  return out;
}

/**
 * 60라운드 계약 art §21 최종 각성 무기 외형 오버레이: 무기 묶음의 무기 동작(휴대·연격·새 동작 — 자원 오버레이 제외)마다
 * `<동작>_awaken` + 각성 순간 fx `<무기>_awaken_in` + 각성 전용 궤적 `<fx>_awaken`(`awakenFxAliases`).
 * 각성 런에서만 로드 (`sheetLoader.preloadWeaponSheets(…, awaken)`·`loadAwakenSheets`). 없는 파일은 매니페스트가 거른다
 */
export function awakenSheetRequests(weaponId: string): SheetRequest[] {
  if (!WEAPONS[weaponId]) return [];
  const gauge = /_(?:ki|grudge)\d$/;
  const overlays = weaponSheetRequests(weaponId)
    .filter((r) => r.category === 'weapons' && r.name === weaponId && !gauge.test(r.action))
    .map((r) => ({ ...r, action: `${r.action}_${AWAKEN_OVERLAY_SUFFIX}` }));
  const fx = [awakenInFxId(weaponId), ...Object.values(awakenFxAliases(weaponId))].map((name): SheetRequest => ({
    category: 'fx',
    name,
    action: FX_ACTION,
  }));
  return dedupe([...overlays, ...fx]);
}

/** 57라운드 전 부팅 목록 (모든 무기) — 회귀 테스트용 */
export function allSheetRequests(): SheetRequest[] {
  return dedupe([
    ...requestsFor(Object.keys(ENEMIES), Object.keys(BOSSES), WEAPONS, bossFxSheets(), [
      ...allStructureSprites(),
      ...bossStructureSheets(),
    ]),
    ...bundleSheetRequests(),
  ]);
}
