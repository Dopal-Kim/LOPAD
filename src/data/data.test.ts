import { describe, expect, it } from 'vitest';
import { BOSSES, ENEMIES, PLAYER_DATA, STAGES, validateEnemies } from './index';
import type { EnemyTable } from './types';

describe('data/*.json', () => {
  it('플레이어·적·보스·스테이지 데이터가 검증을 통과한다', () => {
    expect(PLAYER_DATA.stats.hp).toBeGreaterThan(0);
    expect(Object.keys(ENEMIES)).toEqual(expect.arrayContaining(['dummy', 'archer', 'charger']));
    expect(BOSSES.stage1.phases[0].hpFraction).toBe(1);
    expect(STAGES.stage1.boss).toBe('stage1');
  });

  it('잘못된 행동 키는 거부한다', () => {
    const bad = { x: { ...ENEMIES.dummy, behavior: 'fly' } } as unknown as EnemyTable;
    expect(() => validateEnemies(bad)).toThrow(/behavior/);
  });
});
