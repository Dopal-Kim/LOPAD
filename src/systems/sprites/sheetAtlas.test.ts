import { describe, expect, it } from 'vitest';
import fixture from './__fixtures__/trimAtlas.json';
import { isAtlasSheet, parseAtlasSheet } from './sheetAtlas';
import { frameIndices, sheetToWorldUnits } from './spriteDefs';

const clone = () => JSON.parse(JSON.stringify(fixture)) as Record<string, unknown> & { frames: unknown[] };

describe('57라운드 트림 아틀라스 시트 (시험 시트 2행 × 3열)', () => {
  it('frames 가 배열·객체면 아틀라스, 숫자면 기존 격자 시트', () => {
    expect(isAtlasSheet(fixture)).toBe(true);
    expect(isAtlasSheet({ ...fixture, frames: 3 })).toBe(false);
    const hash = clone();
    hash.frames = Object.fromEntries(
      (fixture.frames as { filename: string }[]).map(({ filename, ...f }) => [filename, f]),
    ) as unknown as unknown[];
    expect(isAtlasSheet(hash)).toBe(true);
    const r = parseAtlasSheet(hash);
    expect('json' in r && r.json.frames).toBe(3);
  });

  it('격자 메타가 칸 기준 그대로: frames = 행당 3, 프레임 번호·피벗·크기 유지', () => {
    const r = parseAtlasSheet(fixture);
    if (!('json' in r)) throw new Error(r.error);
    expect(r.json.frames).toBe(3);
    expect(r.json.frameWidth).toBe(32);
    expect(r.json.frameHeight).toBe(48);
    expect(r.json.pivot).toEqual({ x: 16, y: 44 });
    // 애니 키·프레임 인덱스 호환: up 행 = 3,4,5
    expect(frameIndices(r.json, 'down')).toEqual([0, 1, 2]);
    expect(frameIndices(r.json, 'up')).toEqual([3, 4, 5]);
    // 메모 길이 월드 변환도 칸 기준 (pixelScale 0.5)
    expect(sheetToWorldUnits(r.json).pivot).toEqual({ x: 16, y: 44 });
    // Phaser 아틀라스 데이터: 트림 오프셋 보존
    const f0 = r.atlas.frames.find((f) => f.filename === '0')!;
    expect(f0.trimmed).toBe(true);
    expect(f0.spriteSourceSize).toEqual({ x: 11, y: 24, w: 10, h: 20 });
    expect(f0.sourceSize).toEqual({ w: 32, h: 48 });
  });

  it('columns 가 있으면 그것을 쓴다', () => {
    const r = parseAtlasSheet({ ...clone(), columns: 3, directions: ['down', 'up'] });
    expect('json' in r && r.json.frames).toBe(3);
  });

  it('형식 오류: 빠진 칸 · 이름이 번호가 아님 · sourceSize 불일치 · 회전 · 나눌 수 없는 수', () => {
    const missing = clone();
    missing.frames = missing.frames.slice(0, 5);
    expect('error' in parseAtlasSheet(missing)).toBe(true);
    const named = clone();
    (named.frames[0] as { filename: string }).filename = 'idle_0';
    expect('error' in parseAtlasSheet(named)).toBe(true);
    const size = clone();
    (size.frames[2] as { sourceSize: { w: number } }).sourceSize.w = 30;
    expect('error' in parseAtlasSheet(size)).toBe(true);
    const rot = clone();
    (rot.frames[3] as { rotated: boolean }).rotated = true;
    expect('error' in parseAtlasSheet(rot)).toBe(true);
    expect('error' in parseAtlasSheet({ ...clone(), directions: ['down', 'up', 'left', 'right'] })).toBe(true);
    expect('error' in parseAtlasSheet({ ...clone(), tile: true })).toBe(true);
  });
});
