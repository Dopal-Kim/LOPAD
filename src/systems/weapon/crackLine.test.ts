import { describe, expect, it } from 'vitest';
import { WEAPONS } from '../../data';
import { crackTiles, waveFrontRatio, waveHit, waveTimeline } from './crackWave';
import { pickMove } from './moves';

describe('58라운드 Q3 대검 차지 균열 (꽂아내리기 대체)', () => {
  it('칸 수 = min(단계 최대, 커서까지 반올림·최소 1, 벽까지 내림) — 아트 pickRule', () => {
    expect(crackTiles(3, 200, 999, 16)).toBe(3);
    expect(crackTiles(5, 40, 999, 16)).toBe(3);
    expect(crackTiles(5, 23, 999, 16)).toBe(1);
    expect(crackTiles(5, -10, 999, 16)).toBe(1);
    expect(crackTiles(5, 200, 47, 16)).toBe(2);
    expect(crackTiles(5, 200, 10, 16)).toBe(0);
  });

  it('앞머리가 지나간 칸만 맞는다 (그림 메모가 없으면 선형)', () => {
    const tl = waveTimeline(null, 135);
    expect(waveFrontRatio(tl, 0)).toBe(0);
    expect(waveFrontRatio(tl, 67.5)).toBeCloseTo(0.5);
    const front = 48 * waveFrontRatio(tl, 67.5);
    expect(waveHit({ x: 0, y: 0 }, { x: 1, y: 0 }, front, 8, { x: 20, y: 0, r: 4 })).toBe(true);
    expect(waveHit({ x: 0, y: 0 }, { x: 1, y: 0 }, front, 8, { x: 40, y: 0, r: 4 })).toBe(false);
  });

  it('데이터: 단계 3/4/5칸 · 어느 갈래든 휘둘러 내리찍기 (꽂아내리기 없음)', () => {
    const cl = WEAPONS.greatsword.combo!.charge!.crackLine!;
    expect(cl.tilesByStage).toEqual([3, 4, 5]);
    // 61라운드 P1: 차지 = 좌 홀드 (어느 갈래든)
    expect(pickMove('greatsword', 'attackHold', [])?.id).toBe('charge_swing');
    expect(pickMove('greatsword', 'attackHold', ['crush'])?.id).toBe('charge_swing');
    expect(pickMove('greatsword', 'attackHold', ['crush'], (m) => m.id === 'plunge')).toBeNull();
  });
});
