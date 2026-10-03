import { describe, expect, it } from 'vitest';
import { oncePerKeyEvent } from './keyEvents';

describe('53라운드 키 이벤트 재전달 막기', () => {
  it('같은 이벤트 객체는 한 번만, 다른 객체는 매번, 처리기끼리는 따로 기억', () => {
    const got: string[] = [];
    const a = oncePerKeyEvent((e: { key: string }) => got.push(`a${e.key}`));
    const b = oncePerKeyEvent((e: { key: string }) => got.push(`b${e.key}`));
    const e1 = { key: 'L' };
    const e2 = { key: 'L' };
    // Phaser 3.90 큐 재처리 순서: e1 → (e1 재전달) → e2
    a(e1);
    b(e1);
    a(e1);
    b(e1);
    a(e2);
    expect(got).toEqual(['aL', 'bL', 'aL']);
  });
});
