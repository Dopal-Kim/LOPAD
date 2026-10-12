/**
 * 62 루프 2 시스템 D (P2-10 · art §31.9) 노드 세트피스 1개 + 그을음 데칼 흩뿌리기 (Phaser 의존 없음 — 테스트).
 * - 세트피스: 전투 노드마다 하나 — 지역에 맞는 `structures/v3/setpiece_*`(무너진 마차 · 쏟아진 술통) 를 가운데에서 비켜 둔 자리
 *   (발자국 칸이 모두 바닥 · 다른 배치 칸과 안 겹침 · 시작/출구에서 떨어짐) 에 놓는다. 발자국 칸은 막힌다(엄폐).
 * - 그을음: 바닥 데칼 `structures/v3/decal_soot` 변주 6 — 방마다 좌표 해시로 몇 장 (통과 · 막힌 칸 피함).
 */
import { HERO_SETPIECE } from '../core/Constants';
import { TileId, type FloorLayout } from '../systems/mapgen';
import { Rng, hashSeed } from '../systems/rng';

export interface HeroSetpiece {
  sheet: string;
  tx: number;
  ty: number;
  w: number;
  h: number;
  flipX: boolean;
}

export interface SootDecal {
  x: number;
  y: number;
  variant: number;
  flipX: boolean;
}

/** 지역 → 세트피스 시트 후보 (아트 region 표) */
export function heroSheetsFor(region: string | null): readonly string[] {
  if (!region) return [];
  return HERO_SETPIECE.BY_REGION[region] ?? [];
}

const free = (layout: FloorLayout, x: number, y: number, taken: ReadonlySet<string>) =>
  y >= 0 &&
  y < layout.heightTiles &&
  x >= 0 &&
  x < layout.widthTiles &&
  layout.tiles[y][x] === TileId.Floor &&
  !taken.has(`${x},${y}`);

/** 세트피스 자리 (못 찾으면 null) — taken = 이미 쓴 칸 ("x,y") */
export function planHeroSetpiece(
  layout: FloorLayout,
  region: string | null,
  seed: string,
  taken: ReadonlySet<string>,
  footprints: Readonly<Record<string, readonly [number, number]>> = HERO_SETPIECE.FOOTPRINT,
): HeroSetpiece | null {
  const a = layout.arena;
  const sheets = heroSheetsFor(region);
  if (!a || sheets.length === 0) return null;
  const rng = new Rng(hashSeed(`${seed}:hero`));
  const sheet = sheets[rng.int(0, sheets.length - 1)];
  const [w, h] = footprints[sheet] ?? [4, 2];
  const c = a.center ?? a.spawn;
  const offs = [...HERO_SETPIECE.OFFSETS];
  // 노드마다 다른 자리부터
  const start = rng.int(0, offs.length - 1);
  const far = (x: number, y: number, p: { x: number; y: number }) =>
    Math.hypot(x + w / 2 - p.x, y + h / 2 - p.y) >= HERO_SETPIECE.KEEP_AWAY_TILES;
  for (let i = 0; i < offs.length; i++) {
    const [dx, dy] = offs[(start + i) % offs.length];
    const tx = Math.round(c.x + dx - w / 2);
    const ty = Math.round(c.y + dy - h / 2);
    let ok = far(tx, ty, a.spawn) && far(tx, ty, a.exit);
    // 둘레 1칸까지 비어 있어야 (길이 막히지 않게)
    for (let y = ty - 1; ok && y <= ty + h; y++)
      for (let x = tx - 1; ok && x <= tx + w; x++) if (!free(layout, x, y, taken)) ok = false;
    if (ok) return { sheet, tx, ty, w, h, flipX: rng.next() < 0.5 };
  }
  return null;
}

/** 그을음 데칼 자리 (월드 칸 좌표 — 칸 가운데). 지역이 허용할 때만 */
export function planSoot(
  layout: FloorLayout,
  region: string | null,
  seed: string,
  taken: ReadonlySet<string>,
): SootDecal[] {
  if (!region || !HERO_SETPIECE.SOOT_REGIONS.includes(region)) return [];
  const rng = new Rng(hashSeed(`${seed}:soot`));
  const [lo, hi] = HERO_SETPIECE.SOOT_COUNT;
  const n = rng.int(lo, hi);
  const out: SootDecal[] = [];
  for (let t = 0; t < n * 8 && out.length < n; t++) {
    const x = rng.int(1, layout.widthTiles - 2);
    const y = rng.int(1, layout.heightTiles - 2);
    if (!free(layout, x, y, taken) || out.some((d) => Math.abs(d.x - x) + Math.abs(d.y - y) < 3)) continue;
    out.push({ x, y, variant: rng.int(0, HERO_SETPIECE.SOOT_VARIANTS - 1), flipX: rng.next() < 0.5 });
  }
  return out;
}
