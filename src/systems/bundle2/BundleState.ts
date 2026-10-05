/**
 * 60라운드 2차 묶음 런 상태 (GameState.bundle — 런 시작에 새로, 세이브에 남음). Phaser 의존 없음.
 * 런 단위: 나온 이벤트 · 소모품 칸 · 이벤트가 남긴 예약(다음 전투 끝 전표 · 다음 전투 웨이브 +1 · 다음 상점 할인).
 * 층 단위(세이브 안 함 — 노드 진행 저장 S-5 가 '층 처음부터'라 층 안에서 완결): 노드 정보(FloorExtras)·상점 진열 상태.
 */
import type { ConsumableId, RewardKind } from '../../data/bundle2Types';
import type { FloorExtras } from './routeExtras';
import { ConsumableSlot, type ConsumableSave } from './consumableSlot';

export interface BundleSave {
  usedEvents: string[];
  consumable: ConsumableSave | null;
  laterGold: number;
  extraWave: number;
  shopDiscount: number;
}

/** 상점 노드 진열 (층 안 — 같은 상점 노드에 다시 서면 그대로) */
export interface ShopStock {
  nodeId: string;
  display: { kind: 'passive' | 'consumable'; id: string; rarity?: string; price: number; sold: boolean }[];
  rerolls: number;
  chestUsed: boolean;
}

export class BundleState {
  usedEvents: string[] = [];
  readonly consumable = new ConsumableSlot();
  /** E3 '빚 갚기': 다음 전투 노드 끝에 전표 */
  laterGold = 0;
  /** E3 '앙갚음': 다음 전투 노드 웨이브 +1 */
  extraWave = 0;
  /** E9 '돌려줌': 다음 상점 할인 비율 */
  shopDiscount = 0;
  /** 이번 층 노드 정보 (노드 지도 층만) */
  floor: FloorExtras | null = null;
  /** 이번 층 상점 진열 */
  shops: ShopStock[] = [];

  /** 이벤트를 썼다 (런 안 중복 없음) */
  useEvent(id: string): void {
    if (!this.usedEvents.includes(id)) this.usedEvents.push(id);
  }

  onFloorStart(): void {
    this.floor = null;
    this.shops = [];
  }

  toSave(): BundleSave {
    return {
      usedEvents: [...this.usedEvents],
      consumable: this.consumable.toSave(),
      laterGold: this.laterGold,
      extraWave: this.extraWave,
      shopDiscount: this.shopDiscount,
    };
  }

  restore(s: BundleSave | undefined): void {
    if (!s) return;
    this.usedEvents = Array.isArray(s.usedEvents) ? [...s.usedEvents] : [];
    this.consumable.restore(s.consumable);
    this.laterGold = Number(s.laterGold) || 0;
    this.extraWave = Number(s.extraWave) || 0;
    this.shopDiscount = Number(s.shopDiscount) || 0;
  }
}

/** 보상 지급 계산 (전표 양 — 흔들림 ±jitter, 위험 ×mult). rand = 0..1 */
export function rewardGold(base: number, jitter: number, mult: number, rand: number): number {
  return Math.max(1, Math.round(base * (1 + (rand * 2 - 1) * jitter) * mult));
}

/** 보상 종류 → 지급 묶음 (메뉴가 필요한 것은 passive) */
export function rewardSummary(kind: RewardKind): 'menu' | 'instant' {
  return kind === 'passive' || kind === 'statPoint' ? 'menu' : 'instant';
}

export type { ConsumableId };
