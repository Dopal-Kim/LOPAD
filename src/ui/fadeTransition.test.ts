import { describe, expect, it } from 'vitest';
import { FADE } from './themeTransition';
import { fadeCoverMs, inkCoverAlpha, inkEdgeOrder, planFor, readBegin, revealAlpha } from './transitionView';
import { noteTransitionMode, recentTransitionMode } from './transitionState';

describe("62 루프 3 UI G 짧은 먹 번짐 암전 ('fade')", () => {
  it("시작 페이로드: mode 'fade' · durationMs 읽기 (0·음수·글자는 없음)", () => {
    expect(readBegin({ id: 1, mode: 'fade', durationMs: 420 })?.durationMs).toBe(420);
    expect(readBegin({ id: 1, mode: 'fade' })?.mode).toBe('fade');
    expect(readBegin({ id: 1, mode: 'fade', durationMs: 0 })?.durationMs).toBeNull();
    expect(readBegin({ id: 1, mode: 'fade', durationMs: '400' })?.durationMs).toBeNull();
  });

  it('단계: 덮기 0.25~0.6초(시스템 값은 잘라 씀) · 걷힘 0.3초 · 액자·파고들기 없음', () => {
    const p = planFor('fade');
    expect(p.introMs).toBe(FADE.coverMs);
    expect(p.frameMs).toBe(0);
    expect(p.moveMs).toBe(0);
    expect(p.revealMs).toBe(300);
    expect(planFor('fade', 400).introMs).toBe(400);
    expect(fadeCoverMs(50)).toBe(FADE.minCoverMs);
    expect(fadeCoverMs(5000)).toBe(FADE.maxCoverMs);
    expect(FADE.coverMs).toBeGreaterThanOrEqual(300);
    expect(FADE.coverMs).toBeLessThanOrEqual(450);
  });

  it('먹 순서: 가장자리가 먼저(작음), 가운데가 마지막(큼), 0~1', () => {
    const w = 96;
    const h = 54;
    const o = inkEdgeOrder(w, h, 7);
    let edge = 0;
    let center = 0;
    for (let x = 0; x < w; x++) edge += o[x] + o[(h - 1) * w + x];
    edge /= w * 2;
    for (let y = h / 2 - 3; y < h / 2 + 3; y++) for (let x = w / 2 - 3; x < w / 2 + 3; x++) center += o[y * w + x];
    center /= 36;
    expect(edge).toBeLessThan(0.3);
    expect(center).toBeGreaterThan(0.7);
    for (const v of o) {
      expect(v).toBeGreaterThanOrEqual(0);
      expect(v).toBeLessThanOrEqual(1);
    }
    // 같은 씨앗이면 같은 모양
    expect(inkEdgeOrder(w, h, 7)).toEqual(o);
  });

  it('덮개 알파: t 0 = 하나도 안 덮임, t 1 = 다 덮임, 중간엔 가장자리부터', () => {
    for (const ord of [0, 0.3, 0.7, 1]) {
      expect(inkCoverAlpha(ord, 0)).toBe(0);
      expect(inkCoverAlpha(ord, 1)).toBe(1);
    }
    expect(inkCoverAlpha(0.1, 0.5)).toBeGreaterThan(inkCoverAlpha(0.9, 0.5));
    // 걷힘은 (1 − 순서) — 가운데(순서 1)가 먼저 걷힌다
    expect(revealAlpha(1 - 0.95, 0.5, FADE.soft)).toBeLessThan(revealAlpha(1 - 0.05, 0.5, FADE.soft));
  });

  it("마지막 전환 종류: 'fade' 를 몇 초 안에만 기억한다 (지역 카드 → 띠만)", () => {
    noteTransitionMode('fade', 1000);
    expect(recentTransitionMode(2000)).toBe('fade');
    expect(recentTransitionMode(7000)).toBeNull();
    noteTransitionMode('floor', 8000);
    expect(recentTransitionMode(8100)).toBe('floor');
  });
});
