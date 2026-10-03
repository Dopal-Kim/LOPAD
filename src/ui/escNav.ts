import type { UiMenu } from '../contract/ui';
import { takeKey } from './keyGate';

/**
 * 51라운드 §6: Esc = 모든 인터페이스에서 한 단계 뒤로. 메뉴 씬이 Esc 를 받았을 때 할 일.
 * - `cancelKey` 가 있으면 그 줄을 고른다 — 시스템이 메뉴마다 정한 '그만두기·뒤로' (53라운드 계약: 상점·구조물·시험장 lab '0',
 *   시험장 갈래 labBranch '9'). 키는 **지금 열린 메뉴 객체**의 값만 쓰고, UI 가 메뉴 id 로 추정하지 않는다.
 * - 메타(영혼) 메뉴는 런 시작 전 화면이라 앞 단계 = 타이틀
 * - 나머지(보상·패시브·개성·엔딩 등 반드시 골라야 하는 메뉴, cancelKey 없음)는 앞 단계가 없다 — 머무르고 안내만 띄운다
 */
export type MenuEscAction = { kind: 'select'; key: string } | { kind: 'title' } | { kind: 'stay' };

export function menuEscAction(m: Pick<UiMenu, 'id' | 'cancelKey'>): MenuEscAction {
  if (m.cancelKey) return { kind: 'select', key: m.cancelKey };
  if (m.id === 'meta') return { kind: 'title' };
  return { kind: 'stay' };
}

/**
 * 메뉴 씬 Esc 처리 판단. 아무것도 하지 않을 때 null.
 * - 열린 메뉴가 없거나 닫히는 중(MENU_CLOSE 를 받고 씬이 멈추기 전)이면 null
 * - 자동 반복 입력이면 null
 * - 같은 Esc 이벤트가 다시 넘어오면 null (`takeKey`, keyGate.ts 참조) — 앞 처리로 메뉴가 바뀌었어도
 *   새 메뉴의 cancelKey 를 보내지 않는다 (53라운드 시험장 갈래 첫 Esc 버그)
 */
export function resolveMenuEsc(
  open: Pick<UiMenu, 'id' | 'cancelKey'> | undefined,
  e: { repeat?: boolean } | undefined,
  closing: boolean,
): MenuEscAction | null {
  if (!open || closing || e?.repeat) return null;
  if (!takeKey(e)) return null;
  return menuEscAction(open);
}
