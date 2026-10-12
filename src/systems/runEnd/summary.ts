/**
 * 62 루프 2 시스템 C (P16 §2·§3 · 점검 P1-6·P1-7) 결산 만들기 (Phaser 의존 없음): 처치자 · 지나온 노드 · 빌드 아이콘 줄 ·
 * 층 끝 결산(`UiFloorEnd`) · 결산(`UiRunSummary`). 런 로그(`RunLog.peek`)와 런 상태에서 값을 모은다.
 */
import { BOSSES, ENEMIES } from '../../data';
import { growthBranch, traitDef } from '../../data/growth';
import { RUN_END } from '../../data/runEnd';
import { memoryDef } from '../../data/memory';
import type {
  UiBuildIcon,
  UiFloorEnd,
  UiKiller,
  UiNextUnlock,
  UiPathNode,
  UiRelic,
  UiRoute,
  UiRunStats,
  UiRunSummary,
  UiTagId,
} from '../../contract/ui';
import type { RunLogSummary } from '../runlog/runLog';
import { fill } from '../story';

/** 런 로그 사망 원인 ('enemy:<id>:<kind>' · 'boss:<id>:<패턴>' · 'unknown') → 처치자 (초상은 씬이 붙인다) */
export function killerOf(cause: string | null | undefined): UiKiller {
  const [kind, id] = (cause ?? '').split(':');
  if (kind === 'boss' && id) return { kind: 'boss', id, name: BOSSES[id]?.name ?? id };
  if (kind === 'enemy' && id) return { kind: 'enemy', id, name: ENEMIES[id]?.name ?? id };
  return { kind: 'unknown', id: '', name: '' };
}

/** 지나온 노드 (런 로그 노드 순서 · 노드 지도 칸 자리). died = 마지막 노드(사망일 때) */
export function pathOf(log: Pick<RunLogSummary, 'nodes'> | null, route: UiRoute | null, died: boolean): UiPathNode[] {
  if (!log) return [];
  const at = new Map((route?.nodes ?? []).map((n) => [n.id, n]));
  const nodes = log.nodes.filter((n) => n.id !== '-');
  return nodes.map((n, i) => {
    const r = at.get(n.id);
    return {
      id: n.id,
      type: r?.type ?? n.kind,
      name: r?.name || n.name,
      col: r?.col ?? i,
      row: r?.row ?? 0,
      ...(died && i === nodes.length - 1 ? { died: true } : {}),
    };
  });
}

/** 시간·처치·받은 피해 (런 로그가 없으면 kills 만) */
export function statsOf(log: Pick<RunLogSummary, 'durationMs' | 'totals'> | null, kills: number): UiRunStats {
  return {
    timeMs: log?.durationMs ?? 0,
    kills: log ? Math.max(log.totals.kills, kills) : kills,
    damageTaken: log?.totals.damageTaken ?? 0,
  };
}

export interface BuildIconInput {
  weapon: string;
  branchId: string | null;
  pathId: string | null;
  traits: readonly string[];
  relics: readonly UiRelic[];
  keepsake: string | null;
  aspect: string | null;
  /** 개성 그림 키 (로드됐으면) */
  traitIcon?: (weapon: string, traitId: string) => string | undefined;
  /** 기억 그림 키 (로드됐으면) */
  memoryIcon?: (id: string) => string | undefined;
}

/** 빌드 아이콘 줄: 갈래 → 길 → 개성 → 유품 → 양상 → 소품 */
export function buildIcons(i: BuildIconInput): UiBuildIcon[] {
  const out: UiBuildIcon[] = [];
  const b = growthBranch(i.weapon, i.branchId);
  if (b) {
    out.push({ kind: 'branch', id: b.id, name: b.name });
    const p = b.paths.find((x) => x.id === i.pathId);
    if (p) out.push({ kind: 'path', id: p.id, name: p.name });
  }
  for (const id of i.traits) {
    const t = traitDef(id);
    if (!t) continue;
    const icon = i.traitIcon?.(i.weapon, id);
    out.push({ kind: 'trait', id, name: t.name, tag: t.tag as UiTagId, ...(icon ? { iconKey: icon } : {}) });
  }
  for (const r of i.relics)
    out.push({
      kind: 'relic',
      id: r.id,
      name: r.name,
      ...(r.tag ? { tag: r.tag } : {}),
      ...(r.iconKey ? { iconKey: r.iconKey } : {}),
    });
  for (const [kind, id] of [
    ['aspect', i.aspect],
    ['keepsake', i.keepsake],
  ] as const) {
    const m = id ? memoryDef(id) : undefined;
    if (!m) continue;
    const icon = i.memoryIcon?.(m.id);
    out.push({ kind, id: m.id, name: m.name, ...(icon ? { iconKey: icon } : {}) });
  }
  return out;
}

/** 모은 단서 한 줄 (없음 · 일부 · 전부) */
export function cluesLineOf(found: number, total: number): string {
  const C = RUN_END.floorEnd.summary.cluesLine;
  return found <= 0 ? C.none : found >= total ? C.all : C.some;
}

/** 층 끝 결산 (`UiFloorEnd`) — 문장 = 스토리 63 팩 floorEnd.summary */
export function floorEndOf(o: {
  floor: number;
  stageId: string;
  floorTitle: string;
  stats: UiRunStats;
  build: UiBuildIcon[];
  clues: { found: number; total: number };
  soulsGained: number;
}): UiFloorEnd {
  const S = RUN_END.floorEnd.summary;
  const lines = [S.empire[o.stageId], S.opening[o.stageId], cluesLineOf(o.clues.found, o.clues.total)];
  if (o.stats.damageTaken <= 0) lines.push(S.noHit);
  lines.push(S.closing);
  return {
    ...o.stats,
    floor: o.floor,
    title: fill(S.title, { floor: o.floor }),
    floorTitle: o.floorTitle,
    build: o.build.map((b) => ({ ...b })),
    clues: { ...o.clues },
    lines: lines.filter((l): l is string => Boolean(l)),
    labels: { ...S.fields },
    values: {
      time: timeText(o.stats.timeMs),
      kills: fill(S.values.kills, { n: o.stats.kills }),
      damageTaken: fill(S.values.damageTaken, { n: o.stats.damageTaken }),
      clues: fill(S.values.clues, { n: o.clues.found, max: o.clues.total }),
      souls: fill(S.values.souls, { n: o.soulsGained }),
    },
    footer: S.footer,
    choices: [
      { key: 'reborn', label: S.buttons.reborn },
      { key: 'closeDiary', label: S.buttons.close },
    ],
  };
}

/** '{m}분 {s}초' (층 끝 values.time) */
export function timeText(ms: number): string {
  const sec = Math.max(0, Math.round(ms / 1000));
  return fill(RUN_END.floorEnd.summary.values.time, { m: Math.floor(sec / 60), s: sec % 60 });
}

/** 처치자 한 줄 (정해진 적 줄 → 군주 줄 → 틀에서 pick 번째). pick = 시드에서 고른 정수 */
export function killerLineOf(k: UiKiller | null, stageId: string, pick: number): string {
  const K = RUN_END.deathSummary.killerLines;
  const at = <T>(list: readonly T[]): T => list[((pick % list.length) + list.length) % list.length];
  if (!k || k.kind === 'unknown') return K.unknown;
  if (k.kind === 'boss') {
    const b = K.boss[stageId];
    if (b?.length) return at(b);
  }
  if (k.kind === 'enemy' && K.byEnemy[k.id]) return K.byEnemy[k.id];
  return fill(at(K.creature), { killer: k.name });
}

/** 영혼 한 줄 — 다 떠올림 · 처음 모임 · 지금 떠올릴 수 있음 · 다음 기억까지 */
export function soulsLineOf(next: UiNextUnlock | null, firstEver: boolean): string {
  const S = RUN_END.deathSummary.souls;
  if (!next) return S.all;
  if (next.left > 0) return fill(S.next, { n: next.left });
  return firstEver ? S.firstReady : S.ready;
}

/** 결산 (`UiRunSummary`) */
export function runSummaryOf(o: {
  cause: UiRunSummary['cause'];
  log: RunLogSummary | null;
  kills: number;
  route: UiRoute | null;
  build: UiBuildIcon[];
  killer: UiKiller | null;
  floor: number;
  stageId: string;
  /** 처치자 줄 고르기 정수 (시드에서) */
  pick: number;
  /** 메타에서 처음으로 떠올릴 수 있게 된 순간인가 */
  firstReady: boolean;
  souls: { gained: number; total: number; next: UiNextUnlock | null };
}): UiRunSummary {
  const died = o.cause === 'death';
  const D = RUN_END.deathSummary;
  const path = pathOf(o.log, o.route, died);
  const last = path[path.length - 1];
  return {
    ...statsOf(o.log, o.kills),
    cause: o.cause,
    title: D.title,
    killer: died ? o.killer : null,
    killerLine: died ? killerLineOf(o.killer, o.stageId, o.pick) : '',
    where: died && last ? fill(D.where, { floor: o.floor, place: last.name }) : '',
    path,
    pathEmpty: died && path.length <= 1 ? D.pathEmpty : '',
    route: o.route,
    build: o.build.map((b) => ({ ...b })),
    souls: { gained: o.souls.gained, total: o.souls.total, next: o.souls.next ? { ...o.souls.next } : null },
    soulsText: fill(D.souls.gained, { n: o.souls.gained }),
    soulsLine: soulsLineOf(o.souls.next, o.firstReady),
    labels: { ...D.fields },
    time: timeText(statsOf(o.log, o.kills).timeMs),
  };
}
