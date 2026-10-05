/**
 * 60라운드 2차 묶음 — 노드 지도 위 정보 (Phaser 의존 없음, 층 시드 결정적):
 * (a) 보상 미리보기 — 잔 구간 전투·위험 노드에 보상 종류(같은 단 두 노드는 다르게, 층 상한, 상점 앞 단 전표 ×1.5),
 *     여정 '버려진 길' = 전표 고정. 공개 = 고를 차례가 된 단만(A안) — 지도 정보 '층 전체'면 전부.
 * (b) 위험 노드 — 층당 1, 잔 단2·단3 의 전투 1개를 엘리트 길 / 저주 길로.
 * (f) 도전 성소 — 잔 일반 전투 노드의 35%.
 * (g) 엘리트 접두어 — 엘리트 길(웨이브마다 1)·성소(1)용으로 미리 굴려 둔다 (지도 정보로 공개).
 * (d) 숨은 노드 — 층 확률(1층 50%)로 잔 일반 전투 노드 하나에 단서, 그 노드 다음(같은 단 아래 칸)에 숨은 노드.
 * (c) 이벤트 내용 — 런 안 중복 없이 서사형 가중으로 미리 고른다 (지도 정보로 이름 공개).
 */
import { BUNDLE2, byStage, eventsOn, prefixIdsOn } from '../../data/bundle2';
import { floorOfStage, onFloor, type FloorScope } from '../../data/floorScope';
import type { ElitePrefixId, Grade, HiddenContent, MapInfoId, RewardKind, RiskKind } from '../../data/bundle2Types';
import type { UiRoute, UiRouteNode } from '../../contract/ui';
import { Rng, hashSeed } from '../rng';
import type { RouteGraph, RouteNode } from '../route';

export interface NodeExtra {
  reward: RewardKind | null;
  risk: RiskKind | null;
  shrine: boolean;
  /** 엘리트 접두어 (엘리트 길 = 웨이브 수만큼, 성소 = 1) */
  prefixes: ElitePrefixId[];
  /** 이벤트 노드·숨은 노드(행상·술잔) 내용 */
  eventId: string | null;
  grade: Grade | null;
  /** 상점 앞 단 전투 (전표 가중) */
  preShop: boolean;
  /** 숨은 노드 내용 (숨은 노드만) */
  hiddenContent: HiddenContent | null;
}

export interface HiddenNodeInfo {
  sourceId: string;
  nodeId: string;
  content: HiddenContent;
  clue: string;
  state: 'smudge' | 'located' | 'found';
}

export interface FloorExtras {
  stageId: string;
  nodes: Record<string, NodeExtra>;
  hidden: HiddenNodeInfo | null;
  intel: Record<MapInfoId, boolean>;
}

const emptyExtra = (): NodeExtra => ({
  reward: null,
  risk: null,
  shrine: false,
  prefixes: [],
  eventId: null,
  grade: null,
  preShop: false,
  hiddenContent: null,
});

/** 가중 무작위 (가중 0 은 빼고). 비면 null */
export function weightedPick<T extends string>(rng: Rng, weights: Partial<Record<T, number>>): T | null {
  const entries = Object.entries(weights).filter(([, w]) => typeof w === 'number' && (w as number) > 0) as [
    T,
    number,
  ][];
  const total = entries.reduce((a, [, w]) => a + w, 0);
  if (total <= 0) return null;
  let r = rng.next() * total;
  for (const [k, w] of entries) {
    r -= w;
    if (r < 0) return k;
  }
  return entries[entries.length - 1][0];
}

/** 이벤트 고르기: 런 안 중복 없음, 서사형 가중 ×narrativeMult. 다 썼으면 처음부터. 61라운드 P5: 이 층에서 나오는 것만 (1층 5종) */
export function pickEvent(
  rng: Rng,
  used: readonly string[],
  exclude: readonly string[] = [],
  floor: FloorScope = null,
): string | null {
  const E = BUNDLE2.events;
  const items = eventsOn(floor);
  let pool = items.filter((e) => !used.includes(e.id) && !exclude.includes(e.id));
  if (pool.length === 0) pool = items.filter((e) => !exclude.includes(e.id));
  const weights: Record<string, number> = {};
  for (const e of pool) weights[e.id] = e.narrative ? E.narrativeMult : 1;
  return weightedPick(rng, weights);
}

/** 61라운드 P5: 이 층에서 붙는 접두어만 (1층 3종) */
function rollPrefixes(rng: Rng, n: number, floor: FloorScope): ElitePrefixId[] {
  const ids = prefixIdsOn(floor);
  if (ids.length === 0) return [];
  return Array.from({ length: n }, () => ids[Math.floor(rng.next() * ids.length)]);
}

/** 잔 구간 첫 단(col) — 여정 수 */
export function laneStartCol(g: RouteGraph): number {
  return g.nodes.filter((n) => n.kind === 'birth' || n.kind === 'road' || n.kind === 'post').length;
}

/**
 * 층 노드 정보 생성. usedEvents = 이번 런에 이미 나온 이벤트 id (고른 것은 이 함수가 덧붙이지 않는다 — 진입 때 기록).
 * 숨은 노드가 생기면 그래프에 노드를 더한다 (단서 조사 전까지 어디에도 이어지지 않음)
 */
export function generateExtras(
  g: RouteGraph,
  seed: number | string,
  usedEvents: readonly string[],
  waveCount: number,
): FloorExtras {
  const B = BUNDLE2;
  const floor = floorOfStage(g.stageId);
  const rng = new Rng(hashSeed(`${String(seed)}:bundle2`));
  const nodes: Record<string, NodeExtra> = {};
  for (const n of g.nodes) nodes[n.id] = emptyExtra();
  const J = laneStartCol(g);
  const lane = g.nodes.filter((n) => n.col >= J && n.kind !== 'boss');
  const byId = new Map(g.nodes.map((n) => [n.id, n]));
  // (b) 위험 노드
  const riskCands = lane.filter((n) => n.kind === 'battle' && B.risk.laneCols.includes(n.col - J));
  for (let i = 0; i < B.risk.perFloor && riskCands.length > 0; i++) {
    const n = riskCands.splice(Math.floor(rng.next() * riskCands.length), 1)[0];
    const kind = weightedPick<RiskKind>(rng, B.risk.kinds) ?? 'elite';
    nodes[n.id].risk = kind;
    if (kind === 'elite') nodes[n.id].prefixes = rollPrefixes(rng, Math.max(1, waveCount) * B.risk.elitePerWave, floor);
  }
  // 상점 앞 단 (링크에 상점이 있는 전투)
  for (const n of lane)
    nodes[n.id].preShop = n.links.some((id) => byId.get(id)?.kind === 'shop') && n.kind === 'battle';
  // (a) 보상 — 단(col) 순서대로, 같은 단은 서로 다르게, 층 상한
  const used: Partial<Record<RewardKind, number>> = {};
  const cols = [...new Set(lane.map((n) => n.col))].sort((a, b) => a - b);
  for (const col of cols) {
    const taken = new Set<RewardKind>();
    for (const n of lane.filter((x) => x.col === col).sort((a, b) => a.row - b.row)) {
      const ex = nodes[n.id];
      if (n.kind !== 'battle') continue;
      if (ex.risk === 'curse') continue;
      const w: Partial<Record<RewardKind, number>> = {};
      for (const [k, v] of Object.entries(B.rewards.weights) as [RewardKind, number][]) {
        const cap = B.rewards.floorCaps[k];
        if (taken.has(k) || (cap !== undefined && (used[k] ?? 0) >= cap)) continue;
        w[k] = v * (k === 'gold' && ex.preShop ? B.rewards.preShopGoldMult : 1);
      }
      const r = weightedPick(rng, w) ?? 'gold';
      ex.reward = r;
      taken.add(r);
      used[r] = (used[r] ?? 0) + 1;
    }
  }
  for (const n of g.nodes) if (n.kind === 'road') nodes[n.id].reward = B.rewards.road;
  // (f) 도전 성소 — 잔 일반 전투 (위험 아님). 61라운드 P5: 1층에서 끔 ('완' 등급으로 통합)
  for (const n of lane)
    if (onFloor(B.shrine, floor) && n.kind === 'battle' && !nodes[n.id].risk && rng.chance(B.shrine.chance)) {
      nodes[n.id].shrine = true;
      nodes[n.id].prefixes = rollPrefixes(rng, B.shrine.eliteExtra, floor);
    }
  // (c) 이벤트 내용
  const picked: string[] = [];
  for (const n of lane.filter((x) => x.kind === 'event')) {
    const id = pickEvent(rng, [...usedEvents, ...picked], [], floor);
    nodes[n.id].eventId = id;
    if (id) picked.push(id);
  }
  // (d) 숨은 노드
  let hidden: HiddenNodeInfo | null = null;
  const lanes = Math.max(1, ...lane.map((n) => n.row + 1));
  const srcCands = lane.filter((n) => n.kind === 'battle' && !nodes[n.id].risk && n.links.length > 0);
  // 61라운드 P5: 숨은 노드는 1층에서 끔
  if (onFloor(B.hidden, floor) && srcCands.length > 0 && rng.chance(byStage(B.hidden.chance, g.stageId))) {
    const src = srcCands[Math.floor(rng.next() * srcCands.length)];
    const content = weightedPick<HiddenContent>(rng, B.hidden.contents) ?? 'treasure';
    const id = `h${src.col}r${lanes}`;
    const node: RouteNode = {
      id,
      kind: 'event',
      type: 'event',
      name: B.hidden.name,
      col: src.col,
      row: lanes,
      links: [...src.links],
    };
    g.nodes.push(node);
    nodes[id] = {
      ...emptyExtra(),
      eventId: content === 'peddler' ? 'peddler' : content === 'offering' ? 'offering' : null,
      hiddenContent: content,
    };
    hidden = {
      sourceId: src.id,
      nodeId: id,
      content,
      clue: B.hidden.clues[Math.floor(rng.next() * B.hidden.clues.length)] ?? B.hidden.clues[0],
      state: 'smudge',
    };
  }
  return { stageId: g.stageId, nodes, hidden, intel: { nextTier: false, fullFloor: false, hiddenLocated: false } };
}

/** 숨은 길 열기 (단서 조사) — 갈라지는 노드 링크에 숨은 노드를 더한다. 열었으면 true */
export function revealHidden(g: RouteGraph, ex: FloorExtras): boolean {
  const h = ex.hidden;
  if (!h || h.state === 'found') return false;
  const src = g.nodes.find((n) => n.id === h.sourceId);
  if (!src) return false;
  h.state = 'found';
  if (!src.links.includes(h.nodeId)) src.links.push(h.nodeId);
  return true;
}

/** 지도 정보 사기 (이미 샀으면 false) */
export function buyIntel(ex: FloorExtras, id: MapInfoId): boolean {
  if (ex.intel[id]) return false;
  ex.intel[id] = true;
  if (id === 'hiddenLocated' && ex.hidden && ex.hidden.state === 'smudge') ex.hidden.state = 'located';
  return true;
}

/** 노드 표시용 보상 종류 (계약 §14.5 UiNodeRewardKind) — 공개되지 않았으면 null */
export function uiReward(n: RouteNode, ex: NodeExtra | undefined, revealed: boolean): UiRouteNode['reward'] {
  if (!ex) return null;
  if (n.kind === 'event' || ex.eventId || ex.hiddenContent) return 'unknown';
  if (ex.risk === 'curse') return 'curse';
  if (!revealed || !ex.reward) return null;
  return ex.reward;
}

/** 위험 한 줄 (진입 확인 문구) */
export function riskText(kind: RiskKind | null): string {
  if (!kind) return '';
  const t = BUNDLE2.risk.text[kind];
  return typeof t === 'string' ? t : '';
}

/** 접두어 이름 목록 */
export function prefixNames(ids: readonly ElitePrefixId[]): string[] {
  return ids.map((id) => BUNDLE2.elite.prefixes.find((p) => p.id === id)?.name ?? id);
}

/**
 * 계약 §14.5 노드 지도 확장 — RouteState.toUi 결과에 2차 묶음 필드를 얹는다.
 * available(고를 차례) = 보상 공개, 지도 정보 다음 단 = '?' 이벤트 이름·접두어 공개, 층 전체 = 전부 공개
 */
export function decorateRoute(base: UiRoute, ex: FloorExtras, graph: RouteGraph): UiRoute {
  const byId = new Map(graph.nodes.map((n) => [n.id, n]));
  const h = ex.hidden;
  const nodes = base.nodes.map((u) => {
    const n = byId.get(u.id);
    const e = ex.nodes[u.id];
    if (!n || !e) return u;
    const near = u.state === 'available' || u.state === 'current' || u.state === 'cleared';
    const full = ex.intel.fullFloor;
    const deep = full || (ex.intel.nextTier && u.state === 'available');
    const isHidden = h?.nodeId === u.id;
    const out: UiRouteNode = {
      ...u,
      reward: uiReward(n, e, near || full),
      risk: e.risk,
      riskText: riskText(e.risk),
      prefixes: deep && e.prefixes.length > 0 ? prefixNames(e.prefixes) : null,
      eventName: deep && e.eventId ? (BUNDLE2.events.items.find((x) => x.id === e.eventId)?.name ?? null) : null,
      hidden: isHidden ? h!.state : null,
      grade: e.grade,
    };
    return out;
  });
  return { ...base, nodes, intel: { ...ex.intel } };
}
