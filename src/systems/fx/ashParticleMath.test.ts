import { describe, expect, it } from 'vitest';
import { ashDrawPos, ashFrame, parseAshKinds, parseAshRecipes, spawnAsh, stepAsh } from './ashParticleMath';

/** 아트 particles_ash JSON 을 줄인 예 (계약 §16) */
const json = {
  kinds: {
    ash_s: {
      frames: [0, 1],
      frameMode: 'loop',
      lifeMs: [500, 900],
      speedPxPerSec: [40, 140],
      gravityPxPerSec2: 120,
      dragPerSec: 2,
      frameMs: 80,
    },
    ember_s: {
      frames: [14, 16],
      frameMode: 'life',
      lifeMs: [180, 380],
      speedPxPerSec: [80, 220],
      gravityPxPerSec2: 260,
    },
    ash_l: { frames: [6, 9], frameMode: 'loop', lifeMs: [800, 1400], speedPxPerSec: [20, 80], swayPx: 6, swayHz: 2 },
    broken: { frameMode: 'loop' },
  },
  recipes: { hit_katana: { ember_s: 3, ash_s: 3, coneDeg: 50 } },
};

describe('ashParticleMath: 재 파편 입자 (55라운드 Q8)', () => {
  const unit = 0.25; // pixelScale 0.5 → 월드
  const kinds = parseAshKinds(json.kinds, unit);
  const recipes = parseAshRecipes(json.recipes);

  it('kinds: 프레임 범위·구동 방식, 길이는 도트 → 월드 환산, 틀린 항목은 버림', () => {
    expect(kinds.ash_s).toMatchObject({ start: 0, count: 2, mode: 'loop', speed: [10, 35], gravity: 30, drag: 2 });
    expect(kinds.ember_s).toMatchObject({ start: 14, count: 3, mode: 'life' });
    expect(kinds.ash_l.swayPx).toBe(1.5);
    expect(kinds.broken).toBeUndefined();
    expect(recipes.hit_katana).toEqual({ kinds: { ember_s: 3, ash_s: 3 }, coneDeg: 50 });
  });

  it('발생: 묶음 개수 × 배율(올림), 원뿔 안 방향', () => {
    let i = 0;
    const seq = [0, 1, 0.5];
    const rng = () => seq[i++ % seq.length];
    const ps = spawnAsh(recipes.hit_katana, kinds, 10, 20, 0, 1, rng);
    expect(ps).toHaveLength(6);
    for (const p of ps) {
      const a = Math.atan2(p.vy, p.vx);
      expect(Math.abs(a)).toBeLessThanOrEqual((25 * Math.PI) / 180 + 1e-9);
    }
    expect(spawnAsh(recipes.hit_katana, kinds, 0, 0, 0, 0.5, rng)).toHaveLength(4);
  });

  it('진행: 끌림·중력으로 떨어지고 수명이 다하면 끝', () => {
    const p = { kind: 'ash_s', x: 0, y: 0, vx: 20, vy: 0, ageMs: 0, lifeMs: 100, seed: 0 };
    expect(stepAsh(p, kinds.ash_s, 50)).toBe(true);
    expect(p.vx).toBeLessThan(20);
    expect(p.vy).toBeGreaterThan(0);
    expect(p.x).toBeGreaterThan(0);
    expect(stepAsh(p, kinds.ash_s, 60)).toBe(false);
  });

  it('프레임: life = 수명 진행도로 식음, loop = frameMs 간격 반복', () => {
    const e = { kind: 'ember_s', x: 0, y: 0, vx: 0, vy: 0, ageMs: 0, lifeMs: 300, seed: 0 };
    expect(ashFrame(e, kinds.ember_s)).toBe(14);
    e.ageMs = 150;
    expect(ashFrame(e, kinds.ember_s)).toBe(15);
    e.ageMs = 299;
    expect(ashFrame(e, kinds.ember_s)).toBe(16);
    const a = { kind: 'ash_s', x: 0, y: 0, vx: 0, vy: 0, ageMs: 0, lifeMs: 900, seed: 0 };
    expect(ashFrame(a, kinds.ash_s)).toBe(0);
    a.ageMs = 85;
    expect(ashFrame(a, kinds.ash_s)).toBe(1);
    a.ageMs = 165;
    expect(ashFrame(a, kinds.ash_s)).toBe(0);
  });

  it('그리는 위치는 도트 격자에 맞춘다 (+ 흔들림)', () => {
    const p = { kind: 'ash_l', x: 1.13, y: 2.6, vx: 0, vy: 0, ageMs: 0, lifeMs: 900, seed: 0 };
    const at = ashDrawPos(p, kinds.ash_l, unit);
    expect(at.x % unit).toBeCloseTo(0);
    expect(at.y).toBe(2.5);
  });
});
