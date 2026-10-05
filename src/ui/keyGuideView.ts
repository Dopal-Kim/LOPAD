import type { UiWeaponVerbs } from '../contract/ui';

/**
 * 61라운드 P10 키캡 안내 — 순수 계산 (Phaser 없음). 키 그림 + 동작 이름 한 줄을 범용으로 그리기 위한 해석·배치.
 *
 * 시스템이 무기를 4동사(좌 연격 · 우 시그니처 · 스페이스 대쉬 · 좌 홀드 고유 자원 기술, 61 P1)로 개편 중이다.
 * 계약 필드가 나오면 `verbItems()` 로 `{ input, name }` 목록을 그대로 받아 그린다(다음 작업). 지금은 `currentVerbItems()` 가
 * 기존 스냅샷(우클릭 보조 동작 이름·넣기/뽑기)으로 같은 모양을 만든다.
 */

/** 키 그림 한 칸 */
export type KeyGlyph =
  { kind: 'mouse'; button: 'left' | 'right'; hold: boolean } | { kind: 'key'; label: string; wide: boolean };

/** 한 줄 안내: 키 그림 여럿(W A S D 처럼) + 동작 이름 */
export interface KeyGuideItem {
  keys: string[];
  label: string;
  /** 지금 쓸 수 없는 동작 (흐리게) */
  dim?: boolean;
}

/** 시스템 4동사 필드가 오면 받을 모양 (가정 — 계약에 생기면 그 이름으로 맞춘다) */
export interface VerbLike {
  /** 'lmb' | 'rmb' | 'space' | 'lmbHold' 등 — parseKey 가 읽는 이름 */
  input: string;
  name: string;
  /** 지금 못 씀 (자원 부족 등) */
  disabled?: boolean;
}

const LEFT = ['lmb', 'mouse1', 'mouseleft', 'leftclick', 'left', '좌', '좌클릭', '왼쪽', '왼클릭'];
const RIGHT = ['rmb', 'mouse2', 'mouseright', 'rightclick', 'right', '우', '우클릭', '오른쪽', '오른클릭'];
const HOLD = ['hold', '홀드', '길게', '누르고있기'];
const NAMED: Record<string, string> = {
  space: 'Space',
  spacebar: 'Space',
  스페이스: 'Space',
  esc: 'Esc',
  escape: 'Esc',
  tab: 'Tab',
  shift: 'Shift',
  enter: 'Enter',
  ctrl: 'Ctrl',
  arrowup: '↑',
  arrowdown: '↓',
  arrowleft: '←',
  arrowright: '→',
};
/** 넓은 키 (글이 짧아도 폭을 넓게) */
const WIDE = new Set(['Space']);

/**
 * 키 이름 → 그림. 마우스는 'lmb'·'좌클릭'·'mouse:left' 등, 홀드는 'lmbHold'·'lmb_hold'·'좌 홀드'·'hold:lmb'.
 * 그 밖은 키캡(한 글자는 대문자, ' ' 는 Space).
 */
export function parseKey(raw: string): KeyGlyph {
  if (raw === ' ') return { kind: 'key', label: 'Space', wide: true };
  const flat = String(raw ?? '')
    .trim()
    .toLowerCase()
    .replace(/[\s_\-:+.]/g, '');
  let hold = false;
  let base = flat;
  for (const h of HOLD) {
    if (base.startsWith(h)) {
      hold = true;
      base = base.slice(h.length);
    } else if (base.endsWith(h)) {
      hold = true;
      base = base.slice(0, -h.length);
    }
  }
  if (LEFT.includes(base)) return { kind: 'mouse', button: 'left', hold };
  if (RIGHT.includes(base)) return { kind: 'mouse', button: 'right', hold };
  const named = NAMED[flat];
  if (named) return { kind: 'key', label: named, wide: WIDE.has(named) };
  const label = String(raw ?? '').trim();
  return { kind: 'key', label: label.length === 1 ? label.toUpperCase() : label, wide: false };
}

/** 키 그림 크기 (1배 px). 마우스 11×16, 키캡 높이 16 · 글 양옆 4 · 최소 16(넓은 키 34) */
export const KEY_GLYPH = { mouseW: 11, h: 16, padX: 4, minW: 16, wideW: 34 } as const;

/** 키 그림 폭. textW = 키캡 글자 폭(링 포함) */
export function glyphWidth(g: KeyGlyph, textW: number): number {
  if (g.kind === 'mouse') return KEY_GLYPH.mouseW;
  return Math.max(g.wide ? KEY_GLYPH.wideW : KEY_GLYPH.minW, Math.ceil(textW) + KEY_GLYPH.padX * 2);
}

/** 한 줄 안에서 차례로 놓을 x (왼쪽 끝 0 기준). 끝 폭도 함께 */
export function rowOffsets(widths: number[], gap: number): { xs: number[]; w: number } {
  const xs: number[] = [];
  let x = 0;
  widths.forEach((w, i) => {
    xs.push(x);
    x += w + (i < widths.length - 1 ? gap : 0);
  });
  return { xs, w: x };
}

/** 시스템 동사 목록 → 안내 줄 (이름이 빈 것은 뺀다) */
export function verbItems(verbs: readonly VerbLike[] | null | undefined): KeyGuideItem[] {
  if (!Array.isArray(verbs)) return [];
  return verbs
    .filter((v) => v && typeof v.input === 'string' && typeof v.name === 'string' && v.name.trim())
    .map((v) => ({ keys: [v.input], label: v.name.trim(), dim: Boolean(v.disabled) }));
}

type VerbText = (key: 'verbAttack' | 'verbDash' | 'verbCarry') => string;

/**
 * 지금 스냅샷으로 만드는 조작 안내 (4동사 필드가 오기 전): 좌클릭 공격 · 우클릭 {보조 동작} · Space 대쉬 (+ F 넣기·뽑기).
 */
export function currentVerbItems(
  s: { weapon: { secondaryName: string }; carry?: { key?: string } | null },
  t: VerbText,
): KeyGuideItem[] {
  const out: KeyGuideItem[] = [
    { keys: ['lmb'], label: t('verbAttack') },
    { keys: ['rmb'], label: s.weapon.secondaryName || '보조 동작' },
    { keys: ['space'], label: t('verbDash') },
  ];
  if (s.carry) out.push({ keys: [s.carry.key || 'F'], label: t('verbCarry') });
  return out;
}

/**
 * 스냅샷으로 만드는 조작 안내: 시스템 4동사(`weaponVerbs`, 61 P1 — key 는 '좌클릭'·'우클릭'·'Space'·'좌클릭 길게')가 있으면
 * 그 순서대로, 없으면 지금 조작(`currentVerbItems`).
 */
export function snapshotVerbItems(
  s: {
    weapon: { secondaryName: string };
    carry?: { key?: string } | null;
    weaponVerbs?: UiWeaponVerbs | null;
  },
  t: VerbText,
): KeyGuideItem[] {
  const verbs = s.weaponVerbs?.verbs;
  if (Array.isArray(verbs) && verbs.length) {
    const items = verbItems(verbs.map((v) => ({ input: v.key, name: v.name })));
    if (items.length) return items;
  }
  return currentVerbItems(s, t);
}
