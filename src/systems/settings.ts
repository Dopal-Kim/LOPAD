/**
 * 61라운드 계약 §15 설정: 값 다듬기 · 감각 계층 반영 · 메타 세이브 저장. Phaser 의존 없음(테스트 가능).
 * - 화면 쪽(흔들림 배율·섬광·기울기·피해 숫자)은 `feelSettings` 에 넣는다 — 화면 효과 코드는 이미 그 값을 읽는다.
 * - 음량(master·bgm·sfx)은 주입받은 `applyVolumes`(오디오 시스템)로 넘긴다.
 * - 저장은 메타 세이브(`lopad.meta` 의 `settings`) — 런 세이브와 달리 사망·새 런에도 남는다.
 */
import { SETTINGS } from '../core/Constants';
import type { UiSettings } from '../contract/ui';
import { setFeel, type FeelSettings } from './feel';
import { metaStore, type MetaData } from './meta';

export type GameSettings = UiSettings;

export interface VolumeSettings {
  master: number;
  bgm: number;
  sfx: number;
}

export const DEFAULT_SETTINGS: Readonly<GameSettings> = Object.freeze({ ...SETTINGS.DEFAULT });

const clamp01 = (v: unknown, fallback: number): number =>
  typeof v === 'number' && Number.isFinite(v) ? Math.min(1, Math.max(0, v)) : fallback;
const bool = (v: unknown, fallback: boolean): boolean => (typeof v === 'boolean' ? v : fallback);

/** 저장값·UI 값을 다듬는다: 숫자는 0~1 로 자르고, 형식이 틀린 칸은 base(기본값) 그대로 */
export function sanitizeSettings(raw: unknown, base: Readonly<GameSettings> = DEFAULT_SETTINGS): GameSettings {
  const r = raw && typeof raw === 'object' ? (raw as Partial<Record<keyof GameSettings, unknown>>) : {};
  return {
    shake: clamp01(r.shake, base.shake),
    flash: bool(r.flash, base.flash),
    tilt: bool(r.tilt, base.tilt),
    damageNumbers: bool(r.damageNumbers, base.damageNumbers),
    master: clamp01(r.master, base.master),
    bgm: clamp01(r.bgm, base.bgm),
    sfx: clamp01(r.sfx, base.sfx),
  };
}

/** 설정 → 감각 계층 배율 (기울기는 켜기/끄기 → 배율 1/0) */
export function feelPatchOf(s: Readonly<GameSettings>): Partial<FeelSettings> {
  return { shake: s.shake, flash: s.flash, tilt: s.tilt ? 1 : 0, numbers: s.damageNumbers };
}

export function volumesOf(s: Readonly<GameSettings>): VolumeSettings {
  return { master: s.master, bgm: s.bgm, sfx: s.sfx };
}

/** 메타 세이브 읽기·쓰기만 (MetaStore 와 같은 모양 — 테스트에서 가짜로 바꾼다) */
export interface MetaRW {
  read(): MetaData;
  write(d: MetaData): void;
}

/**
 * 설정 서비스 (게임 수명 동안 하나 — main.ts 가 load). set 은 다듬기 → 감각·음량 즉시 적용 → 메타에 쓰기.
 * 메타는 매번 새로 읽어 settings 칸만 바꾼다 (런 정산 등 다른 쓰기와 겹쳐도 지우지 않음)
 */
export class SettingsService {
  private cur: GameSettings = { ...DEFAULT_SETTINGS };
  private applyVolumes: ((v: VolumeSettings) => void) | null = null;

  constructor(private readonly meta: MetaRW) {}

  /** 부팅: 저장값을 읽어 적용. 음량 적용기는 오디오 시스템이 붙은 뒤 넘긴다 */
  load(applyVolumes: ((v: VolumeSettings) => void) | null = null): GameSettings {
    this.applyVolumes = applyVolumes;
    this.cur = sanitizeSettings(this.meta.read().settings);
    this.apply();
    return this.current();
  }

  current(): GameSettings {
    return { ...this.cur };
  }

  /** UI 명령 (계약 §15 setSettings): 일부 칸만 와도 나머지는 지금 값 유지 */
  set(next: Partial<GameSettings>): GameSettings {
    this.cur = sanitizeSettings(next, this.cur);
    this.apply();
    const m = this.meta.read();
    this.meta.write({ ...m, settings: this.current() });
    return this.current();
  }

  private apply(): void {
    setFeel(feelPatchOf(this.cur));
    this.applyVolumes?.(volumesOf(this.cur));
  }
}

/** 게임 수명 동안 하나 (main.ts 가 load) */
export const settings = new SettingsService(metaStore);
