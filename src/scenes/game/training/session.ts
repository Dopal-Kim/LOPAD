/**
 * 61 단계 6 (P14 §1) 수련장 세션 — 씬 재시작을 넘어 남는 것: 어디서 왔나(타이틀·첫 생 선택·런) · 맡겨 둔 런 · 기본 무기.
 * 런을 맡길 때는 gameState 의 필드를 얕게 떠 둔다(startRun 이 하위 객체를 새로 만들므로 원래 객체는 그대로 남는다).
 * 수련장은 세이브·게이지·전표에 손대지 않는다 — 나가면 맡겨 둔 값을 그대로 되돌린다.
 */
import { gameState } from '../../../core/GameState';
import type { KillKind } from '../../../systems/senses';

export type TrainingOrigin = 'title' | 'setup' | 'run';

export interface RunStash {
  fields: Record<string, unknown>;
  senses: { sense: number; kinds: KillKind[] };
}

export const trainingSession: { origin: TrainingOrigin; stash: RunStash | null; weapon: string | null } = {
  origin: 'title',
  stash: null,
  weapon: null,
};

/** 지금 런을 맡긴다 (gameState 얕은 사본 + 감각) */
export function stashRun(): RunStash {
  const fields = { ...(gameState as unknown as Record<string, unknown>) };
  delete fields.senses;
  return { fields, senses: gameState.senses.snapshot() };
}

/** 맡긴 런을 되돌린다 */
export function restoreRun(s: RunStash): void {
  const target = gameState as unknown as Record<string, unknown>;
  for (const [k, v] of Object.entries(s.fields)) target[k] = v;
  gameState.senses.restore(s.senses);
}
