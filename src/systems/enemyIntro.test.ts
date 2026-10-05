import { describe, expect, it } from 'vitest';
import { EnemyIntro } from './enemyIntro';

describe('61라운드 새 적 소개', () => {
  it('런마다 처음 보는 종류만 한 번', () => {
    const e = new EnemyIntro();
    expect(e.newcomers('run1', ['dummy', 'dummy', 'archer'])).toEqual(['dummy', 'archer']);
    expect(e.newcomers('run1', ['dummy', 'charger'])).toEqual(['charger']);
    expect(e.newcomers('run2', ['dummy'])).toEqual(['dummy']);
  });
});
