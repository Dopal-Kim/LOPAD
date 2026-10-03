/**
 * 52라운드 도트 세분화 시트 메모 (계약 art §11·§12, 결정 round-52 Q8·Q10·Q13). Phaser 의존 없음.
 * - 경로 계층: `sprites/<분류>/v3/` → `v2/` → 기존 (동작 단위로 섞어 쓸 수 있다)
 * - 보폭(stride): 걷기·달리기 재생 배속을 실제 이동 속도에 맞춘다 (이동 속도는 그대로)
 * - 손·칼 앵커: 몸 `handAnchors`, 무기 `gripAnchors`·`handAnchors`·`bladeLocal`·`playerFrameOffset` — 시트 도트 좌표 → 월드
 */
import { ASSETS, SPRITES } from '../core/Constants';
import { artScale, sheetJsonPath, type Facing, type SheetJson, type SheetRequest } from './spriteDefs';

/** 새 도트 하위 폴더 (앞이 우선) */
export const SHEET_TIERS: readonly string[] = [ASSETS.V3_DIR, ASSETS.V2_DIR];

/** `sprites/<분류>/<tier>/<파일>` (예: `sprites/player/v3/player_run.json`) */
export function sheetJsonPathTier(r: SheetRequest, tier: string): string {
  const base = sheetJsonPath(r);
  const i = base.lastIndexOf('/');
  return `${base.slice(0, i)}/${tier}${base.slice(i)}`;
}

/** 로드 후보 경로: v3 → v2 → 기존. 새 도트 폴더는 매니페스트에 있을 때만 쓴다(호출 쪽) */
export function sheetJsonCandidates(r: SheetRequest): string[] {
  return [...SHEET_TIERS.map((t) => sheetJsonPathTier(r, t)), sheetJsonPath(r)];
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
export function strideRate(def: Pick<SheetJson, 'stride' | 'pixelScale'>, speedWorld: number): number {
  const natural = strideSpeed(def);
  if (natural === null || !(speedWorld > 0)) return 1;
  return Math.min(SPRITES.STRIDE_RATE_MAX, Math.max(SPRITES.STRIDE_RATE_MIN, speedWorld / natural));
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
