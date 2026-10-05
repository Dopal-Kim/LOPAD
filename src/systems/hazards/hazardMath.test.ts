import { describe, expect, it } from 'vitest';
import { ENEMIES } from '../../data';
import {
  advanceBarrel,
  bottleArcAt,
  circleHitsRect,
  clampThrowTarget,
  deflectDir,
  peddlerIntent,
  rollFrame,
} from './hazardMath';

describe('61라운드 단계 2 신규 적 투사체 계산', () => {
  it('화염 술병 포물선: 시작은 손 높이, 끝은 땅, 가운데가 꼭대기', () => {
    const from = { x: 0, y: 100 };
    const to = { x: 100, y: 100 };
    expect(bottleArcAt(0, from, to, 30, 10)).toEqual({ x: 0, y: 90, groundY: 100 });
    expect(bottleArcAt(1, from, to, 30, 10).y).toBeCloseTo(100);
    const mid = bottleArcAt(0.5, from, to, 30, 10);
    expect(mid.x).toBe(50);
    expect(mid.y).toBeCloseTo(100 - 30 - 5);
  });

  it('던질 자리는 사거리 [최소, 최대] 로 자른다', () => {
    expect(clampThrowTarget({ x: 0, y: 0 }, { x: 10, y: 0 }, 50, 200)).toEqual({ x: 50, y: 0 });
    expect(clampThrowTarget({ x: 0, y: 0 }, { x: 0, y: 500 }, 50, 200)).toEqual({ x: 0, y: 200 });
    expect(clampThrowTarget({ x: 0, y: 0 }, { x: 120, y: 0 }, 50, 200)).toEqual({ x: 120, y: 0 });
  });

  it('행상 이동 의도: 2칸 안 도망 · 3.5칸 안 물러남 · 5칸 밖 다가감 (data enemies.peddler.throw)', () => {
    const T = ENEMIES.peddler.throw!;
    expect(peddlerIntent(1.5, T)).toBe('flee');
    expect(peddlerIntent(3, T)).toBe('back');
    expect(peddlerIntent(4, T)).toBe('hold');
    expect(peddlerIntent(7, T)).toBe('close');
  });

  it('되치기 방향 = 공격 방향, 없으면 굴러오던 반대', () => {
    expect(deflectDir({ x: 1, y: 0 }, { x: 0, y: -3 })).toEqual({ x: 0, y: -1 });
    const back = deflectDir({ x: 1, y: 0 }, { x: 0, y: 0 });
    expect(back.x).toBe(-1);
    expect(Math.abs(back.y)).toBe(0);
  });

  it('술통 전진: 앞 가장자리가 막힌 칸에 닿으면 멈춘다', () => {
    const wallX = 50;
    const r = advanceBarrel({ x: 0, y: 0 }, { x: 1, y: 0 }, 100, 10, (x) => x >= wallX);
    expect(r.hit).toBe(true);
    expect(r.x + 10).toBeLessThan(wallX);
    expect(r.x).toBeGreaterThan(30);
    const free = advanceBarrel({ x: 0, y: 0 }, { x: 0, y: 1 }, 20, 10, () => false);
    expect(free).toEqual({ x: 0, y: 20, moved: 20, hit: false });
  });

  it('원·사각형 겹침 · 굴림 프레임', () => {
    expect(circleHitsRect({ x: 0, y: 0 }, 5, { x: 3, y: -2, w: 4, h: 4 })).toBe(true);
    expect(circleHitsRect({ x: 0, y: 0 }, 2, { x: 3, y: -2, w: 4, h: 4 })).toBe(false);
    expect(rollFrame(0, 50, 8)).toBe(0);
    expect(rollFrame(25, 50, 8)).toBe(4);
    expect(rollFrame(50, 50, 8)).toBe(0);
  });

  it('신규 적 데이터: 행상 쿨다운 2.6초·비행 0.7초·불 4초 · 짐꾼 술통 5칸/초·판정 0.34칸·쿨다운 3.2초 (아트 §23 제안값)', () => {
    const T = ENEMIES.peddler.throw!;
    expect([T.cooldownMs, T.flightMs, T.poolMs, T.keepMinTiles, T.keepMaxTiles, T.fleeTiles]).toEqual([
      2600, 700, 4000, 3.5, 5, 2,
    ]);
    const R = ENEMIES.porter.roll!;
    expect([R.speedTiles, R.radiusTiles, R.cooldownMs]).toEqual([5, 0.34, 3200]);
    for (const id of ['peddler', 'porter']) {
      expect(ENEMIES[id].deathPool).toBeDefined();
      expect(ENEMIES[id].liquor).toBeDefined();
      expect(ENEMIES[id].intro).toBeTruthy();
    }
  });
});
