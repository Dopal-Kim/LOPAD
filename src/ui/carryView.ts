import type { UiCarry } from '../contract/ui';

/**
 * 53라운드 F 넣기/뽑기 표시 (계약 53라운드 추가 `UiSnapshot.carry`, 51라운드 Q4).
 * 넣고 뽑는 무기(칼·대검)만 값이 오고, 손에 드는 무기(단검·활)·값이 없을 때는 null → HUD 표시를 숨긴다.
 * 시스템이 필드를 아직 채우지 않은 빌드에서도 깨지지 않게 모양을 확인한다.
 */
export interface CarryView {
  /** 넣은 상태 (false = 뽑음) */
  sheathed: boolean;
  /** 넣은 상태에서 준비된 첫 타 이름 (발도·끌어내기). 없으면 null */
  ready: string | null;
  /** 누를 키 (계약상 'F') */
  key: string;
}

export function carryView(c: UiCarry | null | undefined): CarryView | null {
  if (!c || typeof c !== 'object' || typeof c.drawn !== 'boolean') return null;
  const sheathed = !c.drawn;
  const name = typeof c.firstStrike === 'string' ? c.firstStrike.trim() : '';
  return { sheathed, ready: sheathed && name ? name : null, key: c.key || 'F' };
}

/** 같은 표시인지 (다시 그릴지 판단) */
export function carryKey(v: CarryView | null): string {
  return v ? `${v.key}|${v.sheathed ? 1 : 0}|${v.ready ?? ''}` : '';
}
