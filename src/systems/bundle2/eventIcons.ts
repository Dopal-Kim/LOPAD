/**
 * 62 루프 2 시스템 D (P1-12 · 계약 UI §22) 사연 선택지의 대가·보상 아이콘 줄 (Phaser 의존 없음 — 테스트).
 * 효과 목록(data/bundle2.json effects)에서 종류·수치를 정하고, 이름은 스토리 63 팩 talk.options[key].cost/gain 문장을 차례로 쓴다
 * ({n} = 그 효과 값 · {curse} = 저주 이름 · {curseGain} = 저주 이득). 숨은 보상(나중에 갚음·지난 생 기록)은 hidden — UI 는 '?'.
 */
import type { UiEventIcon, UiEventIconKind } from '../../contract/ui';
import type { EventEffect, EventTalkOption } from '../../data/bundle2Types';
import { fill } from '../story';

export interface IconRow {
  costs: UiEventIcon[];
  rewards: UiEventIcon[];
}

/** 효과 하나 → (대가인가, 아이콘 종류, 수치, 숨김) — 아이콘이 없는 효과(lore)는 null */
export function effectIcon(e: EventEffect): {
  cost: boolean;
  kind: UiEventIconKind;
  amount?: number;
  hidden?: boolean;
  vars: Record<string, string | number>;
} | null {
  switch (e.kind) {
    case 'gold':
      return { cost: e.value < 0, kind: 'gold', amount: Math.abs(e.value), vars: { n: Math.abs(e.value) } };
    case 'potion':
      return { cost: e.value < 0, kind: 'potion', amount: Math.abs(e.value), vars: { n: Math.abs(e.value) } };
    case 'potionFill':
      return { cost: false, kind: 'potion', vars: {} };
    case 'maxHp':
      return { cost: e.value < 0, kind: 'maxHp', amount: Math.abs(e.value), vars: { n: Math.abs(e.value) } };
    case 'personality':
      return { cost: false, kind: 'growth', amount: e.value, vars: { n: e.value } };
    case 'reroll':
      return { cost: false, kind: 'growth', amount: e.value, vars: { n: e.value } };
    case 'sense':
      return { cost: false, kind: 'sense', amount: e.value, vars: { n: e.value } };
    case 'passive':
      return { cost: false, kind: 'passive', amount: e.choices, vars: { n: e.choices } };
    case 'laterGold':
      return { cost: false, kind: 'unknown', hidden: true, vars: { n: e.value } };
    case 'diaryRead':
      return { cost: false, kind: 'diary', hidden: true, vars: {} };
    case 'extraWave':
      return { cost: true, kind: 'enemies', amount: e.value, vars: { n: e.value } };
    case 'shopDiscount':
      return {
        cost: false,
        kind: 'discount',
        amount: Math.round(e.value * 100),
        vars: { n: Math.round(e.value * 100) },
      };
    case 'curse':
      return { cost: true, kind: 'curse', vars: {} };
    case 'consumable':
      return { cost: false, kind: 'unknown', amount: e.value, vars: { n: e.value } };
    case 'lore':
      return null;
  }
}

/**
 * 선택지 아이콘 줄. texts = 63 팩 talk.options[key] (없으면 효과 종류 이름) · names = 종류 → 기본 이름 · curse = 저주 이름·이득
 */
export function iconRow(
  effects: readonly EventEffect[],
  texts: Pick<EventTalkOption, 'cost' | 'gain'> | undefined,
  names: Partial<Record<UiEventIconKind, string>>,
  curse?: { name: string; benefit: string },
  unknownLabel = '?',
): IconRow {
  const out: IconRow = { costs: [], rewards: [] };
  let ci = 0;
  let gi = 0;
  for (const e of effects) {
    const ic = effectIcon(e);
    if (!ic) continue;
    const vars = { ...ic.vars, curse: curse?.name ?? '', curseGain: curse?.benefit ?? '' };
    const src = ic.cost ? texts?.cost[ci++] : texts?.gain[gi++];
    const fallback = ic.hidden
      ? unknownLabel
      : `${names[ic.kind] ?? ''}${ic.amount !== undefined ? ` ${ic.amount}` : ''}`;
    const label = src !== undefined ? fill(src, vars) : fallback.trim();
    const icon: UiEventIcon = {
      kind: ic.kind,
      label,
      ...(ic.amount !== undefined ? { amount: ic.amount } : {}),
      ...(ic.hidden || label === unknownLabel ? { hidden: true } : {}),
    };
    (ic.cost ? out.costs : out.rewards).push(icon);
  }
  // 저주 선택지는 이득(저주가 주는 것)도 보상 칸에 — 팩 gain '{curseGain}'
  if (curse && effects.some((e) => e.kind === 'curse') && texts && texts.gain.length > gi)
    for (const g of texts.gain.slice(gi))
      out.rewards.push({ kind: 'gold', label: fill(g, { curseGain: curse.benefit, curse: curse.name }) });
  return out;
}
