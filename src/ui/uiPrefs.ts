/**
 * 62 루프 2 (P1-16) UI 만의 보기 설정 — 글자 크기 2단. 그리기만 바뀌는 값이라 시스템 세이브가 아니라 브라우저 저장소
 * (`lopad.ui.prefs`)에 UI 가 둔다(저장소가 없으면 이번 실행 동안만). Phaser 없음.
 *
 * 크게 = 1.5배: 논리 960×540 이 실제 1920×1080 으로 2배 그려지므로 1.5배 글자는 Galmuri11 도트 하나가 실제 3px — 정수라 선명하다.
 * 적용 범위는 `GlowText` 의 `readable` 글(자막·대사·한마디·이벤트 문장·조사 쪽지·로딩 팁) — 칸 크기가 정해진 라벨·카드·버튼은
 * 그대로(넘침 방지).
 */

export type TextSize = 'normal' | 'large';

export const TEXT_SIZES: readonly TextSize[] = ['normal', 'large'];

/** 크게일 때 배율 (실제 화면 3px = Galmuri 도트 1개) */
export const LARGE_TEXT_SCALE = 1.5;

const STORE_KEY = 'lopad.ui.prefs';

interface Prefs {
  textSize: TextSize;
}

let cache: Prefs | null = null;
/** 브라우저 저장소에 UI 가 적은 값이 있었는가 (없으면 시스템 설정 `textScale` 을 따른다) */
let stored = false;
const listeners = new Set<() => void>();

function storage(): Storage | null {
  try {
    return typeof localStorage === 'undefined' ? null : localStorage;
  } catch {
    return null;
  }
}

/** 저장된 글을 읽는다 (모양이 틀리면 기본값) */
export function parsePrefs(raw: string | null | undefined): Prefs {
  const out: Prefs = { textSize: 'normal' };
  if (!raw) return out;
  try {
    const o = JSON.parse(raw) as Record<string, unknown> | null;
    if (o && typeof o === 'object' && (o.textSize === 'normal' || o.textSize === 'large')) out.textSize = o.textSize;
  } catch {
    /* 틀린 글은 기본값 */
  }
  return out;
}

function prefs(): Prefs {
  if (!cache) {
    const raw = storage()?.getItem(STORE_KEY);
    stored = Boolean(raw);
    cache = parsePrefs(raw);
  }
  return cache;
}

/**
 * 시스템 설정의 글자 크기(계약 D `UiSettings.textScale` 1 | 1.25 — 시스템 월드 글자가 쓴다)를 받아들인다. UI 저장소에 적힌 값이 있으면 그것이
 * 먼저다. UI 의 읽는 글은 크게면 1.5배(선명한 정수 도트)로 그린다
 */
export function adoptTextScale(v: unknown): void {
  prefs();
  if (stored || typeof v !== 'number' || !Number.isFinite(v)) return;
  const s: TextSize = v > 1 ? 'large' : 'normal';
  if (cache && cache.textSize !== s) cache = { ...cache, textSize: s };
}

/** 시스템에 넘길 글자 크기 값 (계약 D `UiTextScale`) */
export function systemTextScale(s: TextSize): number {
  return s === 'large' ? 1.25 : 1;
}

export function textSize(): TextSize {
  return prefs().textSize;
}

export function setTextSize(s: TextSize): void {
  if (prefs().textSize === s) return;
  cache = { ...prefs(), textSize: s };
  stored = true;
  try {
    storage()?.setItem(STORE_KEY, JSON.stringify(cache));
  } catch {
    /* 저장소가 막혀 있으면 이번 실행 동안만 */
  }
  for (const f of listeners) f();
}

/** 읽는 글 배율 (보통 1 · 크게 1.5) */
export function textScale(): number {
  return textScaleOf(prefs().textSize);
}

export function textScaleOf(s: TextSize): number {
  return s === 'large' ? LARGE_TEXT_SCALE : 1;
}

/** 크기가 바뀌면 (설정 화면 미리보기 등) — 돌려준 함수로 끊는다 */
export function onTextSizeChange(f: () => void): () => void {
  listeners.add(f);
  return () => listeners.delete(f);
}

/** 테스트용: 읽어 둔 값 버리기 */
export function resetPrefsCache(): void {
  cache = null;
  stored = false;
}
