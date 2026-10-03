/**
 * 52라운드 도트 세분화 시트 메모 (계약 art §11·§12, 결정 round-52 Q8·Q10·Q13). Phaser 의존 없음.
 * - 경로 계층: `sprites/<분류>/v3/` → `v2/` → 기존 (동작 단위로 섞어 쓸 수 있다)
 * - 보폭(stride): 걷기·달리기 재생 배속을 실제 이동 속도에 맞춘다 (이동 속도는 그대로)
 * - 손·칼 앵커: 몸 `handAnchors`, 무기 `gripAnchors`·`handAnchors`·`bladeLocal`·`playerFrameOffset` — 시트 도트 좌표 → 월드
 */
import { ASSETS, SPRITES } from '../core/Constants';
import {
  BODY_VARIANT_BASES,
  FREE_POSE,
  artScale,
  sheetJsonPath,
  type Facing,
  type SheetJson,
  type SheetRequest,
} from './spriteDefs';

/** 새 도트 하위 폴더 (앞이 우선) */
export const SHEET_TIERS: readonly string[] = [ASSETS.V3_DIR, ASSETS.V2_DIR];

/** `sprites/<분류>/<tier>/<파일>` (예: `sprites/player/v3/player_run.json`) */
export function sheetJsonPathTier(r: SheetRequest, tier: string): string {
  const base = sheetJsonPath(r);
  const i = base.lastIndexOf('/');
  return `${base.slice(0, i)}/${tier}${base.slice(i)}`;
}

/**
 * 53라운드 4번 피드백: v3 만 쓰는 묶음 (구 시트·v2 를 더 이상 로드하지 않는다). 주인공 전부 · 칼 오버레이.
 * 대검·단검·활 오버레이는 v3 가 생길 때까지 v3 → v2 → 기존 (동작 단위)
 */
export function v3Only(r: Pick<SheetRequest, 'category' | 'name'>): boolean {
  return SPRITES.V3_ONLY.some((o) => o.category === r.category && (!o.name || o.name === r.name));
}

/**
 * 로드 후보 경로: v3 → v2 → 기존 (마지막이 기존). 새 도트 폴더는 매니페스트에 있을 때만 쓴다(호출 쪽).
 * v3 만 쓰는 묶음(`v3Only`)은 v3 하나 — 호출 쪽은 마지막 후보를 '있으면 로드'로 다루므로 v3 가 없으면 아무것도 안 읽는다
 */
export function sheetJsonCandidates(r: SheetRequest): string[] {
  if (v3Only(r)) return [sheetJsonPathTier(r, ASSETS.V3_DIR)];
  return [...SHEET_TIERS.map((t) => sheetJsonPathTier(r, t)), sheetJsonPath(r)];
}

// --- 무기별 기본 자세 (53라운드 Q19) ---

/** 시트 이름 접두 (`player_idle_free` → `idle_free`) */
const PLAYER_SHEET_PREFIX = 'player_';

/**
 * 무기별 이동 몸 동작 고르기 (기본 동작 idle·walk·run·dash). `has` = 그 동작 시트가 로드됐는지, `sheet` = JSON.
 * 1) 아트 규칙: 로드된 변형·기본 시트 JSON `bodySheetByWeapon[무기]` (문자열 = 이 기본 동작의 시트, 객체 = 동작 → 시트)
 * 2) 이름 규칙: `<기본>_<무기 id>` 3) 기본 몸. 고른 시트가 로드되지 않았으면 다음 단계로
 */
export function bodyActionFor(
  base: string,
  weaponId: string,
  sheet: (action: string) => Pick<SheetJson, 'bodySheetByWeapon'> | undefined,
): string {
  if (!(BODY_VARIANT_BASES as readonly string[]).includes(base)) return base;
  const strip = (v: string) => (v.startsWith(PLAYER_SHEET_PREFIX) ? v.slice(PLAYER_SHEET_PREFIX.length) : v);
  for (const src of [`${base}_${FREE_POSE}`, `${base}_${weaponId}`, base]) {
    const rule = sheet(src)?.bodySheetByWeapon?.[weaponId];
    const pickName = typeof rule === 'string' ? rule : rule && typeof rule === 'object' ? rule[base] : undefined;
    if (typeof pickName !== 'string') continue;
    const action = strip(pickName);
    if (action === base || sheet(action)) return action;
  }
  const named = `${base}_${weaponId}`;
  return sheet(named) ? named : base;
}

// --- 보폭 (52라운드 Q10, 계약 §12) ---

export interface StrideSpec {
  /** 한 주기 동안 이동하는 거리 (시트 도트) */
  px: number;
  /** 한 주기 ms */
  cycleMs: number;
}

/** 시트 그대로(배속 1) 재생할 때의 이동 속도 (월드 단위/초). stride 가 없거나 잘못되면 null */
export function strideSpeed(def: Pick<SheetJson, 'stride' | 'pixelScale'>): number | null {
  const s = def.stride;
  if (!s || !(s.px > 0) || !(s.cycleMs > 0)) return null;
  return (s.px * artScale(def)) / (s.cycleMs / 1000);
}

/**
 * 재생 배속 = 실제 이동 속도 / stride 속도, [STRIDE_RATE_MIN, STRIDE_RATE_MAX] 로 자른다 (임시 범위).
 * stride 가 없거나 멈춰 있으면 1
 */
export function strideRate(
  def: Pick<SheetJson, 'stride' | 'pixelScale'>,
  speedWorld: number,
  /**
   * 53라운드 Q10: 기준 속도(평소 이동). 주면 기준 속도의 배속을 범위로 자른 뒤 실제/기준 비율을 곱한다 —
   * 상한에 걸려도 Shift 달리기(×sprint)는 그만큼 더 빨리 재생 (상한 STRIDE_RATE_MAX × SPRINT_RATE_HEADROOM)
   */
  refSpeed?: number,
): number {
  const natural = strideSpeed(def);
  if (natural === null || !(speedWorld > 0)) return 1;
  const clamp = (v: number, hi: number) => Math.min(hi, Math.max(SPRITES.STRIDE_RATE_MIN, v));
  if (!(refSpeed && refSpeed > 0)) return clamp(speedWorld / natural, SPRITES.STRIDE_RATE_MAX);
  const base = clamp(refSpeed / natural, SPRITES.STRIDE_RATE_MAX);
  return clamp(base * (speedWorld / refSpeed), SPRITES.STRIDE_RATE_MAX * SPRITES.SPRINT_RATE_HEADROOM);
}

// --- 손·칼 앵커 (52라운드 Q13) ---

export type AnchorPoint = [number, number];

export interface HandAnchor {
  /** 해부 기준 오른손 (칼을 쥔다) · 왼손 */
  handR: AnchorPoint;
  handL: AnchorPoint;
}

/** 몸 기준 칼 방향 (θ: 0 = 앞, + = 해부 오른쪽 · elev: + = 위). 칼집 안이면 null */
export interface BladeLocal {
  thetaDeg: number | null;
  elevDeg: number | null;
}

function pick<T>(table: Partial<Record<Facing, T[]>> | undefined, dir: Facing, column: number): T | null {
  const row = table?.[dir];
  if (!Array.isArray(row) || row.length === 0) return null;
  return row[Math.max(0, Math.min(row.length - 1, column))] ?? null;
}

function isPoint(v: unknown): v is AnchorPoint {
  return Array.isArray(v) && v.length >= 2 && typeof v[0] === 'number' && typeof v[1] === 'number';
}

/** 프레임의 양손 앵커 (시트 도트 좌표). 없으면 null */
export function handAt(def: Pick<SheetJson, 'handAnchors'>, dir: Facing, column: number): HandAnchor | null {
  const h = pick(def.handAnchors, dir, column);
  return h && isPoint(h.handR) && isPoint(h.handL) ? h : null;
}

/** 무기를 쥔 손(시트 도트 좌표): gripAnchors → handAnchors.handR. 없으면 null */
export function gripAt(
  def: Pick<SheetJson, 'gripAnchors' | 'handAnchors'>,
  dir: Facing,
  column: number,
): AnchorPoint | null {
  const g = pick(def.gripAnchors, dir, column);
  if (isPoint(g)) return g;
  return handAt(def, dir, column)?.handR ?? null;
}

/** 프레임의 칼 방향 (bladeLocal 은 방향 공통 열 목록). 없거나 칼집 안이면 null */
export function bladeAt(def: Pick<SheetJson, 'bladeLocal'>, column: number): BladeLocal | null {
  const list = def.bladeLocal;
  if (!Array.isArray(list) || list.length === 0) return null;
  const b = list[Math.max(0, Math.min(list.length - 1, column))];
  return b && typeof b.thetaDeg === 'number' ? b : null;
}

/** 시트 도트 좌표 → 피벗 기준 월드 오프셋 (피벗이 호스트 위치에 놓인다고 볼 때) */
export function anchorOffset(
  def: Pick<SheetJson, 'pivot' | 'pixelScale'>,
  p: AnchorPoint,
  pivot: { x: number; y: number } = def.pivot,
): { x: number; y: number } {
  const k = artScale(def);
  return { x: (p[0] - pivot.x) * k, y: (p[1] - pivot.y) * k };
}

/**
 * 무기 오버레이 원점(피벗, 무기 시트 도트): `playerFrameOffset` 이 있고 몸 시트와 도트 배율이 같으면 몸 피벗 + 오프셋
 * ("무기 시트 좌표 = 몸 좌표 + playerFrameOffset"), 아니면 무기 JSON pivot
 */
export function overlayPivot(
  weapon: Pick<SheetJson, 'pivot' | 'pixelScale' | 'playerFrameOffset'>,
  body: Pick<SheetJson, 'pivot' | 'pixelScale'> | undefined,
): { x: number; y: number } {
  const o = weapon.playerFrameOffset;
  if (o && body && artScale(body) === artScale(weapon)) return { x: body.pivot.x + o.x, y: body.pivot.y + o.y };
  return weapon.pivot;
}

// --- 등 상흔 기준점 (53라운드 Q4, 계약 §13) ---

/** 프레임의 상흔 사각형 (시트 도트, x·y = 중심, rot = 도) */
export interface ScarAnchor {
  x: number;
  y: number;
  w: number;
  h: number;
  rot: number;
  visible: boolean;
}

function scarOf(v: unknown): ScarAnchor | null {
  const a = v as Record<string, unknown> | null;
  if (!a || typeof a !== 'object') return null;
  const n = (k: string) => (typeof a[k] === 'number' && Number.isFinite(a[k]) ? (a[k] as number) : null);
  const x = n('x');
  const y = n('y');
  const w = n('w');
  const h = n('h');
  if (x === null || y === null || w === null || h === null) return null;
  return { x, y, w, h, rot: n('rot') ?? 0, visible: a.visible !== false && w > 0 && h > 0 };
}

/**
 * 프레임의 상흔 사각형. scarAnchor 형식: 방향 → 열 목록(handAnchors 와 같음) 또는 시트 프레임 순서 배열(행 = 방향).
 * 없거나 틀리면 null (그 프레임은 상흔을 숨긴다)
 */
export function scarAt(
  def: Pick<SheetJson, 'scarAnchor' | 'frames' | 'directions'>,
  dir: Facing,
  column: number,
): ScarAnchor | null {
  const raw = def.scarAnchor;
  if (Array.isArray(raw)) {
    const row = Math.max(0, def.directions.indexOf(dir));
    const i = raw.length >= def.frames * def.directions.length ? row * def.frames + column : column;
    return scarOf(raw[Math.max(0, Math.min(raw.length - 1, i))]);
  }
  if (raw && typeof raw === 'object') return scarOf(pick(raw as Partial<Record<Facing, unknown[]>>, dir, column));
  return null;
}

/**
 * 상흔 그림 맞춤: 기준 사각형 가로/세로 비(aspect)를 지켜 앵커 사각형(w×h)에 들어가는 크기 (남는 쪽은 가운데).
 * 반환 = 그림 폭·높이 (앵커와 같은 단위)
 */
export function scarFit(anchor: Pick<ScarAnchor, 'w' | 'h'>, aspect: number): { w: number; h: number } {
  const a = aspect > 0 ? aspect : 1;
  return anchor.w / anchor.h > a ? { w: anchor.h * a, h: anchor.h } : { w: anchor.w, h: anchor.w / a };
}
