import { describe, expect, it } from 'vitest';
import { BORDER, TILE } from '../core/Constants';
import { ROUTE, type RouteNode } from '../systems/route';
import { planNodeArena } from '../systems/routeArena';
import { STRUCTURE_DEFS } from '../systems/structures/data';
import { TileId } from '../systems/mapgen/types';
import {
  WORLD_PER_LOGICAL,
  borderFiles,
  borderGaps,
  doorPlacement,
  floorRectOf,
  gapIsBandGate,
  northLookUp,
  parseBorder,
  planBorder,
} from './border';

/** 아트 outer 시범과 같은 모양 (lights 일부) */
const RAW = {
  pixelScale: 0.5,
  bands: {
    north: {
      image: 'north.png',
      emissive: 'north_emissive.png',
      width: 3107,
      height: 409,
      baselineY: 377,
      lights: [
        { x: 358.5, y: 325, color: '#eeaf5a', radius: 118, intensity: 0.77, flicker: { amp: 0.04, hz: 3 } },
        { x: 3000, y: 300, radius: 80 },
      ],
    },
    south: { image: 'south.png', width: 2310, height: 136, baselineY: 25, occlusion: { fadeAlpha: 0.45 }, lights: [] },
    west: {
      image: 'west.png',
      width: 256,
      height: 1615,
      baselineX: 256,
      lights: [
        { x: 5.5, y: 168, radius: 79 },
        { x: 39.6, y: 600, radius: 64 },
      ],
    },
    east: { image: 'east.png', width: 256, height: 1615, baselineX: 0, lights: [] },
  },
  camera: { bounds: { left: -200 }, northLookUp: 110 },
  doors: {
    north: {
      file: 'door_north.png',
      emissive: 'door_north_emissive.png',
      w: 314,
      h: 402,
      baselineY: 377,
      openingX: 159.4,
    },
    west: { file: 'door_west.png', w: 256, h: 291, baselineX: 256, openingY: 198 },
  },
};

const battle = (col: number): RouteNode =>
  ({ id: `c${col}r0`, kind: 'battle', type: 'battle', name: '', col, row: 0, next: [] }) as unknown as RouteNode;

describe('53라운드 Q6 외벽 테두리 (border.json → 배치)', () => {
  const def = parseBorder(RAW, 'outer')!;
  const floor = { x0: 144, y0: 144, x1: 656, y1: 464 };

  it('읽기: 네 띠 · 문 조각(file·w·h) · 카메라 여유 · 띠가 빠지면 null', () => {
    expect(def.bands.north.width).toBe(3107);
    expect(def.bands.south.fadeAlpha).toBe(0.45);
    expect(def.doors.north?.image).toBe('door_north.png');
    expect(def.doors.north?.width).toBe(314);
    expect(def.doors.south).toBeUndefined();
    expect(def.cameraSide).toBe(200);
    expect(def.lookUp).toBe(110);
    expect(parseBorder({ ...RAW, ambient: { rgb: [0.34, 0.34, 0.38] } }, 'x')!.ambient).toBe('#575761');
    expect(def.ambient).toBeNull();
    expect(parseBorder({ ...RAW, bands: { ...RAW.bands, east: undefined } }, 'x')).toBeNull();
    expect(borderFiles(def, ['north'])).toEqual([
      'west.png',
      'east.png',
      'north.png',
      'north_emissive.png',
      'south.png',
      'door_north.png',
      'door_north_emissive.png',
    ]);
  });

  it('배치: 북 기준선 = 바닥 북쪽 끝, 서·동 띠 폭까지 덮고, 서 띠 오른쪽 끝 = 바닥 서쪽 끝', () => {
    const k = WORLD_PER_LOGICAL;
    const plan = planBorder(def, floor);
    const north = plan.pieces.filter((p) => p.side === 'north');
    expect(north).toHaveLength(1);
    expect(north[0].x).toBeCloseTo(floor.x0 - 256 * k);
    expect(north[0].y + 377 * k).toBeCloseTo(floor.y0);
    expect(north[0].x + north[0].cropW * north[0].scale).toBeCloseTo(floor.x1 + 256 * k);
    const south = plan.pieces.find((p) => p.side === 'south')!;
    expect(south.y + 25 * k).toBeCloseTo(floor.y1);
    const west = plan.pieces.find((p) => p.side === 'west')!;
    expect(west.x + 256 * k).toBeCloseTo(floor.x0);
    expect(west.y).toBeCloseTo(floor.y0 - 377 * k);
    expect(west.y + west.cropH * west.scale).toBeCloseTo(floor.y1 + (136 - 25) * k);
    // 이미지 px = 논리 / pixelScale → 월드/이미지 px = 0.25
    expect(west.scale).toBeCloseTo(0.25);
    expect(plan.camera).toEqual({
      x0: floor.x0 - 100,
      y0: floor.y0 - 377 * k,
      x1: floor.x1 + 100,
      y1: floor.y1 + 111 * k,
    });
  });

  it('focusX: 북 띠 국소 x 가 바닥 가운데에 오도록 반복 위상 (왼쪽 조각은 앞을 잘라냄)', () => {
    const k = WORLD_PER_LOGICAL;
    const f = parseBorder(
      { ...RAW, bands: { ...RAW.bands, north: { ...RAW.bands.north, width: 1623, focusX: 824 } } },
      'gate',
    )!;
    const north = planBorder(f, floor).pieces.filter((p) => p.side === 'north');
    const cx = (floor.x0 + floor.x1) / 2;
    expect(north.some((p) => Math.abs(p.x + 824 * k - cx) < 1e-6)).toBe(true);
    const lo = Math.min(...north.map((p) => p.x + p.cropX * p.scale));
    const hi = Math.max(...north.map((p) => p.x + (p.cropX + p.cropW) * p.scale));
    expect(lo).toBeCloseTo(floor.x0 - 256 * k);
    expect(hi).toBeCloseTo(floor.x1 + 256 * k);
    expect(north[0].cropX).toBeGreaterThan(0);
    const mirror = parseBorder({ ...RAW, doors: { east: { mirrorOf: 'door_west.png', w: 256, h: 291 } } }, 'x')!;
    expect(mirror.doors.east).toMatchObject({ image: 'door_west.png', flipX: true });
  });

  it("성문 repeat 'sides': 가운데 한 번(focusX = 바닥 가운데) + 좌·우 조각을 바깥으로 반복 · 가운데 문 칸은 띠의 성문", () => {
    const k = WORLD_PER_LOGICAL;
    const north = {
      ...RAW.bands.north,
      width: 808,
      repeat: 'sides',
      focusX: 392,
      sides: { left: { image: 'north_left.png', width: 408 }, right: { image: 'north_right.png', width: 400 } },
    };
    const g = parseBorder({ ...RAW, bands: { ...RAW.bands, north } }, 'gate')!;
    const ps = planBorder(g, floor).pieces.filter((p) => p.side === 'north');
    const cx = (floor.x0 + floor.x1) / 2;
    const center = ps.filter((p) => !p.part);
    expect(center).toHaveLength(1);
    expect(center[0].x + 392 * k).toBeCloseTo(cx);
    const lefts = ps.filter((p) => p.part === 'left');
    const rights = ps.filter((p) => p.part === 'right');
    expect(lefts.length).toBeGreaterThan(0);
    expect(rights.length).toBeGreaterThan(0);
    // 왼쪽 조각의 오른쪽 끝 = 가운데 왼쪽 끝, 오른쪽 조각 시작 = 가운데 오른쪽 끝
    expect(Math.max(...lefts.map((p) => p.x + 408 * k))).toBeCloseTo(center[0].x);
    expect(Math.min(...rights.map((p) => p.x))).toBeCloseTo(center[0].x + 808 * k);
    const span = (p: (typeof ps)[number]) => [p.x + p.cropX * p.scale, p.x + (p.cropX + p.cropW) * p.scale];
    expect(Math.min(...ps.map((p) => span(p)[0]))).toBeCloseTo(floor.x0 - 256 * k);
    expect(Math.max(...ps.map((p) => span(p)[1]))).toBeCloseTo(floor.x1 + 256 * k);
    expect(borderFiles(g, [])).toContain('north_left.png');
    expect(gapIsBandGate(g, floor, { side: 'north', x0: cx - 16, x1: cx + 16, y: floor.y0 })).toBe(true);
    expect(gapIsBandGate(g, floor, { side: 'north', x0: floor.x0 + 32, x1: floor.x0 + 64, y: floor.y0 })).toBe(false);
    expect(gapIsBandGate(def, floor, { side: 'north', x0: cx - 16, x1: cx + 16, y: floor.y0 })).toBe(false);
  });

  it('57라운드 Q17·Q38 조각 띠: pieces[] 를 이어 원 띠 한 장처럼 (틈·겹침 없이, 정수 그림 px), 반복은 조각 묶음 한 주기', () => {
    const k = WORLD_PER_LOGICAL;
    const south = {
      width: 2310,
      height: 136,
      baselineY: 25,
      repeat: 'x',
      lights: [],
      pieces: [
        { image: 'south_0.webp', emissive: 'south_0_emissive.webp', x: 0, y: 0, width: 1155, height: 136 },
        { image: 'south_1.webp', emissive: 'south_1_emissive.webp', x: 1155, y: 0, width: 1155, height: 136 },
      ],
    };
    const d = parseBorder({ ...RAW, bands: { ...RAW.bands, south } }, 'outer')!;
    expect(d.bands.south.images.map((i) => i.image)).toEqual(['south_0.webp', 'south_1.webp']);
    expect(borderFiles(d, [])).toEqual(expect.arrayContaining(['south_0.webp', 'south_1_emissive.webp']));
    expect(borderFiles(d, [])).not.toContain('south.png');
    // 넓은 바닥(띠 한 주기보다 넓게)이면 조각 0·1·0… 순서로 이어진다
    const wide = { x0: 144, y0: 144, x1: 144 + 2310 * k * 2, y1: 464 };
    const ps = planBorder(d, wide).pieces.filter((p) => p.side === 'south');
    expect(ps.map((p) => p.image).slice(0, 3)).toEqual(['south_0.webp', 'south_1.webp', 'south_0.webp']);
    expect(ps[0].emissive).toBe('south_0_emissive.webp');
    for (let i = 1; i < ps.length; i++) {
      const prevEnd = ps[i - 1].x + (ps[i - 1].cropX + ps[i - 1].cropW) * ps[i - 1].scale;
      expect(ps[i].x + ps[i].cropX * ps[i].scale).toBeCloseTo(prevEnd, 9);
    }
    for (const p of ps) {
      for (const v of [p.cropX, p.cropY, p.cropW, p.cropH, p.x / p.scale, p.y / p.scale])
        expect(Number.isInteger(v)).toBe(true);
      expect(p.cropX + p.cropW).toBeLessThanOrEqual(1155 / d.pixelScale);
    }
    // 덮는 범위는 한 장짜리 띠와 같다
    const one = planBorder(def, wide).pieces.filter((p) => p.side === 'south');
    const span = (list: typeof ps) => [
      Math.min(...list.map((p) => p.x + p.cropX * p.scale)),
      Math.max(...list.map((p) => p.x + (p.cropX + p.cropW) * p.scale)),
    ];
    expect(span(ps)).toEqual(span(one));
    // 조각 형식이 틀리면(그림 이름 없음) 띠 없음 → 테두리 없음
    const broken = { ...south, pieces: [{ x: 0, y: 0, width: 10, height: 10 }] };
    expect(parseBorder({ ...RAW, bands: { ...RAW.bands, south: broken } }, 'x')).toBeNull();
  });

  it('광원: 잘린 부분 밖 · 서·동 띠의 바닥 세로 범위 밖은 빼고, 반경은 월드로', () => {
    const plan = planBorder(def, floor);
    const k = WORLD_PER_LOGICAL;
    // 북 x 3000 은 잘린 폭(1536 논리) 밖 · 서 y 168 은 바닥 위(북 띠에 가려짐) → 빠짐
    expect(plan.lights).toHaveLength(2);
    const w = plan.lights.find((l) => l.light.y === 600)!;
    expect(w.y).toBeGreaterThanOrEqual(floor.y0);
    expect(w.y).toBeLessThanOrEqual(floor.y1);
    expect(plan.lights.find((l) => l.light.radius === 118)!.x).toBeCloseTo(floor.x0 - 256 * k + 358.5 * k);
  });

  it('Q8 북쪽 치우침: 북쪽 끝 200 논리 px 안에서 최대 110 (선형), 밖은 0', () => {
    const k = WORLD_PER_LOGICAL;
    expect(northLookUp(def, floor, floor.y0)).toBeCloseTo(110 * k);
    expect(northLookUp(def, floor, floor.y0 + 100 * k)).toBeCloseTo(55 * k);
    expect(northLookUp(def, floor, floor.y0 + BORDER.LOOKUP_ZONE_PX * k)).toBe(0);
    expect(northLookUp(def, floor, floor.y1)).toBe(0);
  });

  it('문 조각: openingX 가 문 칸 가운데, baselineY 줄이 바닥 끝', () => {
    const gap = { side: 'north' as const, x0: 352, x1: 384, y: 144 };
    const at = doorPlacement(def.doors.north!, gap);
    expect(at.x + 159.4 * WORLD_PER_LOGICAL).toBeCloseTo(368);
    expect(at.y + 377 * WORLD_PER_LOGICAL).toBeCloseTo(144);
  });

  it('전투장: 테두리 지역은 가장자리 일직선 · 숨은 저장고 없음 · 문 칸 = 바닥 바로 바깥 빈 칸', () => {
    for (let s = 0; s < 12; s++) {
      const plan = planNodeArena(battle(3), 'stage1', `border${s}`, ROUTE, { border: () => true });
      const L = plan.layout;
      const I = L.rooms[0].interior;
      for (let y = I.y; y < I.y + I.h; y++)
        for (let x = I.x; x < I.x + I.w; x++) expect(L.tiles[y][x]).not.toBe(TileId.Void);
      const fr = floorRectOf(L, TILE)!;
      expect(fr).toEqual({ x0: I.x * TILE, y0: I.y * TILE, x1: (I.x + I.w) * TILE, y1: (I.y + I.h) * TILE });
      for (const g of borderGaps(L, TILE)) {
        const row = g.side === 'north' ? I.y - 1 : I.y + I.h;
        for (let x = g.x0 / TILE; x < g.x1 / TILE; x++) expect(L.tiles[row][x]).toBe(TileId.Void);
      }
    }
    const ev = planNodeArena({ ...battle(4), kind: 'event' } as RouteNode, 'stage1', 'b', ROUTE, {
      border: () => true,
    });
    expect(ev.structureNode.kinds.some((k) => STRUCTURE_DEFS.get(k)?.place === 'cellar')).toBe(false);
    const ev2 = planNodeArena({ ...battle(4), kind: 'event' } as RouteNode, 'stage1', 'b', ROUTE);
    expect(ev2.structureNode.kinds.some((k) => STRUCTURE_DEFS.get(k)?.place === 'cellar')).toBe(true);
  });

  it('Q7 노드 전투장 기본 크기 32×20 (보스는 따로) · 61라운드 단계 2: 전투 노드는 크기 후보 중 하나', () => {
    expect(ROUTE.arena.default).toEqual([32, 20]);
    const plan = planNodeArena(battle(3), 'stage1', 'size', ROUTE);
    const I = plan.layout.rooms[0].interior;
    expect(ROUTE.arena.variety!.sizes!.battle).toContainEqual([I.w, I.h]);
    expect(plan.variety.size).toEqual([I.w, I.h]);
  });
});
