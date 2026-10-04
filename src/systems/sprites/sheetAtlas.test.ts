import { describe, expect, it } from 'vitest';
import fixture from './__fixtures__/trimAtlas.json';
import { isAtlasSheet, parseAtlasSheet, readSheetJson } from './sheetAtlas';
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
    const f0 = r.atlas.pages[0].frames.find((f) => f.filename === '0')!;
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

/** 아트 최종 형식 (atlas57-1): framesPerDirection + frames{} (JSON Hash) + atlas.grid + meta.size */
function atlas57(): Record<string, unknown> {
  const { frames, ...rest } = JSON.parse(JSON.stringify(fixture)) as { frames: ({ filename: string } & object)[] };
  return {
    ...rest,
    framesPerDirection: 3,
    atlas: {
      version: 'atlas57-1',
      grid: { columns: 3, rows: 2, frameWidth: 32, frameHeight: 48, frameCount: 6 },
      padding: 2,
      emptyFrames: [1],
      dedupedFrames: 2,
      pages: 1,
    },
    frames: Object.fromEntries(frames.map(({ filename, ...f }) => [filename, f])),
    meta: { image: 'trim_test.png', size: { w: 79, h: 48 } },
  };
}

describe('57라운드 Q38 아틀라스 최종 형식 (atlas57-1)', () => {
  it('framesPerDirection·atlas.grid.columns 로 격자 메타를 채운다', () => {
    const r = parseAtlasSheet(atlas57());
    if (!('json' in r)) throw new Error(r.error);
    expect(r.json.frames).toBe(3);
    expect(r.atlas.pages).toHaveLength(1);
    expect(r.atlas.pages[0].image).toBe('trim_test.png');
    expect(r.atlas.pages[0].frames.map((f) => f.filename).sort()).toEqual(['0', '1', '2', '3', '4', '5']);
    expect(frameIndices(r.json, 'up')).toEqual([3, 4, 5]);
  });

  it('atlas.grid.columns 가 columns·프레임 수 나눗셈보다 우선 (directions 가 없어도)', () => {
    const raw = atlas57();
    delete raw.directions;
    delete raw.framesPerDirection;
    raw.columns = 6;
    const r = parseAtlasSheet(raw);
    if (!('json' in r)) throw new Error(r.error);
    expect(r.json.frames).toBe(3);
  });

  it('여러 장(image null + textures[]): 장마다 프레임, 이미지 이름은 첫 장', () => {
    const raw = atlas57();
    const frames = raw.frames as Record<string, object>;
    const list = Object.entries(frames).map(([filename, f]) => ({ filename, ...f }));
    raw.image = null;
    delete raw.frames;
    delete raw.meta;
    raw.textures = [
      { image: 'trim_test_0.png', size: { w: 79, h: 48 }, frames: list.slice(0, 4) },
      { image: 'trim_test_1.png', size: { w: 79, h: 48 }, frames: list.slice(4) },
    ];
    expect(isAtlasSheet(raw)).toBe(true);
    const r = parseAtlasSheet(raw);
    if (!('json' in r)) throw new Error(r.error);
    expect(r.json.image).toBe('trim_test_0.png');
    expect(r.atlas.pages.map((p) => [p.image, p.frames.length])).toEqual([
      ['trim_test_0.png', 4],
      ['trim_test_1.png', 2],
    ]);
    // 두 장에 같은 칸이 있으면 오류
    (raw.textures as { frames: object[] }[])[1].frames.push(list[0]);
    expect('error' in parseAtlasSheet(raw)).toBe(true);
  });

  it('형식 오류: framesPerDirection ≠ 열 수 · directions 행 ≠ grid.rows · frame 이 이미지 밖', () => {
    expect('error' in parseAtlasSheet({ ...atlas57(), framesPerDirection: 2 })).toBe(true);
    expect('error' in parseAtlasSheet({ ...atlas57(), directions: ['down', 'up', 'left'] })).toBe(true);
    expect('error' in parseAtlasSheet({ ...atlas57(), meta: { size: { w: 40, h: 48 } } })).toBe(true);
  });

  it('readSheetJson: 격자 시트도 framesPerDirection ?? frames(숫자)', () => {
    const grid = {
      image: 'g.png',
      frameWidth: 32,
      frameHeight: 48,
      framesPerDirection: 4,
      directions: ['down'],
      fps: 8,
    };
    expect(readSheetJson(grid)?.json.frames).toBe(4);
    expect(readSheetJson(grid)?.atlas).toBeNull();
    expect(readSheetJson({ ...grid, framesPerDirection: undefined, frames: 5 })?.json.frames).toBe(5);
    expect(readSheetJson(atlas57())?.json.frames).toBe(3);
    const errors: string[] = [];
    expect(readSheetJson({ ...atlas57(), framesPerDirection: 2 }, (e) => errors.push(e))).toBeNull();
    expect(errors).toHaveLength(1);
  });
});
