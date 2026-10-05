import { afterEach, describe, expect, it } from 'vitest';
import { DEFAULT_FEEL, feelSettings, setFeel } from './feel';
import { emptyMeta, type MetaData } from './meta';
import { DEFAULT_SETTINGS, SettingsService, feelPatchOf, sanitizeSettings, type VolumeSettings } from './settings';

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
    });
  });

  it('다듬기: 숫자는 0~1 로 자르고 형식이 틀린 칸은 기본값', () => {
    const s = sanitizeSettings({ shake: 3, flash: 'no', tilt: false, master: -1, bgm: Number.NaN, sfx: 0.25 });
    expect(s).toEqual({ shake: 1, flash: true, tilt: false, damageNumbers: true, master: 0, bgm: 1, sfx: 0.25 });
    expect(sanitizeSettings(null)).toEqual({ ...DEFAULT_SETTINGS });
  });

  it('감각 배율: 기울기 끄기 → tilt 0, 피해 숫자 → numbers', () => {
    expect(feelPatchOf({ ...DEFAULT_SETTINGS, shake: 0.5, tilt: false, flash: false, damageNumbers: false })).toEqual({
      shake: 0.5,
      flash: false,
      tilt: 0,
      numbers: false,
    });
  });

  it('부팅 load: 메타 저장값을 읽어 감각·음량에 바로 적용', () => {
    const meta = new FakeMeta();
    meta.data.settings = { shake: 0, flash: false, tilt: false, damageNumbers: false, master: 0.5, bgm: 0.2, sfx: 0.8 };
    const vols: VolumeSettings[] = [];
    const svc = new SettingsService(meta);
    const cur = svc.load((v) => vols.push(v));
    expect(cur.master).toBe(0.5);
    expect(feelSettings.shake).toBe(0);
    expect(feelSettings.flash).toBe(false);
    expect(feelSettings.tilt).toBe(0);
    expect(feelSettings.numbers).toBe(false);
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
});
