/**
 * Game 씬 월드 준비 (53라운드 정리 6-1 — Game.ts 에서 분리, 동작 그대로):
 * 노드 지도 진입 · 전투장 설계 · 타일 월드 · 외벽 테두리 · 지역 조명 연결.
 * create() 마다 새로 만들어진다 (상태 없음 — 결과는 Game 의 공유 필드에 둔다).
 */
import { TILE } from '../../core/Constants';
import { gameState } from '../../core/GameState';
import { BOSSES, LIGHTING } from '../../data';
import type { LightingAmbient } from '../../data/types';
import { generateFloor, type FloorLayout } from '../../systems/mapgen';
import { RouteState, generateRoute, kindDef, regionIdOf, routeEnabled } from '../../systems/route';
import { Lighting } from '../../systems/lighting/Lighting';
import { lightingAmbientFor } from '../../systems/lighting/lightMath';
import { Rng, hashSeed } from '../../systems/rng';
import { planNodeArena, setPieceTiles } from '../../systems/routeArena';
import { spriteLibrary } from '../../systems/sprites';
import { planStructures, structureTiles, type StructurePlacement } from '../../systems/structures/placement';
import { BorderView, releaseBorderTextures } from '../../world/BorderView';
import { borderFor, borderGaps, floorRectOf, type BorderDef } from '../../world/border';
import { SetPieceView } from '../../world/SetPieceView';
import { pillarSheet } from '../../systems/boss/BossArena';
import { TileSkin, propSkinFor, skinFor, tileSkins } from '../../world/tileskin';
import { TileWorld } from '../../world/TileWorld';
import type { Game } from '../Game';
import { urlParams } from './shared';

export class WorldSetup {
  constructor(private readonly g: Game) {}

  /**
   * 48라운드 노드 지도 (1~2층): 층 그래프는 층 시드로 한 번 만들고 노드마다 씬을 다시 연다. 반환 = 노드 시드 접미.
   * `slice` = 50라운드 시범 확인(`?slice=<지역>`): 새 런에서 그 지역의 전투 노드로 바로 (탄생 생략)
   */
  enterRoute(floor: number, slice: string | undefined): string {
    const g = this.g;
    g.routeMode = !g.lab && routeEnabled(gameState.stageId);
    if (g.routeMode && !gameState.route)
      gameState.route = new RouteState(generateRoute(gameState.stageId, gameState.floorSeed), floor);
    const route = g.routeMode ? gameState.route : null;
    if (route && !route.currentId && slice) this.jumpToSlice(route, slice);
    // 54라운드 디버그: ?boss · ?bossPhase · ?bossPattern = 이 층 보스 노드로 바로 (새 런만)
    if (route && !route.currentId && this.g.initData.bossJump) this.jumpToBoss(route);
    // 진입 노드가 하나뿐이면(1층 탄생지) 바로 들어간다. 여럿이면(2층 갈림) 빈 전투장에서 고른다
    if (route && !route.currentId) {
      const entries = route.nextOptions();
      if (entries.length === 1) route.enter(entries[0].id);
    }
    g.node = route?.current ?? null;
    g.nodeKind = g.node?.kind ?? null;
    const nodeSalt = g.node ? `:${g.node.id}` : route ? ':entry' : '';
    g.rng = new Rng(hashSeed(gameState.floorSeed + ':runtime' + nodeSalt));
    // 52라운드 Q9: 쿼터뷰 지역 타일셋이면 가장자리 깊이 0~1칸 (북쪽 집 앞면이 거의 한 줄)
    const quarterTileset = (t: string | null) => Boolean(skinFor(floor, t).quarter);
    g.nodeArena =
      !g.lab && route
        ? planNodeArena(g.node, gameState.stageId, gameState.floorSeed, undefined, {
            quarterTileset,
            border: (r) => Boolean(borderDefFor(r)),
          })
        : null;
    return nodeSalt;
  }

  /** 54라운드 `?boss`: 보스 노드를 현재 노드로 (탄생 생략) */
  private jumpToBoss(route: RouteState): void {
    const node = route.graph.nodes.find((n) => n.kind === 'boss');
    if (!node) return;
    route.currentId = node.id;
    route.path.push(node.id);
    gameState.birthPending = false;
  }

  /** `?slice=<지역>`: 그 지역의 전투 노드(없으면 그 지역 아무 노드)를 현재 노드로 */
  private jumpToSlice(route: RouteState, region: string): void {
    const inRegion = route.graph.nodes.filter((n) => regionIdOf(gameState.stageId, n.col) === region);
    const node = inRegion.find((n) => n.kind === 'battle') ?? inRegion[0];
    if (!node) return;
    route.currentId = node.id;
    route.path.push(node.id);
    gameState.birthPending = false;
  }

  /** 월드 (노드 지도면 노드 전투장 하나, 시험장이면 작은 아레나, 아니면 방+복도) · 구조물 배치 · 세트 그림 */
  buildWorld(floor: number, nodeSalt: string): StructurePlacement[] {
    const g = this.g;
    const arena = g.nodeArena;
    const layout = g.labMode
      ? g.labMode.buildArena()
      : arena
        ? arena.layout
        : generateFloor(gameState.floorSeed, gameState.stage.layout);
    g.layout = layout;
    g.visitedRooms = new Set(['start']);
    g.clearedRooms = new Set();
    // 47라운드: 구조물을 소품보다 먼저 배치하고 그 칸은 소품에서 뺀다. ?structures=all 이면 이 층 종류 전부(데모·검증)
    // 데모 배포본은 빌드 시 VITE_DEMO_STRUCTURES=all 로 같은 효과(주소 옵션을 붙일 수 없어서, 47라운드 데모 결정)
    // 48라운드: 노드 전투장이면 그 노드 종류에 허용된 구조물만 (forceAll = 허용 종류 전부)
    const forceAll = urlParams().get('structures') === 'all' || import.meta.env.VITE_DEMO_STRUCTURES === 'all';
    const structurePlan = g.lab
      ? []
      : planStructures(layout, gameState.stageId, gameState.floorSeed + nodeSalt, {
          forceAll,
          node: arena ? arena.structureNode : undefined,
        });
    const borderDef = arena ? borderDefFor(arena.regionId) : null;
    g.world = new TileWorld(
      g,
      layout,
      arena ? skinFor(floor, arena.tileset) : (tileSkins.get(floor) ?? TileSkin.placeholder()),
      gameState.floorSeed + nodeSalt,
      arena ? new Set([...structureTiles(structurePlan), ...setPieceTiles(arena)]) : structureTiles(structurePlan),
      // 53라운드 v3 바닥 소품 (`tiles/v3/<지역 타일셋>_props`) — 있으면 큰 소품·작은 소품을 그 시트에서
      // 54라운드 Q11: 보스방 기둥(고정 단단한 큰 소품) · 무작위로 놓지 않을 큰 소품
      {
        boundaryWalls: !borderDef,
        propSkin: arena ? propSkinFor(arena.tileset) : null,
        fixedBigProps: (arena?.setPiece.pillars ?? []).map((r) => ({
          name: pillarPropName(),
          tx: r.x,
          ty: r.y,
          w: r.w,
          h: r.h,
        })),
        excludeBigProps: arena?.setPiece.excludeBigProps ?? [],
      },
    );
    g.border = this.createBorder(borderDef, layout);
    g.physics.world.setBounds(0, 0, g.world.widthPx, g.world.heightPx);
    // 층 강조색: 캐릭터 시트의 1층 램프를 현재 층 램프로 치환한 변형 텍스처·애니 (1층은 원본)
    spriteLibrary.activate(g, floor);
    // 49라운드 세트 배치 그림 (층 램프 변형 시트를 쓰므로 activate 뒤)
    g.setPieceView?.destroy();
    g.setPieceView = arena ? new SetPieceView(g, arena.setPiece) : null;
    // 저장고가 있으면 카메라 경계에 넣는다 (부수면 그 안으로 들어간다)
    for (const p of structurePlan) if (p.cellar) g.world.extendCamera(p.cellar.inner, 1);
    const kd = g.nodeKind ? kindDef(g.nodeKind) : null;
    if (kd?.shopTiles && layout.arena) g.world.placeShopAt(layout.arena.shop.x, layout.arena.shop.y);
    return structurePlan;
  }

  /** 53라운드 Q6: 외벽 테두리 그림 (그림은 지연 로드, 실패하면 경계 벽 타일로) + 카메라 한계 = 테두리 범위 */
  private createBorder(def: BorderDef | null, layout: FloorLayout): BorderView | null {
    const g = this.g;
    releaseBorderTextures(g, def?.region ?? null);
    const floorRect = def ? floorRectOf(layout, TILE) : null;
    if (!def || !floorRect) return null;
    const view = new BorderView(
      g,
      def,
      floorRect,
      borderGaps(layout, TILE),
      () => g.world.quarter?.setBoundaryWalls(true),
      hashSeed(`${gameState.floorSeed}:${g.node?.id ?? 'entry'}:border`),
    );
    const c = view.plan.camera;
    g.world.setArenaCamera(c.x0, c.y0, c.x1 - c.x0, c.y1 - c.y0);
    return view;
  }

  /**
   * 50라운드 동적 조명 + 어둠 (지역 조명이 없으면 꺼진 채) · 53라운드: 상흔 빛은 조명 위 · 테두리 명도는 주변광 보정 틴트로 유지.
   * 카메라 배율·스크롤이 정해진 뒤 부른다
   */
  createLighting(): Lighting {
    const g = this.g;
    const lighting = new Lighting(g, {
      ambient: this.lightingAmbient(),
      player: g.player,
      telegraphs: () => g.telegraph.lightPoints(),
    });
    // 53라운드 Q4: 상흔 빛은 조명 영향을 받지 않는다 (조명이 켜진 지역이면 라이트맵 위)
    g.player.scar.aboveLight = lighting.enabled;
    // 53라운드 Q22~25: 바닥을 밝혀도 테두리 명도는 그대로 (주변광 보정 틴트)
    g.border?.matchAmbient(lighting.enabled ? lighting.ambientHex : null);
    return lighting;
  }

  /**
   * 50라운드 지역 조명: data/lighting.json regions 에 있는 지역 + 53라운드 Q38 외벽 테두리 5지역.
   * `?light=0` 끔 · `?light=1` 이면 그 밖의 전투장·시험장에도 default (검증용)
   */
  private lightingAmbient(): LightingAmbient | null {
    const g = this.g;
    const flag = urlParams().get('light');
    const hasBorder = (r: string | null | undefined) => Boolean(borderDefFor(r));
    return lightingAmbientFor(g.nodeArena?.regionId, flag, Boolean(g.nodeArena || g.lab), hasBorder, LIGHTING);
  }
}

/**
 * 54라운드 보스방 기둥 큰 소품 이름: 기둥 구조물 시트가 있으면 그 이름(지역 소품 시트에 없으니 QuarterView 는 칸만 막고 BossArena 가 그림),
 * 없으면 지역 소품 시트의 pillar
 */
function pillarPropName(): string {
  const A = BOSSES[gameState.stage.boss]?.arena;
  if (!A) return 'pillar';
  return pillarSheet(A) ?? A.pillarProp;
}

/** 53라운드 Q6: 지역 외벽 테두리 정의 (`?border=0` 이면 끔 — 비교용) */
export function borderDefFor(region: string | null | undefined): BorderDef | null {
  return urlParams().get('border') === '0' ? null : borderFor(region);
}
