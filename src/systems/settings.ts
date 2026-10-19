/**
 * 61라운드 계약 §15 설정: 값 다듬기 · 감각 계층 반영 · 메타 세이브 저장. Phaser 의존 없음(테스트 가능).
 * - 화면 쪽(흔들림 배율·섬광·기울기·피해 숫자)은 `feelSettings` 에 넣는다 — 화면 효과 코드는 이미 그 값을 읽는다.
 * - 음량(master·bgm·sfx)은 주입받은 `applyVolumes`(오디오 시스템)로 넘긴다.
 * - 저장은 메타 세이브(`lopad.meta` 의 `settings`) — 런 세이브와 달리 사망·새 런에도 남는다.
 */
import { KEYBIND, SETTINGS } from '../core/Constants';
import type { UiBindAction, UiGoreLevel, UiKeyBindings, UiSettings, UiTextScale } from '../contract/ui';
import { setFeel, type FeelSettings } from './feel';
import { metaStore, type MetaData } from './meta';

/** 시스템 안에서는 62 D 확장 칸(keys·hitstop·textScale)·P21 gore 도 늘 채워져 있다 */
export type GameSettings = UiSettings & {
  keys: UiKeyBindings;
  hitstop: boolean;
  textScale: UiTextScale;
  gore: UiGoreLevel;
};

export interface VolumeSettings {
  master: number;
  bgm: number;
  sfx: number;
}

export const DEFAULT_SETTINGS: Readonly<GameSettings> = Object.freeze({
  ...SETTINGS.DEFAULT,
  keys: { ...SETTINGS.DEFAULT.keys },
  textScale: SETTINGS.DEFAULT.textScale as UiTextScale,
  gore: SETTINGS.DEFAULT.gore as UiGoreLevel,
});

/** 키 재설정 동작 순서 (겹침 검사 차례) */
export const BIND_ACTIONS: readonly UiBindAction[] = ['up', 'down', 'left', 'right', 'dash', 'interact', 'potion'];

/**
 * 62 D (P1-16) 키 다듬기: 바꿀 수 있는 키(KEYBIND.BINDABLE)만 받고, 앞 동작과 겹치면 그 동작은 base 값(그것도 겹치면 기본값)을 둔다.
 * 반환은 늘 7개 동작이 다 찬 서로 다른 키
 */
export function sanitizeKeys(raw: unknown, base: Readonly<UiKeyBindings> = DEFAULT_SETTINGS.keys): UiKeyBindings {
  const r = raw && typeof raw === 'object' ? (raw as Partial<Record<UiBindAction, unknown>>) : {};
  const ok = (k: unknown): k is string => typeof k === 'string' && KEYBIND.BINDABLE.includes(k.toUpperCase());
  const out = {} as UiKeyBindings;
  const used = new Set<string>();
  for (const a of BIND_ACTIONS) {
    const want = r[a];
    const cands = [ok(want) ? want.toUpperCase() : null, base[a], DEFAULT_SETTINGS.keys[a]];
    const pick = cands.find((k): k is string => typeof k === 'string' && !used.has(k));
    // 모두 겹치면(이상한 base) 남은 바꿀 수 있는 키 중 첫 것
    const key = pick ?? KEYBIND.BINDABLE.find((k) => !used.has(k)) ?? DEFAULT_SETTINGS.keys[a];
    used.add(key);
    out[a] = key;
  }
  return out;
}

/** 키 이름 → 화면 표시 이름 ('SPACE' → 'Space') */
export function keyLabel(key: string): string {
  return KEYBIND.LABELS[key] ?? key;
}

const textScaleOf = (v: unknown, fallback: UiTextScale): UiTextScale =>
  typeof v === 'number' && KEYBIND.TEXT_SCALES.includes(v) ? (v as UiTextScale) : fallback;

const goreOf = (v: unknown, fallback: UiGoreLevel): UiGoreLevel => (v === 0 || v === 1 || v === 2 ? v : fallback);

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
    keys: sanitizeKeys(r.keys, base.keys),
    hitstop: bool(r.hitstop, base.hitstop),
    textScale: textScaleOf(r.textScale, base.textScale),
    gore: goreOf(r.gore, base.gore),
  };
}

/** 설정 → 감각 계층 배율 (기울기는 켜기/끄기 → 배율 1/0) */
export function feelPatchOf(s: Readonly<GameSettings>): Partial<FeelSettings> {
  return { shake: s.shake, flash: s.flash, tilt: s.tilt ? 1 : 0, numbers: s.damageNumbers, hitstop: s.hitstop ? 1 : 0 };
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
  /** 62 D: 값이 바뀌면 (키 다시 묶기 등) — 씬이 붙였다 뗀다 */
  private readonly listeners = new Set<(s: GameSettings) => void>();

  constructor(private readonly meta: MetaRW) {}

  /** 부팅: 저장값을 읽어 적용. 음량 적용기는 오디오 시스템이 붙은 뒤 넘긴다 */
  load(applyVolumes: ((v: VolumeSettings) => void) | null = null): GameSettings {
    this.applyVolumes = applyVolumes;
    this.cur = sanitizeSettings(this.meta.read().settings);
    this.apply();
    return this.current();
  }

  current(): GameSettings {
    return { ...this.cur, keys: { ...this.cur.keys } };
  }

  /** UI 명령 (계약 §15 setSettings): 일부 칸만 와도 나머지는 지금 값 유지 */
  set(next: Partial<GameSettings>): GameSettings {
    this.cur = sanitizeSettings(next, this.cur);
    this.apply();
    const m = this.meta.read();
    this.meta.write({ ...m, settings: this.current() });
    return this.current();
  }

  /** 62 D: 바뀜 구독 (반환 = 떼기) */
  onChange(fn: (s: GameSettings) => void): () => void {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }

  /** 지금 묶인 키 (동작 → 키 이름) */
  key(action: UiBindAction): string {
    return this.cur.keys[action];
  }

  private apply(): void {
    setFeel(feelPatchOf(this.cur));
    this.applyVolumes?.(volumesOf(this.cur));
    const snap = this.current();
    for (const fn of this.listeners) fn(snap);
  }
}

/** 게임 수명 동안 하나 (main.ts 가 load) */
export const settings = new SettingsService(metaStore);
