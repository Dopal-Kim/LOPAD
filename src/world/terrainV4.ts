/**
 * P19 1-A 타일셋 v4 지형 (계약 art §34, 타일셋 JSON `v4` 블록) — Phaser 의존 없음 · 순수.
 * - 바닥: 매크로 8×8 칸 위치 규칙 `macro[(ty%8)*8 + tx%8]` (좌표 해시 금지 — 줄눈이 칸 경계와 무관해 격자가 안 보인다)
 * - 낙하 채움: 물 2×2×4프레임 / 낭떠러지 4×4 정지 (`drop.fillRule`)
 * - 덧그림(한 칸 한 장): 낙하 칸 둑 banks[bits]·안쪽 모서리, 다리, 높은 단 테 lip[bits], 단 끝 칸의 앞면(낮은 칸 위 40도트), 계단
 * - P19 2단계 바닥 꾸밈(`planFloorDress` — art §34 mock compose 규칙): 흙·돌 덮개(꼭짓점 재질 → 칸 cfg, 재질 매크로 × 가면 + 테),
 *   데칼 16(바닥 칸 약 11%), 벽 발치 그늘(북·서·동), 낙하 둑 난간(남·북 — 일부 끊김)
 */
import { TileId, type FloorLayout } from '../systems/mapgen';

export interface TerrainV4 {
  floor: { macro: number[] };
  drop: {
    fill: number[];
    fillRule: { kind: 'water' | 'chasm'; frames?: number; frameMs?: number };
    banks: number[];
    innerCorners: { nw: number; ne: number; sw: number; se: number };
    bridge: { h: number; hEndW: number; hEndE: number; v: number; vEndN: number; vEndS: number };
  };
  /** 벽 세트 (없으면 v2 쿼터뷰 벽) — 앞면 아랫단·윗단·처마, 윗면 = topEdges[bits] (그 쪽 이웃이 벽 아님) */
  wall?: { lower: number[]; upper: number[]; topAboveFront: number; topEdges: number[] };
  terrace: {
    lip: number[];
    face: { mid: number; endL: number; endR: number; single: number };
    stairS: { mid: number; endL: number; endR: number; single: number };
  };
  /** 바닥 꾸밈 표 (없으면 꾸밈 없음 — `dressOf`) */
  overlays?: Record<'dirt' | 'stone', { macro: number[]; mask: number[]; rim: number[] }>;
  decals?: { tiles: number[] };
  floorShadows?: { n: number; w: number; e: number };
}

export interface TerrainDress {
  overlays: Record<'dirt' | 'stone', { macro: number[]; mask: number[]; rim: number[] }>;
  decals: number[];
  shadows: { n: number; w: number; e: number };
  railing: { s: number; n: number; s_broken: number } | null;
}

/** v4 블록의 바닥 꾸밈 표 (모자라면 null) */
export function dressOf(def: { v4?: unknown }): TerrainDress | null {
  const v = def.v4 as
    (Partial<TerrainV4> & { drop?: { railing?: { s: number; n: number; s_broken: number } } }) | undefined;
  const ov = v?.overlays;
  const okOv = (o: { macro: number[]; mask: number[]; rim: number[] } | undefined) =>
    o?.macro?.length === 64 && o.mask?.length === 16 && o.rim?.length === 16;
  if (!ov || !okOv(ov.dirt) || !okOv(ov.stone) || !v.decals?.tiles?.length || !v.floorShadows) return null;
  const r = v.drop?.railing;
  return {
    overlays: ov,
    decals: v.decals.tiles,
    shadows: v.floorShadows,
    railing: r && r.s !== undefined && r.n !== undefined ? r : null,
  };
}

/** 타일셋 JSON 의 v4 블록 (필요한 표가 다 있을 때만) */
export function terrainV4Of(def: { v4?: unknown }): TerrainV4 | null {
  const v = def.v4 as Partial<TerrainV4> | undefined;
  const ok =
    v?.floor?.macro?.length === 64 &&
    (v.drop?.fill?.length ?? 0) >= 16 &&
    v.drop?.banks?.length === 16 &&
    v.terrace?.lip?.length === 16 &&
    Boolean(v.drop?.bridge && v.drop.fillRule && v.drop.innerCorners && v.terrace.face && v.terrace.stairS);
  if (!ok) return null;
  const w = v.wall;
  const wallOk = Boolean(
    w?.lower?.length && w.upper?.length && w.topEdges?.length === 16 && w.topAboveFront !== undefined,
  );
  return { ...(v as TerrainV4), wall: wallOk ? w : undefined };
}

const mod = (a: number, n: number) => ((a % n) + n) % n;

/** 이웃 bits N1·E2·S4·W8 (f = 그 쪽 이웃이 조건에 맞음) */
export function wallEdgeBits(f: (x: number, y: number) => boolean, x: number, y: number): number {
  return (f(x, y - 1) ? 1 : 0) | (f(x + 1, y) ? 2 : 0) | (f(x, y + 1) ? 4 : 0) | (f(x - 1, y) ? 8 : 0);
}

export function floorMacroIndex(v: TerrainV4, x: number, y: number): number {
  return v.floor.macro[mod(y, 8) * 8 + mod(x, 8)];
}

/** 낙하 채움 인덱스 (물은 frame 번째 물결) */
export function dropFillIndex(v: TerrainV4, x: number, y: number, frame = 0): number {
  if (v.drop.fillRule.kind === 'water') {
    const frames = Math.max(1, v.drop.fillRule.frames ?? 1);
    return v.drop.fill[mod(frame, frames) * 4 + mod(y, 2) * 2 + mod(x, 2)];
  }
  return v.drop.fill[mod(y, 4) * 4 + mod(x, 4)];
}

export interface TerrainCells {
  /** 낙하 칸 (단 끝 제외) · 단 끝 칸 · 다리 · 높은 단(계단 제외) · 계단 */
  drop: ReadonlySet<string>;
  ledge: ReadonlySet<string>;
  bridge: ReadonlySet<string>;
  high: ReadonlySet<string>;
  stairs: ReadonlySet<string>;
}

const k = (x: number, y: number) => `${x},${y}`;

export function terrainCellsOf(layout: FloorLayout): TerrainCells {
  const A = layout.arena;
  const stairs = new Set((A?.stairs ?? []).map((p) => k(p.x, p.y)));
  return {
    drop: new Set((A?.drops ?? []).filter((d) => d.kind !== 'ledge').map((d) => k(d.x, d.y))),
    ledge: new Set((A?.drops ?? []).filter((d) => d.kind === 'ledge').map((d) => k(d.x, d.y))),
    bridge: new Set((A?.bridges ?? []).map((p) => k(p.x, p.y))),
    high: new Set((A?.high ?? []).map((p) => k(p.x, p.y)).filter((key) => !stairs.has(key))),
    stairs,
  };
}

/** 바닥 레이어 인덱스 (v4 가 맡는 칸만, 아니면 null): 낙하·다리 = 채움, 단 끝 = 아래 단 바닥, 바닥 = 매크로 */
export function groundV4(
  v: TerrainV4,
  c: TerrainCells,
  id: TileId,
  x: number,
  y: number,
  frame: number,
): number | null {
  const key = k(x, y);
  if (c.drop.has(key) || c.bridge.has(key)) return dropFillIndex(v, x, y, frame);
  if (c.ledge.has(key) || id === TileId.Floor) return floorMacroIndex(v, x, y);
  return null;
}

/** 덧그림 한 칸 한 장 */
export function planTerrainOverlay(
  v: TerrainV4,
  c: TerrainCells,
  layout: FloorLayout,
): { x: number; y: number; index: number }[] {
  const out: { x: number; y: number; index: number }[] = [];
  const open = (x: number, y: number) => {
    const id = layout.tiles[y]?.[x];
    return id === TileId.Floor || id === TileId.Shop || id === TileId.Exit;
  };
  const has = (s: ReadonlySet<string>, x: number, y: number) => s.has(k(x, y));
  /** 낙하 칸에서 본 땅 (낙하·다리 아님 · 걸을 수 있는 칸) */
  const land = (x: number, y: number) => open(x, y) && !has(c.bridge, x, y);
  const low = (x: number, y: number) =>
    (open(x, y) && !has(c.high, x, y) && !has(c.stairs, x, y)) || has(c.ledge, x, y);
  const bits = (x: number, y: number, f: (x: number, y: number) => boolean) => wallEdgeBits(f, x, y);
  const run = (
    cells: ReadonlySet<string>,
    x: number,
    y: number,
    t: { mid: number; endL: number; endR: number; single: number },
  ) => {
    const l = has(cells, x - 1, y);
    const r = has(cells, x + 1, y);
    return l && r ? t.mid : r ? t.endL : l ? t.endR : t.single;
  };
  const faceCells = new Set(
    [...c.ledge].filter((key) => {
      const [x, y] = key.split(',').map(Number);
      return has(c.high, x, y - 1) || has(c.stairs, x, y - 1);
    }),
  );
  const stairFront = new Set(
    [...c.stairs].filter((key) => {
      const [x, y] = key.split(',').map(Number);
      return has(c.ledge, x - 1, y) || has(c.ledge, x + 1, y) || (has(c.high, x, y - 1) && low(x, y + 1));
    }),
  );
  for (const key of c.drop) {
    const [x, y] = key.split(',').map(Number);
    const b = bits(x, y, land);
    if (b) out.push({ x, y, index: v.drop.banks[b] });
    else {
      const ic = v.drop.innerCorners;
      const corner = land(x - 1, y - 1)
        ? ic.nw
        : land(x + 1, y - 1)
          ? ic.ne
          : land(x - 1, y + 1)
            ? ic.sw
            : land(x + 1, y + 1)
              ? ic.se
              : -1;
      if (corner >= 0) out.push({ x, y, index: corner });
    }
  }
  for (const key of c.bridge) {
    const [x, y] = key.split(',').map(Number);
    // 가로 다리 = 다리 줄의 서·동 끝 바깥이 모두 땅 (넓은 다리도 건너는 방향으로)
    let x0 = x;
    let x1 = x;
    while (has(c.bridge, x0 - 1, y)) x0--;
    while (has(c.bridge, x1 + 1, y)) x1++;
    const B = v.drop.bridge;
    const index =
      land(x0 - 1, y) && land(x1 + 1, y)
        ? land(x - 1, y)
          ? B.hEndW
          : land(x + 1, y)
            ? B.hEndE
            : B.h
        : land(x, y - 1)
          ? B.vEndN
          : land(x, y + 1)
            ? B.vEndS
            : B.v;
    out.push({ x, y, index });
  }
  for (const key of c.high) {
    const [x, y] = key.split(',').map(Number);
    // 계단과 이어진 쪽은 테를 끈다
    const b = bits(x, y, (nx, ny) => low(nx, ny) && !has(c.stairs, nx, ny));
    if (b) out.push({ x, y, index: v.terrace.lip[b] });
  }
  for (const key of faceCells) {
    const [x, y] = key.split(',').map(Number);
    out.push({ x, y, index: run(faceCells, x, y, v.terrace.face) });
  }
  for (const key of stairFront) {
    const [x, y] = key.split(',').map(Number);
    out.push({ x, y, index: run(stairFront, x, y, v.terrace.stairS) });
  }
  return out;
}

// --- P19 2단계 바닥 꾸밈 (art §34 mock compose) ---

/** 칸 좌표 해시 0..1 (같은 칸 같은 값 — 난수 상태 없음) */
export function cellHash(x: number, y: number, salt: number): number {
  let h = Math.imul(x * 374761393 + y * 668265263 + salt * 2246822519, 1274126177);
  h = Math.imul(h ^ (h >>> 13), 1103515245);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}

export interface DressPlan {
  /** 덮개 칸: 재질 매크로 인덱스 × 가면 인덱스 (합성) + 테 인덱스 */
  cover: { x: number; y: number; material: 'dirt' | 'stone'; macro: number; mask: number; rim: number }[];
  decals: { x: number; y: number; index: number }[];
  /** 그늘: 한 칸에 둘까지 (북 + 서/동) */
  shadows: { x: number; y: number; index: number; layer: 0 | 1 }[];
  railings: { x: number; y: number; index: number }[];
}

/** 바닥 꾸밈 계획 — 꼭짓점 재질(흙 = 문 ↔ 무대 중심 길 + 얼룩, 돌 = 중심 반경·높은 단) → 칸 cfg (NW1·NE2·SW4·SE8) */
export function planFloorDress(d: TerrainDress, c: TerrainCells, layout: FloorLayout, salt = 7): DressPlan {
  const A = layout.arena;
  const W = layout.widthTiles;
  const H = layout.heightTiles;
  // 돌기둥·무대 중심 덩어리 칸은 벽 그림이 없다 — 그늘을 드리우지 않는다
  const coverCells = new Set([...(A?.cover ?? []), ...(A?.stageCells ?? [])].map((p) => k(p.x, p.y)));
  const isFloor = (x: number, y: number) => {
    const id = layout.tiles[y]?.[x];
    return (id === TileId.Floor || id === TileId.Shop || id === TileId.Exit) && !c.bridge.has(k(x, y));
  };
  const isWall = (x: number, y: number) => layout.tiles[y]?.[x] === TileId.Wall && !coverCells.has(k(x, y));
  const dirt = new Uint8Array((W + 1) * (H + 1));
  const stone = new Uint8Array((W + 1) * (H + 1));
  const vi = (x: number, y: number) => y * (W + 1) + x;
  // 흙: 입구·출구 → 중심 BFS 길 (꼭짓점 = 칸 오른쪽 아래, 85% · 35% 흔들림) + 얼룩 2×2
  const ends = A ? [A.spawn, A.exit] : [];
  const center = A?.center;
  if (center)
    for (const e of ends)
      for (const p of bfsPath(isFloor, W, H, e, center)) {
        if (cellHash(p.x, p.y, salt) < 0.85) dirt[vi(p.x + 1, p.y + 1)] = 1;
        if (cellHash(p.x, p.y, salt + 1) < 0.35) {
          const dx = Math.floor(cellHash(p.x, p.y, salt + 2) * 3) - 1;
          const dy = Math.floor(cellHash(p.x, p.y, salt + 3) * 3) - 1;
          dirt[vi(Math.min(W, Math.max(0, p.x + 1 + dx)), Math.min(H, Math.max(0, p.y + 1 + dy)))] = 1;
        }
      }
  const blobs = Math.floor(W * H * 0.006);
  for (let i = 0; i < blobs; i++) {
    const x = Math.floor(cellHash(i, 0, salt + 4) * W);
    const y = Math.floor(cellHash(i, 1, salt + 4) * H);
    for (const [ox, oy] of [
      [0, 0],
      [1, 0],
      [0, 1],
      [1, 1],
    ] as const)
      dirt[vi(x + ox, y + oy)] = 1;
  }
  // 돌: 무대 중심(그림 덩어리가 있으면 그 가운데, 없으면 전투장 중심) 반경 (세로 1.15 눌림) · 높은 단 (둘레 4칸 중 3칸 이상)
  const R = A?.dress?.stoneRadius ?? 0;
  const sc = A?.stageCells?.length
    ? {
        x: A.stageCells.reduce((a, p) => a + p.x, 0) / A.stageCells.length,
        y: A.stageCells.reduce((a, p) => a + p.y, 0) / A.stageCells.length,
      }
    : center;
  for (let y = 0; y <= H; y++)
    for (let x = 0; x <= W; x++) {
      if (sc && R > 0 && (x - sc.x - 0.5) ** 2 + ((y - sc.y - 0.5) * 1.15) ** 2 <= R * R) stone[vi(x, y)] = 1;
      if (A?.dress?.stoneOnHigh) {
        let n = 0;
        for (const [ox, oy] of [
          [-1, -1],
          [0, -1],
          [-1, 0],
          [0, 0],
        ] as const)
          if (c.high.has(k(x + ox, y + oy))) n++;
        if (n >= 3) stone[vi(x, y)] = 1;
      }
    }
  const out: DressPlan = { cover: [], decals: [], shadows: [], railings: [] };
  for (let y = 0; y < H; y++)
    for (let x = 0; x < W; x++) {
      if (!isFloor(x, y) || c.stairs.has(k(x, y))) continue;
      const mi = mod(y, 8) * 8 + mod(x, 8);
      for (const [material, V] of [
        ['dirt', dirt],
        ['stone', stone],
      ] as const) {
        const cfg = V[vi(x, y)] | (V[vi(x + 1, y)] << 1) | (V[vi(x, y + 1)] << 2) | (V[vi(x + 1, y + 1)] << 3);
        if (!cfg) continue;
        const o = d.overlays[material];
        out.cover.push({ x, y, material, macro: o.macro[mi], mask: o.mask[cfg], rim: o.rim[cfg] });
      }
      // 데칼: 낮은 바닥 약 11% (이웃 위·왼쪽과 같은 데칼 피함)
      if (!c.high.has(k(x, y)) && !c.ledge.has(k(x, y)) && cellHash(x, y, salt + 5) < 0.11) {
        let j = Math.floor(cellHash(x, y, salt + 6) * d.decals.length);
        const near = new Set(out.decals.filter((q) => Math.abs(q.x - x) + Math.abs(q.y - y) === 1).map((q) => q.index));
        if (near.has(d.decals[j])) j = (j + 1) % d.decals.length;
        out.decals.push({ x, y, index: d.decals[j] });
      }
      // 벽 발치 그늘 (기둥 칸은 벽 아님)
      if (isWall(x, y - 1)) out.shadows.push({ x, y, index: d.shadows.n, layer: 0 });
      if (isWall(x - 1, y)) out.shadows.push({ x, y, index: d.shadows.w, layer: 1 });
      else if (isWall(x + 1, y)) out.shadows.push({ x, y, index: d.shadows.e, layer: 1 });
      // 난간: 남쪽이 낙하 칸이면 s(다섯 칸마다 끊김 — 떨어뜨릴 수 있는 틈), 북쪽이면 n(네 칸마다 비움)
      const rl = d.railing;
      if (rl && c.drop.has(k(x, y + 1))) {
        const idx = (x * 7 + y) % 5 ? rl.s : (x + y) % 2 ? rl.s_broken : -1;
        if (idx >= 0) out.railings.push({ x, y, index: idx });
      } else if (rl && c.drop.has(k(x, y - 1)) && (x * 3 + y) % 4) out.railings.push({ x, y, index: rl.n });
    }
  return out;
}

/** 4방향 BFS 최단 길 (칸 목록, 못 가면 []) */
function bfsPath(
  ok: (x: number, y: number) => boolean,
  W: number,
  H: number,
  a: { x: number; y: number },
  b: { x: number; y: number },
): { x: number; y: number }[] {
  const prev = new Int32Array(W * H).fill(-2);
  const start = a.y * W + a.x;
  const goal = b.y * W + b.x;
  if (a.x < 0 || a.y < 0 || a.x >= W || a.y >= H) return [];
  prev[start] = -1;
  const q = [start];
  for (let i = 0; i < q.length && prev[goal] === -2; i++) {
    const cx = q[i] % W;
    const cy = Math.floor(q[i] / W);
    for (const [ox, oy] of [
      [1, 0],
      [-1, 0],
      [0, 1],
      [0, -1],
    ] as const) {
      const nx = cx + ox;
      const ny = cy + oy;
      if (nx < 0 || ny < 0 || nx >= W || ny >= H) continue;
      const n = ny * W + nx;
      if (prev[n] !== -2 || !ok(nx, ny)) continue;
      prev[n] = q[i];
      q.push(n);
    }
  }
  if (prev[goal] === -2) return [];
  const out: { x: number; y: number }[] = [];
  for (let c = goal; c >= 0; c = prev[c]) out.push({ x: c % W, y: Math.floor(c / W) });
  return out;
}
