import { describe, expect, it } from 'vitest';
import { HAND_H, HAND_W, handOutline, memoryIconKey } from './memoryArt';

describe('기억 그림 자리 (62 루프 3 UI H · P1-N6)', () => {
  it('시스템 iconKey 가 로드돼 있으면 그것, 아니면 null', () => {
    const has = (k: string): boolean => k === 'ui_relics/keepsake_inkBrush';
    expect(memoryIconKey({ id: 'k', iconKey: 'ui_relics/keepsake_inkBrush' }, has)).toBe('ui_relics/keepsake_inkBrush');
    expect(memoryIconKey({ id: 'shop:ink', iconKey: 'ui_relics/memory_ink' }, has)).toBeNull();
    expect(memoryIconKey(null, has)).toBeNull();
  });
  it('빈 손바닥 윤곽은 칸 안이고 손가락 넷이 따로 보인다', () => {
    const o = handOutline();
    expect(o.length).toBeGreaterThan(60);
    for (const [x, y] of o) {
      expect(x).toBeGreaterThanOrEqual(0);
      expect(x).toBeLessThan(HAND_W);
      expect(y).toBeLessThan(HAND_H);
    }
    // 손가락 사이 틈(손바닥 위 y=6)은 비어 있다
    const row6 = new Set(o.filter(([, y]) => y === 6).map(([x]) => x));
    for (const gap of [8, 12, 16]) expect(row6.has(gap)).toBe(false);
  });
});
