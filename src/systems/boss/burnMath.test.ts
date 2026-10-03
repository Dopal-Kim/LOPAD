import { describe, expect, it } from 'vitest';
import { burnColumn, isBurning, newBurnState, phaseLengthMs, stepBurn } from './burnMath';
import { caskCircumferenceWorld, caskRadiusFromArt } from './caskMath';

const T = { igniteMs: 260, outMs: 420, lingerMs: 1000 };

describe('54라운드 Q18 보스 불타기 상태', () => {
  it('불 위 → ignite → loop, 벗어나면 lingerMs 뒤 out → off', () => {
    const s = newBurnState();
    expect(stepBurn(s, false, 0, T)).toBeNull();
    expect(s.phase).toBe('off');
    expect(stepBurn(s, true, 100, T)).toBe('ignited');
    expect(s.phase).toBe('ignite');
    expect(isBurning(s)).toBe(true);
    stepBurn(s, true, 400, T);
    expect(s.phase).toBe('loop');
    expect(s.since).toBe(360);
    // 불에서 나옴: 1초 동안 그대로 탄다
    stepBurn(s, false, 1000, T);
    stepBurn(s, false, 1999, T);
    expect(s.phase).toBe('loop');
    stepBurn(s, false, 2000, T);
    expect(s.phase).toBe('out');
    expect(isBurning(s)).toBe(false);
    stepBurn(s, false, 2419, T);
    expect(s.phase).toBe('out');
    stepBurn(s, false, 2420, T);
    expect(s.phase).toBe('off');
  });

  it('잠깐 벗어났다 돌아오면 loop 유지 · out 중 다시 불 위면 ignite 부터', () => {
    const s = newBurnState();
    stepBurn(s, true, 0, T);
    stepBurn(s, true, 300, T);
    stepBurn(s, false, 400, T);
    stepBurn(s, true, 1300, T);
    stepBurn(s, false, 1350, T);
    stepBurn(s, false, 2300, T);
    expect(s.phase).toBe('loop');
    stepBurn(s, false, 2350, T);
    expect(s.phase).toBe('out');
    expect(stepBurn(s, true, 2400, T)).toBe('ignited');
    expect(s.phase).toBe('ignite');
  });

  it('ignite 중에 벗어나도 벗어난 시각을 잃지 않는다', () => {
    const s = newBurnState();
    stepBurn(s, true, 0, T);
    stepBurn(s, false, 100, T);
    stepBurn(s, false, 300, T);
    expect(s.phase).toBe('loop');
    stepBurn(s, false, 1100, T);
    expect(s.phase).toBe('out');
  });

  it('국면 열: loop 는 반복, ignite·out 은 마지막 열 유지 · 국면 길이', () => {
    const d = [60, 60, 70, 70, 80, 80, 80, 80, 80, 80, 80, 80, 80, 90, 110, 140];
    const loop = [4, 5, 6, 7, 8, 9, 10, 11];
    expect(burnColumn(loop, d, 0, true)).toBe(4);
    expect(burnColumn(loop, d, 79, true)).toBe(4);
    expect(burnColumn(loop, d, 80, true)).toBe(5);
    expect(burnColumn(loop, d, 640, true)).toBe(4);
    expect(burnColumn([0, 1, 2, 3], d, 5000, false)).toBe(3);
    expect(phaseLengthMs([0, 1, 2, 3], d, 999)).toBe(260);
    expect(phaseLengthMs([12, 13, 14, 15], d, 999)).toBe(420);
    expect(phaseLengthMs(undefined, d, 999)).toBe(999);
  });
});

describe('54라운드 Q21 굴러가는 술통 판정 반경', () => {
  it('diameterPx(논리 px) → 반경 월드 = 지름 / 2 / 2', () => {
    expect(caskRadiusFromArt({ diameterPx: 34, circumferencePx: 98 }, 7, 1)).toBeCloseTo(8.5);
  });
  it('지름이 없으면 굴림 둘레 / 2π (논리 px → 월드 ÷2)', () => {
    expect(caskCircumferenceWorld({ circumferencePx: 98 })).toBe(49);
    expect(caskRadiusFromArt({ circumferencePx: 98 }, 7, 1)).toBeCloseTo(49 / (2 * Math.PI));
    // 1차 그림(둘레 78) 대비 1.25배
    expect(
      caskRadiusFromArt({ circumferencePx: 98 }, 7, 1) / caskRadiusFromArt({ circumferencePx: 78 }, 7, 1),
    ).toBeCloseTo(98 / 78);
  });
  it('그림이 없으면 fallback', () => {
    expect(caskRadiusFromArt(undefined, 7, 1)).toBe(7);
    expect(caskCircumferenceWorld(undefined)).toBeNull();
  });
});
