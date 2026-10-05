import type { UiBuildState, UiMenu } from '../contract/ui';
import { type Tx } from './buildView';
import { fill } from './fmt';
import { choiceMeta, splitLabel } from './menuView';
import { CHOICE_KIND_NAME, CHOICE_MENU_HEAD, R60_TEXT } from './textBuild';
import { CHOICE_CARD } from './themeBuild';

/**
 * 60라운드 Q38 개성·보상·패시브 3지선다 카드 3장 — 카드 한 장에 그릴 글·상태 (순수 계산).
 * 줄 만들기 규칙은 목록(menuView)과 같다: 라벨 끝 설명 중복 제거, 희귀도·태그 한 줄, 잠김 조건.
 * 목록과 달리 〔종류〕는 섞이지 않아도 늘 머리표로 보인다(카드마다 종류가 한눈에 보이게).
 */
export interface ChoiceCardData {
  key: string;
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
  return choiceLines(m).map((l) => {
    const { label, detail } = splitLabel(l);
    const head = (l.kind && CHOICE_KIND_NAME[l.kind]) || l.kind || CHOICE_MENU_HEAD[m.id] || '';
    const locked = l.locked?.condition ? fill(tx('locked'), { condition: l.locked.condition }) : '';
    const enabled = l.enabled && !l.soldOut && !l.locked;
    const note = enabled ? '' : l.locked ? tx('lockedNote') : l.soldOut ? tx('soldOutNote') : tx('disabledNote');
    return {
      key: l.key,
      head,
      headSlot: (l.kind && CHOICE_CARD.kindSlot[l.kind]) || CHOICE_CARD.kindSlotDefault,
      name: label,
      meta: choiceMeta(l, build),
      rarityRank: l.rarity ? (CHOICE_CARD.rarityRank[l.rarity] ?? 0) : 0,
      detail,
      locked,
      enabled,
      note,
    };
  });
}

/** 카드 조작 안내 한 줄 — 카드 키를 '·' 로 잇고, 그만두기 줄이 있으면 덧붙인다 */
export function choiceHint(m: UiMenu, tx: Tx = (k) => R60_TEXT[k]): string {
  const keys = choiceLines(m)
    .map((l) => l.key)
    .join('·');
  const base = fill(tx('choiceHint'), { keys });
  const cancel = m.cancelKey && m.lines.some((l) => l.key === m.cancelKey);
  return cancel ? base + fill(tx('choiceHintCancel'), { key: m.cancelKey! }) : base;
}
