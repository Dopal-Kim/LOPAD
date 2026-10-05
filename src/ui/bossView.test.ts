import { describe, expect, it } from 'vitest';
import {
  breakLabelKey,
  candleGuides,
  normMarks,
  phaseNameOf,
  phaseStrip,
  readBoss,
  readBossBreak,
  readBossEvent,
  tickXs,
} from './bossView';

describe('readBoss', () => {
  it('계약 기본 필드만 와도 1층 기본 국면 이름·경계로 읽는다', () => {
    const b = readBoss({ name: '만취', hp: 500, maxHp: 1000, phase: 2 }, 0, '{n}국면');
    expect(b).toMatchObject({
      phase: 2,
      phaseName: '만취',
      marks: [0.65, 0.3],
      dark: false,
      candles: null,
      broken: null,
    });
    expect(b?.phaseNames).toEqual(['얼큰', '만취', '인사불성']);
  });
  it('시스템이 준 값이 먼저 (국면 이름·경계 퍼센트·무너짐·촛대·어둠)', () => {
    const b = readBoss(
      {
        name: 'X',
        hp: 10,
        maxHp: 100,
        phase: 3,
        phaseName: '바닥',
        phaseMarks: [30, 65, 0, 100],
        broken: { leftMs: 900, totalMs: 3000 },
        candles: [{ x: 1, y: 2, lit: true }, { x: 3, y: 4 }, { bad: 1 }],
        dark: false,
      },
      0,
      '{n}국면',
    );
    expect(b).toMatchObject({
      phaseName: '바닥',
      marks: [0.65, 0.3],
      broken: { leftMs: 900, totalMs: 3000 },
      dark: false,
    });
    expect(b?.candles).toEqual([
      { x: 1, y: 2, lit: true },
      { x: 3, y: 4, lit: false },
    ]);
  });
  it('1층 3국면은 어둠, 다른 층·이름 없음은 n국면, 쓰러졌으면 null', () => {
    expect(readBoss({ name: '만취', hp: 1, maxHp: 10, phase: 3 }, 0, '{n}국면')?.dark).toBe(true);
    expect(readBoss({ name: 'Y', hp: 1, maxHp: 10, phase: 2 }, 4, '{n}국면')).toMatchObject({
      phaseName: '2국면',
      marks: [],
      dark: false,
    });
    expect(readBoss({ name: '만취', hp: 0, maxHp: 10, phase: 3 }, 0, '{n}국면')).toBeNull();
    expect(readBoss(null, 0, '')).toBeNull();
  });
});

describe('국면 띠·눈금', () => {
  it('지난·지금·다음', () => {
    expect(phaseStrip(['얼큰', '만취', '인사불성'], 2).map((x) => x.state)).toEqual(['past', 'now', 'next']);
    expect(phaseNameOf(4, ['a'], '{n}국면')).toBe('4국면');
  });
  it('눈금 x 는 정수, 체력이 지나간 눈금은 passed', () => {
    expect(tickXs([0.65, 0.3], 100, 310, 0.5)).toEqual([
      { x: 302, passed: true },
      { x: 193, passed: false },
    ]);
    expect(normMarks(undefined, 9)).toEqual([]);
  });
});

describe('candleGuides', () => {
  const screen = { w: 960, h: 540 };
  it('화면 안은 표지, 밖은 가장자리 화살 (가까운 것부터, 켜진 것 제외)', () => {
    const g = candleGuides(
      [
        { x: 1200, y: 270, lit: false },
        { x: 500, y: 300, lit: false },
        { x: 100, y: 100, lit: true },
      ],
      screen,
      20,
    );
    expect(g).toHaveLength(2);
    expect(g[0]).toEqual({ kind: 'mark', x: 500, y: 300 });
    expect(g[1]).toMatchObject({ kind: 'arrow', x: 940, y: 270, dx: 1, dy: 0 });
  });
  it('위쪽 밖은 위 가장자리에', () => {
    const [a] = candleGuides([{ x: 480, y: -400, lit: false }], screen, 20);
    expect(a).toMatchObject({ kind: 'arrow', x: 480, y: 20 });
    expect(candleGuides(null, screen, 20)).toEqual([]);
  });
});

describe('파훼·보스 이벤트', () => {
  it('파훼 종류와 결정타', () => {
    expect(readBossBreak({ kind: 'cup' })).toMatchObject({ kind: 'cup', finisher: false, label: null });
    expect(readBossBreak({ kind: 'finisher', text: '끝' })).toMatchObject({ finisher: true, text: '끝' });
    expect(readBossBreak({ kind: 'weird', label: '이상' })).toMatchObject({ kind: 'other', label: '이상' });
    expect(readBossBreak(3)).toBeNull();
    expect(breakLabelKey('pillar')).toBe('breakPillar');
    expect(breakLabelKey('other')).toBe('breakAny');
  });
  it('BOSS_* 페이로드', () => {
    expect(readBossEvent({ name: '만취', phase: 3, finisher: true })).toEqual({
      name: '만취',
      phase: 3,
      phaseName: null,
      finisher: true,
    });
    expect(readBossEvent(undefined)).toEqual({ name: '', phase: 1, phaseName: null, finisher: false });
  });
});
