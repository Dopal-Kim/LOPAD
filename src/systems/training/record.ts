/**
 * 61 단계 6 (P14 §1) 수련장 기록·스냅샷 — 순수 규칙 (메타 `diary.training`, 계약 UI §19 `UiTraining`).
 * 런과 무관: 도장·과제 진행만 일기장에 남는다. 도장이 찍힌 방은 다시 들어오면 새 목록(손은 또 해도 된다).
 */
import type { UiTraining, UiTrainingRoom, UiVerbSlot } from '../../contract/ui';
import type { TrainingRecord } from '../narrative/diary';

/** 과제 완료 기록 (도장 전 방만 진행을 남긴다) */
export function recordTaskDone(r: TrainingRecord, room: string, task: string): TrainingRecord {
  if (r.stamped.includes(room)) return r;
  const cur = r.progress[room] ?? [];
  if (cur.includes(task)) return r;
  return { ...r, progress: { ...r.progress, [room]: [...cur, task] } };
}

/** 도장 (방 과제를 모두 마침) — 진행은 비운다 */
export function recordStamp(r: TrainingRecord, room: string): TrainingRecord {
  const progress = { ...r.progress };
  delete progress[room];
  return { ...r, stamped: r.stamped.includes(room) ? r.stamped : [...r.stamped, room], progress };
}

export function recordVisit(r: TrainingRecord): TrainingRecord {
  return { ...r, visits: r.visits + 1 };
}

export function recordOffered(r: TrainingRecord): TrainingRecord {
  return r.offered ? r : { ...r, offered: true };
}

/** 이번 방문의 시작 진행: 도장 전이면 남긴 진행, 도장 뒤면 새 목록 */
export function startProgress(r: TrainingRecord, room: string): string[] {
  return r.stamped.includes(room) ? [] : [...(r.progress[room] ?? [])];
}

export function allStamped(r: TrainingRecord, rooms: readonly string[]): boolean {
  return rooms.every((id) => r.stamped.includes(id));
}

/** 계약 §19 스냅샷 조립 */
export function buildTrainingUi(a: {
  room: string;
  roomName: string;
  line?: string;
  tasks: { id: string; label: string; done: boolean; verb?: UiVerbSlot }[];
  record: TrainingRecord;
  rooms: readonly { id: string; name: string }[];
  mapKey?: string;
}): UiTraining {
  const rooms: UiTrainingRoom[] = a.rooms.map((r) => ({
    id: r.id,
    name: r.name,
    stamped: a.record.stamped.includes(r.id),
  }));
  return {
    room: a.room,
    roomName: a.roomName,
    tasks: a.tasks.map((t) => ({ ...t })),
    stamped: a.record.stamped.includes(a.room),
    rooms,
    ...(a.line ? { line: a.line } : {}),
    ...(a.mapKey ? { mapKey: a.mapKey } : {}),
  };
}
