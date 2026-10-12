/**
 * 62 루프 2 (P1-16) 키 재설정 — 순수 계산 (Phaser 없음).
 * 값은 Phaser `KeyCodes` 이름('W'·'SPACE'·'Q' — 시스템 `KEYS` 상수와 같은 꼴)이다. 키를 받을 때는 `KeyboardEvent.code` 를 쓴다
 * (한글 입력기가 켜져 있으면 `key` 가 'ㅈ' 처럼 오므로 자판 자리 기준).
 * 계약 필드(시스템 D 추가 중 — 가정): `UiSettings.keys: { up, down, left, right, dash, interact, potion }`.
 */

export type KeyActionId = 'up' | 'down' | 'left' | 'right' | 'dash' | 'interact' | 'potion';
export type KeyBinds = Record<KeyActionId, string>;

/** 설정 화면 순서 */
export const KEY_ACTIONS: readonly KeyActionId[] = ['up', 'down', 'left', 'right', 'dash', 'interact', 'potion'];

/** 기본 키 (시스템 `KEYS` 의 UP·DOWN·LEFT·RIGHT·DASH·INTERACT·POTION) */
export const DEFAULT_KEYS: Readonly<KeyBinds> = Object.freeze({
  up: 'W',
  down: 'S',
  left: 'A',
  right: 'D',
  dash: 'SPACE',
  interact: 'E',
  potion: 'Q',
});

/**
 * 바꿀 수 없는 키 → 까닭. UI 가 쓰는 키(Esc 일시정지·Tab 빌드·M 지도·Enter 정하기·F11 전체화면)와
 * 시스템이 고정해 둔 키(Shift 달리기·R 장전·C 소모품).
 */
export const RESERVED_KEYS: Readonly<Record<string, string>> = Object.freeze({
  ESC: 'Esc',
  TAB: 'Tab',
  M: 'M',
  ENTER: 'Enter',
  F11: 'F11',
  SHIFT: 'Shift',
  R: 'R',
  C: 'C',
});

const NAMED_CODES: Readonly<Record<string, string>> = Object.freeze({
  Space: 'SPACE',
  ArrowUp: 'UP',
  ArrowDown: 'DOWN',
  ArrowLeft: 'LEFT',
  ArrowRight: 'RIGHT',
  ShiftLeft: 'SHIFT',
  ShiftRight: 'SHIFT',
  ControlLeft: 'CTRL',
  ControlRight: 'CTRL',
  AltLeft: 'ALT',
  AltRight: 'ALT',
  Escape: 'ESC',
  Tab: 'TAB',
  Enter: 'ENTER',
  NumpadEnter: 'ENTER',
  Backspace: 'BACKSPACE',
  CapsLock: 'CAPS_LOCK',
  Comma: 'COMMA',
  Period: 'PERIOD',
  Slash: 'FORWARD_SLASH',
  Backslash: 'BACK_SLASH',
  Semicolon: 'SEMICOLON',
  Quote: 'QUOTES',
  BracketLeft: 'OPEN_BRACKET',
  BracketRight: 'CLOSED_BRACKET',
  Minus: 'MINUS',
  Equal: 'PLUS',
  Backquote: 'BACKTICK',
});

const DIGITS = ['ZERO', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE'] as const;

/** 메타 키(Win·Cmd)·입력기 전환 키는 받지 않는다 */
const IGNORED_CODES = new Set(['MetaLeft', 'MetaRight', 'ContextMenu', 'Lang1', 'Lang2', 'HangulMode', 'Hanja']);

/** `KeyboardEvent.code` → Phaser KeyCodes 이름. 받지 않는 키면 null */
export function codeToKeyName(code: string): string | null {
  if (!code || IGNORED_CODES.has(code)) return null;
  const letter = /^Key([A-Z])$/.exec(code);
  if (letter) return letter[1];
  const digit = /^Digit([0-9])$/.exec(code);
  if (digit) return DIGITS[Number(digit[1])];
  const pad = /^Numpad([0-9])$/.exec(code);
  if (pad) return `NUMPAD_${DIGITS[Number(pad[1])]}`;
  const fn = /^F([1-9]|1[0-2])$/.exec(code);
  if (fn) return `F${fn[1]}`;
  return NAMED_CODES[code] ?? null;
}

const LABELS: Readonly<Record<string, string>> = Object.freeze({
  SPACE: 'Space',
  UP: '↑',
  DOWN: '↓',
  LEFT: '←',
  RIGHT: '→',
  SHIFT: 'Shift',
  CTRL: 'Ctrl',
  ALT: 'Alt',
  ESC: 'Esc',
  TAB: 'Tab',
  ENTER: 'Enter',
  BACKSPACE: 'Backspace',
  CAPS_LOCK: 'Caps',
  COMMA: ',',
  PERIOD: '.',
  FORWARD_SLASH: '/',
  BACK_SLASH: '\\',
  SEMICOLON: ';',
  QUOTES: "'",
  OPEN_BRACKET: '[',
  CLOSED_BRACKET: ']',
  MINUS: '-',
  PLUS: '=',
  BACKTICK: '`',
});

/** 화면에 보일 키 이름 ('SPACE' → 'Space', 'ONE' → '1', 'NUMPAD_ONE' → '숫자판 1') */
export function keyLabel(name: string): string {
  if (LABELS[name]) return LABELS[name];
  const d = DIGITS.indexOf(name as (typeof DIGITS)[number]);
  if (d >= 0) return String(d);
  const pad = /^NUMPAD_([A-Z]+)$/.exec(name);
  if (pad) {
    const n = DIGITS.indexOf(pad[1] as (typeof DIGITS)[number]);
    if (n >= 0) return `숫자판 ${n}`;
  }
  return name;
}

/** 이동 네 키를 한 낱말로 ('WASD' · 화살표면 '↑←↓→') — 조작 줄용 */
export function moveKeysLabel(b: KeyBinds): string {
  const parts = [b.up, b.left, b.down, b.right].map(keyLabel);
  return parts.every((p) => p.length === 1) ? parts.join('') : parts.join(' ');
}

/** 스냅샷에서 온 값을 믿을 수 있는 키 묶음으로 (빠지거나 틀린 칸은 기본 키). 객체가 아니면 기본 묶음 */
export function readKeyBinds(raw: unknown): KeyBinds {
  const out: KeyBinds = { ...DEFAULT_KEYS };
  if (!raw || typeof raw !== 'object') return out;
  const r = raw as Record<string, unknown>;
  for (const id of KEY_ACTIONS) {
    const v = r[id];
    if (typeof v === 'string' && /^[A-Z0-9_]{1,16}$/.test(v) && !RESERVED_KEYS[v]) out[id] = v;
  }
  return out;
}

export function sameBinds(a: KeyBinds, b: KeyBinds): boolean {
  return KEY_ACTIONS.every((id) => a[id] === b[id]);
}

export function isDefaultBinds(b: KeyBinds): boolean {
  return sameBinds(b, DEFAULT_KEYS);
}

export type AssignResult =
  | { ok: true; binds: KeyBinds; swapped: KeyActionId | null }
  | { ok: false; reason: 'reserved'; label: string }
  | { ok: false; reason: 'unknown' };

/**
 * 동작에 키를 준다. 그 키를 이미 다른 동작이 쓰고 있으면 두 동작의 키를 맞바꾼다(겹치는 키 없음).
 * 바꿀 수 없는 키·받지 않는 키면 실패. 같은 키면 바뀐 것 없이 ok (binds 그대로).
 */
export function assignKey(b: KeyBinds, action: KeyActionId, name: string | null): AssignResult {
  if (!name) return { ok: false, reason: 'unknown' };
  if (RESERVED_KEYS[name]) return { ok: false, reason: 'reserved', label: RESERVED_KEYS[name] };
  if (b[action] === name) return { ok: true, binds: b, swapped: null };
  const other = KEY_ACTIONS.find((id) => id !== action && b[id] === name) ?? null;
  const next: KeyBinds = { ...b, [action]: name };
  if (other) next[other] = b[action];
  return { ok: true, binds: next, swapped: other };
}
