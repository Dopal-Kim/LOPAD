/**
 * 57라운드 트림 아틀라스 시트 (결정 round-57 Q16·Q38 '빈 공간을 잘라낸 아틀라스', 아트 형식 `atlas57-1`). Phaser 의존 없음.
 * 시트 JSON 의 `frames` 가 객체(TexturePacker JSON Hash)·배열(JSON Array)이거나 `textures[]`(멀티 아틀라스)가 있으면 아틀라스,
 * `frames` 가 숫자면 기존 격자 시트다.
 *
 * 아틀라스 시트 JSON (기존 메타 필드는 그대로 — 의미도 그대로 '잘라내기 전 칸' 기준):
 * - `framesPerDirection`: 방향 행 하나의 프레임 수 (예전 정수 `frames` 가 이 이름으로 옮겨졌다 — 옛 시트는 숫자 `frames`)
 * - `frames{}`: 키 = 격자 프레임 번호 문자열 `String(row * columns + column)`, 값 = `{ frame{x,y,w,h}, rotated:false, trimmed,
 *   spriteSourceSize{x,y,w,h}, sourceSize{w,h} }`. 모든 칸이 있어야 한다 (빈 칸은 공용 1×1 칸, 같은 그림은 같은 frame 좌표 공유)
 * - `atlas{ version:"atlas57-1", grid{columns, rows, frameWidth, frameHeight, frameCount}, padding, noTrim?, emptyFrames,
 *   dedupedFrames, pages }` · `meta.size{w,h}` (아틀라스 이미지 크기)
 * - 4096 을 넘으면 여러 장: `image: null` + `textures[]{ image, size, frames[]{filename, …} }` (Phaser multiatlas 형식)
 * - 반복 타일(`tile: true`)·리본 시트는 잘라내지 않는다 (trimmed false, 칸 전체).
 * 피벗·앵커·프레임 번호는 칸 기준이라 바뀌지 않는다 — Phaser 가 trim 오프셋(spriteSourceSize)을 그릴 때 되돌린다.
 * 열 수(프레임 번호의 행 간격)는 `atlas.grid.columns` → `columns` → 방향당 프레임 수 순서로 읽는다.
 */
import type { SheetJson } from './sheetJson';

export interface AtlasRect {
  x: number;
  y: number;
  w: number;
  h: number;
}

/** Phaser `textures.addAtlasJSONArray` 가 읽는 프레임 한 칸 */
export interface AtlasFrame {
  filename: string;
  frame: AtlasRect;
  rotated: boolean;
  trimmed: boolean;
  spriteSourceSize: AtlasRect;
  sourceSize: { w: number; h: number };
}

/** 아틀라스 이미지 한 장과 그 장에 든 프레임 */
export interface AtlasPage {
  image: string;
  frames: AtlasFrame[];
}

export interface AtlasData {
  /** 한 장이면 길이 1 (`load.atlas`), 여러 장이면 `load.multiatlas` */
  pages: AtlasPage[];
}

const isNum = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v);
const isObj = (v: unknown): v is Record<string, unknown> => !!v && typeof v === 'object' && !Array.isArray(v);
const isRect = (v: unknown): v is AtlasRect => isObj(v) && ['x', 'y', 'w', 'h'].every((k) => isNum(v[k]));
const posInt = (v: unknown): number | null => (isNum(v) && Number.isInteger(v) && v > 0 ? v : null);

/** 시트 JSON 이 트림 아틀라스인가 (`frames` 가 배열·객체, 또는 멀티 아틀라스 `textures[]`) */
export function isAtlasSheet(raw: unknown): boolean {
  if (!isObj(raw)) return false;
  const f = raw.frames;
  return Array.isArray(f) || isObj(f) || Array.isArray(raw.textures);
}

/** 방향당 프레임 수: `framesPerDirection` (57라운드 아틀라스) → 숫자 `frames` (옛 격자 시트) → null */
export function framesPerDirectionOf(raw: Record<string, unknown>): number | null {
  return posInt(raw.framesPerDirection) ?? posInt(raw.frames);
}

/** frames 배열·객체 → 이름 붙은 프레임 목록 */
function frameList(frames: unknown): unknown[] {
  if (Array.isArray(frames)) return frames;
  if (isObj(frames)) return Object.entries(frames).map(([filename, f]) => ({ ...(isObj(f) ? f : {}), filename }));
  return [];
}

function readFrame(f: unknown): AtlasFrame | string {
  const o = isObj(f) ? f : {};
  const ss = o.sourceSize as { w?: unknown; h?: unknown } | undefined;
  if (typeof o.filename !== 'string' || !isRect(o.frame) || !ss || !isNum(ss.w) || !isNum(ss.h))
    return 'frames 에 frame·sourceSize 가 필요';
  if (o.rotated === true) return `프레임 ${o.filename}: rotated 는 지원하지 않음`;
  const sss = isRect(o.spriteSourceSize) ? o.spriteSourceSize : { x: 0, y: 0, w: o.frame.w, h: o.frame.h };
  return {
    filename: o.filename,
    frame: o.frame,
    rotated: false,
    trimmed: o.trimmed === true,
    spriteSourceSize: sss,
    sourceSize: { w: ss.w, h: ss.h },
  };
}

/** 이미지 크기를 알면 frame 이 그 안에 있는지 */
function outOfPage(f: AtlasFrame, size: unknown): boolean {
  if (!isObj(size) || !isNum(size.w) || !isNum(size.h)) return false;
  return f.frame.x < 0 || f.frame.y < 0 || f.frame.x + f.frame.w > size.w || f.frame.y + f.frame.h > size.h;
}

/** 장 목록 (한 장: 최상위 image·frames·meta.size, 여러 장: textures[]) */
function readPages(r: Record<string, unknown>): AtlasPage[] | string {
  const raws: { image: unknown; frames: unknown; size: unknown }[] = Array.isArray(r.textures)
    ? (r.textures as unknown[]).map((t) => {
        const o = isObj(t) ? t : {};
        return { image: o.image, frames: o.frames, size: o.size };
      })
    : [{ image: r.image, frames: r.frames, size: isObj(r.meta) ? r.meta.size : undefined }];
  if (raws.length === 0) return 'textures 가 비었음';
  const pages: AtlasPage[] = [];
  for (const p of raws) {
    if (typeof p.image !== 'string' || p.image === '') return '아틀라스 이미지 이름(image)이 없음';
    const frames: AtlasFrame[] = [];
    for (const f of frameList(p.frames)) {
      const read = readFrame(f);
      if (typeof read === 'string') return read;
      if (outOfPage(read, p.size)) return `프레임 ${read.filename}: frame 이 이미지(${p.image}) 밖`;
      frames.push(read);
    }
    pages.push({ image: p.image, frames });
  }
  return pages;
}

/**
 * 아틀라스 시트 JSON → 격자 메타(`frames` = 방향당 프레임 수)를 채운 SheetJson + Phaser 아틀라스 데이터.
 * 형식이 틀리면 `{ error }` (로더는 그 시트를 건너뛴다 — 없는 시트와 같게 플레이스홀더)
 */
export function parseAtlasSheet(raw: unknown): { json: SheetJson; atlas: AtlasData } | { error: string } {
  if (!isAtlasSheet(raw)) return { error: 'frames 가 배열·객체가 아니고 textures 도 없음' };
  const r = raw as Record<string, unknown>;
  const pages = readPages(r);
  if (typeof pages === 'string') return { error: pages };
  const frames = pages.flatMap((p) => p.frames);
  if (frames.length === 0) return { error: 'frames 가 비었음' };
  const grid = isObj(r.atlas) && isObj(r.atlas.grid) ? r.atlas.grid : {};
  const fw = posInt(grid.frameWidth) ?? posInt(r.frameWidth) ?? frames[0].sourceSize.w;
  const fh = posInt(grid.frameHeight) ?? posInt(r.frameHeight) ?? frames[0].sourceSize.h;
  const dirRows = Array.isArray(r.directions) && r.directions.length > 0 ? r.directions.length : null;
  const fpd = framesPerDirectionOf(r);
  const rows = posInt(grid.rows) ?? dirRows ?? 1;
  const columns = posInt(grid.columns) ?? posInt(r.columns) ?? fpd ?? frames.length / rows;
  if (!Number.isInteger(columns) || columns <= 0)
    return { error: `프레임 ${frames.length}개를 행 ${rows}개로 나눌 수 없음 (atlas.grid.columns 필요)` };
  // 시스템 프레임 번호 계산(row × 방향당 프레임 수 + 열)은 열 수 = 방향당 프레임 수를 전제한다
  const perDir = fpd ?? columns;
  if (perDir !== columns)
    return { error: `framesPerDirection(${perDir}) 과 열 수(${columns})가 다름 — 지원하지 않는 배치` };
  if (dirRows !== null && dirRows !== rows) return { error: `directions ${dirRows}행 ≠ atlas.grid.rows ${rows}` };
  const total = rows * columns;
  const seen = new Set<number>();
  for (const f of frames) {
    const i = Number(f.filename);
    if (!Number.isInteger(i) || i < 0 || i >= total || String(i) !== f.filename)
      return { error: `프레임 이름 "${f.filename}" 은 0..${total - 1} 의 프레임 번호여야 함` };
    if (seen.has(i)) return { error: `프레임 ${f.filename} 이 두 번 있음` };
    if (f.sourceSize.w !== fw || f.sourceSize.h !== fh)
      return { error: `프레임 ${f.filename}: sourceSize 가 frameWidth×frameHeight(${fw}×${fh}) 와 다름` };
    seen.add(i);
  }
  if (seen.size !== total) return { error: `칸 ${total}개 중 ${seen.size}개만 있음 (빈 칸도 1×1 로 넣는다)` };
  // 반복 타일 시트(`tile: true` — 조준선·예고 선, TileSprite)는 칸 전체가 무늬라 잘라내면 무늬 간격이 깨진다
  if (r.tile === true && frames.some((f) => f.trimmed))
    return { error: 'tile: true 시트는 잘라내지 않는다 (trimmed false)' };
  // 내부 SheetJson 은 예전 격자 메타 그대로: frames = 방향당 프레임 수, image = 첫 장 (URL 기준 폴더용)
  const json = { ...r, image: pages[0].image, frameWidth: fw, frameHeight: fh, frames: perDir } as unknown as SheetJson;
  return { json, atlas: { pages } };
}

/**
 * 시트 JSON → 격자 메타 SheetJson (+ 트림 아틀라스면 Phaser 아틀라스 데이터). 형식이 틀리면 null (`onError` 로 이유).
 * 격자 시트도 `framesPerDirection` 을 쓸 수 있다 (`framesPerDirection ?? frames`)
 */
export function readSheetJson(
  raw: unknown,
  onError: (msg: string) => void = () => {},
): { json: SheetJson; atlas: AtlasData | null } | null {
  if (!isObj(raw)) return null;
  let json: SheetJson;
  let atlas: AtlasData | null = null;
  if (isAtlasSheet(raw)) {
    const r = parseAtlasSheet(raw);
    if ('error' in r) {
      onError(r.error);
      return null;
    }
    json = r.json;
    atlas = r.atlas;
  } else {
    const perDir = framesPerDirectionOf(raw);
    json = (perDir !== null && raw.frames !== perDir ? { ...raw, frames: perDir } : raw) as unknown as SheetJson;
  }
  if (!json.image || !(json.frameWidth > 0) || !(json.frameHeight > 0) || !(json.frames > 0)) return null;
  return { json, atlas };
}
