import { describe, expect, it } from 'vitest';
import {
  SETTING_ROWS,
  changeSetting,
  moveCursor,
  normalizeSettings,
  percentText,
  sameSettings,
  setSlider,
  sliderCells,
  sliderFromRatio,
  stepSlider,
  toggleSetting,
} from './settingsView';

/** 계약 `UI_DEFAULT_SETTINGS` 와 같은 값 (계약 코드는 Phaser 를 불러 테스트에서 직접 쓰지 않는다) */
const DEFAULT_SETTINGS = { shake: 1, flash: true, tilt: true, damageNumbers: true, master: 1, bgm: 1, sfx: 1 };

describe('settingsView', () => {
  it('막대: 10% 칸 단위로 움직이고 끝에서 멈춘다', () => {
    expect(stepSlider(0.5, 1)).toBe(0.6);
    expect(stepSlider(0.5, -1)).toBe(0.4);
    expect(stepSlider(1, 1)).toBe(1);
    expect(stepSlider(0, -1)).toBe(0);
    // 칸 사이 값은 가까운 칸으로 맞춘 뒤
    expect(stepSlider(0.73, 1)).toBe(0.8);
    expect(stepSlider(0.1 + 0.2, 1)).toBe(0.4);
  });

  it('마우스 비율 → 칸 값, 켜진 칸 수·퍼센트', () => {
    expect(sliderFromRatio(0.04)).toBe(0);
    expect(sliderFromRatio(0.06)).toBe(0.1);
    expect(sliderFromRatio(1.4)).toBe(1);
    expect(sliderFromRatio(Number.NaN)).toBe(0);
    expect(sliderCells(0.7)).toBe(7);
    expect(percentText(0.7)).toBe('70%');
    expect(percentText(2)).toBe('100%');
  });

  it('켜고 끄기: ← 켬 · → 끔, Enter 뒤집기', () => {
    const off = changeSetting(DEFAULT_SETTINGS, 'flash', 1);
    expect(off.flash).toBe(false);
    expect(changeSetting(off, 'flash', 1)).toBe(off);
    expect(changeSetting(off, 'flash', -1).flash).toBe(true);
    expect(toggleSetting(off, 'flash').flash).toBe(true);
  });

  it('바뀐 것이 없으면 같은 객체 (명령을 다시 보내지 않게)', () => {
    const s = { ...DEFAULT_SETTINGS };
    expect(changeSetting(s, 'master', 1)).toBe(s);
    expect(setSlider(s, 'bgm', 0.98)).toBe(s);
    const t = setSlider(s, 'bgm', 0.42);
    expect(t.bgm).toBe(0.4);
    expect(sameSettings(t, s)).toBe(false);
    expect(sameSettings({ ...s }, s)).toBe(true);
  });

  it('스냅샷 값 정리: 객체가 아니면 null, 빠진 칸은 기본값, 범위 밖은 자름', () => {
    expect(normalizeSettings(undefined, DEFAULT_SETTINGS)).toBeNull();
    expect(normalizeSettings('x', DEFAULT_SETTINGS)).toBeNull();
    const n = normalizeSettings({ shake: 1.5, flash: 'no', tilt: false, master: -1, bgm: 0.3 }, DEFAULT_SETTINGS);
    expect(n).toEqual({ ...DEFAULT_SETTINGS, shake: 1, tilt: false, master: 0, bgm: 0.3 });
  });

  it('줄 순서: 화면 4 → 소리 3 → 되돌리기·덮기, 커서는 돌아간다', () => {
    expect(SETTING_ROWS.map((r) => r.id)).toEqual([
      'shake',
      'flash',
      'tilt',
      'damageNumbers',
      'master',
      'bgm',
      'sfx',
      'reset',
      'close',
    ]);
    expect(moveCursor(0, -1)).toBe(SETTING_ROWS.length - 1);
    expect(moveCursor(SETTING_ROWS.length - 1, 1)).toBe(0);
  });
});
