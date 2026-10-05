import { UI_DEFAULT_SETTINGS, uiCommands } from '../contract/ui';
import { setSettingsCmd, withDebug } from './debug';
import { normalizeSettings, type SettingsValues } from './settingsView';

/**
 * 61라운드 §15 설정 값의 UI 쪽 사본. 저장은 시스템 세이브(메타 영역) 몫이고, 스냅샷 `settings` 로 온다(타이틀에서도).
 * 일시정지 중에는 스냅샷이 늦게 바뀔 수 있어(49라운드 음소거와 같은 까닭) 이번 실행에서 UI 가 마지막으로 보낸 값을 먼저 쓴다.
 */
let sent: SettingsValues | null = null;

/** 지금 설정: 이번 실행에서 보낸 값 → 스냅샷 `settings` → 계약 기본값 */
export function currentSettings(): SettingsValues {
  if (sent) return { ...sent };
  const snap = withDebug(uiCommands.getUiSnapshot());
  return normalizeSettings(snap.settings, UI_DEFAULT_SETTINGS) ?? { ...UI_DEFAULT_SETTINGS };
}

/** 계약 기본값 (설정 화면 '처음 값으로 되돌린다') */
export function defaultSettings(): SettingsValues {
  return { ...UI_DEFAULT_SETTINGS };
}

/** 값이 바뀌면 곧바로 시스템으로 (`uiCommands.setSettings`) */
export function commitSettings(s: SettingsValues): void {
  sent = { ...s };
  setSettingsCmd(sent);
}
