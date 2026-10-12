import { MOUSE, type HeldInput } from './choiceGate';

/**
 * 62 루프 2 UI D: 지금 눌려 있는 키·마우스 왼쪽 버튼 (브라우저 이벤트를 바로 본다 — Phaser 큐가 밀려도 실제 상태).
 * 선택 메뉴가 열릴 때 `heldNow()` 로 '열기 전부터 눌려 있던 것'을 찍고, `lastUp(code)` 로 그 뒤 뗐는지 본다 (choiceGate.ts).
 * 창 밖으로 포커스가 나가면(키를 뗀 이벤트를 못 받는다) 모두 뗀 것으로 친다.
 */
const down = new Set<string>();
const upAt = new Map<string, number>();
let mouseDown = false;
let installed = false;

function install(): void {
  if (installed || typeof window === 'undefined') return;
  installed = true;
  const opt = { capture: true, passive: true } as const;
  window.addEventListener(
    'keydown',
    (e) => {
      if (e.code) down.add(e.code);
    },
    opt,
  );
  window.addEventListener(
    'keyup',
    (e) => {
      if (!e.code) return;
      down.delete(e.code);
      upAt.set(e.code, e.timeStamp);
    },
    opt,
  );
  window.addEventListener(
    'pointerdown',
    (e) => {
      if (e.button === 0) mouseDown = true;
    },
    opt,
  );
  const mouseUp = (e: PointerEvent): void => {
    if (e.button !== 0) return;
    mouseDown = false;
    upAt.set(MOUSE, e.timeStamp);
  };
  window.addEventListener('pointerup', mouseUp, opt);
  window.addEventListener('pointercancel', mouseUp, opt);
  window.addEventListener('blur', () => {
    const now = performance.now();
    for (const c of down) upAt.set(c, now);
    down.clear();
    if (mouseDown) upAt.set(MOUSE, now);
    mouseDown = false;
  });
}

install();

/** 지금 눌려 있는 것 */
export function heldNow(): HeldInput {
  install();
  return { keys: [...down], mouse: mouseDown };
}

/** 이 키(`KeyboardEvent.code`) 또는 `MOUSE` 를 마지막으로 뗀 시각 (모르면 -Infinity) */
export function lastUp(code: string): number {
  return upAt.get(code) ?? -Infinity;
}
