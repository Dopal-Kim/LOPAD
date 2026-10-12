import { describe, expect, it } from 'vitest';
import { estimateProgress, parseTips, pickTip, readLoadProgress, shownProgress } from './loadingView';
import { parsePrefs, textScaleOf } from './uiPrefs';

describe('loadingView (62 루프 2 P2-6)', () => {
  it('로드 진행 페이로드', () => {
    expect(readLoadProgress(null)).toBeNull();
    expect(readLoadProgress({})).toBeNull();
    expect(readLoadProgress({ progress: 0.4, region: ' outer ' })).toEqual({
      progress: 0.4,
      done: false,
      region: 'outer',
    });
    expect(readLoadProgress({ progress: 2 })).toMatchObject({ progress: 1, done: true });
    expect(readLoadProgress({ done: true })).toMatchObject({ progress: 1, done: true });
    // 미리 읽기는 화면을 막지 않는다
    expect(readLoadProgress({ phase: 'prefetch', progress: 0.2, done: false })).toBeNull();
  });

  it('시간 어림은 상한 앞에서 멈추고, 보이는 값은 뒤로 가지 않는다', () => {
    expect(estimateProgress(0)).toBe(0);
    expect(estimateProgress(1600)).toBeCloseTo(0.9 * (1 - Math.exp(-1)));
    expect(estimateProgress(1e6)).toBeLessThanOrEqual(0.9);
    expect(shownProgress(null, 0.3)).toBe(0.3);
    expect(shownProgress(0.6, 0.3)).toBe(0.6);
    expect(shownProgress(0.2, 0.3, 0.5)).toBe(0.5);
  });

  it('팁: 줄바꿈으로 나누고 차례로 돌린다', () => {
    const t = parseTips('가\n\n 나 \n다');
    expect(t).toEqual(['가', '나', '다']);
    expect(pickTip(t, 4)).toBe('나');
    expect(pickTip(t, -1)).toBe('다');
    expect(pickTip([], 3)).toBe('');
  });
});

describe('uiPrefs (62 루프 2 P1-16 글자 크기)', () => {
  it('저장 글 읽기 · 배율', () => {
    expect(parsePrefs(null)).toEqual({ textSize: 'normal' });
    expect(parsePrefs('{"textSize":"large"}')).toEqual({ textSize: 'large' });
    expect(parsePrefs('{"textSize":"huge"}')).toEqual({ textSize: 'normal' });
    expect(parsePrefs('not json')).toEqual({ textSize: 'normal' });
    expect(textScaleOf('large')).toBe(1.5);
    expect(textScaleOf('normal')).toBe(1);
  });
});
