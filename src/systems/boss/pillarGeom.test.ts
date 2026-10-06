import { describe, expect, it } from 'vitest';
import {
  firstBlocker,
  inflate,
  lineBlocked,
  newSteerMemo,
  segmentHitsBox,
  steerWaypoint,
  stepHidden,
} from './pillarGeom';

const pillar = { x: 100, y: 100, w: 32, h: 32 };

describe('61 P13 §3 기둥 기하', () => {
  it('선분이 기둥 안을 지나면 막힘 · 변에 스치기만 하면 통과', () => {
    expect(segmentHitsBox({ x: 50, y: 116 }, { x: 200, y: 116 }, pillar)).toBe(true);
    expect(segmentHitsBox({ x: 50, y: 100 }, { x: 200, y: 100 }, pillar)).toBe(false);
    expect(segmentHitsBox({ x: 50, y: 50 }, { x: 90, y: 90 }, pillar)).toBe(false);
    expect(segmentHitsBox({ x: 116, y: 50 }, { x: 116, y: 300 }, pillar)).toBe(true);
    // 길이 0 · 안쪽 점
    expect(segmentHitsBox({ x: 110, y: 110 }, { x: 110, y: 110 }, pillar)).toBe(true);
  });

  it('가려짐 = 보스 → 주인공 선분이 서 있는 기둥을 지남 · 가까운 기둥이 먼저', () => {
    const far = { x: 300, y: 100, w: 32, h: 32 };
    expect(lineBlocked({ x: 40, y: 116 }, { x: 160, y: 116 }, [pillar])).toBe(true);
    expect(lineBlocked({ x: 40, y: 40 }, { x: 160, y: 40 }, [pillar])).toBe(false);
    expect(firstBlocker({ x: 40, y: 116 }, { x: 400, y: 116 }, [far, pillar])).toBe(1);
  });

  it('가려짐 누적: 가려지면 쌓이고 보이면 decay 배로 줄어든다 (0 아래 없음)', () => {
    let h = 0;
    for (let i = 0; i < 10; i++) h = stepHidden(h, true, 100, 2);
    expect(h).toBe(1000);
    h = stepHidden(h, false, 200, 2);
    expect(h).toBe(600);
    expect(stepHidden(100, false, 500, 2)).toBe(0);
  });

  it('우회 조향: 기둥이 막으면 모서리로 돌아 주인공 쪽으로, 안 막히면 곧장', () => {
    const boxes = [inflate(pillar, 25, 18)];
    const memo = newSteerMemo();
    const O = { marginPx: 4, stickPx: 12, reachPx: 6 };
    // 주인공이 기둥 바로 뒤 (보스 정면 가로막힘), 살짝 아래
    const wp = steerWaypoint({ x: 20, y: 120 }, { x: 170, y: 118 }, boxes, memo, O);
    expect(wp.x).toBeLessThan(pillar.x);
    expect(wp.y > pillar.y + pillar.h || wp.y < pillar.y).toBe(true);
    // 모서리를 넘어가면 다음 모서리(같은 쪽 뒤) 를 거쳐 주인공으로
    const wp2 = steerWaypoint({ x: wp.x + 7, y: wp.y }, { x: 170, y: 118 }, boxes, memo, O);
    expect(wp2.x).toBeGreaterThan(pillar.x + pillar.w);
    // 열린 곳이면 곧장
    expect(steerWaypoint({ x: 20, y: 20 }, { x: 170, y: 20 }, boxes, newSteerMemo(), O)).toEqual({ x: 170, y: 20 });
  });

  it('우회 조향: 주인공이 기둥에 붙어 있으면(부풀린 사각형 안) 그 변 바깥 자리로 돌아간다', () => {
    const boxes = [inflate(pillar, 25, 18)];
    const O = { marginPx: 4, stickPx: 12, reachPx: 6 };
    // 주인공이 기둥 오른쪽에 붙음 → 보스는 왼쪽에서 위·아래 모서리로 돈다 (곧장 기둥으로 밀지 않음)
    const wp = steerWaypoint({ x: 30, y: 116 }, { x: 140, y: 116 }, boxes, newSteerMemo(), O);
    expect(wp.x).toBeLessThan(pillar.x);
    expect(wp.y < 82 || wp.y > 150).toBe(true);
    // 그 변 바깥 자리가 보이면 곧장 주인공에게
    expect(steerWaypoint({ x: 170, y: 60 }, { x: 140, y: 116 }, boxes, newSteerMemo(), O)).toEqual({ x: 140, y: 116 });
  });

  it('우회 조향 반복: 보스가 웨이포인트를 따라가면 주인공에게 닿는다 (기둥에 걸리지 않음)', () => {
    const boxes = [inflate(pillar, 25, 18)];
    for (const target of [
      { x: 170, y: 116 },
      { x: 116, y: 170 },
      { x: 165, y: 80 },
    ]) {
      const memo = newSteerMemo();
      let p = { x: 116 - (target.x - 116), y: 116 - (target.y - 116) };
      let reached = false;
      for (let i = 0; i < 400; i++) {
        const wp = steerWaypoint(p, target, boxes, memo, { marginPx: 4, stickPx: 12, reachPx: 6 });
        const dx = wp.x - p.x;
        const dy = wp.y - p.y;
        const d = Math.hypot(dx, dy);
        if (Math.hypot(target.x - p.x, target.y - p.y) < 4) {
          reached = true;
          break;
        }
        const step = Math.min(3, d);
        const next = { x: p.x + (dx / d) * step, y: p.y + (dy / d) * step };
        // 부풀린 기둥 안으로 들어가지 않는다 (모서리를 도는 순간 3px 안쪽 긁힘은 실제로는 물리 바디가 벽을 따라 미끄러진다)
        expect(segmentHitsBox(p, next, boxes[0], 3)).toBe(false);
        p = next;
      }
      expect(reached, JSON.stringify(target)).toBe(true);
    }
  });
});
