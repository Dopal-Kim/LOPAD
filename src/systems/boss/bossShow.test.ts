import { describe, expect, it } from 'vitest';
import { BOSSES, STORY, validateBosses } from '../../data';
import type { BossTable } from '../../data/types';
import { StepClock, bossLinesOf, defeatSteps, introSteps, speechText } from './bossShow';

const SHOW = BOSSES.stage1.show!;

describe('61라운드 보스 등장·처치 시간표', () => {
  it('등장: 카메라 → 층 자막 → 등장 대사 → 복귀 → 전투 순서', () => {
    const steps = introSteps(SHOW.intro).map((s) => s.step);
    expect(steps).toEqual(['pan', 'floorLine', 'speech', 'return', 'fight']);
    const c = new StepClock(introSteps(SHOW.intro));
    expect(c.due(0)).toEqual(['pan']);
    expect(c.due(SHOW.intro.speechAtMs)).toEqual(['floorLine', 'speech']);
    expect(c.done).toBe(false);
    expect(c.due(1e9)).toEqual(['return', 'fight']);
    expect(c.done).toBe(true);
    expect(c.due(1e9)).toEqual([]);
  });

  it('처치: 일격 → 슬로모 → 대사 → 무기 한마디 자리 → 보상 (보상이 마지막)', () => {
    const steps = defeatSteps(SHOW.defeat);
    expect(steps[0].step).toBe('hit');
    expect(steps[steps.length - 1].step).toBe('reward');
    const at = Object.fromEntries(steps.map((s) => [s.step, s.atMs]));
    expect(at.slowStart).toBe(SHOW.defeat.hitstopMs);
    expect(at.slowEnd).toBeLessThanOrEqual(at.reward);
    expect(at.speech).toBeLessThan(at.fallen);
    expect(new StepClock(steps).lengthMs).toBe(SHOW.defeat.rewardAtMs);
  });

  it('대사: story.json linesKey 묶음 · 파훼 종류 → 대사 키 (reel = stumble)', () => {
    const L = bossLinesOf(STORY, BOSSES.stage1.linesKey);
    expect(L?.speaker).toBe('만취');
    for (const k of ['intro', 'phase2', 'phase3', 'defeat', 'break.cup', 'break.pillar', 'break.cask', 'break.reel'])
      expect(speechText(L, k), k).toBeTruthy();
    expect(speechText(L, 'break.nope')).toBeNull();
    expect(speechText(undefined, 'intro')).toBeNull();
    expect(bossLinesOf(STORY, 'nope')).toBeUndefined();
  });

  it('검증: 순서가 어긋난 처치 시간표 · 잘못된 배율은 오류', () => {
    const base = JSON.parse(JSON.stringify({ x: BOSSES.stage1 })) as BossTable;
    expect(() => validateBosses(base)).not.toThrow();
    const a = JSON.parse(JSON.stringify(base)) as BossTable;
    a.x.show!.defeat.rewardAtMs = 10;
    expect(() => validateBosses(a)).toThrow(/순서/);
    const b = JSON.parse(JSON.stringify(base)) as BossTable;
    b.x.breakDamageMult = 0.5;
    expect(() => validateBosses(b)).toThrow(/breakDamageMult/);
    const c = JSON.parse(JSON.stringify(base)) as BossTable;
    c.x.show!.defeat.slowScale = 2;
    expect(() => validateBosses(c)).toThrow(/slowScale/);
  });
});
