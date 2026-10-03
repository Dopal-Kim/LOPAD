import type { UiSnapshot } from '../contract/ui';
import { carryView } from './carryView';
import type { R53TextKey } from './text';

/** 문구 조회 (화면 쪽에서 `r53Text` + `fill` 로 넘긴다 — 이 파일은 Phaser 없이 시험한다) */
export type TutorialText = (key: R53TextKey, vars?: Record<string, string>) => string;

/**
 * 53라운드 튜토리얼 안내 (51라운드 §3) — 순수 판단. 화면은 `TutorialHud.ts`.
 * 계약에 튜토리얼 단계 이벤트가 없어서, 노드 지도의 지금 노드가 '여정'(journey = 탄생 전장·튜토리얼)일 때를 튜토리얼로 본다.
 */
export interface TutorialRow {
  keys: string[];
  text: string;
}

/** 지금 노드 종류 (노드 지도 층이 아니면 null) */
export function currentNodeType(s: Pick<UiSnapshot, 'route'>): string | null {
  const r = s.route;
  if (!r || !Array.isArray(r.nodes)) return null;
  return r.nodes.find((n) => n.id === r.currentId)?.type ?? null;
}

/** 튜토리얼 노드인가 (무기 시험장 제외) */
export function isTutorialNode(s: Pick<UiSnapshot, 'route' | 'lab'>): boolean {
  return !s.lab && currentNodeType(s) === 'journey';
}

/** 안내 패널을 한 번만 띄우기 위한 열쇠 (런 시드 + 노드 id). 튜토리얼이 아니면 '' */
export function tutorialKey(s: Pick<UiSnapshot, 'route' | 'lab' | 'seed'>): string {
  return isTutorialNode(s) ? `${s.seed}|${s.route?.currentId ?? ''}` : '';
}

/** 안내 패널 줄: 이동 · 공격 · 우클릭 보조 · 대쉬 · (넣고 뽑는 무기면) F */
export function tutorialRows(s: Pick<UiSnapshot, 'weapon' | 'carry'>, t: TutorialText): TutorialRow[] {
  const rows: TutorialRow[] = [
    { keys: ['W', 'A', 'S', 'D'], text: t('tutMove') },
    { keys: [t('keyLeftClick')], text: t('tutAttack') },
  ];
  const sec = s.weapon?.secondaryName;
  if (sec) rows.push({ keys: [t('keyRightClick')], text: t('tutSecondary', { secondary: sec }) });
  rows.push({ keys: [t('keySpace')], text: t('tutDash') });
  const c = carryView(s.carry);
  if (c) {
    const name = s.carry?.firstStrike?.trim();
    rows.push({ keys: [c.key], text: name ? t('tutCarry', { name }) : t('tutCarryPlain') });
  }
  return rows;
}

/** 적 등장 경고: 전투가 막 시작됐고(false → true) 튜토리얼 노드일 때 */
export function shouldWarn(prevInCombat: boolean, s: Pick<UiSnapshot, 'inCombat' | 'route' | 'lab'>): boolean {
  return !prevInCombat && Boolean(s.inCombat) && isTutorialNode(s);
}

/**
 * 튜토리얼 공지 한 줄에서 키를 뽑는다. 시스템 공지는 '땅의 표식까지 걸어가 보자. (WASD)' 처럼 끝 괄호에 키를 적는다.
 * 'WASD' 는 네 칸으로, 그 밖은 공백·가운뎃점·쉼표·슬래시·더하기로 나눈다. 괄호가 없으면 키 없음.
 */
export function parseNoticeKeys(text: string): { text: string; keys: string[] } {
  const m = /\s*\(([^()]{1,24})\)\s*$/.exec(text);
  if (!m) return { text: text.trim(), keys: [] };
  const inner = m[1].trim();
  const keys = /^wasd$/i.test(inner)
    ? ['W', 'A', 'S', 'D']
    : inner
        .split(/\s*[·,/+]\s*|\s+/)
        .map((k) => k.trim())
        .filter(Boolean);
  if (keys.length === 0 || keys.length > 6) return { text: text.trim(), keys: [] };
  return { text: text.slice(0, m.index).trim(), keys };
}
