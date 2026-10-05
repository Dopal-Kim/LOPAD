/**
 * 60라운드 (e) 상점 진열 · (f) 성과 등급 · (h) 파훼 기록 — Phaser 의존 없는 계산.
 */
import { BUNDLE2, consumableDef, consumableIdsOn } from '../../data/bundle2';
import type { FloorScope } from '../../data/floorScope';
import type { BreakKind, Grade } from '../../data/bundle2Types';
import type { Rng } from '../rng';
import { weightedPick } from './routeExtras';
import type { ShopStock } from './BundleState';

/** 패시브 후보 (진열 고르기에 필요한 것만) */
export interface PassiveCandidate {
  id: string;
  rarity: string;
}

/**
 * 진열 3칸 굴리기 — 패시브 display.passive 칸(희귀도 가중 50/35/15, 전설 없음, 같은 것 두 번 없음) + 층 소모품 display.consumable 칸.
 * priceMult = 저주 외상 +20% · E9 할인 등 (호출 쪽 곱)
 */
export function rollDisplay(
  rng: Rng,
  pool: readonly PassiveCandidate[],
  priceMult: number,
  floor: FloorScope = null,
): ShopStock['display'] {
  const S = BUNDLE2.shop;
  const out: ShopStock['display'] = [];
  const taken = new Set<string>();
  for (let i = 0; i < S.display.passive; i++) {
    const rarity = weightedPick(rng, S.rarityWeights);
    const cands = pool.filter((p) => !taken.has(p.id) && (rarity === null || p.rarity === rarity));
    const any =
      cands.length > 0 ? cands : pool.filter((p) => !taken.has(p.id) && S.passivePrices[p.rarity] !== undefined);
    if (any.length === 0) break;
    const p = any[Math.floor(rng.next() * any.length)];
    taken.add(p.id);
    out.push({
      kind: 'passive',
      id: p.id,
      rarity: p.rarity,
      price: Math.round((S.passivePrices[p.rarity] ?? S.passivePrices.common) * priceMult),
      sold: false,
    });
  }
  // 61라운드 P5: 이 층 소모품만 (1층 = 화염 술병)
  const ids = consumableIdsOn(floor);
  for (let i = 0; i < S.display.consumable && ids.length > 0; i++) {
    const id = ids[Math.floor(rng.next() * ids.length)];
    out.push({ kind: 'consumable', id, price: Math.round((consumableDef(id)?.price ?? 0) * priceMult), sold: false });
  }
  return out;
}

/** 리롤 가격 (상점당 n번째 — 15 → 25 → 35, 그 뒤는 마지막 값) */
export function rerollPrice(rerolls: number, priceMult = 1): number {
  const P = BUNDLE2.shop.rerollPrices;
  return Math.round(P[Math.min(rerolls, P.length - 1)] * priceMult);
}

/**
 * 성과 등급: 무피격(허용 피격 수 이하) + 제한 시간 안 → 완 / 하나 → 양 / 없음.
 * 61라운드 P5: good = false 면 '양' 없이 '완' 하나 (1층 — 성소와 통합)
 */
export function gradeOf(
  hits: number,
  elapsedMs: number,
  timeLimitMs: number,
  allowance = 0,
  good = true,
): Grade | null {
  const noHit = hits <= allowance;
  const inTime = elapsedMs <= timeLimitMs;
  if (noHit && inTime) return 'perfect';
  if (good && (noHit || inTime)) return 'good';
  return null;
}

/** 등급 보상 (위험 노드 ×riskMult) */
export function gradeReward(grade: Grade | null, risk: boolean): { gold: number; personality: number } {
  const G = BUNDLE2.grade;
  if (!grade) return { gold: 0, personality: 0 };
  const m = risk ? G.riskMult : 1;
  const r = grade === 'perfect' ? G.perfect : { ...G.good, personality: 0 };
  return { gold: Math.round(r.gold * m), personality: Math.round(r.personality * m) };
}

/**
 * (h) 보스전 파훼 기록: 서로 다른 파훼 종류 수 · 마지막 파훼 경직 끝 시각 (결정타 판정).
 * 반환 distinct = 이번이 처음인 종류인가
 */
export class BreakTracker {
  private readonly kinds = new Set<BreakKind>();
  private stunUntil = -Infinity;

  record(kind: BreakKind, now: number, stunMs: number): { distinct: boolean; count: number } {
    const distinct = !this.kinds.has(kind);
    this.kinds.add(kind);
    this.stunUntil = Math.max(this.stunUntil, now + Math.max(0, stunMs));
    return { distinct, count: this.kinds.size };
  }

  get count(): number {
    return this.kinds.size;
  }

  /** 지금이 파훼 경직 중인가 (결정타) */
  inBreak(now: number): boolean {
    return now < this.stunUntil;
  }

  list(): BreakKind[] {
    return [...this.kinds];
  }
}
