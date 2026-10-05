/**
 * 61라운드 점검 #5·#6 보스 등장·처치 연출의 시간표 (Phaser 의존 없음 — scenes/game/BossFlow 가 매 프레임 꺼내 쓴다).
 * 수치는 data/bosses.json `show` (형식 data/bossShowTypes.ts). 대사 키 → 문장 풀이도 여기.
 */
import { BREAK_LINE_KEY, type BossDefeatShow, type BossIntroShow, type BossLines } from '../../data/bossShowTypes';
import type { BreakKind } from '../../data/bundle2Types';

export type IntroStep = 'pan' | 'floorLine' | 'speech' | 'return' | 'fight';
export type DefeatStep = 'hit' | 'slowStart' | 'slowEnd' | 'speech' | 'fallen' | 'reward';

export interface ShowStep<S extends string> {
  atMs: number;
  step: S;
}

/** 시각 순 (같은 시각이면 목록 순서 — 정렬이 안정적) */
function sorted<S extends string>(list: ShowStep<S>[]): ShowStep<S>[] {
  return list
    .map((s, i) => ({ s, i }))
    .sort((a, b) => a.s.atMs - b.s.atMs || a.i - b.i)
    .map((x) => x.s);
}

/** 등장: 카메라 보스로 → 층 등장 자막 → 등장 대사 → 카메라 복귀 → 전투 */
export function introSteps(I: BossIntroShow): ShowStep<IntroStep>[] {
  return sorted<IntroStep>([
    { atMs: 0, step: 'pan' },
    { atMs: I.floorLineAtMs, step: 'floorLine' },
    { atMs: I.speechAtMs, step: 'speech' },
    { atMs: I.returnAtMs, step: 'return' },
    { atMs: I.fightAtMs, step: 'fight' },
  ]);
}

/** 처치: 일격(히트스톱·섬광·흔들림) → 슬로모 → 쓰러짐 대사 → 무기 한마디 자리 → 보상 */
export function defeatSteps(D: BossDefeatShow): ShowStep<DefeatStep>[] {
  return sorted<DefeatStep>([
    { atMs: 0, step: 'hit' },
    { atMs: D.hitstopMs, step: 'slowStart' },
    { atMs: D.hitstopMs + D.slowMs, step: 'slowEnd' },
    { atMs: D.speechAtMs, step: 'speech' },
    { atMs: D.fallenAtMs, step: 'fallen' },
    { atMs: D.rewardAtMs, step: 'reward' },
  ]);
}

/** 시간표 진행기: elapsed 까지 도달한 단계를 한 번씩 꺼낸다 */
export class StepClock<S extends string> {
  private i = 0;

  constructor(private readonly steps: readonly ShowStep<S>[]) {}

  due(elapsedMs: number): S[] {
    const out: S[] = [];
    while (this.i < this.steps.length && this.steps[this.i].atMs <= elapsedMs) out.push(this.steps[this.i++].step);
    return out;
  }

  get done(): boolean {
    return this.i >= this.steps.length;
  }

  /** 마지막 단계 시각 (ms) */
  get lengthMs(): number {
    return this.steps.length > 0 ? this.steps[this.steps.length - 1].atMs : 0;
  }
}

/** story.json 의 대사 묶음 (linesKey) — 형식이 맞지 않으면 undefined */
export function bossLinesOf(story: object, key: string | undefined): BossLines | undefined {
  if (!key) return undefined;
  const v = (story as Record<string, unknown>)[key];
  return v && typeof v === 'object' && typeof (v as BossLines).speaker === 'string' ? (v as BossLines) : undefined;
}

/** 대사 키: 'intro' · 'phase2' · 'phase3' · 'defeat' · 'break.<파훼 종류>' → 문장 (없으면 null) */
export function speechText(lines: BossLines | undefined, key: string): string | null {
  if (!lines) return null;
  if (key.startsWith('break.')) {
    const kind = key.slice('break.'.length);
    const t = lines.break?.[BREAK_LINE_KEY[kind as BreakKind] ?? kind];
    return typeof t === 'string' && t ? t : null;
  }
  const t = (lines as unknown as Record<string, unknown>)[key];
  return typeof t === 'string' && t ? t : null;
}
