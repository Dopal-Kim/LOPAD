/**
 * 웹 글꼴 로드 확인 (34라운드 글꼴 규칙). `public/style.css` 의 @font-face 가 선언하고, 시스템은 쓰기 전에
 * `document.fonts.load` 로 로드를 기다린다. 실패·시간 초과면 폴백(monospace) 을 쓴다.
 * UI 소유 파일(`assets/ui/fonts/*.woff2`)은 CSS URL 로만 참조한다 — 코드가 열지 않는다.
 */
import { FEEL } from '../core/Constants';

const ready = new Map<string, boolean>();
const pending = new Map<string, Promise<boolean>>();

/** 글꼴 로드를 시작하고(1회) 결과를 기다린다. 환경에 FontFaceSet 이 없으면 false */
export function ensureFont(
  family: string,
  px = FEEL.DAMAGE_TEXT.FONT_PX,
  timeoutMs = FEEL.DAMAGE_TEXT.FONT_TIMEOUT_MS,
): Promise<boolean> {
  const known = ready.get(family);
  if (known !== undefined) return Promise.resolve(known);
  const inflight = pending.get(family);
  if (inflight) return inflight;
  const fonts = typeof document !== 'undefined' ? document.fonts : undefined;
  if (!fonts || typeof fonts.load !== 'function') {
    ready.set(family, false);
    return Promise.resolve(false);
  }
  const spec = `${px}px '${family}'`;
  const load = fonts
    .load(spec)
    .then((faces) => faces.length > 0 && fonts.check(spec))
    .catch(() => false);
  const timeout = new Promise<boolean>((resolve) => setTimeout(() => resolve(false), timeoutMs));
  const p = Promise.race([load, timeout]).then((ok) => {
    ready.set(family, ok);
    pending.delete(family);
    return ok;
  });
  pending.set(family, p);
  return p;
}

/** 로드가 끝난 글꼴이면 그 이름, 아니면 폴백 */
export function fontFamilyOr(family: string, fallback: string): string {
  return ready.get(family) ? family : fallback;
}

/** 로드 상태 (디버그): true 로드됨 / false 실패·폴백 / undefined 아직 */
export function fontStatus(family: string): boolean | undefined {
  return ready.get(family);
}
