import { describe, expect, it } from 'vitest';
import { ROUTE, RouteState, generateRoute, regionIdOf, regionOf, regionTilesets, type RouteNode } from './route';
import { planNodeArena, setPieceTiles } from './routeArena';
import { floorConnected } from './mapgen/arena';
import { TileId } from './mapgen/types';
import { planStructures } from './structures/placement';
import { STRUCTURE_DEFS } from './structures/data';
import { routeSetPieceSprites } from './structures/setpieceSprites';

const node = (kind: RouteNode['kind'], col = 3, id = `c${col}r0`): RouteNode => ({
  id,
  kind,
  type: ROUTE.kinds[kind].type,
  name: kind,
  col,
  row: 0,
  links: [],
});

const dist = (a: { x: number; y: number }, b: { x: number; y: number }) => Math.hypot(a.x - b.x, a.y - b.y);

describe('49라운드 지역 흐름 (4-2·6, 계약 ui §11.2·art §7.3)', () => {
  it('1층 단계 → 황무지·전장 → 성문 → 외곽 거리 → 양조 구역 → 지배자의 연회장 (61: 잔 4단)', () => {
    const ids = [0, 1, 2, 3, 4, 5, 6, 7].map((c) => regionIdOf('stage1', c));
    expect(ids).toEqual(['waste', 'waste', 'gate', 'outer', 'outer', 'brewery', 'brewery', 'hall']);
    expect(regionOf('stage1', 7)!.name).toBe('지배자의 연회장');
    // 넘치는 단계는 마지막 지역
    expect(regionIdOf('stage1', 99)).toBe('hall');
    // 2층 임시 지역 2개 · 3층은 지역 없음
    expect(new Set([0, 1, 2, 3].map((c) => regionIdOf('stage2', c))).size).toBe(2);
    expect(regionIdOf('stage3', 0)).toBeNull();
  });

  it('route 스냅샷(UiRouteNode)에 region·desc 가 채워진다', () => {
    for (const stage of ['stage1', 'stage2']) {
      const r = new RouteState(generateRoute(stage, 'seed:0'), 1);
      const ui = r.toUi();
      for (const n of ui.nodes) {
        expect(typeof n.region).toBe('string');
        expect(n.region!.length).toBeGreaterThan(0);
        expect(n.desc!.length).toBeGreaterThan(0);
      }
    }
    const ui = new RouteState(generateRoute('stage1', 'x'), 1).toUi();
    expect(ui.nodes.find((n) => n.col === 0)!.desc).toBe(ROUTE.regions!.waste.desc.birth);
    expect(ui.nodes.find((n) => n.col === 7)!.region).toBe('지배자의 연회장');
  });

  it('지역 타일셋: 1층 5지역 tiles/stage1_<region>, 2층은 층 타일셋(지역 타일셋 없음)', () => {
    expect(regionTilesets()).toEqual(['stage1_brewery', 'stage1_gate', 'stage1_hall', 'stage1_outer', 'stage1_waste']);
    expect(planNodeArena(node('battle', 3), 'stage1', 's').tileset).toBe('stage1_outer');
    expect(planNodeArena(node('battle', 1), 'stage2', 's').tileset).toBeNull();
  });

  it('세트 소품 시트 이름 = set_<region>_<name> + 전장 소품', () => {
    const ids = routeSetPieceSprites();
    expect(ids).toContain('set_waste_stones');
    expect(ids).toContain('set_outer_stall');
    expect(ids).toContain('battlefield_dummy');
    expect(ids).toContain('battlefield_tutorial_sign');
    expect(ids).toContain('battlefield_weapon');
  });
});

describe('49라운드 세트 배치 (7) · 특수 노드 기능은 중앙 (6)', () => {
  it('같은 입력이면 같은 설계도 (결정성)', () => {
    for (const k of ['battle', 'rest', 'shop', 'event', 'boss'] as const) {
      const n = node(k, k === 'boss' ? 6 : 4);
      expect(planNodeArena(n, 'stage1', 'det')).toEqual(planNodeArena(n, 'stage1', 'det'));
    }
  });

  it('휴식 = 중앙 모닥불 광장: 모닥불이 중앙, 둘레 돌·숙성 통·묘·카운터가 원형으로', () => {
    for (let i = 0; i < 20; i++) {
      const p = planNodeArena(node('rest', 4), 'stage1', `r${i}`);
      const c = p.setPiece.center;
      const fire = p.setPiece.fixed.find((f) => f.kind === 'campfire')!;
      expect(fire.function).toBe(true);
      expect(dist({ x: fire.tx + 1, y: fire.ty }, c)).toBeLessThanOrEqual(2);
      const ring = p.setPiece.fixed.filter((f) => f.kind !== 'campfire');
      expect(ring.length).toBeGreaterThanOrEqual(2);
      for (const f of ring) {
        const d = dist({ x: f.tx, y: f.ty }, c);
        expect(d).toBeGreaterThan(3);
        expect(d).toBeLessThan(10);
      }
      const stones = p.setPiece.decor.filter((d) => d.name === 'stones');
      expect(stones.length).toBeGreaterThanOrEqual(6);
      for (const s of stones) expect(dist({ x: s.tx, y: s.ty }, c)).toBeLessThanOrEqual(4);
      expect(stones[0].sprites).toEqual(['set_outer_stones']);
      // 구조물 배치: 세트 자리 그대로
      const placed = planStructures(p.layout, 'stage1', `r${i}`, { node: p.structureNode });
      const pf = placed.find((s) => s.kind === 'campfire')!;
      expect([pf.tx, pf.ty]).toEqual([fire.tx, fire.ty]);
    }
  });

  it('상점 = 중앙 노점 거리: 상인(상점 타일)이 중앙, 노점 구조물은 길 양옆, 길 위에는 무작위 구조물 없음', () => {
    for (const stage of ['stage1', 'stage2'])
      for (let i = 0; i < 10; i++) {
        const p = planNodeArena(node('shop', 4), stage, `s${i}`);
        const A = p.layout.arena!;
        const c = p.setPiece.center;
        expect(A.shop).toEqual({ x: c.x - 1, y: c.y - 1 });
        expect(p.setPiece.fixed.length).toBeGreaterThanOrEqual(2);
        for (const f of p.setPiece.fixed) expect(Math.abs(f.ty - c.y)).toBeGreaterThanOrEqual(2);
        const placed = planStructures(p.layout, stage, `s${i}`, { node: p.structureNode });
        for (const s of placed) {
          const onStreet =
            s.ty <= c.y + 1 && s.ty + s.h - 1 >= c.y - 1 && s.tx + s.w - 1 >= c.x - 14 && s.tx <= c.x + 14;
          expect(onStreet).toBe(false);
        }
        // 1층은 장부대·궤짝, 2층은 전당포·환전대·궤짝·패 탁자
        const kinds = new Set(p.setPiece.fixed.map((f) => f.kind));
        if (stage === 'stage1') expect([...kinds].sort()).toEqual(['chest', 'ledger']);
        else expect(kinds.has('pawn') && kinds.has('exchange')).toBe(true);
      }
  });

  it('이벤트 = 중앙 사건 장소 (잔해 + 궤짝)', () => {
    const p = planNodeArena(node('event', 5), 'stage1', 'e');
    const c = p.setPiece.center;
    const chest = p.setPiece.fixed.find((f) => f.kind === 'chest')!;
    expect(dist({ x: chest.tx, y: chest.ty }, c)).toBeLessThanOrEqual(4);
    expect(p.setPiece.decor.some((d) => d.name === 'wreck' && dist({ x: d.tx, y: d.ty }, c) <= 3)).toBe(true);
  });

  it('전투 = 엄폐 담(벽 섬) 둘레에 짐·술통, 바닥 연결 유지, 시작점·출구 비움', () => {
    for (let i = 0; i < 30; i++) {
      const p = planNodeArena(node('battle', 3), 'stage1', `b${i}`);
      const L = p.layout;
      expect(p.setPiece.cover.length).toBeGreaterThan(0);
      for (const c of p.setPiece.cover) expect(L.tiles[c.y][c.x]).toBe(TileId.Wall);
      expect(floorConnected(L.tiles)).toBe(true);
      const A = L.arena!;
      expect(L.tiles[A.spawn.y][A.spawn.x]).toBe(TileId.Floor);
      const placed = planStructures(L, 'stage1', `b${i}`, { node: p.structureNode });
      const fillers = placed.filter((s) => s.kind === 'crate' || s.kind === 'cask');
      const near = fillers.filter((s) => p.setPiece.anchors.some((a) => dist({ x: s.tx, y: s.ty }, a) <= 4.5));
      expect(near.length).toBeGreaterThan(0);
    }
  });

  it('소품은 바닥 위에만, 세운 소품은 구조물과 겹치지 않는다', () => {
    for (const k of ['battle', 'rest', 'shop', 'event', 'boss', 'birth'] as const)
      for (let i = 0; i < 5; i++) {
        const n = k === 'birth' ? node('birth', 0) : node(k, k === 'boss' ? 6 : 4);
        const p = planNodeArena(n, 'stage1', `d${i}`);
        const placed = planStructures(p.layout, 'stage1', `d${i}`, { node: p.structureNode });
        const structTiles = new Set<string>();
        for (const s of placed)
          for (let y = s.ty; y < s.ty + s.h; y++) for (let x = s.tx; x < s.tx + s.w; x++) structTiles.add(`${x},${y}`);
        for (const d of p.setPiece.decor) {
          if (d.role === 'cover') continue;
          for (let y = d.ty; y < d.ty + d.h; y++)
            for (let x = d.tx; x < d.tx + d.w; x++) {
              expect(p.layout.tiles[y][x]).toBe(TileId.Floor);
              if (!d.floor) expect(structTiles.has(`${x},${y}`)).toBe(false);
            }
        }
        expect(setPieceTiles(p).size).toBeGreaterThan(0);
      }
  });

  it('구조물 예산: 세트 자리가 먼저, 무작위는 남은 예산만 (filler 밖 종류 ≤ budget max)', () => {
    for (let i = 0; i < 20; i++) {
      const p = planNodeArena(node('rest', 4), 'stage1', `q${i}`);
      const placed = planStructures(p.layout, 'stage1', `q${i}`, { node: p.structureNode });
      const kinds = new Set(placed.filter((s) => STRUCTURE_DEFS.get(s.kind)!.group !== 'filler').map((s) => s.kind));
      expect(kinds.size).toBeLessThanOrEqual(Math.max(ROUTE.kinds.rest.budget[1], p.setPiece.fixed.length));
    }
  });

  it('튜토리얼(탄생 전장): 시작점 = 중앙, 혼불 둘레, 표식·허수아비는 바닥, 전장 소품 흩뿌림', () => {
    for (let i = 0; i < 10; i++) {
      const p = planNodeArena(node('birth', 0, 'c0r0'), 'stage1', `t${i}`);
      const A = p.layout.arena!;
      expect(p.tutorial).not.toBeNull();
      expect(A.spawn).toEqual(p.setPiece.center);
      expect(p.setPiece.wisps.length).toBe(ROUTE.setPieces!.battlefield.wisps!.count);
      for (const w of p.setPiece.wisps) expect(dist(w, { x: A.spawn.x + 0.5, y: A.spawn.y + 0.5 })).toBeLessThan(4);
      expect(p.setPiece.signs).toHaveLength(p.tutorial!.steps.length);
      expect(p.setPiece.dummies).toHaveLength(p.tutorial!.dummies.length);
      for (const s of [...p.setPiece.signs, ...p.setPiece.dummies]) expect(p.layout.tiles[s.y][s.x]).toBe(TileId.Floor);
      const props = p.setPiece.decor.filter((d) => d.sprites.some((s) => s.startsWith('battlefield_')));
      expect(props.length).toBeGreaterThan(8);
      // 중앙(탄생 자리) 둘레는 비어 있다
      for (const d of p.setPiece.decor.filter((d) => d.role === 'decor'))
        expect(dist({ x: d.tx, y: d.ty }, p.setPiece.center)).toBeGreaterThan(4);
      expect(planNodeArena(node('road', 1), 'stage1', `t${i}`).tutorial).toBeNull();
    }
  });

  it('진입 대기(노드 없음)는 세트 배치 없이 빈 전투장', () => {
    const p = planNodeArena(null, 'stage2', 'entry');
    expect(p.setPiece.template).toBeNull();
    expect(p.setPiece.fixed).toEqual([]);
    expect(p.layout.rooms[0].type).toBe('start');
  });
});

describe('52라운드 Q9: 쿼터뷰 타일셋 전투장 가장자리', () => {
  it('쿼터뷰면 가장자리 깊이 0~1칸 (북쪽 경계가 거의 한 줄), 아니면 지역 값 그대로', () => {
    const topFloorRows = (quarter: boolean) => {
      const n = {
        id: 'c3r0',
        kind: 'battle',
        type: 'battle',
        name: '',
        col: 3,
        row: 0,
        next: [],
      } as unknown as RouteNode;
      const plan = planNodeArena(n, 'stage1', 'edge-q9', ROUTE, { quarterTileset: () => quarter });
      const L = plan.layout;
      const I = L.rooms[0].interior;
      const rows: number[] = [];
      // 서·동 가장자리 깊이(최대 1칸)가 겹치는 모서리 두 칸은 뺀다
      for (let x = I.x + 2; x < I.x + I.w - 2; x++) {
        for (let y = I.y - 2; y < I.y + I.h; y++)
          if (L.tiles[y][x] === TileId.Floor) {
            rows.push(y - I.y);
            break;
          }
      }
      return rows;
    };
    const q = topFloorRows(true);
    expect(Math.max(...q) - Math.min(...q)).toBeLessThanOrEqual(1);
    const flat = topFloorRows(false);
    expect(Math.max(...flat)).toBeGreaterThan(1);
  });
});
