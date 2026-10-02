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

/** 45라운드 워프 문구 (임시값, 도영 님 검수 대상). 텍스트 팩 `hud.<키>` 가 있으면 그 문구를 쓴다 */
export const WARP_TEXT = {
  warpTitle: '지나온 길',
  warpHint: 'WASD·방향키 고르기 · Enter·Space·클릭 건너가기 · Tab·Esc 닫기',
  warpEmpty: '아직 건너갈 곳이 없다. 마친 방만 다시 찾아갈 수 있다',
  warpPick: '건너갈 곳을 고른다',
  warpHere: '지금 여기',
  warpCan: '건너갈 수 있다',
  warpCannot: '아직 마치지 않았다',
  warpKeyHint: 'Tab 워프',
  warpDone: '건너왔다 — {room}',
  warpDeniedCombat: '싸움이 끝나야 건너갈 수 있다',
  warpDeniedBusy: '지금은 건너갈 수 없다',
  warpDeniedUnknown: '그런 곳은 없다',
  warpDeniedNotCleared: '아직 마치지 않은 곳이다',
  warpDeniedCurrent: '이미 여기 있다',
  roomStart: '시작한 곳',
  roomTrial: '시련',
  roomRest: '쉼터',
  roomBoss: '본영',
} as const;
export type WarpTextKey = keyof typeof WARP_TEXT;

export function warpText(key: WarpTextKey): string {
  return uiText('hud', key, WARP_TEXT[key]);
}
