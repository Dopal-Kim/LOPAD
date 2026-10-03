import { describe, expect, it } from 'vitest';
import { menuEscAction } from './escNav';

describe('menuEscAction (51라운드 §6 Esc 한 단계 뒤로)', () => {
  it('cancelKey 가 있으면 그 줄', () => {
    expect(menuEscAction({ id: 'cards', cancelKey: '0' })).toEqual({ kind: 'select', key: '0' });
    expect(menuEscAction({ id: 'labBranch', cancelKey: '0' })).toEqual({ kind: 'select', key: '0' });
  });
  it('메타 메뉴는 타이틀로', () => {
    expect(menuEscAction({ id: 'meta' })).toEqual({ kind: 'title' });
  });
  it('반드시 고르는 메뉴는 머문다', () => {
    for (const id of ['reward', 'passive', 'evolve', 'ending', 'shop'] as const)
      expect(menuEscAction({ id })).toEqual({ kind: 'stay' });
  });
});
