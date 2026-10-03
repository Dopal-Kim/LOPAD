/**
 * 53라운드 4지역 쿼터뷰 바닥(art floors_v2)의 바닥 특징 배치 — Phaser 의존 없음 · 시드 결정적. 그림·충돌은 TileWorld / QuarterView.
 * - `decals[]`: 바닥 위·소품 아래 데칼(통과). 시트 rect 를 발자국 칸에 그대로 깐다
 * - `canal`(양조): 가로 한 줄 수로 — 수로 칸은 걷기 막힘, 다리 2칸만 걷기 가능, 다리 좌우 litNearBridge 칸은 밝은 판.
 *   투사체는 통과(투사체는 타일 충돌이 없다 — 52라운드 Q4 투사체 여부는 인터뷰 중, 임시)
 * 배치 수치는 QUARTER.DECALS·QUARTER.CANAL (임시값)
 */
import { QUARTER } from '../core/Constants';
import { TileId, type FloorLayout } from '../systems/mapgen';
import { Rng, hashSeed } from '../systems/rng';

export interface DecalJson {
  name: string;
  rect: { x: number; y: number; w: number; h: number };
  footprint: [number, number];
  index?: number;
}

export interface CanalJson {
  frames: number[];
  framesLit?: number[];
  frameMs?: number;
  bridge: { left: number; right: number };
  litNearBridge?: number;
  walkable?: boolean;
}

export interface DecalPlacement {
  name: string;
  tx: number;
  ty: number;
}

export type CanalTileKind = 'water' | 'lit' | 'bridgeL' | 'bridgeR';

export interface CanalPlan {
  row: number;
  tiles: { x: number; y: number; kind: CanalTileKind }[];
}

const key = (x: number, y: number) => `${x},${y}`;

/** 출구·상점(2×2)·시작점 둘레 칸 (수로·데칼이 덮지 않게) */
function anchorRows(layout: FloorLayout): Set<number> {
  const A = layout.arena!;
  const rows = new Set<number>();
  const pad = QUARTER.CANAL.ANCHOR_CLEAR_ROWS;
  for (const [y, h] of [
    [A.spawn.y, 1],
    [A.exit.y, 2],
    [A.shop.y, 2],
  ] as const)
    for (let r = y - pad; r < y + h + pad; r++) rows.add(r);
  return rows;
}

/**
 * 수로 한 줄: 북쪽 끝에서 ROW_FROM_NORTH 칸 아래부터 시작점·출구·상점 줄을 피해 내려가며 고른다. 다리 = 가운데에 가장 가까운
 * 걸을 수 있는 2칸.
 * 바닥 칸만(벽 섬·막힌 칸은 건너뜀). 놓을 줄이 없으면 null
 */
export function planCanal(layout: FloorLayout, canal: CanalJson, blocked: ReadonlySet<string>): CanalPlan | null {
  const room = layout.rooms[0];
  if (!room || !layout.arena) return null;
  const I = room.interior;
  const C = QUARTER.CANAL;
  const avoid = anchorRows(layout);
  // 후보 줄 중 막힌 칸(구조물·세트)이 가장 적은 줄 — 막힌 칸은 수로가 끊겨 걸어서 건널 틈이 되므로 (같으면 북쪽 먼저)
  let row = -1;
  let best = Infinity;
  for (let y = I.y + C.ROW_FROM_NORTH; y < I.y + I.h - C.SOUTH_KEEP_ROWS; y++) {
    if (avoid.has(y)) continue;
    let n = 0;
    for (let x = I.x; x < I.x + I.w; x++) if (blocked.has(key(x, y))) n++;
    if (n < best) {
      best = n;
      row = y;
    }
  }
  if (row < 0) return null;
  const cx = layout.arena.center?.x ?? I.x + Math.floor(I.w / 2);
  // 다리 = 가운데에 가장 가까운, 두 칸 모두 바닥이고 막히지 않은 자리 (세트·구조물이 가운데를 차지할 수 있다)
  const open = (x: number) => layout.tiles[row]?.[x] === TileId.Floor && !blocked.has(key(x, row));
  let bl = -1;
  for (let x = I.x; x < I.x + I.w - 1; x++)
    if (open(x) && open(x + 1) && (bl < 0 || Math.abs(x - (cx - 1)) < Math.abs(bl - (cx - 1)))) bl = x;
  if (bl < 0) return null;
  const lit = canal.litNearBridge ?? 0;
  const tiles: CanalPlan['tiles'] = [];
  for (let x = I.x; x < I.x + I.w; x++) {
    if (layout.tiles[row]?.[x] !== TileId.Floor || blocked.has(key(x, row))) continue;
    const kind: CanalTileKind =
      x === bl
        ? 'bridgeL'
        : x === bl + 1
          ? 'bridgeR'
          : Math.min(Math.abs(x - bl), Math.abs(x - bl - 1)) <= lit
            ? 'lit'
            : 'water';
    tiles.push({ x, y: row, kind });
  }
  return { row, tiles };
}

/**
 * 데칼: 이름이 QUARTER.DECALS.CENTER 에 있으면 전투장 가운데(발자국 가운데 맞춤) 한 번, 나머지는 COUNT 범위만큼 무작위 바닥에.
 * 발자국이 전부 바닥이고 막힌 칸·다른 데칼과 겹치지 않을 때만
 */
export function planDecals(
  layout: FloorLayout,
  decals: readonly DecalJson[],
  blocked: ReadonlySet<string>,
  seed: number | string,
): DecalPlacement[] {
  const room = layout.rooms[0];
  if (!room || !layout.arena || decals.length === 0) return [];
  const D = QUARTER.DECALS;
  const I = room.interior;
  const rng = new Rng(hashSeed(`${String(seed)}:decals`));
  const taken = new Set<string>();
  const out: DecalPlacement[] = [];
  const fits = (x: number, y: number, w: number, h: number) => {
    for (let yy = y; yy < y + h; yy++)
      for (let xx = x; xx < x + w; xx++)
        if (layout.tiles[yy]?.[xx] !== TileId.Floor || blocked.has(key(xx, yy)) || taken.has(key(xx, yy))) return false;
    return true;
  };
  const put = (d: DecalJson, x: number, y: number) => {
    const [w, h] = d.footprint;
    for (let yy = y; yy < y + h; yy++) for (let xx = x; xx < x + w; xx++) taken.add(key(xx, yy));
    out.push({ name: d.name, tx: x, ty: y });
  };
  for (const d of decals) {
    const [w, h] = d.footprint;
    if (!(w > 0 && h > 0)) continue;
    if ((D.CENTER as readonly string[]).includes(d.name)) {
      const c = layout.arena.center ?? { x: I.x + Math.floor(I.w / 2), y: I.y + Math.floor(I.h / 2) };
      const x = c.x - Math.floor(w / 2);
      const y = c.y - Math.floor(h / 2);
      if (fits(x, y, w, h)) put(d, x, y);
      continue;
    }
    const want = rng.int(D.COUNT[0], D.COUNT[1]);
    let n = 0;
    for (let t = 0; t < D.TRIES && n < want; t++) {
      const x = rng.int(I.x, I.x + I.w - w);
      const y = rng.int(I.y + D.NORTH_KEEP_TILES, I.y + I.h - h);
      if (!fits(x, y, w, h)) continue;
      put(d, x, y);
      n++;
    }
  }
  return out;
}
