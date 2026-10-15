/**
 * P19 1-A 타일셋 v4 지형 (계약 art §34, 타일셋 JSON `v4` 블록) — Phaser 의존 없음 · 순수.
 * - 바닥: 매크로 8×8 칸 위치 규칙 `macro[(ty%8)*8 + tx%8]` (좌표 해시 금지 — 줄눈이 칸 경계와 무관해 격자가 안 보인다)
 * - 낙하 채움: 물 2×2×4프레임 / 낭떠러지 4×4 정지 (`drop.fillRule`)
 * - 덧그림(한 칸 한 장): 낙하 칸 둑 banks[bits]·안쪽 모서리, 다리, 높은 단 테 lip[bits], 단 끝 칸의 앞면(낮은 칸 위 40도트), 계단
 * shortcut: 흙·돌 덮개(가면 합성·굽기)·벽 발치 그늘·데칼 16·난간·v4 벽 세트는 아직 안 쓴다 — 바닥 굽기(RenderTexture) 단계에서.
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
