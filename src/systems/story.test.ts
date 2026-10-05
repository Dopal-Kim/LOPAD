import { describe, expect, it } from 'vitest';
import { deathLine, evolutionLine, fill } from './story';

describe('story text', () => {
  it('치환', () => {
    expect(fill('{a}-{b}-{c}', { a: 1, b: 'x' })).toBe('1-x-{c}');
  });
  it('진화 문장은 이름별, 없으면 공통', () => {
    // 61 G: 갈래·길 자막은 화면 이름(art §26 갈래 이름)으로
    expect(evolutionLine('선풍')).toBe('한가운데가 가장 조용했다. 칼이 돌고 있었으니까.');
    expect(evolutionLine('없는 진화')).toContain('없는 진화');
  });
  it('사망 문장', () => {
    expect(deathLine('도영', 3, 12)).toBe('다시 태어난다. 기록만 남는다. 도영, 3층, 12명.');
    expect(deathLine('', 1, 0)).toContain('―');
  });
});
