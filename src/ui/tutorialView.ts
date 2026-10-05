import type { UiEnemyIncoming, UiSnapshot, UiTutorialStep } from '../contract/ui';
import { carryView } from './carryView';
import type { R53TextKey } from './text';

/** 문구 조회 (화면 쪽에서 `r53Text` + `fill` 로 넘긴다 — 이 파일은 Phaser 없이 시험한다) */
export type TutorialText = (key: R53TextKey, vars?: Record<string, string>) => string;

/**
 * 53라운드 튜토리얼 안내 (51라운드 §3) — 순수 판단. 화면은 `TutorialHud.ts`.
 * '싸우는 법' 패널은 노드 지도의 지금 노드가 '여정'(journey = 탄생 전장·튜토리얼)일 때 띄운다.
 * 단계 카드는 `TUTORIAL_STEP` 이벤트가 기준이고, 그 이벤트를 아직 한 번도 받지 않았으면 여정 노드의 STORY 공지로 대신한다.
 * '주의' 경고는 `ENEMY_INCOMING` 의 delayMs > 0 일 때 (53라운드 Q49·Q60 — 튜토리얼에서만 지연이 온다. 판별은 시스템 몫).
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

/**
 * 안내 패널을 한 번만 띄우기 위한 열쇠. 튜토리얼이 아니면 ''.
 * 61라운드 플레이 점검 #2: 노드마다(런 시드 + 노드 id)가 아니라 **런마다 한 번** — 튜토리얼 뒤 첫 전투 노드('버려진 길'도
 * 여정 노드다)에서 같은 패널이 또 뜨지 않게. 다시 보기는 일시정지 일기장 '싸우는 법'.
 */
export function tutorialKey(s: Pick<UiSnapshot, 'route' | 'lab' | 'seed'>): string {
  return isTutorialNode(s) ? `run|${s.seed}` : '';
}

/**
 * 안내 패널 줄: 이동 + 무기 4동사(61라운드 P1 `weaponVerbs` — 좌 연격 · 우 시그니처 · Space 대쉬 · 좌 홀드 고유 기술, 이름 — 한 줄 설명).
 * 4동사가 아직 없으면 예전 줄: 공격 · 우클릭 보조 · 대쉬 · (넣고 뽑는 무기면) F.
 */
export function tutorialRows(
  s: Pick<UiSnapshot, 'weapon' | 'carry'> & { weaponVerbs?: UiSnapshot['weaponVerbs'] | null },
  t: TutorialText,
): TutorialRow[] {
  const move: TutorialRow = { keys: ['W', 'A', 'S', 'D'], text: t('tutMove') };
  const verbs = s.weaponVerbs?.verbs ?? [];
  if (verbs.length) {
    return [
      move,
      ...verbs
        .filter((v) => v && v.key && v.name)
        .map((v) => ({ keys: [v.key], text: v.hint ? `${v.name} — ${v.hint}` : v.name })),
    ];
  }
  const rows: TutorialRow[] = [move, { keys: [t('keyLeftClick')], text: t('tutAttack') }];
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

/**
 * 적 등장 예고(`ENEMY_INCOMING`)에 '주의' 경고를 띄우는가: 소환까지 시간이 있을 때(delayMs > 0)만.
 * 일반 전투는 delayMs 0 이라 띄우지 않는다 (53라운드 Q60 튜토리얼만 — 지연은 시스템이 튜토리얼에서만 준다).
 */
export function incomingWarns(p: unknown): p is UiEnemyIncoming {
  if (!p || typeof p !== 'object') return false;
  const d = (p as Partial<UiEnemyIncoming>).delayMs;
  return typeof d === 'number' && Number.isFinite(d) && d > 0;
}

/** 단계 카드 한 장 (이벤트·공지 공통) */
export interface StepCard {
  text: string;
  keys: string[];
  /** '2/5' 처럼 그릴 진행 (1부터). 이벤트에 단계 수가 없거나 공지에서 온 카드면 null */
  progress: { n: number; total: number } | null;
}

/**
 * `TUTORIAL_STEP` 페이로드를 카드로. 문구가 비면 null. keys 가 비었으면 문구 끝 괄호의 키를 쓰고,
 * 끝 괄호 키는 문구에서 뗀다 (예전 공지 형식 '…보자. (WASD)' 가 그대로 와도 키 아이콘 한 벌로). index 는 0부터.
 */
export function stepFromEvent(p: unknown): StepCard | null {
  if (!p || typeof p !== 'object') return null;
  const e = p as Partial<UiTutorialStep>;
  if (typeof e.text !== 'string' || !e.text.trim()) return null;
  const given = Array.isArray(e.keys)
    ? e.keys.filter((k): k is string => typeof k === 'string' && k.trim() !== '')
    : [];
  const parsed = parseNoticeKeys(e.text);
  // 문구 끝 괄호의 키는 키 아이콘과 겹치므로 뗀다. 이벤트 keys 가 있으면 그것을 쓴다
  const card = { text: parsed.text, keys: given.length ? given.map((k) => k.trim()) : parsed.keys };
  const ok =
    typeof e.index === 'number' && typeof e.total === 'number' && e.total > 0 && e.index >= 0 && e.index < e.total;
  return {
    ...card,
    progress: ok ? { n: Math.floor(e.index as number) + 1, total: Math.floor(e.total as number) } : null,
  };
}

/** 공지 한 줄을 카드로 (이벤트를 받기 전의 대체 경로) */
export function stepFromNotice(text: string): StepCard {
  return { ...parseNoticeKeys(text), progress: null };
}

/** 두 안내 문구가 같은 단계인가 (끝 괄호 키·앞뒤 공백 무시). 시스템이 STORY 공지와 TUTORIAL_STEP 을 함께 보낼 때 겹침 방지 */
export function sameStepText(a: string, b: string): boolean {
  const x = parseNoticeKeys(a).text;
  return x !== '' && x === parseNoticeKeys(b).text;
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
