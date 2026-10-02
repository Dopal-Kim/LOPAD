import { describe, expect, it } from 'vitest';
import { keyToDir, nearest, pickNeighbor, type NavNode } from './warpNav';

const nodes: NavNode[] = [
  { id: 'a', x: 1.5, y: 1.5 },
  { id: 'b', x: 3.5, y: 1.5 },
  { id: 'c', x: 3.5, y: 3.5 },
  { id: 'd', x: 1.5, y: 4.5 },
];

describe('warpNav', () => {
  it('오른쪽으로 같은 줄의 가장 가까운 방을 고른다', () => {
    expect(pickNeighbor({ x: 1.5, y: 1.5 }, { dx: 1, dy: 0 }, nodes, 'a')).toBe('b');
  });
  it('아래로는 정면에 가까운 방을 고른다', () => {
    expect(pickNeighbor({ x: 1.5, y: 1.5 }, { dx: 0, dy: 1 }, nodes, 'a')).toBe('d');
  });
  it('그 방향에 방이 없으면 null', () => {
    expect(pickNeighbor({ x: 1.5, y: 1.5 }, { dx: -1, dy: 0 }, nodes, 'a')).toBeNull();
    expect(pickNeighbor({ x: 1.5, y: 1.5 }, { dx: 0, dy: -1 }, nodes, 'a')).toBeNull();
  });
  it('가장 가까운 방', () => {
    expect(nearest({ x: 3, y: 3 }, nodes)).toBe('c');
    expect(nearest({ x: 0, y: 0 }, [])).toBeNull();
  });
  it('WASD·방향키를 방향으로', () => {
    expect(keyToDir('w')).toEqual({ dx: 0, dy: -1 });
    expect(keyToDir('ArrowRight')).toEqual({ dx: 1, dy: 0 });
    expect(keyToDir('Enter')).toBeNull();
  });
});
