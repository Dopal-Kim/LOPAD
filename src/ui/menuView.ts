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
 * - §14.4: 칸 종류가 섞인 메뉴(단련 눈금 [단련/개성 발현] 등)는 라벨 앞에 〔종류〕, 희귀도·태그 한 줄, 잠긴 칸은
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

/**
 * 61라운드 플레이 점검 #4: 라벨 앞 개발용 표지(`[common]`·`[d1]`·`[m:nextTier]` 처럼 영문으로 시작하는 대괄호)를 뗀다.
 * 숫자 단축키 `[1]` 은 UI 가 따로 붙이므로 라벨 안의 대괄호는 모두 내부 표지로 본다(한글 〔종류〕는 그대로).
 */
const ID_TAG = /^\s*\[[A-Za-z][\w:.-]*\]\s*/;
export function cleanLabel(label: string): string {
  let s = label ?? '';
  while (ID_TAG.test(s)) s = s.replace(ID_TAG, '');
  return s;
}

/** 가격 글이 라벨에 이미 있는가 (띄어쓰기 차이 무시 — '40 전표' / '40전표') */
export function hasPrice(label: string, price: string): boolean {
  const flat = (t: string): string => t.replace(/\s+/g, '');
  return flat(label).includes(flat(price));
}

/** 이동에 쓰는 키 (단축키로 주지 않는다) */
const NAV_KEYS = new Set(['w', 'a', 's', 'd', 'W', 'A', 'S', 'D']);
const HOTKEY_POOL = '123456789bcfghijklnoprtuvxyz';

/**
 * 61라운드 플레이 점검 #4: 화면에 보일 단축키. 시스템 키가 한 글자면 그대로, 'd1'·'reroll'·'m:nextTier' 처럼 길면
 * 쓰지 않은 숫자(그다음 글자)를 차례로 준다. 선택은 여전히 시스템 키로 보낸다.
 */
export function menuHotkeys(keys: readonly string[]): string[] {
  const used = new Set(keys.filter((k) => k.length === 1));
  const pool = [...HOTKEY_POOL].filter((c) => !used.has(c) && !NAV_KEYS.has(c));
  return keys.map((k) => (k.length === 1 ? k : (pool.shift() ?? '')));
}

/** 희귀도 칸 수 1~4 (없으면 0) */
export const RARITY_RANK: Readonly<Record<string, number>> = { common: 1, rare: 2, epic: 3, legendary: 4 };

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

/**
 * 29라운드 evolve: 라벨 끝 ' — 설명' 이 detail 과 같으면 떼어 낸 이름과, 이름에 이미 들어 있지 않은 설명.
 * 목록(menuLines)과 카드(choiceCardView)가 같이 쓴다.
 */
export function splitLabel(l: Pick<UiMenuLine, 'label' | 'detail'>): { label: string; detail: string } {
  const raw = cleanLabel(l.label);
  const suffix = l.detail ? ` — ${l.detail}` : '';
  const dup = Boolean(suffix) && raw.endsWith(suffix);
  const label = dup ? raw.slice(0, -suffix.length) : raw;
  const detail = l.detail && (dup || !raw.includes(l.detail)) ? l.detail : '';
  return { label, detail };
}

export function menuLines(m: UiMenu, build?: UiBuildState | null, tx: Tx = (k) => R60_TEXT[k]): SelectLine[] {
  const lab = LAB_MENUS.has(m.id);
  const mixed = mixedKinds(m);
  let prevGroup: string | undefined;
  const hotkeys = menuHotkeys(m.lines.map((l) => l.key));
  return m.lines.map((l, i) => {
    const split = splitLabel(l);
    let label = split.label;
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
    if (price && !hasPrice(label, price)) label = `${label} · ${price}`;
    const detailText = split.detail;
    const meta = choiceMeta(l, build);
    const locked = l.locked?.condition ? fill(tx('locked'), { condition: l.locked.condition }) : '';
    const detail = [meta, detailText, locked].filter(Boolean).join('\n');
    let header: string | undefined;
    if (l.group && l.group !== prevGroup) header = tx(GROUP_KEY[l.group] ?? 'groupFixed');
    if (l.group || !cancel) prevGroup = l.group;
    const enabled = l.enabled && !l.soldOut && !l.locked;
    const note = l.soldOut ? tx('soldOutNote') : l.locked ? tx('lockedNote') : undefined;
    const rarity = l.rarity ? (RARITY_RANK[l.rarity] ?? 0) : 0;
    return {
      key: l.key,
      hotkey: hotkeys[i],
      label,
      enabled,
      detail: detail || undefined,
      indent,
      header,
      note,
      rarity: rarity || undefined,
    };
  });
}
