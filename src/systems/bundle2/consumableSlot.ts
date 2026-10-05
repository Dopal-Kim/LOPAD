/**
 * 60라운드 (i) 소모품 칸 (Phaser 의존 없음): 칸 1개, 같은 종류만 최대 slotMax(2)개. 다른 종류를 얻으면 바꿀지 확인(호출 쪽 메뉴).
 */
import { BUNDLE2, consumableDef } from '../../data/bundle2';
import type { ConsumableId } from '../../data/bundle2Types';

export interface ConsumableSave {
  id: ConsumableId;
  count: number;
}

export type GainResult = 'added' | 'full' | 'swap';

export class ConsumableSlot {
  id: ConsumableId | null = null;
  count = 0;

  get max(): number {
    return BUNDLE2.consumables.slotMax;
  }

  /** 얻기 시도: 빈 칸·같은 종류면 더함('added'), 같은 종류인데 가득('full'), 다른 종류('swap' — 바꿀지 물어야 함) */
  tryGain(id: ConsumableId): GainResult {
    if (!consumableDef(id)) return 'full';
    if (this.id === null || this.count <= 0) {
      this.id = id;
      this.count = 1;
      return 'added';
    }
    if (this.id !== id) return 'swap';
    if (this.count >= this.max) return 'full';
    this.count += 1;
    return 'added';
  }

  /** 바꾸기 (다른 종류 1개로) */
  replace(id: ConsumableId): void {
    this.id = id;
    this.count = 1;
  }

  /** 하나 쓰기 — 쓴 종류 (없으면 null) */
  use(): ConsumableId | null {
    if (!this.id || this.count <= 0) return null;
    const id = this.id;
    this.count -= 1;
    if (this.count <= 0) this.id = null;
    return id;
  }

  toSave(): ConsumableSave | null {
    return this.id && this.count > 0 ? { id: this.id, count: this.count } : null;
  }

  restore(s: ConsumableSave | null | undefined): void {
    this.id = s && consumableDef(s.id) ? s.id : null;
    this.count = this.id ? Math.max(1, Math.min(this.max, Math.floor(s!.count))) : 0;
  }
}
