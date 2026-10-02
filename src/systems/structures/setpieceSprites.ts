/**
 * 49라운드 세트 배치 소품 시트 id 목록 (Preloader 로드 대상 — allStructureSprites 기본값에 더해진다).
 * setpiece.ts 와 분리: structures/data.ts 가 이 파일을 읽어도 순환이 생기지 않게.
 */
import { ROUTE, entries, regionIds } from '../route';
import type { SetPieceDef } from './setpiece';

/** 템플릿들이 쓰는 모든 소품 시트 id (Preloader 로드 대상). 지역 × 이름 + 명시 시트 + 튜토리얼 */
export function setPieceSpriteIds(
  templates: Record<string, SetPieceDef>,
  regions: readonly string[],
  extra: readonly string[] = [],
): string[] {
  const out = new Set<string>(extra);
  const add = (name: string, explicit?: string[]) => {
    if (explicit && explicit.length > 0) {
      // 49라운드: `{region}` 후보는 지역마다 펼친다
      for (const s of explicit)
        if (s.includes('{region}')) for (const r of regions) out.add(s.replace('{region}', r));
        else out.add(s);
    } else for (const r of regions) out.add(`set_${r}_${name}`);
  };
  for (const [id, t] of Object.entries(templates)) {
    if (id.startsWith('_') || !t || typeof t !== 'object') continue;
    for (const d of t.decor ?? []) add(d.name, d.sprite);
    if (t.cover?.decor) add(t.cover.decor.name, t.cover.decor.sprite);
  }
  return [...out].sort();
}

/** route.json 의 템플릿·지역·튜토리얼 시트 전부 */
export function routeSetPieceSprites(): string[] {
  const T = ROUTE.tutorial;
  // 표식 `{step}` 후보는 단계 이름마다 펼친다
  const names = T ? T.steps.map((s) => s.signName ?? s.id) : [];
  const signs = T
    ? T.signSprite.flatMap((s) => (s.includes('{step}') ? names.map((n) => s.replace('{step}', n)) : [s]))
    : [];
  const extra = T ? [...signs, ...T.dummySprite] : [];
  return setPieceSpriteIds(entries(ROUTE.setPieces), regionIds(), extra);
}
