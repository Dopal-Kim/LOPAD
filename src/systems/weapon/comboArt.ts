/**
 * 55라운드 §17 연격 그림 이름 표 (data/weapons.json `combo.art`) — 시트 이름을 데이터 한 곳에서 매핑한다. Phaser 의존 없음.
 * 타의 그림 키(`hits[i].art`, 없으면 `combo<n>`) → 후보 이름(앞이 우선, 로드된 첫 시트):
 * 몸 `player_<무기>_<이름>`(무기 오버레이 `<무기>_<이름>` 이 몸을 따라감) · 휘두름 이펙트 `fx/<무기>_<이름>` · 끝점 바닥 충격 `fx/<무기>_<이름>`.
 * 아트의 새 시트 명세가 오면 표의 앞에 새 이름을 넣으면 되고, 새 시트가 아직 없으면 뒤의 기존 시트로 대체돼 로직만 먼저 돈다.
 */
import type { ComboArtEntry, ComboDef } from '../../data/types';

export type ArtCategory = 'body' | 'fx' | 'impactFx' | 'flashFx' | 'crackFx';

/** 기존 연격 그림 이름 `combo<n>` (n = 1부터) */
export function legacyComboArt(n: number): string {
  return `combo${n}`;
}

/** 타의 그림 키 (`hits[i].art`, 없으면 `combo<i+1>`) */
export function hitArtKey(def: Pick<ComboDef, 'hits'> | undefined, index: number): string {
  return def?.hits[index]?.art ?? legacyComboArt(index + 1);
}

/** 그림 키 → 후보 이름. 표에 없는 키는 그 이름 그대로(기존 `combo<n>`). fx 가 없으면 몸 후보와 같게, impactFx·flashFx·crackFx 는 없으면 없음 */
export function artCandidates(def: Pick<ComboDef, 'art'> | undefined, key: string, cat: ArtCategory): string[] {
  const e: ComboArtEntry | undefined = def?.art?.[key];
  if (!e) return cat === 'body' || cat === 'fx' ? [key] : [];
  if (cat === 'body') return e.body ?? [key];
  if (cat === 'fx') return e.fx ?? e.body ?? [key];
  return (cat === 'impactFx' ? e.impactFx : cat === 'crackFx' ? e.crackFx : e.flashFx) ?? [];
}

/** 로드된 첫 후보 (없으면 null) */
export function pickArt(candidates: readonly string[], has: (name: string) => boolean): string | null {
  for (const c of candidates) if (has(c)) return c;
  return null;
}

/** 표에 나오는 모든 이름 (Preloader 로드 목록 — 없는 파일은 매니페스트가 거른다) */
export function comboArtNames(def: Pick<ComboDef, 'art'> | undefined): { body: string[]; fx: string[] } {
  const body = new Set<string>();
  const fx = new Set<string>();
  for (const e of Object.values(def?.art ?? {})) {
    for (const n of e.body ?? []) body.add(n);
    for (const n of e.fx ?? []) fx.add(n);
    for (const n of e.impactFx ?? []) fx.add(n);
    for (const n of e.flashFx ?? []) fx.add(n);
    for (const n of e.crackFx ?? []) fx.add(n);
  }
  return { body: [...body], fx: [...fx] };
}

/**
 * 몸 동작 `<무기>_<이름>` 의 이름이 이 무기 그림 표에 있으면 무기 오버레이 후보 [이름, 'attack'] (없으면 null).
 * 기존 이름(combo<n>·slam 등)은 spriteDefs.overlayActionsFor 규칙이 먼저 처리한다
 */
export function overlayArtCandidates(def: Pick<ComboDef, 'art'> | undefined, rest: string): string[] | null {
  for (const e of Object.values(def?.art ?? {})) if (e.body?.includes(rest)) return [rest, 'attack'];
  return null;
}
