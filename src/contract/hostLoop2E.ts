/**
 * 62 루프 2 시스템 E 계약 명령 구현 (계약 UI §24 — host.ts 를 덜 건드리려 따로): `uiCommands.menuShown(id)`.
 * 메뉴는 지금 열린 TextMenu 가, 'route'(노드 고르기 지도)는 Game 이 등록한 처리기가 받는다. UI 파트는 import 금지.
 */
import { __system } from './ui';
import { TextMenu } from '../systems/TextMenu';

let routeShown: (() => void) | null = null;

/** Game 이 등록 (shutdown 에서 null) — 노드 고르기 지도를 UI 가 실제로 그렸다 */
export function setRouteShown(fn: (() => void) | null): void {
  routeShown = fn;
}

export function installLoop2E(): void {
  __system.patchImpl({
    loop2E: {
      menuShown: (id) => {
        if (id === 'route') routeShown?.();
        else TextMenu.shown(id);
      },
    },
  });
}
