/**
 * 62 루프 2 시스템 G (UI 요청): 종군 상인 말하기 메뉴 'shopTalk' 의 UI 재료 — Phaser 없음.
 * - `UiMenu.event`(사연 메뉴와 같은 머리: 말하는 이 · 초상 · 첫 마디) — UI 가 사연 대화 꼴로 그린다
 * - '외상을 단다' 줄의 대가 = 아이콘 줄 `costs`(저주) + 아이콘을 안 그리는 UI 를 위한 `detail` 글 (용어집 — '상점' 금지, '장터')
 */
import type { UiEventIcon, UiEventScene, UiMenuLine } from '../../contract/ui';
import { BUNDLE2 } from '../../data/bundle2';
import { curseDef } from '../../data/build';
import { fill } from '../../systems/story';

/** 상인 말하기 머리 (사연 UiEventScene 과 같은 꼴 — id 'merchant', 설명 문단 없음) */
export function merchantScene(
  speaker: string,
  greet: string,
  portrait: { key: string; frame: string | number } | null,
): UiEventScene {
  return {
    id: 'merchant',
    name: speaker,
    speaker,
    ...(portrait ? { portrait: { ...portrait } } : {}),
    greet,
    intro: [],
    ...(BUNDLE2.events.ui ? { heads: { ...BUNDLE2.events.ui } } : {}),
  };
}

/** '외상을 단다' 줄 — 대가 아이콘(저주 '외상') · detail = '내준다 저주 외상 — 처치 전표 0 · 장터 값 +20%' */
export function creditLine(curseId: string, label: string): UiMenuLine {
  const c = curseDef(curseId);
  const cost = c ? fill(BUNDLE2.shop.talk?.merchant.creditCost ?? '{curse}', { curse: c.name }) : '';
  const costs: UiEventIcon[] = c ? [{ kind: 'curse', label: cost }] : [];
  const head = BUNDLE2.events.ui?.costHead ?? '';
  const detail = c ? `${head} ${cost} — ${c.penalty}`.trim() : '';
  return { key: 'credit', label, enabled: true, costs, ...(detail ? { detail } : {}) };
}
