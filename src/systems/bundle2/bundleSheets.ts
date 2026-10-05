/**
 * 60라운드 2차 묶음 시트 요청 (계약 art §22 — 부팅 묶음에 더한다): 전투장 소품(`structures/v3/challenge_banner`·`event_*`·`clue_*`) ·
 * 월드 소모품(`items/v3/consumable_f1`) · 엘리트 외곽선(`enemies/v3/<적>_<동작>_elite` — 접두어가 붙을 수 있는 적만).
 * 이펙트(엘리트 문장·이름표·§22.1 접두어 fx·화염 술병)는 fxIds BUILD_STATUS_FX_IDS. 없는 파일은 매니페스트가 거른다. Phaser 의존 없음.
 */
import { BUNDLE2, eventsOn } from '../../data/bundle2';
import { floorItems, onFloor, type FloorScope } from '../../data/floorScope';
import { NARRATIVE } from '../../data/narrative';
import { loadFloorCount } from '../../data/scope';
import { MOB_ACTIONS, STRUCTURE_ACTION } from '../sprites/spriteActions';
import type { SheetRequest } from '../sprites/sheetPaths';

/** 도전 성소 깃발 시트 (계약 art §22 C4) */
export const SHRINE_SHEET = 'challenge_banner';
/** 월드 소모품 시트 · 동작 (구조물 시트 형식) */
export const ITEM_SHEET = 'consumable_f1';
export const ITEM_ACTION = STRUCTURE_ACTION;
/** 엘리트 외곽선 동작 접미 (`<동작>_elite` — 적과 같은 프레임 ×1.15) */
export const ELITE_ACTION_SUFFIX = 'elite';

export function eliteAction(action: string): string {
  return `${action}_${ELITE_ACTION_SUFFIX}`;
}

/**
 * 전투장 소품 시트 id (이벤트 소품 · 단서 · 성소 깃발 · 61라운드 서사 소품). 61라운드 P5: 로드 범위 층(`scope.ts loadFloors`)에서
 * 켜진 것만 — 1층에서 끈 이벤트(E1·E2·E6·E7)·숨은 노드 단서·성소 깃발은 올리지 않는다 (가면 플레이스홀더)
 */
export function bundlePropSheets(floor: FloorScope = loadFloorCount()): string[] {
  const out = new Set<string>(NARRATIVE.props.map((p) => p.sheet));
  if (onFloor(BUNDLE2.shrine, floor)) out.add(SHRINE_SHEET);
  if (onFloor(BUNDLE2.hidden, floor)) for (const c of BUNDLE2.hidden.clues) out.add(c);
  for (const e of eventsOn(floor)) if (e.prop) out.add(e.prop);
  return [...out].sort();
}

/** 접두어가 붙을 수 있는 적 id (로드 범위 층의 접두어) */
export function eliteEnemyIds(floor: FloorScope = loadFloorCount()): string[] {
  return [...new Set(floorItems(BUNDLE2.elite.prefixes, floor).flatMap((p) => p.enemies))].sort();
}

/** 부팅 묶음에 더할 요청 */
export function bundleSheetRequests(): SheetRequest[] {
  const out: SheetRequest[] = bundlePropSheets().map((name) => ({
    category: 'structures',
    name,
    action: STRUCTURE_ACTION,
  }));
  out.push({ category: 'items', name: ITEM_SHEET, action: ITEM_ACTION });
  for (const name of eliteEnemyIds())
    for (const a of MOB_ACTIONS) out.push({ category: 'enemies', name, action: eliteAction(a) });
  return out;
}
