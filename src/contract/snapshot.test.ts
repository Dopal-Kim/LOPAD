import { describe, expect, it } from 'vitest';
import { gameState } from '../core/GameState';
import { STAGES } from '../data';
import { generateFloor } from '../systems/mapgen';
import { buildSnapshot } from './snapshot';

describe('buildSnapshot', () => {
  it('상태를 복사본으로 담고 맵 그래프를 포함한다', () => {
    gameState.startRun('snap', 'katana');
    gameState.gold = 42;
    const layout = generateFloor('snap:0', STAGES.stage1.layout);
    const s = buildSnapshot({
      layout,
      visited: new Set(['start']),
      cleared: new Set(),
      bossName: null,
      paused: false,
      menu: null,
    });
    expect(s.gold).toBe(42);
    expect(s.weapon.name).toBe('사무라이 칼');
    expect(s.map.rooms.length).toBe(layout.rooms.length);
    expect(s.map.rooms.find((r) => r.id === 'start')?.visited).toBe(true);
    expect(s.boss).toBeNull();
    s.gold = 0; // 복사본 수정은 상태에 영향 없음
    expect(gameState.gold).toBe(42);
  });
});
