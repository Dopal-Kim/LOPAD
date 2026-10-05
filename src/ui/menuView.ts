import type { UiBuildState, UiMenu, UiMenuLine } from '../contract/ui';
import { tagName, type Tx } from './buildView';
import { menuIndent } from './resourceView';
import { fill } from './fmt';
import { CHOICE_KIND_NAME, R60_TEXT, RARITY_NAME } from './textBuild';
import type { SelectLine } from './widgets';

/**
 * 메뉴 한 페이지의 줄 만들기 (MenuScene 에서 분리, 60라운드 계약 §14.4·§14.6 반영). 순수 계산.
 * - 29라운드 evolve: 라벨 끝 ' — 설명' 이 detail 과 같으면 떼어 아래 줄로만
 * - 49라운드 시험장(lab·labBranch): 갈래 트리 들여쓰기
 * - §14.4: 칸 종류가 섞인 메뉴(개성 3지선다·이중 개성 칸이 낀 보상)는 라벨 앞에 〔종류〕, 희귀도·태그 한 줄, 잠긴 칸은
 *   '잠김 — 조건' 줄과 '(잠김)'
 * - §14.6: 가격(price.label)이 라벨에 없으면 덧붙이고, 팔린 줄은 '(팔림)', 상점 묶음(group)이 바뀌는 곳에 머리글
 */
const LAB_MENUS: ReadonlySet<string> = new Set(['lab', 'labBranch']);
/** 갈래 한 단계 들여쓰기 px · 트리 기호 */
export const LAB_INDENT = 14;
const LAB_BRANCH_MARK = '└ ';

const GROUP_KEY = {
  fixed: 'groupFixed',
  display: 'groupDisplay',
  reroll: 'groupReroll',
  chest: 'groupChest',
  mapInfo: 'groupMapInfo',
} as const;

/** 넓은 페이지를 쓰는 메뉴 (개성·엔딩·시험장) */
export function wideMenu(m: Pick<UiMenu, 'id'>): boolean {
  return m.id === 'evolve' || m.id === 'ending' || LAB_MENUS.has(m.id);
}

/** 칸 종류가 둘 이상 섞였는가 (그만두기 줄 제외) — 섞였을 때만 〔종류〕를 붙인다 */
function mixedKinds(m: UiMenu): boolean {
  const kinds = new Set(m.lines.filter((l) => l.key !== m.cancelKey && l.kind).map((l) => l.kind));
  return kinds.size > 1;
}

/** 희귀도 · 태그 한 줄 (없으면 '') */
export function choiceMeta(l: UiMenuLine, build?: UiBuildState | null): string {
  const parts: string[] = [];
  if (l.rarity) parts.push(RARITY_NAME[l.rarity] ?? l.rarity);
  if (l.tags?.length) parts.push(l.tags.map((t) => tagName(t, build)).join('·'));
  return parts.join(' · ');
}

export function menuLines(m: UiMenu, build?: UiBuildState | null, tx: Tx = (k) => R60_TEXT[k]): SelectLine[] {
  const lab = LAB_MENUS.has(m.id);
  const mixed = mixedKinds(m);
  let prevGroup: string | undefined;
  return m.lines.map((l) => {
    const suffix = l.detail ? ` — ${l.detail}` : '';
    const dup = Boolean(suffix) && l.label.endsWith(suffix);
    let label = dup ? l.label.slice(0, -suffix.length) : l.label;
    let indent = 0;
    const cancel = l.key === m.cancelKey;
    if (lab && !cancel) {
      const ind = menuIndent({ key: l.key, label });
      if (ind.depth > 0) {
        label = `${LAB_BRANCH_MARK}${ind.label}`;
        indent = (ind.depth - 1) * LAB_INDENT + LAB_INDENT;
      } else label = ind.label;
    }
    if (l.kind && mixed && !cancel) label = `〔${CHOICE_KIND_NAME[l.kind] ?? l.kind}〕 ${label}`;
    const price = l.price && l.price.kind !== 'none' ? l.price.label : '';
    if (price && !label.includes(price)) label = `${label} · ${price}`;
    const detailText = l.detail && (dup || !l.label.includes(l.detail)) ? l.detail : '';
    const meta = choiceMeta(l, build);
    const locked = l.locked?.condition ? fill(tx('locked'), { condition: l.locked.condition }) : '';
    const detail = [meta, detailText, locked].filter(Boolean).join('\n');
    let header: string | undefined;
    if (l.group && l.group !== prevGroup) header = tx(GROUP_KEY[l.group] ?? 'groupFixed');
    if (l.group || !cancel) prevGroup = l.group;
    const enabled = l.enabled && !l.soldOut && !l.locked;
    const note = l.soldOut ? tx('soldOutNote') : l.locked ? tx('lockedNote') : undefined;
    return { key: l.key, label, enabled, detail: detail || undefined, indent, header, note };
  });
}
