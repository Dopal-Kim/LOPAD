/**
 * 57라운드 A2 로드 묶음 (결정 round-57 Q16 '고른 무기만 런 시작 때 로드'). Phaser 의존 없음.
 * - 부팅 묶음: 주인공 기본 몸·적·보스·공용 이펙트·구조물 — Preloader 가 한 번 로드한다.
 * - 무기 묶음: 그 무기의 몸 동작·자세 변형·무기 오버레이(고유 자원 단계 포함)·무기 유도 이펙트 — 런 시작(Game 씬 preload)
 *   또는 시험장 무기 교체 때 그 무기만 로드한다. 부팅 묶음에 이미 있는 시트는 빠진다.
 * 부팅 묶음 + 모든 무기 묶음 = 57라운드 전 부팅 목록 (sheetSets.test 가 확인).
 */
import { BOSSES, ENEMIES, WEAPONS } from '../../data';
import type { WeaponTable } from '../../data/types';
import { bossFxSheets, bossStructureSheets } from '../boss/bossSheets';
import { branchFxSheetIds } from '../fx/branchFx';
import { allFxSheetIds } from '../fx/fxIds';
import { tier2FxSheetIds } from '../fx/fxTier';
import { meleeBranchFxSheetIds } from '../fx/fxVariants';
import { allStructureSprites } from '../structures/data';
import { comboArtNames } from '../weapon/comboArt';
import { gaugeOverlaySuffix } from './spriteActions';
import { sheetId, wantedSheets, type SheetRequest } from './sheetPaths';

/** 무기 표에서 유도하는 이펙트 시트 id (연격·갈래·2단 전용 + 공용 고정 목록 — 빈 표면 공용만) */
function fxIdsFor(weapons: WeaponTable): string[] {
  return [
    ...allFxSheetIds(weapons),
    ...branchFxSheetIds(weapons),
    ...meleeBranchFxSheetIds(weapons),
    ...tier2FxSheetIds(weapons),
    ...Object.values(weapons).flatMap((w) => branchMoveArt(w).fx),
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
  bootCache ??= dedupe(
    requestsFor(Object.keys(ENEMIES), Object.keys(BOSSES), {}, bossFxSheets(), [
      ...allStructureSprites(),
      ...bossStructureSheets(),
    ]),
  );
  return bootCache;
}

/** 무기 묶음: 그 무기만 쓰는 시트 (부팅 묶음에 있는 것은 뺀다). 모르는 무기면 빈 목록 */
export function weaponSheetRequests(weaponId: string): SheetRequest[] {
  if (!WEAPONS[weaponId]) return [];
  bootKeys ??= new Set(bootSheetRequests().map(requestKey));
  const boot = bootKeys;
  return dedupe(requestsFor([], [], pick([weaponId]), [], [])).filter((r) => !boot.has(requestKey(r)));
}

/** 57라운드 전 부팅 목록 (모든 무기) — 회귀 테스트용 */
export function allSheetRequests(): SheetRequest[] {
  return dedupe(
    requestsFor(Object.keys(ENEMIES), Object.keys(BOSSES), WEAPONS, bossFxSheets(), [
      ...allStructureSprites(),
      ...bossStructureSheets(),
    ]),
  );
}
