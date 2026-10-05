import type {
  UiBuildState,
  UiGrowth,
  UiGrowthMarkKind,
  UiMenu,
  UiMenuLine,
  UiTagId,
  UiVerbSlot,
  UiWeaponVerbs,
} from '../contract/ui';
import { tagName } from './buildView';
import { choiceLines } from './choiceCardView';
import { fill } from './fmt';
import { menuHotkeys, splitLabel } from './menuView';
import { GROWTH_TEXT, type GrowthTextKey } from './textGrowth';
import { GROWTH_CARD, LIVE_TAGS_BY_STAGE, VERB_KEY_FALLBACK } from './themeGrowth';

/**
 * 61 단계 4 P12 무기 성장 UI — 순수 계산 (Phaser 없음). 계약 §18:
 * HUD 각성 게이지(눈금 ◇ 개성 발현·단련 / ◆ 1차·2차 각성, 다음 눈금까지 남은 수) · 선택 카드(개성 발현·1차 각성·2차 각성·단련) ·
 * 처음 안내 카드 · Tab 성장도 나무(기본 → 갈래 3 → 길 6).
 */

export type GrowthTx = (key: GrowthTextKey) => string;
const defaultTx: GrowthTx = (k) => GROWTH_TEXT[k];

/** 선택 카드 종류 (메뉴 줄 `kind`) */
export type GrowthKind = 'trait' | 'awaken1' | 'awaken2' | 'temper';
export const GROWTH_KINDS: readonly GrowthKind[] = ['trait', 'awaken1', 'awaken2', 'temper'];

function isGrowthKind(k: unknown): k is GrowthKind {
  return typeof k === 'string' && (GROWTH_KINDS as readonly string[]).includes(k);
}

/** 큰 눈금(◆ 각성)인가 */
export function isBigMark(kind: UiGrowthMarkKind): boolean {
  return kind === 'awaken1' || kind === 'awaken2';
}

/** 눈금 이름 ('개성 발현' · '1차 각성' · '2차 각성' · '단련') */
export function markName(kind: UiGrowthMarkKind, tx: GrowthTx = defaultTx): string {
  switch (kind) {
    case 'awaken1':
      return tx('markAwaken1');
    case 'awaken2':
      return tx('markAwaken2');
    case 'temper':
      return tx('markTemper');
    default:
      return tx('markTrait');
  }
}

// ---------------------------------------------------------------------------------------------
// HUD 각성 게이지

export interface GaugeTick {
  /** 막대 왼쪽 끝에서 마름모 가운데 x (정수) */
  x: number;
  big: boolean;
  /** 지남 · 다음 눈금 · 아직 */
  state: 'done' | 'next' | 'todo';
}

export interface GaugeLayout {
  /** 찬 부분 폭 (막대 왼쪽 끝에서) */
  fillW: number;
  ticks: GaugeTick[];
  /** 다음 눈금까지 남은 수 (더 없으면 null) */
  remain: { n: number; kind: UiGrowthMarkKind } | null;
}

/**
 * 막대 폭 `w` 안의 눈금 자리. 막대 오른쪽 끝 = 이번 층 마지막 눈금(또는 다음 눈금) — 그 너머는 가득.
 * 큰 마름모가 막대 밖으로 나가지 않게 양끝을 `inset` 만큼 들인다.
 */
export function gaugeLayout(g: Pick<UiGrowth, 'gauge' | 'marks' | 'next'>, w: number, inset = 0): GaugeLayout {
  const marks = Array.isArray(g.marks) ? g.marks : [];
  const gauge = Math.max(0, Number.isFinite(g.gauge) ? g.gauge : 0);
  const top = Math.max(1, ...marks.map((m) => m.at), g.next?.at ?? 0);
  const span = Math.max(1, w - inset * 2);
  const xOf = (v: number): number => inset + Math.round((span * Math.max(0, Math.min(top, v))) / top);
  const nextAt = g.next ? g.next.at : null;
  const ticks: GaugeTick[] = marks
    .slice()
    .sort((a, b) => a.at - b.at)
    .map((m) => ({
      x: xOf(m.at),
      big: isBigMark(m.kind),
      state: m.done ? 'done' : nextAt !== null && m.at === nextAt && m.kind === g.next!.kind ? 'next' : 'todo',
    }));
  const fillW = gauge <= 0 ? 0 : gauge >= top ? w : xOf(gauge);
  const remain = g.next ? { n: Math.max(0, Math.ceil(g.next.at - gauge)), kind: g.next.kind } : null;
  return { fillW, ticks, remain };
}

/** '1차 각성까지 40' (더 없으면 '모든 눈금') */
export function remainText(remain: GaugeLayout['remain'], tx: GrowthTx = defaultTx): string {
  if (!remain) return tx('remainDone');
  return fill(tx('remain'), { what: markName(remain.kind, tx), n: remain.n });
}

// ---------------------------------------------------------------------------------------------
// 키 · 태그

/** 4동사 칸 → 키 이름(키캡 그림용)과 지금 그 칸의 동작 이름 (스냅샷 `weaponVerbs`, 없으면 기본 키) */
export function verbKey(
  slot: UiVerbSlot | null | undefined,
  verbs?: UiWeaponVerbs | null,
): { key: string; name: string } | null {
  if (!slot) return null;
  const v = verbs?.verbs?.find((x) => x.slot === slot);
  if (v?.key) return { key: v.key, name: v.name ?? '' };
  const key = VERB_KEY_FALLBACK[slot];
  return key ? { key, name: '' } : null;
}

/** 이 층에서 켜진 태그만 (표를 모르는 층이면 그대로) */
export function liveTags(tags: readonly UiTagId[] | null | undefined, stageIndex: number): UiTagId[] {
  if (!Array.isArray(tags)) return [];
  const live = LIVE_TAGS_BY_STAGE[stageIndex];
  return live ? tags.filter((t) => live.includes(t)) : [...tags];
}

// ---------------------------------------------------------------------------------------------
// 선택 카드

/** 무기 성장 선택 메뉴인가 — `evolve` 이고 그만두기를 뺀 줄이 2~3 장, 모두 성장 칸 종류 */
export function isGrowthMenu(m: Pick<UiMenu, 'id' | 'lines' | 'cancelKey'>): boolean {
  if (m.id !== 'evolve') return false;
  const lines = choiceLines(m as UiMenu);
  return lines.length >= 2 && lines.length <= 3 && lines.every((l) => isGrowthKind(l.kind));
}

export interface GrowthCardData {
  key: string;
  hotkey: string;
  kind: GrowthKind;
  head: string;
  headSlot: number;
  name: string;
  /** 한 문장 (개성) · 한 줄 양상 (갈래·길) · 설명 (단련) */
  line: string;
  enabled: boolean;
  /** 바뀌는 칸의 키 이름과 지금 동작 이름 (단련은 null) */
  verb: { key: string; name: string } | null;
  /** 이 층에서 켜진 태그 이름 */
  tags: string[];
  /** 무기 모양 그림 텍스처 키 (없으면 null — 글자로 대신) */
  look: string | null;
  /** 그림이 없을 때 대신 쓸 글 (무기 이름) */
  lookText: string;
  /** 1차 각성 카드 아래 2차 길 미리보기 */
  paths: { name: string; line: string }[];
  /** 단련 카드의 단련 눈금 */
  temper: { n: number; max: number } | null;
}

interface CardOpts {
  growth?: UiGrowth | null;
  verbs?: UiWeaponVerbs | null;
  stageIndex?: number;
  build?: UiBuildState | null;
  tx?: GrowthTx;
}

function headOf(kind: GrowthKind, tx: GrowthTx): string {
  return kind === 'awaken1'
    ? tx('headAwaken1')
    : kind === 'awaken2'
      ? tx('headAwaken2')
      : kind === 'temper'
        ? tx('headTemper')
        : tx('headTrait');
}

function cardOf(l: UiMenuLine, hotkey: string, o: CardOpts): GrowthCardData {
  const tx = o.tx ?? defaultTx;
  const kind = l.kind as GrowthKind;
  const { label, detail } = splitLabel(l);
  const branch = kind === 'awaken1' ? (l.branch ?? null) : null;
  const path = kind === 'awaken2' ? (l.path ?? null) : null;
  const g = o.growth ?? null;
  const ownBranch = g?.branch ? g.branches?.find((b) => b.id === g.branch) : undefined;
  const slot = kind === 'temper' ? null : (branch?.verb ?? path?.verb ?? l.verb ?? null);
  const look = branch?.lookKey ?? path?.lookKey ?? (kind === 'awaken2' ? ownBranch?.lookKey : undefined) ?? null;
  return {
    key: l.key,
    hotkey,
    kind,
    head: headOf(kind, tx),
    headSlot: GROWTH_CARD.headSlot[kind] ?? GROWTH_CARD.focusSlot,
    name: branch?.name || path?.name || label,
    line: branch?.line || path?.line || detail,
    enabled: l.enabled && !l.locked && !l.soldOut,
    verb: verbKey(slot, o.verbs),
    tags: liveTags(l.tags, o.stageIndex ?? 0).map((t) => tagName(t, o.build)),
    look,
    lookText: g?.weaponName ?? '',
    paths: branch?.paths ? branch.paths.map((p) => ({ name: p.name, line: p.line })) : [],
    temper: kind === 'temper' && g?.temper ? { n: g.temper.n, max: g.temper.max } : null,
  };
}

/** 성장 메뉴 카드 (그만두기 줄 제외, 메뉴 순서 그대로) */
export function growthCards(m: UiMenu, o: CardOpts = {}): GrowthCardData[] {
  const hk = menuHotkeys(m.lines.map((l) => l.key));
  return choiceLines(m)
    .filter((l) => isGrowthKind(l.kind))
    .map((l) => cardOf(l, hk[m.lines.indexOf(l)] || l.key, o));
}

/** 카드 폭 (3장 · 2장) */
export function growthCardW(n: number): number {
  return n <= 2 ? GROWTH_CARD.w2 : GROWTH_CARD.w3;
}

// ---------------------------------------------------------------------------------------------
// 처음 안내 카드

export type GuideKind = 'trait' | 'awaken1' | 'awaken2';

/** 이 메뉴 앞에 띄울 안내 (메타 기준 처음일 때만 — `growth.firstTime`). 단련 눈금 메뉴는 안내하지 않는다 */
export function guideKind(m: UiMenu, g: Pick<UiGrowth, 'firstTime'> | null | undefined): GuideKind | null {
  if (!g?.firstTime || !isGrowthMenu(m)) return null;
  const kinds = new Set(choiceLines(m).map((l) => l.kind));
  if (kinds.has('temper')) return null;
  const k: GuideKind | null = kinds.has('awaken1')
    ? 'awaken1'
    : kinds.has('awaken2')
      ? 'awaken2'
      : kinds.has('trait')
        ? 'trait'
        : null;
  return k && g.firstTime[k] ? k : null;
}

export function guideText(k: GuideKind, tx: GrowthTx = defaultTx): { title: string; lines: [string, string] } {
  if (k === 'awaken1') return { title: tx('guideAwaken1Title'), lines: [tx('guideAwaken1_1'), tx('guideAwaken1_2')] };
  if (k === 'awaken2') return { title: tx('guideAwaken2Title'), lines: [tx('guideAwaken2_1'), tx('guideAwaken2_2')] };
  return { title: tx('guideTraitTitle'), lines: [tx('guideTrait1'), tx('guideTrait2')] };
}

// ---------------------------------------------------------------------------------------------
// Tab 성장도 나무

/** 지나온 길(lit) · 지금 고를 수 있는 다음(open) · 닫힌 것(shut) */
export type TreeState = 'lit' | 'open' | 'shut';

export interface TreeNode {
  id: string;
  name: string;
  col: 0 | 1 | 2;
  /** 나무 위 끝에서 점 가운데 y */
  y: number;
  state: TreeState;
  parent: string | null;
}

/**
 * 기본(가운데) → 갈래 3(각 두 길의 가운데) → 길 6(한 줄씩). 각성 단계(stage)와 고른 갈래·길로 상태를 매긴다:
 * 0 = 갈래 open · 길 shut / 1 = 고른 갈래 lit · 그 두 길 open · 나머지 shut / 2 = 고른 길 lit · 나머지 shut.
 */
export function treeNodes(
  g: Pick<UiGrowth, 'branches' | 'branch' | 'path' | 'stage'>,
  rowH: number,
  baseName: string,
): { nodes: TreeNode[]; h: number } {
  const branches = Array.isArray(g.branches) ? g.branches : [];
  const stage = g.stage ?? 0;
  const nodes: TreeNode[] = [];
  const rows = Math.max(
    1,
    branches.reduce((n, b) => n + Math.max(1, b.paths?.length ?? 0), 0),
  );
  const h = rows * rowH;
  nodes.push({ id: '__base', name: baseName, col: 0, y: Math.round(h / 2), state: 'lit', parent: null });
  let row = 0;
  for (const b of branches) {
    const paths = b.paths ?? [];
    const n = Math.max(1, paths.length);
    const chosenB = stage >= 1 && g.branch === b.id;
    const bState: TreeState = stage === 0 ? 'open' : chosenB ? 'lit' : 'shut';
    nodes.push({
      id: b.id,
      name: b.name,
      col: 1,
      y: Math.round((row + n / 2) * rowH),
      state: bState,
      parent: '__base',
    });
    paths.forEach((p, j) => {
      const pState: TreeState =
        stage >= 2 ? (chosenB && g.path === p.id ? 'lit' : 'shut') : stage === 1 && chosenB ? 'open' : 'shut';
      nodes.push({
        id: p.id,
        name: p.name,
        col: 2,
        y: Math.round((row + j + 0.5) * rowH),
        state: pState,
        parent: b.id,
      });
    });
    row += n;
  }
  return { nodes, h };
}

/** 고른 갈래·길 이름 (' · 선풍 · 회오리', 없으면 '') — 일기장 무기 줄 */
export function growthRouteName(g: Pick<UiGrowth, 'branches' | 'branch' | 'path'> | null | undefined): string {
  if (!g?.branch) return '';
  const b = g.branches?.find((x) => x.id === g.branch);
  if (!b) return '';
  const p = g.path ? b.paths?.find((x) => x.id === g.path) : undefined;
  return [b.name, p?.name]
    .filter(Boolean)
    .map((t) => ` · ${t}`)
    .join('');
}

// ---------------------------------------------------------------------------------------------
// 이벤트 페이로드 (모자라도 깨지지 않게 읽는다)

const str = (v: unknown): string => (typeof v === 'string' ? v.trim() : '');

/** `ui:awaken` `{ stage, weapon, branch, path?, name, line, lookKey? }` → 배너 글. 이름이 없으면 null */
export function readAwaken(p: unknown): { stage: 1 | 2; name: string; line: string; look: string | null } | null {
  const o = p && typeof p === 'object' ? (p as Record<string, unknown>) : {};
  const name = str(o.name);
  if (!name) return null;
  return { stage: o.stage === 2 ? 2 : 1, name, line: str(o.line), look: str(o.lookKey) || null };
}

/** `ui:trait-gained` (UiGrowthTrait) → 알림 글. 이름이 없으면 null */
export function readTrait(p: unknown): { name: string; line: string; verb: UiVerbSlot | null } | null {
  const o = p && typeof p === 'object' ? (p as Record<string, unknown>) : {};
  const name = str(o.name);
  if (!name) return null;
  const verb = str(o.verb);
  const slots: readonly string[] = ['attack', 'signature', 'dash', 'hold'];
  return { name, line: str(o.line), verb: slots.includes(verb) ? (verb as UiVerbSlot) : null };
}
