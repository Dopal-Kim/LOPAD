import { uiCommands } from '../contract/ui';

/**
 * 62 루프 2 (P1-16) 전체화면 — 시스템 명령(계약 D, F11 은 시스템이 읽는다)을 먼저 쓰고, 없으면 브라우저 Fullscreen API 로
 * 문서 전체(`document.documentElement`)를 — 창 크기가 바뀌면 시스템 표시 배율(창 → 캔버스)이 스스로 다시 잰다.
 * 브라우저가 막으면(사용자 동작 밖·iframe 권한 없음) 조용히 그대로.
 */

type FsDoc = Document & { webkitFullscreenElement?: Element | null; webkitExitFullscreen?: () => Promise<void> };
type FsEl = HTMLElement & { webkitRequestFullscreen?: () => Promise<void> };

function doc(): FsDoc | null {
  return typeof document === 'undefined' ? null : (document as FsDoc);
}

/** 전체화면 API 를 쓸 수 있는가 */
export function fullscreenSupported(): boolean {
  const d = doc();
  if (!d) return false;
  const el = d.documentElement as FsEl;
  return Boolean(d.fullscreenEnabled ?? true) && Boolean(el.requestFullscreen || el.webkitRequestFullscreen);
}

export function isFullscreen(): boolean {
  const d = doc();
  return Boolean(d && (d.fullscreenElement || d.webkitFullscreenElement));
}

const listeners = new Set<(on: boolean) => void>();
let watching = false;

function watch(): void {
  const d = doc();
  if (watching || !d) return;
  watching = true;
  const fire = (): void => {
    for (const f of listeners) f(isFullscreen());
  };
  d.addEventListener('fullscreenchange', fire);
  d.addEventListener('webkitfullscreenchange', fire);
}

/** 전체화면이 켜지고 꺼질 때 (설정 화면 표시) — 돌려준 함수로 끊는다 */
export function onFullscreenChange(f: (on: boolean) => void): () => void {
  watch();
  listeners.add(f);
  return () => listeners.delete(f);
}

/** 켜기·끄기 (사용자 입력 처리 안에서 불러야 한다). 끝나면 실제 상태로 resolve */
export function setFullscreen(on: boolean): Promise<boolean> {
  const d = doc();
  if (!d || on === isFullscreen()) return Promise.resolve(isFullscreen());
  try {
    const p = on
      ? (() => {
          const el = d.documentElement as FsEl;
          return el.requestFullscreen ? el.requestFullscreen() : el.webkitRequestFullscreen?.();
        })()
      : d.exitFullscreen
        ? d.exitFullscreen()
        : d.webkitExitFullscreen?.();
    return Promise.resolve(p)
      .catch(() => undefined)
      .then(() => isFullscreen());
  } catch {
    return Promise.resolve(isFullscreen());
  }
}

/**
 * 설정 화면 '전체화면' — 시스템 명령(계약 D `uiCommands.setFullscreen` — F11 도 시스템이 읽는다)이 있으면 그것, 없거나 거절되면
 * 브라우저 API 로 직접. 상태는 `isFullscreen()`(문서 기준 — 어느 쪽으로 켜도 같다)
 */
export function requestFullscreen(on: boolean): void {
  const c = uiCommands as unknown as { setFullscreen?: (on: boolean) => boolean };
  if (typeof c.setFullscreen === 'function' && c.setFullscreen(on)) return;
  void setFullscreen(on);
}
