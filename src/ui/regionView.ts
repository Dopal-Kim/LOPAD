/**
 * 50라운드 지역 카드·키아트의 순수 계산 (Phaser 없이 테스트한다). 계약 `ui-system-interface.md` §12.
 */
import type { UiRoute, UiRouteNode } from '../contract/ui';
import { REGION_ART } from './theme';

/** 지역 표시 이름 → 키아트 키 (waste·gate·outer·brewery·hall). 맞는 것이 없으면 null */
export function regionArtKey(region: string | null | undefined): string | null {
  const r = (region ?? '').trim().toLowerCase();
  if (!r) return null;
  for (const a of REGION_ART) if (a.match.some((m) => r.includes(m.toLowerCase()))) return a.key;
  return null;
}

/** 경로에서 id 로 노드 찾기 (없으면 null) */
export function findNode(route: UiRoute | null | undefined, id: string | null | undefined): UiRouteNode | null {
  if (!route || !id) return null;
  return route.nodes.find((n) => n.id === id) ?? null;
}

/**
 * 지역 카드를 띄울지: 들어온 노드의 지역이 있고, 마지막으로 카드를 띄운(또는 처음 본) 지역과 다르면 true.
 */
export function regionChanged(region: string | null | undefined, last: string | null): boolean {
  const r = (region ?? '').trim();
  return r.length > 0 && r !== last;
}

/**
 * 카드 진행 (경과 ms → 배경·글자 알파). 나타남 → 머묾 → 사라짐. 사라짐은 `outAt`(넘김 시각, 없으면 정해진 시각)부터.
 * done = 다 사라졌다.
 */
export function cardAlpha(
  elapsed: number,
  t: { fadeInMs: number; holdMs: number; fadeOutMs: number; textLag: number },
  skip?: { at: number; fadeMs: number; from: number },
): { bg: number; text: number; done: boolean } {
  const clamp = (v: number) => Math.max(0, Math.min(1, v));
  if (skip) {
    const k = clamp(1 - (elapsed - skip.at) / Math.max(1, skip.fadeMs));
    return { bg: skip.from * k, text: skip.from * k, done: k <= 0 };
  }
  const outAt = t.fadeInMs + t.holdMs;
  if (elapsed >= outAt) {
    const k = clamp(1 - (elapsed - outAt) / Math.max(1, t.fadeOutMs));
    return { bg: k, text: k, done: k <= 0 };
  }
  const bg = clamp(elapsed / Math.max(1, t.fadeInMs));
  const lag = t.fadeInMs * t.textLag;
  const text = clamp((elapsed - lag) / Math.max(1, t.fadeInMs));
  return { bg, text, done: false };
}

/** 설명의 첫 문장 (지역 키 문구가 없을 때 카드 설명으로) */
export function firstSentence(text: string | null | undefined): string {
  const d = (text ?? '').trim();
  if (!d) return '';
  const m = d.match(/^[^.!?。]*[.!?。]?/);
  return (m ? m[0] : d).trim();
}
