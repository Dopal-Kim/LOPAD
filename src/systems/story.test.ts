import { describe, expect, it } from 'vitest';
import { deathLine, evolutionLine, fill } from './story';

describe('story text', () => {
  it('치환', () => {
    expect(fill('{a}-{b}-{c}', { a: 1, b: 'x' })).toBe('1-x-{c}');
  });
  it('진화 문장은 이름별, 없으면 공통', () => {
    expect(evolutionLine('거합 (居合)')).toBe('칼집이 필요 없어졌다.');
    expect(evolutionLine('없는 진화')).toContain('없는 진화');
  });
  it('사망 문장', () => {
    expect(deathLine('도영', 3, 12)).toBe('다시 태어난다. 기록만 남는다. 도영, 3층, 12명.');
    expect(deathLine('', 1, 0)).toContain('―');
  });
});
