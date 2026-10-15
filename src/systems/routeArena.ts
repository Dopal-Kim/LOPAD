/**
 * 49라운드 4-2·6·7·3: 노드 전투장 한 판의 설계도 — 지역(타일셋) + 전투장 + 세트 배치 + 튜토리얼 자리.
 * Phaser 의존 없음 · 시드 결정적. Game 은 `planNodeArena` 결과로 TileWorld·구조물·소품 그림·튜토리얼을 만든다.
 * P19 S2: 전투·여정 전투·보스 노드(`arena.shapeKinds`)는 형태 틀(data/arenas) — 노드 → 형태 배정은 `shapeAssignments`.
 */
import { ARENA_ART, CAMERA, GAME, TILE } from '../core/Constants';
import { ARENA_SHAPES } from '../data/arenas';
import { Rng, hashSeed } from './rng';
import { generateArena } from './mapgen/arena';
import { buildShape, type ArenaShapeDef, type ShapeGrid } from './mapgen/shape';
import type { FloorLayout, Rect } from './mapgen/types';
import {
  ROUTE,
  arenaSize,
  entries,
  generateRoute,
  kindDef,
  regionIdOf,
  type RegionDef,
  type RouteFile,
  type RouteGraph,
  type RouteKind,
  type RouteNode,
} from './route';
import { STRUCTURE_DEFS, availableOn } from './structures/data';
import type { UiStructureKind } from '../contract/ui';
import type { PlanOptions } from './structures/placement';
import { planSetPiece, type SetPieceDef, type SetPiecePlan } from './structures/setpiece';
import { mirrorSetPiece, type Mirror } from './structures/setpieceMirror';
import type { TutorialDef } from './tutorial';

export interface NodeArenaPlan {
  layout: FloorLayout;
  kind: RouteKind;
  regionId: string | null;
  region: RegionDef | null;
  /** 지역 타일셋 이름 (`tiles/<tileset>.json`). 없으면 층 타일셋 */
  tileset: string | null;
  setPiece: SetPiecePlan;
  /** 무작위 구조물·소품을 놓지 않을 칸 (시작점·출구·상점 + 세트 배치) */
  reserve: Rect[];
  /** planStructures 의 node 옵션 그대로 */
  structureNode: NonNullable<PlanOptions['node']>;
  /** 조작 안내 노드면 그 정의 */
  tutorial: TutorialDef | null;
  /** 61라운드 단계 2 방 다양화: 고른 크기·시작 줄 이동·세트 뒤집기 (디버그). 형태 틀이면 변형된 크기·뒤집기 */
  variety: { size: [number, number]; shift: number; mirror: Mirror };
  /** P19 S2 형태 틀 (사각 전투장이면 null): id · 배율 · 주변광 덮어쓰기 · 고정 광원(타일, 소수) · 미리 깔린 술 웅덩이(타일) */
  shape: {
    id: string;
    scale: number;
    ambient: string | null;
    lights: { x: number; y: number; kind: string }[];
    pools: { x: number; y: number }[];
    /** 무대 중심 그림 (타일, 소수 — 발 자리) */
    centerArt: { sheet: string; x: number; y: number } | null;
  } | null;
}

/** 노드 자리 순번 (단 × 2 + 줄) — 같은 길의 이웃 단은 다른 후보를 고르게 */
const slotOf = (node: Pick<RouteNode, 'col' | 'row'>) => node.col * 2 + node.row;

/**
 * 61라운드 단계 2 방 다양화 (플레이 점검 #7): 크기 후보·시작/출구 줄 이동·세트 뒤집기를 노드 자리와 층 시드로 고른다.
 * 보스·튜토리얼 노드와 노드 없음(갈림 대기)은 그대로
 */
export function arenaVariety(
  node: Pick<RouteNode, 'id' | 'kind' | 'col' | 'row'> | null,
  floorSeed: number | string,
  file: RouteFile = ROUTE,
): { size: [number, number]; shift: number; mirror: Mirror } {
  const kind: RouteKind = node?.kind ?? 'birth';
  const base = arenaSize(kind, file);
  const V = file.arena.variety;
  const fixed = { size: base, shift: 0, mirror: { x: false, y: false } };
  if (!node || !V || kind === 'boss' || kindDef(kind, file).tutorial) return fixed;
  const h = hashSeed(`${String(floorSeed)}:${node.id}:variety`);
  const sizes = V.sizes?.[kind] ?? [];
  const size = sizes.length > 0 ? sizes[(h + slotOf(node)) % sizes.length] : base;
  const [lo, hi] = V.spawnShiftTiles ?? [0, 0];
  const shift = hi > lo ? lo + (Math.floor(h / 7) % (hi - lo + 1)) : lo;
  const mirror = V.mirror
    ? { x: ((node.col + node.row + h) & 1) === 1, y: ((Math.floor(node.col / 2) + node.row + (h >> 1)) & 1) === 1 }
    : fixed.mirror;
  return { size: [size[0], size[1]], shift, mirror };
}

/**
 * 61라운드 계약 art §24 방 변주 장면 (소품 시트 `variantTag`): 장면 이름 + '없음' 을 노드 자리 순번으로 돌려 고른다
 * (같은 길 이웃 단이 다른 장면). 보스·튜토리얼은 없음 (보스방 패턴과 겹치는 엄폐를 두지 않는다)
 */
export function pickPropScene(
  tags: readonly string[],
  node: Pick<RouteNode, 'id' | 'kind' | 'col' | 'row'> | null,
  floorSeed: number | string,
  file: RouteFile = ROUTE,
): string | null {
  if (!node || tags.length === 0 || node.kind === 'boss' || kindDef(node.kind, file).tutorial) return null;
  const options = [...tags, null];
  return options[(hashSeed(`${String(floorSeed)}:propscene`) + slotOf(node)) % options.length];
}

/** 노드의 세트 배치 템플릿 id — 지역 덮어쓰기 → 종류 기본 `setPiece` */
export function pickSetPiece(
  node: Pick<RouteNode, 'kind'>,
  region: RegionDef | null,
  file: RouteFile = ROUTE,
): string | null {
  return region?.setPieces?.[node.kind] ?? kindDef(node.kind, file).setPiece ?? null;
}

/** 이 층 그래프(시드 결정적)의 형태 틀 노드 → 형태 id 캐시 */
const shapeCache = new Map<string, Map<string, string>>();

/**
 * P19 S2 노드 → 형태 배정 (같은 층 시드면 같은 결과). 단 순서로 돌며, 형태 regions 에 노드 지역이 든 후보 중
 * (이 층에서 쓴 횟수 → 같은 단에서 쓴 횟수 → 시드 해시) 가 가장 작은 것. 지역에 맞는 후보가 없으면 같은 stage 전부
 * (보스는 사각 그대로). 1층 한 판(전투 5~6노드)에서 형태 5종 이상 · 같은 단 두 갈래는 서로 다르게
 */
export function shapeAssignments(
  stageId: string,
  floorSeed: number | string,
  file: RouteFile = ROUTE,
  shapes: ReadonlyMap<string, ArenaShapeDef> = ARENA_SHAPES,
): Map<string, string> {
  const key = `${stageId}|${String(floorSeed)}`;
  const hit = file === ROUTE && shapes === ARENA_SHAPES ? shapeCache.get(key) : undefined;
  if (hit) return hit;
  const kinds = new Set(file.arena.shapeKinds ?? []);
  const out = new Map<string, string>();
  const used = new Map<string, number>();
  const usedInCol = new Map<string, number>();
  const nodes = generateRoute(stageId, floorSeed, file)
    .nodes.filter((n) => kinds.has(n.kind))
    .sort((a, b) => a.col - b.col || a.row - b.row);
  for (const n of nodes) {
    const stage = n.kind === 'boss' ? 'boss' : 'battle';
    const all = [...shapes.values()].filter((d) => d.stage === stage);
    const region = regionIdOf(stageId, n.col, file);
    const fit = all.filter((d) => region !== null && d.regions.includes(region));
    const cands = fit.length > 0 ? fit : stage === 'boss' ? [] : all;
    if (cands.length === 0) continue;
    const score = (d: ArenaShapeDef) =>
      [used.get(d.id) ?? 0, usedInCol.get(`${n.col}:${d.id}`) ?? 0, hashSeed(`${key}:${n.id}:${d.id}`)] as const;
    const best = cands.reduce((a, b) => {
      const [x, y] = [score(a), score(b)];
      return y[0] < x[0] || (y[0] === x[0] && (y[1] < x[1] || (y[1] === x[1] && y[2] < x[2]))) ? b : a;
    });
    out.set(n.id, best.id);
    used.set(best.id, (used.get(best.id) ?? 0) + 1);
    usedInCol.set(`${n.col}:${best.id}`, (usedInCol.get(`${n.col}:${best.id}`) ?? 0) + 1);
  }
  if (file === ROUTE && shapes === ARENA_SHAPES) shapeCache.set(key, out);
  return out;
}

/**
 * P19 2단계: 노드 그래프 + 전투 노드 이름 = 그 노드 형태 틀의 이름 (`shapeNames` — 같은 형태 두 번째는 [1]).
 * 고정 이름 노드(여정·보스·상점 등)는 그대로. 런의 노드 지도는 이것으로 만든다
 */
export function namedRoute(stageId: string, floorSeed: number | string, file: RouteFile = ROUTE): RouteGraph {
  const graph = generateRoute(stageId, floorSeed, file);
  const names = file.floors[stageId]?.shapeNames;
  if (!names) return graph;
  const shapes = shapeAssignments(stageId, floorSeed, file);
  const used = new Map<string, number>();
  for (const n of [...graph.nodes].sort((a, b) => a.col - b.col || a.row - b.row)) {
    const id = n.kind === 'battle' ? shapes.get(n.id) : undefined;
    const list = id ? names[id] : undefined;
    if (!id || !list?.length) continue;
    const i = used.get(id) ?? 0;
    used.set(id, i + 1);
    n.name = list[Math.min(i, list.length - 1)];
  }
  return graph;
}

/** 화면 하나에 보이는 칸 (탐색 배율 기준 — CAMERA.ZOOM 1.75 → 34.3 × 19.3) */
export const SCREEN_TILES = { w: GAME.WIDTH / CAMERA.ZOOM / TILE, h: GAME.HEIGHT / CAMERA.ZOOM / TILE } as const;
/** 형태 틀 전투장 넓이 ÷ 화면 목표 (P19 ⑤-1) */
export const SHAPE_AREA_SCREENS: readonly [number, number] = [1.8, 3.0];

/**
 * 형태 변형 고르기: 배율은 variants.scale 안에서, 넓이 ÷ 화면이 SHAPE_AREA_SCREENS 안에 들도록 좁힌 범위에서 시드로.
 * 뒤집기는 허용된 축마다 시드 비트
 */
export function shapeVariant(def: ArenaShapeDef, seed: string): { scale: number; flipX: boolean; flipY: boolean } {
  const rng = new Rng(hashSeed(`${seed}:shape`));
  const area = def.mask.length * def.mask[0].length;
  const screen = SCREEN_TILES.w * SCREEN_TILES.h;
  const lo = Math.max(def.variants.scale[0], Math.sqrt((SHAPE_AREA_SCREENS[0] * screen) / area) + 0.01);
  const hi = Math.min(def.variants.scale[1], Math.sqrt((SHAPE_AREA_SCREENS[1] * screen) / area) - 0.01);
  const scale = hi > lo ? lo + (hi - lo) * rng.next() : Math.min(Math.max(1, lo), Math.max(lo, hi));
  return { scale, flipX: def.variants.flipX && rng.chance(0.5), flipY: def.variants.flipY && rng.chance(0.5) };
}

/**
 * 위험물 자리 → 구조물 종류 (pool 은 구조물이 아니라 미리 깔린 웅덩이 · parapet = 부서지는 흉벽 — 동작은 짐 상자, 그림은 art §34 hazard_merlon)
 */
const HAZARD_STRUCTURE: Readonly<Record<string, UiStructureKind | null>> = {
  cask: 'cask',
  still: 'still',
  parapet: 'crate',
  pool: null,
};
const HAZARD_SPRITE: Readonly<Record<string, string>> = { parapet: ARENA_ART.MERLON };

/**
 * 노드 전투장 설계. node 가 null 이면(2층 진입 갈림 선택 대기) 비전투 빈 전투장 (세트 배치 없음, 지역 = 0단계).
 * 같은 (node, stageId, floorSeed) 면 같은 결과.
 */
export function planNodeArena(
  node: RouteNode | null,
  stageId: string,
  floorSeed: number | string,
  file: RouteFile = ROUTE,
  /**
   * 53라운드 Q6: 지역에 Gemini 외벽 테두리가 있는지 — 있으면 숨은 저장고 없음
   * (저장고는 벽 바깥 여백을 파는데 그 자리를 테두리 그림이 덮는다)
   */
  /** shape = 형태 틀 강제 (디버그 `?shape=<id>` — 형태 틀 노드 종류일 때만) */
  opts: { border?: (regionId: string | null) => boolean; shape?: string | null } = {},
): NodeArenaPlan {
  const kind: RouteKind = node?.kind ?? 'birth';
  const d = kindDef(kind, file);
  const A = file.arena;
  const regionId = regionIdOf(stageId, node?.col ?? 0, file);
  const region = regionId ? (entries(file.regions)[regionId] ?? null) : null;
  const nodeSeed = `${String(floorSeed)}:${node?.id ?? 'entry'}`;
  const seed = hashSeed(`${nodeSeed}:arena`);
  const border = Boolean(opts.border?.(regionId));
  const shapeId =
    node && file.arena.shapeKinds?.includes(node.kind)
      ? (opts.shape ?? shapeAssignments(stageId, floorSeed, file).get(node.id))
      : undefined;
  const shapeDef = shapeId ? (ARENA_SHAPES.get(shapeId) ?? null) : null;
  const grid: ShapeGrid | null = shapeDef ? buildShape(shapeDef, shapeVariant(shapeDef, nodeSeed)) : null;
  const variety = grid
    ? { size: [grid.w, grid.h] as [number, number], shift: 0, mirror: { x: grid.flipX, y: grid.flipY } }
    : arenaVariety(node, floorSeed, file);
  const [w, h] = variety.size;
  const layout = generateArena({
    roomId: node?.id ?? 'entry',
    type: node ? d.room : 'start',
    floor: node ? d.floor : 'start',
    w,
    h,
    margin: A.voidMarginTiles,
    spawnInset: A.spawnInsetTiles,
    exitInset: A.exitInsetTiles,
    spawnExactCenter: kind === 'birth' && node !== null,
    shopCenter: Boolean(node && d.shopTiles),
    spawnShiftY: variety.shift,
    shape: grid ?? undefined,
    seed,
  });
  const arena = layout.arena!;
  const c = A.clearTiles;
  const reserve: Rect[] = [
    { x: arena.spawn.x - c, y: arena.spawn.y - c, w: c * 2 + 1, h: c * 2 + 1 },
    { x: arena.exit.x - c, y: arena.exit.y - c, w: c * 2 + 2, h: c * 2 + 2 },
  ];
  if (node && d.shopTiles) reserve.push({ x: arena.shop.x - c, y: arena.shop.y - c, w: c * 2 + 2, h: c * 2 + 2 });
  // P19 S2: 다리 칸은 무작위 구조물·소품·세트피스가 막지 않게
  for (const b of arena.bridges ?? []) reserve.push({ x: b.x, y: b.y, w: 1, h: 1 });

  // 54라운드 Q11: 지역이 노드 종류별 템플릿을 덮어쓸 수 있다 (연회장 보스방 = boss_hall). P19 S2: 형태 틀 소품 세트가 먼저
  const props = shapeDef?.props ?? [];
  const templateId =
    props.length > 0
      ? props[hashSeed(`${nodeSeed}:props`) % props.length]
      : node
        ? pickSetPiece(node, region, file)
        : null;
  const raw: SetPieceDef | null = templateId ? (entries(file.setPieces)[templateId] ?? null) : null;
  const template = raw ? mirrorSetPiece(raw, variety.mirror) : null;
  const tutorial = node && d.tutorial && file.tutorial ? file.tutorial : null;
  const kinds = border ? d.structures.filter((k) => STRUCTURE_DEFS.get(k)?.place !== 'cellar') : d.structures;
  const allowed = new Set(kinds);
  const setPiece = planSetPiece(layout, {
    templateId,
    template,
    region: regionId,
    seed: `${String(floorSeed)}:${node?.id ?? 'entry'}`,
    allowed: (k) => allowed.has(k) && availableOn(STRUCTURE_DEFS.get(k) ?? { floors: [] }, stageId),
    reserve,
    tutorial: tutorial
      ? {
          signs: tutorial.steps.map((s) => s.sign),
          dummies: tutorial.dummies,
          signSprite: tutorial.signSprite,
          signNames: tutorial.steps.map((s) => s.signName ?? s.id),
          dummySprite: tutorial.dummySprite,
        }
      : null,
  });
  // P19 S2: 형태 틀 엄폐 칸(돌기둥 그림) · 위험물 자리 (구조물은 세트 자리처럼 먼저, 웅덩이는 따로)
  const pools: { x: number; y: number }[] = [];
  if (grid) {
    setPiece.cover.unshift(...(arena.cover ?? []));
    const I = layout.rooms[0].interior;
    for (const hz of grid.hazards) {
      const at = { x: I.x + hz.x, y: I.y + hz.y };
      const sk = HAZARD_STRUCTURE[hz.kind];
      if (sk === null) pools.push(at);
      else if (sk && availableOn(STRUCTURE_DEFS.get(sk) ?? { floors: [] }, stageId))
        setPiece.fixed.push({ kind: sk, tx: at.x, ty: at.y, function: false, sprite: HAZARD_SPRITE[hz.kind] });
    }
  }
  const all = [...reserve, ...setPiece.reserve];
  return {
    layout,
    kind,
    regionId,
    region,
    tileset: region?.tileset ?? null,
    setPiece,
    reserve: all,
    structureNode: {
      kinds: node ? kinds : [],
      budget: node ? d.budget : [0, 0],
      reserve: all,
      fixed: setPiece.fixed,
      fillerNear: setPiece.fillerNear,
    },
    tutorial,
    variety,
    shape: grid
      ? {
          id: grid.id,
          scale: grid.scale,
          ambient: (regionId && shapeDef!.lighting.ambientByRegion?.[regionId]) || shapeDef!.lighting.ambient,
          lights: grid.lights.map((l) => ({
            x: layout.rooms[0].interior.x + l.x,
            y: layout.rooms[0].interior.y + l.y,
            kind: l.kind,
          })),
          pools,
          centerArt: grid.centerArt
            ? {
                ...grid.centerArt,
                x: layout.rooms[0].interior.x + grid.centerArt.x,
                y: layout.rooms[0].interior.y + grid.centerArt.y,
              }
            : null,
        }
      : null,
  };
}

/** 소품·세트 그림이 차지한 칸 (`"x,y"`) — TileWorld 타일셋 소품(planProps)에서 뺀다 */
export function setPieceTiles(plan: Pick<NodeArenaPlan, 'setPiece' | 'reserve'>): Set<string> {
  const s = new Set<string>();
  for (const d of plan.setPiece.decor)
    for (let y = d.ty; y < d.ty + d.h; y++) for (let x = d.tx; x < d.tx + d.w; x++) s.add(`${x},${y}`);
  for (const r of plan.setPiece.reserve)
    for (let y = r.y; y < r.y + r.h; y++) for (let x = r.x; x < r.x + r.w; x++) s.add(`${x},${y}`);
  return s;
}
