import { describe, expect, it } from 'vitest';
import { uiBossBreak } from './bossUi';

describe('61라운드 계약 §17 보스 파훼 UI 이벤트', () => {
  it('시스템 파훼 이름 → 계약 이름 (reel = stumble) · 짧은 이름', () => {
    expect(uiBossBreak('cup')).toEqual({ kind: 'cup', label: '잔 깨기' });
    expect(uiBossBreak('reel')?.kind).toBe('stumble');
    expect(uiBossBreak('cask')?.kind).toBe('cask');
    expect(uiBossBreak('finisher')?.label).toBe('결정타');
    expect(uiBossBreak('nope')).toBeNull();
  });
});
