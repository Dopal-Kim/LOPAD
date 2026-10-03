import { describe, expect, it } from 'vitest';
import { TASK_IDS, emptyTaskResult, gradeTrial, presetResults } from '../dodgeTrial';
import { cardText, resultText, statusLine, taskLine, taskMark } from './trialText';
import type { TrialStatus } from '../dodgeTrialRunner';

const st = (over: Partial<TrialStatus>): TrialStatus => ({
  phase: 'card',
  index: 0,
  task: 'lines',
  total: 5,
  hits: 0,
  results: [],
  progress: 0,
  fell: false,
  ...over,
});

describe('회피 시험 문구 (51라운드)', () => {
  it('과제 결과 표시: 무피격 · 피격 n · 떨어짐 · 건너뜀', () => {
    expect(taskMark(emptyTaskResult('lines'))).toBe('무피격');
    expect(taskMark({ ...emptyTaskResult('lines'), hits: 2 })).toBe('피격 2');
    expect(taskMark({ ...emptyTaskResult('lines'), hits: 2, fell: true })).toContain('떨어짐');
    expect(taskMark({ ...emptyTaskResult('lines'), skipped: true })).toBe('건너뜀');
    expect(taskLine({ ...emptyTaskResult('wall'), hits: 1 })).toMatch(/^4\. .+ — 피격 1$/);
  });
  it('첫 카드만 조작 안내, 진행 줄에 과제 번호·피격', () => {
    expect(cardText(st({}))).toContain('WASD');
    expect(cardText(st({ index: 1, task: 'ring' }))).not.toContain('WASD');
    expect(cardText(st({ index: 1, task: 'ring' }))).toContain('과제 2 / 5');
    expect(statusLine(st({ phase: 'run', index: 2, task: 'homing', hits: 3 }))).toContain('피격 3');
    expect(statusLine(st({ phase: 'card' }))).toBe('');
  });
  it('전체 결과: 과제별 한 줄씩 + 등급·시작 감각', () => {
    const text = resultText(gradeTrial(presetResults('B')));
    for (let i = 1; i <= TASK_IDS.length; i++) expect(text).toContain(`${i}. `);
    expect(text).toContain('등급 B');
    expect(text).toContain('시작 감각 +1');
  });
});
