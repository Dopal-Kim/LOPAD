import { describe, expect, it } from 'vitest';
import { gameState } from '../../core/GameState';
import { PLAYER_DATA } from '../../data';
import type { SaveData, SaveSlot } from '../../systems/save';
import { labWeaponFor, runWeaponFor } from './runWeapon';

const slot = (weapon: string | null) =>
  ({ read: () => (weapon ? ({ weapon: { id: weapon } } as unknown as SaveData) : null) }) as unknown as SaveSlot;

describe('57라운드 A2 preload 런 무기 = create 의 prepareRun 무기', () => {
  it('새 런: 고른 무기 (모르는 무기·없음 = 시작 무기)', () => {
    expect(runWeaponFor({ mode: 'new', weapon: 'bow' }, false, slot(null))).toBe('bow');
    expect(runWeaponFor({ mode: 'new', weapon: 'nope' }, false, slot(null))).toBe(PLAYER_DATA.startWeapon);
    expect(runWeaponFor({ mode: 'new' }, false, slot('dagger'))).toBe(PLAYER_DATA.startWeapon);
  });
  it('같은 런의 노드·층: 지금 무기', () => {
    gameState.startRun('t', 'greatsword');
    for (const mode of ['node', 'next', 'floor'] as const)
      expect(runWeaponFor({ mode }, false, slot('bow'))).toBe('greatsword');
  });
  it('이어하기: 세이브 무기, 세이브가 없으면 시작 무기', () => {
    expect(runWeaponFor({}, false, slot('dagger'))).toBe('dagger');
    expect(runWeaponFor({}, false, slot(null))).toBe(PLAYER_DATA.startWeapon);
  });
  it('시험장: 고른 무기 → 지금 무기', () => {
    gameState.startRun('t', 'katana');
    expect(runWeaponFor({ labWeapon: 'bow' }, true, slot(null))).toBe('bow');
    expect(labWeaponFor({})).toBe('katana');
  });
});
