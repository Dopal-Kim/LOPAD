import type { UiSettings } from '../contract/ui';
import { DEFAULT_KEYS, type KeyActionId, type KeyBinds, KEY_ACTIONS, readKeyBinds, sameBinds } from './keyBindView';

/**
 * 61라운드 P10 설정 화면 (계약 §15 `UiSettings`) — 순수 계산 (Phaser 없음). 기본값은 계약 코드 `UI_DEFAULT_SETTINGS`
 * (이 모듈은 Phaser 를 부르지 않게 타입만 가져오고, 기본값은 부르는 쪽이 넘긴다).
 * 62 루프 2 (P1-16): 탭 넷(화면·소리·조작·접근성) + 전체화면 · 소리 끄기 · 키 재설정 · 글자 크기 · 히트스톱 끄기.
 * 계약에 새로 들어올 필드(시스템 D 추가 중 — 가정): `hitstop: boolean`(기본 true) · `keys: KeyBinds`(keyBindView).
 * 전체화면(브라우저)·소리 끄기(§11.3 setMuted)·글자 크기(UI 보기 설정 uiPrefs)는 `UiSettings` 밖 값이라 화면이 따로 읽고 쓴다.
 */
export interface SettingsValues extends UiSettings {
  /** 히트스톱(타격 순간 멈춤) 켜기 — 계약 필드 가정 */
  hitstop: boolean;
  /** 키 재설정 — 계약 필드 가정 */
  keys: KeyBinds;
}

export type SliderId = 'shake' | 'master' | 'bgm' | 'sfx';
export type ToggleId = 'flash' | 'tilt' | 'damageNumbers' | 'hitstop';
/** `UiSettings` 밖 켜고 끄기 (화면이 직접 읽고 바꾼다) */
export type LocalToggleId = 'fullscreen' | 'muted';
export type ChoiceId = 'textSize';
export type SettingId = SliderId | ToggleId;
export type ActionId = 'resetKeys' | 'reset' | 'close';
export type SettingsTab = 'screen' | 'sound' | 'controls' | 'access';

/** 막대 칸 수 = 한 번에 바뀌는 폭 (10% 씩) */
export const SLIDER_STEPS = 10;

export type SettingRow =
  | { id: SliderId; kind: 'slider' }
  | { id: ToggleId; kind: 'toggle' }
  | { id: LocalToggleId; kind: 'local' }
  | { id: ChoiceId; kind: 'choice' }
  | { id: KeyActionId; kind: 'key' }
  | { id: ActionId; kind: 'action' };

export const SETTINGS_TABS: readonly SettingsTab[] = ['screen', 'sound', 'controls', 'access'];

/** 탭마다 줄 (탭 끝에 공통 끝줄 `END_ROWS` 가 붙는다) */
export const TAB_ROWS: Readonly<Record<SettingsTab, readonly SettingRow[]>> = {
  screen: [
    { id: 'fullscreen', kind: 'local' },
    { id: 'damageNumbers', kind: 'toggle' },
  ],
  sound: [
    { id: 'master', kind: 'slider' },
    { id: 'bgm', kind: 'slider' },
    { id: 'sfx', kind: 'slider' },
    { id: 'muted', kind: 'local' },
  ],
  controls: [...KEY_ACTIONS.map((id) => ({ id, kind: 'key' as const })), { id: 'resetKeys', kind: 'action' }],
  access: [
    { id: 'textSize', kind: 'choice' },
    { id: 'shake', kind: 'slider' },
    { id: 'flash', kind: 'toggle' },
    { id: 'tilt', kind: 'toggle' },
    { id: 'hitstop', kind: 'toggle' },
  ],
};

export const END_ROWS: readonly SettingRow[] = [
  { id: 'reset', kind: 'action' },
  { id: 'close', kind: 'action' },
];

/** 그 탭에서 보이는 줄 (탭 줄 제외) */
export function rowsFor(tab: SettingsTab): SettingRow[] {
  return [...TAB_ROWS[tab], ...END_ROWS];
}

/** 탭 옮기기 (끝에서 돌아간다) */
export function cycleTab(tab: SettingsTab, dir: -1 | 1): SettingsTab {
  const i = SETTINGS_TABS.indexOf(tab);
  const n = SETTINGS_TABS.length;
  return SETTINGS_TABS[(((i + dir) % n) + n) % n];
}

const SLIDERS: readonly SliderId[] = ['shake', 'master', 'bgm', 'sfx'];
const TOGGLES: readonly ToggleId[] = ['flash', 'tilt', 'damageNumbers', 'hitstop'];

function clamp01(v: number): number {
  return Math.max(0, Math.min(1, v));
}

/** 칸 단위로 맞춘 값 (부동소수 찌꺼기 없이) */
export function snapSlider(v: number, steps = SLIDER_STEPS): number {
  return Math.round(clamp01(v) * steps) / steps;
}

/** ←(-1)·→(+1) 한 칸. 칸 사이 값이면 먼저 가까운 칸으로 맞춘 뒤 움직인다 */
export function stepSlider(v: number, dir: -1 | 1, steps = SLIDER_STEPS): number {
  const cur = Math.round(clamp01(v) * steps);
  return Math.max(0, Math.min(steps, cur + dir)) / steps;
}

/** 막대 위 마우스 비율(0~1) → 값. 칸 단위로 반올림 */
export function sliderFromRatio(r: number, steps = SLIDER_STEPS): number {
  return snapSlider(Number.isFinite(r) ? r : 0, steps);
}

/** 켜진 칸 수 */
export function sliderCells(v: number, steps = SLIDER_STEPS): number {
  return Math.round(clamp01(v) * steps);
}

export function percentText(v: number): string {
  return `${Math.round(clamp01(v) * 100)}%`;
}

/** 계약 기본값 + 새 필드 기본값 (히트스톱 켬 · 기본 키) */
export function withDefaults(fallback: Readonly<UiSettings>): SettingsValues {
  return { ...fallback, hitstop: true, keys: { ...DEFAULT_KEYS } };
}

/**
 * 스냅샷에서 온 것을 믿을 수 있는 값으로. 빠졌거나 모양이 틀린 칸은 `fallback`(계약 기본값)의 값.
 * 객체가 아니면 null (시스템이 아직 `settings` 를 채우지 않음).
 */
export function normalizeSettings(raw: unknown, fallback: Readonly<UiSettings>): SettingsValues | null {
  if (!raw || typeof raw !== 'object') return null;
  const r = raw as Record<string, unknown>;
  const out = withDefaults(fallback);
  for (const id of SLIDERS) {
    const v = r[id];
    if (typeof v === 'number' && Number.isFinite(v)) out[id] = clamp01(v);
  }
  for (const id of TOGGLES) {
    const v = r[id];
    if (typeof v === 'boolean') out[id] = v;
  }
  out.keys = readKeyBinds(r.keys);
  // 계약 D 글자 크기 (1 | 1.25) — 그대로 실어 둔다 (UI 읽는 글 배율은 uiPrefs)
  if (typeof r.textScale === 'number' && Number.isFinite(r.textScale))
    (out as { textScale?: number }).textScale = r.textScale;
  return out;
}

export function isSlider(id: string): id is SliderId {
  return (SLIDERS as readonly string[]).includes(id);
}

/**
 * ←·→ 로 바꾸기. 막대는 한 칸, 켜고 끄기는 자리대로(← = 켬, → = 끔 — 화면에 '켬 끔' 순서로 놓인다).
 * 바뀐 것이 없으면 같은 객체를 돌려준다.
 */
export function changeSetting(s: SettingsValues, id: SettingId, dir: -1 | 1): SettingsValues {
  if (isSlider(id)) {
    const v = stepSlider(s[id], dir);
    return v === s[id] ? s : { ...s, [id]: v };
  }
  const v = dir < 0;
  return v === s[id] ? s : { ...s, [id]: v };
}

/** Enter·스페이스·클릭: 켜고 끄기 뒤집기 */
export function toggleSetting(s: SettingsValues, id: ToggleId): SettingsValues {
  return { ...s, [id]: !s[id] };
}

/** 막대 값 정하기 (마우스). 바뀐 것이 없으면 같은 객체 */
export function setSlider(s: SettingsValues, id: SliderId, v: number): SettingsValues {
  const nv = snapSlider(v);
  return nv === s[id] ? s : { ...s, [id]: nv };
}

/** 키 묶음 바꾸기 (같으면 같은 객체) */
export function setKeys(s: SettingsValues, keys: KeyBinds): SettingsValues {
  return sameBinds(s.keys, keys) ? s : { ...s, keys: { ...keys } };
}

export function sameSettings(a: SettingsValues, b: SettingsValues): boolean {
  return (
    SLIDERS.every((id) => a[id] === b[id]) &&
    TOGGLES.every((id) => a[id] === b[id]) &&
    sameBinds(a.keys, b.keys) &&
    (a as { textScale?: unknown }).textScale === (b as { textScale?: unknown }).textScale
  );
}

/** 커서 이동 (위아래 끝에서 돌아간다) */
export function moveCursor(i: number, dir: -1 | 1, n: number): number {
  if (n <= 0) return 0;
  return (((i + dir) % n) + n) % n;
}
