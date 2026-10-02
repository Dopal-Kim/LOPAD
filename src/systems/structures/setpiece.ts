/**
 * 49라운드 7·6: 노드 전투장 세트 배치(set-piece). 시드 결정적 · Phaser 의존 없음.
 *
 * 노드 종류별 템플릿(data/route.json setPieces)으로 전투장 **중앙**에 기능(모닥불·상인·사건 장소)을 두고,
 * 둘레 구조물(slots)·소품 그림(decor: structures/set_<region>_<name>)·엄폐 담(cover: 벽 타일 섬)을 배치한다.
 * 결과의 `fixed` 는 planStructures 가 무작위 배치보다 먼저 정확한 자리에 놓고(세트 우선, 무작위는 보조),
 * `cover` 는 layout.tiles 를 직접 벽으로 바꾼다(타일셋 인덱스 5·6 = 지역의 담·잔해·술통 더미로 그려짐).
 * 튜토리얼 노드는 표식·허수아비·혼불 자리도 여기서 정한다.
 */
import type { UiStructureKind } from '../../contract/ui';
import { arenaCenter, floorConnected } from '../mapgen/arena';
import { TileId, type FloorLayout, type Rect } from '../mapgen/types';
import { Rng, hashSeed } from '../rng';
import { STRUCTURE_DEFS } from './data';

type Vec = [number, number];

/** 소품 그림 하나의 정의 (좌표는 전투장 중앙 기준 타일 오프셋) */
export interface SetDecorDef {
  name: string;
  /** 시트 후보 (없으면 `set_<region>_<name>`) */
  sprite?: string[];
  at?: Vec;
  /** 중앙에서 반지름 ring 위에 count 개 고르게 (angle = 시작 각도, 없으면 시드) */
  ring?: number;
  angle?: number;
  count?: number;
  /** 전투장 바닥 아무 데나 scatter 개 (중앙·예약 칸 피함) */
  scatter?: number;
  /** cover 앵커 기준 (at 은 앵커에서의 오프셋) */
  anchor?: number;
  /** 차지하는 칸 [w, h] (기본 1×1) */
  size?: Vec;
  /** 바닥에 깔림 (광장 문양·길) — 구조물 아래에 깔려도 된다 */
  floor?: boolean;
  /** 아트가 없을 때 플레이스홀더 색 */
  color?: string;
}

export interface SetSlotDef {
  /** 후보 종류 — 이 노드·이 층에 허용되고 아직 안 쓴 첫 종류 */
  kinds: UiStructureKind[];
  at?: Vec;
  ring?: number;
  angle?: number;
  anchor?: number;
  /** 노드 기능(모닥불·사건 장소) 표시 — 중앙 배치 검사용 */
  function?: boolean;
  chance?: number;
}

export interface SetCoverDef {
  count: Vec;
  anchors: Vec[];
  shapes: Vec[][];
  decor?: { name: string; sprite?: string[]; color?: string };
}

export interface SetPieceDef {
  clearRadius?: number;
  jitterDeg?: number;
  slots?: SetSlotDef[];
  decor?: SetDecorDef[];
  cover?: SetCoverDef;
  fillerNear?: { radius: number };
  /** 상점 노점 거리: 중앙 가로 띠 (구조물 금지) */
  street?: { halfHeight: number; halfWidth: number };
  /** 혼불 자리 (탄생지) */
  wisps?: { ring: number; count: number };
}

/** 튜토리얼 배치 입력 (data/route.json tutorial 의 좌표 부분) */
export interface TutorialLayoutInput {
  signs: Vec[];
  dummies: Vec[];
  signSprite: string[];
  dummySprite: string[];
  /** 49라운드: 표식 i 의 시트 이름 조각 — signSprite 의 `{step}` 을 바꾼다 (없으면 그 후보는 뺀다) */
  signNames?: string[];
}

export type DecorRole = 'decor' | 'cover' | 'sign' | 'dummy';

export interface DecorPlacement {
  /** 노드 안에서 유일 (`stones-3`) */
  id: string;
  name: string;
  role: DecorRole;
  /** 시트 후보 (앞에서부터 로드된 첫 시트) */
  sprites: string[];
  /** 왼쪽 위 타일, 크기 */
  tx: number;
  ty: number;
  w: number;
  h: number;
  floor: boolean;
  color: string;
}

export interface FixedSlot {
  kind: UiStructureKind;
  tx: number;
  ty: number;
  function: boolean;
}

export interface SetPiecePlan {
  template: string | null;
  center: { x: number; y: number };
  /** planStructures 가 먼저 놓을 구조물 */
  fixed: FixedSlot[];
  /** 벽으로 바꾼 엄폐 칸 */
  cover: { x: number; y: number }[];
  /** 엄폐 앵커 (짐·술통을 주변에) */
  anchors: { x: number; y: number }[];
  fillerNear: { anchors: { x: number; y: number }[]; radius: number } | null;
  decor: DecorPlacement[];
  /** 튜토리얼 표식·허수아비 (타일 중심 좌표) */
  signs: { x: number; y: number }[];
  dummies: { x: number; y: number }[];
  /** 혼불 자리 (타일 좌표, 소수) */
  wisps: { x: number; y: number }[];
  /** 무작위 구조물·소품 금지 사각형 */
  reserve: Rect[];
}

export interface SetPieceInput {
  templateId: string | null;
  template: SetPieceDef | null;
  /** 지역 id (시트 이름 set_<region>_<name>) */
  region: string | null;
  seed: number | string;
  /** 이 노드·이 층에 놓을 수 있는 구조물 종류 */
  allowed: (kind: UiStructureKind) => boolean;
  /** 이미 비워 둘 사각형 (시작점·출구·상점) */
  reserve?: readonly Rect[];
  tutorial?: TutorialLayoutInput | null;
}

const DEFAULT_DECOR_COLOR = '#4a443e';
/** 앵커 슬롯이 자리를 못 찾을 때 주변으로 찾아보는 반경 (타일) */
const SLOT_SEARCH_RADIUS = 2;
/** 엄폐 섬이 가장자리 벽에서 떨어져야 하는 칸 */
const COVER_EDGE_GAP = 1;
/** scatter 시도 배수 */
const SCATTER_TRIES = 30;

const k = (x: number, y: number) => `${x},${y}`;

function inRects(rects: readonly Rect[], x: number, y: number): boolean {
  return rects.some((r) => x >= r.x && x < r.x + r.w && y >= r.y && y < r.y + r.h);
}

/** 원형·사각 공용: 중앙 둘레 정사각형 */
function squareAround(c: { x: number; y: number }, r: number): Rect {
  return { x: c.x - r, y: c.y - r, w: r * 2 + 1, h: r * 2 + 1 };
}

/**
 * 소품 시트 후보. 명시 목록이 있으면 그것(49라운드: `{region}` 은 지역 id 로 바꾸고, 지역이 없으면 그 후보는 뺀다),
 * 없으면 `set_<region>_<name>`
 */
export function decorSprites(name: string, region: string | null, explicit?: string[]): string[] {
  if (explicit && explicit.length > 0)
    return explicit.filter((s) => region || !s.includes('{region}')).map((s) => s.replace('{region}', region ?? ''));
  return region ? [`set_${region}_${name}`] : [];
}

/** 표식 i 의 시트 후보 (`{step}` → 그 단계 이름, 이름이 없으면 그 후보는 뺀다) */
function signSprites(tut: TutorialLayoutInput, i: number): string[] {
  const n = tut.signNames?.[i];
  return tut.signSprite.filter((s) => n || !s.includes('{step}')).map((s) => s.replace('{step}', n ?? ''));
}

export function planSetPiece(layout: FloorLayout, input: SetPieceInput): SetPiecePlan {
  const room = layout.rooms[0];
  const I = room.interior;
  const center = layout.arena?.center ?? arenaCenter(I);
  const T = input.template;
  const plan: SetPiecePlan = {
    template: input.templateId,
    center,
    fixed: [],
    cover: [],
    anchors: [],
    fillerNear: null,
    decor: [],
    signs: [],
    dummies: [],
    wisps: [],
    reserve: [],
  };
  const rng = new Rng(hashSeed(`${String(input.seed)}:setpiece`));
  const tiles = layout.tiles;
  const isFloor = (x: number, y: number) => tiles[y]?.[x] === TileId.Floor;
  const rectFloor = (x: number, y: number, w: number, h: number) => {
    for (let ty = y; ty < y + h; ty++) for (let tx = x; tx < x + w; tx++) if (!isFloor(tx, ty)) return false;
    return true;
  };
  const baseReserve = [...(input.reserve ?? [])];
  /** 단단한 것(구조물·엄폐·세운 소품)이 차지한 칸 + 간격 */
  const solidOcc = new Set<string>();
  const occupy = (x: number, y: number, w: number, h: number, gap: number) => {
    for (let ty = y - gap; ty < y + h + gap; ty++)
      for (let tx = x - gap; tx < x + w + gap; tx++) solidOcc.add(k(tx, ty));
  };
  const free = (x: number, y: number, w: number, h: number) => {
    for (let ty = y; ty < y + h; ty++) for (let tx = x; tx < x + w; tx++) if (solidOcc.has(k(tx, ty))) return false;
    return true;
  };
  const clearR = T?.clearRadius ?? 0;
  const centerClear = clearR > 0 ? squareAround(center, clearR) : null;

  // 1) 튜토리얼 표식·허수아비 (먼저 자리 확보 — 엄폐·소품이 덮지 않게)
  const tut = input.tutorial ?? null;
  const tutZones: Rect[] = [];
  const nearestFloor = (x: number, y: number): { x: number; y: number } => {
    for (let r = 0; r <= 4; r++)
      for (let dy = -r; dy <= r; dy++)
        for (let dx = -r; dx <= r; dx++) if (isFloor(x + dx, y + dy)) return { x: x + dx, y: y + dy };
    return { x, y };
  };
  if (tut) {
    tut.signs.forEach(([dx, dy], i) => {
      const p = nearestFloor(center.x + dx, center.y + dy);
      plan.signs.push(p);
      tutZones.push(squareAround(p, 1));
      plan.decor.push(
        decor(`sign-${i}`, 'tutorial_sign', 'sign', signSprites(tut, i), p.x, p.y, 1, 1, true, '#c8a050'),
      );
    });
    tut.dummies.forEach(([dx, dy], i) => {
      const p = nearestFloor(center.x + dx, center.y + dy);
      plan.dummies.push(p);
      tutZones.push(squareAround(p, 1));
      occupy(p.x, p.y, 1, 1, 1);
      plan.decor.push(decor(`dummy-${i}`, 'dummy', 'dummy', [...tut.dummySprite], p.x, p.y, 1, 1, false, '#9a7a4a'));
    });
  }
  const blockedForCover = (x: number, y: number) =>
    inRects(baseReserve, x, y) || inRects(tutZones, x, y) || (centerClear !== null && inRects([centerClear], x, y));

  // 2) 엄폐 담 (벽 섬): 가장자리 벽과 떨어져야 하고, 바닥 연결을 깨면 되돌린다
  if (T?.cover) {
    const C = T.cover;
    const want = rng.int(C.count[0], C.count[1]);
    const anchors = rng.shuffle(C.anchors.map((a, i) => ({ a, i })));
    for (const { a } of anchors) {
      if (plan.anchors.length >= want) break;
      const ax = center.x + a[0];
      const ay = center.y + a[1];
      const shape = rng.pick(C.shapes);
      const cells = shape.map(([sx, sy]) => ({ x: ax + sx, y: ay + sy }));
      const ok = cells.every((c) => {
        if (!isFloor(c.x, c.y) || blockedForCover(c.x, c.y)) return false;
        for (let oy = -1 - COVER_EDGE_GAP; oy <= 1 + COVER_EDGE_GAP; oy++)
          for (let ox = -1 - COVER_EDGE_GAP; ox <= 1 + COVER_EDGE_GAP; ox++) {
            const nx = c.x + ox;
            const ny = c.y + oy;
            const own = cells.some((o) => o.x === nx && o.y === ny);
            if (!own && !isFloor(nx, ny)) return false;
          }
        return true;
      });
      if (!ok) continue;
      for (const c of cells) tiles[c.y][c.x] = TileId.Wall;
      if (!floorConnected(tiles)) {
        for (const c of cells) tiles[c.y][c.x] = TileId.Floor;
        continue;
      }
      plan.cover.push(...cells);
      plan.anchors.push({ x: ax, y: ay });
      for (const c of cells) occupy(c.x, c.y, 1, 1, 1);
      if (C.decor) {
        const n = plan.decor.length;
        plan.decor.push(
          decor(
            `${C.decor.name}-${n}`,
            C.decor.name,
            'cover',
            decorSprites(C.decor.name, input.region, C.decor.sprite),
            ax,
            ay,
            1,
            1,
            false,
            C.decor.color ?? DEFAULT_DECOR_COLOR,
          ),
        );
      }
    }
    if (T.fillerNear && plan.anchors.length > 0)
      plan.fillerNear = { anchors: plan.anchors.map((p) => ({ ...p })), radius: T.fillerNear.radius };
  }

  // 3) 둘레 구조물 슬롯 (중앙 기능 → 둘레)
  const jitter = T?.jitterDeg ?? 0;
  const ringPos = (r: number, deg: number) => {
    const a = ((deg + (jitter > 0 ? rng.int(-jitter, jitter) : 0)) * Math.PI) / 180;
    return { x: center.x + Math.round(Math.cos(a) * r), y: center.y + Math.round(Math.sin(a) * r) };
  };
  const used = new Set<UiStructureKind>();
  for (const s of T?.slots ?? []) {
    if (s.chance !== undefined && !rng.chance(s.chance)) continue;
    let base: { x: number; y: number } | null;
    if (s.anchor !== undefined) {
      const a = plan.anchors[s.anchor];
      base = a ? { x: a.x + (s.at?.[0] ?? 0), y: a.y + (s.at?.[1] ?? 0) } : null;
    } else if (s.ring !== undefined) base = ringPos(s.ring, s.angle ?? 0);
    else base = { x: center.x + (s.at?.[0] ?? 0), y: center.y + (s.at?.[1] ?? 0) };
    if (!base) continue;
    for (const kind of s.kinds) {
      if (used.has(kind) || !input.allowed(kind)) continue;
      const def = STRUCTURE_DEFS.get(kind);
      if (!def) continue;
      const [w, h] = def.size;
      const spot = findSpot(base.x - Math.floor(w / 2), base.y - Math.floor(h / 2), w, h, (x, y) => {
        if (!rectFloor(x, y, w, h) || !free(x, y, w, h)) return false;
        // 기능 슬롯이 아니면 시작점·출구·튜토리얼 자리를 피한다
        for (let ty = y; ty < y + h; ty++)
          for (let tx = x; tx < x + w; tx++)
            if (inRects(baseReserve, tx, ty) || inRects(tutZones, tx, ty)) return Boolean(s.function);
        return true;
      });
      if (!spot) continue;
      plan.fixed.push({ kind, tx: spot.x, ty: spot.y, function: Boolean(s.function) });
      used.add(kind);
      occupy(spot.x, spot.y, w, h, 1);
      break;
    }
  }

  // 4) 소품 그림
  const scatterBlocked: Rect[] = [...baseReserve, ...tutZones];
  if (centerClear) scatterBlocked.push(squareAround(center, clearR + 1));
  for (const d of T?.decor ?? []) {
    const [w, h] = d.size ?? [1, 1];
    const sprites = decorSprites(d.name, input.region, d.sprite);
    const color = d.color ?? DEFAULT_DECOR_COLOR;
    const floor = Boolean(d.floor);
    const put = (cx: number, cy: number): boolean => {
      const x = cx - Math.floor(w / 2);
      const y = cy - Math.floor(h / 2);
      if (!rectFloor(x, y, w, h)) return false;
      if (!floor && !free(x, y, w, h)) return false;
      plan.decor.push(decor(`${d.name}-${plan.decor.length}`, d.name, 'decor', sprites, x, y, w, h, floor, color));
      if (!floor) occupy(x, y, w, h, 0);
      return true;
    };
    if (d.scatter !== undefined) {
      let placed = 0;
      for (let t = 0; t < d.scatter * SCATTER_TRIES && placed < d.scatter; t++) {
        const x = rng.int(I.x, I.x + I.w - w);
        const y = rng.int(I.y, I.y + I.h - h);
        let bad = false;
        for (let ty = y; ty < y + h && !bad; ty++)
          for (let tx = x; tx < x + w; tx++) if (inRects(scatterBlocked, tx, ty)) bad = true;
        if (bad) continue;
        if (put(x + Math.floor(w / 2), y + Math.floor(h / 2))) {
          placed++;
          // 흩뿌린 소품끼리 한 칸 띄운다
          occupy(x, y, w, h, 1);
        }
      }
    } else if (d.ring !== undefined) {
      const n = Math.max(1, d.count ?? 1);
      const start = d.angle ?? rng.int(0, 359);
      for (let i = 0; i < n; i++) {
        const a = ((start + (360 * i) / n) * Math.PI) / 180;
        put(center.x + Math.round(Math.cos(a) * d.ring), center.y + Math.round(Math.sin(a) * d.ring));
      }
    } else if (d.anchor !== undefined) {
      const a = plan.anchors[d.anchor];
      if (a) put(a.x + (d.at?.[0] ?? 0), a.y + (d.at?.[1] ?? 0));
    } else {
      put(center.x + (d.at?.[0] ?? 0), center.y + (d.at?.[1] ?? 0));
    }
  }

  // 5) 혼불 자리
  if (T?.wisps) {
    const n = Math.max(1, T.wisps.count);
    for (let i = 0; i < n; i++) {
      const a = (Math.PI * 2 * i) / n;
      plan.wisps.push({
        x: center.x + 0.5 + Math.cos(a) * T.wisps.ring,
        y: center.y + 0.5 + Math.sin(a) * T.wisps.ring,
      });
    }
  }

  // 6) 무작위 구조물 금지 구역: 중앙 기능 둘레 · 노점 길 · 튜토리얼 자리
  if (centerClear) plan.reserve.push(centerClear);
  if (T?.street)
    plan.reserve.push({
      x: center.x - T.street.halfWidth,
      y: center.y - T.street.halfHeight,
      w: T.street.halfWidth * 2 + 1,
      h: T.street.halfHeight * 2 + 1,
    });
  plan.reserve.push(...tutZones);
  // 세운 소품(바닥 문양 제외) 칸에도 무작위 구조물이 겹치지 않게
  for (const d of plan.decor)
    if (!d.floor && d.role !== 'cover') plan.reserve.push({ x: d.tx, y: d.ty, w: d.w, h: d.h });
  return plan;
}

function decor(
  id: string,
  name: string,
  role: DecorRole,
  sprites: string[],
  tx: number,
  ty: number,
  w: number,
  h: number,
  floor: boolean,
  color: string,
): DecorPlacement {
  return { id, name, role, sprites, tx, ty, w, h, floor, color };
}

/** (x, y) 부터 반경 SLOT_SEARCH_RADIUS 안에서 가까운 순으로 ok 인 첫 자리 */
function findSpot(
  x: number,
  y: number,
  _w: number,
  _h: number,
  ok: (x: number, y: number) => boolean,
): { x: number; y: number } | null {
  const cands: { x: number; y: number; d: number }[] = [];
  for (let dy = -SLOT_SEARCH_RADIUS; dy <= SLOT_SEARCH_RADIUS; dy++)
    for (let dx = -SLOT_SEARCH_RADIUS; dx <= SLOT_SEARCH_RADIUS; dx++)
      cands.push({ x: x + dx, y: y + dy, d: dx * dx + dy * dy });
  cands.sort((a, b) => a.d - b.d || a.y - b.y || a.x - b.x);
  for (const c of cands) if (ok(c.x, c.y)) return { x: c.x, y: c.y };
  return null;
}
