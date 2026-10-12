/**
 * 60라운드 2차 묶음 시트 요청 (계약 art §22 — 부팅 묶음에 더한다): 전투장 소품(`structures/v3/challenge_banner`·`event_*`·`clue_*`) ·
 * 월드 소모품(`items/v3/consumable_f1`) · 엘리트 외곽선(`enemies/v3/<적>_<동작>_elite` — 접두어가 붙을 수 있는 적만).
 * 이펙트(엘리트 문장·이름표·§22.1 접두어 fx·화염 술병)는 fxIds BUILD_STATUS_FX_IDS. 없는 파일은 매니페스트가 거른다. Phaser 의존 없음.
 */
import { DROP_ART, HERO_SETPIECE } from '../../core/Constants';
import { BUNDLE2, eventsOn } from '../../data/bundle2';
import { ENEMIES } from '../../data';
import { floorItems, onFloor, type FloorScope } from '../../data/floorScope';
import { NARRATIVE } from '../../data/narrative';
import { loadFloorCount } from '../../data/scope';
import { MOB_ACTIONS, STRUCTURE_ACTION } from '../sprites/spriteActions';
import type { SheetRequest } from '../sprites/sheetPaths';

/** 62 D (P1-13): 상점 노드 종군 상인·노점 칸 시트 (structures/v3 — 아트 r62b) */
export const SHOP_STALL_SHEETS: readonly string[] = ['npc_merchant', 'shop_slot'];
/** 62 D (P1-13): 노점 물건 그림 (items/v3 — 유품 꾸러미·단련·다시 뽑기 행) */
export const SHOP_GOODS_SHEET = 'shop_goods';

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

/** 62 D (art §31.3): 일반 적 1도트 림 동작 (`<동작>_rim` — 적과 같은 틀·프레임) */
export function rimAction(action: string): string {
  return `${action}_rim`;
}

/**
 * 전투장 소품 시트 id (이벤트 소품 · 단서 · 성소 깃발 · 61라운드 서사 소품). 61라운드 P5: 로드 범위 층(`scope.ts loadFloors`)에서
 * 켜진 것만 — 1층에서 끈 이벤트(E1·E2·E6·E7)·숨은 노드 단서·성소 깃발은 올리지 않는다 (가면 플레이스홀더)
 */
export function bundlePropSheets(floor: FloorScope = loadFloorCount()): string[] {
  const out = new Set<string>(NARRATIVE.props.map((p) => p.sheet));
  if (onFloor(BUNDLE2.shrine, floor)) out.add(SHRINE_SHEET);
  if (onFloor(BUNDLE2.hidden, floor)) for (const c of BUNDLE2.hidden.clues) out.add(c);
  for (const e of eventsOn(floor)) {
    if (e.prop) out.add(e.prop);
    // 62 D (P1-12): 사연 NPC (structures/v3/npc_*) · 소품 없는 사연의 대체 소품
    if (e.talk?.npc) out.add(e.talk.npc.sheet);
    if (e.talk?.propSheet) out.add(e.talk.propSheet);
  }
  // 62 D (P1-13): 종군 상인 · 노점 칸 (상점 노드)
  for (const s of SHOP_STALL_SHEETS) out.add(s);
  // 62 D (P2-10): 노드 세트피스 · 그을음 데칼
  for (const list of Object.values(HERO_SETPIECE.BY_REGION)) for (const s of list) out.add(s);
  out.add(HERO_SETPIECE.SOOT_SHEET);
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
  // 61 단계 5 (P13 §4) 바닥 줍기 물건 그림 (전표·물약·1층 소모품 — 없는 파일은 매니페스트가 거른다)
  for (const name of DROP_ART.SHEETS) out.push({ category: 'items', name, action: ITEM_ACTION });
  out.push({ category: 'items', name: SHOP_GOODS_SHEET, action: ITEM_ACTION });
  for (const name of eliteEnemyIds())
    for (const a of MOB_ACTIONS) out.push({ category: 'enemies', name, action: eliteAction(a) });
  // 62 D (art §31.3): 일반 적 림 (로드 범위 층 적 — 없는 파일은 매니페스트가 거른다)
  for (const name of Object.keys(ENEMIES))
    for (const a of MOB_ACTIONS) out.push({ category: 'enemies', name, action: rimAction(a) });
  return out;
}
