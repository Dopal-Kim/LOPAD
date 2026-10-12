import type { UiBuildState, UiMenu, UiMenuLine } from '../contract/ui';
import { type Tx } from './buildView';
import { fill } from './fmt';
import { RARITY_RANK, choiceMeta, menuHotkeys, splitLabel } from './menuView';
import { CHOICE_KIND_NAME, CHOICE_MENU_HEAD, R60_TEXT } from './textBuild';
import { CHOICE_CARD } from './themeBuild';
import { tagName } from './buildView';
import { l2eText } from './textLoop2E';

/**
 * 60라운드 Q38 개성·보상·패시브 3지선다 카드 3장 — 카드 한 장에 그릴 글·상태 (순수 계산).
 * 줄 만들기 규칙은 목록(menuView)과 같다: 라벨 끝 설명 중복 제거, 희귀도·태그 한 줄, 잠김 조건.
 * 목록과 달리 〔종류〕는 섞이지 않아도 늘 머리표로 보인다(카드마다 종류가 한눈에 보이게).
 */
export interface ChoiceCardData {
  key: string;
  /** 61라운드: 화면에 보이고 누르는 단축키 (menuHotkeys) */
  hotkey: string;
  /** 머리표 (〔〕 없이 종류 이름) */
  head: string;
  /** 머리표 띠 색 (층 강조 슬롯) */
  headSlot: number;
  name: string;
  /** 희귀도 · 태그 (없으면 '') */
  meta: string;
  /** 희귀도 칸 수 1~4 (없으면 0) */
  rarityRank: number;
  detail: string;
  /** '잠김 — 조건' (잠기지 않았으면 '') */
  locked: string;
  enabled: boolean;
  /** 못 고르는 까닭 꼬리 글 ('(잠김)'·'(팔림)'·'(불가)', 고를 수 있으면 '') */
  note: string;
  /** 62 루프 2 UI E (계약 C `UiRelic`): 카드 그림 키 (128×128 → 64) — 없으면 그림 칸 없음 */
  icon?: string;
  /** 62 루프 2 UI E: 고름 자리일 때 카드 줄 아래 상세 칸 (수치 한 줄 · 흐린 한 줄) — 카드 앞면에는 수치를 그리지 않는다 */
  zoom?: { detail: string; flavor: string };
}

/** 그만두기 줄을 뺀 카드 줄 */
export function choiceLines(m: UiMenu): UiMenu['lines'] {
  return m.lines.filter((l) => l.key !== m.cancelKey);
}

/** 카드 3장 레이아웃을 쓰는 메뉴인가 — 개성·보상·패시브 중 그만두기를 뺀 칸이 정확히 3 (그 밖은 목록 유지) */
export function isChoiceCardMenu(m: Pick<UiMenu, 'id' | 'lines' | 'cancelKey'>): boolean {
  return CHOICE_CARD.menus.includes(m.id) && choiceLines(m as UiMenu).length === CHOICE_CARD.count;
}

export function choiceCards(m: UiMenu, build?: UiBuildState | null, tx: Tx = (k) => R60_TEXT[k]): ChoiceCardData[] {
  const hk = menuHotkeys(m.lines.map((l) => l.key));
  const hotkeyOf = (key: string): string => hk[m.lines.findIndex((l) => l.key === key)] || key;
  return choiceLines(m).map((l) => {
    if (l.relic) return relicCard(l, hotkeyOf(l.key), build);
    const { label, detail } = splitLabel(l);
    const head = (l.kind && CHOICE_KIND_NAME[l.kind]) || l.kind || CHOICE_MENU_HEAD[m.id] || '';
    const locked = l.locked?.condition ? fill(tx('locked'), { condition: l.locked.condition }) : '';
    const enabled = l.enabled && !l.soldOut && !l.locked;
    const note = enabled ? '' : l.locked ? tx('lockedNote') : l.soldOut ? tx('soldOutNote') : tx('disabledNote');
    return {
      key: l.key,
      hotkey: hotkeyOf(l.key),
      head,
      headSlot: (l.kind && CHOICE_CARD.kindSlot[l.kind]) || CHOICE_CARD.kindSlotDefault,
      name: label,
      meta: choiceMeta(l, build),
      rarityRank: l.rarity ? (RARITY_RANK[l.rarity] ?? 0) : 0,
      detail,
      locked,
      enabled,
      note,
    };
  });
}

/**
 * 62 루프 2 UI E (계약 C P1-5): 유품 카드 — 개성 카드와 같은 문법. 머리표 '유품' · 그림 · 이름 · '{n}단계 · 태그' · 한 문장(수치 없음) ·
 * 지닌 유품이면 아래 '지닌 유품 — 한 단계 깊어진다'. 수치(`relic.detail`)와 흐린 한 줄(`flavor`)은 고름 자리 상세 칸에서만.
 */
function relicCard(l: UiMenuLine, hotkey: string, build?: UiBuildState | null): ChoiceCardData {
  const r = l.relic!;
  const enabled = l.enabled && !l.soldOut && !l.locked;
  const maxed = r.owned && r.maxLevel > 0 && r.level > r.maxLevel;
  const meta = [r.levelText, r.tag ? tagName(r.tag, build) : ''].filter(Boolean).join(' · ');
  return {
    key: l.key,
    hotkey,
    head: l2eText('relicHead'),
    headSlot: CHOICE_CARD.kindSlot.passive ?? CHOICE_CARD.kindSlotDefault,
    name: r.name || splitLabel(l).label,
    meta,
    rarityRank: r.rarity ? (RARITY_RANK[r.rarity] ?? 0) : 0,
    detail: r.line || splitLabel(l).detail,
    locked: '',
    enabled,
    note: maxed ? l2eText('relicMaxed') : r.owned ? l2eText('relicOwned') : '',
    icon: r.iconKey,
    zoom: { detail: r.detail ?? '', flavor: r.flavor ?? '' },
  };
}

/** 카드 조작 안내 한 줄 — 카드 키를 '·' 로 잇고, 그만두기 줄이 있으면 덧붙인다 */
export function choiceHint(m: UiMenu, tx: Tx = (k) => R60_TEXT[k]): string {
  const hk = menuHotkeys(m.lines.map((l) => l.key));
  const keys = choiceLines(m)
    .map((l) => hk[m.lines.indexOf(l)] || l.key)
    .join('·');
  const base = fill(tx('choiceHint'), { keys });
  const cancel = m.cancelKey && m.lines.some((l) => l.key === m.cancelKey);
  return cancel ? base + fill(tx('choiceHintCancel'), { key: m.cancelKey! }) : base;
}
