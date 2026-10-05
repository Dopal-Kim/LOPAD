import type { UiSettings } from '../contract/ui';

/**
 * 61라운드 P10 설정 화면 (계약 §15 `UiSettings`) — 순수 계산 (Phaser 없음). 기본값은 계약 코드 `UI_DEFAULT_SETTINGS`
 * (이 모듈은 Phaser 를 부르지 않게 타입만 가져오고, 기본값은 부르는 쪽이 넘긴다).
 */
export type SettingsValues = UiSettings;

export type SliderId = 'shake' | 'master' | 'bgm' | 'sfx';
export type ToggleId = 'flash' | 'tilt' | 'damageNumbers';
export type SettingId = SliderId | ToggleId;
export type ActionId = 'reset' | 'close';

/** 막대 칸 수 = 한 번에 바뀌는 폭 (10% 씩) */
export const SLIDER_STEPS = 10;

export type SettingRow =
  | { id: SliderId; kind: 'slider'; group: 'screen' | 'sound' }
  | { id: ToggleId; kind: 'toggle'; group: 'screen' }
  | { id: ActionId; kind: 'action'; group: 'end' };

/** 화면 순서: 화면(흔들림·섬광·기울기·피해 숫자) → 소리(전체·배경음·효과음) → 되돌리기·덮기 */
export const SETTING_ROWS: readonly SettingRow[] = [
  { id: 'shake', kind: 'slider', group: 'screen' },
  { id: 'flash', kind: 'toggle', group: 'screen' },
  { id: 'tilt', kind: 'toggle', group: 'screen' },
  { id: 'damageNumbers', kind: 'toggle', group: 'screen' },
  { id: 'master', kind: 'slider', group: 'sound' },
  { id: 'bgm', kind: 'slider', group: 'sound' },
  { id: 'sfx', kind: 'slider', group: 'sound' },
  { id: 'reset', kind: 'action', group: 'end' },
  { id: 'close', kind: 'action', group: 'end' },
];

const SLIDERS: readonly SliderId[] = ['shake', 'master', 'bgm', 'sfx'];
const TOGGLES: readonly ToggleId[] = ['flash', 'tilt', 'damageNumbers'];

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

/**
 * 스냅샷에서 온 것을 믿을 수 있는 값으로. 빠졌거나 모양이 틀린 칸은 `fallback`(계약 기본값)의 값.
 * 객체가 아니면 null (시스템이 아직 `settings` 를 채우지 않음).
 */
export function normalizeSettings(raw: unknown, fallback: Readonly<SettingsValues>): SettingsValues | null {
  if (!raw || typeof raw !== 'object') return null;
  const r = raw as Record<string, unknown>;
  const out = { ...fallback };
  for (const id of SLIDERS) {
    const v = r[id];
    if (typeof v === 'number' && Number.isFinite(v)) out[id] = clamp01(v);
  }
  for (const id of TOGGLES) {
    const v = r[id];
    if (typeof v === 'boolean') out[id] = v;
  }
  return out;
}

export function isSlider(id: string): id is SliderId {
  return (SLIDERS as readonly string[]).includes(id);
}

export function isToggle(id: string): id is ToggleId {
  return (TOGGLES as readonly string[]).includes(id);
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

export function sameSettings(a: SettingsValues, b: SettingsValues): boolean {
  return SLIDERS.every((id) => a[id] === b[id]) && TOGGLES.every((id) => a[id] === b[id]);
}

/** 커서 이동 (위아래 끝에서 돌아간다) */
export function moveCursor(i: number, dir: -1 | 1, n = SETTING_ROWS.length): number {
  if (n <= 0) return 0;
  return (((i + dir) % n) + n) % n;
}
