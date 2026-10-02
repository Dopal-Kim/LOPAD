import { describe, expect, it } from 'vitest';
import { bubblePos, cardFocusMove, formatSec, holdSec, timerRatio, withControlExtras } from './structView';

const EXTRAS = [
  { token: /(^|[\s·])E(\s|$)/, text: 'E 상호작용' },
  { token: /Shift/i, text: 'Shift 달리기' },
  { token: /Tab/i, text: 'Tab 워프' },
];

describe('withControlExtras', () => {
  it('빠진 키만 덧붙인다', () => {
    expect(withControlExtras('WASD 이동 · Esc 일시정지', EXTRAS)).toBe(
      'WASD 이동 · Esc 일시정지 · E 상호작용 · Shift 달리기 · Tab 워프',
    );
  });
  it('이미 있으면 그대로 (Esc 의 E 는 E 키로 보지 않는다)', () => {
    const line = 'WASD 이동 · E 살핀다 · Shift 달린다 · Tab 지도';
    expect(withControlExtras(line, EXTRAS)).toBe(line);
  });
});

describe('bubblePos', () => {
  it('기준점 위 가운데', () => {
    expect(bubblePos({ x: 480, y: 300 }, 100, 40, 960, 540, 8, 4)).toEqual({ x: 430, y: 256 });
  });
  it('화면 밖으로 나가지 않는다', () => {
    expect(bubblePos({ x: 10, y: 10 }, 100, 40, 960, 540, 8, 4)).toEqual({ x: 8, y: 8 });
    expect(bubblePos({ x: 955, y: 600 }, 100, 40, 960, 540, 8, 4)).toEqual({ x: 852, y: 492 });
  });
});

describe('timer·sec', () => {
  it('timerRatio', () => {
    expect(timerRatio({})).toBeNull();
    expect(timerRatio({ remainMs: 5000, durationMs: 20000 })).toBe(0.25);
    expect(timerRatio({ remainMs: -1, durationMs: 100 })).toBe(0);
  });
  it('formatSec·holdSec', () => {
    expect(formatSec(12345)).toBe('12.3');
    expect(formatSec(-5)).toBe('0.0');
    expect(holdSec(2000)).toBe('2');
    expect(holdSec(1500)).toBe('1.5');
  });
});

describe('cardFocusMove', () => {
  it('좌우 순환, 아래는 그만두기, 위는 가운데 카드', () => {
    expect(cardFocusMove(0, 3, 'ArrowLeft')).toBe(2);
    expect(cardFocusMove(2, 3, 'd')).toBe(0);
    expect(cardFocusMove(1, 3, 'ArrowDown')).toBe(3);
    expect(cardFocusMove(3, 3, 'ArrowUp')).toBe(1);
    expect(cardFocusMove(3, 3, 'ArrowDown')).toBe(3);
  });
});
