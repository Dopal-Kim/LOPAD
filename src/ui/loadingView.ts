/**
 * 62 루프 2 (P2-6) 로딩 화면 — 순수 계산 (Phaser 없음). 그리기는 `LoadingCard.ts`, 띄우는 곳은 `TransitionScene`
 * (그림 속 입구 전환이 다 덮인 뒤 READY 가 늦을 때 · 시스템 로드 진행 이벤트가 올 때).
 *
 * 진행 막대: 시스템이 로더 진행을 알려 주면(계약 D `ui:loading` `{ phase, progress: 0~1, done }` — region 은 UI 가 덧붙여 읽는 선택) 그 값,
 * 오기 전에는 시간으로 어림한 값(처음엔 빠르게, 90% 앞에서 멈춤). READY·done 이면 끝까지 채우고 걷는다.
 */

/**
 * 시스템 → UI 로드 진행 (계약 D `UI_EVENTS.LOADING` = 'ui:loading' `UiLoading { phase, progress, done }`). 계약 코드가 함께 커밋되기 전에도
 * 돌도록 값만 둔다. phase 'prefetch'(다음 노드 미리 읽기)는 배경이라 화면을 막지 않는다
 */
export const LOAD_PROGRESS_EVENT = 'ui:loading';

export interface LoadProgress {
  progress: number;
  done: boolean;
  region: string | null;
}

/** 페이로드 읽기 (모양이 틀리면 null) */
export function readLoadProgress(p: unknown): LoadProgress | null {
  if (!p || typeof p !== 'object') return null;
  const o = p as Record<string, unknown>;
  if (o.phase === 'prefetch') return null;
  const raw = typeof o.progress === 'number' && Number.isFinite(o.progress) ? o.progress : null;
  const done = o.done === true || (raw !== null && raw >= 1);
  if (raw === null && !done) return null;
  return {
    progress: done ? 1 : Math.max(0, Math.min(1, raw ?? 0)),
    done,
    region: typeof o.region === 'string' && o.region.trim() ? o.region.trim() : null,
  };
}

/** 시간 어림 진행 (0 → cap 로 다가감, tauMs 마다 남은 것의 63%) */
export function estimateProgress(elapsedMs: number, tauMs = 1600, cap = 0.9): number {
  if (!(elapsedMs > 0)) return 0;
  return cap * (1 - Math.exp(-elapsedMs / tauMs));
}

/** 보일 진행: 실제 값이 있으면 그것(뒤로 가지 않게 지난 값과 큰 쪽), 없으면 어림 */
export function shownProgress(real: number | null, estimate: number, prev = 0): number {
  const v = real === null ? estimate : real;
  return Math.max(prev, Math.max(0, Math.min(1, v)));
}

/** 팁 목록 (줄바꿈으로 나눈 글 — 빈 줄 버림) */
export function parseTips(raw: string | null | undefined): string[] {
  if (!raw) return [];
  return raw
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean);
}

/** 팁 하나 (n 번째 로딩마다 돌아가며 — 같은 팁이 이어서 나오지 않게) */
export function pickTip(tips: readonly string[], n: number): string {
  if (!tips.length) return '';
  const i = ((Math.floor(n) % tips.length) + tips.length) % tips.length;
  return tips[i];
}

/**
 * 62 루프 3 UI H (점검 P1-N4): 로딩 카드 그림 — 지역 키아트 키가 없으면 탄생지(`waste`). 액자는 그림이 오기 전에도 비지 않게
 * 지역 색 종이 + 지역 이름을 먼저 깐다(`loadingPaper`).
 */
export const LOADING_ART_KEYS = ['waste', 'gate', 'outer', 'brewery', 'hall'] as const;
export const LOADING_ART_FALLBACK = 'waste';

export function loadingArtKey(art: string | null | undefined): string {
  const a = (art ?? '').trim();
  return a || LOADING_ART_FALLBACK;
}

/** 종이 색 (바탕 · 아래 번짐) — 키별, 모르면 탄생지 */
export function loadingPaper<T>(art: string, papers: Readonly<Record<string, T>>): T {
  return papers[art] ?? papers[LOADING_ART_FALLBACK];
}
