import { describe, expect, it } from 'vitest';
import {
  bodyFrame,
  dirIndex,
  inPolygon,
  clampName,
  newCharIndexes,
  parseHint,
  pushPoint,
  readRitual,
  ritualRebuild,
  sealStates,
} from './ritualView';

describe('parseHint (62 P0-2 의식 안내 줄)', () => {
  it('대괄호 키와 동작을 · 로 나눈다', () => {
    expect(parseHint('[Enter] 덧쓴다 · [R] 획을 다시 긋는다')).toEqual([
      { keys: ['Enter'], label: '덧쓴다' },
      { keys: ['R'], label: '획을 다시 긋는다' },
    ]);
  });
  it('키 여럿·키 없는 글·빈 값', () => {
    expect(parseHint('[W][S] 걷는다 · 마우스를 누른 채 긋고, 떼면 한 획')).toEqual([
      { keys: ['W', 'S'], label: '걷는다' },
      { keys: [], label: '마우스를 누른 채 긋고, 떼면 한 획' },
    ]);
    expect(parseHint('')).toEqual([]);
    expect(parseHint(undefined)).toEqual([]);
  });
});

describe('이름 칸', () => {
  it('최대 글자 수까지 자르고 앞 공백·줄바꿈을 지운다', () => {
    expect(clampName('  도영\n', 8)).toBe('도영 ');
    expect(clampName('가나다라마바사아자차', 8)).toBe('가나다라마바사아');
  });
  it('새로 적힌 글자 (조합 중인 마지막 글자 포함)', () => {
    expect(newCharIndexes('', '도')).toEqual([0]);
    expect(newCharIndexes('도', '도여')).toEqual([1]);
    expect(newCharIndexes('도여', '도영')).toEqual([1]);
    expect(newCharIndexes('도영', '도')).toEqual([]);
  });
});

describe('먹 붓 획', () => {
  it('가까운 점은 버리고 상한을 지킨다', () => {
    const pts: { x: number; y: number; t: number }[] = [];
    expect(pushPoint(pts, { x: 0, y: 0, t: 0 }, 2, 3)).toBe(true);
    expect(pushPoint(pts, { x: 1, y: 0, t: 5 }, 2, 3)).toBe(false);
    expect(pushPoint(pts, { x: 3, y: 0, t: 9 }, 2, 3)).toBe(true);
    expect(pushPoint(pts, { x: 6, y: 0, t: 12 }, 2, 3)).toBe(true);
    expect(pushPoint(pts, { x: 9, y: 0, t: 15 }, 2, 3)).toBe(false);
    expect(pts.map((p) => p.x)).toEqual([0, 3, 6]);
  });
});

describe('의식 상태', () => {
  it('모양이 맞을 때만 읽고, 단계가 바뀌면 다시 짠다', () => {
    expect(readRitual(null)).toBeNull();
    expect(readRitual({ phase: 'oops', lives: 0 })).toBeNull();
    const a = readRitual({ phase: 'name', lives: 0 });
    expect(a?.phase).toBe('name');
    expect(ritualRebuild(null, a)).toBe(true);
    expect(ritualRebuild(a, { phase: 'name', lives: 0 })).toBe(false);
    expect(ritualRebuild(a, { phase: 'strokes', lives: 0 })).toBe(true);
  });
  it('낙관 칸', () => {
    expect(sealStates(0, 3)).toEqual(['now', 'todo', 'todo']);
    expect(sealStates(2, 3)).toEqual(['done', 'done', 'now']);
    expect(sealStates(3, 3)).toEqual(['done', 'done', 'done']);
  });
});

describe('먹 화폭 (ritualBrush 계산)', () => {
  it('진행 방향 칸·속도별 붓·다각형 안', () => {
    expect(dirIndex(1, 0)).toBe(0);
    expect(dirIndex(0, 1)).toBe(2);
    expect(dirIndex(-1, 0)).toBe(4);
    expect(dirIndex(0, -1)).toBe(6);
    expect(bodyFrame(0, 0)).toBe('tip_d10');
    expect(bodyFrame(5, 3)).toBe('dry_d6_r3');
    const sq = [
      [0, 0],
      [10, 0],
      [10, 10],
      [0, 10],
    ] as const;
    expect(inPolygon(5, 5, sq)).toBe(true);
    expect(inPolygon(15, 5, sq)).toBe(false);
  });
});
