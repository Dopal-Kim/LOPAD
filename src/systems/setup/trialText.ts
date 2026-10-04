/**
 * 회피 시험 자리표시 문구 조립 (Phaser 없음): 과제 카드 · 진행 줄 · 과제 결과 한 줄 · 전체 결과.
 * 문구 원본은 `DODGE_TRIAL.TEXT`·`TASKS[id].name/hint` (스토리·UI 파트 교체 대상).
 */
import { DODGE_TRIAL, TASK_IDS, type TaskResult, type TrialResult } from '../dodgeTrial/dodgeTrial';
import { fill } from '../story';
import type { TrialStatus } from '../dodgeTrial/dodgeTrialRunner';

const T = DODGE_TRIAL.TEXT;

/** 과제 결과 표시 */
export function taskMark(r: TaskResult): string {
  if (r.skipped) return T.MARK.skipped;
  if (r.fell) return T.MARK.fell;
  if (r.hits === 0) return T.MARK.clean;
  return fill(T.MARK.hits, { hits: r.hits });
}

/** "n. 이름 — 결과" */
export function taskLine(r: TaskResult): string {
  const i = TASK_IDS.indexOf(r.id);
  return fill(T.TASK_LINE, { n: i + 1, name: DODGE_TRIAL.TASKS[r.id].name, mark: taskMark(r) });
}

/** 제목 카드 (첫 과제는 조작 안내 포함) */
export function cardText(st: TrialStatus): string {
  const def = DODGE_TRIAL.TASKS[st.task];
  const head = fill(T.CARD, { n: st.index + 1, total: st.total, name: def.name });
  return `${head}\n\n${def.hint}${st.index === 0 ? `\n\n${T.CONTROLS}` : ''}`;
}

/** 위쪽 진행 줄 (정비·과제 중) */
export function statusLine(st: TrialStatus): string {
  const vars = { n: st.index + 1, total: st.total, name: DODGE_TRIAL.TASKS[st.task].name, hits: st.hits };
  if (st.phase === 'prep') return fill(T.PREP, vars);
  if (st.phase === 'run') return fill(T.RUN, vars);
  return '';
}

/** 전체 결과: 과제별 한 줄 + 한 마디 + 등급·시작 감각 */
export function resultText(r: TrialResult): string {
  return fill(T.RESULT, {
    lines: r.tasks.map(taskLine).join('\n'),
    line: T.LINES[r.grade],
    grade: r.grade,
    bonus: r.bonus,
  });
}
