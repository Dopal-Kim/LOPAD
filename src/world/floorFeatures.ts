/**
 * 53라운드 4지역 쿼터뷰 바닥(art floors_v2)의 바닥 특징 배치 — Phaser 의존 없음 · 시드 결정적. 그림·충돌은 TileWorld / QuarterView.
 * - `decals[]`: 바닥 위·소품 아래 데칼(통과). 시트 rect 를 발자국 칸에 그대로 깐다
 * - `canal`(양조 수로 그림): P19 S2 — 형태 틀의 물 낙하 칸(`arena.drops` water)·다리 칸(`arena.bridges`)에 그대로 그린다
 *   (53라운드 가로 한 줄 수로 배치는 형태 틀로 교체해 지웠다). 물 칸은 빈 칸이라 걷기 막힘, 다리는 바닥. 다리와 같은 줄
 *   litNearBridge 칸 안 물은 밝은 판. 투사체는 통과(타일 충돌 없음)
 * 배치 수치는 QUARTER.DECALS (임시값)
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
  tiles: { x: number; y: number; kind: CanalTileKind }[];
}

const key = (x: number, y: number) => `${x},${y}`;

/**
 * P19 S2: 형태 틀 물 칸·다리 칸 → 수로 그림 칸. 다리는 줄마다 이어진 다리 칸 묶음의 왼쪽 끝부터 좌·우 번갈아.
 * 물 낙하 칸이 없으면 null
 */
export function canalFromArena(layout: FloorLayout, canal: Pick<CanalJson, 'litNearBridge'>): CanalPlan | null {
  const A = layout.arena;
  const water = (A?.drops ?? []).filter((d) => d.kind === 'water');
  if (!A || water.length === 0) return null;
  const bridge = new Set((A.bridges ?? []).map((b) => key(b.x, b.y)));
  const tiles: CanalPlan['tiles'] = [];
  for (const b of A.bridges ?? []) {
    let run = 0;
    while (bridge.has(key(b.x - run - 1, b.y))) run++;
    tiles.push({ x: b.x, y: b.y, kind: run % 2 === 0 ? 'bridgeL' : 'bridgeR' });
  }
  const lit = canal.litNearBridge ?? 0;
  const nearBridge = (x: number, y: number) => {
    for (let d = 1; d <= lit; d++) if (bridge.has(key(x - d, y)) || bridge.has(key(x + d, y))) return true;
    return false;
  };
  for (const w of water) tiles.push({ x: w.x, y: w.y, kind: nearBridge(w.x, w.y) ? 'lit' : 'water' });
  return { tiles };
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
