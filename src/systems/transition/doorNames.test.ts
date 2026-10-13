import { describe, expect, it } from 'vitest';
import { resolveDoorName, smallDoorName } from './doorNames';

describe('62 I 입구 그림 이름 — 위험 노드 · 카드판 (art §32-1·2)', () => {
  const have = new Set(['door_outer_battle', 'door_outer_elite', 'door_outer_elite_small', 'door_brewery_battle']);
  const exists = (n: string) => have.has(n);

  it('위험이 있으면 door_<지역>_<위험> 먼저, 없으면 기존 순서', () => {
    expect(resolveDoorName('outer', 'battle', null, exists, 'elite')).toBe('door_outer_elite');
    expect(resolveDoorName('outer', 'battle', null, exists, 'curse')).toBe('door_outer_battle');
    expect(resolveDoorName('outer', 'battle', null, exists)).toBe('door_outer_battle');
    expect(resolveDoorName('brewery', 'battle', null, exists, 'elite')).toBe('door_brewery_battle');
  });

  it('카드판 _small 이 있으면 그것, 없으면 원본', () => {
    expect(smallDoorName('door_outer_elite', exists)).toBe('door_outer_elite_small');
    expect(smallDoorName('door_outer_battle', exists)).toBe('door_outer_battle');
    expect(smallDoorName(null, exists)).toBeNull();
  });
});
