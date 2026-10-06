import { describe, expect, it } from 'vitest';
import type { UiTraining, UiWeaponVerbs } from '../contract/ui';
import {
  doneCount,
  fallbackSpots,
  isTrainingHall,
  newlyDone,
  readMapRooms,
  readStampEvent,
  readTaskEvent,
  spotsFor,
  taskRows,
  trainingOf,
} from './trainingView';

const room = (over: Partial<UiTraining> = {}): UiTraining => ({
  room: 'steps',
  roomName: '걸음과 숨',
  tasks: [
    { id: 'move', label: '걸어 본다', done: true },
    { id: 'dash', label: '굴러 본다', done: false, verb: 'dash' },
    { id: 'hold', label: '길게 눌러 본다', done: false, verb: 'hold' },
  ],
  stamped: false,
  rooms: [{ id: 'steps', name: '걸음과 숨', stamped: false }],
  ...over,
});

describe('trainingView (61 단계 6 수련장 UI)', () => {
  it('수련장 스냅샷 · 마당', () => {
    expect(trainingOf({})).toBeNull();
    expect(trainingOf({ training: null })).toBeNull();
    expect(trainingOf({ training: room() })?.room).toBe('steps');
    expect(isTrainingHall(room({ room: 'hall', tasks: [] }))).toBe(true);
    expect(isTrainingHall(room())).toBe(false);
  });

  it('과제 줄: verb 는 지금 무기 키, 없으면 기본 키', () => {
    const verbs: UiWeaponVerbs = {
      weapon: '칼',
      verbs: [{ slot: 'dash', key: 'Space', name: '대쉬 · 일섬', hint: '', branch: null }],
    };
    const rows = taskRows(room(), verbs);
    expect(rows.map((r) => r.key)).toEqual([null, 'Space', '좌클릭 길게']);
    expect(rows[0].done).toBe(true);
    expect(doneCount(room())).toEqual({ done: 1, total: 3 });
  });

  it('새로 끝난 과제: 같은 방에서만', () => {
    const t = room({
      tasks: [
        { id: 'move', label: '', done: true },
        { id: 'dash', label: '', done: true },
      ],
    });
    expect(newlyDone('steps', new Set(['move']), t)).toEqual(['dash']);
    expect(newlyDone('guard', new Set(), t)).toEqual([]);
  });

  it('이벤트 읽기', () => {
    expect(readTaskEvent({ room: 'steps', id: 'dash', label: '굴러 본다' })).toEqual({
      room: 'steps',
      id: 'dash',
      label: '굴러 본다',
    });
    expect(readTaskEvent({ room: 'x' })).toBeNull();
    expect(readStampEvent({ room: 'steps', name: '걸음과 숨', all: true })).toEqual({
      room: 'steps',
      name: '걸음과 숨',
      all: true,
    });
    expect(readStampEvent(null)).toBeNull();
  });

  it('지도 방 자리: 그림 메타(픽셀·비율·사각형·사전) 또는 뱀 길 대체', () => {
    expect(readMapRooms({ rooms: [{ id: 'a', x: 320, y: 90 }] }, 640, 360)).toEqual([{ id: 'a', u: 0.5, v: 0.25 }]);
    expect(readMapRooms({ rooms: [{ id: 'a', x: 0.2, y: 0.4 }] }, 640, 360)).toEqual([{ id: 'a', u: 0.2, v: 0.4 }]);
    expect(readMapRooms({ rooms: [{ id: 'a', x: 300, y: 80, w: 40, h: 20 }] }, 640, 360)).toEqual([
      { id: 'a', u: 0.5, v: 0.25 },
    ]);
    expect(readMapRooms({ rooms: { a: [320, 180] } }, 640, 360)).toEqual([{ id: 'a', u: 0.5, v: 0.5 }]);
    expect(readMapRooms(null, 640, 360)).toEqual([]);
    const ids = ['1', '2', '3', '4', '5', '6', '7', '8'];
    const fb = fallbackSpots(ids);
    expect(fb).toHaveLength(8);
    for (const s of fb) {
      expect(s.u).toBeGreaterThan(0.05);
      expect(s.u).toBeLessThan(0.95);
      expect(s.v).toBeGreaterThan(0.1);
      expect(s.v).toBeLessThan(0.9);
    }
    // 뱀 길: 다섯째는 넷째 아래 (같은 열)
    expect(fb[4].u).toBeCloseTo(fb[3].u);
    expect(fb[4].v).toBeGreaterThan(fb[3].v);
    const mixed = spotsFor(['a', 'b', 'c'], [{ id: 'b', u: 0.9, v: 0.9 }]);
    expect(mixed[1]).toEqual({ id: 'b', u: 0.9, v: 0.9 });
    // 'a' 는 같은 id 가 없어 같은 순서(0번) 메타 자리
    expect(mixed[0]).toEqual({ id: 'a', u: 0.9, v: 0.9 });
    expect(mixed[2].id).toBe('c');
    // index 순서로 정렬 (아트 지도 id 'breath' = 스토리 'step')
    const ordered = readMapRooms(
      {
        rooms: [
          { index: 1, id: 'guard', x: 0.6, y: 0.5 },
          { index: 0, id: 'breath', x: 0.2, y: 0.5 },
        ],
      },
      960,
      540,
    );
    expect(spotsFor(['step', 'guard'], ordered).map((x) => x.u)).toEqual([0.2, 0.6]);
  });
});
