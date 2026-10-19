import { afterEach, describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { DEFAULT_FEEL, feelSettings, setFeel } from './feel';
import { emptyMeta, type MetaData } from './meta';
import {
  DEFAULT_SETTINGS,
  SettingsService,
  feelPatchOf,
  keyLabel,
  sanitizeKeys,
  sanitizeSettings,
  type VolumeSettings,
} from './settings';
import { KEYBIND, SETTINGS } from '../core/constants/settings';

class FakeMeta {
  data: MetaData = emptyMeta();
  writes = 0;
  read(): MetaData {
    return JSON.parse(JSON.stringify(this.data)) as MetaData;
  }
  write(d: MetaData): void {
    this.data = JSON.parse(JSON.stringify(d)) as MetaData;
    this.writes += 1;
  }
}

afterEach(() => {
  setFeel(DEFAULT_FEEL);
});

describe('설정 (61라운드 계약 §15)', () => {
  it('기본값은 계약 §15 (contract/ui UI_DEFAULT_SETTINGS — Phaser 를 불러 테스트에서는 값으로 비교)', () => {
    expect({ ...DEFAULT_SETTINGS }).toEqual({
      shake: 1,
      flash: true,
      tilt: true,
      damageNumbers: true,
      master: 1,
      bgm: 1,
      sfx: 1,
      keys: { up: 'W', down: 'S', left: 'A', right: 'D', dash: 'SPACE', interact: 'E', potion: 'Q' },
      hitstop: true,
      textScale: 1,
      gore: 2,
    });
  });

  it('P21 고어 기본값은 계약 UI_DEFAULT_SETTINGS.gore 와 같고, 0·1·2 밖의 값은 버린다', () => {
    // contract/ui 는 Phaser 를 불러 테스트에서 직접 import 하지 않는다 — 원문에서 기본값 블록을 읽어 비교
    const src = readFileSync(resolve(__dirname, '../contract/ui.ts'), 'utf8');
    const block = src.slice(src.indexOf('export const UI_DEFAULT_SETTINGS'));
    const m = /\bgore: (\d)/.exec(block.slice(0, block.indexOf('});')));
    expect(Number(m?.[1])).toBe(DEFAULT_SETTINGS.gore);
    expect(sanitizeSettings({ gore: 1 }).gore).toBe(1);
    expect(sanitizeSettings({ gore: 0 }).gore).toBe(0);
    expect(sanitizeSettings({ gore: 3 }).gore).toBe(2);
    expect(sanitizeSettings({ gore: '1' }).gore).toBe(2);
  });

  it('다듬기: 숫자는 0~1 로 자르고 형식이 틀린 칸은 기본값', () => {
    const s = sanitizeSettings({ shake: 3, flash: 'no', tilt: false, master: -1, bgm: Number.NaN, sfx: 0.25 });
    expect(s).toEqual({
      ...DEFAULT_SETTINGS,
      shake: 1,
      flash: true,
      tilt: false,
      damageNumbers: true,
      master: 0,
      bgm: 1,
      sfx: 0.25,
    });
    expect(sanitizeSettings(null)).toEqual({ ...DEFAULT_SETTINGS });
  });

  it('감각 배율: 기울기 끄기 → tilt 0, 피해 숫자 → numbers', () => {
    expect(feelPatchOf({ ...DEFAULT_SETTINGS, shake: 0.5, tilt: false, flash: false, damageNumbers: false })).toEqual({
      shake: 0.5,
      flash: false,
      tilt: 0,
      numbers: false,
      hitstop: 1,
    });
    // 62 D (P1-16): 히트스톱 끄기 → 감각 배율 0
    expect(feelPatchOf({ ...DEFAULT_SETTINGS, hitstop: false }).hitstop).toBe(0);
  });

  it('부팅 load: 메타 저장값을 읽어 감각·음량에 바로 적용', () => {
    const meta = new FakeMeta();
    meta.data.settings = {
      shake: 0,
      flash: false,
      tilt: false,
      damageNumbers: false,
      master: 0.5,
      bgm: 0.2,
      sfx: 0.8,
      hitstop: false,
    };
    const vols: VolumeSettings[] = [];
    const svc = new SettingsService(meta);
    const cur = svc.load((v) => vols.push(v));
    expect(cur.master).toBe(0.5);
    expect(feelSettings.shake).toBe(0);
    expect(feelSettings.flash).toBe(false);
    expect(feelSettings.tilt).toBe(0);
    expect(feelSettings.numbers).toBe(false);
    expect(feelSettings.hitstop).toBe(0);
    expect(vols).toEqual([{ master: 0.5, bgm: 0.2, sfx: 0.8 }]);
    expect(meta.writes).toBe(0);
  });

  it('set: 일부 칸만 와도 나머지 유지 · 즉시 적용 · 메타의 다른 칸은 지우지 않고 settings 만 저장', () => {
    const meta = new FakeMeta();
    meta.data.souls = 42;
    const vols: VolumeSettings[] = [];
    const svc = new SettingsService(meta);
    svc.load((v) => vols.push(v));
    const next = svc.set({ shake: 0.3, sfx: 0 });
    expect(next).toEqual({ ...DEFAULT_SETTINGS, shake: 0.3, sfx: 0 });
    expect(feelSettings.shake).toBe(0.3);
    expect(vols[vols.length - 1]).toEqual({ master: 1, bgm: 1, sfx: 0 });
    expect(meta.data.souls).toBe(42);
    expect(meta.data.settings).toEqual(next);
    // 다시 부팅하면 저장값
    const again = new SettingsService(meta).load();
    expect(again).toEqual(next);
  });

  it('current 는 사본 (밖에서 바꿔도 내부 값 그대로)', () => {
    const svc = new SettingsService(new FakeMeta());
    svc.load();
    const c = svc.current();
    c.shake = 0;
    expect(svc.current().shake).toBe(1);
  });

  describe('62 루프 2 시스템 D (P1-16) 키 재설정 · 글자 크기', () => {
    it('옛 저장값(키 없음)은 기본 키 · 히트스톱 켜짐 · 글자 1', () => {
      const s = sanitizeSettings({ shake: 0.5 });
      expect(s.keys).toEqual(SETTINGS.DEFAULT.keys);
      expect(s.hitstop).toBe(true);
      expect(s.textScale).toBe(1);
    });

    it('바꿀 수 있는 키만 받고 소문자는 대문자로, 고정 키(Esc·M·Tab·R·C·L·Shift)는 앞 값', () => {
      const k = sanitizeKeys({
        dash: 'shift',
        interact: 'f',
        potion: 'ESC',
        up: 'UP',
        down: 'M',
        left: 'TAB',
        right: 'R',
      });
      expect(k).toEqual({ up: 'UP', down: 'S', left: 'A', right: 'D', dash: 'SPACE', interact: 'F', potion: 'Q' });
      for (const fixed of ['ESC', 'M', 'TAB', 'R', 'C', 'L', 'SHIFT', 'F11', 'ENTER'])
        expect(KEYBIND.BINDABLE.includes(fixed)).toBe(false);
    });

    it('겹치는 키: 앞 동작이 먼저 갖고 뒤 동작은 base 값 · 결과는 늘 서로 다른 7키', () => {
      const k = sanitizeKeys({ up: 'E', interact: 'E' });
      expect(k.up).toBe('E');
      // interact 가 E 를 원했지만 up 이 가져갔고 base(E)도 겹침 → 기본(E)도 겹침 → 남은 첫 키
      expect(k.interact).not.toBe('E');
      expect(new Set(Object.values(k)).size).toBe(7);
      // 맞바꾸기는 둘을 함께 보낸다
      const sw = sanitizeKeys({ up: 'E', interact: 'W' });
      expect(sw.up).toBe('E');
      expect(sw.interact).toBe('W');
    });

    it('글자 크기는 2단(1 · 1.5)만 · 표시 이름', () => {
      expect(sanitizeSettings({ textScale: 1.5 }).textScale).toBe(1.5);
      expect(sanitizeSettings({ textScale: 1.25 }).textScale).toBe(1);
      expect(sanitizeSettings({ textScale: 2 }).textScale).toBe(1);
      expect(keyLabel('SPACE')).toBe('Space');
      expect(keyLabel('E')).toBe('E');
    });

    it('set: 키를 바꾸면 구독자가 새 키를 받는다 (InputSystem 다시 묶기)', () => {
      const svc = new SettingsService(new FakeMeta());
      svc.load();
      const got: string[] = [];
      const off = svc.onChange((s) => got.push(s.keys.dash));
      svc.set({ keys: { ...DEFAULT_SETTINGS.keys, dash: 'J' } });
      expect(got).toEqual(['J']);
      expect(svc.key('dash')).toBe('J');
      off();
      svc.set({ shake: 0.2 });
      expect(got).toEqual(['J']);
    });
  });
});
