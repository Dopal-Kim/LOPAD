/**
 * 61 단계 6 (P14 §1, 계약 §19) 수련장 UI — 순수 계산 (Phaser 없음, 테스트한다).
 * 과제 줄(키캡) · 새로 끝난 과제 찾기 · 이벤트 읽기 · 수련장 지도 방 자리(그림 메타 rooms 또는 대체 배치).
 */
import type { UiTraining, UiVerbSlot, UiWeaponVerbs } from '../contract/ui';

/** 동사 칸 → 기본 키 이름 (스냅샷 4동사가 없을 때) */
export const VERB_DEFAULT_KEY: Record<UiVerbSlot, string> = {
  attack: '좌클릭',
  signature: '우클릭',
  dash: 'Space',
  hold: '좌클릭 길게',
};

/** 과제 한 줄 (그리기용) */
export interface TaskRow {
  id: string;
  label: string;
  done: boolean;
  /** 키캡 이름 (verb 가 없으면 null) */
  key: string | null;
}

/** 수련장 스냅샷이 쓸 만한가 (training 이 있고 방 id 가 있음) */
export function trainingOf(s: { training?: UiTraining | null }): UiTraining | null {
  const t = s.training;
  if (!t || typeof t !== 'object' || typeof t.room !== 'string') return null;
  return t;
}

/** 지도 마당(방이 아님) — 과제 목록을 그리지 않는다 */
export function isTrainingHall(t: UiTraining): boolean {
  return t.room === '' || t.room === 'hall';
}

/** 과제 줄: verb 가 있으면 지금 무기 4동사의 키(없으면 기본 키) */
export function taskRows(t: UiTraining, verbs: UiWeaponVerbs | null | undefined): TaskRow[] {
  const list = Array.isArray(t.tasks) ? t.tasks : [];
  return list
    .filter((x) => x && typeof x.id === 'string')
    .map((x) => {
      let key: string | null = null;
      if (x.verb) {
        const v = verbs?.verbs?.find((vv) => vv.slot === x.verb);
        key = v?.key || VERB_DEFAULT_KEY[x.verb] || null;
      }
      return { id: x.id, label: String(x.label ?? ''), done: Boolean(x.done), key };
    });
}

/** 지난 스냅샷 대비 새로 끝난 과제 id (같은 방일 때만 — 방이 바뀌면 빈 목록) */
export function newlyDone(prevRoom: string | null, prevDone: ReadonlySet<string>, t: UiTraining): string[] {
  if (prevRoom !== t.room) return [];
  return (t.tasks ?? []).filter((x) => x.done && !prevDone.has(x.id)).map((x) => x.id);
}

/** 끝난 과제 수 */
export function doneCount(t: UiTraining): { done: number; total: number } {
  const list = t.tasks ?? [];
  return { done: list.filter((x) => x.done).length, total: list.length };
}

/** `ui:training-task` 읽기 */
export function readTaskEvent(p: unknown): { room: string; id: string; label: string } | null {
  if (!p || typeof p !== 'object') return null;
  const o = p as Record<string, unknown>;
  if (typeof o.id !== 'string') return null;
  return {
    room: typeof o.room === 'string' ? o.room : '',
    id: o.id,
    label: typeof o.label === 'string' ? o.label : '',
  };
}

/** `ui:training-stamp` 읽기 */
export function readStampEvent(p: unknown): { room: string; name: string; all: boolean } | null {
  if (!p || typeof p !== 'object') return null;
  const o = p as Record<string, unknown>;
  if (typeof o.room !== 'string') return null;
  return { room: o.room, name: typeof o.name === 'string' ? o.name : '', all: o.all === true };
}

// ---------------------------------------------------------------------------------------------
/** 지도 위 방 자리 (지도 영역 0~1 비율) */
export interface MapSpot {
  id: string;
  u: number;
  v: number;
}

/**
 * 그림 메타 `rooms` 읽기 — `[{ id, x, y }]`(그림 픽셀, imgW·imgH 로 나눔) 또는 `{ <id>: [x, y] | {x, y} }`.
 * 0~1 사이 값이면 이미 비율로 본다. 읽을 수 없으면 빈 목록.
 */
export function readMapRooms(meta: unknown, imgW: number, imgH: number): MapSpot[] {
  if (!meta || typeof meta !== 'object') return [];
  const m = meta as Record<string, unknown>;
  const raw = m.rooms ?? (m.meta as Record<string, unknown> | undefined)?.rooms;
  const out: MapSpot[] = [];
  const push = (id: unknown, x: unknown, y: unknown): void => {
    if (typeof id !== 'string' || typeof x !== 'number' || typeof y !== 'number') return;
    const frac = x <= 1 && y <= 1;
    out.push({ id, u: frac ? x : x / Math.max(1, imgW), v: frac ? y : y / Math.max(1, imgH) });
  };
  if (Array.isArray(raw)) {
    // 아트 §28: rooms[]{index,id,name,x,y,r} — 방 id 는 순서로 대응하므로 index 순서로 둔다
    const sorted = [...raw].sort((a, b) => {
      const ia = (a as { index?: unknown })?.index;
      const ib = (b as { index?: unknown })?.index;
      return (typeof ia === 'number' ? ia : 0) - (typeof ib === 'number' ? ib : 0);
    });
    for (const r of sorted) {
      if (!r || typeof r !== 'object') continue;
      const o = r as Record<string, unknown>;
      const c = (o.center ?? o.pos) as { x?: unknown; y?: unknown } | unknown[] | undefined;
      if (Array.isArray(c)) push(o.id, c[0], c[1]);
      else if (c && typeof c === 'object') push(o.id, (c as { x?: unknown }).x, (c as { y?: unknown }).y);
      else if (typeof o.w === 'number' && typeof o.h === 'number' && typeof o.x === 'number' && typeof o.y === 'number')
        push(o.id, o.x + o.w / 2, o.y + o.h / 2);
      else push(o.id, o.x, o.y);
    }
  } else if (raw && typeof raw === 'object') {
    for (const [id, v] of Object.entries(raw as Record<string, unknown>)) {
      if (Array.isArray(v)) push(id, v[0], v[1]);
      else if (v && typeof v === 'object') push(id, (v as { x?: unknown }).x, (v as { y?: unknown }).y);
    }
  }
  return out;
}

/**
 * 대체 배치 (그림 메타가 없을 때): 두루마리 위 뱀 길 — 위 줄 왼쪽 → 오른쪽, 아래 줄 오른쪽 → 왼쪽 (넷씩).
 * 8개가 넘으면 줄을 늘린다.
 */
export function fallbackSpots(ids: readonly string[]): MapSpot[] {
  const perRow = 4;
  const rows = Math.max(1, Math.ceil(ids.length / perRow));
  return ids.map((id, i) => {
    const r = Math.floor(i / perRow);
    const c = i % perRow;
    const col = r % 2 === 0 ? c : perRow - 1 - c;
    const u = 0.14 + (col / (perRow - 1)) * 0.72;
    const v = rows === 1 ? 0.5 : 0.3 + (r / (rows - 1)) * 0.44 + (c % 2 === 0 ? -0.03 : 0.03);
    return { id, u, v };
  });
}

/**
 * 메뉴 줄 방 id 순서대로 자리를 짝짓는다: 같은 id → 같은 순서의 메타 자리(아트 지도 id 는 스토리 id 와 달라 순서로 대응) →
 * 대체 자리. 돌려주는 id 는 메뉴의 방 id
 */
export function spotsFor(ids: readonly string[], meta: readonly MapSpot[]): MapSpot[] {
  const fb = fallbackSpots(ids);
  return ids.map((id, i) => {
    const m = meta.find((x) => x.id === id) ?? meta[i];
    return m ? { id, u: m.u, v: m.v } : fb[i];
  });
}
