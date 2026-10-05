/**
 * 60라운드 2차 묶음 데이터 로드·검증 (data/bundle2.json). 형식이 틀리면 부팅에서 바로 예외 (데이터 오타를 빨리 드러낸다).
 */
import bundleJson from '../../data/bundle2.json';
import {
  REWARD_KINDS,
  type Bundle2Data,
  type ConsumableDef,
  type ConsumableId,
  type ElitePrefixDef,
  type ElitePrefixId,
  type EventDef,
} from './bundle2Types';
import { floorItems, type FloorScope } from './floorScope';

function fail(msg: string): never {
  throw new Error(`[data] bundle2: ${msg}`);
}

const pos = (v: unknown, path: string) => {
  if (typeof v !== 'number' || !(v >= 0)) fail(`${path} 는 0 이상 숫자`);
};

export function validateBundle2(d: Bundle2Data): Bundle2Data {
  for (const k of REWARD_KINDS) pos(d.rewards.weights[k], `rewards.weights.${k}`);
  pos(d.rewards.gold.amount, 'rewards.gold.amount');
  if (!REWARD_KINDS.includes(d.rewards.road)) fail('rewards.road 알 수 없음');
  if (!Array.isArray(d.risk.laneCols) || d.risk.laneCols.length === 0) fail('risk.laneCols 비어 있음');
  pos(d.risk.rewardMult, 'risk.rewardMult');
  const ids = new Set<string>();
  for (const e of d.events.items) {
    if (!e.id || ids.has(e.id)) fail(`events.items 중복·빈 id: ${e.id}`);
    ids.add(e.id);
    if (!e.text && !(e.intro && e.intro.length > 0)) fail(`events.${e.id}: text 또는 intro 필요`);
    for (const o of e.options ?? []) if (!o.key || o.key === '0') fail(`events.${e.id}.options key 는 '0' 이 아닌 값`);
    if ((e.options ?? []).filter((o) => o.pass).length > 1) fail(`events.${e.id}: pass 선택지는 하나`);
    if ((e.options ?? []).some((o) => o.effects.some((x) => x.kind === 'diaryRead')) && !e.diaryRead)
      fail(`events.${e.id}.diaryRead 없음`);
    if (e.kind === 'challenge' && !e.challenge) fail(`events.${e.id}.challenge 없음`);
    if (e.kind === 'ambush' && !(e.ambush && e.ambush.length > 0)) fail(`events.${e.id}.ambush 없음`);
  }
  for (const it of d.mapInfo.items) pos(it.price, `mapInfo.${it.id}.price`);
  if (d.shop.rerollPrices.length === 0) fail('shop.rerollPrices 비어 있음');
  if (!(d.shrine.chance >= 0 && d.shrine.chance <= 1)) fail('shrine.chance 는 0..1');
  for (const p of d.elite.prefixes) if (!p.enemies?.length) fail(`elite.prefixes.${p.id}.enemies 비어 있음`);
  for (const c of d.consumables.items) pos(c.price, `consumables.${c.id}.price`);
  if (!(d.consumables.slotMax >= 1)) fail('consumables.slotMax 는 1 이상');
  return d;
}

export const BUNDLE2: Bundle2Data = validateBundle2(bundleJson as unknown as Bundle2Data);

export function eventDef(id: string): EventDef | undefined {
  return BUNDLE2.events.items.find((e) => e.id === id);
}

export function prefixDef(id: string): ElitePrefixDef | undefined {
  return BUNDLE2.elite.prefixes.find((p) => p.id === id);
}

export function consumableDef(id: string): ConsumableDef | undefined {
  return BUNDLE2.consumables.items.find((c) => c.id === id);
}

export const CONSUMABLE_IDS: readonly ConsumableId[] = BUNDLE2.consumables.items.map((c) => c.id);
export const PREFIX_IDS: readonly ElitePrefixId[] = BUNDLE2.elite.prefixes.map((p) => p.id);

// --- 61라운드 P5 노드 부가 정리 (층 노출 — `data/floorScope`) ---

/** 이 층에서 나오는 소모품 (1층 = 화염 술병) */
export function consumableIdsOn(floor: FloorScope): ConsumableId[] {
  return floorItems(BUNDLE2.consumables.items, floor).map((c) => c.id);
}

/** 이 층에서 붙는 엘리트 접두어 (1층 3종) */
export function prefixIdsOn(floor: FloorScope): ElitePrefixId[] {
  return floorItems(BUNDLE2.elite.prefixes, floor).map((p) => p.id);
}

/** 이 층에서 나오는 이벤트 (1층 5종) */
export function eventsOn(floor: FloorScope): EventDef[] {
  return floorItems(BUNDLE2.events.items, floor);
}

/** 이벤트 메뉴 본문 (intro 줄 또는 옛 text) */
export function eventIntro(e: EventDef): string {
  return e.intro?.join('\n') ?? e.text ?? '';
}

/** 층(stage id)별 값 (없으면 stage1 → 첫 값) */
export function byStage(rec: Record<string, number>, stageId: string): number {
  return rec[stageId] ?? rec.stage1 ?? Object.values(rec)[0] ?? 0;
}
