import { describe, expect, it } from 'vitest';
import { isDestroyedSprite, resetPooledSprite, type ReleasableSprite } from './fxRelease';

/** Phaser Sprite 흉내: destroy() 하면 scene·anims 가 undefined (Sprite.preDestroy 와 같음) */
function fakeSprite() {
  const calls: string[] = [];
  const s = {
    scene: {} as unknown,
    anims: { chain: () => calls.push('chain'), stop: () => calls.push('stop') } as ReleasableSprite['anims'],
    off: () => calls.push('off'),
    destroy(this: { scene?: unknown; anims?: unknown }) {
      this.scene = undefined;
      this.anims = undefined;
    },
  } as unknown as ReleasableSprite & { destroy(): void };
  for (const k of ['setActive', 'setVisible', 'setAlpha', 'setRotation', 'setScale', 'setFlipY', 'clearTint'] as const)
    (s as unknown as Record<string, () => unknown>)[k] = () => {
      calls.push(k);
      return s;
    };
  return { s, calls };
}

describe('61라운드 P0: 씬 종료 중 fx 반납 (저주 표시 루프 → TypeError chain)', () => {
  it('살아 있는 스프라이트는 체인 비우기·정지·비활성', () => {
    const { s, calls } = fakeSprite();
    expect(resetPooledSprite(s, 'animationcomplete')).toBe(true);
    expect(calls.slice(0, 3)).toEqual(['off', 'chain', 'stop']);
    expect(calls).toContain('setActive');
  });

  it('재현: DisplayList 가 먼저 파괴한 스프라이트를 반납해도 예외 없이 건너뛴다', () => {
    const { s, calls } = fakeSprite();
    (s as unknown as { destroy(): void }).destroy();
    expect(isDestroyedSprite(s)).toBe(true);
    expect(() => resetPooledSprite(s, 'animationcomplete')).not.toThrow();
    expect(resetPooledSprite(s, 'animationcomplete')).toBe(false);
    expect(calls).toEqual([]);
  });
});
