/**
 * 49라운드 4-2·6·7·3: 노드 전투장 한 판의 설계도 — 지역(타일셋·가장자리) + 들쭉날쭉한 전투장 + 세트 배치 + 튜토리얼 자리.
 * Phaser 의존 없음 · 시드 결정적. Game 은 `planNodeArena` 결과로 TileWorld·구조물·소품 그림·튜토리얼을 만든다.
 */
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
import { planSetPiece, type SetPiecePlan } from './structures/setpiece';
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
): NodeArenaPlan {
  const kind: RouteKind = node?.kind ?? 'birth';
  const d = kindDef(kind, file);
  const [w, h] = arenaSize(kind, file);
  const A = file.arena;
  const regionId = regionIdOf(stageId, node?.col ?? 0, file);
  const region = regionId ? (entries(file.regions)[regionId] ?? null) : null;
  const seed = hashSeed(`${String(floorSeed)}:${node?.id ?? 'entry'}:arena`);
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
    edge: regionEdge(regionId, file) ?? undefined,
    seed,
  });
  const arena = layout.arena!;
  const c = A.clearTiles;
  const reserve: Rect[] = [
    { x: arena.spawn.x - c, y: arena.spawn.y - c, w: c * 2 + 1, h: c * 2 + 1 },
    { x: arena.exit.x - c, y: arena.exit.y - c, w: c * 2 + 2, h: c * 2 + 2 },
  ];
  if (node && d.shopTiles) reserve.push({ x: arena.shop.x - c, y: arena.shop.y - c, w: c * 2 + 2, h: c * 2 + 2 });

  const templateId = node && d.setPiece ? d.setPiece : null;
  const template = templateId ? (entries(file.setPieces)[templateId] ?? null) : null;
  const tutorial = node && d.tutorial && file.tutorial ? file.tutorial : null;
  const allowed = new Set(d.structures);
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
      kinds: node ? d.structures : [],
      budget: node ? d.budget : [0, 0],
      reserve: all,
      fixed: setPiece.fixed,
      fillerNear: setPiece.fillerNear,
    },
    tutorial,
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
