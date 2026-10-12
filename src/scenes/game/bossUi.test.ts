import { describe, expect, it } from 'vitest';
import { phaseRevealed, uiBossBreak } from './bossUi';

describe('61라운드 계약 §17 보스 파훼 UI 이벤트', () => {
  it('시스템 파훼 이름 → 계약 이름 (reel = stumble) · 짧은 이름', () => {
    expect(uiBossBreak('cup')).toEqual({ kind: 'cup', label: '잔 깨기' });
    expect(uiBossBreak('reel')?.kind).toBe('stumble');
    expect(uiBossBreak('cask')?.kind).toBe('cask');
    expect(uiBossBreak('finisher')?.label).toBe('결정타');
    expect(uiBossBreak('nope')).toBeNull();
  });
});

describe('62 루프 2 시스템 D (P1-14) 국면 이름 공개', () => {
  it('지금 국면까지만 공개 — 1국면이면 [참, 거짓, 거짓], 3국면이면 모두', () => {
    expect(phaseRevealed(3, 1)).toEqual([true, false, false]);
    expect(phaseRevealed(3, 2)).toEqual([true, true, false]);
    expect(phaseRevealed(3, 3)).toEqual([true, true, true]);
    // 아직 국면 0(등장 전)이어도 첫 국면은 공개
    expect(phaseRevealed(3, 0)).toEqual([true, false, false]);
  });
});
