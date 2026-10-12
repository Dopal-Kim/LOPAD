import type { UiBuildIcon, UiFloorEnd, UiPathNode, UiResult, UiRoute, UiRunSummary } from '../contract/ui';
import { fill } from './fmt';
import { LOOP2E_TEXT } from './textLoop2E';

/**
 * 62 루프 2 UI E (계약 C P1-6·P1-7): 결산 일기장 — 순수 계산 (Phaser 없음, 단위 테스트).
 * 지나온 곳 미니맵 배치 · 칸(시간·처치·받은 피해 …) · 빌드 아이콘 줄 접기 · 층 끝 일기장 문장 나누기 · 버튼.
 */

/** 결산 종류 — death 사망 · floorEnd 층 끝 · legacy 계약 C 이전(요약 없음) */
export type ResultKind = 'death' | 'floorEnd' | 'legacy';

export function resultKind(r: Pick<UiResult, 'cleared' | 'summary' | 'floorEnd'>): ResultKind {
  if (r.floorEnd) return 'floorEnd';
  if (r.summary) return r.summary.cause === 'floorEnd' ? 'floorEnd' : 'death';
  return 'legacy';
}

/** 미니맵 점 하나 */
export interface MapDot {
  id: string;
  type: string;
  x: number;
  y: number;
  /** 지나온 곳 (지난 순서 번호, 아니면 -1) */
  step: number;
  died: boolean;
  current: boolean;
}

export interface MapLayout {
  dots: MapDot[];
  /** 지도 길 (지나지 않은 것 포함 — 흐리게) */
  edges: [MapDot, MapDot][];
  /** 지나온 길 (차례대로) */
  path: MapDot[];
}

/**
 * 노드 지도 → 미니맵 점 (col = 왼 → 오, 같은 col 의 row 를 위 → 아래 고르게). 지도가 없으면 지나온 곳만 한 줄로.
 * (x, y) = 칸 왼쪽 위, w·h = 칸 크기. 점은 칸 안쪽 `inset` 만큼 비운다.
 */
export function mapLayout(
  route: Pick<UiRoute, 'nodes' | 'currentId'> | null,
  path: readonly UiPathNode[],
  x: number,
  y: number,
  w: number,
  h: number,
  inset = 10,
): MapLayout {
  const stepOf = new Map<string, number>();
  path.forEach((p, i) => stepOf.set(p.id, i));
  const died = new Set(path.filter((p) => p.died).map((p) => p.id));
  const nodes = route?.nodes?.length
    ? route.nodes.map((n) => ({ id: n.id, type: n.type, col: n.col, row: n.row, links: n.links ?? [] }))
    : path.map((p, i) => ({
        id: p.id,
        type: p.type,
        col: i,
        row: 0,
        links: path[i + 1] ? [path[i + 1].id] : [],
      }));
  if (!nodes.length) return { dots: [], edges: [], path: [] };
  const cols = [...new Set(nodes.map((n) => n.col))].sort((a, b) => a - b);
  const colIndex = new Map(cols.map((c, i) => [c, i]));
  const iw = Math.max(1, w - inset * 2);
  const ih = Math.max(1, h - inset * 2);
  const dots = new Map<string, MapDot>();
  for (const c of cols) {
    const inCol = nodes.filter((n) => n.col === c).sort((a, b) => a.row - b.row);
    const ci = colIndex.get(c)!;
    const px = cols.length === 1 ? x + w / 2 : x + inset + (iw * ci) / (cols.length - 1);
    inCol.forEach((n, i) => {
      const py = y + inset + (ih * (i + 0.5)) / inCol.length;
      dots.set(n.id, {
        id: n.id,
        type: n.type,
        x: Math.round(px),
        y: Math.round(py),
        step: stepOf.get(n.id) ?? -1,
        died: died.has(n.id),
        current: route?.currentId === n.id,
      });
    });
  }
  const edges: [MapDot, MapDot][] = [];
  for (const n of nodes)
    for (const to of n.links) {
      const a = dots.get(n.id);
      const b = dots.get(to);
      if (a && b) edges.push([a, b]);
    }
  const walked = path.map((p) => dots.get(p.id)).filter((d): d is MapDot => Boolean(d));
  return { dots: [...dots.values()], edges, path: walked };
}

/** 칸 하나 (이름 · 값) */
export interface StatCell {
  key: string;
  label: string;
  value: string;
}

/** 사망 결산 칸: 걸린 시간 · 쓰러뜨린 적 · 받은 피해 */
export function deathStats(s: UiRunSummary): StatCell[] {
  const cells: StatCell[] = [
    { key: 'time', label: labelOf(s.labels, 'time'), value: s.time },
    { key: 'kills', label: labelOf(s.labels, 'kills'), value: String(s.kills) },
    { key: 'damageTaken', label: labelOf(s.labels, 'damageTaken'), value: String(s.damageTaken) },
  ];
  return cells.filter((c) => c.value !== '');
}

/** 층 끝 결산 칸: 계약 labels·values 중 값이 있는 것 (차례 고정 — 시간 · 처치 · 받은 피해 · 단서 · 영혼) */
export function floorEndStats(f: UiFloorEnd): StatCell[] {
  const order = ['time', 'kills', 'damageTaken', 'clues', 'souls'];
  const keys = [...order, ...Object.keys(f.values).filter((k) => !order.includes(k) && k !== 'build')];
  return keys
    .filter((k) => f.values[k] !== undefined && f.values[k] !== '')
    .map((k) => ({ key: k, label: f.labels[k] ?? '', value: f.values[k] }));
}

/** 층 끝 일기장 문장: 본문 · 맺음(마지막 줄 — '다음 장은 아직 그려지지 않았다') */
export function floorEndLines(f: Pick<UiFloorEnd, 'lines'>, fallback: string): { body: string[]; closing: string } {
  const lines = (f.lines ?? []).filter((l) => l && l.trim());
  if (!lines.length) return { body: [], closing: fallback };
  return { body: lines.slice(0, -1), closing: lines[lines.length - 1] };
}

/** 빌드 아이콘 줄 접기: 한 줄 칸 수 · 줄 수 → 보이는 것 + 남은 수 ('+n') */
export function buildRows(
  icons: readonly UiBuildIcon[],
  perRow: number,
  maxRows: number,
): { rows: UiBuildIcon[][]; more: number } {
  const cap = Math.max(1, perRow) * Math.max(1, maxRows);
  const shown = icons.length > cap ? icons.slice(0, cap - 1) : icons.slice();
  const rows: UiBuildIcon[][] = [];
  for (let i = 0; i < shown.length; i += perRow) rows.push(shown.slice(i, i + perRow));
  return { rows, more: icons.length - shown.length };
}

/** 결산 버튼 (key → 할 일). 층 끝은 계약 choices, 사망은 UI 글 — 기억 장 버튼은 둘 다 가운데에 */
export interface EndButton {
  key: 'reborn' | 'memory' | 'closeDiary';
  label: string;
}

export function endButtons(
  f: Pick<UiFloorEnd, 'choices'> | null | undefined,
  tx: { reborn: string; memory: string; closeDiary: string },
  memory: boolean,
): EndButton[] {
  const from = (k: 'reborn' | 'closeDiary'): string => f?.choices?.find((c) => c.key === k)?.label || tx[k];
  const out: EndButton[] = [{ key: 'reborn', label: from('reborn') }];
  if (memory) out.push({ key: 'memory', label: tx.memory });
  out.push({ key: 'closeDiary', label: from('closeDiary') });
  return out;
}

/** 처치자 초상 키 (로드된 것만 — 없으면 null) */
export function portraitOf(
  s: Pick<UiRunSummary, 'killer'> | null | undefined,
  has: (k: string) => boolean,
): string | null {
  const p = s?.killer?.portrait;
  return p && has(p.key) ? p.key : null;
}

/** 칸 이름 대체 (계약 labels 에 없을 때) */
export function labelOf(labels: Record<string, string> | undefined, key: string): string {
  const L = LOOP2E_TEXT;
  const fb: Record<string, string> = {
    killer: L.lbKiller,
    path: L.lbPath,
    time: L.lbTime,
    kills: L.lbKills,
    damageTaken: L.lbDamage,
    build: L.lbBuild,
  };
  return labels?.[key] || fb[key] || '';
}

/** 계약 C 이전 결과(요약 없음)를 같은 결산 꼴로 (처치 수 · 영혼만) */
export function legacySummary(
  r: Pick<UiResult, 'kills' | 'soulsGained' | 'soulsTotal' | 'stageName' | 'floorReached'>,
): UiRunSummary {
  return {
    cause: 'death',
    title: LOOP2E_TEXT.diedTitle,
    killer: null,
    killerLine: '',
    where: r.stageName ? `${r.floorReached}층 · ${r.stageName}` : '',
    path: [],
    pathEmpty: '',
    route: null,
    build: [],
    souls: { gained: r.soulsGained, total: r.soulsTotal, next: null },
    soulsText: fill(LOOP2E_TEXT.soulsGained, { n: r.soulsGained }),
    soulsLine: '',
    labels: {},
    time: '',
    timeMs: 0,
    kills: r.kills,
    damageTaken: 0,
  };
}

/** 빌드 아이콘 그림 키에서 무기 (`ui_traits/<무기>_<개성>` — 결과 페이로드에 무기 id 가 없다). 모르면 undefined */
export function weaponOfBuild(icons: readonly UiBuildIcon[]): string | undefined {
  for (const ic of icons) {
    const m = /^ui_traits\/(katana|greatsword|dagger|bow)_/.exec(ic.iconKey ?? '');
    if (m) return m[1];
  }
  return undefined;
}
