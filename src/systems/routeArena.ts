/**
 * 49라운드 4-2·6·7·3: 노드 전투장 한 판의 설계도 — 지역(타일셋·가장자리) + 들쭉날쭉한 전투장 + 세트 배치 + 튜토리얼 자리.
 * Phaser 의존 없음 · 시드 결정적. Game 은 `planNodeArena` 결과로 TileWorld·구조물·소품 그림·튜토리얼을 만든다.
 */
import { QUARTER } from '../core/Constants';
import { hashSeed } from './rng';
import { generateArena } from './mapgen/arena';
import type { FloorLayout, Rect } from './mapgen/types';
import {
  ROUTE,
  arenaSize,
  entries,
  kindDef,
  regionEdge,
  regionIdOf,
  type RegionDef,
  type RouteFile,
  type RouteKind,
  type RouteNode,
} from './route';
import { STRUCTURE_DEFS, availableOn } from './structures/data';
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
  /** 61라운드 단계 2 방 다양화: 고른 크기·시작 줄 이동·세트 뒤집기 (디버그) */
  variety: { size: [number, number]; shift: number; mirror: Mirror };
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

/**
 * 61라운드 단계 2: 노드의 세트 배치 템플릿 id — 지역 덮어쓰기 → 종류 후보(`setPieceVariants`, 층 시드 기준 자리 순번으로 돌려
 * 같은 길의 이웃 단과 겹치지 않게) → 종류 기본 `setPiece`
 */
export function pickSetPiece(
  node: Pick<RouteNode, 'kind' | 'col' | 'row'>,
  region: RegionDef | null,
  floorSeed: number | string,
  file: RouteFile = ROUTE,
): string | null {
  const d = kindDef(node.kind, file);
  const over = region?.setPieces?.[node.kind];
  if (over) return over;
  const list = d.setPieceVariants ?? [];
  if (list.length > 0) return list[(hashSeed(`${String(floorSeed)}:setpiece`) + slotOf(node)) % list.length];
  return d.setPiece ?? null;
}

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
   * 52라운드 Q9: 지역 타일셋이 쿼터뷰인지 (그러면 가장자리 깊이를 QUARTER.EDGE_MAX_INSET 칸까지만).
   * 53라운드 Q6: 지역에 Gemini 외벽 테두리가 있는지 — 있으면 가장자리 일직선(깊이 0, 테두리 기준선과 맞춤)·숨은 저장고 없음
   * (저장고는 벽 바깥 여백을 파는데 그 자리를 테두리 그림이 덮는다)
   */
  opts: { quarterTileset?: (tileset: string | null) => boolean; border?: (regionId: string | null) => boolean } = {},
): NodeArenaPlan {
  const kind: RouteKind = node?.kind ?? 'birth';
  const d = kindDef(kind, file);
  const variety = arenaVariety(node, floorSeed, file);
  const [w, h] = variety.size;
  const A = file.arena;
  const regionId = regionIdOf(stageId, node?.col ?? 0, file);
  const region = regionId ? (entries(file.regions)[regionId] ?? null) : null;
  const seed = hashSeed(`${String(floorSeed)}:${node?.id ?? 'entry'}:arena`);
  const baseEdge = regionEdge(regionId, file);
  const border = Boolean(opts.border?.(regionId));
  const maxInset = border ? 0 : opts.quarterTileset?.(region?.tileset ?? null) ? QUARTER.EDGE_MAX_INSET : Infinity;
  const edge = baseEdge ? { ...baseEdge, maxInset: Math.min(baseEdge.maxInset, maxInset) } : baseEdge;
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
    edge: edge ?? undefined,
    seed,
  });
  const arena = layout.arena!;
  const c = A.clearTiles;
  const reserve: Rect[] = [
    { x: arena.spawn.x - c, y: arena.spawn.y - c, w: c * 2 + 1, h: c * 2 + 1 },
    { x: arena.exit.x - c, y: arena.exit.y - c, w: c * 2 + 2, h: c * 2 + 2 },
  ];
  if (node && d.shopTiles) reserve.push({ x: arena.shop.x - c, y: arena.shop.y - c, w: c * 2 + 2, h: c * 2 + 2 });

  // 54라운드 Q11: 지역이 노드 종류별 템플릿을 덮어쓸 수 있다 (연회장 보스방 = boss_hall)
  const templateId = node ? pickSetPiece(node, region, floorSeed, file) : null;
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
