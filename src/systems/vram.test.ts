import { describe, expect, it } from 'vitest';
import { measureVram, vramGroup } from './vram';

describe('VRAM 추정 (61라운드 P9)', () => {
  it('폭 × 높이 × 4, 같은 GL 텍스처는 한 번, 4096 초과 목록', () => {
    const gl = {};
    const img = {};
    const r = measureVram(
      [
        { key: 'sheet_player_idle', sources: [{ width: 1024, height: 512, gl, image: img }] },
        { key: 'alias', sources: [{ width: 1024, height: 512, gl, image: img }] },
        { key: 'tiles_stage1', sources: [{ width: 5000, height: 64 }] },
      ],
      1024 * 1024,
    );
    expect(r.uploads).toBe(2);
    expect(r.bytes).toBe(1024 * 512 * 4 + 5000 * 64 * 4);
    expect(r.over4096).toEqual([{ key: 'tiles_stage1', width: 5000, height: 64 }]);
    expect(r.overBudget).toBe(true);
    expect(r.top[0].key).toBe('sheet_player_idle');
    expect(r.dupImages).toEqual([]);
  });

  it('같은 그림이 다른 GL 텍스처로 두 번 올라가면 dupImages', () => {
    const img = {};
    const r = measureVram([
      { key: 'a', sources: [{ width: 256, height: 256, gl: {}, image: img }] },
      { key: 'b', sources: [{ width: 256, height: 256, gl: {}, image: img }] },
    ]);
    expect(r.dupImages).toEqual([{ keys: ['a', 'b'], mb: 0.25 }]);
  });

  it('분류', () => {
    expect(vramGroup('sheet_katana_combo1')).toBe('sheet:katana');
    expect(vramGroup('sheet_stage1_idle@f2')).toBe('variant');
    expect(vramGroup('border_outer')).toBe('border');
    expect(vramGroup('3f2b9c1a-1234-4abc-8def-001122334455')).toBe('dynamic');
  });
});
