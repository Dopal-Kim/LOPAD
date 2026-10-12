/**
 * 62 루프 2 시스템 C (P16 §1~§3) 층 끝·죽음·능력치 흡수·장터 품목 데이터 (Phaser 의존 없음). `data/runEnd.json` — 문장은 스토리 63 팩.
 */
import runEndJson from '../../data/runEnd.json';
import type { TrialGrade } from './ritual';

export type ShopGoodId = 'relic' | 'potion' | 'heal' | 'inkBottle' | 'bellows';

export interface ShopGoodDef {
  id: ShopGoodId;
  name: string;
  line: string;
  /** 수치 틀 (상세) */
  detail?: string;
  /** 고정 값 · 유품은 희귀도별 */
  price: number | Record<string, number>;
  /** 이 기억(data/memory.json)을 떠올려야 진열된다 */
  memory?: string;
}

export interface FloorEndSummaryText {
  title: string;
  empire: Record<string, string>;
  opening: Record<string, string>;
  fields: Record<string, string>;
  values: Record<string, string>;
  cluesLine: { none: string; some: string; all: string };
  noHit: string;
  closing: string;
  buttons: { reborn: string; close: string };
  footer: string;
}

export interface DeathSummaryText {
  title: string;
  killerLines: {
    creature: string[];
    hazard: string[];
    boss: Record<string, string[]>;
    byEnemy: Record<string, string>;
    unknown: string;
  };
  hazardNames: Record<string, string>;
  fields: Record<string, string>;
  where: string;
  pathEmpty: string;
  souls: { gained: string; next: string; ready: string; firstReady: string; all: string };
  buttons: { reborn: string; memory: string; close: string; details: string };
}

export interface RunEndData {
  death: { slowMs: number; slowScale: number; inkMs: number; holdMs: number };
  floorEnd: {
    lastFloor: number;
    growthMenus: number;
    delayMs: number;
    bossDown: Record<string, string>;
    exitArrow: string;
    exitNotice: string;
    summary: FloorEndSummaryText;
  };
  deathSummary: DeathSummaryText;
  points: { growthPerPoint: number; breakNotice: string };
  trial: { firstTraitCards: Record<TrialGrade, number>; skipped: number; max: number; giftNote: string };
  shopGoods: { items: ShopGoodDef[] };
  /** 개성 발현 메뉴의 '다시 뽑기' 줄 */
  reroll: { key: string; label: string; detail: string };
}

const GOODS: readonly ShopGoodId[] = ['relic', 'potion', 'heal', 'inkBottle', 'bellows'];

export function validateRunEnd(d: RunEndData): RunEndData {
  const fail = (m: string): never => {
    throw new Error(`[data] runEnd: ${m}`);
  };
  const D = d.death;
  if (!(D.slowMs >= 0) || !(D.slowScale > 0 && D.slowScale <= 1) || !(D.inkMs >= 0) || !(D.holdMs >= 0))
    fail('death 수치');
  const F = d.floorEnd;
  if (!(F.lastFloor >= 1) || !(F.growthMenus >= 0) || !(F.delayMs >= 0)) fail('floorEnd 수치');
  const S = F.summary;
  if (!S?.title || !S.closing || !S.buttons?.reborn || !S.buttons?.close || !S.cluesLine?.none)
    fail('floorEnd.summary 문장');
  const K = d.deathSummary?.killerLines;
  if (!K?.creature?.length || !K.hazard?.length || !K.unknown) fail('deathSummary.killerLines');
  if (!d.deathSummary.souls?.next || !d.deathSummary.souls?.gained) fail('deathSummary.souls');
  if (!(d.points.growthPerPoint >= 0)) fail('points.growthPerPoint');
  for (const g of ['S', 'A', 'B', 'C'] as const)
    if (!(d.trial.firstTraitCards[g] >= 1)) fail(`trial.firstTraitCards.${g}`);
  if (!(d.trial.skipped >= 1) || !(d.trial.max >= d.trial.skipped)) fail('trial.skipped·max');
  for (const it of d.shopGoods.items) {
    if (!GOODS.includes(it.id)) fail(`shopGoods.${it.id} 알 수 없음`);
    if (!it.name) fail(`shopGoods.${it.id}.name`);
  }
  return d;
}

export const RUN_END: RunEndData = validateRunEnd(runEndJson as unknown as RunEndData);
