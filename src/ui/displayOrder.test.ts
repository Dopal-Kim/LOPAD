import { describe, expect, it } from 'vitest';
import { insertNextTo } from './displayOrder';

describe('insertNextTo', () => {
  it('맨 끝(가장 위)에 새로 만든 그림을 바탕 바로 위로 내린다 (MoveAbove 는 옮기지 않던 경우)', () => {
    const list = ['book', 'base', 'links', 'nodes', 'labels', 'img'];
    expect(insertNextTo(list, 'img', 'base', 'above')).toBe(true);
    expect(list).toEqual(['book', 'base', 'img', 'links', 'nodes', 'labels']);
  });
  it('아래 끼우기·앞에 있던 것도', () => {
    const list = ['a', 'frame', 'b', 'img'];
    insertNextTo(list, 'img', 'frame', 'below');
    expect(list).toEqual(['a', 'img', 'frame', 'b']);
    const l2 = ['img', 'a', 'base', 'b'];
    insertNextTo(l2, 'img', 'base', 'above');
    expect(l2).toEqual(['a', 'base', 'img', 'b']);
  });
  it('없는 것·같은 것은 그대로', () => {
    const list = ['a', 'b'];
    expect(insertNextTo(list, 'x', 'a', 'above')).toBe(false);
    expect(insertNextTo(list, 'a', 'a', 'above')).toBe(false);
    expect(list).toEqual(['a', 'b']);
  });
});
