import { describe, expect, it } from 'vitest';
import {
  DEFAULT_KEYS,
  assignKey,
  codeToKeyName,
  isDefaultBinds,
  keyLabel,
  moveKeysLabel,
  readKeyBinds,
} from './keyBindView';

describe('keyBindView (62 루프 2 P1-16 키 재설정)', () => {
  it('KeyboardEvent.code → Phaser 키 이름 (한글 입력기와 무관한 자판 자리)', () => {
    expect(codeToKeyName('KeyW')).toBe('W');
    expect(codeToKeyName('Digit3')).toBe('THREE');
    expect(codeToKeyName('Numpad0')).toBe('NUMPAD_ZERO');
    expect(codeToKeyName('Space')).toBe('SPACE');
    expect(codeToKeyName('ArrowLeft')).toBe('LEFT');
    expect(codeToKeyName('ShiftRight')).toBe('SHIFT');
    expect(codeToKeyName('F4')).toBe('F4');
    expect(codeToKeyName('MetaLeft')).toBeNull();
    expect(codeToKeyName('HangulMode')).toBeNull();
    expect(codeToKeyName('IntlRo')).toBeNull();
  });

  it('화면 이름', () => {
    expect(keyLabel('SPACE')).toBe('Space');
    expect(keyLabel('UP')).toBe('↑');
    expect(keyLabel('THREE')).toBe('3');
    expect(keyLabel('NUMPAD_ONE')).toBe('숫자판 1');
    expect(keyLabel('E')).toBe('E');
    expect(moveKeysLabel(DEFAULT_KEYS)).toBe('WASD');
    expect(moveKeysLabel({ ...DEFAULT_KEYS, up: 'UP', left: 'LEFT', down: 'DOWN', right: 'RIGHT' })).toBe('↑←↓→');
  });

  it('키 주기: 겹치면 맞바꾸고, 막힌 키·모르는 키는 실패', () => {
    const r = assignKey(DEFAULT_KEYS, 'dash', 'E');
    expect(r).toMatchObject({ ok: true, swapped: 'interact' });
    if (r.ok) {
      expect(r.binds.dash).toBe('E');
      expect(r.binds.interact).toBe('SPACE');
    }
    expect(assignKey(DEFAULT_KEYS, 'dash', 'ESC')).toMatchObject({ ok: false, reason: 'reserved', label: 'Esc' });
    expect(assignKey(DEFAULT_KEYS, 'potion', 'SHIFT')).toMatchObject({ ok: false, reason: 'reserved' });
    expect(assignKey(DEFAULT_KEYS, 'potion', null)).toMatchObject({ ok: false, reason: 'unknown' });
    const same = assignKey(DEFAULT_KEYS, 'up', 'W');
    expect(same.ok && same.binds).toBe(DEFAULT_KEYS);
  });

  it('스냅샷 값 읽기: 틀린 칸·막힌 키는 기본 키', () => {
    expect(readKeyBinds(null)).toEqual(DEFAULT_KEYS);
    expect(readKeyBinds({ up: 'UP', dash: 'TAB', potion: 3, interact: 'f' })).toEqual({ ...DEFAULT_KEYS, up: 'UP' });
    expect(isDefaultBinds(readKeyBinds({}))).toBe(true);
  });
});
