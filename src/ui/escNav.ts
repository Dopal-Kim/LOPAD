import type { UiMenu } from '../contract/ui';

/**
 * 51라운드 §6: Esc = 모든 인터페이스에서 한 단계 뒤로. 메뉴 씬이 Esc 를 받았을 때 할 일.
 * - `cancelKey` 가 있으면 그 줄을 고른다 (구조물 메뉴·무기 시험장 메뉴 — 시스템이 정한 '그만두기·닫기')
 * - 메타(영혼) 메뉴는 런 시작 전 화면이라 앞 단계 = 타이틀
 * - 나머지(보상·패시브·개성·엔딩 등 반드시 골라야 하는 메뉴)는 앞 단계가 없다 — 머무르고 안내만 띄운다
 */
export type MenuEscAction = { kind: 'select'; key: string } | { kind: 'title' } | { kind: 'stay' };

export function menuEscAction(m: Pick<UiMenu, 'id' | 'cancelKey'>): MenuEscAction {
  if (m.cancelKey) return { kind: 'select', key: m.cancelKey };
  if (m.id === 'meta') return { kind: 'title' };
  return { kind: 'stay' };
}
