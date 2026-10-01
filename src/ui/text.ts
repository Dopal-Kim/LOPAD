import { uiCommands, type UiText } from '../contract/ui';

/**
 * 세계관 문구 조회 (계약 §4 getUiText, 29라운드). 키가 없거나 비면 기본 문구를 쓴다.
 * 채택 범위는 결정 로그 round-29 자율 결정 B 를 따른다 (보류 항목은 호출하지 않는다).
 */
type Section = Exclude<keyof UiText, 'controls'>;

export function uiText(section: Section, key: string, fallback: string): string {
  const v = uiCommands.getUiText()[section]?.[key];
  return typeof v === 'string' && v.length > 0 ? v : fallback;
}

/** `{name}` 꼴 치환자를 채운다. 값이 없는 치환자는 그대로 둔다 */
export function fill(template: string, vars: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (m, k: string) => (k in vars ? String(vars[k]) : m));
}

const DEFAULT_CONTROLS = 'WASD 이동 · 좌클릭 공격 · 우클릭 {secondary} · 스페이스 대쉬 · Q 물약 · Esc 일시정지';

/** 조작법 한 줄. `{secondary}` 는 스냅샷의 우클릭 보조 동작 이름으로, 비면 '보조 동작' */
export function controlsLine(secondaryName: string): string {
  const tpl = uiCommands.getUiText().controls || DEFAULT_CONTROLS;
  return fill(tpl, { secondary: secondaryName || '보조 동작' });
}
