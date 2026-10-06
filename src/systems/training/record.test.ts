import { describe, expect, it } from 'vitest';
import { emptyTrainingRecord, readDiary, readTrainingRecord } from '../narrative/diary';
import { allStamped, buildTrainingUi, recordStamp, recordTaskDone, startProgress } from './record';

describe('수련장 기록 (diary.training)', () => {
  it('과제 진행 → 도장 → 다시 들어오면 새 목록', () => {
    let r = emptyTrainingRecord();
    r = recordTaskDone(r, 'step', 'dash');
    r = recordTaskDone(r, 'step', 'dash');
    expect(r.progress.step).toEqual(['dash']);
    expect(startProgress(r, 'step')).toEqual(['dash']);
    r = recordStamp(r, 'step');
    expect(r.stamped).toEqual(['step']);
    expect(r.progress.step).toBeUndefined();
    expect(startProgress(r, 'step')).toEqual([]);
    expect(recordTaskDone(r, 'step', 'move')).toBe(r);
    expect(allStamped(r, ['step'])).toBe(true);
    expect(allStamped(r, ['step', 'guard'])).toBe(false);
  });

  it('옛 메타(training 없음)·깨진 값은 빈 기록', () => {
    expect(readDiary({ runs: 2, clears: 0 }).training).toEqual(emptyTrainingRecord());
    expect(readTrainingRecord({ stamped: ['a', 3], progress: { b: 'x' }, offered: 1, visits: -2 })).toEqual({
      stamped: ['a'],
      progress: {},
      offered: false,
      visits: 0,
    });
  });

  it('스냅샷: 방 도장 · 지금 방 도장', () => {
    const r = recordStamp(emptyTrainingRecord(), 'guard');
    const ui = buildTrainingUi({
      room: 'guard',
      roomName: '막고 받아치기',
      tasks: [{ id: 'block', label: '막기 세 번', done: true, verb: 'signature' }],
      record: r,
      rooms: [
        { id: 'step', name: '걸음과 숨' },
        { id: 'guard', name: '막고 받아치기' },
      ],
    });
    expect(ui.stamped).toBe(true);
    expect(ui.rooms).toEqual([
      { id: 'step', name: '걸음과 숨', stamped: false },
      { id: 'guard', name: '막고 받아치기', stamped: true },
    ]);
  });
});
