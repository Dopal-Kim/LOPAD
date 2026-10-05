import { describe, expect, it } from 'vitest';
import { placeLabels } from './routeLabels';

const area = { x: 0, y: 0, w: 400, h: 300 };

describe('routeLabels (61라운드 지도 이름표 겹침)', () => {
  it('비어 있으면 오른쪽', () => {
    const p = placeLabels([{ id: 'a', x: 100, y: 100, w: 60, h: 16, priority: 0 }], [], area, 16, 6);
    expect(p.get('a')).toEqual({ x: 122, y: 92, side: 'right' });
  });

  it('오른쪽에 다른 아이콘이 있으면 비킨다', () => {
    const icon = { x: 130, y: 84, w: 32, h: 32 };
    const p = placeLabels([{ id: 'a', x: 100, y: 100, w: 60, h: 16, priority: 0 }], [icon], area, 16, 6);
    expect(p.get('a')?.side).not.toBe('right');
  });

  it('지도 오른쪽 끝이면 왼쪽', () => {
    const p = placeLabels([{ id: 'a', x: 380, y: 100, w: 60, h: 16, priority: 0 }], [], area, 16, 6);
    expect(p.get('a')?.side).toBe('left');
  });

  it('먼저 놓은 이름표와 겹치지 않는다 (우선순위 순)', () => {
    const items = [
      { id: 'late', x: 100, y: 108, w: 60, h: 16, priority: 2 },
      { id: 'first', x: 100, y: 100, w: 60, h: 16, priority: 0 },
    ];
    const p = placeLabels(items, [], area, 16, 6);
    expect(p.get('first')?.side).toBe('right');
    expect(p.get('late')?.side).not.toBe('right');
  });
});
