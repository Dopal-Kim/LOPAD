/**
 * 구조물 배치 (47라운드, 초안 5.1). 시드 결정적 · Phaser 의존 없음.
 * - 층에 나올 수 있는 정의만 (공통 'all' + 그 층 테마). 3층 이상은 공통만.
 * - 예산: common·theme 묶음마다 [min, max] (countBy kind = 종류 수, instance = 개수). filler(짐·술통)는 방마다 따로.
 * - 방당 E형 최대 maxInteractPerRoom. 문 반경·시작점 반경·보스 출구/상점 여유 칸을 피하고, 구조물끼리 gapTiles 띄운다.
 * - 숨은 벽(cellar)은 문이 없는 벽면 바깥 여백이 비어 있을 때만 저장고 자리를 잡는다.
 * 소품(planProps)은 이 결과의 칸을 제외하고 놓인다 (`structureTiles`).
 */
import type { UiStructureKind } from '../../contract/ui';
import { CELL_H, CELL_W, TileId, type Dir, type FloorLayout, type Rect, type Room } from '../mapgen/types';
import { Rng, hashSeed } from '../rng';
import {
  STRUCTURE_DEFS,
  STRUCTURE_RULES,
  availableOn,
  num,
  spriteFor,
  type StructureDef,
  type StructureRules,
} from './data';

export interface CellarPlan {
  side: Dir;
  /** 저장고 바닥 (타일) */
  inner: Rect;
  /** 부수면 바닥이 되는 벽선 칸 */
  opening: { x: number; y: number }[];
  /** 새로 세울 벽 칸 (벽선 제외) */
  ring: { x: number; y: number }[];
}

export interface StructurePlacement {
  /** 층 안에서 유일 (`chest-0`) */
  id: string;
  kind: UiStructureKind;
  roomId: string;
  /** 왼쪽 위 타일, 크기(타일) */
  tx: number;
  ty: number;
  w: number;
  h: number;
  solid: boolean;
  sprite: string;
  cellar?: CellarPlan;
}

export interface PlanOptions {
  defs?: Iterable<StructureDef>;
  rules?: StructureRules;
  /** 데모·검증: 이 층에 나올 수 있는 종류를 확률·예산 없이 전부 놓는다 */
  forceAll?: boolean;
}

const key = (x: number, y: number) => `${x},${y}`;

interface RoomOcc {
  room: Room;
  /** 막힌 칸 (문·시작점·보스 여유 + 놓인 구조물과 간격) */
  blocked: Set<string>;
  interact: number;
  perKind: Map<UiStructureKind, number>;
}

/** 방의 기본 금지 칸: 문 반경 · 시작점 반경 · 보스 출구/상점 여유 */
export function baseBlocked(room: Room, rules: StructureRules = STRUCTURE_RULES): Set<string> {
  const b = new Set<string>();
  const mark = (x0: number, y0: number, x1: number, y1: number) => {
    for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) b.add(key(x, y));
  };
  const I = room.interior;
  const cx = I.x + Math.floor(I.w / 2);
  const cy = I.y + Math.floor(I.h / 2);
  const C = rules.clear;
  if (room.type === 'start') mark(cx - C.startTiles, cy - C.startTiles, cx + C.startTiles, cy + C.startTiles);
  if (room.type === 'boss') mark(cx - C.boss.left, cy - C.boss.up, cx + C.boss.right, cy + C.boss.down);
  for (const d of room.doors)
    for (const t of d.tiles) mark(t.x - C.doorTiles, t.y - C.doorTiles, t.x + C.doorTiles, t.y + C.doorTiles);
  return b;
}

function rectFits(layout: FloorLayout, occ: RoomOcc, x: number, y: number, w: number, h: number): boolean {
  const I = occ.room.interior;
  if (x < I.x || y < I.y || x + w > I.x + I.w || y + h > I.y + I.h) return false;
  for (let ty = y; ty < y + h; ty++)
    for (let tx = x; tx < x + w; tx++) {
      if (layout.tiles[ty]?.[tx] !== TileId.Floor) return false;
      if (occ.blocked.has(key(tx, ty))) return false;
    }
  return true;
}

function occupy(occ: RoomOcc, x: number, y: number, w: number, h: number, gap: number): void {
  for (let ty = y - gap; ty < y + h + gap; ty++)
    for (let tx = x - gap; tx < x + w + gap; tx++) occ.blocked.add(key(tx, ty));
}

/** 벽가 후보: 방 안쪽 테두리에 붙는 사각형 왼쪽 위 */
function wallSpot(rng: Rng, I: Rect, w: number, h: number): { x: number; y: number } {
  const side = rng.int(0, 3);
  if (side === 0) return { x: rng.int(I.x, I.x + I.w - w), y: I.y };
  if (side === 1) return { x: rng.int(I.x, I.x + I.w - w), y: I.y + I.h - h };
  if (side === 2) return { x: I.x, y: rng.int(I.y, I.y + I.h - h) };
  return { x: I.x + I.w - w, y: rng.int(I.y, I.y + I.h - h) };
}

/** 안쪽 후보: 벽에서 1칸 이상 떨어진 사각형 왼쪽 위 */
function anySpot(rng: Rng, I: Rect, w: number, h: number): { x: number; y: number } {
  return {
    x: rng.int(I.x + 1, Math.max(I.x + 1, I.x + I.w - 1 - w)),
    y: rng.int(I.y + 1, Math.max(I.y + 1, I.y + I.h - 1 - h)),
  };
}

/** 중앙에서 가까운 순 후보 (결정적) */
function centerSpots(I: Rect, w: number, h: number): { x: number; y: number }[] {
  const cx = I.x + I.w / 2;
  const cy = I.y + I.h / 2;
  const out: { x: number; y: number; d: number }[] = [];
  for (let y = I.y; y <= I.y + I.h - h; y++)
    for (let x = I.x; x <= I.x + I.w - w; x++) {
      const d = (x + w / 2 - cx) ** 2 + (y + h / 2 - cy) ** 2;
      if (d <= 64) out.push({ x, y, d });
    }
  return out.sort((a, b) => a.d - b.d || a.y - b.y || a.x - b.x);
}

/** 방이 차지한 셀들의 타일 범위 */
function cellBounds(room: Room): Rect {
  const xs = room.cells.map((c) => c.cx);
  const ys = room.cells.map((c) => c.cy);
  const x0 = Math.min(...xs) * CELL_W;
  const y0 = Math.min(...ys) * CELL_H;
  return { x: x0, y: y0, w: (Math.max(...xs) + 1) * CELL_W - x0, h: (Math.max(...ys) + 1) * CELL_H - y0 };
}

/**
 * 숨은 저장고 자리: 문이 없는 벽면 바깥에 inner(가로×세로, 좌우 벽이면 뒤집음)가 전부 빈 공간이고
 * 둘레가 빈 공간 또는 벽이며 방의 셀 안에 들어가면 그 자리. 열리는 칸은 벽선 위 가운데 2칸
 */
export function planCellar(
  layout: FloorLayout,
  room: Room,
  rng: Rng,
  size: [number, number],
  minMargin: number,
  blocked: ReadonlySet<string>,
): CellarPlan | null {
  const I = room.interior;
  const cb = cellBounds(room);
  const doorDirs = new Set(room.doors.map((d) => d.dir));
  const sides = rng.shuffle((['N', 'S', 'W', 'E'] as Dir[]).filter((d) => !doorDirs.has(d)));
  for (const side of sides) {
    const horiz = side === 'N' || side === 'S';
    const w = horiz ? size[0] : size[1];
    const h = horiz ? size[1] : size[0];
    const margin =
      side === 'N'
        ? I.y - cb.y
        : side === 'S'
          ? cb.y + cb.h - (I.y + I.h)
          : side === 'W'
            ? I.x - cb.x
            : cb.x + cb.w - (I.x + I.w);
    if (margin < minMargin) continue;
    const span = horiz ? I.w - w - 2 : I.h - h - 2;
    if (span < 0) continue;
    const offsets = rng.shuffle(Array.from({ length: span + 1 }, (_, i) => i));
    for (const off of offsets) {
      let inner: Rect;
      if (side === 'N') inner = { x: I.x + 1 + off, y: I.y - 1 - h, w, h };
      else if (side === 'S') inner = { x: I.x + 1 + off, y: I.y + I.h + 1, w, h };
      else if (side === 'W') inner = { x: I.x - 1 - w, y: I.y + 1 + off, w, h };
      else inner = { x: I.x + I.w + 1, y: I.y + 1 + off, w, h };
      const plan = checkCellar(layout, side, inner, I, cb, blocked);
      if (plan) return plan;
    }
  }
  return null;
}

function checkCellar(
  layout: FloorLayout,
  side: Dir,
  inner: Rect,
  I: Rect,
  cb: Rect,
  blocked: ReadonlySet<string>,
): CellarPlan | null {
  const at = (x: number, y: number) => layout.tiles[y]?.[x];
  const inCell = (x: number, y: number) => x >= cb.x && y >= cb.y && x < cb.x + cb.w && y < cb.y + cb.h;
  for (let y = inner.y; y < inner.y + inner.h; y++)
    for (let x = inner.x; x < inner.x + inner.w; x++) if (!inCell(x, y) || at(x, y) !== TileId.Void) return null;
  const wallLine = side === 'N' ? I.y - 1 : side === 'S' ? I.y + I.h : side === 'W' ? I.x - 1 : I.x + I.w;
  const ring: { x: number; y: number }[] = [];
  for (let y = inner.y - 1; y <= inner.y + inner.h; y++)
    for (let x = inner.x - 1; x <= inner.x + inner.w; x++) {
      const isInner = x >= inner.x && x < inner.x + inner.w && y >= inner.y && y < inner.y + inner.h;
      if (isInner) continue;
      const onWallLine = side === 'N' || side === 'S' ? y === wallLine : x === wallLine;
      if (onWallLine) continue;
      if (!inCell(x, y)) return null;
      const id = at(x, y);
      if (id !== TileId.Void && id !== TileId.Wall) return null;
      ring.push({ x, y });
    }
  const horiz = side === 'N' || side === 'S';
  const opening: { x: number; y: number }[] = [];
  if (horiz) {
    const x0 = inner.x + Math.floor((inner.w - 2) / 2);
    opening.push({ x: x0, y: wallLine }, { x: x0 + 1, y: wallLine });
  } else {
    const y0 = inner.y + Math.floor((inner.h - 2) / 2);
    opening.push({ x: wallLine, y: y0 }, { x: wallLine, y: y0 + 1 });
  }
  for (const o of opening) {
    if (at(o.x, o.y) !== TileId.Wall) return null;
    // 방 안쪽 바로 앞 칸이 문·시작점 여유에 걸리면 안 된다
    const fx = side === 'W' ? o.x + 1 : side === 'E' ? o.x - 1 : o.x;
    const fy = side === 'N' ? o.y + 1 : side === 'S' ? o.y - 1 : o.y;
    if (blocked.has(key(fx, fy))) return null;
  }
  return { side, inner, opening, ring };
}

function weightedRoom(rng: Rng, rooms: RoomOcc[], weights: Partial<Record<string, number>>): RoomOcc | null {
  const total = rooms.reduce((a, r) => a + (weights[r.room.type] ?? 0), 0);
  if (total <= 0) return null;
  let r = rng.next() * total;
  for (const o of rooms) {
    r -= weights[o.room.type] ?? 0;
    if (r < 0) return o;
  }
  return rooms[rooms.length - 1];
}

/** 예산 묶음에서 이번 층에 쓸 정의 (종류 수 또는 개수 기준) */
function chooseGroup(
  rng: Rng,
  defs: StructureDef[],
  budget: [number, number],
  countBy: 'kind' | 'instance',
  forceAll: boolean,
): { def: StructureDef; count: number }[] {
  const counts = new Map(defs.map((d) => [d.id, rng.int(d.perFloor![0], d.perFloor![1])]));
  const rolled = defs.map((d) => ({ def: d, hit: forceAll || rng.chance(d.chance) }));
  if (forceAll) return defs.map((d) => ({ def: d, count: Math.max(1, counts.get(d.id)!) }));
  const target = rng.int(budget[0], budget[1]);
  const yes = rng.shuffle(rolled.filter((r) => r.hit).map((r) => r.def));
  const no = rng.shuffle(rolled.filter((r) => !r.hit).map((r) => r.def));
  const out: { def: StructureDef; count: number }[] = [];
  let used = 0;
  const cost = (c: number) => (countBy === 'kind' ? 1 : c);
  for (const d of [...yes, ...no]) {
    const fromNo = !yes.includes(d);
    if (fromNo && used >= budget[0]) break;
    let c = Math.max(1, counts.get(d.id)!);
    if (countBy === 'instance') c = Math.min(c, target - used);
    if (c <= 0 || used + cost(c) > target) continue;
    out.push({ def: d, count: c });
    used += cost(c);
    if (used >= target) break;
  }
  return out;
}

const PLACE_ORDER: Record<string, number> = { center: 0, cellar: 1 };

/** 한 층의 구조물 배치 */
export function planStructures(
  layout: FloorLayout,
  stageId: string,
  seed: number | string,
  opts: PlanOptions = {},
): StructurePlacement[] {
  const rules = opts.rules ?? STRUCTURE_RULES;
  const defs = [...(opts.defs ?? STRUCTURE_DEFS.values())].filter((d) => availableOn(d, stageId));
  const rng = new Rng(hashSeed(`${String(seed)}:structures`));
  const occs = layout.rooms.map<RoomOcc>((room) => ({
    room,
    blocked: baseBlocked(room, rules),
    interact: 0,
    perKind: new Map(),
  }));
  const out: StructurePlacement[] = [];
  const serial = new Map<UiStructureKind, number>();
  const gap = rules.clear.gapTiles;
  const forceAll = Boolean(opts.forceAll);

  const push = (def: StructureDef, occ: RoomOcc, x: number, y: number, w: number, h: number, cellar?: CellarPlan) => {
    const n = serial.get(def.id) ?? 0;
    serial.set(def.id, n + 1);
    out.push({
      id: `${def.id}-${n}`,
      kind: def.id,
      roomId: occ.room.id,
      tx: x,
      ty: y,
      w,
      h,
      solid: def.solid,
      sprite: spriteFor(def, stageId),
      cellar,
    });
    occ.perKind.set(def.id, (occ.perKind.get(def.id) ?? 0) + 1);
    if (def.kind === 'interact') occ.interact += 1;
  };

  /** 방 하나 안에서 위치를 찾아 놓는다 */
  const placeIn = (def: StructureDef, occ: RoomOcc): boolean => {
    const [w, h] = def.size;
    const I = occ.room.interior;
    if (def.place === 'cellar') {
      const size = def.params.cellar as [number, number];
      const plan = planCellar(layout, occ.room, rng, size, num(def, 'minMarginTiles'), occ.blocked);
      if (!plan) return false;
      const xs = plan.opening.map((o) => o.x);
      const ys = plan.opening.map((o) => o.y);
      const x = Math.min(...xs);
      const y = Math.min(...ys);
      push(def, occ, x, y, Math.max(...xs) - x + 1, Math.max(...ys) - y + 1, plan);
      // 저장고 입구 앞 한 칸은 비워 둔다
      for (const o of plan.opening) occupy(occ, o.x, o.y, 1, 1, 1);
      return true;
    }
    if (def.place === 'center') {
      for (const s of centerSpots(I, w, h)) {
        if (!rectFits(layout, occ, s.x, s.y, w, h)) continue;
        push(def, occ, s.x, s.y, w, h);
        occupy(occ, s.x, s.y, w, h, gap);
        return true;
      }
      return false;
    }
    for (let t = 0; t < rules.placeTries; t++) {
      const wall = def.place === 'wall' || (def.place === 'wallPrefer' && rng.chance(def.wallBias ?? 0.5));
      const s = wall ? wallSpot(rng, I, w, h) : anySpot(rng, I, w, h);
      if (!rectFits(layout, occ, s.x, s.y, w, h)) continue;
      push(def, occ, s.x, s.y, w, h);
      occupy(occ, s.x, s.y, w, h, gap);
      return true;
    }
    return false;
  };

  /** 정의 1개 인스턴스: 조건 맞는 방을 가중치로 고르고, 안 되면 그 방을 빼고 다시 */
  const placeOne = (def: StructureDef): boolean => {
    let candidates = occs.filter(
      (o) =>
        (def.roomTypes[o.room.type] ?? 0) > 0 &&
        (o.perKind.get(def.id) ?? 0) < def.maxPerRoom &&
        (def.kind !== 'interact' || o.interact < rules.budget.maxInteractPerRoom) &&
        (!def.minRoomW || o.room.interior.w >= def.minRoomW),
    );
    while (candidates.length > 0) {
      const pick = weightedRoom(rng, candidates, def.roomTypes);
      if (!pick) return false;
      if (placeIn(def, pick)) return true;
      candidates = candidates.filter((o) => o !== pick);
    }
    return false;
  };

  // 1) 예산 묶음 (공통 → 테마), 중앙·저장고 자리를 먼저 잡는다
  const chosen: { def: StructureDef; count: number }[] = [];
  for (const group of ['common', 'theme'] as const) {
    const list = defs.filter((d) => d.group === group);
    if (list.length === 0) continue;
    chosen.push(...chooseGroup(rng, list, rules.budget[group], rules.budget.countBy, forceAll));
  }
  // 중앙·저장고 자리 먼저, 그다음 놓일 수 있는 방이 적은(제약이 큰) 것부터
  const roomKinds = (d: StructureDef) => layout.rooms.filter((r) => (d.roomTypes[r.type] ?? 0) > 0).length;
  const order = (d: StructureDef) => (d.place === 'center' || d.place === 'cellar' ? PLACE_ORDER[d.place] : 2);
  chosen.sort((a, b) => order(a.def) - order(b.def) || roomKinds(a.def) - roomKinds(b.def));
  for (const c of chosen) for (let i = 0; i < c.count; i++) placeOne(c.def);

  // 2) filler: 방마다 개수
  for (const def of defs.filter((d) => d.group === 'filler')) {
    if (!forceAll && !rng.chance(def.chance)) continue;
    for (const occ of occs) {
      const range = def.perRoom?.[occ.room.type];
      if (!range) continue;
      const n = Math.min(def.maxPerRoom, rng.int(range[0], range[1]));
      for (let i = 0; i < n; i++) placeIn(def, occ);
    }
  }
  return out;
}

/** 구조물이 차지한 방 안 칸 (소품 제외용). 숨은 벽은 벽선이라 넣지 않아도 되지만 함께 넣는다 */
export function structureTiles(list: readonly StructurePlacement[]): Set<string> {
  const s = new Set<string>();
  for (const p of list)
    for (let y = p.ty; y < p.ty + p.h; y++) for (let x = p.tx; x < p.tx + p.w; x++) s.add(key(x, y));
  return s;
}

/** 단단한 구조물 칸 (걸을 수 없는 칸 — 적 생성·워프 착지 회피). 숨은 벽은 이미 벽이라 제외 */
export function solidStructureTiles(list: readonly StructurePlacement[]): Set<string> {
  return structureTiles(list.filter((p) => p.solid && p.kind !== 'hiddenWall'));
}
