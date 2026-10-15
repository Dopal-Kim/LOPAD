import { describe, expect, it } from 'vitest';
import { offscreenEnemies } from './offscreen';

describe('P19 화면 밖 적', () => {
  it('화면 안·죽은 적은 빼고, 방향은 화면 가운데 기준 · 거리는 주인공 기준 · 같은 적은 같은 번호', () => {
    const view = { x: 0, y: 0, width: 100, height: 100 };
    const right = { x: 150, y: 50, active: true, threat: 'warn' as const };
    const mobs = [{ x: 50, y: 50, active: true, threat: null }, { x: -50, y: 0, active: false, threat: null }, right];
    const a = offscreenEnemies(view, { x: 10, y: 50 }, mobs);
    expect(a).toHaveLength(1);
    expect(a[0].angle).toBe(0);
    expect(a[0].threat).toBe('warn');
    expect(a[0].distTiles).toBe(8.8);
    expect(offscreenEnemies(view, { x: 0, y: 0 }, mobs)[0].id).toBe(a[0].id);
  });
});
