/**
 * 53라운드 Q6 Gemini 외벽 테두리 — 정의 읽기·배치 계산 (Phaser 없음). 그림은 `BorderView`.
 * 근거: 계약 art §13, 아트 `border.json`(지역마다 `assets/tiles/border/<지역>/`). 길이·좌표는 논리 px(960×540 기준) →
 * 월드 = 논리 × WORLD_PER_LOGICAL. 이미지 픽셀 = 논리 / pixelScale.
 *
 * 배치 규칙 (border.json `place`·아트 NOTES 7절):
 * - 북 띠 baselineY 줄 = 바닥 북쪽 끝, x 는 (바닥 왼쪽 − 서 띠 폭) 부터 (바닥 오른쪽 + 동 띠 폭) 까지 반복(마지막 조각은 잘라냄)
 * - 남 띠 baselineY 줄 = 바닥 남쪽 끝, 가로 범위는 북과 같다
 * - 서 띠 baselineX = 바닥 서쪽 끝, 동 띠 baselineX = 바닥 동쪽 끝, 세로는 북 띠 위끝 ~ 남 띠 아래끝 반복
 * - 광원 lights[] 는 조각마다 등록(잘린 부분 밖은 빼기), 서·동 띠 광원은 바닥 세로 범위 밖이면 빼기(lightsRule)
 * - 문·출구: 바닥 바로 바깥 북·남 줄의 열린 틈(void) 칸 → 골목 입구 조각(`doors.<north|south>`, 임시 형식) 또는 어둠
 */
import { BORDER, RENDER } from '../core/Constants';
import { TileId, type FloorLayout } from '../systems/mapgen';

/** 월드 단위 / 논리 px */
export const WORLD_PER_LOGICAL = 1 / RENDER.WORLD_TO_SCREEN;

export type BandSide = 'north' | 'south' | 'west' | 'east';
export const BAND_SIDES: readonly BandSide[] = ['west', 'east', 'north', 'south'];

export interface BorderLight {
  x: number;
  y: number;
  color?: string;
  radius: number;
  intensity?: number;
  flicker?: number | { amp: number; hz?: number };
  kind?: string;
}

export interface BorderBand {
  image: string;
  emissive: string | null;
  width: number;
  height: number;
  /** 북·남: 바닥 끝과 맞닿는 줄 (띠 위끝 기준) */
  baselineY: number;
  /** 서·동: 바닥 끝과 맞닿는 열 (띠 왼끝 기준) */
  baselineX: number;
  lights: BorderLight[];
  /** 남 띠 가림 알파 */
  fadeAlpha: number | null;
  /** 반복 위상: 이 띠 국소 x(논리)를 바닥 가운데에 (성문·연회장 북 띠). 없으면 null = 바닥 왼쪽 − 서 띠 폭부터 */
  focusX: number | null;
  /**
   * 'none' = 한 장만 · 'sides' = 가운데 조각(image) 한 번(focusX 를 바닥 가운데에) + 좌·우 조각(sides)을 바깥으로 반복
   * (성문 북 띠 — Q22: 성문 하나가 가운데) · 그 밖 = 통째 반복
   */
  repeat: 'none' | 'repeat' | 'sides';
  /** repeat 'sides' 의 좌·우 반복 조각 (높이·baselineY 는 가운데와 같다) */
  sides: { left: BorderSidePart; right: BorderSidePart } | null;
}

export interface BorderSidePart {
  image: string;
  emissive: string | null;
  width: number;
  lights: BorderLight[];
}

/**
 * 골목 입구 조각 (border.json `doors.<north|south|west|east>`, 아트 53라운드 Q13 형식 — `file`·`w`·`h`):
 * 북·남 = baselineY 줄이 바닥 끝, 조각 국소 openingX 를 문 칸들의 가운데 x 에. 서·동 = baselineX 열이 바닥 끝, openingY 를 문 칸 가운데 y 에
 */
export interface BorderDoor {
  image: string;
  emissive: string | null;
  width: number;
  height: number;
  baselineY: number;
  baselineX: number;
  openingX: number;
  openingY: number;
  /** 파일 없이 mirrorOf 만 있으면 그 그림을 좌우 반전 */
  flipX: boolean;
  lights: BorderLight[];
}

export interface BorderDef {
  region: string;
  pixelScale: number;
  bands: Record<BandSide, BorderBand>;
  doors: Partial<Record<BandSide, BorderDoor>>;
  /** border.json ambient.rgb (0~1) → '#rrggbb'. 없으면 null — 53라운드 Q38: 주변광은 data/lighting.json 기준 (테두리 명도 보정 기준값으로만 쓴다) */
  ambient: string | null;
  /** 카메라 좌우 여유 (논리 px) · 북쪽 치우침 최대 (논리 px) */
  cameraSide: number;
  lookUp: number;
}

/** 월드 사각형 (바닥: 벽 안쪽 끝) */
export interface WorldRect {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

export interface BorderPiece {
  side: BandSide;
  /** 조각 왼쪽 위 (월드) */
  x: number;
  y: number;
  /** repeat 'sides' 의 좌·우 조각이면 그 쪽 (그림은 band.sides[part]) */
  part?: 'left' | 'right';
  /** 이미지 px 잘라내기: (cropX, cropY) 부터 cropW×cropH */
  cropX: number;
  cropY: number;
  cropW: number;
  cropH: number;
  /** 월드 / 이미지 px */
  scale: number;
}

export interface BorderGap {
  side: 'north' | 'south';
  /** 월드 x 범위 (칸 끝 포함) · 바닥 끝 y */
  x0: number;
  x1: number;
  y: number;
}

export interface BorderPlan {
  pieces: BorderPiece[];
  lights: { x: number; y: number; light: BorderLight }[];
  camera: WorldRect;
  gaps: BorderGap[];
}

// --- 읽기 ---

const num = (v: unknown, fallback: number): number => (typeof v === 'number' && Number.isFinite(v) ? v : fallback);
const str = (v: unknown): string | null => (typeof v === 'string' && v.length > 0 ? v : null);

function lightsOf(raw: unknown): BorderLight[] {
  if (!Array.isArray(raw)) return [];
  const out: BorderLight[] = [];
  for (const l of raw as Record<string, unknown>[]) {
    if (!l || typeof l.x !== 'number' || typeof l.y !== 'number' || typeof l.radius !== 'number') continue;
    const f = l.flicker as BorderLight['flicker'] | undefined;
    out.push({
      x: l.x,
      y: l.y,
      radius: l.radius,
      color: str(l.color) ?? undefined,
      intensity: num(l.intensity, 1),
      flicker: typeof f === 'number' || (f && typeof f.amp === 'number') ? f : 0,
      kind: str(l.kind) ?? undefined,
    });
  }
  return out;
}

function bandOf(raw: unknown): BorderBand | null {
  const b = raw as Record<string, unknown> | undefined;
  if (!b || !str(b.image) || !(num(b.width, 0) > 0) || !(num(b.height, 0) > 0)) return null;
  const occ = b.occlusion as Record<string, unknown> | undefined;
  return {
    image: str(b.image)!,
    emissive: str(b.emissive),
    width: num(b.width, 0),
    height: num(b.height, 0),
    baselineY: num(b.baselineY, 0),
    baselineX: num(b.baselineX, 0),
    lights: lightsOf(b.lights),
    fadeAlpha: occ && typeof occ.fadeAlpha === 'number' ? occ.fadeAlpha : null,
    focusX: typeof b.focusX === 'number' ? b.focusX : null,
    repeat: b.repeat === 'none' || b.repeat === false ? 'none' : b.repeat === 'sides' ? 'sides' : 'repeat',
    sides: sidesOf(b.sides),
  };
}

function sidesOf(raw: unknown): BorderBand['sides'] {
  const r = raw as Record<string, Record<string, unknown> | undefined> | undefined;
  const part = (p: Record<string, unknown> | undefined): BorderSidePart | null =>
    p && str(p.image) && num(p.width, 0) > 0
      ? { image: str(p.image)!, emissive: str(p.emissive), width: num(p.width, 0), lights: lightsOf(p.lights) }
      : null;
  const left = part(r?.left);
  const right = part(r?.right);
  return left && right ? { left, right } : null;
}

function doorOf(raw: unknown): BorderDoor | null {
  const d = raw as Record<string, unknown> | undefined;
  // 동쪽 조각은 서쪽의 좌우 반전일 수 있다 (mirrorOf) — 파일이 따로 있으면 그것
  const own = d ? (str(d.file) ?? str(d.image)) : null;
  const image = own ?? (d ? str(d.mirrorOf) : null);
  const width = d ? num(d.w, num(d.width, 0)) : 0;
  const height = d ? num(d.h, num(d.height, 0)) : 0;
  if (!d || !image || !(width > 0) || !(height > 0)) return null;
  return {
    image,
    emissive: str(d.emissive),
    width,
    height,
    baselineY: num(d.baselineY, height),
    baselineX: num(d.baselineX, 0),
    openingX: num(d.openingX, width / 2),
    openingY: num(d.openingY, height / 2),
    flipX: !own && Boolean(str(d.mirrorOf)),
    lights: lightsOf(d.lights),
  };
}

/** border.json → 정의. 네 띠 중 하나라도 없거나 틀리면 null (테두리 없이 기존 벽 타일) */
export function parseBorder(raw: unknown, region: string): BorderDef | null {
  const j = raw as Record<string, unknown> | null;
  if (!j || typeof j !== 'object') return null;
  const b = (j.bands ?? {}) as Record<string, unknown>;
  const bands = {} as Record<BandSide, BorderBand>;
  for (const side of BAND_SIDES) {
    const band = bandOf(b[side]);
    if (!band) return null;
    bands[side] = band;
  }
  const doorsRaw = (j.doors ?? {}) as Record<string, unknown>;
  const doors: BorderDef['doors'] = {};
  for (const side of BAND_SIDES) {
    const d = doorOf(doorsRaw[side]);
    if (d) doors[side] = d;
  }
  const cam = (j.camera ?? {}) as Record<string, unknown>;
  const bounds = (cam.bounds ?? {}) as Record<string, unknown>;
  const rgb = (j.ambient as { rgb?: unknown } | undefined)?.rgb;
  const ambient =
    Array.isArray(rgb) && rgb.length === 3 && rgb.every((v) => typeof v === 'number')
      ? '#' +
        (rgb as number[])
          .map((v) =>
            Math.round(Math.max(0, Math.min(1, v)) * 255)
              .toString(16)
              .padStart(2, '0'),
          )
          .join('')
      : null;
  return {
    region,
    ambient,
    pixelScale: num(j.pixelScale, 0.5) > 0 ? num(j.pixelScale, 0.5) : 0.5,
    bands,
    doors,
    cameraSide: typeof bounds.left === 'number' ? Math.abs(bounds.left) : BORDER.CAMERA_SIDE_PX,
    lookUp: num(cam.northLookUp, BORDER.LOOKUP_PX),
  };
}

// --- 등록 (Preloader 가 채운다) ---

/** 지역 id → 테두리 정의 (border.json 이 있는 지역만) */
export const borderDefs = new Map<string, BorderDef>();

export function borderFor(region: string | null | undefined): BorderDef | null {
  return region ? (borderDefs.get(region) ?? null) : null;
}

/** `tiles/border/<지역>/border.json` (assets-game 기준) */
export function borderJsonRel(region: string): string {
  return `${BORDER.DIR}/${region}/${BORDER.JSON}`;
}

export function borderFileRel(region: string, file: string): string {
  return `${BORDER.DIR}/${region}/${file}`;
}

/** 띠·문 그림의 텍스처 키 */
export function borderTextureKey(region: string, file: string): string {
  return `border_${region}_${file}`;
}

/** 이 정의가 쓰는 그림 파일 (띠·발광 + 문 조각). doorSides 를 주면 그 쪽 문 조각만 (문 칸이 있는 쪽 — 지연 로드량 줄이기) */
export function borderFiles(def: BorderDef, doorSides?: readonly BandSide[]): string[] {
  const out = new Set<string>();
  for (const s of BAND_SIDES) {
    out.add(def.bands[s].image);
    if (def.bands[s].emissive) out.add(def.bands[s].emissive!);
  }
  for (const p of Object.values(def.bands.north.sides ?? {})) {
    out.add(p.image);
    if (p.emissive) out.add(p.emissive);
  }
  for (const side of doorSides ?? BAND_SIDES) {
    const d = def.doors[side];
    if (!d) continue;
    out.add(d.image);
    if (d.emissive) out.add(d.emissive);
  }
  return [...out];
}

// --- 배치 ---

/** 노드 전투장 바닥 사각형 (월드) = 방 내부 */
export function floorRectOf(layout: FloorLayout, tile: number): WorldRect | null {
  const I = layout.rooms[0]?.interior;
  if (!layout.arena || !I) return null;
  return { x0: I.x * tile, y0: I.y * tile, x1: (I.x + I.w) * tile, y1: (I.y + I.h) * tile };
}

/** 바닥 바로 바깥 북·남 줄의 열린 틈(void) — 문·출구 자리 */
export function borderGaps(layout: FloorLayout, tile: number): BorderGap[] {
  const I = layout.rooms[0]?.interior;
  if (!I) return [];
  const out: BorderGap[] = [];
  const scan = (side: 'north' | 'south', row: number, y: number) => {
    let start = -1;
    for (let x = I.x; x <= I.x + I.w; x++) {
      const open = x < I.x + I.w && layout.tiles[row]?.[x] === TileId.Void;
      if (open && start < 0) start = x;
      if (!open && start >= 0) {
        out.push({ side, x0: start * tile, x1: x * tile, y });
        start = -1;
      }
    }
  };
  scan('north', I.y - 1, I.y * tile);
  scan('south', I.y + I.h, (I.y + I.h) * tile);
  return out;
}

/**
 * 반복 조각: 위상 기준점 phase(그림 국소 0 이 오는 월드 좌표)에서 period 마다, [from, to) 에 보이는 부분만.
 * at = 그림 원점(월드), skip = 그림 앞쪽에서 잘라낸 길이, len = 보이는 길이
 */
function repeatSpans(
  from: number,
  to: number,
  period: number,
  phase = from,
  /** 한 장만 (repeat 'none') — phase 자리에 */
  once = false,
): { at: number; skip: number; len: number }[] {
  const out: { at: number; skip: number; len: number }[] = [];
  if (!(period > 0)) return out;
  let at = once ? phase : phase - Math.ceil((phase - from) / period - 1e-9) * period;
  for (; at < to - 1e-6 && !(once && at > phase); at += period) {
    const a = Math.max(at, from);
    const b = Math.min(at + period, to);
    if (b - a > 1e-6) out.push({ at, skip: a - at, len: b - a });
  }
  return out;
}

/** 테두리 조각·광원·카메라 한계 (월드) */
export function planBorder(def: BorderDef, floor: WorldRect, gaps: BorderGap[] = []): BorderPlan {
  const k = WORLD_PER_LOGICAL;
  const scale = def.pixelScale * k;
  const { north: N, south: S, west: W, east: E } = def.bands;
  const left = floor.x0 - W.width * k;
  const right = floor.x1 + E.width * k;
  const top = floor.y0 - N.baselineY * k;
  const bottom = floor.y1 + (S.height - S.baselineY) * k;
  const pieces: BorderPiece[] = [];
  const lights: BorderPlan['lights'] = [];
  /** x·y = 그림 원점, (sx, sy) 부터 w×h 가 보인다 (월드) */
  const add = (
    side: BandSide,
    band: Pick<BorderBand, 'lights'>,
    x: number,
    y: number,
    sx: number,
    sy: number,
    w: number,
    h: number,
    part?: 'left' | 'right',
  ) => {
    const piece: BorderPiece = {
      side,
      x,
      y,
      cropX: sx / scale,
      cropY: sy / scale,
      cropW: w / scale,
      cropH: h / scale,
      scale,
    };
    if (part) piece.part = part;
    pieces.push(piece);
    for (const l of band.lights) {
      const lx = l.x * k;
      const ly = l.y * k;
      if (lx < sx || lx > sx + w || ly < sy || ly > sy + h) continue;
      const wy = y + ly;
      if ((side === 'west' || side === 'east') && (wy < floor.y0 || wy > floor.y1)) continue;
      lights.push({ x: x + lx, y: wy, light: l });
    }
  };
  for (const [side, band, x] of [
    ['west', W, floor.x0 - W.baselineX * k],
    ['east', E, floor.x1 - E.baselineX * k],
  ] as const)
    for (const s of repeatSpans(top, bottom, band.height * k, top, band.repeat === 'none'))
      add(side, band, x, s.at, 0, s.skip, band.width * k, s.len);
  // focusX(성문·왕좌)가 있으면 그 x 를 바닥 가운데에 — 반복 위상
  const cx = (floor.x0 + floor.x1) / 2;
  const northPhase = N.focusX !== null ? cx - N.focusX * k : left;
  const NH = N.height * k;
  if (N.repeat === 'sides' && N.sides) {
    // 가운데 한 번 + 왼쪽 조각은 가운데 왼쪽 끝에서 왼쪽으로, 오른쪽 조각은 오른쪽 끝에서 오른쪽으로 반복
    const c0 = N.focusX !== null ? northPhase : cx - (N.width * k) / 2;
    const c1 = c0 + N.width * k;
    for (const s of repeatSpans(left, right, N.width * k, c0, true)) add('north', N, s.at, top, s.skip, 0, s.len, NH);
    const L = N.sides.left;
    const R = N.sides.right;
    for (const s of repeatSpans(left, Math.min(c0, right), L.width * k, c0))
      add('north', L, s.at, top, s.skip, 0, s.len, NH, 'left');
    for (const s of repeatSpans(Math.max(c1, left), right, R.width * k, c1))
      add('north', R, s.at, top, s.skip, 0, s.len, NH, 'right');
  } else
    for (const s of repeatSpans(left, right, N.width * k, northPhase, N.repeat === 'none'))
      add('north', N, s.at, top, s.skip, 0, s.len, NH);
  const southPhase = S.focusX !== null ? cx - S.focusX * k : left;
  for (const s of repeatSpans(left, right, S.width * k, southPhase, S.repeat === 'none'))
    add('south', S, s.at, floor.y1 - S.baselineY * k, s.skip, 0, s.len, S.height * k);
  const side = def.cameraSide * k;
  return {
    pieces,
    lights,
    camera: { x0: floor.x0 - side, y0: top, x1: floor.x1 + side, y1: bottom },
    gaps,
  };
}

/** 문 칸(gap) 위 골목 입구 조각의 왼쪽 위 (월드) — openingX 가 문 칸 가운데, baselineY 줄이 바닥 끝 */
export function doorPlacement(door: BorderDoor, gap: BorderGap): { x: number; y: number } {
  const k = WORLD_PER_LOGICAL;
  return { x: (gap.x0 + gap.x1) / 2 - door.openingX * k, y: gap.y - door.baselineY * k };
}

/**
 * 성문처럼 북 띠 가운데 조각(repeat 'sides')에 큰 문이 그려져 있으면, 그 문(focusX) 자리에 걸친 북쪽 문 칸은 띠의 문이 곧 출구
 * — 골목 입구 조각도 어둠도 덧그리지 않는다 (아트 NOTES_borders_f1 10절)
 */
export function gapIsBandGate(def: BorderDef, floor: WorldRect, gap: BorderGap): boolean {
  const N = def.bands.north;
  if (gap.side !== 'north' || N.repeat !== 'sides' || N.focusX === null) return false;
  const cx = (floor.x0 + floor.x1) / 2;
  const tol = BORDER.GATE_CENTER_TOL_PX * WORLD_PER_LOGICAL;
  return gap.x0 <= cx + tol && gap.x1 >= cx - tol;
}

/** Q8: 주인공 발 y 가 바닥 북쪽 끝에서 ZONE 안이면 카메라를 위로 (월드, 0 ~ lookUp) */
export function northLookUp(def: BorderDef, floor: WorldRect, footY: number): number {
  const k = WORLD_PER_LOGICAL;
  const zone = BORDER.LOOKUP_ZONE_PX * k;
  const f = Math.max(0, Math.min(1, 1 - (footY - floor.y0) / zone));
  return f * (BORDER.LOOKUP_BY_REGION[def.region] ?? def.lookUp) * k;
}

/** 53라운드 황무지 둑 위 혼불 자리 (월드, 시드 결정적). 지역 설정이 없으면 [] */
export function wispSpots(region: string, floor: WorldRect, seed: number): { x: number; y: number }[] {
  const W = BORDER.WISPS[region];
  if (!W) return [];
  const k = WORLD_PER_LOGICAL;
  let h = seed >>> 0 || 1;
  const rnd = () => {
    h = Math.imul(h ^ (h >>> 15), 2246822507) >>> 0;
    h = Math.imul(h ^ (h >>> 13), 3266489909) >>> 0;
    return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
  };
  const n = Math.min(W.X_FRACS.length, W.COUNT[0] + Math.floor(rnd() * (W.COUNT[1] - W.COUNT[0] + 1)));
  const fracs =
    n < W.X_FRACS.length
      ? [...W.X_FRACS]
          .sort(() => rnd() - 0.5)
          .slice(0, n)
          .sort()
      : W.X_FRACS;
  return fracs.map((f) => ({
    x: floor.x0 + (floor.x1 - floor.x0) * f + (rnd() * 2 - 1) * W.JITTER_PX * k,
    y: floor.y0 - (W.ABOVE_PX[0] + rnd() * (W.ABOVE_PX[1] - W.ABOVE_PX[0])) * k,
  }));
}
