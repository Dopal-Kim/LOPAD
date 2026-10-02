/**
 * 48라운드 Q3·Q4·Q9: 노드 지도 진행 (1~2층 한정). Phaser 의존 없음.
 *
 * 층 = 왼→오 단계(col). 1층은 여정 3(탄생지 → 버려진 길 → 국경 초소) + 두 갈래(lane) × 3단계 + 보스,
 * 2층은 여정 없이 두 갈래 × 3단계 + 보스. 갈래 노드 종류(전투 3·상점 1·휴식 1·이벤트 1)는 층 시드로 섞는다.
 * 같은 갈래의 다음 단계로 항상 이어지고, crossChance 로 옆 갈래 다음 단계에도 이어진다(교차).
 * 어느 경로로 가도 전투가 1번 이상 있도록 다시 섞는다. 같은 시드면 같은 지도.
 */
import routeJson from '../../data/route.json';
import type { UiNodeType, UiRoute, UiRouteNode, UiNodeState } from '../contract/ui';
import type { WaveEntry } from '../data/types';
import type { RoomType } from './mapgen/types';
import { Rng, hashSeed } from './rng';
import type { UiStructureKind } from '../contract/ui';

/** 노드 세부 종류 (data/route.json kinds) — 여정 3종은 UI 에 journey 로 보인다 */
export type RouteKind = 'birth' | 'road' | 'post' | 'battle' | 'shop' | 'rest' | 'event' | 'boss';
export const LANE_KINDS = ['battle', 'shop', 'rest', 'event'] as const;
export type LaneKind = (typeof LANE_KINDS)[number];

export interface RouteKindDef {
  type: UiNodeType;
  /** 방 상태 머신이 보는 방 종류 (trial = 웨이브 전투, rest = 입장 회복, boss = 보스, start = 비전투) */
  room: RoomType;
  /** 바닥 타일 (tiles roomFloors 키) */
  floor: RoomType;
  /** 이 노드에 놓을 수 있는 구조물 (층 테마 제한은 별도) */
  structures: UiStructureKind[];
  /** filler(짐·술통) 밖 구조물 종류 수 [min, max] */
  budget: [number, number];
  /** 이 노드 전용 웨이브 (없으면 층 trial.waves) */
  waves?: WaveEntry[][];
  /** 기존 상점 타일(2×2)을 놓는다 */
  shopTiles?: boolean;
}

export interface RouteFloorDef {
  journey: RouteKind[];
  lanes: number;
  laneLength: number;
  pool: Record<LaneKind, number>;
  crossChance: number;
  names: Partial<Record<RouteKind, string[]>>;
}

export interface RouteArenaDef {
  default: [number, number];
  boss: [number, number];
  voidMarginTiles: number;
  spawnInsetTiles: number;
  exitInsetTiles: number;
  clearTiles: number;
}

export interface RouteFile {
  floors: Record<string, RouteFloorDef>;
  arena: RouteArenaDef;
  kinds: Record<RouteKind, RouteKindDef>;
}

export interface RouteNode {
  id: string;
  kind: RouteKind;
  type: UiNodeType;
  name: string;
  col: number;
  row: number;
  links: string[];
}

export interface RouteGraph {
  stageId: string;
  nodes: RouteNode[];
}

function fail(msg: string): never {
  throw new Error(`[data] route: ${msg}`);
}

const KINDS: readonly RouteKind[] = ['birth', 'road', 'post', 'battle', 'shop', 'rest', 'event', 'boss'];
const ROOMS: readonly RoomType[] = ['start', 'trial', 'rest', 'boss'];

export function validateRoute(f: RouteFile): RouteFile {
  for (const k of KINDS) {
    const d = f.kinds?.[k];
    if (!d) fail(`kinds.${k} 없음`);
    if (!ROOMS.includes(d.room) || !ROOMS.includes(d.floor)) fail(`kinds.${k}.room/floor 는 start|trial|rest|boss`);
    if (!Array.isArray(d.structures)) fail(`kinds.${k}.structures 는 목록`);
    if (!Array.isArray(d.budget) || d.budget.length !== 2 || d.budget[0] > d.budget[1])
      fail(`kinds.${k}.budget 는 [min, max]`);
  }
  const A = f.arena;
  for (const key of ['default', 'boss'] as const)
    if (!Array.isArray(A?.[key]) || A[key].length !== 2 || A[key].some((n) => !(n >= 12)))
      fail(`arena.${key} 는 [w, h] (12 이상)`);
  for (const [id, fl] of Object.entries(f.floors ?? {})) {
    if (!Array.isArray(fl.journey)) fail(`floors.${id}.journey 는 목록`);
    for (const j of fl.journey) if (!KINDS.includes(j)) fail(`floors.${id}.journey 알 수 없음: ${j}`);
    if (!(fl.lanes >= 1) || !(fl.laneLength >= 1)) fail(`floors.${id}.lanes/laneLength 는 1 이상`);
    const total = LANE_KINDS.reduce((a, k) => a + (fl.pool?.[k] ?? 0), 0);
    if (total !== fl.lanes * fl.laneLength) fail(`floors.${id}.pool 합(${total}) ≠ lanes × laneLength`);
    if (!(fl.crossChance >= 0 && fl.crossChance <= 1)) fail(`floors.${id}.crossChance 는 0..1`);
  }
  return f;
}

export const ROUTE: RouteFile = validateRoute(routeJson as unknown as RouteFile);

/** 이 층(stage id)이 노드 지도로 진행하는가 */
export function routeEnabled(stageId: string, file: RouteFile = ROUTE): boolean {
  return Boolean(file.floors[stageId]);
}

export function nodeId(col: number, row: number): string {
  return `c${col}r${row}`;
}

/** 모든 경로(진입 노드 → 보스)에서 전투 수의 최솟값 */
export function minBattlesOnAnyPath(g: RouteGraph): number {
  const byId = new Map(g.nodes.map((n) => [n.id, n]));
  const memo = new Map<string, number>();
  const walk = (id: string): number => {
    const hit = memo.get(id);
    if (hit !== undefined) return hit;
    const n = byId.get(id)!;
    const here = n.kind === 'battle' || n.kind === 'road' ? 1 : 0;
    const rest = n.links.length === 0 ? 0 : Math.min(...n.links.map(walk));
    const v = here + rest;
    memo.set(id, v);
    return v;
  };
  return Math.min(...entryNodes(g).map((n) => walk(n.id)));
}

/** 층 시작에 고를 수 있는 노드 (0단계) */
export function entryNodes(g: RouteGraph): RouteNode[] {
  return g.nodes.filter((n) => n.col === 0);
}

/** 층 노드 그래프 생성 (시드 결정적) */
export function generateRoute(stageId: string, seed: number | string, file: RouteFile = ROUTE): RouteGraph {
  const F = file.floors[stageId];
  if (!F) throw new Error(`[route] 노드 지도가 없는 층: ${stageId}`);
  const rng = new Rng(hashSeed(`${String(seed)}:route`));
  const nameRng = new Rng(hashSeed(`${String(seed)}:route-names`));
  const nameUse = new Map<RouteKind, number>();
  const nameOrder = new Map<RouteKind, number[]>();
  const nameOf = (kind: RouteKind): string => {
    const list = F.names[kind] ?? [];
    if (list.length === 0) return kind;
    const used = nameUse.get(kind) ?? 0;
    nameUse.set(kind, used + 1);
    // 같은 종류가 여럿이면 목록을 시드로 한 번 섞어 차례로 (모자라면 번호)
    let order = nameOrder.get(kind);
    if (!order) {
      order = nameRng.shuffle(list.map((_, i) => i));
      nameOrder.set(kind, order);
    }
    return used < list.length ? list[order[used]] : `${list[0]} ${used + 1}`;
  };

  const J = F.journey.length;
  const L = F.laneLength;
  const R = F.lanes;
  const bossCol = J + L;
  const pool: LaneKind[] = [];
  for (const k of LANE_KINDS) for (let i = 0; i < F.pool[k]; i++) pool.push(k);

  let best: RouteGraph | null = null;
  for (let attempt = 0; attempt < 40; attempt++) {
    const kinds = rng.shuffle([...pool]);
    const cross: boolean[][] = [];
    for (let c = 0; c < L - 1; c++) cross.push(Array.from({ length: R }, () => rng.chance(F.crossChance)));
    const nodes: RouteNode[] = [];
    nameUse.clear();
    // 여정 (한 줄)
    F.journey.forEach((kind, i) => {
      nodes.push({
        id: nodeId(i, 0),
        kind,
        type: file.kinds[kind].type,
        name: '',
        col: i,
        row: 0,
        links: [],
      });
    });
    // 갈래
    for (let c = 0; c < L; c++)
      for (let r = 0; r < R; r++) {
        const kind = kinds[c * R + r];
        nodes.push({
          id: nodeId(J + c, r),
          kind,
          type: file.kinds[kind].type,
          name: '',
          col: J + c,
          row: r,
          links: [],
        });
      }
    nodes.push({ id: nodeId(bossCol, 0), kind: 'boss', type: 'boss', name: '', col: bossCol, row: 0, links: [] });
    const at = (col: number, row: number) => nodes.find((n) => n.col === col && n.row === row)!;
    // 연결
    for (let i = 0; i < J - 1; i++) at(i, 0).links.push(nodeId(i + 1, 0));
    if (J > 0) for (let r = 0; r < R; r++) at(J - 1, 0).links.push(nodeId(J, r));
    for (let c = 0; c < L; c++)
      for (let r = 0; r < R; r++) {
        const n = at(J + c, r);
        if (c === L - 1) n.links.push(nodeId(bossCol, 0));
        else {
          n.links.push(nodeId(J + c + 1, r));
          if (R > 1 && cross[c][r]) n.links.push(nodeId(J + c + 1, (r + 1) % R));
        }
      }
    // 이름 (단계 순서대로 — 결정적)
    for (const n of nodes) n.name = nameOf(n.kind);
    const g: RouteGraph = { stageId, nodes };
    best = g;
    if (minBattlesOnAnyPath(g) >= 1) return g;
  }
  return best!;
}

/** 진행 상태 (층 안에서 유지, 층 전환 시 새로 만든다) */
export class RouteState {
  currentId: string | null = null;
  /** 지나온 노드 (순서) */
  readonly path: string[] = [];
  readonly cleared = new Set<string>();
  choosing = false;

  constructor(
    readonly graph: RouteGraph,
    readonly floor: number,
  ) {}

  node(id: string | null): RouteNode | undefined {
    return id ? this.graph.nodes.find((n) => n.id === id) : undefined;
  }

  get current(): RouteNode | undefined {
    return this.node(this.currentId);
  }

  /** 지금 고를 수 있는 다음 노드 (현재가 없으면 진입 노드) */
  nextOptions(): RouteNode[] {
    const cur = this.current;
    if (!cur) return entryNodes(this.graph);
    return cur.links.map((id) => this.node(id)!).filter(Boolean);
  }

  canChoose(id: string): boolean {
    return this.nextOptions().some((n) => n.id === id);
  }

  /** 노드에 들어간다 (선택 끝) */
  enter(id: string): boolean {
    if (!this.canChoose(id)) return false;
    this.currentId = id;
    this.path.push(id);
    this.choosing = false;
    return true;
  }

  markCleared(): void {
    if (this.currentId) this.cleared.add(this.currentId);
  }

  get currentCleared(): boolean {
    return this.currentId !== null && this.cleared.has(this.currentId);
  }

  stateOf(n: RouteNode): UiNodeState {
    if (n.id === this.currentId) return 'current';
    if (this.path.includes(n.id)) return 'cleared';
    const cur = this.current;
    const curCol = cur ? cur.col : -1;
    if (this.choosing && this.canChoose(n.id)) return 'available';
    if (n.col <= curCol) return 'passed';
    return 'locked';
  }

  toUi(): UiRoute {
    const nodes: UiRouteNode[] = this.graph.nodes.map((n) => ({
      id: n.id,
      type: n.type,
      name: n.name,
      col: n.col,
      row: n.row,
      links: [...n.links],
      state: this.stateOf(n),
    }));
    return { floor: this.floor, nodes, currentId: this.currentId, choosing: this.choosing };
  }
}

/** 노드 세부 종류의 정의 */
export function kindDef(kind: RouteKind, file: RouteFile = ROUTE): RouteKindDef {
  return file.kinds[kind];
}

/** 전투장 크기 [w, h] (타일) */
export function arenaSize(kind: RouteKind, file: RouteFile = ROUTE): [number, number] {
  return kind === 'boss' ? file.arena.boss : file.arena.default;
}
