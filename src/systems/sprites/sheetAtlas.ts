/**
 * 57라운드 트림 아틀라스 시트 (결정 round-57 Q16 '빈 공간을 잘라낸 아틀라스'). Phaser 의존 없음.
 * 시트 JSON 의 `frames` 가 배열(TexturePacker JSON Array) 또는 객체(JSON Hash)면 아틀라스, 숫자면 기존 격자 시트다.
 *
 * 아틀라스 시트 JSON (기존 메타 필드는 그대로 — 의미도 그대로 '잘라내기 전 칸' 기준):
 * - `image`: 아틀라스 PNG (JSON 과 같은 폴더) · `frameWidth`·`frameHeight`: 잘라내기 전 칸 크기 (= 모든 프레임의 sourceSize)
 * - `columns` (선택): 방향 행 하나의 프레임 수 — 없으면 프레임 수 ÷ 행 수(`directions` 길이)
 * - `frames[]`: `{ filename, frame{x,y,w,h}, rotated:false, trimmed, spriteSourceSize{x,y,w,h}, sourceSize{w,h} }`
 *   filename = 격자 프레임 번호 문자열 ("0" … 행 × columns − 1, 행 우선). 모든 칸이 있어야 한다(빈 칸은 1×1 트림).
 * - 반복 타일 시트(`tile: true`)는 잘라내지 않는다 (TileSprite 는 trim 을 모른다 — 프레임은 칸 전체, trimmed false).
 * 피벗·앵커·프레임 번호는 칸 기준이라 바뀌지 않는다 — Phaser 가 trim 오프셋(spriteSourceSize)을 그릴 때 되돌린다.
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

export interface AtlasData {
  frames: AtlasFrame[];
}

/** 시트 JSON 이 트림 아틀라스인가 (`frames` 가 배열·객체) */
export function isAtlasSheet(raw: unknown): boolean {
  if (!raw || typeof raw !== 'object') return false;
  const f = (raw as { frames?: unknown }).frames;
  return Array.isArray(f) || (typeof f === 'object' && f !== null);
}

const isNum = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v);
const isRect = (v: unknown): v is AtlasRect =>
  !!v && typeof v === 'object' && ['x', 'y', 'w', 'h'].every((k) => isNum((v as Record<string, unknown>)[k]));

/**
 * 아틀라스 시트 JSON → 격자 메타(`frames` = 행당 프레임 수)를 채운 SheetJson + Phaser 아틀라스 데이터.
 * 형식이 틀리면 `{ error }` (로더는 그 시트를 건너뛴다 — 없는 시트와 같게 플레이스홀더)
 */
export function parseAtlasSheet(raw: unknown): { json: SheetJson; atlas: AtlasData } | { error: string } {
  if (!isAtlasSheet(raw)) return { error: 'frames 가 배열·객체가 아님' };
  const r = raw as Record<string, unknown> & { frames: unknown };
  const list: unknown[] = Array.isArray(r.frames)
    ? r.frames
    : Object.entries(r.frames as Record<string, unknown>).map(([filename, f]) => ({
        ...(f as object),
        filename,
      }));
  if (list.length === 0) return { error: 'frames 가 비었음' };
  const frames: AtlasFrame[] = [];
  for (const f of list) {
    const o = (f ?? {}) as Record<string, unknown>;
    const ss = o.sourceSize as { w?: unknown; h?: unknown } | undefined;
    if (typeof o.filename !== 'string' || !isRect(o.frame) || !ss || !isNum(ss.w) || !isNum(ss.h))
      return { error: 'frames[] 에 filename·frame·sourceSize 가 필요' };
    if (o.rotated === true) return { error: `프레임 ${o.filename}: rotated 는 지원하지 않음` };
    const sss = isRect(o.spriteSourceSize) ? o.spriteSourceSize : { x: 0, y: 0, w: o.frame.w, h: o.frame.h };
    frames.push({
      filename: o.filename,
      frame: o.frame,
      rotated: false,
      trimmed: o.trimmed === true,
      spriteSourceSize: sss,
      sourceSize: { w: ss.w, h: ss.h },
    });
  }
  const fw = isNum(r.frameWidth) ? r.frameWidth : frames[0].sourceSize.w;
  const fh = isNum(r.frameHeight) ? r.frameHeight : frames[0].sourceSize.h;
  const rows = Array.isArray(r.directions) && r.directions.length > 0 ? r.directions.length : 1;
  const columns = isNum(r.columns) && r.columns > 0 ? r.columns : frames.length / rows;
  if (!Number.isInteger(columns) || columns <= 0)
    return { error: `프레임 ${frames.length}개를 행 ${rows}개로 나눌 수 없음 (columns 필요)` };
  const total = rows * columns;
  const seen = new Set<number>();
  for (const f of frames) {
    const i = Number(f.filename);
    if (!Number.isInteger(i) || i < 0 || i >= total || String(i) !== f.filename)
      return { error: `filename "${f.filename}" 은 0..${total - 1} 의 프레임 번호여야 함` };
    if (f.sourceSize.w !== fw || f.sourceSize.h !== fh)
      return { error: `프레임 ${f.filename}: sourceSize 가 frameWidth×frameHeight(${fw}×${fh}) 와 다름` };
    seen.add(i);
  }
  if (seen.size !== total) return { error: `칸 ${total}개 중 ${seen.size}개만 있음 (빈 칸도 1×1 로 넣는다)` };
  // 반복 타일 시트(`tile: true` — 조준선·예고 선, TileSprite)는 칸 전체가 무늬라 잘라내면 무늬 간격이 깨진다
  if (r.tile === true && frames.some((f) => f.trimmed))
    return { error: 'tile: true 시트는 잘라내지 않는다 (trimmed false)' };
  const json = { ...r, frameWidth: fw, frameHeight: fh, frames: columns } as unknown as SheetJson;
  return { json, atlas: { frames } };
}
