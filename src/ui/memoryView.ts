import type { UiMemoryBook, UiMemoryEntry, UiMemoryKind, UiMenu, UiNextUnlock } from '../contract/ui';
import { fill } from './fmt';
import { LOOP2E_TEXT, type Loop2ETextKey } from './textLoop2E';

/**
 * 62 루프 2 UI E (계약 C P1-8): 일기장 '기억' 장 — 순수 계산 (Phaser 없음, 단위 테스트).
 * 다섯 칸(소품 · 손이 기억한 모양 · 떠올릴 개성 · 장터에 놓일 것 · 몸의 기억)을 줄로, 기억 하나를 칸으로 놓는 격자 ·
 * 고름 자리 옮기기 · Enter 동작(떠올린다 / 지니고 태어난다 / 내려놓는다) · 칸 상태 글.
 */
type Tx = (k: Loop2ETextKey) => string;
const defaultTx: Tx = (k) => LOOP2E_TEXT[k];

/** 칸 차례 (계약 `UiMemoryKind`) */
export const MEMORY_CHAPTERS: readonly UiMemoryKind[] = ['keepsake', 'aspect', 'pool', 'shop', 'stat'];

/** 장 이름 대체 글 (시스템 장 이름이 없을 때) */
const CHAPTER_NAME: Record<UiMemoryKind, Loop2ETextKey> = {
  keepsake: 'chapterKeepsake',
  aspect: 'chapterAspect',
  pool: 'chapterPool',
  shop: 'chapterShop',
  stat: 'chapterStat',
};

/** 화면 줄 하나 (빈 장은 빠진다) */
export interface MemoryRow {
  kind: UiMemoryKind;
  name: string;
  entries: UiMemoryEntry[];
}

/** 격자 — 계약 장 순서가 달라도 MEMORY_CHAPTERS 차례로, 빈 장은 뺀다 */
export function memoryRows(book: Pick<UiMemoryBook, 'chapters'>): MemoryRow[] {
  const rows: MemoryRow[] = [];
  for (const kind of MEMORY_CHAPTERS) {
    const c = book.chapters.find((x) => x.kind === kind);
    if (c && c.entries.length) rows.push({ kind, name: c.name, entries: c.entries });
  }
  // 계약에 새 장이 생기면 뒤에 붙인다
  for (const c of book.chapters)
    if (!MEMORY_CHAPTERS.includes(c.kind) && c.entries.length)
      rows.push({ kind: c.kind, name: c.name, entries: c.entries });
  return rows;
}

/** 고름 자리 (줄 · 칸) */
export interface MemoryFocus {
  r: number;
  c: number;
}

/** 평평한 번호 (다시 그릴 때 지킬 자리) ↔ 자리 */
export function focusIndex(rows: readonly MemoryRow[], f: MemoryFocus): number {
  let i = 0;
  for (let r = 0; r < f.r && r < rows.length; r++) i += rows[r].entries.length;
  return i + f.c;
}

export function focusAt(rows: readonly MemoryRow[], index: number): MemoryFocus {
  let left = Math.max(0, Math.floor(index));
  for (let r = 0; r < rows.length; r++) {
    const n = rows[r].entries.length;
    if (left < n) return { r, c: left };
    left -= n;
  }
  const r = Math.max(0, rows.length - 1);
  return { r, c: Math.max(0, (rows[r]?.entries.length ?? 1) - 1) };
}

export type MemoryDir = 'left' | 'right' | 'up' | 'down';

/** 키 → 방향 (방향키 · WASD) */
export function memoryDir(key: string): MemoryDir | null {
  switch (key) {
    case 'ArrowLeft':
    case 'a':
    case 'A':
      return 'left';
    case 'ArrowRight':
    case 'd':
    case 'D':
      return 'right';
    case 'ArrowUp':
    case 'w':
    case 'W':
      return 'up';
    case 'ArrowDown':
    case 's':
    case 'S':
      return 'down';
    default:
      return null;
  }
}

/**
 * 고름 자리 옮기기: ←→ 는 줄 안(끝에서 앞·뒤 줄로 넘어감), ↑↓ 는 줄 사이(칸 번호는 그 줄 길이로 자름, 끝에서 돌아감)
 */
export function moveFocus(rows: readonly MemoryRow[], f: MemoryFocus, dir: MemoryDir): MemoryFocus {
  if (!rows.length) return f;
  const len = (r: number) => rows[r].entries.length;
  const R = rows.length;
  if (dir === 'up' || dir === 'down') {
    const r = (f.r + (dir === 'down' ? 1 : -1) + R) % R;
    return { r, c: Math.min(f.c, len(r) - 1) };
  }
  if (dir === 'right') {
    if (f.c + 1 < len(f.r)) return { r: f.r, c: f.c + 1 };
    return { r: (f.r + 1) % R, c: 0 };
  }
  if (f.c > 0) return { r: f.r, c: f.c - 1 };
  const r = (f.r - 1 + R) % R;
  return { r, c: len(r) - 1 };
}

/** Enter 동작 — recall 떠올린다 · equip 지니고 태어난다 · unequip 내려놓는다 · none 할 것 없음(영혼 모자람 · 다 떠올림) */
export type MemoryAction = 'recall' | 'equip' | 'unequip' | 'none';

export function memoryAction(e: UiMemoryEntry, keepsake: string | null): MemoryAction {
  if (e.kind === 'keepsake' && e.unlocked) return keepsake === e.id ? 'unequip' : 'equip';
  if (e.affordable && !e.unlocked) return 'recall';
  return 'none';
}

/** 칸 상태 한 줄 (지닌 소품은 '지니고 태어난다', 그 밖은 시스템 글 그대로) */
export function memoryState(e: UiMemoryEntry, keepsake: string | null, tx: Tx = defaultTx): string {
  if (e.kind === 'keepsake' && e.unlocked && keepsake === e.id) return tx('equipped');
  return e.state;
}

/** 동작 안내 ('[Enter] 떠올린다' …, 할 것이 없으면 '') */
export function memoryActionHint(a: MemoryAction, tx: Tx = defaultTx): string {
  if (a === 'recall') return tx('recall');
  if (a === 'equip') return tx('equip');
  if (a === 'unequip') return tx('unequip');
  return '';
}

/** 다음 기억 한 줄 (계약 `UiNextUnlock` — 없으면 다 떠올림) */
export function nextLine(next: UiNextUnlock | null, tx: Tx = defaultTx): string {
  if (!next) return tx('nextAll');
  if (next.left <= 0) return tx('nextReady');
  return fill(tx('nextLeft'), { n: next.left });
}

/**
 * 칸에 그림이 없을 때 쓸 글자 한 자 — 몸의 기억은 첫 낱말('몸의 기억' → '몸'), 그 밖은 끝 낱말('장터의 먹물' → '먹')
 */
export function memoryGlyph(e: Pick<UiMemoryEntry, 'name' | 'kind'>): string {
  const words = e.name.split(/\s+/).filter(Boolean);
  const word = (e.kind === 'stat' ? words[0] : words[words.length - 1]) ?? e.name;
  return (word[0] ?? '?').trim() || '?';
}

/** 단계 칸 ('{n}단계 / {max}', 몸의 기억만) */
export function memoryLevel(e: UiMemoryEntry, tx: Tx = defaultTx): string {
  return e.level ? fill(tx('stepLevel'), { n: e.level.n, max: e.level.max }) : '';
}

/**
 * 메뉴 'meta'(의식 화면 F2 — 줄마다 `line.memory`, key 'm:<id>' · 닫기 '0')에서 기억 장을 다시 짓는다 —
 * 시스템 `uiCommands.memory.book()` 이 없을 때(디버그 가짜 메뉴) 대신. 장 이름은 UI 대체 글.
 */
export function bookFromMenu(m: Pick<UiMenu, 'title' | 'footer' | 'lines'>, tx: Tx = defaultTx): UiMemoryBook | null {
  const entries = m.lines.map((l) => l.memory).filter((e): e is UiMemoryEntry => Boolean(e));
  if (!entries.length) return null;
  const chapters = MEMORY_CHAPTERS.map((kind) => ({
    kind,
    name: tx(CHAPTER_NAME[kind]),
    entries: entries.filter((e) => e.kind === kind),
  })).filter((c) => c.entries.length);
  const souls = Number(/(\d+)\s*$/.exec(m.title ?? '')?.[1] ?? 0);
  return {
    title: tx('bookTitle'),
    intro: m.footer ? [m.footer] : [],
    soulsText: (m.title ?? '').split('·').slice(1).join('·').trim(),
    souls,
    chapters,
    next: null,
    keepsake: null,
  };
}

/** 메뉴 'meta' 가 기억 장인가 (줄에 `line.memory` 가 하나라도) */
export function isMemoryBookMenu(m: Pick<UiMenu, 'id' | 'lines'>): boolean {
  return m.id === 'meta' && m.lines.some((l) => Boolean(l.memory));
}

/** 운명 공개 뒤 고르기 메뉴 ('aspect' 손이 기억한 모양 · 'keepsake' 지니고 태어날 소품) */
export function isMemoryPickMenu(m: Pick<UiMenu, 'id' | 'lines'>): boolean {
  return (m.id === 'aspect' || m.id === 'keepsake') && m.lines.length >= 1 && m.lines.length <= 5;
}

/** 같은 기억을 방금 떠올렸나 (다시 그린 뒤 떠올리기 연출을 이어서 보일지) — 떠올린 id · 시각 */
export interface RecallMark {
  id: string;
  at: number;
}

/** 떠올리기 연출을 보일 칸 id (표식이 오래됐거나 아직 안 열렸으면 null) */
export function recallTarget(
  mark: RecallMark | null,
  rows: readonly MemoryRow[],
  now: number,
  windowMs: number,
): string | null {
  if (!mark || now - mark.at > windowMs) return null;
  for (const r of rows)
    for (const e of r.entries) if (e.id === mark.id && (e.unlocked || (e.level?.n ?? 0) > 0)) return e.id;
  return null;
}
