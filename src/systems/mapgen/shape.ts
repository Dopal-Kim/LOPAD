/**
 * P19 S2 전투장 형태 틀 (계약 free-combat §3, `data/arenas/<id>.json`) — Phaser 의존 없음 · 시드 결정적.
 * 마스크(문자 격자 = 방 내부, 바깥 벽 1칸은 생성기가 두른다)를 크기·뒤집기 변형한 뒤 칸 종류·문 줄·위험물·적 등장 자리·조명으로 푼다.
 *
 * 크기 변형은 '이음매' 방식: 줄(열)을 늘릴 때는 이웃과 같은 줄을 복제하고, 줄일 때는 이웃과 같은 줄만 지운다 →
 * 다리·난간·문 같은 한 칸짜리 지형이 사라지지 않고 바닥 연결(BFS)이 그대로 유지된다. 지울 줄이 모자라면 그만큼 덜 줄인다.
 */
import type { ArenaDress } from './types';
export type ShapeToken =
  | 'floor'
  | 'wall'
  | 'water'
  | 'drop'
  | 'ledge'
  | 'bridge'
  | 'cover'
  | 'hazard'
  | 'spawn'
  | 'start'
  | 'high'
  | 'stairs'
  | 'door';

/** 위험물 자리 종류 (cask = 술통 · still = 증류기 · pool = 술 웅덩이 · parapet = 부서지는 흉벽) */
export type ShapeHazardKind = 'cask' | 'still' | 'pool' | 'parapet';
export type ShapeStage = 'battle' | 'elite' | 'event' | 'shop' | 'rest' | 'boss';
export type ShapeDoorSide = 'west' | 'east';

export interface ArenaShapeDef {
  id: string;
  name: string;
  /** 어울리는 지역 (노드 → 형태 배정의 1순위) */
  regions: string[];
  /** 변형 뒤 크기 한계 (타일) */
  size: { w: [number, number]; h: [number, number] };
  mask: string[];
  /** 기본 문자표 덮어쓰기 (예: `"~": "drop"` = 낭떠러지) */
  legend?: Record<string, ShapeToken>;
  variants: { flipX: boolean; flipY: boolean; scale: [number, number] };
  /** [입구, 출구] — 면 + 그 면 위 위치(0 = 위, 1 = 아래) */
  doors: { side: ShapeDoorSide; at: number }[];
  /** 마스크 `h` 자리(읽는 순서 번호 slot)마다 위험물 */
  hazards: { kind: ShapeHazardKind; slot: number }[];
  /** 소품 세트 후보 (route.json setPieces id) — 노드마다 하나 */
  props: string[];
  /** 주변광 덮어쓰기 · 고정 광원 (x, y = 마스크 칸, kind = data/lighting.json fallback 키) */
  lighting: {
    ambient: string | null;
    /** P19 2단계 지역별 주변광 (아트 p19 lighting_proposal — 노드 지역이 있으면 ambient 대신) */
    ambientByRegion?: Record<string, string>;
    lights: { x: number; y: number; kind: string }[];
  };
  stage: ShapeStage;
  /** P19 2단계 무대 중심 그림 (art §34 stage_* — 내부 벽 덩어리 위 장식). x, y = 마스크 칸 좌표의 발 자리(덩어리 밑변 가운데) · h = 덩어리 높이 칸 */
  centerArt?: { sheet: string; x: number; y: number; h: number };
  /** P19 2단계 바닥 덮개 (art §34 mock compose): 돌 덮개 = 무대 중심 반경 stoneRadius 칸(배율 반영) · stoneOnHigh = 높은 단 위 */
  dress?: { stoneRadius?: number; stoneOnHigh?: boolean; dropLift?: number };
}

export const DEFAULT_LEGEND: Readonly<Record<string, ShapeToken>> = {
  '.': 'floor',
  '#': 'wall',
  '~': 'water',
  '=': 'bridge',
  c: 'cover',
  h: 'hazard',
  D: 'door',
  S: 'spawn',
  P: 'start',
  '^': 'high',
  '/': 'stairs',
  _: 'ledge',
};

const TOKENS: readonly ShapeToken[] = [
  'floor',
  'wall',
  'water',
  'drop',
  'ledge',
  'bridge',
  'cover',
  'hazard',
  'spawn',
  'start',
  'high',
  'stairs',
  'door',
];
const HAZARDS: readonly ShapeHazardKind[] = ['cask', 'still', 'pool', 'parapet'];
const STAGES: readonly ShapeStage[] = ['battle', 'elite', 'event', 'shop', 'rest', 'boss'];

/** 걸을 수 있는 칸 */
export const WALKABLE: ReadonlySet<ShapeToken> = new Set(['floor', 'bridge', 'high', 'stairs']);
/** 떨어지는 칸 (걷기 막힘 · 밀려 들어가면 낙하) */
export const DROPS: ReadonlySet<ShapeToken> = new Set(['water', 'drop', 'ledge']);

/** 칸 하나에 표식(위험물·등장 자리 등)이 있으면 그 밑 바닥 종류로 풀고 표식은 따로 */
const MARKERS: ReadonlySet<ShapeToken> = new Set(['hazard', 'spawn', 'start', 'door']);

export interface ShapeGrid {
  id: string;
  w: number;
  h: number;
  /** cells[y][x] (표식은 밑 바닥으로 풀린 뒤) */
  cells: ShapeToken[][];
  /** 입구·출구 문 줄 (내부 y, 3칸 띠의 가운데) — 서·동 면 */
  entryRow: number;
  exitRow: number;
  hazards: { x: number; y: number; kind: ShapeHazardKind }[];
  spawns: { x: number; y: number }[];
  /** 광원 (내부 칸 좌표, 칸 가운데 = +0.5 소수) */
  lights: { x: number; y: number; kind: string }[];
  /** 무대 중심 그림 발 자리 (내부 칸 좌표, 소수) */
  centerArt: { sheet: string; x: number; y: number } | null;
  /** 무대 중심 그림이 덮는 벽 덩어리 (내부 칸 — 벽 그림을 그리지 않고 바닥 위에 그림만, 판정은 벽 그대로) */
  centerCells: { x: number; y: number }[];
  dress: ArenaDress;
  flipX: boolean;
  flipY: boolean;
  scale: number;
}

function fail(id: string, msg: string): never {
  throw new Error(`[data] arenas/${id}: ${msg}`);
}

export function validateShape(d: ArenaShapeDef): ArenaShapeDef {
  const id = d.id ?? '?';
  if (typeof d.id !== 'string' || !/^[a-z0-9_]+$/.test(d.id)) fail(id, 'id 형식 (소문자·숫자·_)');
  if (!STAGES.includes(d.stage)) fail(id, `stage 알 수 없음: ${String(d.stage)}`);
  if (!Array.isArray(d.mask) || d.mask.length < 8) fail(id, 'mask 는 8줄 이상');
  const w = d.mask[0].length;
  const legend = { ...DEFAULT_LEGEND, ...(d.legend ?? {}) };
  for (const t of Object.values(d.legend ?? {})) if (!TOKENS.includes(t)) fail(id, `legend 알 수 없는 뜻: ${t}`);
  let slots = 0;
  d.mask.forEach((row, y) => {
    if (row.length !== w) fail(id, `mask ${y}줄 폭 ${row.length} ≠ ${w}`);
    for (const ch of row) {
      const t = legend[ch];
      if (!t) fail(id, `mask 알 수 없는 문자 '${ch}' (${y}줄)`);
      if (t === 'hazard') slots++;
    }
  });
  for (const hz of d.hazards ?? []) {
    if (!HAZARDS.includes(hz.kind)) fail(id, `hazards 종류 알 수 없음: ${String(hz.kind)}`);
    if (!(hz.slot >= 0 && hz.slot < slots)) fail(id, `hazards slot ${hz.slot} — 마스크 h 는 ${slots}곳`);
  }
  if (!Array.isArray(d.doors) || d.doors.length !== 2) fail(id, 'doors 는 [입구, 출구] 2개');
  for (const dr of d.doors)
    if ((dr.side !== 'west' && dr.side !== 'east') || !(dr.at >= 0 && dr.at <= 1))
      fail(id, 'doors[] = { side: west|east, at: 0..1 }');
  if (d.doors[0].side === d.doors[1].side) fail(id, '입구·출구는 다른 면');
  const [s0, s1] = d.variants?.scale ?? [];
  if (!(s0 > 0 && s1 >= s0)) fail(id, 'variants.scale 는 [min, max]');
  for (const k of ['w', 'h'] as const) {
    const r = d.size?.[k];
    if (!Array.isArray(r) || r.length !== 2 || !(r[0] >= 12 && r[1] >= r[0])) fail(id, `size.${k} 는 [min, max]`);
  }
  if (!Array.isArray(d.props)) fail(id, 'props 는 목록');
  if (!d.lighting || !Array.isArray(d.lighting.lights)) fail(id, 'lighting.lights 는 목록');
  return d;
}

/** 표식 칸의 밑 바닥: 4방향 이웃에 높은 단이 있으면 높은 단, 아니면 바닥 */
function baseOf(grid: ShapeToken[][], x: number, y: number): ShapeToken {
  for (const [dx, dy] of [
    [1, 0],
    [-1, 0],
    [0, 1],
    [0, -1],
  ])
    if (grid[y + dy]?.[x + dx] === 'high') return 'high';
  return 'floor';
}

/**
 * 한 축 이음매 변형: rows 를 target 줄로. 늘릴 때 복제 후보 = 이웃과 같은 줄(없으면 아무 줄), 줄일 때 = 이웃과 같은 줄만.
 * origin[i] = 결과 i 번째 줄의 원래 번호
 */
export function resizeAxis<T>(rows: T[][], target: number): { rows: T[][]; origin: number[] } {
  let cur = rows.map((r, i) => ({ r, o: i }));
  const same = (a: T[], b: T[]) => a.length === b.length && a.every((v, i) => v === b[i]);
  const pickNear = (cands: number[], at: number) =>
    cands.reduce((best, c) => (Math.abs(c - at) < Math.abs(best - at) ? c : best), cands[0]);
  const n0 = cur.length;
  if (target > n0) {
    const need = target - n0;
    const stretch = cur.map((_, i) => i).filter((i) => i > 0 && same(cur[i].r, cur[i - 1].r));
    const pool = stretch.length > 0 ? stretch : cur.map((_, i) => i);
    // 고르게: k 번째 복제는 원래 길이의 (k + 0.5)/need 자리에 가장 가까운 후보
    const dup = new Map<number, number>();
    for (let k = 0; k < need; k++) {
      const i = pickNear(pool, ((k + 0.5) / need) * n0);
      dup.set(i, (dup.get(i) ?? 0) + 1);
    }
    const out: { r: T[]; o: number }[] = [];
    cur.forEach((row, i) => {
      out.push(row);
      for (let k = 0; k < (dup.get(i) ?? 0); k++) out.push({ r: [...row.r], o: row.o });
    });
    cur = out;
  } else {
    for (let k = 0, need = n0 - target; k < need; k++) {
      const cands = cur.map((_, i) => i).filter((i) => i > 0 && same(cur[i].r, cur[i - 1].r));
      if (cands.length === 0) break;
      cur.splice(pickNear(cands, ((k + 0.5) / need) * cur.length), 1);
    }
  }
  return { rows: cur.map((c) => c.r), origin: cur.map((c) => c.o) };
}

const transpose = <T>(g: T[][]): T[][] => (g.length === 0 ? [] : g[0].map((_, x) => g.map((row) => row[x])));

/** 원래 번호 → 결과 번호 (지워졌으면 가장 가까운 남은 줄) */
function mapIndex(origin: readonly number[], src: number): number {
  let best = 0;
  for (let i = 0; i < origin.length; i++) {
    if (origin[i] === src) return i;
    if (Math.abs(origin[i] - src) < Math.abs(origin[best] - src)) best = i;
  }
  return best;
}

/** 소수 좌표(광원) 변환: 정수 부분은 mapIndex, 나머지는 그대로 */
function mapCoord(origin: readonly number[], v: number): number {
  const i = Math.floor(v);
  return mapIndex(origin, i) + (v - i);
}

/** 문 줄: at 자리에서 가장 가까운, 그 면 끝 칸이 위아래 1칸까지 걸을 수 있는 줄 */
function doorRow(cells: ShapeToken[][], side: ShapeDoorSide, at: number, id: string): number {
  const h = cells.length;
  const x = side === 'west' ? 0 : cells[0].length - 1;
  const ok = (y: number) => [y - 1, y, y + 1].every((r) => WALKABLE.has(cells[r]?.[x] as ShapeToken));
  const want = Math.round(at * (h - 1));
  for (let d = 0; d < h; d++) for (const y of [want - d, want + d]) if (y >= 1 && y < h - 1 && ok(y)) return y;
  return fail(id, `${side} 면에 3칸 문 자리가 없음`);
}

export interface ShapeVariant {
  scale: number;
  flipX: boolean;
  flipY: boolean;
}

/** 마스크 → 변형된 격자. 크기는 size 한계 안으로 자른다 */
export function buildShape(def: ArenaShapeDef, v: ShapeVariant): ShapeGrid {
  const legend = { ...DEFAULT_LEGEND, ...(def.legend ?? {}) };
  let grid: ShapeToken[][] = def.mask.map((row) => [...row].map((ch) => legend[ch]));
  // 표식 꺼내기 (읽는 순서 = slot 번호)
  const marks: { x: number; y: number; t: ShapeToken; slot: number }[] = [];
  let slot = 0;
  grid.forEach((row, y) =>
    row.forEach((t, x) => {
      if (MARKERS.has(t)) marks.push({ x, y, t, slot: t === 'hazard' ? slot++ : -1 });
    }),
  );
  for (const m of marks) grid[m.y][m.x] = baseOf(grid, m.x, m.y);
  const H0 = grid.length;
  const W0 = grid[0].length;
  const clamp = (n: number, r: [number, number]) => Math.max(r[0], Math.min(r[1], n));
  const tw = clamp(Math.round(W0 * v.scale), def.size.w);
  const th = clamp(Math.round(H0 * v.scale), def.size.h);
  const ry = resizeAxis(grid, th);
  const rx = resizeAxis(transpose(ry.rows), tw);
  grid = transpose(rx.rows);
  let w = grid[0].length;
  let h = grid.length;
  let mx = (x: number) => mapIndex(rx.origin, x);
  let my = (y: number) => mapIndex(ry.origin, y);
  let fx = (x: number) => mapCoord(rx.origin, x);
  let fy = (y: number) => mapCoord(ry.origin, y);
  if (v.flipX) {
    grid = grid.map((row) => [...row].reverse());
    const [a, b] = [mx, fx];
    mx = (x) => w - 1 - a(x);
    fx = (x) => w - b(x);
  }
  if (v.flipY) {
    grid = [...grid].reverse();
    const [a, b] = [my, fy];
    my = (y) => h - 1 - a(y);
    fy = (y) => h - b(y);
  }
  w = grid[0].length;
  h = grid.length;
  const art = def.centerArt
    ? { x: fx(def.centerArt.x), y: fy(v.flipY ? def.centerArt.y - def.centerArt.h : def.centerArt.y) }
    : null;
  const centerCells = art ? wallBlock(grid, Math.floor(art.x), Math.round(art.y) - 1) : [];
  const hzBySlot = new Map(def.hazards.map((hz) => [hz.slot, hz.kind]));
  const hazards: ShapeGrid['hazards'] = [];
  const spawns: ShapeGrid['spawns'] = [];
  for (const m of marks) {
    const p = { x: mx(m.x), y: my(m.y) };
    if (m.t === 'hazard') {
      const kind = hzBySlot.get(m.slot);
      if (kind) hazards.push({ ...p, kind });
    } else if (m.t === 'spawn') spawns.push(p);
  }
  // 뒤집으면 서·동이 바뀐다 — 입구는 늘 서쪽, 출구는 동쪽 (노드 지도 진행 방향)
  const flipSide = (s: ShapeDoorSide): ShapeDoorSide => (v.flipX ? (s === 'west' ? 'east' : 'west') : s);
  const doors = def.doors.map((d) => ({ side: flipSide(d.side), at: v.flipY ? 1 - d.at : d.at }));
  const west = doors.find((d) => d.side === 'west')!;
  const east = doors.find((d) => d.side === 'east')!;
  return {
    id: def.id,
    w,
    h,
    cells: grid,
    entryRow: doorRow(grid, 'west', west.at, def.id),
    exitRow: doorRow(grid, 'east', east.at, def.id),
    hazards,
    spawns,
    lights: def.lighting.lights.map((l) => ({ x: fx(l.x + 0.5), y: fy(l.y + 0.5), kind: l.kind })),
    // 발 자리는 덩어리 밑변 — 위아래로 뒤집으면 덩어리 윗변이 밑변이 된다 (dy = 덩어리 높이 칸)
    centerArt: def.centerArt && art ? { sheet: def.centerArt.sheet, ...art } : null,
    centerCells,
    dress: {
      stoneRadius: (def.dress?.stoneRadius ?? 0) * v.scale,
      stoneOnHigh: Boolean(def.dress?.stoneOnHigh),
      dropLift: Math.max(0, Math.min(1, def.dress?.dropLift ?? 0)),
    },
    flipX: v.flipX,
    flipY: v.flipY,
    scale: v.scale,
  };
}

/** (x, y) 에서 4방향으로 이어진 벽 칸 (무대 중심 덩어리 — 최대 64칸) */
function wallBlock(grid: ShapeToken[][], x: number, y: number): { x: number; y: number }[] {
  const out: { x: number; y: number }[] = [];
  const seen = new Set<string>();
  const q = [{ x, y }];
  while (q.length > 0 && out.length < 64) {
    const c = q.pop()!;
    const key = `${c.x},${c.y}`;
    if (seen.has(key) || grid[c.y]?.[c.x] !== 'wall') continue;
    seen.add(key);
    out.push(c);
    q.push({ x: c.x + 1, y: c.y }, { x: c.x - 1, y: c.y }, { x: c.x, y: c.y + 1 }, { x: c.x, y: c.y - 1 });
  }
  return out;
}
